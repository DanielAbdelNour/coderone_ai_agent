from os import sched_yield
import numpy as np
from copy import deepcopy
from numba import njit, typeof, typed, types

ent_type_dict = {
    'p':0,
    'a': 1,
    'b': 2,
    'x': 3,
    'bp': 4,
    'm':5,
    'o':6,
    'w':7, 
}

agent_number_ent_dict = {
    0:10,
    1:11
}

agent_id_ent_dict = {
    'A':10,
    'B':11
}

move_dir_dict = {
    'left': (0,-1),
    'right': (0, 1),
    'up': (-1,0),
    'down': (1,0)
}


move_actions = ['left', 'right', 'up', 'down']
other_actions = ['bomb', 'detonate']

def generate_board(game_state):
    '''
    convert a returned game_state to a lsit of 2D arrays
    '''
    entity_board = np.zeros((game_state['world']['height'], game_state['world']['width']))
    bomb_exp_board = np.zeros_like(entity_board) -1
    bomb_dia_board = np.zeros_like(entity_board)
    fire_board = np.zeros_like(entity_board) -1
    hp_board = np.zeros_like(entity_board)
    agent_hp_board = np.zeros_like(entity_board)

    tick = game_state['tick']

    # populate entity board
    for ent in game_state['entities']:
        ent_type = ent['type']
        ent_x = ent['x']
        ent_y = ent['y']

        entity_board[(len(entity_board)-1) - ent_y, ent_x] = ent_type_dict[ent_type]

        # add bombs to bomb map
        if ent_type == 'b':
            bomb_dia_board[(len(entity_board)-1) - ent_y, ent_x] = ent['blast_diameter']
            bomb_exp_board[(len(entity_board)-1) - ent_y, ent_x] = ent['expires'] - tick

        # add fire to map
        if ent_type == 'x':
            fire_board[(len(entity_board)-1) - ent_y, ent_x] = ent['expires'] - tick

        # add hp to map
        if ent.get('hp') != None:
            hp_board[(len(entity_board)-1) - ent_y, ent_x] = ent['hp']

    # place agents on the board
    agents = game_state['agent_state']
    agentA_x, agentA_y = agents['0']['coordinates']
    agentB_x, agentB_y = agents['1']['coordinates']

    entity_board[(len(entity_board)-1) - agentA_y, agentA_x] = 10
    entity_board[(len(entity_board)-1) - agentB_y, agentB_x] = 11

    agent_hp_board[(len(entity_board)-1) - agentA_y, agentA_x] = agents['0']['hp']
    agent_hp_board[(len(entity_board)-1) - agentB_y, agentB_x] = agents['1']['hp']

    return {
        'entity_board': entity_board.astype(np.int32),
        'hp_board': hp_board.astype(np.int32),
        'bomb_dia_board': bomb_dia_board.astype(np.int32),
        'bomb_exp_board': bomb_exp_board.astype(np.int32),
        'fire_board': fire_board.astype(np.int32),
        'agent_hp_board': agent_hp_board.astype(np.int32)
    }


#@njit
def forward(game_state_boards, action, agent_number):
    '''
    forward step all state boards
    '''

    # start with the entity board
    entity_board = game_state_boards[0].copy()
    hp_board = game_state_boards[1].copy()
    bomb_dia_board = game_state_boards[2].copy()
    bomb_exp_board = game_state_boards[3].copy()
    fire_board = game_state_boards[4].copy()
    agent_hp_board = game_state_boards[5].copy()

    agent_ent = 10 if agent_number == 0 else 11 #agent_number_ent_dict[agent_number]

    board_shape = entity_board.shape

    # apply forward for a movement
    if action in ['left', 'right', 'up', 'down']: #move_actions:
        cy,cx = np.argwhere(entity_board==agent_ent)[0] # current x, y of target agent

        if action == 'left':
            move_dir = (0,-1)
        elif action == 'right':
            move_dir = (0,1)
        elif action == 'up':
            move_dir = (-1,0)
        else:
            move_dir = (1,0)

        ny, nx = cy+move_dir[0], cx+move_dir[1]  # proposed new positions of target agent

        # illegal move out of bounds
        if ny > board_shape[0]-1 or nx > board_shape[1]-1 or ny < 0 or nx < 0:
            return entity_board

        ent_at_position = entity_board[ny, nx]
        # position is empty - can move - modify entity board to reflect new position
        if ent_at_position == 0:
            entity_board[ny, nx] = agent_ent
            entity_board[cy, cx] = 0

    # tick bombs
    bomb_exp_board[bomb_exp_board > 0] -= 1
    exploded_bombs = np.argwhere(bomb_exp_board == 0)

    # add fire
    for xb in exploded_bombs:
        xby, xbx = xb
        dia = bomb_dia_board[xby, xbx]
        dia_per_side = dia-2

        # place fire `dia_per_side` times each side from the center of the xplosion
        # auto place fire if entity at fire location is wood(7)
        # decrement health all other locations
        fire_board[xby, xbx] = 10


        for zz in [[-1, 0], [1, 0], [0, -1], [0, 1]]:
            for i in range(dia_per_side):
                step = i+1
                yy = xby+step*zz[0]
                xx = xbx+step*zz[1]

                # stop propagating when out of bounds
                if (yy < 0 or xx < 0)  or (yy > board_shape[0]-1 or xx > board_shape[1]-1):
                    break

                # stop propagating if encoutered a metal block
                if entity_board[yy, xx] == 5:
                    break
                
                # continue if there is empty space
                if entity_board[yy, xx] == 0:
                    fire_board[yy, xx] = 10

                if agent_hp_board[yy, xx] > 0:
                    agent_hp_board[yy, xx] -= 1
                    fire_board[yy, xx] = 10
                    break

                # stop if we hit something with hp and decrement hp
                if hp_board[yy, xx] > 0:
                    hp_board[yy, xx] -= 1
                    if hp_board[yy, xx] == 0 and entity_board[yy, xx] in [7,6]:
                        fire_board[yy, xx] = 10
                        entity_board[yy, xx] = 0
                        break
                    else:
                        break
          
    return entity_board

