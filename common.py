# --------------------------------------------------------------------------
# BlenderAndMBDyn
# Copyright (C) 2015 G. Douglas Baldwin - http://www.baldwintechnology.com
# --------------------------------------------------------------------------
# ***** BEGIN GPL LICENSE BLOCK *****
#
#    This file is part of BlenderAndMBDyn.
#
#    BlenderAndMBDyn is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    BlenderAndMBDyn is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with BlenderAndMBDyn.  If not, see <http://www.gnu.org/licenses/>.
#
# ***** END GPL LICENCE BLOCK *****
# -------------------------------------------------------------------------- 

if "bpy" in locals():
    import imp
    imp.reload(bpy)
    imp.reload(sqrt)
    imp.reload(bmesh)
else:
    import bpy
    from math import sqrt
    import bmesh

FORMAT = "{:.6g}".format

aerodynamic_types = [
    ("Aerodynamic body", 1),
    ("Aerodynamic beam2", 2),
    "Aerodynamic beam3",
    "Generic aerodynamic force",
    "Induced velocity"]
beam_types = [
    ("Beam segment", 2),
    "Three node beam"]
force_types = [
    "Abstract force",
    ("Structural force", 1),
    ("Structural internal force", 2),
    ("Structural couple", 1),
    ("Structural internal couple", 2)]
genel_types = [
    "Swashplate"]
joint_types = [
    ("Axial rotation", 2),
    ("Clamp", 1),
    ("Distance", 2),
    ("Deformable displacement joint", 2),
    ("Deformable hinge", 2),
    ("Deformable joint", 2),
    ("Inline", 2),
    ("Inplane", 2),
    ("Revolute hinge", 2),
    ("Rod", 2),
    ("Spherical hinge", 2),
    ("Total joint", 2),
    ("Viscous body", 1)]
environment_types = [
    "Air properties",
    "Gravity"]
node_types = [
    ("Rigid offset", 2),
    ("Dummy node", 2),
    "Feedback node"]

rigid_body_types = ["Body"]

structural_static_types = aerodynamic_types + joint_types + ["Rotor"] + beam_types + force_types

structural_dynamic_types = rigid_body_types

method_types = [
    "Crank Nicolson",
    "ms",
    "Hope",
    "Third order",
    "bdf",
    "Implicit Euler"]

nonlinear_solver_types = [
    "Newton Raphston",
    "Line search",
    "Matrix free"]

class Common:
    def write_vector(self, v, f, end=""):
        f.write(", ".join([FORMAT(round(x, 6) if round(x, 6) != -0. else 0) for x in v]) + end)
    def write_matrix(self, m, f, pad=""):
        f.write(",\n".join([pad + ", ".join(FORMAT(round(x, 6) if round(x, 6) != -0. else 0) for x in r) for r in m]))

def subsurf(obj):
    subsurf = [m for m in obj.modifiers if m.type == 'SUBSURF']
    subsurf = subsurf[0] if subsurf else obj.modifiers.new("Subsurf", 'SUBSURF')
    subsurf.levels = 3

def Ellipsoid(obj, mass, mat):
    if mat.subtype == "eye":
        diag = [1.]*3
    else:
        diag = [mat.floats[4*i] for i in range(3)]
    s = mat.factor if mat.scale else 1.0
    s = [0.5*sqrt(x*s/mass) for x in diag]
    bm = bmesh.new()
    for v in [(x*s[0],y*s[1],z*s[2]) for z in [-1., 1.] for y in [-1., 1.] for x in [-1., 1.]]:
        bm.verts.new(v)
    if hasattr(bm.verts, "ensure_lookup_table"):
        bm.verts.ensure_lookup_table()
    for f in [(1,0,2,3),(4,5,7,6),(0,1,5,4),(1,3,7,5),(3,2,6,7),(2,0,4,6)]:
        bm.faces.new([bm.verts[i] for i in f])
    crease = bm.edges.layers.crease.new()
    for e in bm.edges:
        e[crease] = 0.184
    bm.to_mesh(obj.data)
    subsurf(obj)
    bm.free()

def Sphere(obj):
    bm = bmesh.new()
    for v in [(x, y, z) for z in [-0.5, 0.5] for y in [-0.5, 0.5] for x in [-0.5, 0.5]]:
        bm.verts.new(v)
    if hasattr(bm.verts, "ensure_lookup_table"):
        bm.verts.ensure_lookup_table()
    for f in [(1,0,2,3),(4,5,7,6),(0,1,5,4),(1,3,7,5),(3,2,6,7),(2,0,4,6)]:
        bm.faces.new([bm.verts[i] for i in f])
    bm.to_mesh(obj.data)
    subsurf(obj)
    bm.free()

def RhombicPyramid(obj):
    bm = bmesh.new()
    for v in [(.333,0.,0.),(0.,.666,0.),(-.333,0.,0.),(0.,-.666,0.),(0.,0.,1.)]:
        bm.verts.new(v)
    if hasattr(bm.verts, "ensure_lookup_table"):
        bm.verts.ensure_lookup_table()
    for f in [(3,2,1,0),(0,1,4),(1,2,4),(2,3,4),(3,0,4)]:
        bm.faces.new([bm.verts[i] for i in f])
    crease = bm.edges.layers.crease.new()
    for e in bm.edges:
        e[crease] = 1.0
    bm.to_mesh(obj.data)
    subsurf(obj)
    bm.free()

def Teardrop(obj):
    bm = bmesh.new()
    for v in [(x, y, -.5) for y in [-.5, .5] for x in [-.5, .5]] + [(0.,0.,0.)]:
        bm.verts.new(v)
    if hasattr(bm.verts, "ensure_lookup_table"):
        bm.verts.ensure_lookup_table()
    for q in [(2,3,1,0),(0,1,4),(1,3,4),(3,2,4),(2,0,4)]:
        bm.faces.new([bm.verts[i] for i in q])
    crease = bm.edges.layers.crease.new()
    for i in range(4,8):
        bm.edges[i][crease] = 1.0
    bm.to_mesh(obj.data)
    bm.free()
    subsurf(obj)

def Cylinder(obj):
    bm = bmesh.new()
    scale = .5
    for z in [-1., 1.]:
        for y in [-1., 1.]:
            for x in [-1., 1.]:
                bm.verts.new((scale*x,scale*y,scale*z))
    if hasattr(bm.verts, "ensure_lookup_table"):
        bm.verts.ensure_lookup_table()
    for q in [(1,0,2,3),(4,5,7,6),(0,1,5,4),(1,3,7,5),(3,2,6,7),(2,0,4,6)]:
        bm.faces.new([bm.verts[i] for i in q])
    crease = bm.edges.layers.crease.new()
    for v0, v1 in ([(0,1),(0,2),(2,3),(3,1),(4,5),(4,6),(6,7),(7,5)]):
        bm.edges.get((bm.verts[v0], bm.verts[v1]))[crease] = 1.0
    bm.to_mesh(obj.data)
    bm.free()
    subsurf(obj)

def RectangularCuboid(obj):
    bm = bmesh.new()
    for v in [(x, y, z) for z in [-0.2, 0.2] for y in [-0.1, 0.1] for x in [-0.3, 0.3]]:
        bm.verts.new(v)
    if hasattr(bm.verts, "ensure_lookup_table"):
        bm.verts.ensure_lookup_table()
    for f in [(1,0,2,3),(4,5,7,6),(0,1,5,4),(1,3,7,5),(3,2,6,7),(2,0,4,6)]:
        bm.faces.new([bm.verts[i] for i in f])
    crease = bm.edges.layers.crease.new()
    for e in bm.edges:
        e[crease] = 1.0
    bm.to_mesh(obj.data)
    subsurf(obj)
    bm.free()
