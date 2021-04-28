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

def position_on_board(board, position):
    '''Determines if a positions is on the board'''
    x, y = position
    return all([len(board) > x, len(board[0]) > y, x >= 0, y >= 0])


def get_direction(position, next_position):
    """Get the direction such that position --> next_position.

    We assume that they are adjacent.
    """
    x, y = position
    next_x, next_y = next_position
    if x == next_x:
        if y < next_y:
            return constants.Action.Right
        else:
            return constants.Action.Left
    elif y == next_y:
        if x < next_x:
            return constants.Action.Down
        else:
            return constants.Action.Up
    raise constants.InvalidAction("We did not receive a valid position transition.")


def get_next_position(position, direction):
    '''Returns the next position coordinates'''
    x, y = position
    if direction == constants.Action.Right:
        return (x, y + 1)
    elif direction == constants.Action.Left:
        return (x, y - 1)
    elif direction == constants.Action.Down:
        return (x + 1, y)
    elif direction == constants.Action.Up:
        return (x - 1, y)
    elif direction == constants.Action.Stop:
        return (x, y)
    raise constants.InvalidAction("We did not receive a valid direction.")