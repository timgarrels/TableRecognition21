"""Creates a Graph from Label Regions"""
import graphviz
from functools import reduce

class SpreadSheetGraph(object):
    def __init__(self, nodes, edge_list):
        self.nodes = nodes
        self.edge_list = edge_list

        self.edge_toggle_list = [True for _ in range(len(self.edge_list))]

    def from_label_regions(lr_list):
        """Creates a graph from label regions
        Refer to `A Genetic-based Search for Adaptive TableRecognition in Spreadsheets.pdf`
        for the approach"""
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
                        edge_list.append({
                            "source": i,
                            "dest": j,
                            "overlap_type": "horizontal" if horizontal_overlap else "vertical"
                        })
        return SpreadSheetGraph(lr_list, edge_list)

    def visualize(self, format="png", engine="dot", out="out"):
        """Uses graphviz to visualize the current graph"""
        g = graphviz.Graph(format=format, engine=engine, strict=True)
        for i, node in enumerate(self.nodes):
            color = "blue" if node["type"] == "Header" else "green"
            g.node(str(i), color=color)

        all_true = reduce(lambda x,y: x and y, self.edge_toggle_list)
        all_false = reduce(lambda x,y: not x and not y, self.edge_toggle_list)

        for i, edge in enumerate(self.edge_list):
            enabled = self.edge_toggle_list[i]
            style = "solid" if edge["overlap_type"] == "horizontal" else "dashed"
            color = "green" if enabled else "red"
            if all_true or all_false:
                color = "black"
            g.edge(str(edge["source"]), str(edge["dest"]), style=style, color=color)
        g.render(out)
