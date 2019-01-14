from .blip import Blip, Action

from enum import Enum
from typing import Optional, List, Tuple

import json
import random

class CellType(Enum):
    EMPTY = 0
    WATER = 1
    FOOD = 2

class Cell:
    def __init__(self, type: CellType, **kwargs):
        self.type = type
        self.prop = kwargs
        self.entities = []

    def update(self) -> None:
        if self.isFood():
            self.prop['resource'] += self.prop['resource_build']

            if self.prop['resource'] > self.prop['resource_max']:
                self.prop['resource'] = self.prop['resource_max']

    # tries to consume value resources
    # @returns number of resources consumed
    def consume(self, value: int) -> Optional[int]:
        if self.isWater():
            return value

        if self.isFood():
            consumed = value if value <= self.prop['resource'] else self.prop['resource']

            self.prop['resource'] -= consumed
            return consumed

        return None

    def addEntity(self, entity: Blip) -> None:
        self.entities.append(entity)

    def removeEntity(self, entity: Blip) -> None:
        self.entities.remove(entity)

    def getEntities(self) -> List[Blip]:
        return self.entities

    def isEmpty(self) -> bool:
        return self.type is CellType.EMPTY

    def isWater(self) -> bool:
        return self.type is CellType.WATER

    def isFood(self) -> bool:
        return self.type is CellType.FOOD


class Medium:
    def __init__(self, input_file: str):
        self.prop = Medium.__default_prop()
        
        with open(input_file, 'r') as input:
            self.json_prop = input.read()

        self.prop.update(json.loads(self.json_prop))
        self.map_size = (20, 50)

        map_h, map_l = self.map_size
        self.map = [[Cell(CellType.EMPTY) for _ in range(map_l)] for _ in range(map_h)]

        self.water_size = (5, 5)
        water_h, water_l = self.water_size

        self.empty_cells = [(x, y) for x in range(map_h) for y in range(map_l)]

        for x in range(water_h):
            for y in range(water_l):
                self.map[x][y] = Cell(CellType.WATER)
                self.empty_cells.remove((x, y))

        self.forest_size = (20, 5)
        forest_h, forest_l = self.forest_size

        for x in range(forest_h):
            for y in range(forest_l):
                self.map[x][self.map_size[1] - forest_l + y] = \
                    Cell(CellType.FOOD,
                        resource=self.prop['FOOD-SIZE'],
                        resource_max=self.prop['FOOD-SIZE'],
                        resource_build=self.prop['FOOD-BUILD'])
                self.empty_cells.remove((x, self.map_size[1] - forest_l + y))

        self.entities = {}
        for _ in range(self.prop['INIT-POP']):
            x, y = random.choice(self.empty_cells)

            entity_life = self.get_entity_life(x, y)
            entity = Blip(self, entity_life, self.prop['BLIP'])

            self.entities[entity] = (x, y)
            self.map[x][y].addEntity(entity)

        self.population_history = []

    @staticmethod
    def __default_prop():
        return {
            'INIT-POP': 20,
            'AGE-VAR': 100,
            'SEE-RANGE': 25,
            'FOOD-SIZE': 100,
            'FOOD-BUILD': 1,
            'MAX-LIFE': 500,
            'BLIP': {
                'BUDDING-MIN-RES': 100,
                'MIN-BUDDING-AGE': 150,
                'MAX-BUDDING-AGE': 350,
                'BUDDING-PROB': 10,
                'BUDDING-TIME': 1,
                'BUD-FACTOR': 2,
                'POWER-TO-STAY': 1,
                'VAPOUR-TO-STAY': 1,
                'POWER-TO-MOVE': 2,
                'VAPOUR-TO-MOVE': 2,
                'MAX-RES': 300
            }
        }

    def isEmpty(self, x: int, y: int) -> bool:
        return self.map[x][y].isEmpty()

    def isWater(self, x: int, y: int) -> bool:
        return self.map[x][y].isWater()

    def isFood(self, x: int, y: int) -> bool:
        return self.map[x][y].isFood()

    def numberOfEntities(self, x: int, y: int) -> int:
        return len(self.map[x][y].getEntities())

    def update(self) -> None:        
        map_h, map_l = self.map_size

        for blip in self.entities:
            blip.new_cycle()

        for x in range(map_h):
            for y in range(map_l):
                cell = self.map[x][y]
                cell.update()

                for blip in cell.getEntities():
                    if blip.updated():
                        continue

                    allowed_actions = self.get_allowed_actions(x, y)
            
                    blip_action = blip.update(allowed_actions)

                    # calculate new coords
                    new_x = x
                    new_y = y
                    if blip_action == Action.Die:
                        # if entity diedededed just remove it
                        cell.removeEntity(blip)
                        self.entities.pop(blip)

                        continue
                    elif blip_action == Action.North:
                        new_x = x - 1
                    elif blip_action == Action.South:
                        new_x = x + 1
                    elif blip_action == Action.West:
                        new_y = y - 1
                    elif blip_action == Action.East:
                        new_y = y + 1

                    # move the entity
                    new_cell = self.map[new_x][new_y]
                    if new_cell != cell:
                        cell.removeEntity(blip)
                        new_cell.addEntity(blip)

                        self.entities[blip] = (new_x, new_y)

                    if new_cell.isWater():
                        water_need = blip.getWaterNeed()
                        water_available = new_cell.consume(water_need)

                        if water_available:
                            blip.drink(water_available)
                    elif new_cell.isFood():
                        food_need = blip.getFoodNeed()
                        food_available = new_cell.consume(food_need)

                        if food_available:
                            blip.eat(food_available)

        self.check_population_change()


    def get_allowed_actions(self, x: int, y: int) -> List[Action]:
            map_h, map_l = self.map_size
            
            allowed_actions = [Action.Die, Action.Stay]

            if x > 0:
                allowed_actions.append(Action.North)
            if x < map_h - 1:
                allowed_actions.append(Action.South)
            if y > 0:
                allowed_actions.append(Action.West)
            if y < map_l - 1:
                allowed_actions.append(Action.East)

            return allowed_actions


    def get_entity_life(self, x: int, y: int) -> int:
        map_h, map_l = self.map_size
        if x < 0 or y < 0 or x >= map_h or y >= map_l:
            return 0

        max_life = self.prop['MAX-LIFE']
        max_life_var = self.prop['AGE-VAR']

        mid_h, mid_l = (map_h // 2, map_l // 2)

        max_dist = mid_h + mid_l

        dist = abs(mid_h - x) + abs(mid_l - y)

        life_var = (dist / max_dist) * max_life_var

        return max_life - max_life_var + int(life_var)


    def new_entity_sprouted(self, source_blip: Blip) -> None:
        x, y = self.entities[source_blip]

        entity_life = self.get_entity_life(x, y)
        blip = Blip(self, entity_life, self.prop['BLIP'])

        self.map[x][y].addEntity(blip)
        self.entities[blip] = (x, y)


    # checks the population change
    # and ends simulation if it's not changed by 10%
    # by setting self.entities to an empty dict
    def check_population_change(self) -> None:
        crr_pop = len(self.entities)
        self.population_history.append(crr_pop)

        if len(self.population_history) > self.prop['MAX-LIFE']:
            # get mean
            mean = sum(self.population_history[:-1]) / (len(self.population_history) - 1)
            
            # pop the oldest history
            self.population_history = self.population_history[1:]

            # if the fluctuation is within 10% stop simulation
            if 9/10 * mean <= crr_pop and 11/10 * mean >= crr_pop:
                print('End simulation - population fluctuation is within 10%')
                self.entities = {}


    def get_sight(self, source: Blip):
        x, y = self.entities[source]

        water_found: List[Action] = []
        food_found: List[Action] = []
        blips_found: List[Action] = []

        map_h, map_l = self.map_size
        d = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        action = [Action.East, Action.South, Action.West, Action.North]

        queue = []
        visited = [(x, y)]
        for index in range(len(d)):
            m_h, m_l = d[index]
            n_x, n_y = (x + m_h, y + m_l)

            if n_x < 0 or n_x >= map_h or\
                n_y < 0 or n_y >=map_l:
                continue
        
            # each element in queue is (x, y, length_till_here, first_action_to_get_here)
            queue.append((n_x, n_y, 1, action[index]))
            visited.append((n_x, n_y))

        while queue:
            x, y, l, act = queue[0]
            queue = queue[1:]

            if l > self.prop['SEE-RANGE']:
                continue

            cell = self.map[x][y]
            if cell.isFood():
                food_found.append((l, act))
            elif cell.isWater():
                water_found.append((l, act))

            if len(cell.getEntities()) > 0:
                blips_found.append((l, act))

            for move in d:
                m_h, m_l = move
                n_x, n_y = (x + m_h, y + m_l)

                if (n_x, n_y) in visited:
                    continue

                if n_x < 0 or n_x >= map_h or\
                    n_y < 0 or n_y >=map_l:
                    continue

                queue.append((n_x, n_y, l + 1, act))
                visited.append((n_x, n_y))

        dir_to_water = None
        if water_found:
            _, dir_to_water = water_found[0]

        dir_to_food = None
        if food_found:
            _, dir_to_food = food_found[0]

        dir_to_blip = None
        if blips_found:
            _, dir_to_blip = blips_found[0]

        return dir_to_water, dir_to_food, dir_to_blip
