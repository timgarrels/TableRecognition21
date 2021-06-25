"""Creates a Graph from Label Regions"""
import logging
from typing import List, Dict, Set

from openpyxl.worksheet.worksheet import Worksheet

from dataset.SheetData import SheetData
from graph.Edge import Edge, AlignmentType
from labelregions.BoundingBox import BoundingBox
from labelregions.LabelRegion import LabelRegion

logger = logging.getLogger(__name__)


# logger.setLevel(logging.DEBUG)


class SpreadSheetGraph(object):
    def __init__(self, sheetdata: SheetData):
        self.sheet_data = sheetdata
        self.nodes: List[LabelRegion] = sheetdata.label_regions
        self.node_id_lookup: Dict[int, LabelRegion] = dict([(node.id, node) for node in self.nodes])
        self.edge_list: List[Edge] = self.get_generate_edge_list()
        self.sheet: Worksheet = sheetdata.worksheet

        self.edge_toggle_list: List[bool] = self.edge_toggle_list_from_table_definition(sheetdata.table_definitions)

        self.node_edges_lookup: Dict[LabelRegion, Set[Edge]] = {}
        for node in self.nodes:
            # Dont use `.fromkeys(self.nodes, set())` here, as the set is then created only once and the same reference
            # in all keys:
            # d = {}.fromkeys([1,2], set()
            # d[0].add(1)
            # d
            # > {0: {1}, 1: {1}}
            self.node_edges_lookup[node] = set()

        for edge in self.edge_list:
            self.node_edges_lookup[edge.source].add(edge)
            self.node_edges_lookup[edge.destination].add(edge)

    def enable_all_edges(self):
        self.edge_toggle_list = [True for _ in range(len(self.edge_toggle_list))]

    def get_neighbours(self, node) -> List[LabelRegion]:
        edges = self.node_edges_lookup[node]

        def get_partner_from_edge(edge: Edge):
            return edge.source if edge.source != node else edge.destination

        nodes = set([get_partner_from_edge(edge) for edge in edges])
        return list(nodes)

    def get_generate_edge_list(self):
        """Creates a graph from label regions
        Refer to `A Genetic-based Search for Adaptive TableRecognition in Spreadsheets.pdf`
        for the approach"""
        # WARNING: Based on the assumption, that each row index / col index can match only once
        # That means that three regions H1, D1, H2 that span the exact same cols and are directly on top of each other
        # That H1 is not connected to H2, because the edge H1-D1 already uses all col indices
        logger.debug("Creating Spreadsheet Graph...")
        existing_edges = []
        edge_list = []

        # Vertical Overlap
        sorted_by_y = sorted(self.nodes, key=lambda node: node.top)
        for i, source in enumerate(sorted_by_y):
            source_xs = set(source.get_all_x())
            for j, destination in enumerate(sorted_by_y):
                destination_bottom_of_source = i < j
                if destination_bottom_of_source:
                    # Two different label regions, dest right of source
                    destination_xs = set(destination.get_all_x())

                    intersection = source_xs.intersection(destination_xs)
                    vertical_overlap = True if len(intersection) > 0 else False
                    if vertical_overlap:
                        # Eat up indices
                        source_xs = source_xs - destination_xs
                        # Make sure edges exist only once, regardless on order of source and dest
                        if ((source.id, destination.id) not in existing_edges and
                                (destination.id, source.id) not in existing_edges):
                            existing_edges.extend([(source.id, destination.id), (destination.id, source.id)])
                            edge_list.append(Edge(source, destination, list(intersection), AlignmentType.VERTICAL))

        # Horizontal Overlap
        sorted_by_x = sorted(self.nodes, key=lambda node: node.left)
        for i, source in enumerate(sorted_by_x):
            source_ys = set(source.get_all_y())
            for j, destination in enumerate(sorted_by_x):
                destination_right_of_source = i < j
                if destination_right_of_source:
                    # Two different label regions, dest bottom of source
                    destination_ys = set(destination.get_all_y())

                    intersection = source_ys.intersection(destination_ys)
                    horizontal_overlap = True if len(intersection) > 0 else False
                    source_ys = source_ys - destination_ys
                    if horizontal_overlap:
                        # Make sure edges exist only once, regardless on order of source and dest
                        if ((source.id, destination.id) not in existing_edges and
                                (destination.id, source.id) not in existing_edges):
                            existing_edges.extend([(source.id, destination.id), (destination.id, source.id)])
                            edge_list.append(Edge(source, destination, list(intersection), AlignmentType.HORIZONTAL))

        return edge_list

    def edge_toggle_list_from_table_definition(self, tds: List[BoundingBox]):
        """Matches the edge toggle list to the table definitions
        Assumption: There can be multiple valid graph representations of the same table definition
        In a three node component (a table definition with three label regions) there can be either 2 or 3 edges
        and the 2 edges can be at any place. It still is a valid component.
        We create a graph representation, where each component only contains enabled edges."""

        # Group Label Regions into should-be-components
        # label_region -> component_id
        components = {}
        for i, td in enumerate(tds):
            for lr in self.nodes:
                if lr.intersect(td):
                    components[lr] = i

        edge_toggle_list: List[bool] = [True for _ in range(len(self.edge_list))]
        # Find and disable all edges that connect components
        for edge_index, edge in enumerate(self.edge_list):
            if components[edge.source] != components[edge.destination]:
                # Edge nodes are in different components, edge should be disabled
                edge_toggle_list[edge_index] = False
        return edge_toggle_list

    def enabled_edges(self):
        """Returns all enabled edges"""
        return [edge for i, edge in enumerate(self.edge_list) if self.edge_toggle_list[i] is True]

    def disabled_edges(self):
        """Returns all disabled edges"""
        return [edge for i, edge in enumerate(self.edge_list) if self.edge_toggle_list[i] is False]

    def build_adj_list(self, edges: List[Edge]) -> Dict[LabelRegion, Set[LabelRegion]]:
        """Creates a adj list from the edge list and the edge toggle list"""
        adj_list = {}
        # Dont use `.fromkeys(self.nodes, set())` here, as the set is then created only once and the same reference
        # in all keys:
        # d = {}.fromkeys([1,2], set()
        # d[0].add(1)
        # d
        # > {0: {1}, 1: {1}}
        for node in self.nodes:
            adj_list[node] = set()

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
                connected_node = queue.pop()
                if connected_node.id in visited:
                    continue
                visited.append(connected_node.id)
                component.append(connected_node)
                queue = queue.union(adj_list[connected_node])
            components.append(component)

        return components

    def get_table_definitions(self):
        return [BoundingBox.merge(component) for component in self.get_components()]
