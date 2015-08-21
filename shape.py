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
    from .base import bpy, BPY, database, Operator, Entity, Bundle
    from .common import FORMAT

types = [
    "Const shape",
    "Piecewise const shape",
    "Linear shape",
    "Piecewise linear shape",
    "Parabolic shape"]

tree = ["Shape", types]

klasses = dict()

class Base(Operator):
    bl_label = "Shapes"
    bl_options = {'DEFAULT_CLOSED'}
    @classmethod
    def poll(cls, context):
        return True
    @classmethod
    def make_list(self, ListItem):
        bpy.types.Scene.shape_uilist = bpy.props.CollectionProperty(type = ListItem)
        bpy.types.Scene.shape_index = bpy.props.IntProperty(default=-1)
    @classmethod
    def delete_list(self):
        del bpy.types.Scene.shape_uilist
        del bpy.types.Scene.shape_index
    @classmethod
    def get_uilist(self, context):
        return context.scene.shape_index, context.scene.shape_uilist
    def set_index(self, context, value):
        context.scene.shape_index = value
    def prereqs(self, context):
        pass

for t in types:
    class Tester(Base):
        bl_label = t
        @classmethod
        def poll(cls, context):
            return False
        def create_entity(self):
            return Entity(self.name)
    klasses[t] = Tester

class ConstShape(Entity):
    def string(self, scale=1.):
        return '\t\tconst, '+ FORMAT(self.constant*scale)

class ConstShapeOperator(Base):
    bl_label = "Const shape"
    constant = bpy.props.FloatProperty(name="Constant", description="", min=-9.9e10, max=9.9e10, precision=6, default=1.0)
    def assign(self, context):
        self.constant = self.entity.constant
    def store(self, context):
        self.entity.constant = self.constant
    def create_entity(self):
        return ConstShape(self.name)

klasses[ConstShapeOperator.bl_label] = ConstShapeOperator

class PiecewiseConstShape(Entity):
    def string(self, scale=1.):
        ret += "\t\tpiecewise const, " + FORMAT(self.N)
        for i in range(self.N):
            ret += ",\n\t\t\t" + FORMAT(self.X[i]) + ", " + FORMAT(self.Y[i])
        return ret

class PiecewiseShapeOperator(Base):
    N = bpy.props.IntProperty(name="Number of points", min=2, max=50, description="")
    X = bpy.props.CollectionProperty(name="Abscissas", type = BPY.Floats)
    Y = bpy.props.CollectionProperty(name="Values", type = BPY.Floats)
    def prereqs(self, context):
        self.N = 2
        self.X.clear()
        self.Y.clear()
        for i in range(50):
            self.X.add()
            self.Y.add()
    def assign(self, context):
        self.N = self.entity.N
        for i, value in enumerate(self.entity.X):
            self.X[i].value = value
        for i, value in enumerate(self.entity.Y):
            self.Y[i].value = value
    def store(self, context):
        self.entity.N = self.N
        self.entity.X = [x.value for x in self.X]
        self.entity.Y = [y.value for y in self.Y]
    def draw(self, context):
        self.basis = self.N
        layout = self.layout
        layout.prop(self, "N")
        row = layout.row()
        row.label("Abscissa")
        row.label("Value")
        for i in range(self.N):
            row = layout.row()
            row.prop(self.X[i], "value", text="")
            row.prop(self.Y[i], "value", text="")
    def check(self, context):
        return self.basis != self.N

class PiecewiseConstShapeOperator(PiecewiseShapeOperator):
    bl_label = "Piecewise const shape"
    def create_entity(self):
        return PiecewiseConstShape(self.name)

klasses[PiecewiseConstShapeOperator.bl_label] = PiecewiseConstShapeOperator

class LinearShape(Entity):
    def string(self, scale=1.):
        return '\t\tlinear' + ", ".join([FORMAT(y*scale) for y in [self.y1, self.y2]])

class LinearShapeOperator(Base):
    bl_label = "Linear shape"
    y1 = bpy.props.FloatProperty(name="y(x=-1)", description="", min=-9.9e10, max=9.9e10, precision=6, default=0.0)
    y2 = bpy.props.FloatProperty(name="y(x=1)", description="", min=-9.9e10, max=9.9e10, precision=6, default=0.0)
    def assign(self, context):
        self.y1 = self.entity.y1
        self.y2 = self.entity.y2
    def store(self, context):
        self.entity.y1 = self.y1
        self.entity.y2 = self.y2
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "y1")
        layout.prop(self, "y2")
    def create_entity(self):
        return LinearShape(self.name)

klasses[LinearShapeOperator.bl_label] = LinearShapeOperator

class PiecewiseLinearShape(Entity):
    def string(self, scale=1.):
        ret += "\t\tpiecewise linear, " + FORMAT(self.N)
        for i in range(self.N):
            ret += ",\n\t\t\t" + FORMAT(self.X[i]) + ", " + FORMAT(self.Y[i])
        return ret

class PiecewiseLinearShapeOperator(PiecewiseShapeOperator):
    bl_label = "Piecewise linear shape"
    def create_entity(self):
        return PiecewiseLinearShape(self.name)

klasses[PiecewiseLinearShapeOperator.bl_label] = PiecewiseLinearShapeOperator

class ParabolicShape(Entity):
    def string(self, scale=1.):
        return '\t\tparabolic' + ", ".join([FORMAT(y*scale) for y in [self.y1, self.y2, self.y2]])

class ParabolicShapeOperator(Base):
    bl_label = "Parabolic shape"
    y1 = bpy.props.FloatProperty(name="y(x=-1)", description="", min=-9.9e10, max=9.9e10, precision=6, default=0.0)
    y2 = bpy.props.FloatProperty(name="y(x=0)", description="", min=-9.9e10, max=9.9e10, precision=6, default=0.0)
    y3 = bpy.props.FloatProperty(name="y(x=1)", description="", min=-9.9e10, max=9.9e10, precision=6, default=0.0)
    def assign(self, context):
        self.y1 = self.entity.y1
        self.y2 = self.entity.y2
        self.y3 = self.entity.y3
    def store(self, context):
        self.entity.y1 = self.y1
        self.entity.y2 = self.y2
        self.entity.y3 = self.y3
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "y1")
        layout.prop(self, "y2")
        layout.prop(self, "y3")
    def create_entity(self):
        return ParabolicShape(self.name)

klasses[ParabolicShapeOperator.bl_label] = ParabolicShapeOperator

bundle = Bundle(tree, Base, klasses, database.shape, "shape")
