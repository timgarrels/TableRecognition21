"""Creates a Graph from Label Regions"""
import logging
from typing import List, Dict, Set

import graphviz
from openpyxl.worksheet.worksheet import Worksheet

from Edge import Edge, AlignmentType
from LabelRegion import LabelRegion
from LabelRegionType import LabelRegionType

logger = logging.getLogger(__name__)


class SpreadSheetGraph(object):
    def __init__(self, nodes: List[LabelRegion], edge_list: List[Edge], sheet: Worksheet):
        self.nodes: List[LabelRegion] = nodes
        self.node_id_lookup: Dict[int, LabelRegion] = dict([(node.id, node) for node in self.nodes])
        self.edge_list: List[Edge] = edge_list
        self.sheet: Worksheet = sheet

        self.edge_toggle_list: List[bool] = [True for _ in range(len(self.edge_list))]

        self.node_edges_lookup: Dict[LabelRegion, Set[Edge]] = {}.fromkeys(self.nodes, set())
        for edge in self.edge_list:
            self.node_edges_lookup[edge.source].add(edge)
            self.node_edges_lookup[edge.destination].add(edge)

    def get_neighbours(self, node) -> List[LabelRegion]:
        edges = self.node_edges_lookup[node]

        def get_partner_from_edge(edge: Edge):
            return edge.source if edge.source != node else edge.destination

        nodes = [get_partner_from_edge(edge) for edge in edges]
        return nodes

    @staticmethod
    def from_label_regions_and_sheet(lr_list: List[LabelRegion], sheet: Worksheet):
        """Creates a graph from label regions
        Refer to `A Genetic-based Search for Adaptive TableRecognition in Spreadsheets.pdf`
        for the approach"""
        # WARNING: Based on the assumption, that each row index / col index can match only once
        # That means that three regions H1, D1, H2 that span the exact same cols and are directly on top of each other
        # That H1 is not connected to H2, because the edge H1-D1 already uses all col indices
        logger.info("Creating Spreadsheet Graph...")
        existing_edges = []
        edge_list = []

        # Vertical Overlap
        sorted_by_y = sorted(lr_list, key=lambda node: node.left)
        for i, source in enumerate(sorted_by_y):
            source_xs = set(source.get_all_x())
            for j, destination in enumerate(sorted_by_y):
                destination_right_of_source = i < j
                if destination_right_of_source:
                    # Two different label regions, dest right of source
                    destination_xs = set(destination.get_all_x())

                    intersection = source_xs.intersection(destination_xs)
                    horizontal_overlap = True if len(intersection) > 0 else False
                    source_xs = source_xs - destination_xs
                    if horizontal_overlap:
                        # Make sure edges exist only once, regardless on order of source and dest
                        if ((source.id, destination.id) not in existing_edges and
                                (destination.id, source.id) not in existing_edges):
                            existing_edges.extend([(source.id, destination.id), (destination.id, source.id)])
                            edge_list.append(Edge(source, destination, list(intersection), AlignmentType.VERTICAL))

        # Horizontal Overlap
        sorted_by_x = sorted(lr_list, key=lambda node: node.top)
        for i, source in enumerate(sorted_by_x):
            source_ys = set(source.get_all_y())
            for j, destination in enumerate(sorted_by_x):
                destination_bottom_of_source = i < j
                if destination_bottom_of_source:
                    # Two different label regions, dest bottom of source
                    destination_ys = set(destination.get_all_y())

                    intersection = source_ys.intersection(destination_ys)
                    vertical_overlap = True if len(intersection) > 0 else False
                    source_ys = source_ys - destination_ys
                    if vertical_overlap:
                        # Make sure edges exist only once, regardless on order of source and dest
                        if ((source.id, destination.id) not in existing_edges and
                                (destination.id, source.id) not in existing_edges):
                            existing_edges.extend([(source.id, destination.id), (destination.id, source.id)])
                            edge_list.append(Edge(source, destination, list(intersection), AlignmentType.HORIZONTAL))

        return SpreadSheetGraph(lr_list, edge_list, sheet)

    def enabled_edges(self):
        """Returns all enabled edges"""
        return [edge for i, edge in enumerate(self.edge_list) if self.edge_toggle_list[i] is True]

    def disabled_edges(self):
        """Returns all disabled edges"""
        return [edge for i, edge in enumerate(self.edge_list) if self.edge_toggle_list[i] is False]

    def visualize(self, output_format="png", engine="dot", out="out"):
        """Uses graphviz to visualize the current graph"""
        g = graphviz.Graph(format=output_format, engine=engine, strict=True)

        # Add nodes for each component
        components = self.get_components()
        for i, component in enumerate(components):
            p = graphviz.Graph(f"cluster{i}")
            for label_region in component:
                color = "blue" if label_region.type == LabelRegionType.HEADER else "green"
                p.node(str(label_region.id), color=color)
            g.subgraph(p)

        # Add edges
        for edge in self.enabled_edges():
            color = "green"
            style = "solid" if edge.alignment_type == AlignmentType.HORIZONTAL else "dashed"
            g.edge(str(edge.source.id), str(edge.destination.id), style=style, color=color)
        for edge in self.disabled_edges():
            color = "red"
            style = "solid" if edge.alignment_type == AlignmentType.HORIZONTAL else "dashed"
            g.edge(str(edge.source.id), str(edge.destination.id), style=style, color=color)

        g.render(out)

    def build_adj_list(self, edges: List[Edge]) -> Dict[LabelRegion, Set[LabelRegion]]:
        """Creates a adj list from the edge list and the edge toggle list"""
        adj_list = {}.fromkeys(self.nodes, set())
        for edge in edges:
            adj_list[edge.source].add(edge.destination)
            adj_list[edge.destination].add(edge.source)

        return adj_list

    def get_components(self) -> List[List[LabelRegion]]:
        """Returns graph components in regard of toggled edges"""
        components: List[List[LabelRegion]] = []

        visited: List[int] = []
        adj_list = self.build_adj_list(self.enabled_edges())
        for node in self.nodes:
            if node.id in visited:
                # Node already marked and therefore already part of a component
                continue
            visited.append(node.id)
            component = [node]
            queue = adj_list[node]
            while queue:
                node = queue.pop()
                if node.id in visited:
                    continue
                visited.append(node.id)
                component.append(node)
                queue.union(adj_list[node])
            components.append(component)

        return components
