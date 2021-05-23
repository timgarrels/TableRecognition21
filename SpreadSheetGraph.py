"""Creates a Graph from Label Regions"""
import logging
from typing import List

import graphviz

logger = logging.getLogger(__name__)


class SpreadSheetGraph(object):
    def __init__(self, nodes, edge_list, sheet):
        self.nodes = nodes
        self.edge_list = edge_list
        self.sheet = sheet

        self.edge_toggle_list = [True for _ in range(len(self.edge_list))]

    @staticmethod
    def from_label_regions_and_sheet(lr_list, sheet):
        """Creates a graph from label regions
        Refer to `A Genetic-based Search for Adaptive TableRecognition in Spreadsheets.pdf`
        for the approach"""
        # WARNING: Based on the assumption, that each row index / col index can match only once
        # That means that three regions H1, D1, H2 that span the exact same cols and are directly on top of each other
        # That H1 is not connected to H2, because the edge H1-D1 already uses all col indices
        logger.info("Creating Spreadsheet Graph...")
        existing_edges = []
        edge_list = []

        for i, lr in enumerate(lr_list):
            lr["id"] = i

        # Vertical Overlap
        sorted_by_y = sorted(lr_list, key=lambda node: node['top_left'][1])
        for i, source in enumerate(sorted_by_y):
            source_xs = set(range(source['top_left'][0], source['bottom_right'][0] + 1))
            for j, dest in enumerate(sorted_by_y):
                dest_right_of_source = i < j
                if dest_right_of_source:
                    # Two different label regions, dest right of source
                    dest_xs = set(range(dest['top_left'][0], dest['bottom_right'][0] + 1))

                    intersection = source_xs.intersection(dest_xs)
                    horizontal_overlap = True if len(intersection) > 0 else False
                    source_xs = source_xs - dest_xs
                    if horizontal_overlap:
                        # Make sure edges exist only once, regardless on order of source and dest
                        s_id = source["id"]
                        d_id = dest["id"]
                        if (s_id, d_id) not in existing_edges and (d_id, s_id) not in existing_edges:
                            existing_edges.extend([(s_id, d_id), (d_id, s_id)])

                            connection_type = "-".join(sorted([source["type"][0], dest["type"][0]]))
                            edge_list.append({
                                "source": s_id,
                                "dest": d_id,
                                "connection_type": connection_type,
                                "aligned_indices": intersection,
                                "overlap_type": "vertical"
                            })

        # Horizontal Overlap
        sorted_by_x = sorted(lr_list, key=lambda node: node['top_left'][0])
        for i, source in enumerate(sorted_by_x):
            source_ys = set(range(source['top_left'][1], source['bottom_right'][1] + 1))
            for j, dest in enumerate(sorted_by_x):
                dest_bottom_of_source = i < j
                if dest_bottom_of_source:
                    # Two different label regions, dest bottom of source
                    dest_ys = set(range(dest['top_left'][1], dest['bottom_right'][1] + 1))

                    intersection = source_ys.intersection(dest_ys)
                    vertical_overlap = True if len(intersection) > 0 else False
                    source_ys = source_ys - dest_ys
                    if vertical_overlap:
                        # Make sure edges exist only once, regardless on order of source and dest
                        s_id = source["id"]
                        d_id = dest["id"]
                        if (s_id, d_id) not in existing_edges and (d_id, s_id) not in existing_edges:
                            existing_edges.extend([(s_id, d_id), (d_id, s_id)])

                            connection_type = "-".join(sorted([source["type"][0], dest["type"][0]]))
                            edge_list.append({
                                "source": s_id,
                                "dest": d_id,
                                "connection_type": connection_type,
                                "aligned_indices": intersection,
                                "overlap_type": "vertical"
                            })

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
            for node_index in component:
                color = "blue" if self.nodes[node_index]["type"] == "Header" else "green"
                p.node(str(node_index), color=color)
            g.subgraph(p)

        # Add edges
        for edge in self.enabled_edges():
            color = "green"
            style = "solid" if edge["overlap_type"] == "horizontal" else "dashed"
            g.edge(str(edge["source"]), str(edge["dest"]), style=style, color=color)
        for edge in self.disabled_edges():
            color = "red"
            style = "solid" if edge["overlap_type"] == "horizontal" else "dashed"
            g.edge(str(edge["source"]), str(edge["dest"]), style=style, color=color)

        g.render(out)

    def build_adj_list(self, edges):
        """Creates a adj list from the edge list and the edge toggle list"""
        adj_list = [set() for _ in range(len(self.nodes))]
        for edge in edges:
            source = edge["source"]
            dest = edge["dest"]
            adj_list[source].add(dest)
            adj_list[dest].add(source)

        return [list(node_connections) for node_connections in adj_list]

    def get_components(self) -> List[List[int]]:
        """Returns graph components in regard of toggled edges"""
        components = []

        visited = []
        adj_list = self.build_adj_list(self.enabled_edges())
        for i, node in enumerate(self.nodes):
            if i in visited:
                # Node already marked and therefore already part of a component
                continue
            visited.append(i)
            component = [i]
            queue = adj_list[i]
            while queue:
                node = queue.pop()
                if node in visited:
                    continue
                visited.append(node)
                component.append(node)
                queue.extend(adj_list[node])
            components.append(component)

        return components
