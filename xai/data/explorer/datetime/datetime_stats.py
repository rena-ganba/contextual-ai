from typing import Dict, List

from xai.data.constants import STATSKEY
from xai.data.exceptions import InvalidTypeError, InconsistentSize
from xai.data.abstract_stats import AbstractStats


class DatetimeStats(AbstractStats):

    def __init__(self, frequency_count, resolution_list):
        self.resolution_list = resolution_list
        self.frequency_count = frequency_count

    @property
    def frequency_count(self):
        return self._frequency_count

    @frequency_count.setter
    def frequency_count(self, frequency: Dict[str, int]):
        self._total_count = 0
        self._cur_resolution_level = 0

        def __check_dict(dict_item):
            if type(dict_item) != dict:
                self._total_count = 0
                raise InvalidTypeError('frequency_count', type(dict_item), '<dict>')
            height_list = []
            for key, value in dict_item.items():
                if type(key) not in [str, int]:
                    self._total_count = 0
                    raise InvalidTypeError('frequency_count:key', type(key), '<str> or <int>')
                if type(value) != [dict or int]:
                    self._total_count = 0
                    raise InvalidTypeError('frequency_count:value', type(value), '<int> or <dict>')

                if type(value) == dict:
                    height = __check_dict(value)
                    height_list.append(height)

                if type(value) == int:
                    self._total_count += value
                    height_list.append(0)
            return max(height_list) + 1

        max_level = __check_dict(frequency)
        if len(self.resolution_list) != max_level:
            raise InconsistentSize('frequency_count depth', 'resolution_list', max_level, len(self.resolution_list))
        self._frequency_count = frequency

    @property
    def resolution_list(self):
        return self._resolution_list

    @resolution_list.setter
    def resolution_list(self, resolution_list: List[str]):
        if type(resolution_list) != list:
            raise InvalidTypeError('resolution_list', type(resolution_list), '<list>')
        for value in resolution_list:
            if type(value) != str:
                raise InvalidTypeError('resolution_list: item', type(value), '<str>')

    def to_json(self) -> Dict:
        """
        map stats information into a json object

        Returns:
            a json that represents frequency count and total count
        """

        json_obj = dict()
        json_obj[STATSKEY.TOTAL_COUNT] = self._total_count
        json_obj[STATSKEY.DISTRIBUTION] = self._frequency_count
        json_obj[STATSKEY.FIELDS] = self._resolution_list
        return json_obj
