import builtins

from direct.actor.Actor import Actor

from gamedb import GameDB

class Combatant:
    def __init__(self, parent_node, ability_inputs):
        gdb = GameDB.get_instance()

        if hasattr(builtins, 'base'):
            model = base.loader.load_model('clay_golem.bam')
            self.path = Actor(model.find('**/ClayGolemArm'))
            self.path.loop('cg.Run')
            self.path.reparent_to(parent_node)
        else:
            self.path = Actor()

        self.breed = gdb['breeds']['bobcatshark']

        self.name = self.breed.name
        self.current_hp = 100
        self.current_ap = 20

        self.ability_inputs = ability_inputs
        self.abilities = [gdb['abilities'][i] for i in self.breed.abilities]

        self.range_index = 0
        self.target = None

    @property
    def max_hp(self):
        return self.breed.hp

    @property
    def max_ap(self):
        return self.breed.ap

    @property
    def ap_per_second(self):
        return self.breed.ap_per_second

    @property
    def physical_attack(self):
        return self.breed.physical_attack

    @property
    def magical_attack(self):
        return self.breed.magical_attack

    @property
    def move_cost(self):
        return self.breed.move_cost

    def update(self, dt, range_index):
        self.range_index = range_index
        self.current_ap += self.ap_per_second * dt
        self.current_ap = min(self.current_ap, self.max_ap)

    def get_state(self):
        ability_labels = [
            base.event_mapper.get_labels_for_event(inp)[0]
            for inp in self.ability_inputs
        ]

        return {
            'name': self.name,
            'hp_current': self.current_hp,
            'hp_max': self.max_hp,
            'ap_current': int(self.current_ap),
            'ap_max': self.max_ap,
            'abilities': [{
                'name': ability.name,
                'input': _input.upper(),
                'range': ability.range,
                'cost': ability.cost,
                'usable': self.ability_is_usable(ability),
            } for ability, _input in zip(self.abilities, ability_labels)],
        }

    def ability_is_usable(self, ability):
        return (
            ability.cost < self.current_ap and
            self.range_index in ability.range and
            self.target is not None
        )
