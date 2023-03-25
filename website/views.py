import math

from flask import Blueprint, render_template, request, redirect
from flask_login import current_user, login_required
from src import database
views = Blueprint('views', __name__)


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
    print(request.form)
    print("Hello Editing Character")
    return render_template("edit_character.html", user=current_user)


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
