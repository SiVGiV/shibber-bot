import requests

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


class CurrencyConverter:
    def __init__(self, crypto_key):
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        crypto_url = "http://api.coinlayer.com/api/live?access_key=" + crypto_key
        self.data = requests.get(url).json()
        if "rates" not in self.data:
            self.data.update({"rates":{}})
        self.crypto_data = requests.get(crypto_url).json()
        if "rates" not in self.crypto_data:
            self.crypto_data.update({"rates":{}})
        self.currencies = self.data["rates"]
        temp = map(
            lambda x: (x[0], 1 / x[1] if x[1] != 0 else 0),
            self.crypto_data["rates"].items()
        )
        self.currencies.update(temp)

    def convert(self, from_currency, to_currency, amount):
        # first convert it into USD if it is not in USD.
        # because our base currency is USD
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        if from_currency not in self.currencies or to_currency not in self.currencies:
            raise ValueError("A currency code passed does not exist")
        if from_currency != 'USD':
            amount /= self.currencies[from_currency]

            # limiting the precision to 4 decimal places
        amount = round(amount * self.currencies[to_currency], 4)
        return amount
