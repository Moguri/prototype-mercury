import collections
import json
import os
import pprint

import jsonschema

from . import pathutils


def _extend_with_default(validator_class):
    validate_properties = validator_class.VALIDATORS["properties"]

    def set_defaults(validator, properties, instance, schema):
        for prop, subschema in properties.items():
            if "default" in subschema:
                instance.setdefault(prop, subschema["default"])

        for error in validate_properties(validator, properties, instance, schema):
            yield error

    return jsonschema.validators.extend(
        validator_class, {"properties" : set_defaults},
    )


_VALIDATOR = _extend_with_default(jsonschema.Draft4Validator)


VALIDATE_SCHEMA = False


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


class GameDB(collections.UserDict):
    _ptr = None
    data_dir = os.path.join(pathutils.APP_ROOT_DIR, 'data')
    schema_dir = os.path.join(data_dir, 'schemas')
    schema_suffix = '.schema.json'

    def __init__(self):
        self.schema_to_datamodel = {}
        top_level_keys = [
            i.replace(self.schema_suffix, '')
            for i in os.listdir(self.schema_dir)
            if i.endswith(self.schema_suffix)
        ]
        for tlk in top_level_keys:
            if tlk in self.schema_to_datamodel:
                continue

            with open(os.path.join(self.schema_dir, f'{tlk}{self.schema_suffix}')) as schema_file:
                schema = json.load(schema_file)
                self.schema_to_datamodel[tlk] = DataModel.from_schema(schema)

        super().__init__({
            i: self._load_directory(i, self.schema_to_datamodel[i])
            for i in top_level_keys
            if os.path.exists(os.path.join(self.data_dir, i))
        })

    def _load_directory(self, dirname, data_model):
        dirpath = os.path.join(self.data_dir, dirname)

        data_list = [
            json.load(open(os.path.join(dirpath, filename)))
            for filename in os.listdir(dirpath)
        ]

        if VALIDATE_SCHEMA:
            schema_name = '{}.schema.json'.format(dirname)
            schema_path = os.path.join(self.data_dir, 'schemas', schema_name)
            with open(schema_path) as schema_file:
                schema = _VALIDATOR(json.load(schema_file))
            list(map(schema.validate, data_list))

        return {
            i['id']: data_model(i)
            for i in data_list
        }

    def _link_models(self):
        for key in self.keys():
            _ = [model.link(self) for model in self[key].values()]

    @classmethod
    def get_instance(cls):
        if cls._ptr is None:
            cls._ptr = cls()
            #pylint: disable=protected-access
            cls._ptr._link_models()
        return cls._ptr


def get_instance():
    return GameDB.get_instance()


def dump_db():
    print("GameDB:")
    for key, value in get_instance().items():
        print("\t", key)
        for i in value.values():
            for j in repr(i).split('\n'):
                print("\t\t", j)


if __name__ == '__main__':
    dump_db()
