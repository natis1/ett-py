# This holds all the database API interaction routes.
# Everything in here is accessed at /api/
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, abort, flash
from flask_login import current_user, login_required
from src import database, ett
from src.database import CHARACTERS, PLAYERS, GAMES
from website import views

api = Blueprint('api', __name__)
API_VERSION = "1"


def api_error():
    flash("ERROR 400 - Invalid POST request to: " + request.path + ".", "error")
    return redirect('/characters')


def get_character():
    player = request.form.get("PlayerName", type=str)
    name = request.form.get("Name", type=str)
    cur_char = database.get_character(player, name)
    if cur_char is None:
        return api_error()
    return list(cur_char)


def get_player():
    player = request.form.get("PlayerName", type=str)
    cur_player = database.get_player(player)
    if cur_player is None:
        return api_error()
    return list(cur_player)


def get_query_data():
    search = request.args.get('search[value]')
    start = request.args.get('start', type=int)
    length = request.args.get('length', type=int)
    order = []
    i = 0
    while True:
        col_index = request.args.get(f'order[{i}][column]')
        if col_index is None:
            break
        col_name = request.args.get(f'columns[{col_index}][data]')
        descending = ' desc' if request.args.get(f'order[{i}][dir]') == 'desc' else ''
        order += [col_name + descending]
        i += 1
    return [order, start, length, search]


@api.route('/characters')
def characters():
    q = get_query_data()
    total, table = database.get_characters_table(q[0], q[1], q[2], q[3])
    print(total, table)
    out_table = []
    for data in table:
        outdict = {'PlayerName': data[0], 'Name': data[1], 'Ancestry': data[2],
                   'Class': data[4], 'XP': round(data[14], 2), 'CurrentGold': round(data[16], 2)}
        out_table += [outdict]

    print(out_table)

    return {
        'data': out_table,
        'recordsFiltered': total,
        'recordsTotal': total,
        'draw': request.args.get('draw', type=int),
    }


@api.route('/players')
def players():
    q = get_query_data()
    total, table = database.get_players_table(q[0], q[1], q[2], q[3])
    print(total, table)
    out_table = []
    for data in table:
        out_dict = {'PlayerName': data[0], 'Karma': data[1]}
        out_table += [out_dict]
    return {
        'data': out_table,
        'recordsFiltered': total,
        'recordsTotal': total,
        'draw': request.args.get('draw', type=int),
    }

@api.route('/adventures')
def adventures():
    q = get_query_data()
    total, table = database.get_games_table(q[0], q[1], q[2], q[3])
    out_table = []
    for data in table:
        out_dict = {'Name': data[1], 'Date': data[2], 'GM': data[7], 'Time': data[4], 'GameLevel': data[5]}
        out_table += [out_dict]
    return {
        'data': out_table,
        'recordsFiltered': total,
        'recordsTotal': total,
        'draw': request.args.get('draw', type=int),
    }


@api.route('/edit_character_names', methods=['POST'])
@login_required
def edit_character_names():
    data = request.form
    pass


@api.route('/edit_character_core', methods=['POST'])
@login_required
def edit_character_core():
    data = request.form
    print(data)
    pass


@api.route('/edit_character_pdfurl', methods=['POST'])
@login_required
def edit_character_pdfurl():
    data = request.form
    print(data)
    pass


@api.route('/edit_character_fvtturl', methods=['POST'])
@login_required
def edit_character_fvtturl():
    data = request.form
    print(data)
    pass


@api.route('/edit_character_pburl', methods=['POST'])
@login_required
def edit_character_pburl():
    data = request.form
    print(data)
    pass


@api.route('/edit_character_karmabuy', methods=['POST'])
@login_required
def edit_character_karmabuy():
    data = request.form
    print(data)
    pass


@api.route('/edit_character_karmaadd', methods=['POST'])
@login_required
def edit_character_karmaadd():
    new_karma = request.form.get("karma")
    if new_karma is None:
        return api_error()
    pl = get_player()
    pl[PLAYERS.Karma] = new_karma
    database.edit
    pass


@api.route('/edit_character_karmaloss', methods=['POST'])
@login_required
def edit_character_karmaloss():
    loss_item = request.form.get("k_unlocks", type=str)
    loss_number = request.form.get("remove_num", type=int)
    if loss_number is None or loss_item is None:
        return api_error()
    cur_char = get_character()
    item = ett.Pf2eElement(loss_item, quantity=loss_number)
    rewards = ett.string_to_pf2e_element_list(cur_char[CHARACTERS.Rewards])
    out_rewards = []
    for r in rewards:
        store_reward = True
        if item.name == r.name:
            # remove all
            if item.quantity >= r.quantity:
                store_reward = False
            else:
                r.quantity -= item.quantity
        if store_reward:
            out_rewards += [r]
    cur_char[CHARACTERS.Rewards] = ett.pf2e_element_list_to_string(out_rewards)
    return database.edit_character(cur_char)


@api.route('/edit_character_buy_item', methods=['POST'])
@login_required
def edit_character_buy_item():
    buy_name = request.form.get("buy_name")
    level = request.form.get("buy_level", type=int)
    cost = request.form.get("buy_cost", type=float)
    rarity = request.form.get("buy_rarity", type=int)
    qty = request.form.get("buy_qty", type=int)
    value_factor = request.form.get("cost_factor", type=float)
    if buy_name is None or level is None or cost is None or qty is None or value_factor is None:
        return api_error()
    cur_char = get_character()
    items = [ett.Pf2eElement(buy_name, level, cost, rarity, qty)]
    err = database.buy_items(cur_char, datetime.today().strftime('%Y-%m-%d'),
                             f"WEB API v{API_VERSION} edit_character_buy_item",
                             items, value_factor)
    if err is not None:
        flash("ERROR: " + err, "error")
    return redirect("/edit_character", code=307)


@api.route('/edit_character_sell_item', methods=['POST'])
@login_required
def edit_character_sell_item():
    item_sold = request.form.get("inventory")
    sell_qty = request.form.get("sell_qty", type=int)
    sell_value = request.form.get("sell_value", type=float)
    if item_sold is None or sell_value is None or sell_qty is None:
        return api_error()
    cur_char = get_character()
    items = [ett.Pf2eElement(item_sold, quantity=sell_qty)]
    err = database.sell_items(cur_char, datetime.today().strftime('%Y-%m-%d'),
                              f"WEB API v{API_VERSION} edit_character_sell_item",
                              items, sell_value)
    if err is not None:
        flash("ERROR: " + err, "error")
    return redirect("/edit_character", code=307)


@api.route('/edit_character_remove_unlock', methods=['POST'])
@login_required
def edit_character_remove_unlock():
    remove_item = request.form.get("i_unlocks", type=str)
    if remove_item is None:
        return api_error()
    cur_char = get_character()
    el = ett.Pf2eElement(remove_item)
    cur_unlocks = ett.string_to_pf2e_element_list(cur_char[CHARACTERS.Unlocks])
    new_unlocks = ett.ett_parse_unlocks(cur_unlocks, [], el, ett.get_level(cur_char[CHARACTERS.XP]))
    cur_char[CHARACTERS.Unlocks] = ett.pf2e_element_list_to_string(new_unlocks)
    err = database.edit_character(cur_char)
    if err is not None:
        flash("ERROR: " + err, "error")
    return redirect("/edit_character", code=307)


@api.route('/edit_character_add_unlock', methods=['POST'])
@login_required
def edit_character_add_unlock():
    name = request.form.get("unlock_name", type=str)
    level = request.form.get("unlock_level", type=int)
    cost = request.form.get("unlock_cost", type=float)
    rarity = request.form.get("unlock_rarity", type=int)
    if name is None or level is None or cost is None or rarity is None:
        return api_error()
    cur_char = get_character()
    el = ett.Pf2eElement(name, level, cost, rarity)
    cur_unlocks = ett.string_to_pf2e_element_list(cur_char[CHARACTERS.Unlocks])
    new_unlocks = ett.ett_parse_unlocks(cur_unlocks, el, [], ett.get_level(cur_char[CHARACTERS.XP]))
    cur_char[CHARACTERS.Unlocks] = ett.pf2e_element_list_to_string(new_unlocks)
    err = database.edit_character(cur_char)
    if err is not None:
        flash("ERROR: " + err, "error")
    return redirect("/edit_character", code=307)


@api.route('/edit_character_xpcs', methods=['POST'])
@login_required
def edit_character_xpcs():
    xp = request.form.get("XP", type=float)
    cs = request.form.get("CS", type=float)
    if xp is None or cs is None:
        return api_error()
    cur_char = get_character()
    cur_char[CHARACTERS.XP] = xp
    cur_char[CHARACTERS.CommunityService] = cs
    err = database.edit_character(cur_char)
    if err is not None:
        flash("ERROR: " + err, "error")
    return redirect("/edit_character", code=307)


@api.route('/edit_character_modify_gold', methods=['POST'])
@login_required
def edit_character_modify_gold():
    gold = request.form.get("gold", type=float)
    if gold is None:
        return api_error()
    cur_char = get_character()
    cur_char[CHARACTERS.CurrentGold] = gold
    err = database.edit_character(cur_char)
    if err is not None:
        flash("ERROR: " + err, "error")
    return redirect("/edit_character", code=307)
