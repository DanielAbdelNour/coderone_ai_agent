import constants


def _position_is_item(board, position, item):
    '''Determins if a position holds an item'''
    return board[position] == item.value


def position_in_items(board, position, items):
    '''Dtermines if the current positions has an item'''
    return any([_position_is_item(board, position, item) for item in items])


def position_is_flames(board, position):
    '''Determins if a position has flames'''
    return _position_is_item(board, position, constants.Item.Blast)


def position_is_bomb(bombs, position):
    """Check if a given position is a bomb.
    
    We don't check the board because that is an unreliable source. An agent
    may be obscuring the bomb on the board.
    """
    for bomb in bombs:
        if position == bomb.position:
            return True
    return False


def position_is_powerup(board, position):
    '''Determins is a position has a powerup present'''
    powerups = [
        constants.Item.Ammo, constants.Item.Blast_Powerup
    ]
    item_values = [item.value for item in powerups]
    return board[position] in item_values


def position_is_wall(board, position):
    '''Determins if a position is a wall tile'''
    return position_is_rigid(board, position) or position_is_wood(board, position)


def position_is_passage(board, position):
    '''Determins if a position is passage tile'''
    return _position_is_item(board, position, constants.Item.Passage)


def position_is_rigid(board, position):
    '''Determins if a position has a rigid tile'''
    return _position_is_item(board, position, constants.Item.Metal_Block)


def position_is_wood(board, position):
    '''Determins if a position has a wood tile'''
    return _position_is_item(board, position, constants.Item.Wooden_Block)


def position_is_agent(board, position):
    '''Determins if a position has an agent present'''
    return board[position] in [constants.Item.Agent0.value, constants.Item.Agent1.value]


def position_is_enemy(board, position, enemies):
    '''Determins if a position is an enemy'''
    return constants.Item(board[position]) in enemies


def position_is_passable(board, position, enemies):
    '''Determins if a possible can be passed'''
    return all([
        any([
            position_is_agent(board, position),
            position_is_powerup(board, position),
            position_is_passage(board, position)
        ]), not position_is_enemy(board, position, enemies)
    ])