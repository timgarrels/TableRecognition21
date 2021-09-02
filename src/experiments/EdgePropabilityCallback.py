from graph.Edge import Edge, ConnectionType


def default_edge_mutation_probability_callback(edge: Edge) -> int:
    return 1


def short_edges_different_types(edge: Edge) -> int:
    value = 1
    if edge.connection_type == ConnectionType.D_H:
        value += 1
    if edge.length <= 1:
        value += 1
    return value


def extreme_short_edges_different_types(edge: Edge) -> int:
    value = 1
    if edge.connection_type == ConnectionType.D_H:
        value += 20
    if edge.length <= 1:
        value += 20
    return value
