import collections
import json
import os
import pprint
import sys

import fastjsonschema

from . import pathutils


class DataModel:
    _props = []
    _links = {}
    _schema = {}

    def __init__(self, dict_data):
        self.validate(dict_data)
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
            if isinstance(linkname, list):
                linkval = [
                    gdb[gdbkey][i]
                    for i in linkname
                ]
            else:
                linkval = gdb[gdbkey][linkname]
            setattr(self, prop, linkval)

    def to_dict(self):
        def _ga(prop):
            return getattr(self, prop)

        return {
            prop: _ga(prop).id if isinstance(_ga(prop), DataModel) else _ga(prop)
            for prop in self._props
        }

    @classmethod
    def validate(cls, _data): # pylint: disable=unused-argument
        return True

    @classmethod
    def from_schema(cls, schema):
        validate_func = fastjsonschema.compile(schema)
        def validate(cls, data): # pylint: disable=unused-argument
            try:
                validate_func(data)
            except fastjsonschema.exceptions.JsonSchemaException:
                print(f"Failed to load {schema['title']}", file=sys.stderr)
                pprint.pprint(schema)
                raise
        model = type(schema['title'] + 'Model', (DataModel,), {
            '_props': set(schema['properties'].keys()),
            '_links': schema.get('links', {}),
            '_schema': schema,
            'validate': classmethod(validate),
        })

        return model


def load_schema(schema_path):
    with open(schema_path) as schema_file:
        schema = json.load(schema_file)
    schema['$schema'] = 'http://json-schema.org/draft-04/schema#'
    schema['type'] = 'object'
    schema['required'] = list(
        key
        for key, value in schema['properties'].items()
        if 'default' not in value
    )
    schema['additionalProperties'] = False
    return schema


class GameDB(collections.UserDict):
    _ptr = None
    root_dir = pathutils.APP_ROOT_DIR.to_os_specific()
    data_dir = os.path.join(root_dir, 'data')
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

            schema = load_schema(os.path.join(self.schema_dir, f'{tlk}{self.schema_suffix}'))
            self.schema_to_datamodel[tlk] = DataModel.from_schema(schema)

        super().__init__({
            i: self._load_directory(i, self.schema_to_datamodel[i])
            for i in top_level_keys
            if os.path.exists(os.path.join(self.data_dir, i))
        })

    def get_schema(self, key):
        #pylint: disable=protected-access
        return self.schema_to_datamodel[key]._schema

    def _load_directory(self, dirname, data_model):
        dirpath = os.path.join(self.data_dir, dirname)

        data_list = []
        for filename in os.listdir(dirpath):
            with open(os.path.join(dirpath, filename)) as datafile:
                data = json.load(datafile)
            if not 'id' in data:
                data['id'] = filename.rsplit('.', 1)[0]
            data_list.append(data)


        for data in data_list:
            try:
                data_model.validate(data)
            except fastjsonschema.exceptions.JsonSchemaException:
                print(f"Failed to load {dirname}: {data['id']}")
                raise

        return {
            i['id']: data_model(i)
            for i in data_list
        }

    def _link_models(self):
        for key in self.keys():
            _ = [model.link(self) for model in self[key].values()]

    def to_dict(self):
        return {
            key: {
                k: v.to_dict() for k, v in value.items()
            }
            for key, value in self.items()
        }

    @classmethod
    def get_instance(cls):
        if cls._ptr is None:
            cls._ptr = cls()
            #pylint: disable=protected-access
            cls._ptr._link_models()
        return cls._ptr


def get_instance():
    return GameDB.get_instance()
