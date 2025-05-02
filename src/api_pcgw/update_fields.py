#!/bin/env python

import json
from time import sleep

import httpx

from pcgw import TABLES_INFO_FILENAME

FORCED_TYPES = {
    'Multiplayer': {
        'Local players': {'type':'int', 'post_processing':'int'},
        'LAN players': {'type':'int', 'post_processing':'int'},
        'Online players': {'type':'int', 'post_processing':'int'},
    }
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

    return [Field(k,v,table) for k,v in j.get('cargofields', {}).items()
                        if k[0].isalpha()]

python_tables_txt = '''
import datetime
from typing import Any

from utils import parse_list, parse_value
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
            else:
                python_tables_txt += ' '*8 + f'self.{field.name}: {field.type}|None = parse_value(j, "{field.key}", {field.post_processing})\n'
    sleep(.5)

with open(PYTHON_TABLES_FILENAME, "w") as f:
    f.write(python_tables_txt)
json.dump(j, open(TABLES_INFO_FILENAME, "w"))
