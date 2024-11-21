def map_cluster_value(value):
    if value == 0.5:
        return "True"
    elif value == 1:
        return "False"
    elif value == 0:
        return "NaN"
    return value
