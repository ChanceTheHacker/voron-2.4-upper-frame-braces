#!/usr/bin/env python3
"""Draw Images/corner_map.png: the top of the frame seen from above, and which brace file goes where.

The side braces (fit all four) are solid green on the side bars; the optional front and
rear pairs are dashed on the front and back bars. Left and right are as seen standing in
front of the printer, which is at the bottom of the picture.

Usage (from anywhere):
    uv run --with matplotlib python -I corner_map.py OUT_PNG
Needs the Noto Sans font installed.
"""
import sys

import matplotlib

matplotlib.use('Agg')
import matplotlib.font_manager as fm  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

FONT = 'Noto Sans'
BACKGROUND = '#f6f8fa'
INK = '#1f2328'
MUTED = '#59636e'
GREEN = '#3fb950'
GREEN_DARK = '#1a7f37'
BAR_FILL = '#d5dae0'
BAR_LINE = '#8c959f'
POST = '#57606a'

W, H = 1600, 960           # pixels; the drawing works in pixels with y up
LEFT, RIGHT = 600, 1000    # centre lines of the left and right top bars
FRONT, REAR = 305, 705     # centre lines of the front and back top bars
BAR = 30                   # drawn width of a 2020 bar
BRACE_LEN = 112            # drawn length of a brace along its bar
BRACE_W = 18               # drawn width of a brace marker


def side_brace(x, y0, y1):
    """Solid marker along a side bar."""
    return Rectangle((x - BRACE_W / 2, min(y0, y1)), BRACE_W, abs(y1 - y0),
                     facecolor=GREEN, edgecolor=GREEN_DARK, lw=1.6, zorder=5)


def optional_brace(y, x0, x1):
    """Dashed marker along the front or back bar."""
    return Rectangle((min(x0, x1), y - BRACE_W / 2), abs(x1 - x0), BRACE_W,
                     facecolor='white', edgecolor=GREEN_DARK, lw=2.0, ls=(0, (4, 2.5)), zorder=5)


def label(ax, x, y, name, note, ha, primary):
    """File name (bold for the side braces) with a short muted note under it."""
    ax.text(x, y + 2, name, ha=ha, va='bottom', fontsize=18,
            weight='bold' if primary else 'normal', color=INK)
    ax.text(x, y - 4, note, ha=ha, va='top', fontsize=16, color=MUTED)


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    out = sys.argv[1]
    fm.findfont(fm.FontProperties(family=FONT), fallback_to_default=False)
    plt.rcParams.update({'font.family': FONT, 'text.color': INK})
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100, facecolor=BACKGROUND)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis('off')

    fig.text(0.5, 1 - 62 / H, 'Where each brace goes, seen from above', ha='center', va='baseline',
             fontsize=30, weight='bold')
    fig.text(0.5, 1 - 108 / H, 'The top of the frame. Left and right are as seen standing in front '
             'of the printer.', ha='center', va='baseline', fontsize=20, color=MUTED)

    # The four top bars and the corner posts.
    half = BAR / 2
    for x in (LEFT, RIGHT):
        ax.add_patch(Rectangle((x - half, FRONT - half), BAR, REAR - FRONT + BAR,
                               facecolor=BAR_FILL, edgecolor=BAR_LINE, lw=1.4, zorder=1))
    for y in (FRONT, REAR):
        ax.add_patch(Rectangle((LEFT - half, y - half), RIGHT - LEFT + BAR, BAR,
                               facecolor=BAR_FILL, edgecolor=BAR_LINE, lw=1.4, zorder=1))
    for x in (LEFT, RIGHT):
        for y in (FRONT, REAR):
            ax.add_patch(Rectangle((x - half, y - half), BAR, BAR, facecolor=POST, edgecolor=POST, zorder=2))

    # Side braces, under the side bars at each corner.
    start = half + 8
    ax.add_patch(side_brace(LEFT, FRONT + start, FRONT + start + BRACE_LEN))
    ax.add_patch(side_brace(LEFT, REAR - start, REAR - start - BRACE_LEN))
    ax.add_patch(side_brace(RIGHT, FRONT + start, FRONT + start + BRACE_LEN))
    ax.add_patch(side_brace(RIGHT, REAR - start, REAR - start - BRACE_LEN))
    yf, yr = FRONT + start + BRACE_LEN / 2, REAR - start - BRACE_LEN / 2
    gap = half + 26
    label(ax, LEFT - gap, yr, 'upper_brace_side_front_right_rear_left_x2',
          'rear-left corner; the same file as front-right', 'right', True)
    label(ax, LEFT - gap, yf, 'upper_brace_side_front_left', 'front-left corner', 'right', True)
    label(ax, RIGHT + gap, yr, 'upper_brace_side_rear_right', 'rear-right corner; shorter leg on the post',
          'left', True)
    label(ax, RIGHT + gap, yf, 'upper_brace_side_front_right_rear_left_x2',
          'front-right corner; the same file as rear-left', 'left', True)

    # Optional braces, under the back bar and the front bar at their ends.
    ax.add_patch(optional_brace(REAR, LEFT + start, LEFT + start + BRACE_LEN))
    ax.add_patch(optional_brace(REAR, RIGHT - start, RIGHT - start - BRACE_LEN))
    ax.add_patch(optional_brace(FRONT, LEFT + start, LEFT + start + BRACE_LEN))
    ax.add_patch(optional_brace(FRONT, RIGHT - start, RIGHT - start - BRACE_LEN))
    # Each label lines up with the inner end of its marker and reaches outwards, past the corner.
    lx, rx = LEFT + start + BRACE_LEN, RIGHT - start - BRACE_LEN
    up, down = REAR + half + 38, FRONT - half - 62
    label(ax, lx, up, 'upper_brace_rear_left', 'optional, under the rear bar', 'right', False)
    label(ax, rx, up, 'upper_brace_rear_right', 'optional, under the rear bar', 'left', False)
    label(ax, lx, down, 'upper_brace_front_left', 'optional, arched, under the front bar', 'right', False)
    label(ax, rx, down, 'upper_brace_front_right', 'optional, arched, under the front bar', 'left', False)

    # Front marker.
    ax.text((LEFT + RIGHT) / 2, FRONT + half + 26, 'FRONT', ha='center', va='bottom', fontsize=22,
            weight='bold', color=MUTED)
    ax.text((LEFT + RIGHT) / 2, REAR - half - 26, 'REAR', ha='center', va='top', fontsize=22,
            weight='bold', color=MUTED)

    # Legend.
    ly = 80
    ax.add_patch(Rectangle((372, ly - 9), 56, BRACE_W, facecolor=GREEN, edgecolor=GREEN_DARK, lw=1.6))
    ax.text(442, ly, 'Side braces: fit all four', va='center', fontsize=19)
    ax.add_patch(Rectangle((842, ly - 9), 56, BRACE_W, facecolor='white', edgecolor=GREEN_DARK,
                           lw=2.0, ls=(0, (4, 2.5))))
    ax.text(912, ly, 'Optional front and rear pairs', va='center', fontsize=19)
    ax.text(W / 2, ly - 42, '_x2 at the end of a file name means print two.', ha='center', va='center',
            fontsize=16, color=MUTED)

    fig.savefig(out, dpi=100, facecolor=BACKGROUND)
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
