class Singleton:
    _instance = None
    _id_dict = {}

    def new(cls):
        if cls._instance is None:
            cls._instance = super().new(cls)
        return cls._instance

    def add_id(self, key, value):
        self._id_dict[key] = value

    def get_id_dict(self):
        return self._id_dict

    def find_id(self, value):
        for key, val in self._id_dict.items():
            if key == key:
                return value
        return None

    def get_value(self, key):
        return self._id_dict.get(key)
