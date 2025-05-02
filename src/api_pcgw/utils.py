from typing import Callable, Any

def parse_list(j: dict, key: str, delimiter: str, post_processing: Callable[[str], Any]) -> list:
    if s := j.get(key):
        l = []
        for x in set(filter(lambda x:x.strip(), s.split(delimiter))):
            try:
                l.append(post_processing(x))
            except ValueError:
                pass
        return l
    else:
        return []

def parse_value(j: dict, key: str, post_processing: Callable[[str], Any]) -> Any|None:
    try:
        if s := j.get(key):
            return post_processing(s)
        else:
            return None
    except (TypeError, ValueError):
        return None
