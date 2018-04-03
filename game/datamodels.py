class Ability:
    def __init__(self, dict_data):
        self.name = dict_data['name']
        self.cost = dict_data['cost']

        self.range = dict_data['range']
        self.effects = dict_data['effects']
