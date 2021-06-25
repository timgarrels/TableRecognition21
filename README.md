# TableRecognition21

[Table Recognition Seminar SS21 HPI](https://hpi.de/naumann/teaching/current-courses/ss-21/table-recognition.html)

Implementing and improving  
`Koci, E., Thiele, M., Romero, O. and Lehner, W. 2019. A Genetic-Based Search for Adaptive Table Recognition in Spreadsheets. International Conference on Document Analysis and Recognition (ICDAR)`

## Overview

This algorithm uses a graph representation of annotated regions within a spreadsheet to do table recognition. The
annotated regions ("label regions") are turned into nodes within a graph. The edges are formed by horizontal or vertical
alignment of these label regions.

The components in the graph represent table definitions. All label regions (=nodes) within a component belong to the
same table.

By removing edges we can create components. If we iterate over all possible edge combinations we will find all possible
table definitions. This is exactly what the `ExhaustiveSearch` does.

However, the search space scales with the edge count within the graph, and makes the exhaustive search unfeasible. We
therefore introduce `GeneticSearch`, a genetic approach to scan a part of the total search space. It is used on graphs
with more than 10 edges.

The quality of a graph with a specific edge list is measured with metrics defined in `FitnessRater`.

## Usage

There are two experiments in this repository:

### NoTrainingNoSeed

This algorithm will perform the searches as explained above on all annotated spreadsheets. The results are evaluated
with precision, recall and F1 scores.

```
python3 src/run_no_training.py --dataset FusTe
```

### CrossValidationTraining

This algorithm will cross validate the machine learning approach to tune the metrics to a specific dataset. As it can
run really long, there is the option to split the run into separate folds.

Complete run: `python3 src/run_cross_validation.py --dataset Test --action full_run`

To split, call in this order:

```
python3 src/run_cross_validation.py --dataset Test --action prepare

python3 src/run_cross_validation.py --dataset Test --action run_fold_number --fold-number 0
python3 src/run_cross_validation.py --dataset Test --action run_fold_number --fold-number ...
python3 src/run_cross_validation.py --dataset Test --action run_fold_number --fold-number 9


python3 src/run_cross_validation.py --dataset Test --action finalize
```