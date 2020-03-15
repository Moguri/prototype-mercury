#pylint: disable=attribute-defined-outside-init

import pprint


class DataModel:
    _props = []
    _links = {}

    def __init__(self, dict_data):
        self._props |= {'id', 'name'}
        for prop in self._props:
            setattr(self, prop, dict_data[prop])

    def __repr__(self):
        return '{}({})'.format(
            type(self).__name__,
            pprint.pformat(self.__dict__)
        )

    def link(self, gdb):
        for prop, gdbkey in self._links.items():
            linkname = getattr(self, prop)
            setattr(self, prop, gdb[gdbkey][linkname])

    def to_dict(self):
        def _ga(prop):
            return getattr(self, prop)

        return {
            prop: _ga(prop).id if isinstance(_ga(prop), DataModel) else _ga(prop)
            for prop in self._props
        }

    @classmethod
    def from_schema(cls, schema):
        model = type(schema['title'] + 'Model', (DataModel,), {
            '_props': set(schema['properties'].keys()),
            '_links': schema.get('links', {}),
        })

        return model
