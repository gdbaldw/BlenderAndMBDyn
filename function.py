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
    from .base import bpy, database, Operator, Entity, Bundle, BPY, enum_function
    from .base import update_function
    from .common import FORMAT

types = [
    "Const",
    "Exp",
    "Log",
    "Pow",
    "Linear",
    "Cubic natural spline",
    "Multilinear",
    "Chebychev",
    "Sum",
    "Sub",
    "Mul",
    "Div"]

tree = ["Add Function", types]

klasses = dict()

class Base(Operator):
    bl_label = "Functions"
    bl_options = {'DEFAULT_CLOSED'}
    @classmethod
    def poll(cls, context):
        return True
    @classmethod
    def make_list(self, ListItem):
        bpy.types.Scene.function_uilist = bpy.props.CollectionProperty(type = ListItem)
        bpy.types.Scene.function_index = bpy.props.IntProperty(default=-1)
    @classmethod
    def delete_list(self):
        del bpy.types.Scene.function_uilist
        del bpy.types.Scene.function_index
    @classmethod
    def get_uilist(self, context):
        return context.scene.function_index, context.scene.function_uilist
    def set_index(self, context, value):
        context.scene.function_index = value

for t in types:
    class Tester(Base):
        bl_label = t
        @classmethod
        def poll(cls, context):
            return False
        def create_entity(self):
            return Entity(self.name)
    klasses[t] = Tester

class Const(Entity):
    def write(self, text):
        if self.written:
            return
        text.write("scalar function: \"" + self.name + "\", const, " + FORMAT(self.constant) + ";\n")

class ConstOperator(Base):
    bl_label = "Const"
    constant = bpy.props.FloatProperty(name="Constant", description="", min=-9.9e10, max=9.9e10, precision=6, default=0.0)
    def assign(self, context):
        self.constant = self.entity.constant
    def store(self, context):
        self.entity.constant = self.constant
    def create_entity(self):
        return Const(self.name)

klasses[ConstOperator.bl_label] = ConstOperator

class Exp(Entity):
    def write(self, text):
        if self.written:
            return
        text.write("scalar function: \"" + self.name + "\", exp")
        if not self.default_base:
            text.write(", base, " + FORMAT(self.base))
        if not self.default_coefficient:
            text.write(", coefficient, " + FORMAT(self.coefficient))
        text.write(", " + FORMAT(self.multiplier) + ";\n")

class ExpLogBase(Base):
    default_base = bpy.props.BoolProperty(name="Default base (e)", default=True)
    base = bpy.props.FloatProperty(name="Base", description="", min=-9.9e10, max=9.9e10, precision=6, default=10.0)
    default_coefficient = bpy.props.BoolProperty(name="Default coefficient (1)", default=True)
    coefficient = bpy.props.FloatProperty(name="Coefficient", description="", min=-9.9e10, max=9.9e10, precision=6, default=1.0)
    multiplier = bpy.props.FloatProperty(name="Multiplier", description="", min=-9.9e10, max=9.9e10, precision=6, default=1.0)
    def assign(self, context):
        self.default_base = self.entity.default_base
        self.base = self.entity.base
        self.default_coefficient = self.entity.default_coefficient
        self.coefficient = self.entity.coefficient
        self.multiplier = self.entity.multiplier
    def store(self, context):
        self.entity.default_base = self.default_base
        self.entity.base = self.base
        self.entity.default_coefficient = self.default_coefficient
        self.entity.coefficient = self.coefficient
        self.entity.multiplier = self.multiplier
    def draw(self, context):
        self.basis = (self.default_base, self.default_coefficient)
        layout = self.layout
        row = layout.row()
        row.prop(self, "default_base")
        if not self.default_base:
            row.prop(self, "base")
        row = layout.row()
        row.prop(self, "default_coefficient")
        if not self.default_coefficient:
            row.prop(self, "coefficient")
        layout.prop(self, "multiplier")
    def check(self, context):
        return self.basis != (self.default_base, self.default_coefficient)

class ExpOperator(ExpLogBase):
    bl_label = "Exp"
    def create_entity(self):
        return Exp(self.name)

klasses[ExpOperator.bl_label] = ExpOperator

class Log(Entity):
    def write(self, text):
        if self.written:
            return
        text.write("scalar function: \"" + self.name + "\", log")
        if not self.default_base:
            text.write(", base, " + FORMAT(self.base))
        if not self.default_coefficient:
            text.write(", coefficient, " + FORMAT(self.coefficient))
        text.write(", " + FORMAT(self.multiplier) + ";\n")

class LogOperator(ExpLogBase):
    bl_label = "Log"
    def create_entity(self):
        return Log(self.name)

klasses[LogOperator.bl_label] = LogOperator

class Pow(Entity):
    def write(self, text):
        if self.written:
            return
        text.write("scalar function: \"" + self.name + "\", pow, " + FORMAT(self.power) + ";\n")

class PowOperator(Base):
    bl_label = "Pow"
    power = bpy.props.FloatProperty(name="Power", description="", min=-9.9e10, max=9.9e10, precision=6, default=1.0)
    def assign(self, context):
        self.power = self.entity.power
    def store(self, context):
        self.entity.power = self.power
    def create_entity(self):
        return Pow(self.name)

klasses[PowOperator.bl_label] = PowOperator

class Linear(Entity):
    def write(self, text):
        if self.written:
            return
        text.write("scalar function: \"" + self.name + "\", linear")
        text.write(",\n\t" + FORMAT(self.x1) + ", " + FORMAT(self.x2))
        text.write(", " + FORMAT(self.y1) + ", " + FORMAT(self.y2) + ";\n")

class LinearOperator(Base):
    bl_label = "Linear"
    x1 = bpy.props.FloatProperty(name="x1", description="", min=-9.9e10, max=9.9e10, precision=6, default=0.0)
    x2 = bpy.props.FloatProperty(name="x2", description="", min=-9.9e10, max=9.9e10, precision=6, default=0.0)
    y1 = bpy.props.FloatProperty(name="y1", description="", min=-9.9e10, max=9.9e10, precision=6, default=0.0)
    y2 = bpy.props.FloatProperty(name="y2", description="", min=-9.9e10, max=9.9e10, precision=6, default=0.0)
    def assign(self, context):
        self.x1 = self.entity.x1
        self.x2 = self.entity.x2
        self.y1 = self.entity.y1
        self.y2 = self.entity.y2
    def store(self, context):
        self.entity.x1 = self.x1
        self.entity.x2 = self.x2
        self.entity.y1 = self.y1
        self.entity.y2 = self.y2
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "x1")
        layout.prop(self, "x2")
        layout.prop(self, "y1")
        layout.prop(self, "y2")
    def create_entity(self):
        return Linear(self.name)

klasses[LinearOperator.bl_label] = LinearOperator

class CubicNaturalSpline(Entity):
    def write(self, text):
        if self.written:
            return
        text.write("scalar function: \"" + self.name + "\", cubicspline")
        if not self.extrapolate:
            text.write(", do not extrapolate")
        for i in range(self.N):
            text.write(",\n\t" + FORMAT(self.X[i]) + ", " + FORMAT(self.Y[i]))
        text.write(";\n")

class MultipleBase(Base):
    extrapolate = bpy.props.BoolProperty(name="Extrapolate", default=True)
    N = bpy.props.IntProperty(name="Number of points", min=2, max=50, description="", default=2)
    X = bpy.props.CollectionProperty(name="X", type = BPY.Floats)
    Y = bpy.props.CollectionProperty(name="Y", type = BPY.Floats)
    def prereqs(self, context):
        self.X.clear()
        self.Y.clear()
        for i in range(50):
            self.X.add()
            self.Y.add()
    def assign(self, context):
        self.extrapolate = self.entity.extrapolate
        self.N = self.entity.N
        for i, value in enumerate(self.entity.X):
            self.X[i].value = value
        for i, value in enumerate(self.entity.Y):
            self.Y[i].value = value
    def store(self, context):
        self.entity.extrapolate = self.extrapolate
        self.entity.N = self.N
        self.entity.X = [x.value for x in self.X]
        self.entity.Y = [y.value for y in self.Y]
    def draw(self, context):
        self.basis = self.N
        layout = self.layout
        layout.prop(self, "extrapolate")
        layout.prop(self, "N")
        row = layout.row()
        row.label("X")
        row.label("Y")
        for i in range(self.N):
            row = layout.row()
            row.prop(self.X[i], "value", text="")
            row.prop(self.Y[i], "value", text="")
    def check(self, context):
        return self.basis != self.N

class CubicNaturalSplineOperator(MultipleBase):
    bl_label = "Cubic natural spline"
    def create_entity(self):
        return CubicNaturalSpline(self.name)

klasses[CubicNaturalSplineOperator.bl_label] = CubicNaturalSplineOperator

class Multilinear(Entity):
    def write(self, text):
        if self.written:
            return
        text.write("scalar function: \"" + self.name + "\", multilinear")
        if not self.extrapolate:
            text.write(", do not extrapolate")
        for i in range(self.N):
            text.write(",\n\t" + FORMAT(self.X[i]) + ", " + FORMAT(self.Y[i]))
        text.write(";\n")

class MultilinearOperator(MultipleBase):
    bl_label = "Multilinear"
    def create_entity(self):
        return Multilinear(self.name)

klasses[MultilinearOperator.bl_label] = MultilinearOperator

class Chebychev(Entity):
    def write(self, text):
        if self.written:
            return
        text.write("scalar function: \"" + self.name + "\", chebychev")
        text.write(",\n\t" + FORMAT(self.lower_bound) + ", " + FORMAT(self.upper_bound))
        if not self.extrapolate:
            text.write(", do not extrapolate")
        N = int(self.N/4)
        for i in range(N):
            text.write(",\n\t" + ", ".join([FORMAT(c) for c in self.C[4*i:4*(i+1)]]))
        if 4*N == self.N:
            text.write(";\n")
        else:
            text.write(",\n\t" + ", ".join([FORMAT(c) for c in self.C[4*N:self.N]]) + ";\n")

class ChebychevOperator(Base):
    bl_label = "Chebychev"
    lower_bound = bpy.props.FloatProperty(name="Lower bound", description="", min=-9.9e10, max=9.9e10, precision=6, default=0.0)
    upper_bound = bpy.props.FloatProperty(name="Upper bound", description="", min=-9.9e10, max=9.9e10, precision=6, default=0.0)
    extrapolate = bpy.props.BoolProperty(name="Extrapolate", default=True)
    N = bpy.props.IntProperty(name="Number of points", min=2, max=50, description="", default=2)
    C = bpy.props.CollectionProperty(name="Coefficients", type = BPY.Floats)
    def prereqs(self, context):
        self.C.clear()
        for i in range(50):
            self.C.add()
    def assign(self, context):
        self.lower_bound = self.entity.lower_bound
        self.upper_bound = self.entity.upper_bound
        self.extrapolate = self.entity.extrapolate
        self.N = self.entity.N
        for i, value in enumerate(self.entity.C):
            self.C[i].value = value
    def store(self, context):
        self.entity.lower_bound = self.lower_bound
        self.entity.upper_bound = self.upper_bound
        self.entity.extrapolate = self.extrapolate
        self.entity.N = self.N
        self.entity.C = [c.value for c in self.C]
    def draw(self, context):
        self.basis = self.N
        layout = self.layout
        layout.prop(self, "lower_bound")
        layout.prop(self, "upper_bound")
        layout.prop(self, "extrapolate")
        layout.prop(self, "N")
        layout.label("Coefficients")
        for i in range(self.N):
            layout.prop(self.C[i], "value", text="")
    def check(self, context):
        return self.basis != self.N
    def create_entity(self):
        return Chebychev(self.name)

klasses[ChebychevOperator.bl_label] = ChebychevOperator

class Sum(Entity):
    def write(self, text):
        if self.written:
            return
        text.write("scalar function: \"" + self.name + "\", sum")
        text.write(",\n\t\"" + self.links[0].name + "\", \"" + self.links[1].name + "\";\n")

class BinaryOperator(Base):
    f1_name = bpy.props.EnumProperty(items=enum_function, name="f1",
        update=lambda self, context: update_function(self, context, self.f1_name))
    f2_name = bpy.props.EnumProperty(items=enum_function, name="f2",
        update=lambda self, context: update_function(self, context, self.f2_name))
    def assign(self, context):
        self.f1_name = self.entity.links[0].name
        self.f2_name = self.entity.links[1].name
    def store(self, context):
        self.entity.unlink_all()
        self.link_function(context, self.f1_name)
        self.link_function(context, self.f2_name)
        self.entity.increment_links()
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "f1_name")
        layout.prop(self, "f2_name")

class SumOperator(BinaryOperator):
    bl_label = "Sum"
    def create_entity(self):
        return Sum(self.name)

klasses[SumOperator.bl_label] = SumOperator

class Sub(Entity):
    def write(self, text):
        if self.written:
            return
        text.write("scalar function: \"" + self.name + "\", sub")
        text.write(",\n\t\"" + self.links[0].name + "\", \"" + self.links[1].name + "\";\n")

class SubOperator(BinaryOperator):
    bl_label = "Sub"
    def create_entity(self):
        return Sub(self.name)

klasses[SubOperator.bl_label] = SubOperator

class Mul(Entity):
    def write(self, text):
        if self.written:
            return
        text.write("scalar function: \"" + self.name + "\", mul")
        text.write(",\n\t\"" + self.links[0].name + "\", \"" + self.links[1].name + "\";\n")

class MulOperator(BinaryOperator):
    bl_label = "Mul"
    def create_entity(self):
        return Mul(self.name)

klasses[MulOperator.bl_label] = MulOperator

class Div(Entity):
    def write(self, text):
        if self.written:
            return
        text.write("scalar function: \"" + self.name + "\", div")
        text.write(",\n\t\"" + self.links[0].name + "\", \"" + self.links[1].name + "\";\n")

class DivOperator(BinaryOperator):
    bl_label = "Div"
    def create_entity(self):
        return Div(self.name)

klasses[DivOperator.bl_label] = DivOperator

bundle = Bundle(tree, Base, klasses, database.function, "function")
