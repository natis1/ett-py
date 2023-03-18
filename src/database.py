import math
import queue
import sqlite3
import threading
import traceback
import uuid
import time
from enum import Enum

from . import ett


class Fetch(Enum):
    NONE = 0
    ONE = 1
    ALL = 2


work_queue = queue.Queue()


def sqlite_worker():
    con = sqlite3.connect("ett.db")
    cur = con.cursor()
    while True:
        try:
            (sql, params, fetch_one), result_queue = work_queue.get()
            res = None
            print(sql.strip(), params, fetch_one)
            if params is not None:
                res = cur.execute(sql, params)
            else:
                res = cur.execute(sql)
            if fetch_one == Fetch.ONE:
                result_queue.put(cur.fetchone())
            elif fetch_one == Fetch.ALL:
                result_queue.put(cur.fetchall())
            else:
                result_queue.put(res)
            con.commit()
        except Exception as e:
            traceback.print_exc()


threading.Thread(target=sqlite_worker, daemon=True).start()


def sql_exec(sql, params=None, fetch: Fetch = Fetch.NONE) -> sqlite3.Cursor:
    # you might not really need the results if you only use this
    # for writing unless you use something like https://www.sqlite.org/lang_returning.html
    result_queue = queue.Queue()
    work_queue.put(((sql, params, fetch), result_queue))
    return result_queue.get()


# WARNING: ONLY search_for can be untrusted. ALL OTHERS MUST BE HARDCODED.
def get_code(table: str, key: str, search: str, search_for: str):
    v = sql_exec(f"""
            SELECT {key} FROM {table} WHERE {search} = ?
    """, (search_for,), Fetch.ONE)
    if v is not None:
        return v[0]
    return None


# WARNING: ONLY search_for can be untrusted. ALL OTHERS MUST BE HARDCODED.
def get_row(table: str, search: str, search_for: str):
    return sql_exec(f"""
            SELECT * FROM {table} WHERE {search} = ?
    """, (search_for,), Fetch.ONE)


def init_db():
    sql_exec("CREATE TABLE IF NOT EXISTS players(PlayerName, Karma, Characters, BonusXP, Upgrades, Enterer, "
             "PRIMARY KEY(PlayerName))")
    # Unlocks = items unlocked by player to be purchased
    # Rewards = karma spent on the PC
    sql_exec("CREATE TABLE IF NOT EXISTS characters(PlayerName, Name, Ancestry, Background, Class, Heritage, "
             "Unlocks, Rewards, Home, Pathbuilder, Comments, CommunityService, PDFs, FVTTs, XP, ExpectedGold, "
             "CurrentGold, Games, Items, Rares, Ironman, Enterer, PRIMARY KEY(PlayerName, Name))")
    sql_exec("CREATE TABLE IF NOT EXISTS games(ID, Name, Date, Enterer, Time, GameLevel, Items, PRIMARY KEY(ID))")
    # Events holds all games, transactions, and adjustments that could happen to a player.
    sql_exec("CREATE TABLE IF NOT EXISTS events(ID, TimeStamp, PlayerName, CharacterName, EventDate, "
             "XPAdjust, KarmaAdjust, GoldAdjust, ItemsBought, ItemsLost, Unlocks, Rewards, CommunityService, "
             "Comment, PRIMARY KEY(ID))")
    sql_exec("CREATE TABLE IF NOT EXISTS historians(OathID, Email, Name, permissions, PRIMARY KEY(OathID))")


def get_player(name):
    return sql_exec("""
        SELECT PlayerName FROM players WHERE PlayerName = ?
    """, (name,), Fetch.ONE)


def add_player(name, enterer, starting_karma: int = 0, starting_xp: float = 0.0):
    if get_player(name) is not None:
        print("Player already exists " + name)
        return False

    print("Adding Character " + name)
    sql_exec("""
        INSERT INTO players VALUES
        (?, ?, '', ?, '', ?)
    """, (name, starting_karma, starting_xp, enterer))


def add_xp_to_player(name, xp: float):
    existing_xp = get_code("players", "BonusXP", "PlayerName", name)
    if existing_xp is None:
        print("Player does not exist " + name)
        return False
    new_xp = existing_xp + xp
    sql_exec("""
            UPDATE players SET BonusXP = ? where PlayerName = ?
    """, (new_xp, name))


def get_character(player_name, name):
    return sql_exec("""
        SELECT PlayerName FROM characters WHERE PlayerName = ? and Name = ?
    """, (player_name, name), Fetch.ONE)


def add_character(player_name, enterer, name, ancestry, background, pc_class, heritage, pathbuilder, ironman, home='',
                  starting_xp: float = 0.0):
    if get_player(player_name) is None:
        print("Player does not exist " + player_name)
        return False

    if get_character(player_name, name) is not None:
        print("PC already exists with name " + name + " on player: " + player_name)
        return False

    print("Adding PC " + name)
    sql_exec("""
        INSERT INTO characters VALUES
        (?, ?, ?, ?, ?, ?, '', '', ?, ?, '', 0, '', '', ?, 0, 0, '', '', '', ?, ?)""",
             (player_name, name, ancestry, background, pc_class, heritage, home, pathbuilder, starting_xp, ironman,
              enterer))


# Add item to the player's inventory, spending any money as appropriate. This ALSO
# adds the item to the rare unlocks if it's a rare item
def add_items(items: list[ett.Pf2eElement]):
    pass


# Remove item from the player's inventory, gaining any gold on the Pf2eElement
# gold multiplier should be set to 0 if the item was used.
# gold multiplier should be set to half the item's value if the item was sold.
# This also removes the item from the rare unlocks if it's a rare item.
def remove_items(items: list[ett.Pf2eElement], gold_multiplier):
    pass


def add_game(name, date, time, items: list[ett.Pf2eElement], players: list[ett.EttGamePlayer],
             continuation, comments, enterer):
    comments = "GAME PLAYED: " + comments
    game_level = ett.ett_party_level(players)
    items_text = ett.pf2e_element_list_to_string(items)
    rare_items = []
    for i in items:
        if i.rarity == 2:
            rare_items.append(i)
    rare_text = ett.pf2e_element_list_to_string(rare_items)
    timestamp = time.time()
    sql_exec("""
            INSERT INTO games VALUES
            (?, ?, ?, ?, ?, ?, ?)
        """, (uuid.uuid4(), name, date, enterer, time, game_level, items_text))
    for pl in players:
        if pl.player_level == 0:
            add_xp_to_player(pl.player_name, pl.time_played * 1.5)
        else:
            pl_stats = sql_exec("""
                SELECT XP, ExpectedGold, CurrentGold, Unlocks, CommunityService, Ironman
                from characters WHERE PlayerName = ? and Name = ?
            """, (pl.player_name, pl.name), Fetch.ONE)
            # This means the PC is invalid
            if pl_stats is None:
                print("ERROR: Character with player name: " + pl.player_name +
                      " and name: " + pl.name + " does not exist!")
                continue
            cur_karma = get_code("players", "Karma", "PlayerName", pl.player_name)
            # This means the player is invalid
            if cur_karma is None:
                print("ERROR: Player with name: " + pl.player_name + " does not exist!")
                continue
            cur_karma = cur_karma[0]
            expected_level = (pl_stats[0] / 12) + 1
            tt_up = (expected_level < pl.player_level) and (not continuation)
            net_karma = pl.gained_karma - tt_up
            total_karma = net_karma + cur_karma
            if not pl_stats[1]:
                pl_stats[1] = 0
            if not pl_stats[2]:
                pl_stats[2] = 0
            # subtract any community service you need to do
            cs_remaining = pl_stats[4]
            if not (pl_stats[4] == '' or pl_stats[4] == 0):
                if (pl_stats[4] - pl.time_played) <= 0:
                    cs_remaining = 0
                    pl.time_played = pl.time_played - pl_stats[4]
                else:
                    cs_remaining = pl_stats[4] - pl.time_played
                    pl.time_played = 0
            # add gold and XP

            xp_added = ett.ett_xp_rate(pl.player_level, game_level) * pl.time_played
            adventure_gold = ett.ett_gold_add_xp(pl_stats[0], xp_added)
            total_xp = xp_added + pl_stats[0]
            expected_gold = adventure_gold + pl_stats[1]
            current_gold = adventure_gold + pl_stats[2]

            cur_unlocks = ett.string_to_pf2e_element_list(pl_stats[3])
            unlocks = ett.ett_parse_unlocks(cur_unlocks, items, [], (1 + math.floor(total_xp / 12)))
            unlocks_str = ett.pf2e_element_list_to_string(unlocks)
            # If you died, your community service gets set from your current level
            # But you at least gain the xp from playing.
            if not pl.alive:
                cs_remaining = ett.ett_died_cs(pl, (1 + math.floor(total_xp / 12)), pl_stats[5])
            # Update the player with the new game information
            sql_exec("""
                UPDATE characters SET XP = ?, ExpectedGold = ?, CurrentGold = ?, Unlocks = ?, CommunityService = ?
                where PlayerName = ? and Name = ?
            """, (total_xp, expected_gold, current_gold, unlocks_str, cs_remaining, pl.player_name, pl.name))
            sql_exec("""
                UPDATE players SET Karma = ? where PlayerName = ?
            """, (total_karma, pl.player_name))
            sql_exec("""
                INSERT INTO events VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, '', '', ?, '', ?)
            """, (uuid.uuid4(), timestamp, pl.player_name, pl.name, date, xp_added, net_karma, adventure_gold,
                  items_text, comments))
            print("Updated player with the following information: ")
            print("total_xp, expected_gold, current_gold, unlocks_str, cs_remaining, pl.player_name, pl.name")
            print(total_xp, expected_gold, current_gold, unlocks_str, cs_remaining, pl.player_name, pl.name)
            print("Karma: " + str(total_karma))


def buy_items(player_name, name, date, comments, items: list[ett.Pf2eElement], price_factor: float = 1.0):
    comments = "BUY EVENT: " + comments
    pl_stats = sql_exec("""
        SELECT CurrentGold, Unlocks, Items, XP
        from characters WHERE PlayerName = ? and Name = ?
    """, (player_name, name), Fetch.ONE)
    if pl_stats is None:
        print("ERROR: Character: " + player_name + ", " + name + "does not exist!")
        return

    timestamp = time.time()
    # Add cost
    total_cost = 0
    for i in items:
        total_cost += i.cost * i.quantity * price_factor
    final_money = pl_stats[0] - total_cost
    # Now add rare items to the unlocks if applicable
    cur_unlocks = ett.string_to_pf2e_element_list(pl_stats[1])
    unlocks = ett.ett_parse_unlocks(cur_unlocks, items, [], 1 + (math.floor(pl_stats[3] / 12)))
    unlocks_str = ett.pf2e_element_list_to_string(unlocks)
    # Finally add all items together
    cur_items = ett.string_to_pf2e_element_list(pl_stats[2])
    output_items = []
    for j in cur_items:
        temp_item = j
        for i in items:
            if i.name == j.name:
                temp_item.quantity += i.quantity
        output_items += temp_item
    items_str = ett.pf2e_element_list_to_string(output_items)
    sql_exec("""
                    UPDATE characters SET CurrentGold = ?, Unlocks = ?, Items = ?
                    where PlayerName = ? and Name = ?
                """, (final_money, unlocks_str, items_str, player_name, name))
    sql_exec("""
        INSERT INTO events VALUES
        (?, ?, ?, ?, ?, 0, 0, 0, ?, '', ?, '', ?)
    """, (uuid.uuid4(), timestamp, player_name, name, date,
          items_str, unlocks_str, comments))
    print("Updated player with the following information: ")
    print("final_money, unlocks_str, items_str, player_name, name")
    print(final_money, unlocks_str, items_str, player_name, name)


# For selling items. Also for using items in an adventure
# set price factor to 0 if you are using an item and price factor to
def sell_items(player_name, name, date, comments, items: list[ett.Pf2eElement], price_factor: float = 0.5):
    comments = "SELL EVENT: " + comments
    pl_stats = sql_exec("""
            SELECT CurrentGold, Items
            from characters WHERE PlayerName = ? and Name = ?
        """, (player_name, name), Fetch.ONE)
    if pl_stats is None:
        print("ERROR: Character: " + player_name + ", " + name + "does not exist!")
        return

    timestamp = time.time()
    cur_items = ett.string_to_pf2e_element_list(pl_stats[1])
    cur_gold = pl_stats[0]
    final_items = []
    gold_sold = 0
    for j in cur_items:
        for i in items:
            if i.name == j.name:
                # We are able to sell all of our items
                if i.quantity <= j.quantity:
                    j.quantity -= i.quantity
                    gold_sold += i.quantity * price_factor * i.cost
                else:
                    # Otherwise, sell all that we can
                    gold_sold += j.quantity * price_factor * i.cost
                    j.quantity = 0
        # If we still have stock left after doing the sell, we want to add this item to the list of items to return
        if j.quantity > 0:
            final_items += j

    final_str = ett.pf2e_element_list_to_string(final_items)
    final_gold = cur_gold + gold_sold
    sql_exec("""
                    UPDATE characters SET CurrentGold = ?, Items = ?
                    where PlayerName = ? and Name = ?
                """, (final_gold, final_str, player_name, name))
    sql_exec("""
            INSERT INTO events VALUES
            (?, ?, ?, ?, ?, 0, 0, 0, '', ?, '', '', ?)
        """, (uuid.uuid4(), timestamp, player_name, name, date,
              ett.pf2e_element_list_to_string(items), comments))
    print("Updated player with the following information: ")
    print("final_gold, final_str, items sold, player_name, name")
    print(final_gold, final_str, ett.pf2e_element_list_to_string(items), player_name, name)
