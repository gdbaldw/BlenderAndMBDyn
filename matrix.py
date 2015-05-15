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
    imp.reload(Operator)
    imp.reload(Entity)
else:
    from .base import bpy, database, Operator, Entity, Bundle, Props

types = ["3x1", "6x1", "3x3", "6x6", "6xN"]

tree = ["Add Matrix", types]

class Base(Operator):
    bl_label = "Matrices"
    bl_options = {'DEFAULT_CLOSED'}
    @classmethod
    def make_list(self, ListItem):
        bpy.types.Scene.matrix_uilist = bpy.props.CollectionProperty(type = ListItem)
        bpy.types.Scene.matrix_index = bpy.props.IntProperty(default=-1)
    @classmethod
    def delete_list(self):
        del bpy.types.Scene.matrix_uilist
        del bpy.types.Scene.matrix_index
    @classmethod
    def get_uilist(self, context):
        return context.scene.matrix_index, context.scene.matrix_uilist
    def set_index(self, context, value):
        context.scene.matrix_index = value

klasses = dict()

for t in types:
    class DefaultOperator(Base):
        bl_label = t
        def defaults(self, context):
            pass
        def assign(self, context):
            self.entity = database.matrix[context.scene.matrix_index]
        def store(self, context):
            self.entity = database.matrix[context.scene.matrix_index]
        def create_entity(self):
            return Entity(self.name)
    klasses[t] = DefaultOperator

class MatrixBase(Base):
    N = None
    subtype = None
    floats = bpy.props.CollectionProperty(type = Props.Floats)
    scale = bpy.props.BoolProperty(name="Scale", description="Scale the vector")
    factor = bpy.props.FloatProperty(name="Factor", description="Scale factor", default=1.0, min=-9.9e10, max=9.9e10, precision=6)
    def defaults(self, context):
        self.floats.clear()
        for i in range(self.N):
            self.floats.add()
        self.entity_name = ""
    def assign(self, context):
        self.index = context.scene.matrix_index
        self.entity = database.matrix[self.index]
        self.entity_name = database.matrix[self.index].name
        self.subtype = self.entity.subtype
        self.floats.clear()
        for i in range(self.N):
            self.floats.add()
        for i, value in enumerate(self.entity.floats):
            self.floats[i].value = value
        self.scale = self.entity.scale
        self.factor = self.entity.factor
    def store(self, context):
        self.entity = database.matrix[self.index]
        self.entity.subtype = self.subtype
        self.entity.floats = [f.value for f in self.floats]
        self.entity.scale = self.scale
        self.entity.factor = self.factor
    def draw(self, context):
        self.basis = [self.subtype, self.scale]
        layout = self.layout
        layout.label(self.entity_name)
        layout.prop(self, "subtype")
        if self.subtype == "matr":
            row = layout.row()
            rowrow = row.row()
            rowrow.enabled = self.scale
            rowrow.prop(self, "factor")
            row.prop(self, "scale")
            for i in range(self.N):
                layout.prop(self.floats[i], "value", text="x"+str(i+1))
    def check(self, context):
        return [None for a, b in zip(self.basis, [self.subtype, self.scale]) if a != b]

class Matrix3x1(Entity):
    def string(self):
        if self.subtype == "null":
            ret = "\n\t\t\tnull"
        elif self.subtype == "default":
            ret = "\n\t\t\tdefault"
        else:
            ret = "\n\t\t\t"+str(self.floats).strip("[]")
            if self.scale:
                ret += ", scale, "+str(self.factor)
        return ret

class Matrix3x1Operator(MatrixBase):
    N = 3
    bl_label = "3x1"
    subtype = bpy.props.EnumProperty(items=[
        ("matr", "General", ""),
        ("null", "Null", ""),
        ("default", "Default", "")],
        name="Subtype")
    def draw(self, context):
        self.basis = [self.subtype, self.scale]
        layout = self.layout
        layout.label(self.entity_name)
        layout.prop(self, "subtype")
        if self.subtype not in "null default".split():
            row = layout.row()
            rowrow = row.row()
            rowrow.enabled = self.scale
            rowrow.prop(self, "factor")
            row.prop(self, "scale")
            for i in range(self.N):
                layout.prop(self.floats[i], "value", text="x"+str(i+1))
    def create_entity(self):
        return Matrix3x1(self.name)

klasses[Matrix3x1Operator.bl_label] = Matrix3x1Operator

class Matrix6x1(Matrix3x1):
    pass

class Matrix6x1Operator(Matrix3x1Operator):
    N = 6
    bl_label = "6x1"
    def create_entity(self):
        return Matrix6x1(self.name)

klasses[Matrix6x1Operator.bl_label] = Matrix6x1Operator

class Matrix3x3(Entity):
    def string(self):
        if self.subtype == "matr":
            ret = ("\n\t\t\tmatr,\n"+
            "\t"*4+str(self.floats[0:3]).strip("[]")+",\n"+
            "\t"*4+str(self.floats[3:6]).strip("[]")+",\n"+
            "\t"*4+str(self.floats[6:9]).strip("[]"))
        elif self.subtype == "sym":
            ret = ("\n\t\t\tsym,\n"+
            "\t"*4+str(self.floats[0:3]).strip("[]")+",\n"+
            "\t"*5+str(self.floats[4:6]).strip("[]")+",\n"+
            "\t"*6+str(self.floats[8]))
        elif self.subtype == "skew":
            ret = "\n\t\t\tskew, "+str([self.floats[i] for i in [7, 2, 3]]).strip("[]")
        elif self.subtype == "diag":
            ret = "\n\t\t\tdiag, "+str([self.floats[i] for i in [0, 4, 8]]).strip("[]")
        elif self.subtype == "eye":
            ret = "\n\t\t\teye"
        elif self.subtype == "null":
            ret = "\n\t\t\tnull"
        if self.scale:
            ret += ", scale, " + str(self.factor)
        return ret

class Matrix3x3Operator(MatrixBase):
    N = 9
    bl_label = "3x3"
    subtype = bpy.props.EnumProperty(items=[
        ("matr", "General", "General matrix"),
        ("null", "Null", "Null matrix"),
        ("sym", "Symmetric", "Symmetrix matrix"),
        ("skew", "Skew symmetric", "Skew symmetric matrix"),
        ("diag", "Diagonal", "Diagonal matrix"),
        ("eye", "Identity", "Identity matrix"),
        ], name="Subtype", default="eye")
    def draw(self, context):
        self.basis = [self.subtype, self.scale]
        layout = self.layout
        layout.label(self.entity_name)
        layout.prop(self, "subtype")
        if self.subtype != "null":
            row = layout.row()
            rowrow = row.row()
            rowrow.enabled = self.scale
            rowrow.prop(self, "factor")
            row.prop(self, "scale")
            if self.subtype != "eye":
                for i in range(3):
                    row = layout.row()
                    for j in range(3):
                        k = 3*i+j
                        if ((self.subtype == "sym" and k in [3,6,7])
                        or (self.subtype == "skew" and k not in [2,3,7])
                        or (self.subtype == "diag" and k not in [0,4,8])):
                            row.label("")
                        else:
                            row.prop(self.floats[k], "value", text="x"+str(k+1))
    def create_entity(self):
        return Matrix3x3(self.name)

klasses[Matrix3x3Operator.bl_label] = Matrix3x3Operator

class Matrix6x6(Entity):
    def string(self):
        if self.subtype == "matr":
            ret = ("\n\t\t\tmatr,\n"+
            "\t"*4+str(self.floats[0:6]).strip("[]")+",\n"+
            "\t"*4+str(self.floats[6:12]).strip("[]")+",\n"+
            "\t"*4+str(self.floats[12:18]).strip("[]")+",\n"+
            "\t"*4+str(self.floats[18:24]).strip("[]")+",\n"+
            "\t"*4+str(self.floats[24:30]).strip("[]")+",\n"+
            "\t"*4+str(self.floats[30:36]).strip("[]"))
        elif self.subtype == "sym":
            ret = ("\n\t\t\tsym,\n"+
            "\t"*4+str(self.floats[0:6]).strip("[]")+",\n"+
            "\t"*5+str(self.floats[7:12]).strip("[]")+",\n"+
            "\t"*6+str(self.floats[14:18]).strip("[]")+",\n"+
            "\t"*7+str(self.floats[21:24]).strip("[]")+",\n"+
            "\t"*8+str(self.floats[28:30]).strip("[]")+",\n"+
            "\t"*9+str(self.floats[35]))
        elif self.subtype == "diag":
            ret = "\n\t\t\tdiag, "+str([self.floats[i] for i in [0,7,14,21,28,35]]).strip("[]")
        elif self.subtype == "eye":
            ret = "\n\t\t\teye"
        elif self.subtype == "null":
            ret = "\n\t\t\tnull"
        if self.scale:
            ret += ", scale, "+str(self.factor)
        return ret

class Matrix6x6Operator(MatrixBase):
    N = 36
    bl_label = "6x6"
    subtype = bpy.props.EnumProperty(items=[
        ("matr", "General", "General matrix"),
        ("null", "Null", "Null matrix"),
        ("sym", "Symmetric", "Symmetrix matrix"),
        ("diag", "Diagonal", "Diagonal matrix"),
        ("eye", "Identity", "Identity matrix"),
        ], name="Subtype", default="eye")
    @classmethod
    def poll(cls, context):
        return True
    def draw(self, context):
        self.basis = [self.subtype, self.scale]
        layout = self.layout
        layout.label(self.entity_name)
        layout.prop(self, "subtype")
        if self.subtype != "null":
            row = layout.row()
            rowrow = row.row()
            rowrow.enabled = self.scale
            rowrow.prop(self, "factor")
            row.prop(self, "scale")
            if self.subtype != "eye":
                for i in range(6):
                    row = layout.row()
                    for j in range(6):
                        k = 6*i+j
                        if ((self.subtype == "sym" and k in [6,12,13,18,19,20,24,25,26,27,30,31,32,33,34])
                        or (self.subtype == "diag" and k not in [0,7,14,21,28,35])):
                            row.label("")
                        else:
                            row.prop(self.floats[k], "value", text="x"+str(k+1))
    def create_entity(self):
        return Matrix6x6(self.name)

klasses[Matrix6x6Operator.bl_label] = Matrix6x6Operator

class Matrix6xN(Entity):
    ...

class Matrix6xNOperator(MatrixBase):
    N = 30
    bl_label = "6xN"
    @classmethod
    def poll(cls, context):
        return False

klasses[Matrix6xNOperator.bl_label] = Matrix6xNOperator

bundle = Bundle(tree, Base, klasses, database.matrix, "matrix")
