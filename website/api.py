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
        return None
    return list(cur_char)


def get_player():
    player = request.form.get("PlayerName", type=str)
    cur_player = database.get_player(player)
    if cur_player is None:
        return None
    return list(cur_player)


def get_adventure():
    adv_id = request.form.get("ID")
    cur_adventure = database.get_row("games", "ID", adv_id)
    if cur_adventure is None:
        return None
    return list(cur_adventure)


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
    count, total, table = database.get_characters_table(q[0], q[1], q[2], q[3])
    out_table = []
    for data in table:
        outdict = {'PlayerName': data[CHARACTERS.PlayerName], 'Name': data[CHARACTERS.Name],
                   'Ancestry': data[CHARACTERS.Ancestry],
                   'Class': data[CHARACTERS.Class],
                   'XP': round(data[CHARACTERS.XP], 2), 'Level': ett.get_level(data[CHARACTERS.XP]),
                   'CurrentGold': round(data[CHARACTERS.CurrentGold], 2),
                   'ExpectedGold': round(data[CHARACTERS.ExpectedGold], 2)}
        out_table += [outdict]

    return {
        'data': out_table,
        'recordsFiltered': total,
        'recordsTotal': count,
        'draw': request.args.get('draw', type=int),
    }


@api.route('/players')
def players():
    q = get_query_data()
    count, total, table = database.get_players_table(q[0], q[1], q[2], q[3])
    out_table = []
    for data in table:
        chars = len(database.string_list_to_list(data[PLAYERS.Characters]))
        max_chars = ett.get_available_slots(data[PLAYERS.Upgrades], [])
        out_dict = {'PlayerName': data[PLAYERS.PlayerName], 'Karma': data[PLAYERS.Karma],
                    'Chars': str(chars) + " / " + str(max_chars)}
        out_table += [out_dict]
    return {
        'data': out_table,
        'recordsFiltered': total,
        'recordsTotal': count,
        'draw': request.args.get('draw', type=int),
    }


@api.route('/adventures')
def adventures():
    q = get_query_data()
    count, total, table = database.get_games_table(q[0], q[1], q[2], q[3])
    out_table = []
    for data in table:
        out_dict = {'Name': data[1], 'Date': data[2], 'GM': data[7], 'Time': data[4], 'GameLevel': data[5]}
        out_table += [out_dict]
    return {
        'data': out_table,
        'recordsFiltered': total,
        'recordsTotal': count,
        'draw': request.args.get('draw', type=int),
    }


@api.route('/edit_player_regenk', methods=['POST'])
@login_required
def edit_player_regenk():
    pl = get_player()
    if not pl:
        return api_error()
    pl = list(pl)
    pl_events = database.sql_exec("SELECT * FROM events WHERE PlayerName = ?", (pl[PLAYERS.PlayerName], ), database.Fetch.ALL)
    k = ett.STARTING_KARMA
    for i in pl_events:
        karma = i[database.EVENTS.KarmaAdjust]
        if karma:
            k += int(karma)
    print("RECALCULATED PLAYER KARMA FOR PL: ", pl[PLAYERS.PlayerName], " FROM ", pl[PLAYERS.Karma], " TO ", k)
    pl[PLAYERS.Karma] = k
    database.edit_player(pl)
    return redirect("/edit_player", code=307)


@api.route('/edit_player_xptransfer', methods=['POST'])
@login_required
def edit_player_xptransfer():
    xp_target = request.form.get("sendto", type=str)
    xp_target_split = xp_target.split("|", 1)
    xp_sent = request.form.get("xpsend", type=float)
    if not xp_target or not xp_sent or (len(xp_target_split) != 2):
        return api_error()
    pl = get_player()
    if not pl:
        return api_error()
    char = database.get_character(xp_target_split[0], xp_target_split[1])
    if char is None:
        return api_error()
    char = list(char)
    pl[PLAYERS.BonusXP] -= xp_sent
    gold_add = ett.ett_gold_add_xp(char[CHARACTERS.XP], xp_sent)
    char[CHARACTERS.XP] += xp_sent
    char[CHARACTERS.CurrentGold] += gold_add
    char[CHARACTERS.ExpectedGold] += gold_add
    err = database.edit_player(pl)
    if err:
        flash("ERROR: " + err, "error")
    err = database.edit_character(char)
    if err:
        flash("ERROR: " + err, "error")
    return redirect("/edit_player", code=307)


@api.route('/edit_player_xpedit', methods=['POST'])
@login_required
def edit_player_xpedit():
    new_xp = request.form.get("xp", type=float)
    if new_xp is None:
        return api_error()
    pl = get_player()
    if not pl:
        return api_error()
    pl[PLAYERS.BonusXP] = new_xp
    err = database.edit_player(pl)
    if err:
        flash("ERROR: " + err, "error")
    return redirect("/edit_player", code=307)


@api.route('/edit_player_karmaadd', methods=['POST'])
@login_required
def edit_player_karmaadd():
    new_karma = request.form.get("karma", type=int)
    if new_karma is None:
        return api_error()
    pl = get_player()
    if not pl:
        return api_error()
    pl[PLAYERS.Karma] = new_karma
    err = database.edit_player(pl)
    if err:
        flash("ERROR: " + err, "error")
    return redirect("/edit_player", code=307)


@api.route('/edit_player_url', methods=['POST'])
@login_required
def edit_player_url():
    intro = request.form.get("intro")
    if intro is None:
        return api_error()
    pl = get_player()
    if not pl:
        return api_error()
    pl[PLAYERS.DiscordIntro] = intro
    err = database.edit_player(pl)
    if err:
        flash("ERROR: " + err, "error")
    return redirect("/edit_player", code=307)


@api.route('/edit_player_karmadel', methods=['POST'])
@login_required
def edit_player_karmadel():
    loss_item = request.form.get("k_unlocks", type=str)
    loss_number = request.form.get("remove_num", type=int)
    if not loss_number or not loss_item:
        return api_error()
    pl = get_player()
    if not pl:
        return api_error()
    item = ett.Pf2eElement(loss_item, quantity=loss_number)
    rewards = ett.string_to_pf2e_element_list(pl[PLAYERS.Upgrades])
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
    pl[PLAYERS.Upgrades] = ett.pf2e_element_list_to_string(out_rewards)
    err = database.edit_player(pl)
    if err:
        flash("ERROR: " + err, "error")
    return redirect("/edit_player", code=307)


@api.route('/edit_player_name', methods=['POST'])
@login_required
def edit_player_name():
    new_name = request.form.get("PlayerName2")
    if not new_name:
        return api_error()
    pl = get_player()
    if not pl:
        return api_error()
    new_pl_test = database.get_player(new_name)
    if new_pl_test:
        flash("API ERROR: Player with name " + new_pl_test + " already exists!", "error")
        return redirect("/edit_player", code=307)
    err = database.change_player_name(pl[PLAYERS.PlayerName], new_name)
    if err:
        flash("ERROR: " + err, "error")
    return redirect("/players")


@api.route('/edit_player_delete', methods=['POST'])
@login_required
def edit_player_delete():
    pl = get_player()
    if not pl:
        return api_error()
    database.delete_player(pl[PLAYERS.PlayerName])
    return redirect("/players")


@api.route('/edit_character_delete', methods=['POST'])
@login_required
def edit_character_delete():
    c = get_character()
    if not c:
        return api_error()
    database.delete_character(c[CHARACTERS.PlayerName], c[CHARACTERS.Name])
    return redirect('/characters')


@api.route('/edit_character_names', methods=['POST'])
@login_required
def edit_character_names():
    new_player = request.form.get("PlayerName2")
    new_char_name = request.form.get("Name2")
    if not new_player or not new_char_name:
        return api_error()
    cur_char = get_character()
    if not cur_char:
        return api_error()
    # The player changed. move to new player
    if new_player != cur_char[CHARACTERS.PlayerName]:
        e = database.move_character(cur_char, new_player)
        if e:
            flash(e, "error")

    # The char name changed. rename char name in DB
    if new_char_name != cur_char[CHARACTERS.Name]:
        e = database.change_character_name(cur_char, new_char_name)
        if e:
            flash(e, "error")

    return redirect("/characters")


@api.route('/edit_character_core', methods=['POST'])
@login_required
def edit_character_core():
    ancestry = request.form.get("ancestry", type=str)
    heritage = request.form.get("heritage", type=str)
    background = request.form.get("background", type=str)
    pc_class = request.form.get("class", type=str)
    home = request.form.get("home", type=str)
    subclass = request.form.get("subclass", type=str)
    ironman = request.form.get("ironman", type=int)
    comments = request.form.get("comments", type=str)
    if (not ancestry or not heritage or not background or not pc_class
            or not home or ironman is None or comments is None):
        return api_error()

    cur_char = get_character()
    if not cur_char:
        return api_error()
    cur_char[CHARACTERS.Ancestry] = ancestry
    cur_char[CHARACTERS.Heritage] = heritage
    cur_char[CHARACTERS.Background] = background
    cur_char[CHARACTERS.Class] = pc_class
    cur_char[CHARACTERS.Home] = home
    cur_char[CHARACTERS.Ironman] = ironman
    cur_char[CHARACTERS.Comments] = comments
    cur_char[CHARACTERS.Subclass] = subclass

    err = database.edit_character(cur_char)
    if err:
        flash("ERROR: " + err, "error")
    return redirect("/edit_character", code=307)


@api.route('/edit_character_pdfurl', methods=['POST'])
@login_required
def edit_character_pdfurl():
    url = request.form.get("url", type=str)
    level = request.form.get("level", type=int)
    if not url or level is None:
        return api_error()
    level = level - 1

    cur_char = get_character()
    if not cur_char:
        return api_error()
    pdf_urls = cur_char[CHARACTERS.PDFs]
    # Discard invalid fvtt url entries in DB
    if not pdf_urls:
        # setup fvtt urls for first time use
        pdfs = 20 * ['']
    else:
        pdfs = database.string_list_to_list(pdf_urls)
        if len(pdfs) != 20:
            pdfs = 20 * ['']

    pdfs[level] = url
    cur_char[CHARACTERS.PDFs] = database.list_to_string(pdfs)
    err = database.edit_character(cur_char)
    if err:
        flash("ERROR: " + err, "error")
    return redirect("/edit_character", code=307)


@api.route('/edit_character_fvtturl', methods=['POST'])
@login_required
def edit_character_fvtturl():
    url = request.form.get("url", type=str)
    level = request.form.get("level", type=int)
    if not url or level is None:
        return api_error()
    level = level - 1

    cur_char = get_character()
    if not cur_char:
        return api_error()
    fvtt_urls = cur_char[CHARACTERS.FVTTs]
    # Discard invalid fvtt url entries in DB
    if not fvtt_urls:
        # setup fvtt urls for first time use
        fvtts = 20 * ['']
    else:
        fvtts = database.string_list_to_list(fvtt_urls)
        if len(fvtts) != 20:
            fvtts = 20 * ['']

    fvtts[level] = url
    cur_char[CHARACTERS.FVTTs] = database.list_to_string(fvtts)
    err = database.edit_character(cur_char)
    if err:
        flash("ERROR: " + err, "error")
    return redirect("/edit_character", code=307)


@api.route('/edit_character_pburl', methods=['POST'])
@login_required
def edit_character_pburl():
    url = request.form.get("url", type=str)
    discord = request.form.get("discord", type=str)
    picture = request.form.get("picture", type=str)
    if not url:
        return api_error()
    cur_char = get_character()
    if not cur_char:
        return api_error()
    cur_char[CHARACTERS.Pathbuilder] = url
    cur_char[CHARACTERS.DiscordLink] = discord
    cur_char[CHARACTERS.Picture] = picture
    err = database.edit_character(cur_char)
    if err:
        flash("ERROR: " + err, "error")
    return redirect("/edit_character", code=307)


@api.route('/edit_character_karmabuy', methods=['POST'])
@login_required
def edit_character_karmabuy():
    buy = request.form.get("k_buy", type=str)
    qty = request.form.get("k_qty", type=int)
    if not buy or not qty:
        return api_error()
    valid_buy_items = [x for x in ett.KARMA_REWARDS if x.name == buy]
    if not valid_buy_items:
        return api_error()
    player = get_player()
    if not player:
        return api_error()
    cur_char = get_character()
    if not cur_char:
        return api_error()
    buy_item = valid_buy_items[0]
    buy_item.quantity = qty
    cost = buy_item.level * buy_item.quantity
    if buy_item.name == "New Face":
        cost = ett.get_new_face_karma_cost(buy_item, player[PLAYERS.Upgrades])

    # add to player
    if buy_item.rarity == 2:
        pl_items = ett.string_to_pf2e_element_list(player[PLAYERS.Upgrades])
        new_item = True
        for i in pl_items:
            if buy_item.name == i.name:
                i.quantity += buy_item.quantity
                new_item = False
        if new_item:
            pl_items += [buy_item]
        player[PLAYERS.Upgrades] = ett.pf2e_element_list_to_string(pl_items)

    # add to character
    if buy_item.rarity == 1:
        ch_items = ett.string_to_pf2e_element_list(cur_char[CHARACTERS.Rewards])
        new_item = True
        for i in ch_items:
            if buy_item.name == i.name:
                i.quantity += buy_item.quantity
                new_item = False
        if new_item:
            ch_items += [buy_item]
        cur_char[CHARACTERS.Rewards] = ett.pf2e_element_list_to_string(ch_items)
        err = database.edit_character(cur_char)
        if err:
            flash("ERROR: " + err, "error")

    player[PLAYERS.Karma] = int(player[PLAYERS.Karma])
    player[PLAYERS.Karma] -= cost
    err = database.edit_player(player)
    if err:
        flash("ERROR: " + err, "error")
    return redirect("/edit_character", code=307)


@api.route('/edit_character_karmaadd', methods=['POST'])
@login_required
def edit_character_karmaadd():
    new_karma = request.form.get("karma")
    if new_karma is None:
        return api_error()
    pl = get_player()
    if not pl:
        return api_error()
    pl[PLAYERS.Karma] = new_karma
    err = database.edit_player(pl)
    if err:
        flash("ERROR: " + err, "error")
    return redirect("/edit_character", code=307)


@api.route('/edit_character_karmaloss', methods=['POST'])
@login_required
def edit_character_karmaloss():
    loss_item = request.form.get("k_unlocks", type=str)
    loss_number = request.form.get("remove_num", type=int)
    if not loss_number or not loss_item:
        return api_error()
    cur_char = get_character()
    if not cur_char:
        return api_error()
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
    err = database.edit_character(cur_char)
    if err:
        flash("ERROR: " + err, "error")
    return redirect("/edit_character", code=307)


@api.route('/edit_character_buy_item', methods=['POST'])
@login_required
def edit_character_buy_item():
    buy_name = request.form.get("buy_name")
    level = request.form.get("buy_level", type=int)
    cost = request.form.get("buy_cost", type=float)
    rarity = request.form.get("buy_rarity", type=int)
    qty = request.form.get("buy_qty", type=int)
    value_factor = request.form.get("cost_factor", type=float)
    if (not buy_name or level is None or cost is None or not qty
            or value_factor is None or rarity is None):
        return api_error()
    cur_char = get_character()
    if not cur_char:
        return api_error()
    items = [ett.Pf2eElement(buy_name, level, cost, rarity, qty)]
    err = database.buy_items(cur_char, datetime.today().strftime('%Y-%m-%d'),
                             f"WEB API v{API_VERSION} edit_character_buy_item",
                             items, value_factor)
    if err:
        flash("ERROR: " + err, "error")
    return redirect("/edit_character", code=307)


@api.route('/edit_character_sell_item', methods=['POST'])
@login_required
def edit_character_sell_item():
    item_sold = request.form.get("inventory")
    sell_qty = request.form.get("sell_qty", type=int)
    sell_value = request.form.get("sell_value", type=float)
    if not item_sold or sell_value is None or not sell_qty:
        return api_error()
    cur_char = get_character()
    if not cur_char:
        return api_error()
    items = [ett.Pf2eElement(item_sold, quantity=sell_qty)]
    err = database.sell_items(cur_char, datetime.today().strftime('%Y-%m-%d'),
                              f"WEB API v{API_VERSION} edit_character_sell_item",
                              items, sell_value)
    if err:
        flash("ERROR: " + err, "error")
    return redirect("/edit_character", code=307)


@api.route('/edit_character_remove_rare', methods=['POST'])
@login_required
def edit_character_remove_rare():
    remove_item = request.form.get("r_unlocks", type=str)
    if not remove_item:
        return api_error()
    cur_char = get_character()
    if not cur_char:
        return api_error()
    el = ett.Pf2eElement(remove_item)
    cur_unlocks = ett.string_to_pf2e_element_list(cur_char[CHARACTERS.Rares])
    new_unlocks = ett.ett_parse_unlocks(cur_unlocks, [], [el], 0)
    cur_char[CHARACTERS.Rares] = ett.pf2e_element_list_to_string(new_unlocks)
    err = database.edit_character(cur_char)
    if err:
        flash("ERROR: " + err, "error")
    return redirect("/edit_character", code=307)


@api.route('/edit_character_remove_unlock', methods=['POST'])
@login_required
def edit_character_remove_unlock():
    remove_item = request.form.get("i_unlocks", type=str)
    if not remove_item:
        return api_error()
    cur_char = get_character()
    if not cur_char:
        return api_error()
    el = ett.Pf2eElement(remove_item)
    cur_unlocks = ett.string_to_pf2e_element_list(cur_char[CHARACTERS.Unlocks])
    new_unlocks = ett.ett_parse_unlocks(cur_unlocks, [], [el], ett.get_level(cur_char[CHARACTERS.XP]))
    cur_char[CHARACTERS.Unlocks] = ett.pf2e_element_list_to_string(new_unlocks)
    err = database.edit_character(cur_char)
    if err:
        flash("ERROR: " + err, "error")
    return redirect("/edit_character", code=307)


@api.route('/edit_character_add_unlock', methods=['POST'])
@login_required
def edit_character_add_unlock():
    name = request.form.get("unlock_name", type=str)
    level = request.form.get("unlock_level", type=int)
    cost = request.form.get("unlock_cost", type=float)
    rarity = request.form.get("unlock_rarity", type=int)
    if not name or level is None or cost is None or rarity is None:
        return api_error()
    cur_char = get_character()
    if not cur_char:
        return api_error()
    el = ett.Pf2eElement(name, level, cost, rarity)
    cur_unlocks = ett.string_to_pf2e_element_list(cur_char[CHARACTERS.Unlocks])
    new_unlocks = ett.ett_parse_unlocks(cur_unlocks, [el], [], ett.get_level(cur_char[CHARACTERS.XP]))
    cur_char[CHARACTERS.Unlocks] = ett.pf2e_element_list_to_string(new_unlocks)
    err = database.edit_character(cur_char)
    if err:
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
    if not cur_char:
        return api_error()
    gold_change = ett.ett_gold_add_xp(cur_char[CHARACTERS.XP], xp - cur_char[CHARACTERS.XP])
    cur_char[CHARACTERS.CurrentGold] += gold_change
    # Reset expected gold to normal amount just in case
    # it got messed up by some other change made.
    cur_char[CHARACTERS.ExpectedGold] = ett.STARTING_GOLD + ett.ett_gold_add_xp(0, xp)
    cur_char[CHARACTERS.XP] = xp
    cur_char[CHARACTERS.CommunityService] = cs
    err = database.edit_character(cur_char)
    if err:
        flash("ERROR: " + err, "error")
    return redirect("/edit_character", code=307)


@api.route('/edit_character_modify_gold', methods=['POST'])
@login_required
def edit_character_modify_gold():
    gold = request.form.get("gold", type=float)
    if gold is None:
        return api_error()
    cur_char = get_character()
    if not cur_char:
        return api_error()
    cur_char[CHARACTERS.CurrentGold] = gold
    err = database.edit_character(cur_char)
    if err:
        flash("ERROR: " + err, "error")
    return redirect("/edit_character", code=307)


@api.route('/edit_adventure_name', methods=['POST'])
@login_required
def edit_adventure_name():
    name = request.form.get("name")
    date = request.form.get("date")
    if not name or not date:
        return api_error()
    # The adventure you're trying to rename to already exists.
    test_adv = database.get_game(name, date)
    if test_adv:
        flash("API ERROR: adventure already exists " + name + ", " + date, "error")
        return redirect("/adventures")
    a = get_adventure()
    if not a:
        return api_error()
    a[GAMES.Name] = name
    a[GAMES.Date] = date
    err = database.edit_game(a)
    if err:
        flash("ERROR: " + err, "error")
    return redirect("/adventures")


@api.route('/edit_adventure_gm', methods=['POST'])
@login_required
def edit_adventure_gm():
    gm = request.form.get("gm")
    if not gm:
        return api_error()
    test_gm = database.get_player(gm)
    if not test_gm:
        return api_error()

    a = get_adventure()
    if not a:
        return api_error()
    a[GAMES.GM] = gm
    err = database.edit_game(a)
    if err:
        flash("ERROR: " + err, "error")
    return redirect("/adventures")


@api.route('/edit_adventure_delete', methods=['POST'])
@login_required
def edit_adventure_delete():
    a = get_adventure()
    if not a:
        return api_error()
    database.delete_game(a[GAMES.ID])
    return redirect("/adventures")
