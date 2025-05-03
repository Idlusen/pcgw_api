from enum import Enum
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

def parse_support_enum(j: dict, key: str):
    value = j.get(key)
    if value in [field.value for field in Support]:
        new_enum = Support(value)
    elif value == 'fakse': # normalize erroneous values
        new_enum = Support('false')
    elif value == 'yes': # normalize erroneous values
        new_enum = Support('true')
    elif value == 'partial': # normalize erroneous values
        new_enum = Support('limited')
    else:
        new_enum = Support('other value')
    new_enum.raw_value = value
    return new_enum

class Support(Enum):
    NULL = None
    UNKNOWN = 'unknown'
    NA = 'n/a'
    FALSE = 'false'
    LIMMITED = 'limited'
    HACKABLE = 'hackable'
    TRUE = 'true'
    COMPLETE = 'complete'
    ALWAYS_ON = 'always on'
    OTHER_VALUE = 'other value'
    def __init__(self, *args):
        super().__init__(*args)
        self.raw_value: str|None = None

