import math

from flask import Blueprint, render_template, request, redirect
from flask_login import current_user, login_required
from src import database, ett
views = Blueprint('views', __name__)
from src.database import CHARACTERS, PLAYERS


@views.route('/')
def home():
    return render_template("home.html", user=current_user)


@views.route('/players')
def players():
    pl = database.get_table("Players", "PlayerName", 0, 15)
    print(pl)
    return render_template("players.html", user=current_user, players=pl)


@views.route('/add_player', methods=['GET'])
@login_required
def add_player():
    return render_template("add_player.html", user=current_user)


@views.route('/add_player', methods=['POST'])
@login_required
def add_player_post():
    print(request.form)
    data = request.form
    karma = data.get('karma')
    if karma == '':
        karma = 0
    else:
        karma = int(karma)
    xp = data.get('xp')
    if xp == '':
        xp = 0
    else:
        xp = float(xp)
    database.add_player(data.get('playerName'), current_user.name, karma, xp)
    return redirect('/players')


@views.route('/characters')
def characters():
    ch = database.get_table("Characters", ["PlayerName", "Name"], 0, 15)
    print(ch)
    return render_template("characters.html", user=current_user, characters=ch)


@views.route('/edit_character', methods=['POST'])
@login_required
def edit_character():
    pl = database.get_table("Players", "PlayerName")
    character = database.get_character(request.form.get("PlayerName"), request.form.get("Name"))
    player = database.get_player(request.form.get("PlayerName"))
    karma = player[PLAYERS.Karma]

    print(character)
    total_rares = 1
    rewards = ett.string_to_pf2e_element_list(character[CHARACTERS.Rewards])
    unlocks = ett.string_to_pf2e_element_list(character[CHARACTERS.Unlocks])
    inventory = ett.string_to_pf2e_element_list(character[CHARACTERS.Items])
    for i in rewards:
        if i.name == "Skeleton Key":
            total_rares += i.quantity
    rare_unlocks = ett.string_to_pf2e_element_list(character[CHARACTERS.Rares])
    extra = (ett.get_level(CHARACTERS.XP), rare_unlocks, len(rare_unlocks),
             total_rares, rewards, karma, ett.KARMA_REWARDS, unlocks, inventory)
    return render_template("edit_character.html", user=current_user, players=pl, c=character, e=extra)


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
    xp = data.get('xp')
    if xp == '':
        xp = 0
    else:
        xp = float(xp)
    database.add_character(data.get("playerName"), current_user.name, data.get("name"), data.get("ancestry"),
                           data.get("background"), data.get("class"), data.get("heritage"),
                           data.get("pathbuilder"), int(data.get("ironman")), data.get("home"), xp)
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
    print(formatted_ch)

    return render_template("add_adventure.html", user=current_user, players=pl, characters=formatted_ch)


@views.route('/add_adventure', methods=['POST'])
@login_required
def add_adventure_post():
    print(request.form)
    data = request.form
    items = []
    items_name = request.form.getlist('items[][name]')
    items_level = request.form.getlist('items[][level]')
    items_cost = request.form.getlist('items[][cost]')
    items_rarity = request.form.getlist('items[][rarity]')
    items_num = request.form.get('itemsNr')
    if not items_num:
        items_num = 0
    else:
        items_num = int(items_num)

    players_num = int(request.form.get('playersNr'))
    for i in range(0, items_num):
        itm = ett.Pf2eElement(items_name[i], int(items_level[i]), float(items_cost[i]), int(items_rarity[i]))
        items += [itm]

    gm_player_name = request.form.get('gm')
    gm_game_time = float(request.form.get('time'))
    gm_karma_gain = request.form.get('gmKarma')
    if not gm_karma_gain:
        gm_karma_gain = 0
    else:
        gm_karma_gain = int(gm_karma_gain)

    player_list = [ett.EttGamePlayer(gm_player_name, '', 0, gm_game_time, gm_karma_gain, True)]
    player_names = request.form.getlist('players[][name]')
    player_levels = request.form.getlist('players[][level]')
    player_times = request.form.getlist('players[][time]')
    player_karma = request.form.getlist('players[][karma]')
    player_died = request.form.getlist('players[][died]')
    for i in range(0, players_num):
        pl_name = player_names[i]
        pl_name_split = pl_name.split("|", 1)
        pl = ett.EttGamePlayer(pl_name_split[0], pl_name_split[1], int(player_levels[i]),
                               float(player_times[i]), int(player_karma[i]), player_died[i] != 'X')
        player_list += [pl]

    game_name = request.form.get('gameName')
    game_length = float(request.form.get('time'))
    game_date = request.form.get('date')
    game_continuation = (request.form.get('continuation') is not None)
    game_comments = request.form.get('comments')

    database.add_game(game_name, game_date, game_length, items,
                      player_list, game_continuation, game_comments, current_user.name)

    return redirect('/adventures')
