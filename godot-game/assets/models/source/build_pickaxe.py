"""Builds the base pickaxe and its skin previews.

Run from the repo root (Blender 3.6+):
    blender --background --factory-startup --python godot-game/assets/models/source/build_pickaxe.py -- [--render preview.png]

Writes:
    models/pickaxe.glb    the base pickaxe the game loads (one material per part)
    models/pickaxe.blend  the base plus one preview copy per skin
and, with --render, a picture of every skin side by side.

The base is about 1 m long, handle along +Z, with the origin at the bottom of
the handle. Each part has its own Pick_<Part> material; models/pickaxe-skins.json
says how each skin colours or hides those parts.
"""

import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

MODELS = os.path.dirname(os.path.abspath(__file__))   # godot-game/assets/models/source
SKINS_PATH = os.path.join(MODELS, "pickaxe-skins.json")
HEAD_Z = 0.88


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    render = argv[argv.index("--render") + 1] if "--render" in argv else None
    return render


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


def material(part):
    m = bpy.data.materials.new("Pick_" + part)
    m.use_nodes = True
    return m


def link(scene, name, bm, mat, smooth):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for poly in me.polygons:
        poly.use_smooth = smooth
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    return ob


def cylinder(scene, name, z0, z1, r0, r1, mat, segments=8, smooth=True):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segments, radius1=r0, radius2=r1,
                          depth=z1 - z0, matrix=Matrix.Translation((0, 0, (z0 + z1) / 2)))
    return link(scene, name, bm, mat, smooth)


def head(scene, mat):
    """A double pick: hexagonal cross-sections along an arc that droops to both tips."""
    bm = bmesh.new()
    radius, theta_max, steps = 0.62, math.radians(34), 14
    profile = [(1, 0), (0.45, 1), (-0.45, 1), (-1, 0), (-0.45, -1), (0.45, -1)]
    rings = []
    for i in range(steps + 1):
        t = -1 + 2 * i / steps
        theta = t * theta_max
        centre = Vector((radius * math.sin(theta), 0, HEAD_Z + radius * (math.cos(theta) - 1)))
        up = Vector((math.sin(theta), 0, math.cos(theta)))
        side = Vector((0, 1, 0))
        k = 1 - abs(t)
        height = 0.085 * k ** 0.65 + 0.004
        depth = 0.055 * k ** 0.55 + 0.004
        rings.append([bm.verts.new(centre + up * (a * height) + side * (b * depth)) for a, b in profile])
    for a, b in zip(rings, rings[1:]):
        for j in range(6):
            bm.faces.new((a[j], a[(j + 1) % 6], b[(j + 1) % 6], b[j]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return link(scene, "Head", bm, mat, smooth=False)


def build_base(scene):
    mats = {p: material(p) for p in ("Head", "Collar", "Rivets", "Handle", "Grip", "Bands", "Pommel")}
    parts = [
        cylinder(scene, "Handle", 0.0, 0.97, 0.034, 0.029, mats["Handle"]),
        head(scene, mats["Head"]),
    ]

    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1, matrix=Matrix.Translation((0, 0, HEAD_Z - 0.005))
                          @ Matrix.Diagonal((0.13, 0.11, 0.16, 1)))
    parts.append(link(scene, "Collar", bm, mats["Collar"], smooth=False))

    bm = bmesh.new()
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                bmesh.ops.create_uvsphere(bm, u_segments=6, v_segments=4, radius=0.014,
                                          matrix=Matrix.Translation((sx * 0.035, sy * 0.056,
                                                                     HEAD_Z - 0.005 + sz * 0.045)))
    parts.append(link(scene, "Rivets", bm, mats["Rivets"], smooth=True))

    parts.append(cylinder(scene, "Grip", 0.06, 0.36, 0.039, 0.037, mats["Grip"], smooth=False))
    parts.append(cylinder(scene, "BandLow", 0.05, 0.085, 0.042, 0.042, mats["Bands"]))
    parts.append(cylinder(scene, "BandHigh", 0.34, 0.375, 0.041, 0.041, mats["Bands"]))

    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=6, radius=0.045,
                              matrix=Matrix.Diagonal((1, 1, 0.75, 1)))
    parts.append(link(scene, "Pommel", bm, mats["Pommel"], smooth=True))

    root = bpy.data.objects.new("Pickaxe", None)
    scene.collection.objects.link(root)
    for ob in parts:
        ob.parent = root
    return root


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def set_bsdf(mat, spec):
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    h = spec["color"].lstrip("#")
    rgb = [srgb_to_linear(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4)]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Metallic"].default_value = spec["metalness"]
    bsdf.inputs["Roughness"].default_value = spec["roughness"]


def skinned_copy(scene, root, key, skin, x):
    """A copy of the base with its own materials, coloured and trimmed by one skin."""
    copy = bpy.data.objects.new("Preview_" + key, None)
    scene.collection.objects.link(copy)
    copy.location = (x, 0, 0)
    mats = {}
    for ob in root.children:
        part = ob.data.materials[0].name.replace("Pick_", "")
        spec = skin["parts"].get(part, {})
        if spec.get("visible", True) is False:
            continue
        if part not in mats:
            mats[part] = ob.data.materials[0].copy()
            mats[part].name = f"Pick_{part}_{key}"
            set_bsdf(mats[part], spec)
        c = ob.copy()
        c.data = ob.data.copy()
        c.data.materials[0] = mats[part]
        c.name = f"{ob.name}_{key}"
        scene.collection.objects.link(c)
        c.parent = copy
    return copy


def export_glb(root, path):
    bpy.ops.object.select_all(action="DESELECT")
    root.select_set(True)
    for ob in root.children:
        ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True)


def render_preview(scene, path, count):
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 48
    scene.cycles.device = "CPU"
    scene.render.resolution_x, scene.render.resolution_y = 1200, 640
    scene.render.film_transparent = False
    world = bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Color"].default_value = (0.03, 0.035, 0.05, 1)
    bg.inputs["Strength"].default_value = 1.0

    for name, rot, energy in (("Key", (50, 0, 35), 4.0), ("Rim", (60, 0, -150), 2.0)):
        light = bpy.data.objects.new(name, bpy.data.lights.new(name, "SUN"))
        light.data.energy = energy
        light.rotation_euler = [math.radians(a) for a in rot]
        scene.collection.objects.link(light)

    cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = count * 0.85 + 0.2
    centre_x = (count - 1) * 0.85 / 2
    cam.location = (centre_x + 1.6, -4.0, 1.9)
    direction = Vector((centre_x, 0, 0.5)) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    scene.collection.objects.link(cam)
    scene.camera = cam
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def main():
    render = args()
    scene = reset_scene()
    skins = {k: v for k, v in json.load(open(SKINS_PATH)).items() if not k.startswith("_")}

    root = build_base(scene)
    export_glb(root, os.path.join(MODELS, "pickaxe.glb"))

    for i, (key, skin) in enumerate(skins.items()):
        skinned_copy(scene, root, key, skin, i * 0.85)
    root.hide_render = True
    for ob in root.children:
        ob.hide_render = True
        ob.hide_set(True)
    root.location = (-1.0, 0, 0)

    if render:
        render_preview(scene, os.path.abspath(render), len(skins))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(MODELS, "pickaxe.blend"), compress=True)
    print("built", ", ".join(skins))


main()
