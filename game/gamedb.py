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
    top_level_keys = (
        ('abilities', datamodels.Ability),
        ('breeds', datamodels.Breed),
        ('monsters', datamodels.Monster),
    )

    def __init__(self):
        super().__init__({
            i[0]: self._load_directory(*i)
            for i in self.top_level_keys
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
        for key in self.top_level_keys:
            _ = [model.link(self) for model in self[key[0]].values()]

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
