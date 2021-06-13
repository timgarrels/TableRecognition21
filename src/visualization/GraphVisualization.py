import graphviz

from graph.Edge import AlignmentType
from graph.SpreadSheetGraph import SpreadSheetGraph
from labelregions.LabelRegionType import LabelRegionType


def visualize_graph(graph: SpreadSheetGraph, output_format="png", engine="dot", out="out"):
    """Uses graphviz to visualize the current graph"""
    g = graphviz.Graph(format=output_format, engine=engine, strict=True)

    # Add nodes for each component
    components = graph.get_components()
    for i, component in enumerate(components):
        p = graphviz.Graph(f"cluster{i}")
        for label_region in component:
            color = "blue" if label_region.type == LabelRegionType.HEADER else "green"
            p.node(str(label_region.id), color=color)
        g.subgraph(p)

    # Add edges
    for edge in graph.enabled_edges():
        color = "green"
        style = "solid" if edge.alignment_type == AlignmentType.HORIZONTAL else "dashed"
        g.edge(str(edge.source.id), str(edge.destination.id), style=style, color=color)
    for edge in graph.disabled_edges():
        color = "red"
        style = "solid" if edge.alignment_type == AlignmentType.HORIZONTAL else "dashed"
        g.edge(str(edge.source.id), str(edge.destination.id), style=style, color=color)

    g.render(out, cleanup=True)
