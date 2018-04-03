class Ability:
    def __init__(self, dict_data):
        self.name = dict_data['name']
        self.cost = dict_data['cost']

        self.range = dict_data['range']
        self.effects = dict_data['effects']


class Breed:
    def __init__(self, dict_data):
        self.name = dict_data['name']
        self.hp = dict_data['hp']
        self.ap = dict_data['ap']
        self.ap_per_second = dict_data['ap_per_second']
        self.physical_attack = dict_data['physical_attack']
        self.magical_attack = dict_data['magical_attack']
