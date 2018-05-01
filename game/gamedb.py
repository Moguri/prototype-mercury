import collections
import json
import os
import sys

import jsonschema

import datamodels


if hasattr(sys, 'frozen'):
    _APP_ROOT_DIR = os.path.dirname(sys.executable)
else:
    _APP_ROOT_DIR = os.path.dirname(__file__)
if not _APP_ROOT_DIR:
    print('empty app_root_dir')
    sys.exit()


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
    data_dir = os.path.join(_APP_ROOT_DIR, 'data')
    top_level_keys = (
        ('abilities', datamodels.Ability),
        ('breeds', datamodels.Breed),
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
            map(schema.validate, data_list)

        return {
            i['id']: data_model(i)
            for i in data_list
        }

    @classmethod
    def get_instance(cls):
        if cls._ptr is None:
            cls._ptr = cls()
        return cls._ptr


if __name__ == '__main__':
    print("GameDB:")
    for key, value in GameDB.get_instance().items():
        print("\t", key)
        for i in value.values():
            for j in repr(i).split('\n'):
                print("\t\t", j)
