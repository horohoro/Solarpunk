"""
DXF Generator for Curtain Opener Case (AutoCAD R12 ASCII DXF)
Compatible with Epilog Mini 24, CorelDraw, Illustrator, LightBurn, RDWorks
"""

class DxfWriter:
    def __init__(self, filepath):
        self.filepath = filepath
        self.entities = []

    def line(self, x1, y1, x2, y2, layer="CUT_RED"):
        self.entities.append(f"0\nLINE\n8\n{layer}\n10\n{x1:.3f}\n20\n{y1:.3f}\n30\n0.0\n11\n{x2:.3f}\n21\n{y2:.3f}\n31\n0.0")

    def polyline(self, pts, layer="CUT_RED"):
        for i in range(len(pts) - 1):
            self.line(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1], layer)

    def circle(self, cx, cy, r, layer="CUT_RED"):
        self.entities.append(f"0\nCIRCLE\n8\n{layer}\n10\n{cx:.3f}\n20\n{cy:.3f}\n30\n0.0\n40\n{r:.3f}")

    def rect(self, x, y, w, h, layer="CUT_RED"):
        pts = [(x, y), (x+w, y), (x+w, y+h), (x, y+h), (x, y)]
        self.polyline(pts, layer)

    def text(self, x, y, height, text_str, layer="ENGRAVE_BLACK"):
        self.entities.append(f"0\nTEXT\n8\n{layer}\n10\n{x:.3f}\n20\n{y:.3f}\n30\n0.0\n40\n{height:.3f}\n1\n{text_str}")

    def save(self):
        header = "0\nSECTION\n2\nHEADER\n0\nENDSEC\n0\nSECTION\n2\nTABLES\n0\nTABLE\n2\nLAYER\n70\n2\n"
        # Layer CUT_RED (color 1 = red)
        header += "0\nLAYER\n2\nCUT_RED\n70\n0\n62\n1\n6\nCONTINUOUS\n"
        # Layer ENGRAVE_BLACK (color 7 = white/black)
        header += "0\nLAYER\n2\nENGRAVE_BLACK\n70\n0\n62\n7\n6\nCONTINUOUS\n0\nENDTAB\n0\nENDSEC\n"
        entities_section = "0\nSECTION\n2\nENTITIES\n" + "\n".join(self.entities) + "\n0\nENDSEC\n0\nEOF\n"
        with open(self.filepath, 'w', encoding='utf-8') as f:
            f.write(header + entities_section)
