from enum import Enum

ent_type_dict = {
    'p':0,
    'a': 1,
    'b': 2,
    'x': 3,
    'bp': 4,
    'm':5,
    'o':5,
    'w':6, 
}

class Item(Enum):
    Passage = 0
    Ammo = 1
    Bomb = 2
    Blast = 3
    Blast_Powerup = 4
    Metal_Block = 5
    Ore_Block = 6
    Wooden_Block = 7
    Agent0 = 10
    Agent1 = 11