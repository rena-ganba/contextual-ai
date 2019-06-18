FIGURE_WIDTH = 120
FIGURE_HEIGHT = 60

SUBFIGURE_WIDTH = 70
SUBFIGURE_HEIGHT = 35

LARGE_FIGURE_WIDTH = 180
LARGE_FIGURE_HEIGHT = 85
TRIPLE_FIGURE_WIDTH = 50
TRIPLE_FIGURE_HEIGHT = 50

"""
ABSOLUTE_3_LEFT_BIG_GRID_SPEC
==============
|        | 1 |
|   0    |---|
|        | 2 |
==============


ABSOLUTE_3_RIGHT_BIG_GRID_SPEC
=============
| 0 |       |
|---|   2   |
| 1 |       |
=============

ABSOLUTE_3_EQUAL_GRID_SPEC
=======================
    |     |     |     |
'30'|  0  |  1  |  2  |
    |     |     |     |
=======================

ABSOLUTE_3_COMPARISON_2_GRID_SPEC
================
 0 |  1  |  2  |
================
"""

ABSOLUTE_LEFT_BIG_3_GRID_SPEC = {0: (0, 0, FIGURE_WIDTH, FIGURE_HEIGHT),
                                 1: (FIGURE_WIDTH, 0, SUBFIGURE_WIDTH, SUBFIGURE_HEIGHT),
                                 2: (FIGURE_WIDTH, SUBFIGURE_HEIGHT, SUBFIGURE_WIDTH, SUBFIGURE_HEIGHT)}

ABSOLUTE_RIGHT_BIG_3_GRID_SPEC = {0: (0, 0, SUBFIGURE_WIDTH, SUBFIGURE_HEIGHT),
                                  1: (0, SUBFIGURE_HEIGHT, SUBFIGURE_WIDTH, SUBFIGURE_HEIGHT),
                                  2: (SUBFIGURE_WIDTH, 0, FIGURE_WIDTH, FIGURE_HEIGHT)}

ABSOLUTE_RESULT_3_EQUAL_GRID_SPEC = {0: (30, 0, TRIPLE_FIGURE_WIDTH, TRIPLE_FIGURE_HEIGHT),
                                     1: (30 + TRIPLE_FIGURE_WIDTH, 0, TRIPLE_FIGURE_WIDTH, TRIPLE_FIGURE_HEIGHT),
                                     2: (30 + TRIPLE_FIGURE_WIDTH * 2, 0, TRIPLE_FIGURE_WIDTH, TRIPLE_FIGURE_HEIGHT)}

ABSOLUTE_3_COMPARISON_2_GRID_SPEC = {0: (0, 0, 35, 35),
                                     1: (35, 0, 70, 35),
                                     2: (105, 0, 70, 35)}
