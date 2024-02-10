import threading
import copy

class protected_dict:
    _instance_lock = threading.Lock()
    _dictionary = {}

    @classmethod
    def instance(cls):
        if not hasattr(cls, "_instance"):
            with cls._instance_lock:
                if not hasattr(cls, "_instance"):
                    cls._instance = cls()
        return cls._instance

    def set_value(self, key, value):
        with self._instance_lock:
            self._dictionary[key] = copy.deepcopy(value)

    def get_value(self, key):
        with self._instance_lock:
            return copy.deepcopy(self._dictionary.get(key))

    def set_values(self, values_dict):
        with self._instance_lock:
            for key, value in values_dict.items():
                self._dictionary[key] = copy.deepcopy(value)

    def get_values(self, keys):
        with self._instance_lock:
            return [copy.deepcopy(self._dictionary.get(key)) for key in keys]

if __name__ == '__main__':
    singleton_dict = protected_dict.instance()
    singleton_dict.set_value("key0", "value0")
    value0 = singleton_dict.get_value("key0")
    singleton_dict.set_values({"key1": "value1", "key2": "value2", "key3": "value3"})
    values = singleton_dict.get_values(["key1", "key2", "key3"])
    value1, value2, value3 = singleton_dict.get_values(["key1", "key2", "key3"])
    print(value0)
    print(values)
    print(value1)
    print(value2)
    print(value3)
    print(protected_dict.instance().get_values(["key0", "key3"]))
