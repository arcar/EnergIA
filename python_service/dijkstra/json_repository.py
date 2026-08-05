import json


class JsonRepository:

    def __init__(self, filename: str):
        self.filename = filename
        self._data = None

    def load(self):
        if self._data is None:
            with open(self.filename, "r", encoding="utf-8") as f:
                self._data = json.load(f)

        return self._data

    def get_regions(self):
        return self.load()["regions"]

    def get_plants(self):
        return self.load()["plants"]

    def get_edges(self):
        return self.load()["plant_edges"]