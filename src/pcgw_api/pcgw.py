import json
from typing import Sequence

import httpx

import pcgw_api.tables as tables
from pcgw_api.utils import TABLES_INFO_FILENAME

class Game:
    """
    Represents the information of a PCGamingWiki game page.

    Centralizes the information about a PCGamingWiki game page
    fetched from the API and deserialized by the classes from the
    tables module.

    Attributes:
        json_data: data before deserialization.
        pcgw_client: API client class to optionnally fetch data from association
                     tables after initialization.
        name: name of the game.
        id: id of the game page.
        api: information about the API used by the game.
        audio: audio-relative information about the game.
        availability: information about the availability of the game.
        cloud: information about the cloud possibilities (saves) of the game.
        infobox: general information about the game.
        input: input-relative information about the game.
        middleware: information about the middleware used by the game.
        multiplayer: information about the multiplayer aspects of the game.
        tags: various information about the game entered as tags in PCGamingWiki.
        vr_support: information about the Virtual Reality capabilities of the game.
        video: information about the game relative to video rendering.
        xdg: information about the XDG standard support of the game.
        languages: list of languages supported by the game.
        engines: list of engines used by the game.
    """
    def __init__(self, j: dict, pcgw_client: "PCGW|None" = None):
        """
        Constructor for a Game.

        Parameters:
            j: data to deserialize by the classes from the tables module,
                typically a json response from the API.
            pcgw_client: API client class to optionally fetch data from
                         association tables later.
        """
        self.json_data = j
        self.pcgw_client: PCGW|None = pcgw_client
        self.name = j.get('Page')
        try:
            self.id = int(j.get('PageID', '') or '')
        except ValueError:
            self.id = None
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
        self.languages = []
        self.engines = []

    def _get_association_table(self, table: str, attr: str) -> list:
        """
        Generic function to fetch list elements corresponding to an association
        table in the PCGamingWiki database, with unnormalized rows like
        (<Game name>, <Table info 1>, <Table info 2>…). Populates and returns the
        corresponding attribute.
        """
        if not getattr(self,attr) and self.pcgw_client:
            tables_info = {k:v for k,v in json.load(open(TABLES_INFO_FILENAME)).items()}
            params = {
                'action' : 'cargoquery',
                'where'  : f'Infobox_game._pageName="{self.name}"',
                'tables' : f'Infobox_game,{table}',
                'join_on': f'Infobox_game._pageID={table}._pageID',
                'fields' : ','.join(f'{table}.{field}' for field in tables_info.get(table,[])),
                'format' : 'json',
            }
            response = self.pcgw_client.http_client.get(self.pcgw_client.API_URL, params=params).json()
            setattr(self, attr, [getattr(tables, table)(j.get('title', {})) for j in response.get('cargoquery', [])])
        return getattr(self, attr)

    def get_languages(self) -> list[tables.L10n]:
        """
        Populates and returns the languages attribute with the list elements corresponding
        to the association table "L10n" in the PCGamingWiki database.
        """
        return self._get_association_table('L10n', 'languages')

    def get_engines(self) -> list[tables.Infobox_game_engine]:
        """
        Populates and returns the engines attribute with the list elements corresponding
        to the association table "Infobox_game_engine" in the PCGamingWiki database.
        """
        return self._get_association_table('Infobox_game_engine', 'engines')

    def __str__(self):
        if self.name:
            return self.name
        else:
            return "Unknown game"


class PCGW:
    """
    Main class interacting with the PCGamingWiki API.

    Attributes:
        API_URL: the URL of the PCGamingWiki API.
        http_client: httpx client used for synchronous requests.
        async_http_client: httpx client used for asynchronous requests.
    """
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
        return [Game(j.get('title', {}), self) for j in response.get('cargoquery', [])]

    def search(self, query: str) -> list[Game]:
        """
        Searches PCGamingWiki.

        The search returns the games with name containing the query string,
        the API request using the SQL LIKE operator.

        Parameters:
            query: query string.

        Returns:
            A list of results deserialized into Game objects.
        """
        return self._handle_search_response(self.http_client.post(
                                            self.API_URL,
                                            data=self._build_search_request(query))
                                    .json())

    async def async_search(self, query: str) -> list[Game]:
        """
        Searches PCGamingWiki, asynchronous version.

        The search returns the games with name containing the query string,
        the API request using the SQL LIKE operator.

        Parameters:
            query: query string.

        Returns:
            A list of results deserialized into Game objects.
        """
        return self._handle_search_response((await self.async_http_client.post(
                                                self.API_URL,
                                                data=self._build_search_request(query))
                                   ).json())

    def get_game(self, *, page_id: int|None = None,
                          page_name: str|None = None,
                          gog_id: int|None = None,
                          steam_id: int|None = None) -> Game|None:
        """
        Get information about a game from PCGamingWiki.

        The function uses only one parameter among page_id, page_name, gog_id
        and steam_id: if more than one is specified, it will use the first in
        the order of the parameters list.

        Parameters:
            page_id: ID of a PCGamingWiki page.
            page_name: name of a PCGamingWiki page.
            gog_id: ID of a GOG.com game.
            steam_id: AppID of a Steam game.

        Returns:
            A Game object or None if the request went wrong.
        """
        if not page_id and not page_name and not gog_id and not steam_id:
            return None
        else:
            if page_id:
                req_where = f'Infobox_game._pageID="{page_id}"'
            elif page_name:
                req_where = f'Infobox_game._pageName="{page_name}"'
            elif gog_id:
                req_where = f'Infobox_game.GOGcom_ID HOLDS "{gog_id}"'
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
            return Game(results[0], self)

    def get_games(self, page_ids: Sequence[int] = [],
                        page_names: Sequence[str] = []) -> dict[int|str, Game]:
        """
        Get information about multiple games from PCGamingWiki in one request.

        Parameters:
            page_ids: sequence of IDs of PCGamingWiki pages.
            page_names: sequence of names of PCGamingWiki pages.

        Returns:
            A dictionary with the page_ids and page_names from the parameters
            as keys and the corresponding Game objects as values. The value is 
            None if the game could not be found in the request response.
        """
        if not page_ids and not page_names:
            return {}
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
        response = self.http_client.post(self.API_URL, data=params).json()
        results = [Game(j['title'], self) for j in response.get('cargoquery', []) if 'title' in j]
        mapped_results = {}
        for k in page_ids:
            mapped_results[k] = None
        for k in page_names:
            mapped_results[k] = None
        for result in results:
            if result.id in page_ids:
                mapped_results[result.id] = result
            elif result.name in page_names:
                mapped_results[result.name] = result
        return mapped_results

    def get_possible_values(self, attr: str) -> list[str]:
        """
        Get the set of possible values in the PCGamingWiki database 
        for a given field.

        Parameters:
            attr: name of an attribute of a class from the tables module.
        
        Returns:
            The list of possible values for the given attribute.
        """
        found = False
        field = table = None
        for table,fields in json.load(open(TABLES_INFO_FILENAME)).items():
            for field in fields:
                if field.lower() == attr:
                    found = True
                    break
            if found: break
        else:
            return []
        if not table or not field:
            return []
        params = {
            'action': 'cargoquery',
            'where' : 'Infobox_game._pageName LIKE "%"',
            'tables' : ','.join(t for t in set(['Infobox_game', table])),
            'fields' : f'{table}.{field}',
            'group_by' : f'{table}.{field}',
            'format' : 'json',
        }
        if table != 'Infobox_game':
            params['join_on'] = f'Infobox_game._pageID={table}._pageID'

        j = httpx.get(self.API_URL, params=params).json().get('cargoquery', {})
        return [row.get('title',{}).get(field.replace('_',' ')) for row in j]
