import math
import queue
import sqlite3
import threading
import traceback
import uuid
import time
from enum import Enum, IntEnum

from . import ett


class Fetch(Enum):
    NONE = 0
    ONE = 1
    ALL = 2


class PLAYERS(IntEnum):
    PlayerName = 0
    Karma = 1
    Characters = 2
    BonusXP = 3
    Upgrades = 4
    Enterer = 5


class CHARACTERS(IntEnum):
    PlayerName = 0
    Name = 1
    Ancestry = 2
    Background = 3
    Class = 4
    Heritage = 5
    Unlocks = 6
    Rewards = 7
    Home = 8
    Pathbuilder = 9
    Comments = 10
    CommunityService = 11
    PDFs = 12
    FVTTs = 13
    XP = 14
    ExpectedGold = 15
    CurrentGold = 16
    Games = 17
    Items = 18
    Rares = 19
    Ironman = 20
    Enterer = 21


class GAMES(IntEnum):
    ID = 0
    Name = 1
    Date = 2
    Enterer = 3
    Time = 4
    GameLevel = 5
    Items = 6
    GM = 7


class HISTORIANS(IntEnum):
    OathID = 0
    Email = 1
    Name = 2
    Permissions = 3


class EVENTS(IntEnum):
    ID = 0
    RelatedID = 1
    TimeStamp = 2
    PlayerName = 3
    CharacterName = 4
    EventDate = 5
    XPAdjust = 6
    KarmaAdjust = 7
    GoldAdjust = 8
    ItemsBought = 9
    ItemsLost = 10
    Unlocks = 11
    Rewards = 12
    CommunityService = 13
    Comment = 14


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


def sql_exec(sql, params=None, fetch: Fetch = Fetch.NONE):
    # you might not really need the results if you only use this
    # for writing unless you use something like https://www.sqlite.org/lang_returning.html
    result_queue = queue.Queue()
    work_queue.put(((sql, params, fetch), result_queue))
    return result_queue.get()


SAFE_PLAYER_COLUMNS = ['PlayerName', 'Karma', 'Characters', 'BonusXP', 'Upgrades', 'Enterer',
                       'PlayerName desc', 'Karma desc', 'Characters desc', 'BonusXP desc',
                       'Upgrades desc', 'Enterer desc']
SAFE_CHARACTER_COLUMNS = ['PlayerName', 'Name', 'Ancestry', 'Background', 'Class', 'Heritage',
                          'Unlocks', 'Rewards', 'Home', 'CommunityService', 'XP', 'ExpectedGold',
                          'CurrentGold', 'Ironman', 'Enterer',
                          'PlayerName desc', 'Name desc', 'Ancestry desc', 'Background desc', 'Class desc',
                          'Heritage desc', 'Unlocks desc', 'Rewards desc', 'Home desc', 'CommunityService desc',
                          'XP desc', 'ExpectedGold desc', 'CurrentGold desc', 'Ironman desc', 'Enterer desc'
                          ]
SAFE_GAME_COLUMNS = ['ID', 'Name', 'Date', 'Enterer', 'Time', 'GameLevel', 'GM',
                     'ID desc', 'Name desc', 'Date desc', 'Enterer desc', 'Time desc', 'GameLevel desc', 'GM desc']


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


# NOTE: order_by MUST be made SAFE before running this to avoid SQL injection.
def get_offset_limit_query(order_by, offset: int = 0, limit: int = 0):
    if (not isinstance(offset, int)) or (not isinstance(limit, int)):
        print("ERROR: ATTEMPTED POSSIBLE SQL INJECTION FROM ", offset, limit)
        return []
    qry = ''

    if isinstance(order_by, str):
        qry += f' ORDER BY {order_by}'
    elif isinstance(order_by, list) and len(order_by) > 0:
        append = order_by[0]
        for i in range(1, len(order_by)):
            append += ',' + order_by[i]
        qry += f' ORDER BY {append}'

    if offset != 0:
        qry += f' OFFSET {offset}'

    if limit != 0:
        qry += f' LIMIT {limit}'

    return qry


# ONLY OFFSET AND LIMIT ARE ALLOWED TO BE UNSAFE HERE
def get_table(table: str, order_by, offset: int = 0, limit: int = 0):
    qry = get_offset_limit_query(order_by, offset, limit)
    return sql_exec(f"SELECT * FROM {table} " + qry, None, Fetch.ALL)


def get_players_table(order_by, offset: int = 0, limit: int = 0, search: str = ""):
    true_order = []
    if isinstance(order_by, str):
        order_by = [order_by]

    if isinstance(order_by, list):
        for i in order_by:
            if i in SAFE_PLAYER_COLUMNS:
                true_order += [i]

    qry = get_offset_limit_query(true_order, offset, limit)
    if search:
        total = sql_exec("SELECT COUNT(*) FROM players WHERE PlayerName LIKE ?", ('%'+search+'%',), Fetch.ONE)
        page = sql_exec("SELECT * FROM players WHERE PlayerName LIKE ? " + qry, ('%' + search + '%',), Fetch.ALL)
        return total, page
    else:
        total = sql_exec("SELECT COUNT(*) FROM players", None, Fetch.ONE)
        page = sql_exec("SELECT * FROM players " + qry, None, Fetch.ALL)
        return total, page


def get_characters_table(order_by, offset: int = 0, limit: int = 0, search: str = ""):
    true_order = []
    if isinstance(order_by, str):
        order_by = [order_by]

    if isinstance(order_by, list):
        for i in order_by:
            if i in SAFE_CHARACTER_COLUMNS:
                true_order += [i]

    qry = get_offset_limit_query(true_order, offset, limit)
    if search:
        s = '%' + search + '%'
        total = sql_exec("SELECT COUNT(*) FROM characters WHERE "
                         "PlayerName LIKE ? or Name LIKE ? or Ancestry LIKE ? or Class LIKE ? ",
                         (s, s, s, s), Fetch.ONE)
        page = sql_exec("SELECT * FROM characters WHERE "
                        "PlayerName LIKE ? or Name LIKE ? or Ancestry LIKE ? or Class LIKE ? " + qry,
                        (s, s, s, s), Fetch.ALL)
        return total, page
    else:
        total = sql_exec("SELECT COUNT(*) FROM characters ", None, Fetch.ONE)
        page = sql_exec("SELECT * FROM characters " + qry, None, Fetch.ALL)
        return total, page


def get_games_table(order_by, offset: int = 0, limit: int = 0, search: str = ""):
    true_order = []
    if isinstance(order_by, str):
        order_by = [order_by]

    if isinstance(order_by, list):
        for i in order_by:
            if i in SAFE_GAME_COLUMNS:
                true_order += [i]

    qry = get_offset_limit_query(true_order, offset, limit)
    if search:
        s = '%' + search + '%'
        total = sql_exec("SELECT COUNT(*) FROM games WHERE "
                         "Name LIKE ? or Date LIKE ? or GameLevel LIKE ? or GM LIKE ? ",
                         (s, s, s, s), Fetch.ONE)
        page = sql_exec("SELECT * FROM games WHERE "
                        "Name LIKE ? or Date LIKE ? or GameLevel LIKE ? or GM LIKE ? " + qry,
                        (s, s, s, s), Fetch.ALL)
        return total, page
    else:
        total = sql_exec("SELECT COUNT(*) FROM games ", None, Fetch.ONE)
        page = sql_exec("SELECT * FROM games " + qry, None, Fetch.ALL)
        return total, page



def init_db():
    sql_exec("CREATE TABLE IF NOT EXISTS players(PlayerName, Karma, Characters, BonusXP, Upgrades, Enterer, "
             "PRIMARY KEY(PlayerName))")
    # Unlocks = items unlocked by player to be purchased
    # Rewards = karma spent on the PC
    sql_exec("CREATE TABLE IF NOT EXISTS characters(PlayerName, Name, Ancestry, Background, Class, Heritage, "
             "Unlocks, Rewards, Home, Pathbuilder, Comments, CommunityService, PDFs, FVTTs, XP, ExpectedGold, "
             "CurrentGold, Games, Items, Rares, Ironman, Enterer, PRIMARY KEY(PlayerName, Name))")
    sql_exec("CREATE TABLE IF NOT EXISTS games(ID, Name, Date, Enterer, Time, GameLevel, Items, GM, PRIMARY KEY(ID))")
    # Events holds all games, transactions, and adjustments that could happen to a player.
    sql_exec("CREATE TABLE IF NOT EXISTS events(ID, RelatedID, TimeStamp, PlayerName, CharacterName, EventDate, "
             "XPAdjust, KarmaAdjust, GoldAdjust, ItemsBought, ItemsLost, Unlocks, Rewards, CommunityService, "
             "Comment, PRIMARY KEY(ID))")
    sql_exec("CREATE TABLE IF NOT EXISTS historians(OathID, Email, Name, permissions, PRIMARY KEY(OathID))")


def get_player(name):
    return sql_exec("""
        SELECT * FROM players WHERE PlayerName = ?
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


def add_karma_to_player(name, karma: int):
    existing_karma = get_code("players", "Karma", "PlayerName", name)
    if existing_karma is None:
        print("Player does not exist " + name)
        return False
    new_karma = existing_karma + karma
    sql_exec("""
            UPDATE players SET Karma = ? where PlayerName = ?
    """, (new_karma, name))


def get_character(player_name, name):
    return sql_exec("""
        SELECT * FROM characters WHERE PlayerName = ? and Name = ?
    """, (player_name, name), Fetch.ONE)


def add_character(player_name, enterer, name, ancestry, background, pc_class, heritage, pathbuilder, ironman, home='',
                  starting_xp: float = 0.0):
    p = get_player(player_name)
    if p is None:
        print("Player does not exist " + player_name)
        return "Player does not exist " + player_name
    p = list(p)

    if get_character(player_name, name) is not None:
        print("PC already exists with name " + name + " on player: " + player_name)
        return "PC already exists with name " + name + " on player: " + player_name

    if ett.get_available_slots(p[PLAYERS.Upgrades], p[PLAYERS[CHARACTERS]]) <= 0:
        print("Not enough character slots for PC " + name + " on player: " + player_name)
        return "Not enough character slots for PC " + name + " on player: " + player_name

    gold = ett.STARTING_GOLD + ett.ett_gold_add_xp(0, starting_xp)
    # Add character to char list
    chars = string_list_to_list(p[PLAYERS.Characters])
    chars += [name]
    p[PLAYERS.Characters] = list_to_string(chars)
    edit_player(p)

    sql_exec("""
        INSERT INTO characters VALUES
        (?, ?, ?, ?, ?, ?, '', '', ?, ?, '', 0, '', '', ?, ?, ?, '', '', '', ?, ?)""",
             (player_name, name, ancestry, background, pc_class, heritage, home, pathbuilder, starting_xp,
              gold, gold, ironman, enterer))


def add_game(name, date, game_time, items: list[ett.Pf2eElement], players: list[ett.EttGamePlayer],
             continuation, comments, enterer):
    existing_games = sql_exec("""
        SELECT * FROM Games WHERE Name = ? and Date = ?
    """, (name, date), Fetch.ONE)
    if existing_games:
        print("This game is already logged in our DB. Exiting. ")
    comments = "GAME PLAYED: " + comments
    game_level = ett.ett_party_level(players)
    items_text = ett.pf2e_element_list_to_string(items)
    timestamp = time.time()
    game_id = str(uuid.uuid4())
    for pl in players:
        # GM player
        if pl.player_level == 0:
            add_xp_to_player(pl.player_name, pl.time_played * 1.5)
            sql_exec("""
                        INSERT INTO games VALUES
                        (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (game_id, name, date, enterer, game_time, game_level, items_text, pl.player_name))

            sql_exec("""
                            INSERT INTO events VALUES
                            (?, ?, ?, ?, ?, ?, ?, ?, ?, '', '', ?, '', 0, ?)
                        """, (
                str(uuid.uuid4()), game_id, timestamp, pl.player_name, pl.name, date, pl.time_played * 1.5,
                pl.gained_karma, 0, items_text, comments))
        else:
            character = get_character(pl.player_name, pl.name)
            # This means the PC is invalid
            if character is None:
                print("ERROR: Character with player name: " + pl.player_name +
                      " and name: " + pl.name + " does not exist!")
                continue
            character = list(character)
            expected_level = ett.get_level(character[CHARACTERS.XP])
            tt_up = (expected_level < pl.player_level) and (not continuation)
            net_karma = pl.gained_karma - tt_up
            if not character[CHARACTERS.ExpectedGold]:
                character[CHARACTERS.ExpectedGold] = 0
            if not character[CHARACTERS.CurrentGold]:
                character[CHARACTERS.CurrentGold] = 0
            # subtract any community service you need to do
            cs_remaining = character[CHARACTERS.CommunityService]
            cs_change = -cs_remaining
            if not (character[CHARACTERS.CommunityService] == '' or character[CHARACTERS.CommunityService] == 0):
                if (character[CHARACTERS.CommunityService] - pl.time_played) <= 0:
                    cs_remaining = 0
                    pl.time_played = pl.time_played - character[CHARACTERS.CommunityService]
                else:
                    cs_remaining = character[CHARACTERS.CommunityService] - pl.time_played
                    pl.time_played = 0
            # add gold and XP

            xp_added = ett.ett_xp_rate(pl.player_level, game_level) * pl.time_played
            adventure_gold = ett.ett_gold_add_xp(character[CHARACTERS.XP], xp_added)
            total_xp = xp_added + character[CHARACTERS.XP]
            character[CHARACTERS.ExpectedGold] = adventure_gold + character[CHARACTERS.ExpectedGold]
            character[CHARACTERS.CurrentGold] = adventure_gold + character[CHARACTERS.CurrentGold]

            cur_unlocks = ett.string_to_pf2e_element_list(character[CHARACTERS.Unlocks])
            # Even if no new items are unlocked. This removes all AT LEVEL items from the
            # unlocked list.
            unlocks = ett.ett_parse_unlocks(cur_unlocks, items, [], ett.get_level(total_xp))
            character[CHARACTERS.Unlocks] = ett.pf2e_element_list_to_string(unlocks)
            # If you died, your community service gets set from your current level
            # But you at least gain the xp from playing.
            if not pl.alive:
                cs_remaining = ett.ett_died_cs(pl, ett.get_level(total_xp), character[CHARACTERS.Ironman])
                cs_change += cs_remaining

            # Add game to player games list
            games = string_list_to_list(character[CHARACTERS.Games])
            games += [game_id]
            character[CHARACTERS.Games] = list_to_string(games)

            # Update the player with the new game information

            character[CHARACTERS.CommunityService] = cs_remaining
            character[CHARACTERS.XP] = total_xp
            sql_exec("""
                INSERT INTO events VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?, '', '', ?, '', ?, ?)
            """, (str(uuid.uuid4()), game_id, timestamp, pl.player_name, pl.name, date, xp_added, net_karma,
                  adventure_gold, items_text, cs_change, comments))
            add_karma_to_player(pl.name, net_karma)
            edit_character(character)


def buy_items(character, date, comments, items: list[ett.Pf2eElement], price_factor: float = 1.0):
    if len(character) != len(CHARACTERS):
        print("INVALID CHARACTER: ", character)
        return "Invalid character. Unable to parse buy_items. Please report as a bug."

    comments = "BUY EVENT: " + comments
    timestamp = time.time()

    # Check if items are legal
    cur_level = ett.get_level(character[CHARACTERS.XP])
    unlocks = ett.string_to_pf2e_element_list(character[CHARACTERS.Unlocks])
    legal_items = []
    rare_items = []
    for i in items:
        # It's legal
        if i.level <= cur_level and i.rarity <= 1:
            legal_items += [i]
            continue
        # You unlocked it so it's legal
        unlocked_rare = False
        for j in unlocks:
            # You have the right level for it
            if i.name == j.name and i.level <= (cur_level + 2):
                legal_items += [i]
                unlocked_rare = True
        # It's legal but requires a rare unlock potentially
        if i.level <= cur_level and (not unlocked_rare):
            rare_items += [i]
            legal_items += [i]

    # Add cost
    total_cost = 0
    for i in items:
        total_cost += i.cost * i.quantity * price_factor
    final_money = character[CHARACTERS.CurrentGold] - total_cost
    # Now add rare items to the rares if applicable
    cur_rares = ett.string_to_pf2e_element_list(character[CHARACTERS.Rares])
    rares = ett.ett_parse_unlocks(cur_rares, rare_items, [], 20)
    # Finally add all items together
    cur_items = ett.string_to_pf2e_element_list(character[CHARACTERS.Items])
    output_items = cur_items
    for i in legal_items:
        found_item = False
        for j in range(len(cur_items)):
            if i.name == cur_items[j].name:
                output_items[j].quantity += i.quantity
                found_item = True
                break
        if not found_item:
            output_items += [i]
    character[CHARACTERS.CurrentGold] = final_money
    character[CHARACTERS.Rares] = ett.pf2e_element_list_to_string(rares)
    character[CHARACTERS.Items] = ett.pf2e_element_list_to_string(output_items)
    sql_exec("""
        INSERT INTO events VALUES
        (?, '', ?, ?, ?, ?, 0, 0, ?, ?, '', '', ?, '', ?)
    """, (str(uuid.uuid4()), timestamp, character[CHARACTERS.PlayerName],
          character[CHARACTERS.Name], date, -total_cost,
          ett.pf2e_element_list_to_string(legal_items), ett.pf2e_element_list_to_string(rare_items), comments))
    return edit_character(character)


# For selling items. Also for using items in an adventure
# set price factor to 0 if you are using an item and price factor to
def sell_items(character, date, comments, items: list[ett.Pf2eElement], price_factor: float = 0.5):
    if len(character) != len(CHARACTERS):
        print("INVALID CHARACTER: ", character)
        return "Invalid character. Unable to parse sell_items. Please report as a bug."

    comments = "SELL EVENT: " + comments
    timestamp = time.time()
    cur_items = ett.string_to_pf2e_element_list(character[CHARACTERS.Items])
    cur_gold = character[CHARACTERS.CurrentGold]
    final_items = []
    gold_sold = 0
    for j in cur_items:
        for i in items:
            if i.name == j.name:
                # We are able to sell all of our items
                if i.quantity <= j.quantity:
                    j.quantity -= i.quantity
                    # NOTE: DO NOT PULL COST FROM i.
                    # We do not expect i to hold the cost. j should.
                    gold_sold += i.quantity * price_factor * j.cost
                else:
                    # Otherwise, sell all that we can
                    gold_sold += j.quantity * price_factor * j.cost
                    j.quantity = 0
        # If we still have stock left after doing the sell, we want to add this item to the list of items to return
        if j.quantity > 0:
            final_items += [j]

    final_str = ett.pf2e_element_list_to_string(final_items)
    final_gold = cur_gold + gold_sold
    character[CHARACTERS.CurrentGold] = final_gold
    character[CHARACTERS.Items] = final_str
    sql_exec("""
            INSERT INTO events VALUES
            (?, '', ?, ?, ?, ?, 0, 0, ?, '', ?, '', '', '',  ?)
        """, (str(uuid.uuid4()), timestamp, character[CHARACTERS.PlayerName], character[CHARACTERS.Name],
              date, gold_sold, ett.pf2e_element_list_to_string(items), comments))
    return edit_character(character)


def edit_player(player: list):
    if len(player) != len(PLAYERS):
        print("INVALID PLAYER: ", player)
        return "INVALID PLAYER: " + str(player)

    cur_player = list(get_player(player[PLAYERS.PlayerName]))

    for i in range(len(player)):
        if player[i] is None or i < 1:
            player[i] = cur_player[i]

    # move playername to the end so that query works
    player = player[1:] + player[:1]
    sql_exec("""UPDATE players SET Karma = ?, Characters = ?, BonusXP = ?, Upgrades = ?, Enterer = ?
    WHERE PlayerName = ?
    """, tuple(player))


# NOTE that character must be a correctly ordered list
def edit_character(character: list):
    if len(character) != len(CHARACTERS):
        print("INVALID CHARACTER: ", character)
        return "INVALID CHARACTER: " + str(character)

    cur_char = list(get_character(character[CHARACTERS.PlayerName], character[CHARACTERS.Name]))

    for i in range(len(character)):
        if character[i] is None or i < 2:
            character[i] = cur_char[i]

    # move playername and name to the end so that it works
    character = character[2:] + character[:2]
    # Final character Data to write:
    sql_exec("""UPDATE characters SET Ancestry = ?, Background = ?, Class = ?, Heritage = ?,
        Unlocks = ?, Rewards = ?, Home = ?, Pathbuilder = ?, Comments = ?, CommunityService = ?,
        PDFs = ?, FVTTs = ?, XP = ?, ExpectedGold = ?, CurrentGold = ?, Games = ?, Items = ?,
        Rares = ?, Ironman = ?, Enterer = ? WHERE PlayerName = ? and Name = ?
    """, tuple(character))

# TODO: Generate all items, gold, unlocked items, xp, etc, on a character, from just their
# audit history. By going through the audit history ordered by timestamp for a character
# and applying it to that character.


def string_list_to_list(elements: str):
    if not elements:
        return []
    e_str = elements.splitlines(False)
    element_list = []
    for line in e_str:
        element_list += [line]
    return element_list


def list_to_string(elements: str):
    e_str = ""
    for element_index in range(len(elements)):
        e_str += elements[element_index]
        if element_index < (len(elements) - 1):
            e_str += "\n"
    return e_str


# oh no this feels so dangerous and wrong
def change_character_name(cur_character: list, new_name: str):

    if len(cur_character) != len(CHARACTERS):
        print("INVALID CHARACTER: ", cur_character)
        return "INVALID CHARACTER: " + str(cur_character)
    cur_player = get_player(cur_character[CHARACTERS.PlayerName])
    if not cur_player:
        print("INVALID PLAYER ON CHARACTER: " + cur_character[CHARACTERS.PlayerName])
        return "INVALID PLAYER ON CHARACTER: " + cur_character[CHARACTERS.PlayerName]
    cur_player = list(cur_player)

    player_char_list = string_list_to_list(cur_player[PLAYERS.Characters])
    for i in range(len(player_char_list)):
        if player_char_list[i] == cur_character[CHARACTERS.Name]:
            player_char_list[i] = new_name

    cur_player[PLAYERS.Characters] = list_to_string(player_char_list)

    sql_exec("""
        UPDATE events SET CharacterName = ? WHERE PlayerName = ? and CharacterName = ?
    """, (new_name, cur_character[CHARACTERS.PlayerName], cur_character[CHARACTERS.Name]))
    sql_exec("""
        UPDATE characters SET Name = ? WHERE PlayerName = ? and Name = ?
    """, (new_name, cur_character[CHARACTERS.PlayerName], cur_character[CHARACTERS.Name]))

    edit_player(cur_player)


def move_character(cur_character: list, new_player_name: str):
    new_player = get_player(new_player_name)
    if not new_player:
        print("INVALID NEW PLAYER TO MOVE TO: " + new_player_name)
        return "INVALID NEW PLAYER TO MOVE TO: " + new_player_name
    new_player = list(new_player)
    if len(cur_character) != len(CHARACTERS):
        print("INVALID CHARACTER: ", cur_character)
        return "INVALID CHARACTER: " + str(cur_character)
    cur_player = get_player(cur_character[CHARACTERS.PlayerName])
    if not cur_player:
        print("INVALID PLAYER ON CHARACTER: " + cur_character[CHARACTERS.PlayerName])
        return "INVALID PLAYER ON CHARACTER: " + cur_character[CHARACTERS.PlayerName]
    cur_player = list(cur_player)
    player_char_list = string_list_to_list(cur_player[PLAYERS.Characters])
    # Remove character from old player list
    new_pc_list = []
    for i in player_char_list:
        if player_char_list != cur_character[CHARACTERS.Name]:
            new_pc_list += i

    cur_player[PLAYERS.Characters] = list_to_string(new_pc_list)

    new_player_pc_list = string_list_to_list(new_player[PLAYERS.Characters])
    new_player_pc_list += cur_character[CHARACTERS.Name]
    new_player[PLAYERS.Characters] = list_to_string(new_player_pc_list)
    # commit all the changes to DB
    edit_player(cur_player)
    edit_player(new_player)
    sql_exec("""
        UPDATE characters SET PlayerName = ? WHERE PlayerName = ? and Name = ?
    """, (new_player_name, cur_character[CHARACTERS.PlayerName], cur_character[CHARACTERS.Name]))


def change_player_name(old_name: str, new_name: str):
    sql_exec("""
        UPDATE events SET PlayerName = ? WHERE PlayerName = ?
    """, (new_name, old_name))
    sql_exec("""
        UPDATE characters SET Name = ? WHERE PlayerName = ? and Name = ?
    """, (new_name, old_name))
    sql_exec("""
        UPDATE games SET GM = ? WHERE GM = ?
    """, (new_name, old_name))
    sql_exec("""
        UPDATE players SET PlayerName = ? WHERE PlayerName = ?
    """, (new_name, old_name))
