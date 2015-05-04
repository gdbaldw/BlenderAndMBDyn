if "bpy" in locals():
    import imp
    imp.reload(bpy)
    imp.reload(sqrt)
    imp.reload(bmesh)
else:
    import bpy
    from math import sqrt
    import bmesh

aerodynamic_types = [
    "Aerodynamic body",
    "Aerodynamic beam2",
    "Aerodynamic beam3",
    "Generic aerodynamic force"]
beam_types = [
    "Beam segment",
    "Three node beam"]
force_types = [
    "Abstract force",
    "Structural force",
    "Structural internal force",
    "Structural couple",
    "Structural internal couple"]
genel_types = [
    "Swashplate"]
joint_types = [
    "Axial rotation",
    "Clamp",
    "Distance",
    "Deformable displacement joint",
    "Deformable hinge",
    "Deformable joint",
    "In line",
    "In plane",
    "Revolute hinge",
    "Rod",
    "Spherical hinge",
    "Total joint",
    "Viscous body"]
environment_types = [
    "Air properties",
    "Gravity"]
node_types = [
    "Rigid offset",
    "Dummy node",
    "Feedback node"]

rigid_body_types = ["Body"]

structural_static_types = aerodynamic_types + joint_types + ["Rotor"] + beam_types + force_types

structural_dynamic_types = rigid_body_types

class Common:
    def round_vector(self, v):
        for i in range(3):
            v[i] = round(v[i], 5)
        return v
    def round_matrix(self, r):
        for i in range(3):
            r[i] = self.round_vector(r[i])
        return r
    def locationVector_write(self, v, text, end=''):
        v = self.round_vector(v)
        text.write(str(v[0])+', '+str(v[1])+', '+str(v[2])+end)
    def rotationMatrix_write(self, rot, text, pad):
        rot = self.round_matrix(rot)
        text.write(
        pad+', '.join([str(rot[0][j]) for j in range(3)])+',\n'+
        pad+', '.join([str(rot[1][j]) for j in range(3)])+',\n'+
        pad+', '.join([str(rot[2][j]) for j in range(3)]))
    def write_node(self, text, i, node=False, position=False, orientation=False, p_label='', o_label=''):
        rot_i, globalV_i, Node_i = self.rigid_offset(i)
        localV_i = rot_i*globalV_i
        rotT = self.objects[i].matrix_world.to_quaternion().to_matrix().transposed()
        if node:
            text.write('\t\t'+str(Node_i)+',\n')
        if position:
            text.write('\t\t\t')
            if p_label:
                text.write(p_label+', ')
            self.locationVector_write(localV_i, text)
        if orientation:
            text.write(',\n\t\t\t')
            if o_label:
                text.write(o_label+', ')
            text.write('matr,\n')
            self.rotationMatrix_write(rot_i*rotT, text, '\t\t\t\t')
    def rigid_offset(self, i):
        if self.objects[i] in self.database.node:
            ob = self.objects[i]
        elif self.objects[i] in self.database.rigid_dict:
            ob = self.database.rigid_dict[self.objects[i]]
        else:
            bpy.context.window_manager.popup_menu(lambda self, c: self.layout.label(
                "Object "+self.objects[i].name+" is not associated with a Node"),
                title="MBDyn Error", icon='ERROR')
            print("***Model Error: Object "+self.objects[i].name+" is not associated with a Node")
            return
        rot = ob.matrix_world.to_quaternion().to_matrix()
        globalV = self.objects[i].matrix_world.translation - ob.matrix_world.translation
        return rot, globalV, self.database.node.index(ob)

def subsurf(obj):
    if not [m for m in obj.modifiers if m.type == 'SUBSURF']:
        obj.modifiers.new("Subsurf", 'SUBSURF')
        obj.modifiers["Subsurf"].levels = 3

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
    for f in [(1,0,2,3),(4,5,7,6),(0,1,5,4),(1,3,7,5),(3,2,6,7),(2,0,4,6)]:
        bm.faces.new([bm.verts[i] for i in f])
    crease = bm.edges.layers.crease.new()
    for e in bm.edges:
        e[crease] = 0.184
    bm.to_mesh(obj.data)
    subsurf(obj)
    bm.free()

def RhombicPyramid(obj):
    bm = bmesh.new()
    for v in [(.333,0.,0.),(0.,.666,0.),(-.333,0.,0.),(0.,-.666,0.),(0.,0.,1.)]:
        bm.verts.new(v)
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
    for q in [(2,3,1,0),(0,1,4),(1,3,4),(3,2,4),(2,0,4)]:
        bm.faces.new([bm.verts[i] for i in q])
    crease = bm.edges.layers.crease.new()
    for i in range(4,8):
        bm.edges[i][crease] = 1.0
    bm.to_mesh(obj.data)
    bm.free()
    subsurf(obj)

