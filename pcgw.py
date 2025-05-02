import json
from typing import Sequence

import httpx

import tables

TABLES_INFO_FILENAME = "tables.json"


class Game:
    def __init__(self, j: dict):
        self.name = j.get('Page')
        self.id = j.get('PageID')
        self.api = tables.API(j)
        self.audio = tables.Audio(j)
        self.availability = tables.Availability(j)
        self.cloud = tables.Cloud(j)
        self.infobox = tables.Infobox_game(j)
        self.input = tables.Input(j)
        self.middleware = tables.Middleware(j)
        self.multiplayer = tables.Multiplayer(j)
        self.tags = tables.Tags(j)
        self.vr_support = tables.VR_support(j)
        self.video = tables.Video(j)
        self.xdg = tables.XDG(j)

    def __str__(self):
        if self.name:
            return self.name
        else:
            return "Unknown game"


class PCGW:
    API_URL = "https://www.pcgamingwiki.com/w/api.php"

    def __init__(self):
        self.async_http_client = httpx.AsyncClient()
        self.http_client = httpx.Client()
        j = {k:v for k,v in json.load(open(TABLES_INFO_FILENAME)).items() if k not in ('L10n','Infobox_game_engine')}
        self._game_req_tables = list(j.keys())
        self._game_req_joins = [f'Infobox_game._pageID={table}._pageID' for table in j
                                if table not in ('Infobox_game',)]
        self._game_req_fields = [
            'Infobox_game._pageName=Page,'
            'Infobox_game._pageID=PageID,'
        ]
        for table in j:
            for field in j[table]:
                self._game_req_fields.append(f'{table}.{field}')

    def _build_search_request(self, query: str) -> dict:
        return {
            'action': 'cargoquery',
            'where': f'Infobox_game._pageName LIKE "%{query}%"',
            'tables' : ','.join(self._game_req_tables),
            'join_on': ','.join(self._game_req_joins),
            'fields' : ','.join(self._game_req_fields),
            'format': 'json',
        }
    
    def _handle_search_response(self, response: dict) -> list[Game]:
        return [Game(j.get('title', {})) for j in response.get('cargoquery', [])]

    def search(self, query: str) -> list[Game]:
        return self._handle_search_response(self.http_client.post(
                                            self.API_URL,
                                            data=self._build_search_request(query))
                                    .json())

    async def async_search(self, query: str) -> list[Game]:
        return self._handle_search_response((await self.async_http_client.get(
                                                self.API_URL,
                                                params=self._build_search_request(query))
                                   ).json())

    def get_game(self, *, page_id: int|None = None,
                          page_name: str|None = None,
                          gog_id: int|None = None,
                          steam_id: int|None = None) -> Game|None:
        if not page_id and not page_name and not gog_id and not steam_id:
            return None
        else:
            if page_id:
                req_where = f'Infobox_game._pageID="{page_id}"'
            elif page_name:
                req_where = f'Infobox_game._pageName="{page_name}"'
            elif gog_id:
                req_where = f'Infobox_game.GOGcom_ID = "{gog_id}"'
            else:
                req_where = f'Infobox_game.Steam_AppID HOLDS "{steam_id}"',
        params = {
            'action' : 'cargoquery',
            'where'  : req_where,
            'tables' : ','.join(self._game_req_tables),
            'join_on': ','.join(self._game_req_joins),
            'fields' : ','.join(self._game_req_fields),
            'format' : 'json',
        }
        response = self.http_client.post(self.API_URL, data=params).json()
        results = [j['title'] for j in response.get('cargoquery', []) if 'title' in j]
        if results:
            return Game(results[0])

    def get_games(self, page_ids: Sequence[int] = [],
                        page_names: Sequence[str] = []) -> dict[int|str, Game]:
        params = {
            'action': 'cargoquery',
            'where' : ' OR '.join(
                    [f'Infobox_game._pageName="{nom}"' for nom in page_names] +
                    [f'Infobox_game._pageID="{id}"' for id in page_ids]
                    ),
            'tables' : ','.join(self._game_req_tables),
            'join_on': ','.join(self._game_req_joins),
            'fields' : ','.join(self._game_req_fields),
            'format' : 'json',
        }
        response = self.http_client.get(self.API_URL, params=params).json()
        results = [Game(j['title']) for j in response.get('cargoquery', []) if 'title' in j]
        mapped_results = {}
        for result in results:
            if result.id in page_ids:
                mapped_results[result.id] = result
            elif result.name in page_names:
                mapped_results[result.name] = result
        return mapped_results
