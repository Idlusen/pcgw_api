import datetime
import httpx

class SearchResult:
    def __init__(self, j: dict):
        self.name: str|None = j.get('Page')

        try:
            self.id = int(j.get('PageID', ''))
        except ValueError:
            self.id = None

        self.steam_ids: list[int] = []
        if s := j.get('Steam AppID'):
            for s in s.split(','):
                try:
                    self.steam_ids.append(int(s))
                except ValueError:
                    pass

        self.gog_ids: list[int] = []
        if s := j.get('GOGcom ID'):
            for s in s.split(','):
                try:
                    self.gog_ids.append(int(s))
                except ValueError:
                    pass

        self.dates: list[datetime.datetime] = []
        if s := j.get('Released'):
            for s in s.split(';'):
                try:
                    self.dates.append(datetime.datetime.fromisoformat(s))
                except ValueError:
                    pass
            self.date = self.dates[0] if self.dates else None

    def __str__(self):
        if self.name:
            if self.date:
                return f'{self.name} ({self.date.year})'
            else:
                return self.name 
        else:
            return 'Unknown search result'

class PCGW:
    API_URL = "https://www.pcgamingwiki.com/w/api.php"

    def __init__(self):
        self.async_http_client = httpx.AsyncClient()
        self.http_client = httpx.Client()

    def _build_search_request(self, query: str) -> dict:
        return {
            'action': 'cargoquery',
            'tables': 'Infobox_game',
            'where': f'Infobox_game._pageName LIKE "%{query}%"',
            'fields': 'Infobox_game._pageName=Page,'
                      'Infobox_game._pageID=PageID,'
                      'Infobox_game.Steam_AppID,'
                      'Infobox_game.GOGcom_ID,'
                      'Infobox_game.Released',
            'format': 'json',
        }
    
    def _handle_search_response(self, response: dict) -> list[SearchResult]:
        return [SearchResult(j.get('title', {})) for j in response.get('cargoquery', [])]

    def search(self, query: str) -> list[SearchResult]:
        return self._handle_search_response(self.http_client.get(
                                            self.API_URL,
                                            params=self._build_search_request(query))
                                    .json())

    async def async_search(self, query: str) -> list[SearchResult]:
        return self._handle_search_response((await self.async_http_client.get(
                                                self.API_URL,
                                                params=self._build_search_request(query))
                                    ).json())
