"""Creates a Graph from Label Regions"""
import graphviz


class SpreadSheetGraph(object):
    def from_label_regions(lr_list):
        """Creates a graph from label regions
        Refer to `A Genetic-based Search for Adaptive TableRecognition in Spreadsheets.pdf`
        for the approach"""

        g = SpreadSheetGraph()
        g.nodes = lr_list

        adj_list = [[] for _ in range(len(g.nodes))]
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
                        adj_list[i].append({
                            "index": j,
                            "overlap_type": "horizontal" if horizontal_overlap else "vertical"
                        })
        g.adj_list = adj_list
        return g

    def visualize(self, format="png", engine="dot", out="out"):
        g = graphviz.Graph(format=format, engine=engine, strict=True)
        for i, node in enumerate(self.nodes):
            color = "blue" if node["type"] == "Header" else "green"
            g.node(str(i), color=color)

        for source in range(len(self.adj_list)):
            for dest in self.adj_list[source]:
                style = "solid" if dest["overlap_type"] == "horizontal" else "dashed"
                g.edge(str(source), str(dest["index"]), style=style)
        g.render(out)
