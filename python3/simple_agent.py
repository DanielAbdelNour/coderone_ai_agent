from game_state import GameState
import asyncio
import random
import os

import numpy as np
from collections import defaultdict
import queue

import utility
import constants

uri = os.environ.get(
    'GAME_CONNECTION_STRING') or "ws://127.0.0.1:3000/?role=agent&agentId=agentA&name=defaultName"

actions = ["up", "down", "left", "right", "bomb", "detonate"]


class Agent():
    def __init__(self):
        self._client = GameState(uri)

        self._client.set_game_tick_callback(self._on_game_tick)
        loop = asyncio.get_event_loop()
        connection = loop.run_until_complete(self._client.connect())
        tasks = [
            asyncio.ensure_future(self._client._handle_messages(connection)),
        ]
        loop.run_until_complete(asyncio.wait(tasks))

        self._recently_visited_positions = []
        self._recently_visited_length = 6
        # Keep track of the previous direction to help with the enemy standoffs.
        self._prev_direction = None

    def _get_bomb_to_detonate(self, game_state) -> [int, int] or None:
        agent_number = game_state.get("connection").get("agent_number")
        entities = self._client._state.get("entities")
        bombs = list(filter(lambda entity: entity.get(
            "owner") == agent_number and entity.get("type") == "b", entities))
        bomb = next(iter(bombs or []), None)
        if bomb != None:
            return [bomb.get("x"), bomb.get("y")]
        else:
            return None

    def convert_coords(self, board, coords):
        x, y = coords
        y = (len(board)-1) - y
        return (y,x)
        

    async def _on_game_tick(self, tick_number, game_state):
        my_agent_number = game_state['connection']['agent_number']
        my_agent_data = game_state['agent_state'][str(my_agent_number)]

        board, bomb_map = self.generate_board(game_state)
        my_position = self.convert_coords(board, my_agent_data['coordinates'])
        bombs = self.convert_bombs(bomb_map)

        enemies = [constants.Item.Agent1 if my_agent_number == 0 else constants.Item.Agent0]
        ammo = int(my_agent_data['inventory']['bombs'])
        blast_strength = int(my_agent_data['blast_diameter'])
        items, dist, prev = self._djikstra(board, my_position, bombs, enemies, depth=10)

        asd

        return None


    def generate_board(self, game_state):
        ent_type_dict = constants.ent_type_dict

        board = np.zeros((game_state['world']['height'], game_state['world']['width']))
        bomb_map = np.zeros_like(board)

        # place entities on the board
        for ent in game_state['entities']:
            ent_type = ent['type']
            ent_x = ent['x']
            ent_y = ent['y']

            ent_exp = ent.get("expires")
            ent_own = ent.get("owner")

            board[(len(board)-1) - ent_y, ent_x] = ent_type_dict[ent_type]

            # add bombs to bomb map
            if ent_type == 'b':
                bomb_map[(len(board)-1) - ent_y, ent_x] = ent['blast_diameter']


        # place agents on the board
        agents = game_state['agent_state']
        agent0_x, agent0_y = agents['0']['coordinates']
        agent1_x, agent1_y = agents['1']['coordinates']

        board[(len(board)-1) - agent0_y, agent0_x] = 10
        board[(len(board)-1) - agent1_y, agent1_x] = 11

        return board.astype(int), bomb_map.astype(int)

    def convert_bombs(self, bomb_map):
        '''Flatten outs the bomb array'''
        ret = []
        locations = np.where(bomb_map > 0)
        for r, c in zip(locations[0], locations[1]):
            ret.append({
                'position': (r, c),
                'blast_strength': int(bomb_map[(r, c)])
            })
        return ret  

    def generate_random_action(self):
        actions_length = len(actions)
        return actions[random.randint(0, actions_length - 1)]

    
    @staticmethod
    def _djikstra(board, my_position, bombs, enemies, depth=None, exclude=None):
        assert (depth is not None)

        if exclude is None:
            exclude = [
                constants.Item.Metal_Block, constants.Item.Blast, constants.Item.Ore_Block
            ]

        def out_of_range(p_1, p_2):
            '''Determines if two points are out of rang of each other'''
            x_1, y_1 = p_1
            x_2, y_2 = p_2
            return abs(y_2 - y_1) + abs(x_2 - x_1) > depth

        items = defaultdict(list)
        dist = {}
        prev = {}
        Q = queue.Queue()

        my_x, my_y = my_position
        for r in range(max(0, my_x - depth), min(len(board), my_x + depth)):
            for c in range(max(0, my_y - depth), min(len(board), my_y + depth)):
                position = (r, c)
                if any([out_of_range(my_position, position), utility.position_in_items(board, position, exclude),]):
                    continue

                prev[position] = None
                item = constants.Item(board[position])
                items[item].append(position)
                
                if position == my_position:
                    Q.put(position)
                    dist[position] = 0
                else:
                    dist[position] = np.inf


        for bomb in bombs:
            if bomb['position'] == my_position:
                items[constants.Item.Bomb].append(my_position)

        while not Q.empty():
            position = Q.get()

            if utility.position_is_passable(board, position, enemies):
                x, y = position
                val = dist[(x, y)] + 1
                for row, col in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    new_position = (row + x, col + y)
                    if new_position not in dist:
                        continue

                    if val < dist[new_position]:
                        dist[new_position] = val
                        prev[new_position] = position
                        Q.put(new_position)
                    elif (val == dist[new_position] and random.random() < .5):
                        dist[new_position] = val
                        prev[new_position] = position   


        return items, dist, prev

def main():
    Agent()


if __name__ == "__main__":
    main()
