from game_state import GameState
import asyncio
import random
import os
import fsm_utils
from pprint import pprint
import time
from numba import njit, typeof, typed, types
from copy import deepcopy
import numpy as np

uri = os.environ.get(
    'GAME_CONNECTION_STRING') or "ws://127.0.0.1:3000/?role=agent&agentId=agentId&name=defaultName"

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

    async def _on_game_tick(self, tick_number, game_state):
        game_state['tick'] = tick_number # force tick number to be correct
        game_state_boards = fsm_utils.generate_board(deepcopy(game_state))

        game_boards_stacked = np.stack([game_state_boards[v] for v in game_state_boards.keys()])

        new_entity_board = fsm_utils.forward(game_boards_stacked, 'up', 0)  
        pprint(new_entity_board)    



        # @njit
        # def do_loop(new_board):
        #     for i in range(1000000):
        #         new_board = fsm_utils.forward_entity_board(new_board, 'up', 0)

        # s = time.time()
        # do_loop(new_board)
        # print(time.time() - s)

        
    


    async def send_action(self, action, bomb_coords=None):
        '''
        send an action to the server
        '''
        if action in ['left', 'right', 'up', 'down']:
            await self._client.send_move(action)
        elif action == 'bomb':
            await self._client.send_bomb()
        elif action == 'detonate' and bomb_coords != None:
            await self._client.send_detonate(*bomb_coords)
        else:
            print(f"Unhandled action: {action}")


def main():
    Agent()


if __name__ == "__main__":
    main()
