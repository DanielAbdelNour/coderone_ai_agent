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
    agent_power_board = np.zeros_like(entity_board)
    agent_ammo_board = np.zeros_like(entity_board)
    agent_board = np.zeros_like(entity_board)
    bomb_owner_board = np.zeros_like(entity_board)

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
            bomb_owner_board[(len(entity_board)-1) - ent_y, ent_x] = 10 if ent['owner'] == 0 else 11

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

    #entity_board[(len(entity_board)-1) - agentA_y, agentA_x] = 10
    #entity_board[(len(entity_board)-1) - agentB_y, agentB_x] = 11

    agent_board[(len(entity_board)-1) - agentA_y, agentA_x] = 10
    agent_board[(len(entity_board)-1) - agentB_y, agentB_x] = 11

    agent_hp_board[(len(entity_board)-1) - agentA_y, agentA_x] = agents['0']['hp']
    agent_hp_board[(len(entity_board)-1) - agentB_y, agentB_x] = agents['1']['hp']

    agent_power_board[(len(entity_board)-1) - agentA_y, agentA_x] = agents['0']['blast_diameter']
    agent_power_board[(len(entity_board)-1) - agentB_y, agentB_x] = agents['1']['blast_diameter']

    agent_ammo_board[(len(entity_board)-1) - agentA_y, agentA_x] = agents['0']['inventory']['bombs']
    agent_ammo_board[(len(entity_board)-1) - agentB_y, agentB_x] = agents['1']['inventory']['bombs']

    return {
        'entity_board': entity_board.astype(np.int32), #0
        'hp_board': hp_board.astype(np.int32), #1
        'bomb_dia_board': bomb_dia_board.astype(np.int32), #2
        'bomb_exp_board': bomb_exp_board.astype(np.int32), #3
        'fire_board': fire_board.astype(np.int32), #4
        'agent_hp_board': agent_hp_board.astype(np.int32), #5
        'agent_power_board': agent_power_board.astype(np.int32), #6
        'agent_ammo_board': agent_ammo_board.astype(np.int32), #7
        'agent_board': agent_board.astype(np.int32), #8,
        'bomb_owner_board': bomb_owner_board.astype(np.int32) #9,
    }


#@njit
def forward(game_state_boards, actions):
    '''
    forward step all state boards actions[0] for agentA actions[1] for agentB
    '''

    # start with all boards
    entity_board = game_state_boards[0].copy()
    hp_board = game_state_boards[1].copy()
    bomb_dia_board = game_state_boards[2].copy()
    bomb_exp_board = game_state_boards[3].copy()
    fire_board = game_state_boards[4].copy()
    agent_hp_board = game_state_boards[5].copy()
    agent_power_board = game_state_boards[6].copy()
    agent_ammo_board = game_state_boards[7].copy()
    agent_board = game_state_boards[8].copy()
    bomb_owner_board = game_state_boards[9].copy()

    board_shape = entity_board.shape

    # apply actions
    for agent_ent, action in [[10, actions[0]], [11, actions[1]]]:
        cy,cx = np.argwhere(agent_board==agent_ent)[0] # current x, y of target agent
        if action in ['left', 'right', 'up', 'down']: #move_actions:
            if action == 'left':
                move_dir = (0,-1)
            elif action == 'right':
                move_dir = (0,1)
            elif action == 'up':
                move_dir = (-1,0)
            else:
                move_dir = (1,0)

            ny, nx = cy+move_dir[0], cx+move_dir[1]  # proposed new positions of target agent

            # apply move if target location is legal in bounds and not over another agent
            if (ny > board_shape[0]-1 or nx > board_shape[1]-1 or ny < 0 or nx < 0) == False and agent_board[ny, nx] == 0:
                ent_at_position = entity_board[ny, nx]
                # position is empty or has a powerup - can move - modify entity board to reflect new position
                if ent_at_position in [0, 4, 1]:
                    agent_board[ny, nx] = agent_ent
                    agent_board[cy, cx] = 0

                    # move ammo and power and hp indicators with agent (cut and paste prev pos to new pos)
                    agent_ammo_board[ny, nx] = agent_ammo_board[cy, cx]
                    agent_ammo_board[cy, cx] = 0

                    agent_power_board[ny, nx] = agent_power_board[cy, cx]
                    agent_power_board[cy, cx] = 0

                    agent_hp_board[ny, nx] = agent_hp_board[cy, cx]
                    agent_hp_board[cy, cx] = 0

                    # handle power powerup (blast diameter)
                    if ent_at_position == 4:
                        agent_power_board[ny, nx] = agent_power_board[ny, nx] + 1 # set new position to new power
                    # handle ammo powerup
                    elif ent_at_position == 1:
                        agent_ammo_board[ny, nx] = agent_ammo_board[ny, nx] + 1

        # place bombs if agent has enough ammo and not standing an another bomb
        if action == 'bomb' and agent_ammo_board[cy, cx] > 0 and entity_board[cx, cy] != 2:
            entity_board[cy, cx] = 2 # add bomb to position
            bomb_exp_board[cy, cx] = 40
            agent_ammo_board[cy, cx] -= 1
            bomb_dia_board[cy, cx] = agent_power_board[cy, cx]
            bomb_owner_board[cy, cx] = agent_ent
        
        if action == 'detonate':
            # find all bombs belonging to agent
            to_detonate = np.argwhere(bomb_owner_board == agent_ent)
            for td in to_detonate:
                tdy, tdx = td
                bomb_exp_board[tdy, tdx] = 0+1 # will tick to zero in next step so make 1 not 0


    # TODO convert to funtion to enable bomb chaining
    
    # tick bombs
    bomb_exp_board[bomb_exp_board >= 0] -= 1
    # tick fire
    fire_board[fire_board >= 0] -= 1

    # find exploded bombs
    exploded_bombs = np.argwhere(bomb_exp_board == 0)

    # add fire to expired bombs
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

                # damage agents
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
                
                # explode other bombs
                if entity_board[yy, xx] == 2:
                    bomb_exp_board[yy, xx] = 1
                    exploded_bombs = np.argwhere(bomb_exp_board == 0)
                    break
                    
        # remove exploded bomb entity
        if entity_board[xby, xbx] == 2:
            entity_board[xby, xbx] = 0  
        bomb_dia_board[xby, xbx] = 0
        bomb_owner_board[xby, xbx] = 0

    # damage agents standing in fire
    active_fire = np.argwhere(fire_board > 0)
    for af in active_fire:
        afy, afx = af
        if agent_board[afy, afx] > 0:
            agent_hp_board[afy, afx] -= 1


    return np.stack([entity_board, hp_board, bomb_dia_board,  bomb_exp_board, fire_board, agent_hp_board, agent_power_board, agent_ammo_board, agent_board, bomb_owner_board])

