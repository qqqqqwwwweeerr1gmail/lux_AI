


def get_opposite_direction(direction,team):
    mapp = {'w':'e', 'n':'s', 'c':'c', 'e':'w', 's':'n'}
    if team%2==1:
        return mapp[direction]
    else:
        return direction


def get_opposite_ew(direction,team):
    mapp = {'w':'e', 'n':'n', 'c':'c', 'e':'w', 's':'s'}
    if team%2==1:
        return mapp[direction]
    else:
        return direction

def get_opposite_ns(direction,team):
    mapp = {'e':'e', 'n':'s', 'c':'c', 'w':'w', 's':'n'}
    if team%2==1:
        return mapp[direction]
    else:
        return direction

def get_opposite_di(direction,team,di):
    if di == 'ew':
        return get_opposite_ew(direction,team)
    if di == 'ns':
        return get_opposite_ns(direction,team)

def get_di(u1_pos,u2_pos,team):
    if u1_pos.x == u2_pos.x:
        return 'ns'
    else:
        return 'ew'













