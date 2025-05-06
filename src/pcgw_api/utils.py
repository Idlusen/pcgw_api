from enum import Enum
import os
from typing import Callable, Any

TABLES_INFO_FILENAME = os.path.join(os.path.dirname(__file__), "tables.json")

def parse_list(j: dict, key: str, delimiter: str, post_processing: Callable[[str], Any]) -> list:
    """
    Parses a string value in a dictionary into a list.

    Parameters:
        j: dictionary to get the value from.
        key: key of the value to parse in the dictionary.
        delimiter: character delimiting the elements of the list in the string value.
        post_processing: function with wich to process each string element parsed.

    Returns:
        A list of values of the type returned by the post_processing function.
    """
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
    """
    Parses a string in a dictionary.

    Parameters:
        j: dictionary to get the string from.
        key: key of the string to parse in the dictionary.
        post_processing: function with wich to process the string parsed.

    Returns:
        The parsed value or None if the key is not present or the parsed value cannot
        be processed.
    """
    try:
        if s := j.get(key):
            return post_processing(s)
        else:
            return None
    except (TypeError, ValueError):
        return None

def parse_support_enum(j: dict, key: str) -> "Support":
    """
    Parses a string value from a dictionary into a Support object.

    The string value is used to initialize a Support object of the
    matching enum value.
    If the value is erroneous or a synonym of a value of Support,
    it is translated into the corresponding enum value,
    for instance "fakse" −> "false" or "yes" −> "true".
    If the value does not match any enum value of Support, the 
    Support object is initialized to OTHER_VALUE.
    In any case the attribute raw_value of the Support object is
    set to the value obtained from the input dictionary.

    Parameters:
        j: dictionary to get the string value from.
        key: key of the value to parse in the dictionary.

    Returns:
        A Support object.
    """
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
    """
    Represents the support status of a feature of a game in PCGamingWiki
    as an Enum.

    Values:
        NULL: no value in the PCGamingWiki database.
        UNKNOWN: support for the feature unknown.
        NA: feature not applicable.
        FALSE: feature not supported.
        LIMITED: feature not entirely supported.
        HACKABLE: feature not supported but can be activated with workarounds.
        TRUE: feature supported.
        COMPLETE: feature completely supported.
        ALWAYS_ON: feature supported and cannot be deactivated.
        OTHER_VALUE represents any value not enumerated. The actual value parsed
                    from the database is available in the attribute raw_value.

    When used as a boolean, an object of this class is True when the enum value
    is not NULL, UNKNOWN, NA or FALSE.
    """
    NULL = None
    UNKNOWN = 'unknown'
    NA = 'n/a'
    FALSE = 'false'
    LIMITED = 'limited'
    HACKABLE = 'hackable'
    TRUE = 'true'
    COMPLETE = 'complete'
    ALWAYS_ON = 'always on'
    OTHER_VALUE = 'other value'
    def __init__(self, *args):
        super().__init__(*args)
        self.raw_value: str|None = None
    def __bool__(self):
        return self.name not in ('NULL', 'UNKNOWN', 'NA', 'FALSE')
