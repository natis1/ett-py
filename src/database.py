import sqlite3
import uuid

from . import ett

con = sqlite3.connect("ett.db")
cur = con.cursor()


def init_db():
    cur.execute("CREATE TABLE IF NOT EXISTS players(PlayerName, Karma, Characters, BonusXP, Upgrades, Enterer, "
                "PRIMARY KEY(PlayerName))")
    cur.execute("CREATE TABLE IF NOT EXISTS characters(PlayerName, Name, Ancestry, Background, Class, Heritage, "
                "Unlocks, Rewards, Home, Pathbuilder, Comments, CommunityService, PDFs, FVTTs, XP, ExpectedGold, "
                "CurrentGold, Games, Items, Transactions, AncestryFeats, ClassFeats, ArchetypeFeats, SkillFeats, "
                "GeneralFeats, Enterer, PRIMARY KEY(PlayerName, Name))")
    cur.execute("CREATE TABLE IF NOT EXISTS games(ID, Name, Date, Enterer, Time, GameLevel, Items, PRIMARY KEY(ID))")
    cur.execute("CREATE TABLE IF NOT EXISTS gamePlayers(GameID, PlayerName, CharacterName, PlayerLevel, TimePlayed, "
                "TTUp, GainedKarma, PRIMARY KEY(GameID, Player))")
    cur.execute("CREATE TABLE IF NOT EXISTS transactions(ID, PlayerName, CharacterName, ItemsBought, "
                "ItemsLost, PRIMARY KEY(ID))")
    cur.execute("CREATE TABLE IF NOT EXISTS adjustments(ID, PlayerName, CharacterName, KarmaAdjust, XpAdjust, "
                "GoldAdjust, Comment, PRIMARY KEY(ID))")


def get_player(name):
    cur.execute("""
        SELECT PlayerName FROM players WHERE PlayerName = ?
    """, (name, ))
    return cur.fetchone()


def add_player(name, enterer, starting_karma: int = 0, starting_xp: float = 0.0):
    if get_player(name) is not None:
        print("Player already exists " + name)
        return False

    print("Adding Character " + name)

    cur.execute("""
        INSERT INTO players VALUES
        (?, ?, '', ?, '', ?)
    """, (name, starting_karma, starting_xp, enterer))
    con.commit()


def add_xp_to_player(name, xp: float):
    pl = get_player(name)
    if pl is None:
        print("Player does not exist " + name)
        return False
    cur.execute("""
            SELECT BonusXP FROM players WHERE PlayerName = ? 
        """, (name,))
    existing_xp = cur.fetchone()[0]
    new_xp = existing_xp + xp
    cur.execute("""
            UPDATE players SET BonusXP = ? where PlayerName = ?
    """, (new_xp, name))
    con.commit()


def get_character(player_name, name):
    cur.execute("""
        SELECT PlayerName FROM characters WHERE PlayerName = ? and Name = ?
    """, (player_name, name))
    return cur.fetchone()


def add_character(player_name, enterer, name, ancestry, background, pc_class, heritage, pathbuilder, home='',
                  starting_xp: float = 0.0):
    if get_player(player_name) is None:
        print("Player does not exist " + player_name)
        return False

    if get_character(player_name, name) is not None:
        print("PC already exists with name " + name + " on player: " + player_name)
        return False

    print("Adding PC " + name)
    cur.execute("""
            INSERT INTO characters VALUES
            (?, ?, ?, ?, ?, ?, '', '', ?, ?, '', '', '', '', ?, 0, 0, '', '', '', '', '', '', '', '', ?)
        """, (player_name, name, ancestry, background, pc_class, heritage, home, pathbuilder, starting_xp, enterer))
    con.commit()


def add_game(name, date, time, items: list[ett.Pf2eElement], players: list[ett.EttPlayer], enterer):
    id = uuid.uuid4()
    game_level = ett.ett_party_level(players)
    items_text = ett.pf2e_element_list_to_string(items)
    cur.execute("""
            INSERT INTO games VALUES
            (?, ?, ?, ?, ?, ?, ?)
        """, (id, name, date, enterer, time, game_level, items_text))
    for pl in players:
        if pl.player_level == 0:
            add_xp_to_player(pl.player_name, pl.time_played * 1.5)
        else:
            cur.execute("""
                SELECT XP, ExpectedGold, CurrentGold from characters WHERE PlayerName = ? and Name = ?
            """, (pl.player_name, pl.name))
            pl_stats = cur.fetchone()
            # This means the player is invalid
            if pl_stats is None:
                continue
            expected_level = (pl_stats[0] / 12) + 1
            tt_up = (expected_level < pl.player_level)
            cur.execute("""
                INSERT INTO gamePlayers VALUES
                (?, ?, ?, ?, ?, ?, ?)
            """, (id, pl.player_name, pl.name, pl.player_level, pl.time_played, tt_up, pl.gained_karma))
            if not pl_stats[1]:
                pl_stats[1] = 0
            if not pl_stats[2]:
                pl_stats[2] = 0
            # add gold
            xp_added = ett.ett_xp_rate(pl.player_level, game_level) * pl.time_played
            adventure_gold = ett.ett_gold_add_xp(pl_stats[0], xp_added)
            total_xp = xp_added + pl_stats[0]
            expected_gold = adventure_gold + pl_stats[1]
            current_gold = adventure_gold + pl_stats[2]
            # Update the player with the new game information
            cur.execute("""
                UPDATE characters SET XP = ?, ExpectedGold = ?, CurrentGold = ? where PlayerName = ? and Name = ?
            """, (total_xp, expected_gold, current_gold, pl.player_name, pl.name))
            con.commit()
