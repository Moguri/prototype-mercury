import collections
import json
import os

import jsonschema

from . import datamodels
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


class GameDB(collections.UserDict):
    _ptr = None
    data_dir = os.path.join(pathutils.APP_ROOT_DIR, 'data')
    schema_dir = os.path.join(data_dir, 'schemas')
    schema_suffix = '.schema.json'

    def __init__(self):
        schema_to_datamodel = {
            'monsters': datamodels.Monster,
        }
        top_level_keys = [
            i.replace(self.schema_suffix, '')
            for i in os.listdir(self.schema_dir)
            if i.endswith(self.schema_suffix)
        ]
        for tlk in top_level_keys:
            if tlk in schema_to_datamodel:
                continue

            with open(os.path.join(self.schema_dir, f'{tlk}{self.schema_suffix}')) as schema_file:
                schema = json.load(schema_file)
                print(f'{tlk}')
                schema_to_datamodel[tlk] = datamodels.DataModel.from_schema(schema)

        super().__init__({
            i: self._load_directory(i, schema_to_datamodel[i])
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
