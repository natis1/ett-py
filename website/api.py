# This holds all the database API interaction routes.
# Everything in here is accessed at /api/

from flask import Blueprint, render_template, request, redirect
from flask_login import current_user, login_required
from src import database, ett
api = Blueprint('api', __name__)

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
