#!/usr/bin/env python3
"""Make supplementary upper corner braces for a Voron 2.4r2 2020 frame.

Each brace touches the underside of its top bar and the face of the corner
post that looks toward the middle of that bar. The first print layer is the
broad face nearest the corresponding outside panel. The mirrored parts keep
this face outwards in every corner. The pointed roofs on the horizontal screw
holes print without supports, and the open head pockets admit a straight hex key.

As on Voron's own frame-mounted parts, each leg carries a key that sits in the
extrusion's slot opening to centre the brace on the slot. It is 5.8 mm wide and
1 mm high, like the keys on Voron's Z idlers, with 45 degree flanks so that it
prints without supports. It runs the length of the leg and is broken only
around each screw, as the keys on Voron's skirts are, because the M5 screw hole
is almost as wide as the key. The key passes over the T-nuts: under Voron's
drop-in T-nut it leaves 0.4 mm, the same as on Voron's Z idlers.

Usage (from the repository root):
    uv run --with manifold3d==3.5.5 --with numpy==2.5.5 python -I CAD/make_braces.py [STL_DIR]
    STL_DIR defaults to the repository's STLs folder; the files are written
    into its Side, Front_Optional and Rear_Optional subfolders.
    --bar and --post change the rear brace lengths only, in millimetres.
    Re-check clearances if you change them.

Copyright (C) 2026 ChanceTheHacker. Licensed under the GNU General Public
License v3.0; see LICENSE in the repository root.
"""

import argparse
import math
import struct
from pathlib import Path

import manifold3d as m3
import numpy as np

BAR = 65.0
POST = 50.0
FRONT_BAR = 42.0
FRONT_BAR_SEATS = (14.0, 31.0)
SIDE_REAR_RIGHT_POST = 41.0  # give the rising chain bracket extra room
FLANGE = 5.0
OUTSIDE_SETBACK = 1.5  # from the outside face of the extrusion
INSIDE_SETBACK = 3.5   # keep the pads clear of the adjacent Beefy Z idler
WIDTH = 20.0 - OUTSIDE_SETBACK - INSIDE_SETBACK
SLOT_CENTRE = 10.0 - OUTSIDE_SETBACK
WEB = 7.0
FIRST_LAYER_BEVEL = 0.35
WEB_BEVEL = 0.7
HOLE_RADIUS = 2.8
HEAD_SPACE_RADIUS = 5.3  # 9.5 mm M5 button head, plus room to drop it in
KEY_WIDTH = 5.8      # at the brace face; Voron's slot opening is 6.0 mm
KEY_HEIGHT = 1.0     # into the slot opening; Voron's slot lips are 2.0 mm thick
KEY_STRAIGHT = 0.3   # full-width depth before the 45 degree flanks start
KEY_CLEAR = 4.5      # from a screw centre: 1.7 mm of flat face around the hole
KEY_START = 1.5      # from the inside corner
KEY_MIN = 3.0        # shorter stretches between screws get no key


def trimmed_extrusion(outline, height, top_bevel):
    """Build an exact loft between flat, parallel profiles with edge bevels."""
    profile = m3.CrossSection([outline])
    points = []
    for z, inset in ((0, FIRST_LAYER_BEVEL), (FIRST_LAYER_BEVEL, 0),
                     (height - top_bevel, 0), (height, top_bevel)):
        rings = profile.offset(-inset, m3.JoinType.Miter).to_polygons() if inset else [outline]
        points.extend((x, y, z) for ring in rings for x, y in ring)
    return m3.Manifold.hull_points(np.asarray(points, dtype=np.float64))


def drill_outline(radius, open_head):
    """The lower curve carries the screw; the pointed end faces away from the bed."""
    if open_head:
        angles = np.linspace(math.pi, 2 * math.pi, 33)
    else:
        angles = np.linspace(3 * math.pi / 4, 9 * math.pi / 4, 73)
    points = [(radius * math.cos(a), SLOT_CENTRE + radius * math.sin(a)) for a in angles]
    if open_head:
        points.extend(((radius, WIDTH + 1), (-radius, WIDTH + 1)))
    else:
        points.append((0, SLOT_CENTRE + math.sqrt(2) * radius))
    return m3.CrossSection([points])


def across_flange(profile, at, start, reach, in_bar):
    """Map the screw cross section into the bar's or post's flange."""
    tool = profile.extrude(reach)
    if in_bar:
        return tool.rotate((90, 0, 0)).translate((at, start + reach, 0))
    return tool.rotate((90, 0, 90)).translate((start, at, 0))


def front_curve():
    """Piecewise quadratic edge from the bar pad to the post pad."""
    def span(start, control, end, steps):
        t = np.linspace(0.0, 1.0, steps + 1)[:, None]
        return (1 - t)**2 * start + 2 * (1 - t) * t * control + t**2 * end

    # Both spans have the same tangent direction where they meet.
    a = span(np.array([39., 5.]), np.array([22., 8.]), np.array([16., 20.]), 20)
    b = span(np.array([16., 20.]), np.array([10.4, 31.2]), np.array([5., 47.]), 20)
    return np.vstack((a, b[1:]))


def key_spans(length, seats):
    """Stretches of a leg's frame face between the screw holes."""
    spans, start = [], KEY_START
    for seat in sorted(seats):
        if seat - KEY_CLEAR - start >= KEY_MIN:
            spans.append((start, seat - KEY_CLEAR))
        start = max(start, seat + KEY_CLEAR)
    # The frame face ends 1.5 mm short of the leg's tip; stop 0.5 mm inside it.
    if length - 2.0 - start >= KEY_MIN:
        spans.append((start, length - 2.0))
    return spans


def slot_key(start, end, in_bar):
    """A key on the bar's (y = 0) or the post's (x = 0) frame face.

    The key's root is buried 0.5 mm in the flange so that it fuses with it.
    Both flanks and both ends slope at 45 degrees after the straight part.
    """
    taper = KEY_HEIGHT - KEY_STRAIGHT
    points = []
    for depth, inset in ((-0.5, 0.0), (KEY_STRAIGHT, 0.0), (KEY_HEIGHT, taper)):
        for along in (start + inset, end - inset):
            for across in (-KEY_WIDTH / 2 + inset, KEY_WIDTH / 2 - inset):
                z = SLOT_CENTRE + across
                points.append((along, -depth, z) if in_bar else (-depth, along, z))
    return m3.Manifold.hull_points(np.asarray(points, dtype=np.float64))


def build(bar, post, *, arch=False, post_seats=None):
    trim = 1.5
    # Leave 1 mm at the inside corner for the extrusion edges' radius or a burr.
    root = 1.0
    bar_pad = [(root, 0), (bar - trim, 0), (bar, trim), (bar, FLANGE - 1),
               (bar - trim, FLANGE), (0, FLANGE), (0, root)]
    post_pad = [(0, root), (root, 0), (FLANGE, 0), (FLANGE, post - trim),
                (FLANGE - 1, post), (trim, post), (0, post - trim)]
    web = [(root, 0), (bar - trim, 0), (bar - 2 * trim, FLANGE),
           (FLANGE, post - 2 * trim), (0, post - trim), (0, root)]
    solid = (trimmed_extrusion(bar_pad, WIDTH, 0.45)
             + trimmed_extrusion(post_pad, WIDTH, 0.45))
    web_solid = trimmed_extrusion(web, WEB, WEB_BEVEL)
    if arch:
        # The bevelled blank is convex. Cut out the curved edge rather than
        # passing a concave outline to the convex hull used for its bevels.
        cut = [*map(tuple, front_curve()), (bar + 1, post + 1), (bar + 1, FLANGE)]
        web_solid -= m3.CrossSection([cut[::-1]]).extrude(WEB + 2).translate((0, 0, -1))
    solid += web_solid

    shaft = drill_outline(HOLE_RADIUS, open_head=False)
    for in_bar, length, reach in ((True, bar, post), (False, post, bar)):
        # The reliefs cross in the web. Stagger their floors a fraction to avoid
        # a tangential intersection between two perfectly co-planar cutters.
        head = drill_outline(HEAD_SPACE_RADIUS + (0.0 if in_bar else 0.05), open_head=True)
        seats = (17.0, length - 13.0)
        if arch and in_bar:
            seats = FRONT_BAR_SEATS
        elif not in_bar and post_seats is not None:
            seats = post_seats
        for start, end in key_spans(length, seats):
            solid += slot_key(start, end, in_bar)
        for at in seats:
            solid -= across_flange(shaft, at, -1.0, FLANGE + 2.0, in_bar)
            solid -= across_flange(head, at, FLANGE, reach, in_bar)

    return checked_solid(solid)


def build_side(post=POST):
    """Keep both mounting slots, but recess the edge next to the Z pulley."""
    recess = [(5, WIDTH), (8, WIDTH - 1.5), (35, WIDTH - 1.5), (38, WIDTH),
              (38, WIDTH + 1), (5, WIDTH + 1)]
    cutter = m3.CrossSection([recess]).extrude(FLANGE + 2)
    cutter = cutter.rotate((90, 0, 0)).translate((0, FLANGE + 1, 0))
    seats = (14.0, post - 13.0) if post < POST else None
    return checked_solid(build(BAR, post, post_seats=seats) - cutter)


def checked_solid(solid):
    solid = solid.simplify(0.0001)
    if solid.status() != m3.Error.NoError or len(solid.decompose()) != 1 or solid.volume() <= 0:
        raise ValueError('The brace is not one closed solid.')
    return solid


def save_stl(solid, path, label):
    mesh = solid.to_mesh()
    tris = np.asarray(mesh.vert_properties)[np.asarray(mesh.tri_verts), :3]
    normals = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    sizes = np.linalg.norm(normals, axis=1)
    if np.any(sizes <= 0):
        raise ValueError('The STL would contain a zero-area face.')
    records = np.zeros(len(tris), dtype=[('n', '<3f4'), ('v', '<9f4'), ('a', '<u2')])
    records['n'] = normals / sizes[:, None]
    records['v'] = tris.reshape(-1, 9)
    header = label.encode('ascii')
    if len(header) > 80:
        raise ValueError('The STL label exceeds its 80-byte header.')
    with path.open('wb') as f:
        f.write(header.ljust(80, b' '))
        f.write(struct.pack('<I', len(tris)))
        f.write(records.tobytes())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    default_dir = Path(__file__).resolve().parent.parent / 'STLs'
    parser.add_argument('output_dir', type=Path, nargs='?', default=default_dir)
    parser.add_argument('--bar', type=float, default=BAR)
    parser.add_argument('--post', type=float, default=POST)
    args = parser.parse_args()
    if not all(math.isfinite(x) and x >= 44 for x in (args.bar, args.post)):
        parser.error('both legs must be at least 44 mm long to keep two screw seats per leg')
    rear = build(args.bar, args.post)
    side = build_side()
    front = build(FRONT_BAR, POST, arch=True)
    # With the flat print face out and the long leg under the bar, the
    # left/right mirror order on the rear is the opposite of the front.
    # Each entry: (folder, file name, position label, solid).
    parts = [
        ('Side', 'upper_brace_side_front_left.stl', 'side-front-left', mirrored(side, BAR)),
        ('Side', 'upper_brace_side_front_right_rear_left_x2.stl', 'side-front-right-rear-left', side),
        ('Side', 'upper_brace_side_rear_right.stl', 'side-rear-right',
         mirrored(build_side(SIDE_REAR_RIGHT_POST), BAR)),
        ('Front_Optional', 'upper_brace_front_left.stl', 'front-left', front),
        ('Front_Optional', 'upper_brace_front_right.stl', 'front-right', mirrored(front, FRONT_BAR)),
        ('Rear_Optional', 'upper_brace_rear_left.stl', 'rear-left', mirrored(rear, args.bar)),
        ('Rear_Optional', 'upper_brace_rear_right.stl', 'rear-right', rear),
    ]
    for folder, name, position, part in parts:
        path = args.output_dir / folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        # The header wording is kept exactly as in the released files, so a
        # rebuild with the default sizes is byte-identical to the STLs folder.
        unit = 'millimetres' if position.startswith('rear-') else 'mm'
        save_stl(part, path, f"Voron upper {position.replace('-', ' ')} brace, {unit}, print flat as supplied")
        print(f'{folder}/{name}: {part.volume() / 1000:.1f} cm³')


def mirrored(solid, bar):
    return solid.mirror((1, 0, 0)).translate((bar, 0, 0))


if __name__ == '__main__':
    main()
