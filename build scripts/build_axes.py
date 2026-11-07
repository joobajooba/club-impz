"""Builds the ten game lumber axes, one per sprite in godot-game/sprites/items/tool_<id>_axe.png, as the axe
variant of build_pickaxes.py: same tiers, materials, metal finish, glow extras, animations and scale (K).

docs/blockbench_detailed_prompts.md section 3.5, Axe: handle (slight curve from 2 to 3 offset cubes), end_cap,
socket, blade (wide head with a stepped curved edge, 4 to 8 cubes), back_spike (higher tiers), binding.
The sprites show a single bit blade, a band at the socket and a round knob on the handle end.
Output: C:\\Users\\lucas\\blockbench_models\\tools\\<id>_axe.bbmodel (+ .png) and axes_showcase.bbmodel.
"""
import math, sys
import numpy as np
import build_pickaxes as bp
from build_pickaxes import Pick, TIERS, col, smooth

SPIKED = ("obsidian", "titanite", "dreadstone", "void", "stellarite")   # doc: back_spike on higher tiers


class Axe(Pick):
    def __init__(self, tid, cfg):
        super().__init__(tid, cfg)
        self.name = f"{tid}_axe"
        self.rng = np.random.default_rng(sum(map(ord, tid)) * 131)
        self.arc = (np.array([0.0, 0.0]), 1.0)          # unused by axes, kept for the shared painter

    def build(self):
        c = self.cfg
        stone = c.get("chunky", False)
        wood, head = c["wood"], c["head"]
        # handle: three offset cubes give it a slight curve; the grip zone (design y 2.3 to 6.8) stays plain
        self.box("handle", "handle_lower", wood, (-.75, 1, -.75), (.75, 6.25, .75), wood_part="shaft")
        self.box("handle", "handle_mid", wood, (-.5, 6, -.75), (1.0, 10.5, .75), wood_part="shaft")
        self.box("handle", "handle_upper", wood, (-.75, 10.25, -.75), (.75, 16.75, .75), wood_part="shaft")
        if c.get("bands"):
            self.box("handle", "end_cap", c["bands"], (-1, 0, -1), (1, 1.25, 1), band=True)
        else:   # the sprite's round knob
            self.box("handle", "end_knob", wood, (-1, 0, -1), (1, 1.25, 1), wood_part="end")
        if stone:
            self.bar("handle", "twig_stub", wood, (-.5, 8.5), (-1.4, 9.4), .5, .5, wood_part="stub")

        # head on the +x side
        zb = .75 if stone else .5           # blade half thickness
        if stone:
            self.box("details", "lashing_1", "rope", (-1.125, 12.25, -1.125), (1.125, 13.0, 1.125), rope=True)
            self.box("details", "lashing_2", "rope", (-1.125, 15.25, -1.125), (1.125, 16.0, 1.125), rope=True)
            self.bar("details", "lashing_cross", "rope", (-.9, 12.4), (1.9, 15.9), .5, 2.5, rope=True)
        else:
            self.box("details", "socket", c["collar"], (-1.25, 12.25, -1.25), (1.25, 16.0, 1.25), socket=True)
            if c.get("rivets"):
                for k, y in enumerate((13.0, 15.25), 1):
                    self.box("details", f"rivet_{k}", c["rivets"], (-.25, y - .25, -1.5), (.25, y + .25, 1.5),
                             share="rivet", rivet=True)
        # blade: slices that grow taller and thinner toward the edge, so the outline flares like the sprite's
        self.box("head", "blade_neck", head, (1.0, 12.75, -zb - .25), (2.75, 15.25, zb + .25), blade=True)
        slices = ((2.5, 3.75, 12.25, 15.75, 0), (3.5, 4.75, 11.5, 16.5, .0625), (4.5, 5.75, 10.75, 17.25, .125))
        for k, (x0, x1, y0, y1, thin) in enumerate(slices, 1):
            self.box("head", f"blade_slice_{k}", head, (x0, y0, -zb + thin), (x1, y1, zb - thin), blade=True)
        # the stepped, curved cutting edge: tallest in the middle, tips swept out at the top and bottom
        e = .25 if not stone else .5
        self.box("head", "edge_mid", head, (5.5, 10.5, -e), (6.75, 17.5, e), blade=True, edge_bit=True)
        self.box("head", "edge_front", head, (6.5, 11.75, -e + .0625), (7.25, 16.25, e - .0625), blade=True, edge_bit=True)
        self.box("head", "edge_top", head, (5.0, 17.0, -e), (6.75, 18.25, e), rot=(0, 0, 20), origin=(5.75, 17.25, 0),
                 blade=True, edge_bit=True)
        self.box("head", "edge_bottom", head, (5.0, 9.75, -e), (6.75, 11.0, e), rot=(0, 0, -20), origin=(5.75, 10.75, 0),
                 blade=True, edge_bit=True)
        # back: a flat poll on the lower tiers, a spike on the higher ones
        if self.id in SPIKED:
            self.bar("head", "back_spike_1", head, (-1.0, 14.4), (-3.0, 14.0), 1.5, 1.0, over=.25, blade=True)
            self.bar("head", "back_spike_2", head, (-2.9, 14.0), (-4.4, 13.3), .75, .5, blade=True)
        elif not stone:
            self.box("head", "back_poll", head, (-2.25, 13.25, -.875), (-1.0, 15.5, .875), blade=True)
        self.box("details", "cap_pin", wood, (-.625, 16.0 if not stone else 16.0, -.625), (.625, 17.25, .625), wood_part="cap")
        # emblem on the blade face (animated on void and stellarite)
        if "emblem" in c and not stone:
            em_r, em = c["emblem"]
            gl = em_r.endswith("glow")
            self.box("emblem" if c.get("anim") else "details", "emblem_glow" if gl else "emblem", em_r,
                     (3.875, 13.5, -zb - .25), (5.125, 14.75, zb + .25), emblem=em)
        if c.get("shard"):
            self.box("shard", "shard_glow", "void_glow", (-.375, 18.25, -.375), (.375, 19.5, .375), rot=(0, 45, 0),
                     origin=(0, 18.9, 0))
        if c.get("sparkles"):
            for k, (x, y) in enumerate(((7.4, 18.2), (7.4, 9.9), (0.0, 18.6)), 1):
                self.box(f"sparkle_{k}", f"sparkle_{k}_v_glow", "star_glow", (x - .125, y - .875, -.125), (x + .125, y + .875, .125),
                         share="spark_v", sparkle=True)
                self.box(f"sparkle_{k}", f"sparkle_{k}_h_glow", "star_glow", (x - .875, y - .125, -.0625), (x + .875, y + .125, .0625),
                         share="spark_h", sparkle=True)
        glow = c.get("cracks") or c.get("core") or c.get("edges")
        if glow:
            kind = "crack" if c.get("cracks") else ("core" if c.get("core") else "edge")
            for body in [k for k in self.cubes if k["name"].startswith("blade_slice")]:
                n = body["name"][-1]
                for zsign, fname in ((1, "south"), (-1, "north")):
                    z = zsign * (body["t"][2] + .05)
                    self.box("details", f"{kind}_{n}_{'front' if zsign < 0 else 'back'}_glow", glow,
                             (body["f"][0], body["f"][1], z), (body["t"][0], body["t"][1], z), origin=body["o"], scaled=True,
                             panel=kind, panel_face=fname, parent=body)
        return self

    def paint_panel(self, c, W, h, w):
        X, Y = W[..., 0], W[..., 1]
        kind = c["panel"]
        if kind == "crack":           # a forked crack across the blade
            path = 14.1 + .45 * np.sin(X * 2.6) + .25 * np.sin(X * 6.1)
            m = np.abs(Y - path) < .2
            fork = 14.1 - (X - 4.4) * 1.1 + .2 * np.sin(X * 7)
            m |= (np.abs(Y - fork) < .17) & (X > 4.4) & (X < 5.6)
            v = 4.6 - 6 * np.minimum(np.abs(Y - path), np.abs(Y - fork))
        elif kind == "core":          # a glowing line just inside the cutting edge
            m = np.abs(X - 5.2) < .2
            v = 4.4 - np.abs(X - 5.2) * 8
        else:                         # a glowing band along the edge
            m = X > 5.25
            v = 3.2 + (X - 5.25) * 3
        a = np.where(m, 255, 0).astype(np.uint8)
        return self.rgba(col(c["mat"], v), a)


if __name__ == "__main__":
    only = sys.argv[1:]
    paths = []
    for tid, cfg in TIERS.items():
        if only and tid not in only: continue
        r = Axe(tid, cfg).build().write()
        paths.append(r.pop("path"))
        print(r)
    if not only:
        print("showcase", bp.showcase(paths, "axes_showcase"))
