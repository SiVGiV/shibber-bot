length = {
    "mm": {
        "name": "millimeters",
        "base_value": 1
    },
    "cm": {
        "name": "centimeters",
        "base_value": 10
    },
    "m": {
        "name": "meters",
        "base_value": 1000
    },
    "km": {
        "name": "kilometers",
        "base_value": 1000000
    },
    "feet": {
        "name": "feet",
        "base_value": 304.8
    },
    "inch": {
        "name": "inches",
        "base_value": 25.4
    },
    "miles": {
        "name": "miles",
        "base_value": 1609344
    },
    "yards": {
        "name": "yards",
        "base_value": 914.4
    },
    "bananas": {
        "name": "bananas",
        "base_value": 177.8
    }
}
weight = {
    "kg": {
        "name": "kilograms",
        "base_value": 1000
    },
    "lbs": {
        "name": "pounds",
        "base_value": 453.59
    },
    "g": {
        "name": "grams",
        "base_value": 1
    },
    "st": {
        "name": "stone",
        "base_value": 6350.29
    },
    "ton": {
        "name": "tonnes",
        "base_value": 1000000
    }
}

area = {
    "acre": {
        "name": "acre",
        "base_value": 2.471
    },
    "hectare": {
        "name": "hectare",
        "base_value": 1
    },
    "sqm": {
        "name": "square meters",
        "base_value": 10000
    },
    "sqkm": {
        "name": "square kilometers",
        "base_value": 0.01
    },
    "sqft": {
        "name": "square feet",
        "base_value": 107639.104
    },
    "sqyd": {
        "name": "square yards",
        "base_value": 11959.9
    }
}

speed = {
    "kmh": {
        "name": "kilometers per hour",
        "base_value": 1
    },
    "mps": {
        "name": "meters per second",
        "base_value": 3.6
    },
    "mph": {
        "name": "miles per hour",
        "base_value": 1.609
    },
    "knots": {
        "name": "knots",
        "base_value": 0.5399
    }
}

volume = {
    "l": {
        "name": "liters",
        "base_value": 1000
    },
    "ml": {
        "name": "milliliters",
        "base_value": 1
    },
    "gallon": {
        "name": "gallon (US)",
        "base_value": 3785.411
    },
    "pint": {
        "name": "pint (US)",
        "base_value": 473.176
    },
    "cuft": {
        "name": "cubic feet",
        "base_value": 28316.846
    },
    "cuinch": {
        "name": "cubic inches",
        "base_value": 16.387
    },
    "cubed_m": {
        "name": "M³",
        "base_value": 1000000
    }
}

temperature = {
    "c": {
        "name": "celsius"
    },
    "f": {
        "name": "fahrenheit"
    },
    "k": {
        "name": "kelvin"
    }
}


def convert_length(quantity: float, fr: str, to: str):
    return quantity * length[fr]["base_value"] / length[to]["base_value"]


def convert_weight(quantity: float, fr: str, to: str):
    return quantity * weight[fr]["base_value"] / weight[to]["base_value"]


def convert_area(quantity: float, fr: str, to: str):
    return quantity * area[fr]["base_value"] / area[to]["base_value"]


def convert_speed(quantity: float, fr: str, to: str):
    return quantity * speed[fr]["base_value"] / speed[to]["base_value"]


def convert_volume(quantity: float, fr: str, to: str):
    return quantity * volume[fr]["base_value"] / volume[to]["base_value"]


def convert_temperature(quantity: float, fr: str, to: str):
    if fr == "c":
        if to == "k":
            return quantity - 273.15
        elif to == "f":
            return (quantity * 1.8) + 32
    elif fr == "k":
        if to == "c":
            return quantity + 273.15
        elif to == "f":
            return ((quantity + 273.15) * 1.8) + 32
    else:
        if to == "k":
            return (quantity - 32) * 5 / 9 - 273.15
        elif to == "c":
            return (quantity - 32) * 5 / 9
    return quantity
