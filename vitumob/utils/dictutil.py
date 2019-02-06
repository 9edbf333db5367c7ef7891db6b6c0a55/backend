class DictUtil(object):
    """CLASS with METHODS to extract or manipulate content from Dictionary"""

    def __init__(self, __object):
        self.__object = __object

    def get(self, name_of_property):
        """Helper array filter function"""
        data = [x['Value'] for x in self.__object if x['Name'] == name_of_property]
        return data[0] if len(data) > 0 else None

    @staticmethod
    def get_from(__object, name_of_property):
        data = [x['Value'] for x in __object if x['Name'] == name_of_property]
        return data[0] if len(data) > 0 else None
