import logging
import random
from typing import List

from openpyxl import Workbook
from openpyxl.styles import Color, PatternFill

from labelregions.LabelRegion import LabelRegion

logger = logging.getLogger(__name__)


def random_rgb_hex():
    """Creates a random rgb string like 00FF00FF"""
    return ''.join([hex(random.choice(range(16)))[2:] for _ in range(8)])


def add_lr_visualization(lrs: List[LabelRegion], workbook: Workbook, sheet_name="Label Region Visualization"):
    """Creates a colorful spreadsheet from the lr data"""
    ws = workbook.create_sheet(sheet_name)
    for i, lr in enumerate(lrs):
        color = Color(rgb=random_rgb_hex())
        fill = PatternFill(patternType='solid', fgColor=color)
        # Y is our row, X our column
        for y in range(lr.top, lr.bottom + 1):
            for x in range(lr.left, lr.right + 1):
                # Cell is referred by row, col
                d = ws.cell(y, x)
                d.value = f"{i} - {str(lr.type.value)}"
                d.fill = fill
