import random


from direct.showbase.MessengerGlobal import messenger


class Controller():
    DEFAULT_TIMEOUT = 1.5

    def __init__(self, combatant):
        self.combatant = combatant
        self.ability_index = None
        self.decision_timeout = 0
        self.target_range = None

    def update(self, dt):
        if self.ability_index is not None:
            ability = self.combatant.abilities[self.ability_index]

            if self.combatant.ability_is_usable(ability):
                messenger.send(self.combatant.ability_inputs[self.ability_index])
                self.decision_timeout = 0
            elif self.combatant.range_index < self.target_range:
                messenger.send('p2-move-right')
            elif self.combatant.range_index > self.target_range:
                messenger.send('p2-move-left')

        self.decision_timeout -= dt
        if self.decision_timeout <= 0:
            # Pick a new decision
            self.ability_index = random.choice([0, 1, 2, 3, None, None, None])
            self.target_range = None
            self.decision_timeout = self.DEFAULT_TIMEOUT

            if self.ability_index is not None:
                ability = self.combatant.abilities[self.ability_index]
                self.target_range = random.choice(ability.range)
