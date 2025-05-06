#!/bin/env python

import json
from time import sleep

import httpx

from pcgw_api.utils import TABLES_INFO_FILENAME

FORCED_TYPES = {
    'Multiplayer': {
        'Local players': {'type':'int', 'post_processing':'int'},
        'LAN players': {'type':'int', 'post_processing':'int'},
        'Online players': {'type':'int', 'post_processing':'int'},
    },
    'Cloud': {
        'Steam': {'type': 'Support', 'post_processing': ''},
    },
    'Input': {
        'Controller support level': {'type': 'Support', 'post_processing': ''},
        'Controller hotplugging': {'type': 'Support', 'post_processing': ''},
    },
    'L10n': {
        'Interface': {'type': 'Support', 'post_processing': ''},
        'Audio': {'type': 'Support', 'post_processing': ''},
        'Subtitles': {'type': 'Support', 'post_processing': ''},
    },
    'Video': {
        'Anisotropic filtering': {'type': 'Support', 'post_processing': ''},
        'Antialiasing': {'type': 'Support', 'post_processing': ''},
    },
    'XDG': {
        'Supported': {'type': 'Support', 'post_processing': ''},
    },
}

PYTHON_TABLES_FILENAME = "tables.py"

class Field:
    def __init__(self, key: str, j: dict, table: str):
        self.query_key = key
        self.key = key.replace('_', ' ')
        self.name = key.lower()

        self.type = {
            'String' : 'str',
            'URL' : 'str',
            'Page' : 'str',
            'File' : 'str',
            'Wikitext' : 'str',
            'Date' : 'datetime.datetime',
            }.get(j['type'], 'Any')

        self.post_processing = {
            'Date' : 'datetime.datetime.fromisoformat',
            }.get(j['type'], 'str')

        if table in FORCED_TYPES and self.key in FORCED_TYPES[table]:
            self.type = FORCED_TYPES[table][self.key]['type']
            self.post_processing = FORCED_TYPES[table][self.key]['post_processing']

        self.is_list = 'isList' in j
        self.delimiter = j.get('delimiter')

def get_table_fields(table):
    url = "https://www.pcgamingwiki.com/w/api.php"
    params = {
        'action' : 'cargofields',
        'format' : 'json',
        'table' : table,
    }
    j = httpx.get(url, params=params).json()

    fields = []
    for k,v in j.get('cargofields', {}).items():
        if k[0].isalpha():
            new_field = Field(k,v,table)

            if not new_field.is_list and new_field.type == 'str':
                params['action'] = 'cargoquery'
                params['where'] = 'Infobox_game._pageName LIKE "%"'
                params['tables'] = ','.join(t for t in set(['Infobox_game', table]))
                params['fields'] = f'{table}.{k}'
                if table != 'Infobox_game':
                    params['join_on'] = f'Infobox_game._pageID={table}._pageID'
                params['group_by'] = f'{table}.{k}'

                j = httpx.get(url, params=params).json().get('cargoquery', {})
                possible_values = [row.get('title',{}).get(new_field.key,'null') or 'null' for row in j]
                if set(possible_values).issubset({'null','unknown','n/a','false','limited','hackable','true','complete','always on'}):
                    new_field.type = 'Support'

            fields.append(new_field)
    return fields

python_tables_txt = '''
import datetime
from typing import Any

from pcgw_api.utils import parse_list, parse_value, parse_support_enum, Support
'''

j = {}
for table in (
    'API',
    'Audio',
    'Availability',
    'Cloud',
    'Infobox_game',
    'Infobox_game_engine',
    'Input',
    'L10n',
    'Middleware',
    'Multiplayer',
    'Tags',
    'VR_support',
    'Video',
    'XDG',
    ):
    print(f'fetching fields info for table "{table}"')
    fields = get_table_fields(table)
    j[table] = [field.query_key for field in fields]

    python_tables_txt += f'''
class {table}:
    def __init__(self, j):
'''
    for field in fields:
        if field.is_list:
            python_tables_txt += ' '*8 + f'self.{field.name}: list[{field.type}] = parse_list(j, "{field.key}", "{field.delimiter}", {field.post_processing})\n'
        else:
            if field.type == 'str':
                python_tables_txt += ' '*8 + f'self.{field.name}: {field.type}|None = j.get("{field.key}")\n'
            elif field.type == 'Support':
                python_tables_txt += ' '*8 + f'self.{field.name}: {field.type} = parse_support_enum(j, "{field.key}")\n'
            else:
                python_tables_txt += ' '*8 + f'self.{field.name}: {field.type}|None = parse_value(j, "{field.key}", {field.post_processing})\n'
    sleep(.5)

with open(PYTHON_TABLES_FILENAME, "w") as f:
    f.write(python_tables_txt)
json.dump(j, open(TABLES_INFO_FILENAME, "w"))
