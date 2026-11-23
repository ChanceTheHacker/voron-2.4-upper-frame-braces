"""Render Images/overview.png: one of each of the seven brace files, as printed.

The three side braces stand in the front row; behind them, the optional front pair
on the left and the optional rear pair on the right.

Usage (from anywhere):
    blender -b --factory-startup -P render_overview.py -- STL_DIR OUT_PNG
STL_DIR is this repo's STLs folder (with Side, Front_Optional and Rear_Optional inside).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import studio  # noqa: E402

ROWS = [  # each row is a list of groups, nearest the camera first
    [('Side', ['upper_brace_side_front_left', 'upper_brace_side_front_right_rear_left_x2',
               'upper_brace_side_rear_right'])],
    [('Front_Optional', ['upper_brace_front_left', 'upper_brace_front_right']),
     ('Rear_Optional', ['upper_brace_rear_left', 'upper_brace_rear_right'])],
]
PART_GAP = 12.0    # mm between braces in a group
GROUP_GAP = 40.0   # mm between groups in a row
ROW_GAP = 30.0     # mm between rows

if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    if len(args) != 2:
        raise SystemExit(__doc__)
    stl_dir, out = Path(args[0]), Path(args[1])
    studio.reset()
    green = studio.part_material(studio.MOD_GREEN, 'mod')
    y = 0.0
    for row in ROWS:
        placed, x, depth = [], 0.0, 0.0
        for gi, (folder, names) in enumerate(row):
            if gi:
                x += GROUP_GAP - PART_GAP
            for name in names:
                obj = studio.load_stl(stl_dir / folder / f'{name}.stl')
                studio.paint(obj, green)
                size = studio.place(obj)
                obj.location = (x + size[0] / 2, y + size[1] / 2, 0)
                placed.append(obj)
                x += size[0] + PART_GAP
                depth = max(depth, size[1])
        for obj in placed:          # centre each row on x = 0
            obj.location.x -= (x - PART_GAP) / 2
        y += depth + ROW_GAP
    studio.lighting()
    studio.camera_three_quarter(1600, 880, azimuth=-22, elevation=44)
    studio.render(out)
