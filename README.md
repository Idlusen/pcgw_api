# pcgw_api: Python client for the PCGamingWiki API

# Installation
```
pip install pcgw_api
```

# Usage
## Searching
```python
import pcgw_api
client = pcgw_api.PCGW()
for result in client.search("Celeste"):
  print(result)
```
Search is performed with a SQL LIKE query. In the future you will be able to search with opensearch,
allowing more flexible results at the expense of less informative data wich will require further
requests to get interesting information.

There is also `PCGW.async_search` should you need an asynchronous version.

## Fetching data
The above search function returns `Game` objects, which have all the information from the 
tables of the PCGamingWiki database. The tables are accessible as attributes:
```python
cuphead = client.search("Cuphead")[0]
print(cuphead.infobox.genres)
print(cuphead.availability.available_from)
print(cuphead.multiplayer.local_players)
```
See `tables.py` for the full list of available fields.

Dates are parsed as `datetime` python objects and fields indicating the support of the game
for a feature are generally parsed into a `Support` enum object:
```python
print(', '.join(str(date.year) for date in cuphead.infobox.released))
print(cuphead.input.controller_hotplugging == pcgw_api.Support.TRUE) # True
print(cuphead.input.controller_hotplugging == pcgw_api.Support.HACKABLE) # False
print(cuphead.input.mouse_sensitivity == pcgw_api.Support.NA) # True
```
`Support` is falsy for the values NULL, NA, UNKNOWN and FALSE, truthy otherwise:
```python
print(bool(cuphead.input.controller_support)) # True
if cuphead.input.controller_support:
  print("This will be printed")
```

Language and engine information require additionnal requests to fetch the data:
```python
# the data is fetched on the first call to Game.get_languages/engines
print('\n'.join(f'{l.language} audio:{l.audio} subtitles:{l.subtitles}' for l in cuphead.get_languages()))
print(', '.join(e.engine for e in cuphead.get_engines()))
```

It is possible to request specific games with `PCGW.get_game` or `PCGW.get_games`:
```python
print(client.get_game(page_id=63516).name) # Cuphead
print(client.get_game(steam_id=268910).name) # Cuphead
print(client.get_game(gog_id=1963513391).name) # Cuphead
print(client.get_game(page_name="Cuphead").name)
results = client.get_games(page_names=("Fez", "Limbo", "notagame"))
print(results["Fez"].name) # Fez
print(results["notagame"]) # None
```
`get_games` accepts the parameters `page_ids` and `page_names` and returns a dictionary
with these identifiers as keys to the resulting `Game` objects. Fetching multiple games
at a time with steam or gog ids is not supported as these ids can actually refer to
more than one PCGamingWiki page.

It is possible to retrieve the set of values of a given field in the database:
```python
print(client.get_possible_values('themes'))
print(client.get_possible_values('available_on'))
```
