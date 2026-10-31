"""
Laser-Cut Enclosure Generator for ESP32 Smart Curtain Opener
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
"""

import os
from export_dxf import DxfWriter

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

    # 4 Wardrobe Screw Holes (4.2mm dia)
    left_x = bx + ear / 2.0
    right_x = bx + 2*ear + W - ear / 2.0
    top_y = by + 16.0
    bot_y = by + D_outer - 16.0
    svg.append(f'<circle class="cut" cx="{left_x}" cy="{top_y}" r="2.1" />')
    svg.append(f'<circle class="cut" cx="{left_x}" cy="{bot_y}" r="2.1" />')
    svg.append(f'<circle class="cut" cx="{right_x}" cy="{top_y}" r="2.1" />')
    svg.append(f'<circle class="cut" cx="{right_x}" cy="{bot_y}" r="2.1" />')

    # Base Mortises for Top & Bottom Walls
    for i in [0, 2, 4, 6]:
        sx = bx + ear + i * sW
        svg.append(f'<rect class="cut" x="{sx}" y="{by + D_outer - t}" width="{sW}" height="{t}" rx="0.1" />')
        svg.append(f'<rect class="cut" x="{sx}" y="{by}" width="{sW}" height="{t}" rx="0.1" />')

    # Base Mortises for Left & Right Walls (Inset Tabs: 18mm at y=32..50 and y=60..78)
    for mx in [bx + ear, bx + ear + W - t]:
        svg.append(f'<rect class="cut" x="{mx}" y="{by + t + 14.0}" width="{t}" height="18.0" rx="0.1" />')
        svg.append(f'<rect class="cut" x="{mx}" y="{by + t + 42.0}" width="{t}" height="18.0" rx="0.1" />')

    # ULN2003 Driver Board Mount (30mm x 26mm pitch, 3.0mm dia)
    uln_cx = bx + ear + 25.0
    uln_cy = by + D_outer / 2.0
    svg.append(f'<circle class="cut" cx="{uln_cx - 15}" cy="{uln_cy - 13}" r="1.5" />')
    svg.append(f'<circle class="cut" cx="{uln_cx + 15}" cy="{uln_cy - 13}" r="1.5" />')
    svg.append(f'<circle class="cut" cx="{uln_cx - 15}" cy="{uln_cy + 13}" r="1.5" />')
    svg.append(f'<circle class="cut" cx="{uln_cx + 15}" cy="{uln_cy + 13}" r="1.5" />')
    svg.append(f'<text class="engrave" x="{uln_cx}" y="{uln_cy + 1}" font-size="3" text-anchor="middle">ULN2003 MOUNT</text>')

    # Internal Divider mortise slots
    div_x = bx + ear + 52.0
    svg.append(f'<rect class="cut" x="{div_x}" y="{by + 16.0}" width="{t}" height="10.0" rx="0.1" />')
    svg.append(f'<rect class="cut" x="{div_x}" y="{by + D_outer - 26.0}" width="{t}" height="10.0" rx="0.1" />')
    svg.append(f'<text class="engrave" x="{bx + ear + 82}" y="{by + D_outer/2 + 1}" font-size="3.5" text-anchor="middle">ESP32 ZONE</text>')
    svg.append(f'<text class="engrave" x="{bx + ear + W/2}" y="{by + 10}" font-size="3.8" text-anchor="middle">BASE (4x CLOSET SCREWS)</text>')

    # 2. Front Plate / Removable Lid (103.5 x 73.5 mm)
    tx, ty = 180.0, 15.0
    lid_w = 103.5
    lid_h = 73.5
    svg.append(f'<rect class="cut" x="{tx}" y="{ty}" width="{lid_w}" height="{lid_h}" rx="1.0" />')
    svg.append(f'<text class="engrave" x="{tx + lid_w/2}" y="{ty + 28}" font-size="7.0" font-weight="bold" text-anchor="middle">☀️ SMART CURTAIN</text>')
    svg.append(f'<text class="engrave" x="{tx + lid_w/2}" y="{ty + 40}" font-size="3.8" text-anchor="middle">WAKE-UP AUTOMATION</text>')
    svg.append(f'<text class="engrave" x="{tx + lid_w/2}" y="{ty + 51}" font-size="3.0" text-anchor="middle">ESP32 • 28BYJ-48 • NTP CLOCK</text>')

    # 3. Left Wall (Vents, Inset Base Tabs)
    lx, ly = 305.0, 15.0
    pts_left = [(lx, ly), (lx + D_body, ly)]
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
        svg.append(f'<rect class="cut" x="{lx + D_body/2 + v*8 - 1.5}" y="{ly + 16}" width="3.0" height="20.0" rx="1.5" />')
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
    for i in range(NW - 1, -1, -1):
        x_right = fx + (i + 1) * sW
        x_left = fx + i * sW
        is_tab = (i % 2 == 0)
        y_val = fy + H + t if is_tab else fy + H
        if is_tab:
            pts_top.extend([(x_right, y_val), (x_left, y_val), (x_left, fy + H)])
        else:
            pts_top.extend([(x_right, y_val), (x_left, y_val), (x_left, fy + H + t)])
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
    for i in range(NW - 1, -1, -1):
        x_right = kx + (i + 1) * sW
        x_left = kx + i * sW
        is_tab = (i % 2 == 0)
        y_val = ky + H + t if is_tab else ky + H
        if is_tab:
            pts_bot.extend([(x_right, y_val), (x_left, y_val), (x_left, ky + H)])
        else:
            pts_bot.extend([(x_right, y_val), (x_left, y_val), (x_left, ky + H + t)])
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

    svg.append(f'<rect class="cut" x="{kx + 8.0 - 2.75}" y="{ky + 2.0}" width="5.5" height="3.5" rx="0.3" />')
    svg.append(f'<rect class="cut" x="{kx + 102.0 - 2.75}" y="{ky + 2.0}" width="5.5" height="3.5" rx="0.3" />')
    svg.append(f'<text class="engrave" x="{kx + 8.0}" y="{ky + 8.5}" font-size="2.0" text-anchor="middle">PIN 1</text>')
    svg.append(f'<text class="engrave" x="{kx + 102.0}" y="{ky + 8.5}" font-size="2.0" text-anchor="middle">PIN 2</text>')
    svg.append(f'<text class="engrave" x="{kx + W/2}" y="{ky + H - 10}" font-size="3.5" text-anchor="middle">BOTTOM FACE (PIN PASS-THROUGH)</text>')

    # 6. Right Wall (Button 12mm)
    rx, ry = 280.0, 110.0
    pts_right = [(rx, ry), (rx + D_body, ry)]
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
        sx = bx + ear + i * sW
        dxf.rect(sx, by + D_outer - t, sW, t)
        dxf.rect(sx, by, sW, t)

    for mx in [bx + ear, bx + ear + W - t]:
        dxf.rect(mx, by + t + 14.0, t, 18.0)
        dxf.rect(mx, by + t + 42.0, t, 18.0)

    dxf.circle(uln_cx - 15, uln_cy - 13, 1.5)
    dxf.circle(uln_cx + 15, uln_cy - 13, 1.5)
    dxf.circle(uln_cx - 15, uln_cy + 13, 1.5)
    dxf.circle(uln_cx + 15, uln_cy + 13, 1.5)
    dxf.text(uln_cx - 15, uln_cy + 1, 3.0, "ULN2003 MOUNT")

    dxf.rect(div_x, by + 16.0, t, 10.0)
    dxf.rect(div_x, by + D_outer - 26.0, t, 10.0)
    dxf.text(bx + ear + W/2 - 25, by + 10, 3.8, "BASE (4x CLOSET SCREWS)")

    # Front Plate
    dxf.rect(tx, ty, lid_w, lid_h)
    dxf.text(tx + 16, ty + 28, 7.0, "SMART CURTAIN")
    dxf.text(tx + 22, ty + 40, 3.8, "WAKE-UP AUTOMATION")
    dxf.text(tx + 14, ty + 51, 3.0, "ESP32 - 28BYJ-48 - NTP")

    # Left Wall
    dxf.polyline(pts_left)
    for v in range(-2, 3):
        dxf.rect(lx + D_body/2 + v*8 - 1.5, ly + 16, 3.0, 20.0)
    dxf.text(lx + D_body/2 - 12, ly + 42, 3.5, "LEFT (VENTS)")

    # Top Face
    dxf.polyline(pts_top)
    dxf.rect(fx + 8.0 - 2.75, fy + 2.0, 5.5, 3.5)
    dxf.rect(fx + 102.0 - 2.75, fy + 2.0, 5.5, 3.5)
    dxf.text(fx + 6, fy + 8.5, 2.0, "PIN 1")
    dxf.text(fx + 100, fy + 8.5, 2.0, "PIN 2")
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
    dxf.text(kx + 6, ky + 8.5, 2.0, "PIN 1")
    dxf.text(kx + 100, ky + 8.5, 2.0, "PIN 2")
    dxf.text(kx + 20, ky + H - 10, 3.5, "BOTTOM FACE (PIN PASS-THROUGH)")

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

    dxf.save()
    print(f"Saved DXF to: {output_dxf_path}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    generate_case(
        os.path.join(base_dir, "curtain_case_3mm.svg"),
        os.path.join(base_dir, "curtain_case_3mm.dxf")
    )
