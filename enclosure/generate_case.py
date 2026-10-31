"""
Laser-Cut Enclosure & Precision Spool Kit Generator for ESP32 Smart Curtain Opener
Material: 3.0mm Plywood / MDF (Sheet Size: 450 mm x 300 mm)
Compatible with Epilog Mini 24, CorelDraw, LightBurn, Illustrator

Generates:
1. curtain_case_3mm.svg (Red #FF0000 0.1mm = Vector Cut, Black = Raster Engrave)
2. curtain_case_3mm.dxf (AutoCAD R12 DXF format with layers CUT_RED and ENGRAVE_BLACK)

Features:
- Inset Base Tabs on Side Walls (14mm flat corners to prevent corner tab binding)
- Front Plate (103.5 x 73.5 mm) sized to slide inside 104 x 74 mm cavity with 0.5mm clearance
- Internal Divider (74 x 43.5 mm) acting as mechanical backstop for Front Plate
- 28BYJ-48 motor mount with 4.2mm M4 screw holes and accurate 8.0mm eccentric shaft offset
- Top Face features both Motor and USB-C power port (aligned with overhead power strip)
- 4x 4.2mm wardrobe mounting screw holes on Base Plate (128 x 48 mm rectangular pitch)
- Gravity-hung T-Pins (11x7mm low-profile head, 5mm shaft, 96mm long, chamfered tip)
- Laser-Cut Spool Kit: 2x complete multi-layer wooden spools with exact 5mm D-shaft keyways,
  string-knot capture holes, toothpick alignment dowels, and 3mm motor spacer washers!
"""

import os
import math
from export_dxf import DxfWriter

def d_hole_svg(cx, cy, r=2.5, d=1.5):
    x_int = math.sqrt(r**2 - d**2)
    return (
        f"M {cx - x_int:.2f} {cy - d:.2f} "
        f"L {cx + x_int:.2f} {cy - d:.2f} "
        f"A {r:.2f} {r:.2f} 0 0 1 {cx + x_int:.2f} {cy + d:.2f} "
        f"L {cx - x_int:.2f} {cy + d:.2f} "
        f"A {r:.2f} {r:.2f} 0 0 1 {cx - x_int:.2f} {cy - d:.2f} Z"
    )

def d_hole_dxf(cx, cy, r=2.5, d=1.5, n_arc=6):
    x_int = math.sqrt(r**2 - d**2)
    pts = [(cx - x_int, cy - d), (cx + x_int, cy - d)]
    a_start = -math.asin(d/r)
    a_end = math.asin(d/r)
    for i in range(1, n_arc + 1):
        a = a_start + (a_end - a_start) * (i / n_arc)
        pts.append((cx + r*math.cos(a), cy + r*math.sin(a)))
    pts.append((cx - x_int, cy + d))
    a_left_start = math.pi - a_end
    a_left_end = math.pi - a_start
    for i in range(1, n_arc + 1):
        a = a_left_start + (a_left_end - a_left_start) * (i / n_arc)
        pts.append((cx + r*math.cos(a), cy + r*math.sin(a)))
    pts.append(pts[0])
    return pts

def generate_case(output_svg_path, output_dxf_path):
    t = 3.0        # 3.0mm wood plank thickness
    W = 110.0      # Box outer width
    D_body = 74.0  # Side walls inner body length
    D_outer = 80.0 # Box outer depth (74 + 2*t)
    H = 52.0       # Box height
    ear = 18.0     # Mounting flange width on Base plate

    NW = 7
    sW = W / NW    # 15.714 mm
    NH = 3
    sH = H / NH    # 17.333 mm

    # =========================================================================
    # 1. GENERATE SVG
    # =========================================================================
    svg = []
    svg.append('<svg xmlns="http://www.w3.org/2000/svg" width="450mm" height="300mm" viewBox="0 0 450 300">')
    svg.append('<!-- 450 x 300 mm Plank. RED (#FF0000 0.1mm) = Cut, BLACK = Engrave -->')
    svg.append('<defs><style>')
    svg.append('  .cut { stroke: #ff0000; stroke-width: 0.1; fill: none; }')
    svg.append('  .engrave { fill: #000000; font-family: "Arial", sans-serif; }')
    svg.append('</style></defs>')

    # --- ROW 1 (Y ≈ 15 to 95 mm) ---
    # 1. Base Plate
    bx, by = 15.0, 15.0
    base_outer = [
        f"M {bx + ear} {by}",
        f"L {bx + ear + W} {by}",
        f"L {bx + 2*ear + W} {by + 6}",
        f"L {bx + 2*ear + W} {by + D_outer - 6}",
        f"L {bx + ear + W} {by + D_outer}",
        f"L {bx + ear} {by + D_outer}",
        f"L {bx} {by + D_outer - 6}",
        f"L {bx} {by + 6}",
        "Z"
    ]
    svg.append(f'<path class="cut" d="{" ".join(base_outer)}" />')

    # 4x Mounting screw holes
    left_x = bx + ear / 2.0
    right_x = bx + 2*ear + W - ear / 2.0
    top_y = by + 16.0
    bot_y = by + D_outer - 16.0
    svg.append(f'<circle class="cut" cx="{left_x}" cy="{top_y}" r="2.1" />')
    svg.append(f'<circle class="cut" cx="{left_x}" cy="{bot_y}" r="2.1" />')
    svg.append(f'<circle class="cut" cx="{right_x}" cy="{top_y}" r="2.1" />')
    svg.append(f'<circle class="cut" cx="{right_x}" cy="{bot_y}" r="2.1" />')

    # Top & Bottom wall mortises on base
    for i in [0, 2, 4, 6]:
        slot_x = bx + ear + i * sW
        svg.append(f'<rect class="cut" x="{slot_x}" y="{by + D_outer - t}" width="{sW}" height="{t}" rx="0.1" />')
        svg.append(f'<rect class="cut" x="{slot_x}" y="{by}" width="{sW}" height="{t}" rx="0.1" />')

    # Inset Left & Right wall mortises
    for y_slot in [32.0, 60.0]:
        svg.append(f'<rect class="cut" x="{bx + ear}" y="{by + y_slot}" width="{t}" height="18.0" rx="0.1" />')
        svg.append(f'<rect class="cut" x="{bx + ear + W - t}" y="{by + y_slot}" width="{t}" height="18.0" rx="0.1" />')

    # ULN2003 mounting holes on base
    svg.append(f'<circle class="cut" cx="{bx + ear + 10.0}" cy="{by + 27.0}" r="1.5" />')
    svg.append(f'<circle class="cut" cx="{bx + ear + 40.0}" cy="{by + 27.0}" r="1.5" />')
    svg.append(f'<circle class="cut" cx="{bx + ear + 10.0}" cy="{by + 53.0}" r="1.5" />')
    svg.append(f'<circle class="cut" cx="{bx + ear + 40.0}" cy="{by + 53.0}" r="1.5" />')
    svg.append(f'<text class="engrave" x="{bx + ear + 25.0}" y="{by + 41.0}" font-size="3" text-anchor="middle">ULN2003 MOUNT</text>')

    # Internal divider floor mortises
    div_floor_x = bx + ear + 52.0
    svg.append(f'<rect class="cut" x="{div_floor_x}" y="{by + 16.0}" width="{t}" height="10.0" rx="0.1" />')
    svg.append(f'<rect class="cut" x="{div_floor_x}" y="{by + 54.0}" width="{t}" height="10.0" rx="0.1" />')

    svg.append(f'<text class="engrave" x="{bx + ear + 82.0}" y="{by + 41.0}" font-size="3.5" text-anchor="middle">ESP32 ZONE</text>')
    svg.append(f'<text class="engrave" x="{bx + ear + W/2}" y="{by + 10.0}" font-size="3.8" text-anchor="middle">BASE (4x CLOSET SCREWS)</text>')

    # 2. Front Plate (Removable Lid)
    tx, ty = 180.0, 15.0
    lid_w, lid_d = 103.5, 73.5
    svg.append(f'<rect class="cut" x="{tx}" y="{ty}" width="{lid_w}" height="{lid_d}" rx="1.0" />')
    svg.append(f'<text class="engrave" x="{tx + lid_w/2}" y="{ty + 28}" font-size="7.0" font-weight="bold" text-anchor="middle">☀️ SMART CURTAIN</text>')
    svg.append(f'<text class="engrave" x="{tx + lid_w/2}" y="{ty + 40}" font-size="3.8" text-anchor="middle">WAKE-UP AUTOMATION</text>')
    svg.append(f'<text class="engrave" x="{tx + lid_w/2}" y="{ty + 51}" font-size="3.0" text-anchor="middle">ESP32 • 28BYJ-48 • NTP CLOCK</text>')

    # 3. Left Wall (Vents)
    lx, ly = 305.0, 15.0
    pts_left = [(lx, ly), (lx + D_body, ly), (lx + D_body + t, ly)]
    for k in range(NH):
        y1 = ly + k * sH
        y2 = ly + (k + 1) * sH
        tab = (k % 2 == 0)
        x_val = lx + D_body + t if tab else lx + D_body
        pts_left.extend([(x_val, y1), (x_val, y2)])
    pts_left.append((lx + D_body - 14.0, ly + H))
    pts_left.append((lx + D_body - 14.0, ly + H + t))
    pts_left.append((lx + D_body - 32.0, ly + H + t))
    pts_left.append((lx + D_body - 32.0, ly + H))
    pts_left.append((lx + D_body - 42.0, ly + H))
    pts_left.append((lx + D_body - 42.0, ly + H + t))
    pts_left.append((lx + 14.0, ly + H + t))
    pts_left.append((lx + 14.0, ly + H))
    pts_left.append((lx, ly + H))
    for k in range(NH - 1, -1, -1):
        y1 = ly + (k + 1) * sH
        y2 = ly + k * sH
        tab = (k % 2 == 0)
        x_val = lx - t if tab else lx
        pts_left.extend([(x_val, y1), (x_val, y2)])
    pts_left.append(pts_left[0])
    d_left = "M " + " L ".join([f"{p[0]:.2f} {p[1]:.2f}" for p in pts_left]) + " Z"
    svg.append(f'<path class="cut" d="{d_left}" />')

    for v in range(-2, 3):
        vx = lx + D_body/2 + v * 8.0 - 1.5
        svg.append(f'<rect class="cut" x="{vx}" y="{ly + 16.0}" width="3.0" height="20.0" rx="1.5" />')
    svg.append(f'<text class="engrave" x="{lx + D_body/2}" y="{ly + 42}" font-size="3.5" text-anchor="middle">LEFT (VENTS)</text>')

    # --- ROW 2 (Y ≈ 110 to 165 mm) ---
    # 4. Top Face (Motor + USB-C)
    fx, fy = 15.0, 110.0
    pts_top = [(fx, fy), (fx + W, fy)]
    for k in range(NH):
        y1 = fy + k * sH
        y2 = fy + (k + 1) * sH
        slot = (k % 2 == 0)
        x_val = fx + W - t if slot else fx + W
        pts_top.extend([(x_val, y1), (x_val, y2)])
    pts_top.append((fx + W, fy + H))
    pts_top.append((fx + W, fy + H + t))
    for j in range(NW - 1, -1, -1):
        x1 = fx + (j + 1) * sW
        x2 = fx + j * sW
        tab = (j % 2 == 0)
        y_val = fy + H + t if tab else fy + H
        pts_top.extend([(x1, y_val), (x2, y_val)])
    pts_top.append((fx, fy + H))
    for k in range(NH - 1, -1, -1):
        y1 = fy + (k + 1) * sH
        y2 = fy + k * sH
        slot = (k % 2 == 0)
        x_val = fx + t if slot else fx
        pts_top.extend([(x_val, y1), (x_val, y2)])
    pts_top.append(pts_top[0])
    d_top = "M " + " L ".join([f"{p[0]:.2f} {p[1]:.2f}" for p in pts_top]) + " Z"
    svg.append(f'<path class="cut" d="{d_top}" />')

    # Link pin holes in Top Face
    svg.append(f'<rect class="cut" x="{fx + 8.0 - 2.75}" y="{fy + 2.0}" width="5.5" height="3.5" rx="0.3" />')
    svg.append(f'<rect class="cut" x="{fx + 102.0 - 2.75}" y="{fy + 2.0}" width="5.5" height="3.5" rx="0.3" />')
    svg.append(f'<text class="engrave" x="{fx + 8.0}" y="{fy + 8.5}" font-size="2.0" text-anchor="middle">PIN 1</text>')
    svg.append(f'<text class="engrave" x="{fx + 102.0}" y="{fy + 8.5}" font-size="2.0" text-anchor="middle">PIN 2</text>')

    # 28BYJ-48 MOTOR MOUNT (M4 holes, 8mm shaft offset)
    mcx, mcy = fx + 28.0, fy + 18.0
    screw_y = mcy + 8.0
    svg.append(f'<circle class="cut" cx="{mcx}" cy="{mcy}" r="5.0" />')
    svg.append(f'<circle class="cut" cx="{mcx - 17.5}" cy="{screw_y}" r="2.1" />')
    svg.append(f'<circle class="cut" cx="{mcx + 17.5}" cy="{screw_y}" r="2.1" />')
    svg.append(f'<text class="engrave" x="{mcx}" y="{screw_y + 8}" font-size="3" text-anchor="middle">28BYJ-48 MOTOR</text>')
    svg.append(f'<text class="engrave" x="{mcx}" y="{screw_y + 13}" font-size="2.4" text-anchor="middle">(M4 holes, 8mm offset)</text>')

    # USB-C Cutout
    usb_x = fx + 79.5
    usb_y = fy + H - 12.0
    svg.append(f'<rect class="cut" x="{usb_x}" y="{usb_y}" width="14.0" height="10.0" rx="2.0" />')
    svg.append(f'<text class="engrave" x="{usb_x + 7.0}" y="{usb_y - 4.0}" font-size="3.0" text-anchor="middle">USB-C POWER</text>')
    svg.append(f'<text class="engrave" x="{fx + 60.0}" y="{fy + H - 4.0}" font-size="3.2" text-anchor="middle">TOP FACE (MOTOR + USB)</text>')

    # 5. Bottom Face
    kx, ky = 145.0, 110.0
    pts_bot = [(kx, ky), (kx + W, ky)]
    for k in range(NH):
        y1 = ky + k * sH
        y2 = ky + (k + 1) * sH
        slot = (k % 2 == 0)
        x_val = kx + W - t if slot else kx + W
        pts_bot.extend([(x_val, y1), (x_val, y2)])
    pts_bot.append((kx + W, ky + H))
    pts_bot.append((kx + W, ky + H + t))
    for j in range(NW - 1, -1, -1):
        x1 = kx + (j + 1) * sW
        x2 = kx + j * sW
        tab = (j % 2 == 0)
        y_val = ky + H + t if tab else ky + H
        pts_bot.extend([(x1, y_val), (x2, y_val)])
    pts_bot.append((kx, ky + H))
    for k in range(NH - 1, -1, -1):
        y1 = ky + (k + 1) * sH
        y2 = ky + k * sH
        slot = (k % 2 == 0)
        x_val = kx + t if slot else kx
        pts_bot.extend([(x_val, y1), (x_val, y2)])
    pts_bot.append(pts_bot[0])
    d_bot = "M " + " L ".join([f"{p[0]:.2f} {p[1]:.2f}" for p in pts_bot]) + " Z"
    svg.append(f'<path class="cut" d="{d_bot}" />')

    # Link pin holes in Bottom Face
    svg.append(f'<rect class="cut" x="{kx + 8.0 - 2.75}" y="{ky + 2.0}" width="5.5" height="3.5" rx="0.3" />')
    svg.append(f'<rect class="cut" x="{kx + 102.0 - 2.75}" y="{ky + 2.0}" width="5.5" height="3.5" rx="0.3" />')
    svg.append(f'<text class="engrave" x="{kx + 8.0}" y="{ky + 8.5}" font-size="2.0" text-anchor="middle">PIN 1</text>')
    svg.append(f'<text class="engrave" x="{kx + 102.0}" y="{ky + 8.5}" font-size="2.0" text-anchor="middle">PIN 2</text>')
    svg.append(f'<text class="engrave" x="{kx + W/2}" y="{ky + 35}" font-size="4" text-anchor="middle">BOTTOM FACE (PIN SECURED)</text>')

    # 6. Right Wall (12mm Button)
    rx, ry = 275.0, 110.0
    pts_right = [(rx, ry), (rx + D_body, ry), (rx + D_body + t, ry)]
    for k in range(NH):
        y1 = ry + k * sH
        y2 = ry + (k + 1) * sH
        tab = (k % 2 == 0)
        x_val = rx + D_body + t if tab else rx + D_body
        pts_right.extend([(x_val, y1), (x_val, y2)])
    pts_right.append((rx + D_body - 14.0, ry + H))
    pts_right.append((rx + D_body - 14.0, ry + H + t))
    pts_right.append((rx + D_body - 32.0, ry + H + t))
    pts_right.append((rx + D_body - 32.0, ry + H))
    pts_right.append((rx + D_body - 42.0, ry + H))
    pts_right.append((rx + D_body - 42.0, ry + H + t))
    pts_right.append((rx + 14.0, ry + H + t))
    pts_right.append((rx + 14.0, ry + H))
    pts_right.append((rx, ry + H))
    for k in range(NH - 1, -1, -1):
        y1 = ry + (k + 1) * sH
        y2 = ry + k * sH
        tab = (k % 2 == 0)
        x_val = rx - t if tab else rx
        pts_right.extend([(x_val, y1), (x_val, y2)])
    pts_right.append(pts_right[0])
    d_right = "M " + " L ".join([f"{p[0]:.2f} {p[1]:.2f}" for p in pts_right]) + " Z"
    svg.append(f'<path class="cut" d="{d_right}" />')

    svg.append(f'<circle class="cut" cx="{rx + D_body/2}" cy="{ry + H/2 + 2}" r="6.1" />')
    svg.append(f'<text class="engrave" x="{rx + D_body/2}" y="{ry + 42}" font-size="3.5" text-anchor="middle">BUTTON (12mm)</text>')

    # --- ROW 3 (Y ≈ 185 to 281 mm) ---
    # 7. Internal Divider
    ix, iy = 15.0, 185.0
    div_h = 43.5
    p_div = [
        f"M {ix} {iy}",
        f"L {ix + D_body} {iy}",
        f"L {ix + D_body} {iy + div_h}",
        f"L {ix + 61.0} {iy + div_h}", f"L {ix + 61.0} {iy + div_h + t}", f"L {ix + 51.0} {iy + div_h + t}", f"L {ix + 51.0} {iy + div_h}",
        f"L {ix + 23.0} {iy + div_h}", f"L {ix + 23.0} {iy + div_h + t}", f"L {ix + 13.0} {iy + div_h + t}", f"L {ix + 13.0} {iy + div_h}",
        f"L {ix} {iy + div_h}",
        "Z"
    ]
    svg.append(f'<path class="cut" d="{" ".join(p_div)}" />')
    svg.append(f'<rect class="cut" x="{ix + D_body/2 - 11}" y="{iy + 8}" width="22.0" height="14.0" rx="2.0" />')
    svg.append(f'<text class="engrave" x="{ix + D_body/2}" y="{iy + 28}" font-size="3.0" text-anchor="middle">WIRE PASS-THROUGH</text>')
    svg.append(f'<text class="engrave" x="{ix + D_body/2}" y="{iy + 36}" font-size="3.2" text-anchor="middle">DIVIDER (8.5mm BACKSTOP FOR LID)</text>')

    # 8. 3x Link Pins
    for idx, pin_x in enumerate([115.0, 145.0, 175.0]):
        pin_y = 185.0
        p_pin = [
            f"M {pin_x} {pin_y}",
            f"L {pin_x + 11} {pin_y}",
            f"L {pin_x + 11} {pin_y + 7}",
            f"L {pin_x + 8} {pin_y + 7}",
            f"L {pin_x + 8} {pin_y + 94}",
            f"L {pin_x + 7} {pin_y + 96}",
            f"L {pin_x + 4} {pin_y + 96}",
            f"L {pin_x + 3} {pin_y + 94}",
            f"L {pin_x + 3} {pin_y + 7}",
            f"L {pin_x} {pin_y + 7}",
            "Z"
        ]
        svg.append(f'<path class="cut" d="{" ".join(p_pin)}" />')
        svg.append(f'<circle class="cut" cx="{pin_x + 5.5}" cy="{pin_y + 3.5}" r="1.5" />')
        label = f"PIN {idx+1}" if idx < 2 else "SPARE"
        svg.append(f'<text class="engrave" x="{pin_x + 5.5}" y="{pin_y - 2}" font-size="2.2" text-anchor="middle">{label}</text>')

    # 9. Laser-Cut Spool Kit (Row 3, X ≈ 215 to 335 mm)
    svg.append('<text class="engrave" x="270.0" y="190.0" font-size="3.2" font-weight="bold" text-anchor="middle">☀️ 28BYJ-48 SPOOL KIT (2x SPOOLS + WASHERS)</text>')

    # --- Spool 1 (Standard: 26mm Flange, 15mm Core) ---
    c1_bx, c1_by = 224.0, 208.0
    svg.append(f'<circle class="cut" cx="{c1_bx}" cy="{c1_by}" r="13.0" />')
    svg.append(f'<path class="cut" d="{d_hole_svg(c1_bx, c1_by, 2.5, 1.5)}" />')
    svg.append(f'<circle class="cut" cx="{c1_bx - 8.5}" cy="{c1_by}" r="1.1" />')
    svg.append(f'<circle class="cut" cx="{c1_bx + 8.5}" cy="{c1_by}" r="1.1" />')
    svg.append(f'<text class="engrave" x="{c1_bx}" y="{c1_by - 6.5}" font-size="2.0" text-anchor="middle">SPOOL 1 BACK</text>')

    c1_fx, c1_fy = 224.0, 242.0
    svg.append(f'<circle class="cut" cx="{c1_fx}" cy="{c1_fy}" r="13.0" />')
    svg.append(f'<circle class="cut" cx="{c1_fx}" cy="{c1_fy}" r="1.6" />')
    svg.append(f'<circle class="cut" cx="{c1_fx}" cy="{c1_fy + 8.5}" r="1.25" />')
    svg.append(f'<circle class="cut" cx="{c1_fx - 8.5}" cy="{c1_fy}" r="1.1" />')
    svg.append(f'<circle class="cut" cx="{c1_fx + 8.5}" cy="{c1_fy}" r="1.1" />')
    svg.append(f'<text class="engrave" x="{c1_fx}" y="{c1_fy - 6.5}" font-size="2.0" text-anchor="middle">SPOOL 1 FRONT</text>')

    w1_x, w1_y = 224.0, 267.0
    svg.append(f'<circle class="cut" cx="{w1_x}" cy="{w1_y}" r="4.5" />')
    svg.append(f'<circle class="cut" cx="{w1_x}" cy="{w1_y}" r="2.75" />')
    svg.append(f'<text class="engrave" x="{w1_x}" y="{w1_y + 1.0}" font-size="1.5" text-anchor="middle">WASH</text>')

    for idx, c_y in enumerate([203.0, 223.0, 243.0]):
        core_x = 252.0
        svg.append(f'<circle class="cut" cx="{core_x}" cy="{c_y}" r="7.5" />')
        svg.append(f'<path class="cut" d="{d_hole_svg(core_x, c_y, 2.5, 1.5)}" />')
        svg.append(f'<circle class="cut" cx="{core_x}" cy="{c_y + 4.8}" r="1.0" />')
        svg.append(f'<circle class="cut" cx="{core_x - 5.0}" cy="{c_y}" r="1.1" />')
        svg.append(f'<circle class="cut" cx="{core_x + 5.0}" cy="{c_y}" r="1.1" />')
        lbl = f"CORE {idx+1}" if idx < 2 else "SPARE"
        svg.append(f'<text class="engrave" x="{core_x}" y="{c_y - 4.5}" font-size="1.6" text-anchor="middle">{lbl}</text>')

    w2_x, w2_y = 252.0, 267.0
    svg.append(f'<circle class="cut" cx="{w2_x}" cy="{w2_y}" r="4.5" />')
    svg.append(f'<circle class="cut" cx="{w2_x}" cy="{w2_y}" r="2.75" />')
    svg.append(f'<text class="engrave" x="{w2_x}" y="{w2_y + 1.0}" font-size="1.5" text-anchor="middle">WASH</text>')

    # --- Spool 2 (Deep Rim: 28mm Flange, 14mm Core, Snug D-fit) ---
    c2_bx, c2_by = 282.0, 209.0
    svg.append(f'<circle class="cut" cx="{c2_bx}" cy="{c2_by}" r="14.0" />')
    svg.append(f'<path class="cut" d="{d_hole_svg(c2_bx, c2_by, 2.45, 1.45)}" />')
    svg.append(f'<circle class="cut" cx="{c2_bx - 9.5}" cy="{c2_by}" r="1.1" />')
    svg.append(f'<circle class="cut" cx="{c2_bx + 9.5}" cy="{c2_by}" r="1.1" />')
    svg.append(f'<text class="engrave" x="{c2_bx}" y="{c2_by - 7.0}" font-size="2.0" text-anchor="middle">SPOOL 2 BACK</text>')

    c2_fx, c2_fy = 282.0, 244.0
    svg.append(f'<circle class="cut" cx="{c2_fx}" cy="{c2_fy}" r="14.0" />')
    svg.append(f'<circle class="cut" cx="{c2_fx}" cy="{c2_fy}" r="1.6" />')
    svg.append(f'<circle class="cut" cx="{c2_fx}" cy="{c2_fy + 9.5}" r="1.25" />')
    svg.append(f'<circle class="cut" cx="{c2_fx - 9.5}" cy="{c2_fy}" r="1.1" />')
    svg.append(f'<circle class="cut" cx="{c2_fx + 9.5}" cy="{c2_fy}" r="1.1" />')
    svg.append(f'<text class="engrave" x="{c2_fx}" y="{c2_fy - 7.0}" font-size="2.0" text-anchor="middle">SPOOL 2 FRONT</text>')

    w3_x, w3_y = 282.0, 269.0
    svg.append(f'<circle class="cut" cx="{w3_x}" cy="{w3_y}" r="4.5" />')
    svg.append(f'<circle class="cut" cx="{w3_x}" cy="{w3_y}" r="2.75" />')
    svg.append(f'<text class="engrave" x="{w3_x}" y="{w3_y + 1.0}" font-size="1.5" text-anchor="middle">WASH</text>')

    for idx, c_y in enumerate([203.0, 223.0, 243.0]):
        core_x = 308.0
        svg.append(f'<circle class="cut" cx="{core_x}" cy="{c_y}" r="7.0" />')
        svg.append(f'<path class="cut" d="{d_hole_svg(core_x, c_y, 2.45, 1.45)}" />')
        svg.append(f'<circle class="cut" cx="{core_x}" cy="{c_y + 4.5}" r="1.0" />')
        svg.append(f'<circle class="cut" cx="{core_x - 4.8}" cy="{c_y}" r="1.1" />')
        svg.append(f'<circle class="cut" cx="{core_x + 4.8}" cy="{c_y}" r="1.1" />')
        lbl = f"CORE {idx+1}" if idx < 2 else "SPARE"
        svg.append(f'<text class="engrave" x="{core_x}" y="{c_y - 4.0}" font-size="1.6" text-anchor="middle">{lbl}</text>')

    w4_x, w4_y = 308.0, 269.0
    svg.append(f'<circle class="cut" cx="{w4_x}" cy="{w4_y}" r="4.5" />')
    svg.append(f'<circle class="cut" cx="{w4_x}" cy="{w4_y}" r="2.75" />')
    svg.append(f'<text class="engrave" x="{w4_x}" y="{w4_y + 1.0}" font-size="1.5" text-anchor="middle">WASH</text>')

    svg.append('</svg>')

    with open(output_svg_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(svg))
    print(f"Saved SVG to: {output_svg_path}")

    # =========================================================================
    # 2. GENERATE DXF
    # =========================================================================
    dxf = DxfWriter(output_dxf_path)

    # Base Plate
    dxf.polyline([
        (bx + ear, by), (bx + ear + W, by), (bx + 2*ear + W, by + 6),
        (bx + 2*ear + W, by + D_outer - 6), (bx + ear + W, by + D_outer),
        (bx + ear, by + D_outer), (bx, by + D_outer - 6), (bx, by + 6), (bx + ear, by)
    ])
    dxf.circle(left_x, top_y, 2.1)
    dxf.circle(left_x, bot_y, 2.1)
    dxf.circle(right_x, top_y, 2.1)
    dxf.circle(right_x, bot_y, 2.1)

    for i in [0, 2, 4, 6]:
        slot_x = bx + ear + i * sW
        dxf.rect(slot_x, by + D_outer - t, sW, t)
        dxf.rect(slot_x, by, sW, t)

    for y_slot in [32.0, 60.0]:
        dxf.rect(bx + ear, by + y_slot, t, 18.0)
        dxf.rect(bx + ear + W - t, by + y_slot, t, 18.0)

    dxf.circle(bx + ear + 10.0, by + 27.0, 1.5)
    dxf.circle(bx + ear + 40.0, by + 27.0, 1.5)
    dxf.circle(bx + ear + 10.0, by + 53.0, 1.5)
    dxf.circle(bx + ear + 40.0, by + 53.0, 1.5)
    dxf.text(bx + ear + 12.0, by + 41.0, 3.0, "ULN2003")

    dxf.rect(div_floor_x, by + 16.0, t, 10.0)
    dxf.rect(div_floor_x, by + 54.0, t, 10.0)
    dxf.text(bx + ear + 70.0, by + 41.0, 3.5, "ESP32 ZONE")
    dxf.text(bx + ear + 25.0, by + 10.0, 3.8, "BASE PLATE (4x CLOSET SCREWS)")

    # Front Plate
    dxf.rect(tx, ty, lid_w, lid_d)
    dxf.text(tx + 18, ty + 28, 6.0, "SMART CURTAIN")
    dxf.text(tx + 22, ty + 40, 3.8, "WAKE-UP AUTOMATION")
    dxf.text(tx + 14, ty + 51, 3.0, "ESP32 - 28BYJ-48 - NTP")

    # Left Wall
    dxf.polyline(pts_left)
    for v in range(-2, 3):
        vx = lx + D_body/2 + v * 8.0 - 1.5
        dxf.rect(vx, ly + 16.0, 3.0, 20.0)
    dxf.text(lx + D_body/2 - 15, ly + 42, 3.5, "LEFT (VENTS)")

    # Top Face
    dxf.polyline(pts_top)
    dxf.rect(fx + 8.0 - 2.75, fy + 2.0, 5.5, 3.5)
    dxf.rect(fx + 102.0 - 2.75, fy + 2.0, 5.5, 3.5)
    dxf.text(fx + 6.0, fy + 8.5, 2.0, "PIN 1")
    dxf.text(fx + 100.0, fy + 8.5, 2.0, "PIN 2")

    dxf.circle(mcx, mcy, 5.0)
    dxf.circle(mcx - 17.5, screw_y, 2.1)
    dxf.circle(mcx + 17.5, screw_y, 2.1)
    dxf.text(mcx - 18, screw_y + 8, 3.0, "28BYJ-48 (M4 holes)")

    dxf.rect(usb_x, usb_y, 14.0, 10.0)
    dxf.text(usb_x - 2, usb_y - 4, 3.0, "USB-C POWER")
    dxf.text(fx + 30, fy + H - 4, 3.2, "TOP FACE (MOTOR + USB)")

    # Bottom Face
    dxf.polyline(pts_bot)
    dxf.rect(kx + 8.0 - 2.75, ky + 2.0, 5.5, 3.5)
    dxf.rect(kx + 102.0 - 2.75, ky + 2.0, 5.5, 3.5)
    dxf.text(kx + 6.0, ky + 8.5, 2.0, "PIN 1")
    dxf.text(kx + 100.0, ky + 8.5, 2.0, "PIN 2")
    dxf.text(kx + 25, ky + 35, 4.0, "BOTTOM FACE (PIN SECURED)")

    # Right Wall
    dxf.polyline(pts_right)
    dxf.circle(rx + D_body/2, ry + H/2 + 2, 6.1)
    dxf.text(rx + D_body/2 - 15, ry + 42, 3.5, "BUTTON (12mm)")

    # Divider
    dxf.polyline([
        (ix, iy), (ix + D_body, iy), (ix + D_body, iy + div_h),
        (ix + 61.0, iy + div_h), (ix + 61.0, iy + div_h + t), (ix + 51.0, iy + div_h + t), (ix + 51.0, iy + div_h),
        (ix + 23.0, iy + div_h), (ix + 23.0, iy + div_h + t), (ix + 13.0, iy + div_h + t), (ix + 13.0, iy + div_h),
        (ix, iy + div_h), (ix, iy)
    ])
    dxf.rect(ix + D_body/2 - 11, iy + 8, 22.0, 14.0)
    dxf.text(ix + 6, iy + 36, 3.2, "DIVIDER (8.5mm BACKSTOP)")

    # Pins
    for idx, pin_x in enumerate([115.0, 145.0, 175.0]):
        pin_y = 185.0
        dxf.polyline([
            (pin_x, pin_y), (pin_x + 11, pin_y), (pin_x + 11, pin_y + 7),
            (pin_x + 8, pin_y + 7), (pin_x + 8, pin_y + 94),
            (pin_x + 7, pin_y + 96), (pin_x + 4, pin_y + 96),
            (pin_x + 3, pin_y + 94), (pin_x + 3, pin_y + 7),
            (pin_x, pin_y + 7), (pin_x, pin_y)
        ])
        dxf.circle(pin_x + 5.5, pin_y + 3.5, 1.5)
        lbl = f"PIN {idx+1}" if idx < 2 else "SPARE"
        dxf.text(pin_x, pin_y - 2, 2.2, lbl)

    # Spool Kit DXF
    dxf.text(230.0, 190.0, 3.0, "28BYJ-48 SPOOL KIT")

    # Spool 1 (26mm OD)
    dxf.circle(c1_bx, c1_by, 13.0)
    dxf.polyline(d_hole_dxf(c1_bx, c1_by, 2.5, 1.5))
    dxf.circle(c1_bx - 8.5, c1_by, 1.1)
    dxf.circle(c1_bx + 8.5, c1_by, 1.1)
    dxf.text(c1_bx - 10, c1_by - 6.5, 2.0, "S1 BACK")

    dxf.circle(c1_fx, c1_fy, 13.0)
    dxf.circle(c1_fx, c1_fy, 1.6)
    dxf.circle(c1_fx, c1_fy + 8.5, 1.25)
    dxf.circle(c1_fx - 8.5, c1_fy, 1.1)
    dxf.circle(c1_fx + 8.5, c1_fy, 1.1)
    dxf.text(c1_fx - 10, c1_fy - 6.5, 2.0, "S1 FRONT")

    dxf.circle(w1_x, w1_y, 4.5)
    dxf.circle(w1_x, w1_y, 2.75)

    for idx, c_y in enumerate([203.0, 223.0, 243.0]):
        core_x = 252.0
        dxf.circle(core_x, c_y, 7.5)
        dxf.polyline(d_hole_dxf(core_x, c_y, 2.5, 1.5))
        dxf.circle(core_x, c_y + 4.8, 1.0)
        dxf.circle(core_x - 5.0, c_y, 1.1)
        dxf.circle(core_x + 5.0, c_y, 1.1)
        lbl = f"C{idx+1}" if idx < 2 else "SP"
        dxf.text(core_x - 4, c_y - 4.5, 1.6, lbl)

    dxf.circle(w2_x, w2_y, 4.5)
    dxf.circle(w2_x, w2_y, 2.75)

    # Spool 2 (28mm OD)
    dxf.circle(c2_bx, c2_by, 14.0)
    dxf.polyline(d_hole_dxf(c2_bx, c2_by, 2.45, 1.45))
    dxf.circle(c2_bx - 9.5, c2_by, 1.1)
    dxf.circle(c2_bx + 9.5, c2_by, 1.1)
    dxf.text(c2_bx - 10, c2_by - 7.0, 2.0, "S2 BACK")

    dxf.circle(c2_fx, c2_fy, 14.0)
    dxf.circle(c2_fx, c2_fy, 1.6)
    dxf.circle(c2_fx, c2_fy + 9.5, 1.25)
    dxf.circle(c2_fx - 9.5, c2_fy, 1.1)
    dxf.circle(c2_fx + 9.5, c2_fy, 1.1)
    dxf.text(c2_fx - 10, c2_fy - 7.0, 2.0, "S2 FRONT")

    dxf.circle(w3_x, w3_y, 4.5)
    dxf.circle(w3_x, w3_y, 2.75)

    for idx, c_y in enumerate([203.0, 223.0, 243.0]):
        core_x = 308.0
        dxf.circle(core_x, c_y, 7.0)
        dxf.polyline(d_hole_dxf(core_x, c_y, 2.45, 1.45))
        dxf.circle(core_x, c_y + 4.5, 1.0)
        dxf.circle(core_x - 4.8, c_y, 1.1)
        dxf.circle(core_x + 4.8, c_y, 1.1)
        lbl = f"C{idx+1}" if idx < 2 else "SP"
        dxf.text(core_x - 4, c_y - 4.0, 1.6, lbl)

    dxf.circle(w4_x, w4_y, 4.5)
    dxf.circle(w4_x, w4_y, 2.75)

    dxf.save()
    print(f"Saved DXF to: {output_dxf_path}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    generate_case(
        os.path.join(base_dir, "curtain_case_3mm.svg"),
        os.path.join(base_dir, "curtain_case_3mm.dxf")
    )
