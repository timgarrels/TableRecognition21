"""Creates a Graph from Label Regions"""
from typing import List
import graphviz
from typing import List
class SpreadSheetGraph(object):
    def __init__(self, nodes, edge_list, sheet):
        self.nodes = nodes
        self.edge_list = edge_list
        self.sheet = sheet

        self.edge_toggle_list = [True for _ in range(len(self.edge_list))]

    def from_label_regions_and_sheet(lr_list, sheet):
        """Creates a graph from label regions
        Refer to `A Genetic-based Search for Adaptive TableRecognition in Spreadsheets.pdf`
        for the approach"""
        existing_edges = []
        edge_list = []
        for i, source in enumerate(lr_list):
            for j, dest in enumerate(lr_list):
                if i != j:
                    # Two different label regions, find overlap
                    source_xs = range(source['top_left'][0], source['bottom_right'][0] + 1)
                    source_ys = range(source['top_left'][1], source['bottom_right'][1] + 1)
                    dest_xs = range(dest['top_left'][0], dest['bottom_right'][0] + 1)
                    dest_ys = range(dest['top_left'][1], dest['bottom_right'][1] + 1)

                    horizontal_overlap = True if len(set(source_xs).intersection(dest_xs)) > 0 else False
                    vertical_overlap = True if len(set(source_ys).intersection(dest_ys)) > 0 else False

                    if horizontal_overlap or vertical_overlap:
                        if (i, j) not in existing_edges and (j, i) not in existing_edges:
                            # Make sure edges exist only once, regardless on order of source and dest
                            existing_edges.extend([(i, j), (j, i)])
                            edge_list.append({
                                "source": i,
                                "dest": j,
                                "overlap_type": "horizontal" if horizontal_overlap else "vertical"
                            })

        return SpreadSheetGraph(lr_list, edge_list, sheet)

    def enabled_edges(self):
        """Returns all enabled edges"""
        return [edge for i, edge in enumerate(self.edge_list) if self.edge_toggle_list[i] is True]

    def disabled_edges(self):
        """Returns all disabled edges"""
        return [edge for i, edge in enumerate(self.edge_list) if self.edge_toggle_list[i] is False]

    def visualize(self, format="png", engine="dot", out="out"):
        """Uses graphviz to visualize the current graph"""
        g = graphviz.Graph(format=format, engine=engine, strict=True)

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

        return [list(l) for l in adj_list]

    def get_components(self) -> List[int]:
        """Returns graph components in regard of toggled edges"""
        components = []

        visited = []
        queue = []
        adj_list = self.build_adj_list(self.enabled_edges())
        for i, node in enumerate(self.nodes):
            if i in visited:
                # Node already marked and therefor already part of a component
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
