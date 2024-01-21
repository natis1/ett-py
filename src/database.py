import dataclasses
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
    Upgrades = 3
    Enterer = 4
    DiscordIntro = 5
    NrGames = 6
    Hours = 7


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
    PDFs = 11
    FVTTs = 12
    Games = 13
    Enterer = 14
    Subclass = 15
    DiscordLink = 16
    Picture = 17
    NrGames = 18
    Archetype = 19
    Hours = 20


class GAMES(IntEnum):
    ID = 0
    Name = 1
    Date = 2
    Enterer = 3
    Time = 4
    GameLevel = 5
    GM = 6


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
    KarmaAdjust = 6
    Unlocks = 7
    Rewards = 8
    Comment = 9


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


SAFE_PLAYER_COLUMNS = ['PlayerName', 'Karma', 'Characters', 'Upgrades', 'Enterer', 'NrGames', 'Hours'
                       'PlayerName desc', 'Karma desc', 'Characters desc',
                       'Upgrades desc', 'Enterer desc', 'NrGames desc', 'Hours desc']
SAFE_CHARACTER_COLUMNS = ['PlayerName', 'Name', 'Ancestry', 'Background', 'Class', 'Heritage',
                          'Unlocks', 'Rewards', 'Home', 'Enterer', 'NrGames', 'Hours',
                          'PlayerName desc', 'Name desc', 'Ancestry desc',
                          'Background desc', 'Class desc',
                          'Heritage desc', 'Unlocks desc', 'Rewards desc', 'Home desc',
                          'Enterer desc', 'Subclass', 'Subclass desc', 'NrGames desc', 'Hours desc']
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

    if limit != 0:
        qry += f' LIMIT {limit}'

    if offset != 0:
        qry += f' OFFSET {offset}'

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
        count = sql_exec("SELECT COUNT(*) FROM players", None, Fetch.ONE)
        if search == "!PLACEHOLDER":
            total = 1
            page = sql_exec("SELECT * FROM players WHERE PlayerName = '!PLACEHOLDER' " + qry, None, Fetch.ALL)
        else:
            total = sql_exec("SELECT COUNT(*) FROM players WHERE PlayerName != '!PLACEHOLDER' and PlayerName LIKE ?"
                             , ('%' + search + '%',), Fetch.ONE)
            page = sql_exec("SELECT * FROM players WHERE PlayerName != '!PLACEHOLDER' and PlayerName LIKE ? " + qry
                            , ('%' + search + '%',), Fetch.ALL)
        return count, total, page
    else:
        total = sql_exec("SELECT COUNT(*) FROM players WHERE PlayerName != '!PLACEHOLDER'", None, Fetch.ONE)
        page = sql_exec("SELECT * FROM players WHERE PlayerName != '!PLACEHOLDER'" + qry, None, Fetch.ALL)
        return total, total, page


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
        count = sql_exec("SELECT COUNT(*) FROM characters", None, Fetch.ONE)
        if search == "!PLACEHOLDER":
            total = 1
            page = sql_exec("SELECT * FROM characters WHERE PlayerName = '!PLACEHOLDER'", None, Fetch.ALL)
        else:
            s = '%' + search + '%'
            total = sql_exec("SELECT COUNT(*) FROM characters WHERE PlayerName != '!PLACEHOLDER' AND "
                             "PlayerName LIKE ? or Subclass LIKE ? or Name LIKE ? or Ancestry LIKE ? "
                             "or Class LIKE ? ",
                             (s, s, s, s, s), Fetch.ONE)
            page = sql_exec("SELECT * FROM characters WHERE PlayerName != '!PLACEHOLDER' AND "
                            "PlayerName LIKE ? or Subclass LIKE ? or Name LIKE ? or Ancestry LIKE ? "
                            "or Class LIKE ? " + qry,
                            (s, s, s, s, s), Fetch.ALL)
        return count, total, page
    else:
        total = sql_exec("SELECT COUNT(*) FROM characters WHERE PlayerName != '!PLACEHOLDER'", None, Fetch.ONE)
        page = sql_exec("SELECT * FROM characters WHERE PlayerName != '!PLACEHOLDER' " + qry, None, Fetch.ALL)
        return total, total, page


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
        count = sql_exec("SELECT COUNT(*) FROM games", None, Fetch.ONE)
        s = '%' + search + '%'
        total = sql_exec("SELECT COUNT(*) FROM games WHERE "
                         "Name LIKE ? or Date LIKE ? or GameLevel LIKE ? or GM LIKE ? ",
                         (s, s, s, s), Fetch.ONE)
        page = sql_exec("SELECT * FROM games WHERE "
                        "Name LIKE ? or Date LIKE ? or GameLevel LIKE ? or GM LIKE ? " + qry,
                        (s, s, s, s), Fetch.ALL)
        return count, total, page
    else:
        total = sql_exec("SELECT COUNT(*) FROM games ", None, Fetch.ONE)
        page = sql_exec("SELECT * FROM games " + qry, None, Fetch.ALL)
        return total, total, page


# This not only reindexes but also CLEANS and FIXES any BUGS in ur table
def reindex():
    ch = sql_exec("SELECT * FROM characters", None, Fetch.ALL)
    for i in ch:
        i = list(i)
        p = sql_exec("SELECT * FROM players WHERE PlayerName = ?", (i[CHARACTERS.PlayerName],), Fetch.ONE)
        # Player does not exist. Delete character
        if not p:
            print("WARNING: DELETING INVALID CHARACTER TIED TO MISSING PLAYER: ", i[CHARACTERS.PlayerName])
            sql_exec("DELETE FROM characters WHERE PlayerName = ? and Name = ?",
                     (i[CHARACTERS.PlayerName], i[CHARACTERS.Name]))
            continue

        # Reindex games
        games = sql_exec("SELECT * FROM events WHERE PlayerName = ? and CharacterName = ? and RelatedID != ''",
                         (i[CHARACTERS.Name], i[CHARACTERS.Name]), Fetch.ALL)
        games_list = []
        for j in games:
            games_list += [j[EVENTS.RelatedID]]

        existing_games = string_list_to_list(i[CHARACTERS.Games])
        games_list += existing_games
        deduplicated = list(set(games_list))
        ch_hours = 0
        for j in deduplicated:
            game = sql_exec("SELECT * FROM games WHERE ID = ?", (j,), Fetch.ONE)
            ch_hours += game[GAMES.Time]

        i[CHARACTERS.Games] = list_to_string(deduplicated)
        i[CHARACTERS.NrGames] = len(deduplicated)
        i[CHARACTERS.Hours] = ch_hours
        print("Character: " + i[CHARACTERS.Name] + " has: " + str(ch_hours) + " hours logged in games.")
        edit_character(i)

    # Clean up invalid characters
    pl = sql_exec("SELECT * FROM players", None, Fetch.ALL)
    for i in pl:
        i = list(i)
        nr_games = 0
        chars = sql_exec("SELECT * FROM characters WHERE PlayerName = ?", (i[PLAYERS.PlayerName],), Fetch.ALL)
        char_list = []
        ch_hours = 0
        for j in chars:
            char_list += [j[CHARACTERS.Name]]
            nr_games += j[CHARACTERS.NrGames]
            ch_hours += j[CHARACTERS.Hours]

        gm_games = sql_exec("SELECT * FROM events WHERE PlayerName = ? and CharacterName = '' and RelatedID != '' ",
                            (i[PLAYERS.PlayerName], ), Fetch.ALL)
        gm_hours = 0
        for j in gm_games:
            game = sql_exec("SELECT * FROM games WHERE ID = ?", (j[EVENTS.RelatedID], ), Fetch.ONE)
            gm_hours += game[GAMES.Time]

        gm_games_ct = len(list(gm_games))
        print("GM: " + i[PLAYERS.PlayerName] +
              " has: " + str(nr_games) + " games on their chars and "
              + str(gm_games_ct) + " gm games.")

        i[PLAYERS.Characters] = list_to_string(char_list)
        i[PLAYERS.NrGames] = nr_games + gm_games_ct
        i[PLAYERS.Hours] = gm_hours + ch_hours
        edit_player(i)
    sql_exec("VACUUM")


def init_db():
    user_version = sql_exec("PRAGMA user_version", (), Fetch.ONE)[0]
    print("Setting up database, current version is ", user_version)
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

    # V1, add subclass field
    if user_version < 1:
        sql_exec("ALTER TABLE characters ADD COLUMN Subclass")
        sql_exec("ALTER TABLE characters ADD COLUMN DiscordLink")
        sql_exec("ALTER TABLE characters ADD COLUMN Picture")
        sql_exec("ALTER TABLE players ADD COLUMN DiscordIntro")
        sql_exec("PRAGMA user_version = 1")

    # V2, collate nocase
    if user_version < 2:
        sql_exec("ALTER TABLE characters RENAME TO characters_V1")
        sql_exec("ALTER TABLE players RENAME TO players_V1")
        sql_exec("ALTER TABLE games RENAME TO games_V1")
        sql_exec("CREATE TABLE IF NOT EXISTS players(PlayerName COLLATE NOCASE, Karma, Characters, BonusXP, Upgrades, "
                 "Enterer, DiscordIntro, PRIMARY KEY(PlayerName))")
        sql_exec("CREATE TABLE IF NOT EXISTS characters(PlayerName COLLATE NOCASE, Name COLLATE NOCASE, Ancestry,"
                 "Background, Class, Heritage, Unlocks, Rewards, Home, Pathbuilder, Comments, CommunityService, "
                 "PDFs, FVTTs, XP, ExpectedGold, CurrentGold, Games, Items, Rares, Ironman, Enterer, Subclass, "
                 "DiscordLink, Picture, PRIMARY KEY(PlayerName, Name))")
        sql_exec(
            "CREATE TABLE IF NOT EXISTS games(ID, Name COLLATE NOCASE, Date, Enterer, Time, "
            "GameLevel, Items, GM, PRIMARY KEY(ID))")
        # This also clears any dupes
        sql_exec("INSERT OR IGNORE INTO players SELECT * FROM players_V1")
        sql_exec("INSERT OR IGNORE INTO characters SELECT * FROM characters_V1")
        sql_exec("INSERT OR IGNORE INTO games SELECT * FROM games_V1")
        sql_exec("DROP TABLE players_V1")
        sql_exec("DROP TABLE characters_V1")
        sql_exec("DROP TABLE games_V1")
        sql_exec("PRAGMA user_version = 2")
        # Once every update is done, reindex to clean up bad data.
        reindex()

    # V3 - remove fvtt and pdf urls for each level, switching to "canonical" ones:
    if user_version < 3:
        sql_exec("UPDATE characters SET FVTTs = '' WHERE FVTTs LIKE '%\n%'")
        sql_exec("UPDATE characters SET PDFs = '' WHERE FVTTs LIKE '%\n%'")
        sql_exec("PRAGMA user_version = 3")

    # V4 - remove xp, count games by raw number
    if user_version < 4:
        sql_exec("ALTER TABLE characters RENAME TO characters_V3")
        sql_exec("ALTER TABLE players RENAME TO players_V3")
        sql_exec("ALTER TABLE games RENAME TO games_V3")
        sql_exec("ALTER TABLE events RENAME TO events_V3")

        sql_exec("CREATE TABLE IF NOT EXISTS players(PlayerName COLLATE NOCASE, Karma, Characters, Upgrades, "
                 "Enterer, DiscordIntro, NrGames, PRIMARY KEY(PlayerName))")
        sql_exec("CREATE TABLE IF NOT EXISTS characters(PlayerName COLLATE NOCASE, Name COLLATE NOCASE, Ancestry, "
                 "Background, Class, Heritage, Unlocks, Rewards, Home, Pathbuilder, Comments, "
                 "PDFs, FVTTs, Games, Enterer, Subclass, "
                 "DiscordLink, Picture, NrGames, PRIMARY KEY(PlayerName, Name))")
        sql_exec(
            "CREATE TABLE IF NOT EXISTS games(ID, Name COLLATE NOCASE, Date, Enterer, Time, "
            "GameLevel, GM, PRIMARY KEY(ID))")
        sql_exec(
            "CREATE TABLE IF NOT EXISTS events(ID, RelatedID, TimeStamp, PlayerName, CharacterName, EventDate, "
            "KarmaAdjust, Unlocks, Rewards, Comment, PRIMARY KEY(ID))")
        # This also clears any dupes
        sql_exec("INSERT OR IGNORE INTO players(PlayerName, Karma, Characters, "
                 "Upgrades, Enterer, DiscordIntro)"
                 " SELECT PlayerName, Karma, Characters, "
                 "Upgrades, Enterer, DiscordIntro FROM players_V3")
        sql_exec("INSERT OR IGNORE INTO characters(PlayerName, Name, "
                 "Ancestry, Background, Class, Heritage, Unlocks, Rewards, "
                 "Home, Pathbuilder, Comments, PDFs, FVTTs, Games, Enterer, "
                 "Subclass, DiscordLink, Picture) SELECT PlayerName, Name, "
                 "Ancestry, Background, Class, Heritage, Unlocks, Rewards, "
                 "Home, Pathbuilder, Comments, PDFs, FVTTs, Games, Enterer, "
                 "Subclass, DiscordLink, Picture FROM characters_V3")
        sql_exec("INSERT OR IGNORE INTO games SELECT ID, Name, Date, Enterer, "
                 "Time, GameLevel, GM FROM games_V3")
        sql_exec("INSERT OR IGNORE INTO events(ID, RelatedID, TimeStamp, "
                 "PlayerName, CharacterName, EventDate, KarmaAdjust, Unlocks, "
                 "Rewards, Comment) SELECT ID, RelatedID, TimeStamp, "
                 "PlayerName, CharacterName, EventDate, KarmaAdjust, Unlocks, "
                 "Rewards, Comment FROM events_V3")

        sql_exec("DROP TABLE players_V3")
        sql_exec("DROP TABLE characters_V3")
        sql_exec("DROP TABLE games_V3")
        sql_exec("DROP TABLE events_V3")
        # Reindex required to build nr games list
        reindex()
        sql_exec("PRAGMA user_version = 4")

    # V5, add hours to players and characters, and archetype to characters
    if user_version < 5:
        sql_exec("ALTER TABLE characters RENAME TO characters_V4")
        sql_exec("ALTER TABLE players RENAME TO players_V4")
        sql_exec("CREATE TABLE IF NOT EXISTS players(PlayerName COLLATE NOCASE, Karma, Characters, Upgrades, "
                 "Enterer, DiscordIntro, NrGames, Hours, PRIMARY KEY(PlayerName))")
        sql_exec("CREATE TABLE IF NOT EXISTS characters(PlayerName COLLATE NOCASE, Name COLLATE NOCASE, Ancestry, "
                 "Background, Class, Heritage, Unlocks, Rewards, Home, Pathbuilder, Comments, "
                 "PDFs, FVTTs, Games, Enterer, Subclass, "
                 "DiscordLink, Picture, NrGames, Archetype, Hours, PRIMARY KEY(PlayerName, Name))")
        sql_exec("INSERT OR IGNORE INTO players(PlayerName, Karma, Characters, "
                 "Upgrades, Enterer, DiscordIntro, NrGames)"
                 " SELECT PlayerName, Karma, Characters, "
                 "Upgrades, Enterer, DiscordIntro, NrGames FROM players_V4")
        sql_exec("INSERT OR IGNORE INTO characters(PlayerName, Name, "
                 "Ancestry, Background, Class, Heritage, Unlocks, Rewards, "
                 "Home, Pathbuilder, Comments, PDFs, FVTTs, Games, Enterer, "
                 "Subclass, DiscordLink, Picture, NrGames) SELECT PlayerName, Name, "
                 "Ancestry, Background, Class, Heritage, Unlocks, Rewards, "
                 "Home, Pathbuilder, Comments, PDFs, FVTTs, Games, Enterer, "
                 "Subclass, DiscordLink, Picture, NrGames FROM characters_V4")
        sql_exec("DROP TABLE players_V4")
        sql_exec("DROP TABLE characters_V4")
        # Reindex required to calculate hours from games played.
        reindex()
        sql_exec("PRAGMA user_version = 5")



def get_player(name):
    return sql_exec("""
        SELECT * FROM players WHERE PlayerName = ?
    """, (name,), Fetch.ONE)


def add_player(name, enterer, starting_karma: int = 0, discord: str = ''):
    if get_player(name) is not None:
        print("Player already exists " + name)
        return False

    print("Adding Player " + name)
    sql_exec("""
        INSERT INTO players VALUES
        (?, ?, '', '', ?, ?, 0, 0)
    """, (name, starting_karma, enterer, discord))


def get_character(player_name, name):
    return sql_exec("""
        SELECT * FROM characters WHERE PlayerName = ? and Name = ?
    """, (player_name, name), Fetch.ONE)


def add_character(player_name, enterer, name, ancestry, background, pc_class, heritage, pathbuilder, home='',
                  subclass: str = '', discord_link: str = '', picture: str = '',
                  pdf_url: str = '', fvtt_url: str = '', archetype: str = ''):
    if subclass is None:
        subclass = ''
    p = get_player(player_name)
    if p is None:
        print("Player does not exist " + player_name)
        return "Player does not exist " + player_name
    p = list(p)

    if get_character(player_name, name) is not None:
        print("PC already exists with name " + name + " on player: " + player_name)
        return "PC already exists with name " + name + " on player: " + player_name

    if ett.get_available_slots(p[PLAYERS.Upgrades], string_list_to_list(p[PLAYERS.Characters])) <= 0:
        print("Not enough character slots for PC " + name + " on player: " + player_name)
        return "Not enough character slots for PC " + name + " on player: " + player_name

    # Add character to char list
    chars = string_list_to_list(p[PLAYERS.Characters])
    chars += [name]
    p[PLAYERS.Characters] = list_to_string(chars)
    edit_player(p)

    sql_exec("""
        INSERT INTO characters VALUES
        (?, ?, ?, ?, ?, ?, '', '', ?, ?, '', ?, ?, '', ?, ?, ?, ?, 0, ?, 0)""",
             (player_name, name, ancestry, background, pc_class, heritage, home, pathbuilder,
              pdf_url, fvtt_url, enterer, subclass, discord_link, picture, archetype))


def get_game(name, date):
    return sql_exec("""
        SELECT * FROM games WHERE Name = ? AND Date = ?
    """, (name, date), Fetch.ONE)


@dataclasses.dataclass
class GameChanges:
    player_name: str
    name: str = ''
    karma_change: int = 0
    net_games: int = 0


def add_game(name, date, game_time, players: list[ett.EttGamePlayer],
             comments, enterer, dry_run: int, game_level: int):
    existing_games = sql_exec("""
        SELECT * FROM Games WHERE Name = ? and Date = ?
    """, (name, date), Fetch.ONE)
    if existing_games:
        print("This game is already logged in our DB. Exiting. ")
        return "This game is already logged in our DB. Exiting."
    comments = "GAME PLAYED: " + comments
    timestamp = time.time()
    game_id = str(uuid.uuid4())
    changes = []
    for pl in players:
        # GM player
        if pl.name == '':
            pl.gained_karma = 2
            if dry_run == 0:
                gm = get_player(pl.player_name)
                if gm:
                    gm = list(gm)
                    gm[PLAYERS.Karma] = gm[PLAYERS.Karma] + pl.gained_karma
                    edit_player(gm)
            if dry_run == 0 or dry_run == 2:
                sql_exec("""
                         INSERT INTO games VALUES
                         (?, ?, ?, ?, ?, ?, ?)
                         """, (game_id, name, date, enterer, game_time, game_level, pl.player_name))
                sql_exec("""
                            INSERT INTO events VALUES
                            (?, ?, ?, ?, ?, ?, ?, '', '', ?)
                        """, (
                    str(uuid.uuid4()), game_id, timestamp, pl.player_name, pl.name, date, 1,
                    comments))
            else:
                gm = get_player(pl.player_name)
                if gm:
                    gm = list(gm)
                    changes += [GameChanges(pl.player_name, '', pl.gained_karma, int(gm[PLAYERS.NrGames]) + 1)]

        else:
            character = get_character(pl.player_name, pl.name)
            # This means the PC is invalid
            if not character:
                print("ERROR: Character with player name: " + pl.player_name +
                      " and name: " + pl.name + " does not exist!")
                continue
            character = list(character)

            player = get_player(pl.player_name)
            if not player:
                print("ERROR: Player with name: " + pl.player_name + " does not exist!")
                continue
            player = list(player)
            net_karma = pl.gained_karma
            games = string_list_to_list(character[CHARACTERS.Games])
            games += [game_id]
            nr_games = len(games)
            if nr_games % 3 == 0:
                net_karma += 1

            if dry_run == 2 or dry_run == 0:
                # Add game to player games list. Ensure this transaction commits before even any others.
                # It should always transact to avoid needing to reindex later.
                character[CHARACTERS.Games] = list_to_string(games)
                character[CHARACTERS.NrGames] = nr_games
                edit_character(character)

            if dry_run == 0 or dry_run == 2:
                sql_exec("""
                    INSERT INTO events VALUES
                    (?, ?, ?, ?, ?, ?, ?, '', '', ?)
                    """, (str(uuid.uuid4()), game_id, timestamp, pl.player_name, pl.name, date, net_karma,
                          comments))
            else:
                changes += [GameChanges(pl.player_name, pl.name, net_karma, nr_games)]
            if dry_run == 0:
                player[PLAYERS.Karma] = int(player[PLAYERS.Karma]) + int(net_karma)
                edit_player(player)
                edit_character(character)
    if dry_run == 1:
        return changes


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
    sql_exec("""UPDATE players SET Karma = ?, Characters = ?,
    Upgrades = ?, Enterer = ?, DiscordIntro = ?, NrGames = ?, Hours = ?
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
        Unlocks = ?, Rewards = ?, Home = ?, Pathbuilder = ?, Comments = ?,
        PDFs = ?, FVTTs = ?, Games = ?, 
        Enterer = ?, Subclass = ?, DiscordLink = ?, Picture = ?, NrGames = ?, Archetype = ?, Hours = ?
        WHERE PlayerName = ? and Name = ?
    """, tuple(character))


def edit_game(game: list):
    if len(game) != len(GAMES):
        print("INVALID GAME: ", game)
        return "INVALID GAME: " + str(game)

    cur_game = list(get_row("games", "ID", game[GAMES.ID]))

    for i in range(len(game)):
        if game[i] is None or i < 1:
            game[i] = cur_game[i]

    # move ID to the end so that it works
    game = game[1:] + game[:1]
    # Final character Data to write:
    sql_exec("""UPDATE games set Name = ?, Date = ?, Enterer = ?, Time = ?,
    GameLevel = ?, GM = ? WHERE ID = ?
    """, tuple(game))


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


def list_to_string(elements: list):
    e_str = ""
    for element_index in range(len(elements)):
        e_str += elements[element_index]
        e_str += "\n"
        # Since splitlines will always remove the last line if it's blank, you need to include an extra \n at the end.
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
        if i != cur_character[CHARACTERS.Name]:
            new_pc_list += [i]

    cur_player[PLAYERS.Characters] = list_to_string(new_pc_list)

    new_player_pc_list = string_list_to_list(new_player[PLAYERS.Characters])
    new_player_pc_list += [cur_character[CHARACTERS.Name]]
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
        UPDATE characters SET PlayerName = ? WHERE PlayerName = ?
    """, (new_name, old_name))
    sql_exec("""
        UPDATE games SET GM = ? WHERE GM = ?
    """, (new_name, old_name))
    sql_exec("""
        UPDATE players SET PlayerName = ? WHERE PlayerName = ?
    """, (new_name, old_name))


def delete_character(player_name: str, char_name: str):
    pl = get_player(player_name)
    if pl is not None:
        pl = list(pl)
        c = string_list_to_list(pl[PLAYERS.Characters])
        new_list = []
        for i in c:
            if i != char_name:
                new_list += [i]
        pl[PLAYERS.Characters] = list_to_string(c)
        edit_player(pl)
    sql_exec("""
        DELETE FROM characters WHERE PlayerName = ? AND Name = ?
    """, (player_name, char_name))
    sql_exec("""
        DELETE FROM events WHERE PlayerName = ? AND CharacterName = ?
        """, (player_name, char_name))


def delete_player(player_name: str):
    sql_exec("""
        DELETE FROM players WHERE PlayerName = ?
    """, (player_name,))
    sql_exec("""
        DELETE FROM characters WHERE PlayerName = ?
    """, (player_name,))
    sql_exec("""
        DELETE FROM events WHERE PlayerName = ?
    """, (player_name,))


def delete_game(game_id: str):
    sql_exec("""
        DELETE FROM games WHERE ID = ?
    """, (game_id,))
    events = sql_exec("""
        SELECT * FROM events WHERE RelatedID = ?
    """, (game_id,), Fetch.ALL)
    for e in events:
        e_list = list(e)
        char = get_character(e_list[EVENTS.PlayerName], e_list[EVENTS.CharacterName])
        p = get_player(e_list[EVENTS.PlayerName])
        if p:
            p_list = list(p)
            p_list[PLAYERS.NrGames] = int(p_list[PLAYERS.NrGames]) - 1
            edit_player(p)

        if char is None:
            continue
        c_list = list(char)
        games = string_list_to_list(c_list[CHARACTERS.Games])
        new_games = []
        for i in games:
            if i != game_id:
                new_games += [i]
        c_list[CHARACTERS.Games] = list_to_string(new_games)
        c_list[CHARACTERS.NrGames] = int(c_list[CHARACTERS.NrGames]) - 1
        edit_character(c_list)

    sql_exec("""
        DELETE FROM events WHERE RelatedID = ?
    """, (game_id,))
