from discord_slash.utils import manage_components
import requests


def get_number_emoji_dict(n: int):
    """
    returns a passed integer as a Discord emoji dictionary
    :param n: any integer between 0 and 9 (both inclusive)
    :return: an emoji dictionary from the discord_slash.utils package
    """
    if not n <= 9 and not n >= 0:
        raise ValueError("Expected number between 0 and 9 (inclusive)")
    button_numbers = [
        manage_components.emoji_to_dict("0️⃣"),
        manage_components.emoji_to_dict("1️⃣"),
        manage_components.emoji_to_dict("2️⃣"),
        manage_components.emoji_to_dict("3️⃣"),
        manage_components.emoji_to_dict("4️⃣"),
        manage_components.emoji_to_dict("5️⃣"),
        manage_components.emoji_to_dict("6️⃣"),
        manage_components.emoji_to_dict("7️⃣"),
        manage_components.emoji_to_dict("8️⃣"),
        manage_components.emoji_to_dict("9️⃣")
    ]
    return button_numbers[n]


def get_number_emoji(n: int) -> str:
    """
    returns a unicode emoji for the number passed
    :param n: any integer between 0 and 9 (both inclusive)
    :return: a string containing a number emoji for that number
    """
    if not n <= 9 and not n >= 0:
        raise ValueError("Expected number between 0 and 9 (inclusive)")
    button_numbers = [
        "0️⃣",
        "1️⃣",
        "2️⃣",
        "3️⃣",
        "4️⃣",
        "5️⃣",
        "6️⃣",
        "7️⃣",
        "8️⃣",
        "9️⃣"
    ]
    return button_numbers[n]


def ellipsis_truncate(st, max_len, mid_ellipsis=False):
    """
    Truncates the string and adds an ellipsis
    :param st: any string
    :param max_len: maximum string length
    :param mid_ellipsis: True if you want the ellipsis in the middle, false if at the end
    :return: A truncated string
    """
    if len(st) > max_len:
        if mid_ellipsis:
            new_st = st[:max_len/2-2] + "..." + st[max_len/2+2:]
        else:
            new_st = st[:max_len-3] + "..."
    else:
        return st
    return new_st


def list2str(var, max_items=1, join_str=", "):
    """
    Concatenates list items into one string.
    :param var: any variable
    :param max_items: maximum number of items to concatenate
    :param join_str: The string to join items with
    :return: if list, returns a concatenated string.
    """
    if isinstance(var, list):
        return join_str.join(var[:min(len(var), max_items)]).split("::")[0]
    elif isinstance(var, str):
        return str
    elif isinstance(var, int) or isinstance(var, float):
        return str(var)


def magnet_shorten(token: str, magnet: str):
    """
    Shortens a torrent magnet link.
    :param magnet: (str) a magnet string
    :param token: (str) the tinyurl api token
    :return: a shortened link
    """
    api_address = "http://api.tinyurl.com/create?api_token=" + token
    api_parameters = {
        "url": magnet,
        "domain": "tinyurl.com"
        }
    try:
        res = requests.post(api_address, api_parameters)
        res.raise_for_status()
    except Exception:
        raise NameError("Encountered an API error.")
    else:
        results = res.json()
        if results["code"] == 0:
            return results["data"]["tiny_url"]
        else:
            raise NameError("API failed")


def none2str(x):
    """
    returns a string if variable is None
    :param x: any type variable
    :return: empty string if None
    """
    if x is None:
        return ""
    else:
        return x
