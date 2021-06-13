import json
from os import listdir
from os.path import isfile, join

import matplotlib.pyplot as plt
import numpy as np


class Summarizer(object):
    def __init__(self, experiment_path: str):
        self._experiment_path = experiment_path

    def load_results(self):
        results = {}
        files = [f for f in listdir(self._experiment_path) if isfile(join(self._experiment_path, f))]
        for file in files:
            path = join(self._experiment_path, file)
            xml_file = file.replace("_result.json", "")
            with open(path, "r") as result:
                result_dict = json.load(result)

            table_count = len(result_dict["ground_truth"])

            results[xml_file] = {"result_dict": result_dict, "table_count": table_count}
        return results

    def split_results(self):
        results = self.load_results()

        multi_table = []
        single_table = []
        all = []
        for xml_file, result in results.items():

            precision_recall = {
                "area_precision": result["result_dict"]["evaluation"]["area_precision"],
                "area_recall": result["result_dict"]["evaluation"]["area_recall"],
            }
            all.append(precision_recall)
            if result["table_count"] > 1:
                multi_table.append(precision_recall)
            else:
                single_table.append(precision_recall)

        return {"all": all, "single": single_table, "multi": multi_table}

    def summarize(self):
        results = self.split_results()
        precision = [
            [d["area_precision"] for d in results["all"]],
            [d["area_precision"] for d in results["single"]],
            [d["area_precision"] for d in results["multi"]],
        ]
        recall = [
            [d["area_recall"] for d in results["all"]],
            [d["area_recall"] for d in results["single"]],
            [d["area_recall"] for d in results["multi"]],
        ]
        f1 = [
            [(2 * p * r) / (p + r) for p, r in list(zip(precision[0], recall[0]))],
            [(2 * p * r) / (p + r) for p, r in list(zip(precision[1], recall[1]))],
            [(2 * p * r) / (p + r) for p, r in list(zip(precision[2], recall[2]))],
        ]

        for i, label in enumerate(["all", "single", "multi"]):
            if len(results[label]) == 0:
                continue
            print(f"{label} ({len(precision[i])})")
            print("\tPrecision")
            print(
                f"\t\tMin: {min(precision[i])}\n\t\tMax: {max(precision[i])}\n\t\tMean: {sum(precision[i]) / len(precision[i])}")
            print("\tRecall")
            print(f"\t\tMin: {min(recall[i])}\n\t\tMax: {max(recall[i])}\n\t\tMean: {sum(recall[i]) / len(recall[i])}")
            print("\tF1")
            print(f"\t\tMin: {min(f1[i])}\n\t\tMax: {max(f1[i])}\n\t\tMean: {sum(f1[i]) / len(f1[i])}")

    def plot(self):
        results = self.split_results()

        fig1, (ax1, ax2, ax3) = plt.subplots(1, 3)
        plt.setp((ax1, ax2, ax3), ylim=[0, 1.1])

        ax1.set_title("Precision")
        ax2.set_title("Recall")

        ax1.boxplot(
            [
                [d["area_precision"] for d in results["all"]],
                [d["area_precision"] for d in results["single"]],
                [d["area_precision"] for d in results["multi"]],
            ],
            labels=["All", "Single", "Multi"]
        )
        ax2.boxplot(
            [
                [d["area_recall"] for d in results["all"]],
                [d["area_recall"] for d in results["single"]],
                [d["area_recall"] for d in results["multi"]],
            ],
            labels=["All", "Single", "Multi"]
        )

        ax3.set_title("F1")
        ax3.boxplot(
            [
                [(2 * d["area_precision"] * d["area_recall"]) / (d["area_precision"] + d["area_recall"]) for d in
                 results["all"]],
                [(2 * d["area_precision"] * d["area_recall"]) / (d["area_precision"] + d["area_recall"]) for d in
                 results["single"]],
                [(2 * d["area_precision"] * d["area_recall"]) / (d["area_precision"] + d["area_recall"]) for d in
                 results["multi"]],
            ],
            labels=["All", "Single", "Multi"]

        )

        fig1.savefig("plot")

    def reproduce_fig_2(self):
        results = self.load_results()

        sheet_to_table_count = dict([(file, result["table_count"]) for file, result in results.items()])
        sheets_with_one_table = [file for file, table_count in sheet_to_table_count.items() if table_count == 1]
        sheets_with_ten_or_more_tables = [file for file, table_count in sheet_to_table_count.items() if
                                          table_count >= 10]
        max_tables = max(sheet_to_table_count.values())
        avg_tables = sum(sheet_to_table_count.values()) / len(sheet_to_table_count.keys())

        fig1, axis = plt.subplots()

        axis.set_title("Table Counts")
        axis.set_xticks(
            [x for x in range(min(sheet_to_table_count.values()), max(sheet_to_table_count.values()) + 1, 1)])
        axis.set_ylabel("#Sheets")
        axis.set_xlabel("#Tables")
        axis.hist(sheet_to_table_count.values(), bins=np.arange(max(sheet_to_table_count.values()) + 2) - 0.5)

        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)

        textstr = "\n".join([
            f"#sheets w. 1 table = {len(sheets_with_one_table)}",
            f"#sheets w. > 10 tables = {len(sheets_with_ten_or_more_tables)}",
            f"max #tables = {max_tables}",
            f"avg. #tables = {avg_tables:.4f}",
        ])
        axis.text(0.55, 0.95, textstr, transform=axis.transAxes, fontsize=14,
                  verticalalignment='top', bbox=props)

        fig1.savefig("reproduce_fig_2_table_count")

        edges = [r["result_dict"]["edge_count"] for r in results.values()]
        fig2, axis = plt.subplots()

        axis.set_title("Edge Count")
        axis.set_ylabel("#Graphs")
        axis.set_xlabel("#Edges")
        axis.hist(edges, bins=10 ** np.arange(0, 5))
        fig2.savefig("reproduce_fig_2_edge_counts")
