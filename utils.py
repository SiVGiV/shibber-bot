from discord_slash.utils import manage_components


def get_number_emoji_dict(n: int):
    # receives a number between 0 and 9 (inclusive)
    # returns an emoji dict from the discord_slash.utils package
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
    # receives a number between 0 and 9 (inclusive)
    # returns a string containing the number emoji for that number
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
    # receives a string and truncates it to fit max_len
    # mid_ellipsis: True - middle ellipsis, False - end ellipsis
    if len(st) > max_len:
        if mid_ellipsis:
            new_st = st[:max_len/2-2] + "..." + st[max_len/2+2:]
        else:
            new_st = st[:max_len-3] + "..."
    else:
        return st
    return new_st


def list2str(var, max_items=1, join_str=", "):
    if isinstance(var, list):
        return join_str.join(var[:min(len(var), max_items)]).split("::")[0]
    elif isinstance(var, str):
        return str
    elif isinstance(var, int) or isinstance(var, float):
        return str(var)
