from typing import List, Dict

from labelregions.BoundingBox import BoundingBox


def table_overlap(ground_truth_table: BoundingBox, detected_table: BoundingBox):
    """See Table Detection in Heterogeneous Documents 4., eq. 1"""
    cells = ground_truth_table.intersection(detected_table)
    return (2 * len(cells)) / (ground_truth_table.area + detected_table.area)


def detection_evaluation(ground_truth_tables: List[BoundingBox], detected_tables: List[BoundingBox]):
    """See Table Detection in Heterogeneous Documents 4."""
    ground_truth_overlap_to_detected: Dict[BoundingBox, Dict[BoundingBox, float]] = {}.fromkeys(ground_truth_tables, {})
    detected_overlap_to_ground_truth: Dict[BoundingBox, Dict[BoundingBox, float]] = {}.fromkeys(detected_tables, {})

    # Create an overlap lookup in both directions
    # ground_truth -> detected & overlap, detected -> ground_truth & overlap
    for ground_truth_table in ground_truth_tables:
        for detected_table in detected_tables:
            overlap = table_overlap(ground_truth_table, detected_table)
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


def area_precision_and_recall(ground_truth_tables: List[BoundingBox], detected_tables: List[BoundingBox]):
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
    }
