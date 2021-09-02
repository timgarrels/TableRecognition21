"""Methods to analyse detected vs ground truth results"""

from typing import List, Dict

from labelregions.BoundingBox import BoundingBox


def bayesian_scores(
        ground_truth_tables: List[BoundingBox],
        detected_tables: List[BoundingBox],
) -> Dict[str, float]:
    """Calculates precision, recall and F1 score and returns a dict containing these values"""
    cells_in_detected_tables = []
    for detected_table in detected_tables:
        cells_in_detected_tables.extend(detected_table.cells())

    cells_in_ground_truth_tables = []
    for ground_truth_table in ground_truth_tables:
        cells_in_ground_truth_tables.extend(ground_truth_table.cells())

    true_positives = set(cells_in_detected_tables).intersection(cells_in_ground_truth_tables)

    area_precision = len(true_positives) / len(cells_in_detected_tables)
    area_recall = len(true_positives) / len(cells_in_ground_truth_tables)

    return {
        "area_precision": area_precision,
        "area_recall": area_recall,
        "area_f1": (2 * area_precision * area_recall) / (area_precision + area_recall)
    }


def _table_overlap(ground_truth_table: BoundingBox, detected_table: BoundingBox) -> float:
    """See Table Detection in Heterogeneous Documents 4., Shafait et al., 2010, eq. 1"""
    overlap = ground_truth_table.intersection(detected_table)
    return (2 * overlap) / (ground_truth_table.area + detected_table.area)


def detection_evaluation(
        ground_truth_tables: List[BoundingBox],
        detected_tables: List[BoundingBox],
) -> Dict[str, int]:
    """See Table Detection in Heterogeneous Documents 4., Shafait et al., 2010"""
    ground_truth_overlap_to_detected: Dict[BoundingBox, Dict[BoundingBox, float]] = {}.fromkeys(
        ground_truth_tables, {})
    detected_overlap_to_ground_truth: Dict[BoundingBox, Dict[BoundingBox, float]] = {}.fromkeys(
        detected_tables, {})

    # Create an overlap lookup in both directions
    # ground_truth -> detected & overlap, detected -> ground_truth & overlap
    for ground_truth_table in ground_truth_tables:
        for detected_table in detected_tables:
            overlap = _table_overlap(ground_truth_table, detected_table)
            ground_truth_overlap_to_detected[ground_truth_table][detected_table] = overlap
            detected_overlap_to_ground_truth[detected_table][ground_truth_table] = overlap

    correct_detections = 0
    partial_detections = 0
    over_segmented_tables = 0
    under_segmented_tables = 0
    missed_tables = 0
    false_positive_detections = 0
    for ground_truth_table, detected_overlap_lookup in ground_truth_overlap_to_detected.items():
        detected_with_major_overlap = [detected for detected, overlap in detected_overlap_lookup.items() if
                                       overlap >= 0.9]

        detected_with_partial_overlap = [detected for detected, overlap in detected_overlap_lookup.items() if
                                         0.1 < overlap < 0.9]

        if len(detected_with_major_overlap) > 0:
            correct_detections += 1

        if len(detected_with_partial_overlap) == 1:
            partial_detections += 1
        elif len(detected_with_partial_overlap) > 1:
            over_segmented_tables += 1

        for detected_table in detected_overlap_lookup.keys():
            major_overlap = [ground_truth
                             for ground_truth, overlap in detected_overlap_to_ground_truth[detected_table].items()
                             if 0.1 < overlap < 0.9]
            if len(major_overlap) > 1:
                # A detected table matching this ground truth has multiple major overlaps, under-segmentation!
                under_segmented_tables += 1
                break

        if len(detected_with_major_overlap) == 0 and len(detected_with_partial_overlap) == 0:
            missed_tables += 1

    for detected_table, ground_truth_overlap_lookup in detected_overlap_to_ground_truth.items():
        ground_truth_with_major_overlap = [ground_truth
                                           for ground_truth, overlap in ground_truth_overlap_lookup.items()
                                           if overlap > 0.1]
        if len(ground_truth_with_major_overlap) == 0:
            false_positive_detections += 1

    return {
        "correct_detections": correct_detections,
        "partial_detections": partial_detections,
        "over_segmented_tables": over_segmented_tables,
        "under_segmented_tables": under_segmented_tables,
        "missed_tables": missed_tables,
        "false_positive_detections": false_positive_detections,
    }


def accuracy_based_on_jacard_index(
        ground_truth: List[BoundingBox],
        computed_result: List[BoundingBox],
) -> float:
    """Percent of recognized tables as proposed in the paper Section V.D, based on the jacard index"""
    recognized_tables = []
    for table in ground_truth:
        for computed_table in computed_result:
            cells_in_common = table.intersection(computed_table)
            cells_in_union = table.area + computed_table.area - cells_in_common
            jacard_index = cells_in_common / cells_in_union
            if jacard_index >= 0.9:
                recognized_tables.append(table)
    return len(set(recognized_tables)) / len(ground_truth)
