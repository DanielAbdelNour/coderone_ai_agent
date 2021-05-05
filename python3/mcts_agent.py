from forward_model import ForwardModel
from game_state import GameState
import asyncio
import copy
import os
import random
import time
from datetime import datetime
import numpy as np
from copy import deepcopy
import itertools
from pprint import pprint

fwd_model_uri = (
    os.environ.get("FWD_MODEL_CONNECTION_STRING") or "ws://127.0.0.1:6969/?role=admin"
)

uri = (
    os.environ.get("GAME_CONNECTION_STRING")
    or "ws://127.0.0.1:3000/?role=agent&agentId=agentId&name=defaultName"
)

actions = ["up", "down", "left", "right", "bomb", "detonate"]


def argmax_tiebreaking(Q):
    # find the best action with random tie-breaking
    idx = np.flatnonzero(Q == np.max(Q))
    assert len(idx) > 0, str(Q)
    return np.random.choice(idx)

def resolve_action(action, agent_number):
    move_actions = ['left', 'right', 'up', 'down']
    if action in move_actions:
        return {
            'action': {
                "move": action,
                "type": "move"
            },
            'agent_number': agent_number
        }
    else: 
        return {
            'action':{
                'type': action
            },
            'agent_number': agent_number
        }




class Agent:
    def __init__(self):
        self.async_next_state = None
        self._client_fwd = ForwardModel(fwd_model_uri)
        self._client = GameState(uri)

        self._client.set_game_tick_callback(self._on_game_tick)
        self._client_fwd.set_next_state_callback(self._on_next_game_state)
        self.connect()
    
    
    def connect(self):
        loop = asyncio.get_event_loop()

        client_connection = loop.run_until_complete(self._client.connect())
        client_fwd_connection = None

        client_fwd_connection = loop.run_until_complete(self._client_fwd.connect())

        loop = asyncio.get_event_loop()
        loop.create_task(self._client._handle_messages(client_connection))
        loop.create_task(self._client_fwd._handle_messages(client_fwd_connection))
        loop.run_forever()


    async def _on_game_tick(self, tick_number, game_state):   
        game_state['tick'] = tick_number    
       
        action_combinations = list(itertools.product(actions, actions))

        prev_state = deepcopy(game_state)

        print('-------------------------------------------------')
        pprint(prev_state)
        print('-------------------------------------------------')

        print('<><><><><><>')

        a = resolve_action('bomb', 0)
        b = resolve_action('left', 1)
        fwd_actions = [a, b]
        self.async_next_state = asyncio.get_event_loop().create_future()
        _, next_state = await asyncio.gather(self._client_fwd.send_next_state(0, prev_state, fwd_actions), self.async_next_state)
        print('-------------------------------------------------')
        pprint(next_state)
        print('-------------------------------------------------')
    

    async def _on_next_game_state(self, state):
        next_state = state["next_state"]
        pprint(next_state['entities'])
        self.async_next_state.set_result(next_state)
        

    def generate_random_action(self):
        actions_length = len(actions)
        return actions[random.randint(0, actions_length - 1)]


def main():
    Agent()


if __name__ == "__main__":
    main()
