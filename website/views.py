from flask import Blueprint, render_template, request, redirect, flash
from flask_login import current_user, login_required
from src import database, ett
from src.database import CHARACTERS, PLAYERS
views = Blueprint('views', __name__)


@views.route('/players')
def players():
    pl = database.get_table("Players", "PlayerName", 0, 15)
    return render_template("players.html", user=current_user, players=pl)


@views.route('/add_player', methods=['GET'])
@login_required
def add_player():
    return render_template("add_player.html", user=current_user)


@views.route('/add_player', methods=['POST'])
@login_required
def add_player_post():
    data = request.form
    discord = data.get('discord')
    karma = data.get('karma')
    if karma == '':
        # Per Ghost Yuki you start with 1 karma
        karma = 1
    else:
        karma = int(karma)
    xp = data.get('xp')
    if xp == '':
        xp = 0
    else:
        xp = float(xp)
    database.add_player(data.get('playerName'), current_user.name, karma, xp, discord)
    return redirect('/players')


@views.route('/view_player', methods=['POST', 'GET'])
def view_player():
    # Do not handle get requests at all.
    if request.method == 'GET':
        return redirect("/players")
    player = database.get_player(request.form.get("PlayerName"))
    if not player:
        flash("API ERROR viewing player: " + request.form.get("PlayerName"), "error")
        return redirect("/players")
    player = list(player)
    player[PLAYERS.BonusXP] = round(player[PLAYERS.BonusXP], 2)
    upgrades = ett.string_to_pf2e_element_list(player[PLAYERS.Upgrades])
    chars = database.string_list_to_list(player[PLAYERS.Characters])
    char_num = len(chars)
    max_chars = ett.get_available_slots(player[PLAYERS.Upgrades], [])
    extra = (upgrades, chars, char_num, max_chars)
    return render_template("view_player.html", user=current_user, p=player, e=extra)


@views.route('/edit_player', methods=['POST', 'GET'])
@login_required
def edit_player():
    # Do not handle get requests at all.
    if request.method == 'GET':
        return redirect("/players")
    player = database.get_player(request.form.get("PlayerName"))
    if not player:
        flash("API ERROR viewing player: " + request.form.get("PlayerName"), "error")
        return redirect("/players")
    player = list(player)
    player[PLAYERS.BonusXP] = round(player[PLAYERS.BonusXP], 2)
    danger = bool(request.form.get("danger"))
    player = database.get_player(request.form.get("PlayerName"))
    my_chars = database.string_list_to_list(player[PLAYERS.Characters])
    karma = ett.string_to_pf2e_element_list(player[PLAYERS.Upgrades])
    ch = database.get_table("Characters", ["PlayerName", "Name"])
    formatted_ch = []
    for i in ch:
        tab = [i[0], i[1]]
        formatted_ch.append(tab)
    return render_template("edit_player.html", user=current_user, my_chars=my_chars,
                           p=player, ch=formatted_ch, karma=karma, danger=danger)


# This is the most important screen so it should take priority.
@views.route('/')
@views.route('/characters')
def characters():
    ch = database.get_table("Characters", ["PlayerName", "Name"], 0, 15)
    return render_template("characters.html", user=current_user, characters=ch)


@views.route('/view_character', methods=['POST', 'GET'])
def view_character():
    # Do not handle get requests at all.
    if request.method == 'GET':
        return redirect("/characters")
    character = database.get_character(request.form.get("PlayerName"), request.form.get("Name"))
    player = database.get_player(request.form.get("PlayerName"))
    if not player or not character:
        flash("API ERROR viewing player,char: " + request.form.get("PlayerName") + request.form.get("Name"), "error")
        return redirect("/characters")
    character = list(character)
    karma = player[PLAYERS.Karma]
    total_rares = 1
    rewards = ett.string_to_pf2e_element_list(character[CHARACTERS.Rewards])
    unlocks = ett.string_to_pf2e_element_list(character[CHARACTERS.Unlocks])
    inventory = ett.string_to_pf2e_element_list(character[CHARACTERS.Items])
    # Round to fix html problems
    character[CHARACTERS.ExpectedGold] = round(character[CHARACTERS.ExpectedGold], 2)
    character[CHARACTERS.CurrentGold] = round(character[CHARACTERS.CurrentGold], 2)
    character[CHARACTERS.XP] = round(character[CHARACTERS.XP], 2)
    for i in rewards:
        if i.name == "Skeleton Key":
            total_rares += i.quantity
    rare_unlocks = ett.string_to_pf2e_element_list(character[CHARACTERS.Rares])
    extra = (ett.get_level(character[CHARACTERS.XP]), rare_unlocks, len(rare_unlocks),
             total_rares, rewards, karma, ett.KARMA_REWARDS, unlocks, inventory, rare_unlocks)
    fvtts = database.string_list_to_list(character[CHARACTERS.FVTTs])
    if len(fvtts) != 20:
        fvtts = 20 * ['']
    pdfs = database.string_list_to_list(character[CHARACTERS.PDFs])
    if len(pdfs) != 20:
        pdfs = 20 * ['']

    return render_template("view_character.html", user=current_user, c=character, e=extra,
                           p=pdfs, f=fvtts)


@views.route('/edit_character', methods=['POST', 'GET'])
@login_required
def edit_character():
    # Do not handle get requests at all.
    if request.method == 'GET':
        return redirect("/characters")
    pl = database.get_table("Players", "PlayerName")
    character = database.get_character(request.form.get("PlayerName"), request.form.get("Name"))
    player = database.get_player(request.form.get("PlayerName"))
    if not player or not character:
        flash("API ERROR editing player,char: " + request.form.get("PlayerName") + request.form.get("Name"), "error")
        return redirect("/characters")
    character = list(character)
    danger = bool(request.form.get("danger"))
    karma = player[PLAYERS.Karma]

    total_rares = 1
    rewards = ett.string_to_pf2e_element_list(character[CHARACTERS.Rewards])
    unlocks = ett.string_to_pf2e_element_list(character[CHARACTERS.Unlocks])
    inventory = ett.string_to_pf2e_element_list(character[CHARACTERS.Items])
    # Round to fix html problems
    character[CHARACTERS.ExpectedGold] = round(character[CHARACTERS.ExpectedGold], 2)
    character[CHARACTERS.CurrentGold] = round(character[CHARACTERS.CurrentGold], 2)
    character[CHARACTERS.XP] = round(character[CHARACTERS.XP], 2)
    for i in rewards:
        if i.name == "Skeleton Key":
            total_rares += i.quantity
    rare_unlocks = ett.string_to_pf2e_element_list(character[CHARACTERS.Rares])
    extra = (ett.get_level(character[CHARACTERS.XP]), rare_unlocks, len(rare_unlocks),
             total_rares, rewards, karma, ett.KARMA_REWARDS, unlocks, inventory, rare_unlocks)

    return render_template("edit_character.html", user=current_user, players=pl, c=character, e=extra, danger=danger)


@views.route('/add_character')
@login_required
def add_character():
    pl = database.get_table("Players", "PlayerName")
    return render_template("add_character.html", user=current_user, players=pl)


@views.route('/add_character', methods=['POST'])
@login_required
def add_character_post():
    print(request.form)
    data = request.form
    region = data.get('home')
    if not region:
        region = 'Tavern Region'
    xp = data.get('xp')
    if xp == '':
        xp = 0
    else:
        xp = float(xp)
    err = database.add_character(data.get("playerName"), current_user.name, data.get("name"), data.get("ancestry"),
                                 data.get("background"), data.get("class"), data.get("heritage"),
                                 data.get("pathbuilder"), int(data.get("ironman")), region, xp,
                                 data.get("subclass"), data.get("discord"), data.get("picture"))
    if err:
        flash("ERROR ADDING CHARACTER: " + err, "error")
    return redirect('/characters')


@views.route('/adventures')
def adventures():
    adv = database.get_table("Games", "Date", 0, 15)
    return render_template("/adventures.html", user=current_user, adventures=adv)


@views.route('/add_adventure')
@login_required
def add_adventure():
    pl = database.get_table("Players", "PlayerName")
    ch = database.get_table("Characters", ["PlayerName", "Name"])
    formatted_ch = []
    for i in ch:
        tab = [i[0], i[1]]
        formatted_ch.append(tab)

    return render_template("add_adventure.html", user=current_user, players=pl, characters=formatted_ch)


def parse_button(button: list):
    output_button = []
    it = iter(range(len(button)))
    for i in it:
        if button[i]:
            output_button += [1]
            next(it)
        else:
            output_button += [0]
    return output_button


@views.route('/add_adventure', methods=['POST'])
@views.route('/add_adventure_submit', methods=['POST'], endpoint='add_adventure_submit')
@login_required
def add_adventure_post():
    print(request.form)
    items = []
    items_name = request.form.getlist('items[][name]')
    items_level = request.form.getlist('items[][level]')
    items_rarity = request.form.getlist('items[][rarity]')
    items_num = request.form.get('itemsNr')
    if not items_num:
        items_num = 0
    else:
        items_num = int(items_num)

    players_num = int(request.form.get('playersNr'))
    for i in range(0, items_num):
        itm = ett.Pf2eElement(items_name[i], int(items_level[i]), 0, int(items_rarity[i]))
        items += [itm]

    gm_player_name = request.form.get('gm')
    gm_game_time = float(request.form.get('time'))

    player_list = [ett.EttGamePlayer(gm_player_name, '', 0, gm_game_time, 0, True)]
    player_names = request.form.getlist('players[][name]')
    player_levels = request.form.getlist('players[][level]')
    player_times = request.form.getlist('players[][time]')
    print("karma list is ", request.form.getlist('players[][karma]', int))
    player_karma = parse_button(request.form.getlist('players[][karma]', int))
    print("player karma is ", player_karma)
    player_tt = parse_button(request.form.getlist('players[][ttcost]', int))
    total_karma = [x - y for x, y in zip(player_karma, player_tt)]
    player_died = parse_button(request.form.getlist('players[][died]', int))
    print("Karma gained + died is ", total_karma, player_died)
    for i in range(0, players_num):
        pl_name = player_names[i]
        pl_name_split = pl_name.split("|", 1)
        pl = ett.EttGamePlayer(pl_name_split[0], pl_name_split[1], int(player_levels[i]),
                               float(player_times[i]), int(total_karma[i]), not bool(player_died[i]))
        player_list += [pl]

    game_name = request.form.get('gameName')
    game_length = float(request.form.get('time'))
    game_date = request.form.get('date')
    game_comments = request.form.get('comments')
    if bool(request.form.get('submitonly')):
        submit_only = 2
    else:
        submit_only = 0

    if request.endpoint == 'views.add_adventure_submit':
        err = database.add_game(game_name, game_date, game_length, items,
                                player_list, game_comments, current_user.name, submit_only)
        if err is not None:
            flash("API ERROR: " + err, "error")

        return redirect('/adventures')
    else:
        return database.add_game(game_name, game_date, game_length, items,
                                 player_list, game_comments, current_user.name, 1)


@views.route('/edit_adventure', methods=['POST', 'GET'])
@login_required
def edit_adventure():
    # Do not handle get requests at all.
    if request.method == 'GET':
        return redirect("/adventures")
    pl = database.get_table("Players", "PlayerName")
    danger = bool(request.form.get("danger"))
    name = request.form.get("Name")
    date = request.form.get("date")
    adventure = database.get_game(name, date)
    return render_template("edit_adventure.html", user=current_user, players=pl, a=adventure, danger=danger)
