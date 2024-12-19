import json

class Config:
    """
    A class to load and access configuration data as a dictionary.
    """

    def __init__(self, config_path: str):
        with open(config_path, 'r') as file:
            self._data = json.load(file)

    def __getitem__(self, key):
        """
        Allows accessing keys as if Config is a dictionary.
        """
        return self._data[key]

    def get(self, key, default=None):
        """
        Implements a 'get' method similar to dict.
        """
        return self._data.get(key, default)
