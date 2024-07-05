import math

def p_dist(point1, point2):
    if len(point1) != len(point2):
        raise ValueError("Points must have the same dimension")

    squared_diffs = [(x - y) ** 2 for x, y in zip(point1, point2)]
    return math.sqrt(sum(squared_diffs))

def v_mod(vector):
    return math.sqrt(sum([(x) ** 2 for x in vector]))

def v_abs(vector):
    return tuple(abs(x) for x in vector)

def v_norm(vector):
    norm = math.sqrt(sum(x**2 for x in vector))
    return tuple(x / norm for x in vector)

def v_add(vector1, vector2):
    return tuple(v1 + v2 for v1, v2 in zip(vector1, vector2))

def v_sub(vector1, vector2):
    return tuple(v1 - v2 for v1, v2 in zip(vector1, vector2))

def v_mul(vector, scalar):
    return tuple(v * scalar for v in vector)

def v_dot_p(vector1, vector2):
    return tuple(v1 * v2 for v1, v2 in zip(vector1, vector2))

def v_cross(vector1, vector2):
    if len(vector1) != 3 or len(vector2) != 3:
        raise ValueError("Cross product is defined only for 3-dimensional vectors.")

    x = vector1[1] * vector2[2] - vector1[2] * vector2[1]
    y = vector1[2] * vector2[0] - vector1[0] * vector2[2]
    z = vector1[0] * vector2[1] - vector1[1] * vector2[0]

    return (x, y, z)
