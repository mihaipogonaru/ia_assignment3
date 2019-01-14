from . import medium

from enum import Enum
from typing import List, Tuple, Dict, Optional

import random

class Action(Enum):
    Die = -3
    East = -2
    North = -1
    Stay = 0
    South = 1
    West = 2

class Blip:
    def __init__(self, med, entity_life: int, prop: Dict[str, any]):
        self.medium: medium.Medium = med
        self.age = 0
        self.max_age = entity_life
        self.prop = prop

        self.sprouting_chance = self.prop['BUDDING-PROB'] / 100
        self.sprouting_left = 0
        
        self.resources = self.prop['MAX-RES'], self.prop['MAX-RES']

        self.upd = True

    def new_cycle(self) -> None:
        self.upd = False

    def updated(self) -> bool:
        return self.upd

    def update(self, allowed_actions: List[Action]) -> Action:
        if self.upd:
            # shouldn't happen
            return None
        
        self.upd = True

        self.advance_sprouting()
        self.try_to_sprout()

        #print(f'{self.resources} - {self.is_sprouting()}')

        self.age += 1
        # decide on action
        action = self.decide([action for action in allowed_actions if action is not Action.Die])
        # filter action (see if we have enough resources or life left)
        action = self.filter(action)

        water, food = self.resources
        water_c, food_c = self.get_resources_consumption(action)
        self.resources = (water - water_c, food - food_c)

        #print(f'{self.age} {self.max_age} <-> {self.resources} - {action}')
        #print()

        return action

    def decide(self, allowed_actions: List[Action]) -> Action:
        water_s, food_s, blip_s = self.medium.get_sight(self)

        max_res = self.prop['MAX-RES']
        food_n = self.getFoodNeed()
        water_n = self.getWaterNeed()

        water_move = self.prop['VAPOUR-TO-MOVE']
        water_stay = self.prop['VAPOUR-TO-STAY']
        food_move = self.prop['POWER-TO-MOVE']
        food_stay = self.prop['POWER-TO-STAY']

        # if i'm too old just stay and die
        if self.age > self.prop['MAX-BUDDING-AGE']:
            return Action.Stay

        # if i don't need too much food or water stay near blips
        # or check if it's better to stay or to wander
        if water_n < 0.1 * max_res and food_n < 0.1 * max_res:
            if blip_s:
                return blip_s

            if water_move + food_move > water_stay + food_stay and \
                self.age >= self.prop['MIN-BUDDING-AGE']:
                return Action.Stay

            return random.choice([action for action in allowed_actions if action is not Action.Stay])

        # if i need a lot of water go to water
        if water_n > 1.3 * food_n:
            if water_s:
                return water_s

            return Action.West

        # if i need a lot of food go to food
        if food_n > 1.3 * water_n:
            if food_s:
                return food_s
            
            return Action.East
        
        # if i know where food is go there
        if food_s:
            return food_s

        # if i know where water is go there
        if water_s:
            return water_s

        # check the raport between resources needed and 
        # cost to move
        if food_n / water_n > food_move / water_move:
            return Action.East

        return Action.West

    def filter(self, action: Action) -> Action:
        if action is Action.Die:
            return action
        
        if self.age == self.max_age:
            return Action.Die

        water, food = self.resources
        water_n, food_n = self.get_resources_consumption(action)

        if water <= water_n or food <= food_n:
            if action is Action.Stay:
                return Action.Die

            action = Action.Stay
            water_n, food_n = self.get_resources_consumption(action)

        if water <= water_n or food <= food_n:
            return Action.Die

        return action

    def get_resources_consumption(self, action: Action) -> Tuple[int, int]:
        res = (0, 0)

        if action is Action.Die:
            return res

        if action is Action.Stay:
            res = (self.prop['VAPOUR-TO-STAY'], self.prop['POWER-TO-STAY'])
        else:
            res = (self.prop['VAPOUR-TO-MOVE'], self.prop['POWER-TO-MOVE'])

        water, food = res
        if self.is_sprouting():
            water *= self.prop['BUD-FACTOR']
            food *= self.prop['BUD-FACTOR']

        return water, food


    def is_sprouting(self) -> bool:
        return self.sprouting_left > 0


    # advances a current sprouting process
    def advance_sprouting(self) -> None:
        if not self.is_sprouting():
            return

        self.sprouting_left -= 1

        if not self.sprouting_left:
            self.medium.new_entity_sprouted(self)


    # tries to start a sprouting process
    def try_to_sprout(self) -> None:
        if self.is_sprouting():
            return

        if self.age < self.prop['MIN-BUDDING-AGE'] or \
        self.age > self.prop['MAX-BUDDING-AGE']:
            return

        water, food = self.resources
        if water < self.prop['BUDDING-MIN-RES'] or food < self.prop['BUDDING-MIN-RES']:
            return

        if random.random() < self.sprouting_chance:
            self.sprouting_left = self.prop['BUDDING-TIME']


    def getWaterNeed(self) -> int:
        water, _ = self.resources
        
        return self.prop['MAX-RES'] - water


    def getFoodNeed(self) -> int:
        _, food = self.resources
        
        return self.prop['MAX-RES'] - food


    def drink(self, value: Optional[int]) -> None:
        if not value:
            return
        
        water, food = self.resources

        water_n = water + value

        if water_n > self.prop['MAX-RES']:
            water_n = self.prop['MAX-RES']

        self.resources = (water_n,  food)


    def eat(self, value: Optional[int]) -> None:
        if not value:
            return
        
        water, food = self.resources

        food_n = food + value

        if food_n > self.prop['MAX-RES']:
            food_n = self.prop['MAX-RES']

        self.resources = (water, food_n)
        