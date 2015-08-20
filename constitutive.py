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
    from .base import bpy, root_dot, database, Operator, Entity, Bundle, BPY, enum_drive, enum_function, enum_matrix_3x1, enum_matrix_6x1, enum_matrix_3x3, enum_matrix_6x6, enum_matrix_6xN
    from .base import update_drive, update_function, update_matrix
    from .common import FORMAT

types = [
    "Linear elastic",
    "Linear elastic generic",
    "Linear elastic generic axial torsion coupling",
    "Cubic elastic generic",
    "Inverse square elastic",
    "Log elastic",
    "Linear elastic bistop",
    "Double linear elastic",
    "Isotropic hardening elastic",
    "Scalar function elastic isotropic",
    "Scalar function elastic orthotropic",
    "Linear viscous",
    "Linear viscous generic",
    "Linear viscoelastic",
    "Linear viscoelastic generic",
    "Linear time variant viscoelastic generic",
    "Linear viscoelastic generic axial torsion coupling",
    "Cubic viscoelastic generic",
    "Double linear viscoelastic",
    "Turbulent viscoelastic",
    "Linear viscoelastic bistop",
    "Shock absorber",
    "Symbolic elastic",
    "Symbolic viscous",
    "Symbolic viscoelastic",
    "ann elastic",
    "ann viscoelastic",
    "nlsf elastic",
    "nlsf viscous",
    "nlsf viscoelastic",
    "nlp elastic",
    "nlp viscous",
    "nlp viscoelastic",
    ]

tree = ["Constitutive", types]

klasses = dict()

class Base(Operator):
    @classmethod
    def get_uilist(self, context):
        return context.scene.input_card_index, context.scene.input_card_uilist
    def set_index(self, context, value):
        context.scene.input_card_index = value
    def draw_dimension(self, layout):
        if self.bl_idname.endswith("c_" + "_".join(self.name.lower().split())):
            layout.prop(self, "dimension")
        else:
            layout.label(self.dimension)

for t in types:
    class Tester(Base):
        bl_label = t
        dimension_items = [("1D", "1D", ""), ("3D", "3D", ""), ("6D", "6D", "")]
        dimension = bpy.props.EnumProperty(items=dimension_items, name="Dimension")
        @classmethod
        def poll(cls, context):
            return False
        def create_entity(self):
            return Entity(self.name)
    klasses[t] = Tester

class LinearElastic(Entity):
    def string(self):
        if self.dimension == "1D":
            return "linear elastic, " + FORMAT(self.stiffness)
        else:
            return "linear elastic isotropic, " + FORMAT(self.stiffness)

class LinearElasticOperator(Base):
    bl_label = "Linear elastic"
    dimension_items = [("1D", "1D", ""), ("3D", "3D", ""), ("6D", "6D", "")]
    dimension = bpy.props.EnumProperty(items=dimension_items, name="Dimension")
    stiffness = bpy.props.FloatProperty(name="Stiffness", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    def assign(self, context):
        self.stiffness = self.entity.stiffness
        self.dimension = self.entity.dimension
    def store(self, context):
        self.entity.stiffness = self.stiffness
        self.entity.dimension = self.dimension
    def draw(self, context):
        layout = self.layout
        self.draw_dimension(layout)
        layout.prop(self, "stiffness")
    def create_entity(self):
        return LinearElastic(self.name)

klasses[LinearElasticOperator.bl_label] = LinearElasticOperator

class LinearElasticGeneric(Entity):
    def string(self):
        if self.dimension == "1D":
            return "linear elastic generic, " + FORMAT(self.stiffness)
        else:
            return "linear elastic generic, " + self.links[0].string()

class LinearElasticGenericOperator(Base):
    bl_label = "Linear elastic generic"
    dimension_items = [("1D", "1D", ""), ("3D", "3D", ""), ("6D", "6D", "")]
    dimension = bpy.props.EnumProperty(items=dimension_items, name="Dimension")
    stiffness = bpy.props.FloatProperty(name="Stiffness", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    stiffness_matrix_3x3_name = bpy.props.EnumProperty(items=enum_matrix_3x3, name="Stiffness",
        update=lambda self, context: update_matrix(self, context, self.stiffness_matrix_3x3_name, "3x3"))
    stiffness_matrix_6x6_name = bpy.props.EnumProperty(items=enum_matrix_6x6, name="Stiffness",
        update=lambda self, context: update_matrix(self, context, self.stiffness_matrix_6x6_name, "6x6"))
    def assign(self, context):
        self.dimension = self.entity.dimension
        if self.dimension == "1D":
            self.stiffness = self.entity.stiffness
        elif self.dimension == "3D":
            self.stiffness_matrix_3x3_name = self.entity.links[0].name
        else:
            self.stiffness_matrix_6x6_name = self.entity.links[0].name
    def store(self, context):
        self.entity.dimension = self.dimension
        if self.dimension == "1D":
            self.entity.stiffness = self.stiffness
        else:
            if self.dimension == "3D":
                self.entity.links.append(database.matrix.get_by_name(self.stiffness_matrix_3x3_name))
            else:
                self.entity.links.append(database.matrix.get_by_name(self.stiffness_matrix_6x6_name))
    def draw(self, context):
        self.basis = self.dimension
        layout = self.layout
        self.draw_dimension(layout)
        if self.dimension == "1D":
            layout.prop(self, "stiffness")
        elif self.dimension == "3D":
            layout.prop(self, "stiffness_matrix_3x3_name")
        else:
            layout.prop(self, "stiffness_matrix_6x6_name")
    def check(self, context):
        return self.basis != self.dimension
    def create_entity(self):
        return LinearElasticGeneric(self.name)

klasses[LinearElasticGenericOperator.bl_label] = LinearElasticGenericOperator

class LinearElasticGenericAxialTorsionCoupling(Entity):
    def string(self):
        return "linear elastic generic axial torsion coupling," + self.links[0].string() + ",\n\t\t\t" + FORMAT(self.coupling_coefficient)
                
class LinearElasticGenericAxialTorsionCouplingOperator(Base):
    bl_label = "Linear elastic generic axial torsion coupling"
    dimension_items = [("6D", "6D", "")]
    dimension = bpy.props.EnumProperty(items=dimension_items, name="Dimension")
    coupling_coefficient = bpy.props.FloatProperty(name="Coupling coefficient", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    stiffness_matrix_6x1_name = bpy.props.EnumProperty(items=enum_matrix_6x1, name="Stiffness",
        update=lambda self, context: update_matrix(self, context, self.stiffness_matrix_6x1_name, "6x1"))
    def assign(self, context):
        self.dimension = self.entity.dimension
        self.coupling_coefficient = self.entity.coupling_coefficient
        self.stiffness_matrix_6x1_name = self.entity.links[0].name
    def store(self, context):
        self.entity.dimension = self.dimension
        self.entity.coupling_coefficient = self.coupling_coefficient
        self.entity.links.append(database.matrix.get_by_name(self.stiffness_matrix_6x1_name))
    def draw(self, context):
        self.basis = self.dimension
        layout = self.layout
        self.draw_dimension(layout)
        layout.prop(self, "coupling_coefficient")
        layout.prop(self, "stiffness_matrix_6x1_name")
    def create_entity(self):
        return LinearElasticGenericAxialTorsionCoupling(self.name)

klasses[LinearElasticGenericAxialTorsionCouplingOperator.bl_label] = LinearElasticGenericAxialTorsionCouplingOperator

class CubicElasticGeneric(Entity):
    def string(self):
        ret = "cubic elastic generic"
        if self.dimension == "1D":
            for stiffness in [self.stiffness_1, self.stiffness_2, self.stiffness_3]:
                ret += ", " + FORMAT(stiffness)
        else:
            for link in self.links:
                ret += "," + link.string()
        return ret

class CubicElasticGenericOperator(Base):
    bl_label = "Cubic elastic generic"
    dimension_items = [("1D", "1D", ""), ("3D", "3D", "")]
    dimension = bpy.props.EnumProperty(items=dimension_items, name="Dimension")
    stiffness_1 = bpy.props.FloatProperty(name="Stiffness 1", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    stiffness_2 = bpy.props.FloatProperty(name="Stiffness 2", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    stiffness_3 = bpy.props.FloatProperty(name="Stiffness 3", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    stiffness_matrix_3x1_1_name = bpy.props.EnumProperty(items=enum_matrix_3x1, name="Stiffness 1",
        update=lambda self, context: update_matrix(self, context, self.stiffness_matrix_3x1_1_name, "3x1"))
    stiffness_matrix_3x1_2_name = bpy.props.EnumProperty(items=enum_matrix_3x1, name="Stiffness 2",
        update=lambda self, context: update_matrix(self, context, self.stiffness_matrix_3x1_2_name, "3x1"))
    stiffness_matrix_3x1_3_name = bpy.props.EnumProperty(items=enum_matrix_3x1, name="Stiffness 3",
        update=lambda self, context: update_matrix(self, context, self.stiffness_matrix_3x1_3_name, "3x1"))
    def assign(self, context):
        self.dimension = self.entity.dimension
        if self.dimension == "1D":
            self.stiffness_1 = self.entity.stiffness_1
            self.stiffness_2 = self.entity.stiffness_2
            self.stiffness_3 = self.entity.stiffness_3
        else:
            self.stiffness_matrix_3x1_1_name = self.entity.links[0].name
            self.stiffness_matrix_3x1_2_name = self.entity.links[1].name
            self.stiffness_matrix_3x1_3_name = self.entity.links[2].name
    def store(self, context):
        self.entity.dimension = self.dimension
        if self.dimension == "1D":
            self.entity.stiffness_1 = self.stiffness_1
            self.entity.stiffness_2 = self.stiffness_2
            self.entity.stiffness_3 = self.stiffness_3
        else:
            for matrix_name in [self.stiffness_matrix_3x1_1_name, self.stiffness_matrix_3x1_2_name, self.stiffness_matrix_3x1_3_name]:
                self.entity.links.append(database.matrix.get_by_name(matrix_name))
    def draw(self, context):
        self.basis = self.dimension
        layout = self.layout
        self.draw_dimension(layout)
        if self.dimension == "1D":
            for c in "123":
                layout.prop(self, "stiffness_" + c)
        else:
            for c in "123":
                layout.prop(self, "stiffness_matrix_3x1_" + c + "_name")
    def check(self, context):
        return self.basis != self.dimension
    def create_entity(self):
        return CubicElasticGeneric(self.name)

klasses[CubicElasticGenericOperator.bl_label] = CubicElasticGenericOperator

class InverseSquareElastic(Entity):
    def string(self):
        return "inverse square elastic, " + FORMAT(self.stiffness) + ", " + FORMAT(self.ref_length)

class InverseSquareElasticOperator(Base):
    bl_label = "Inverse square elastic"
    dimension_items = [("1D", "1D", ""), ]
    dimension = bpy.props.EnumProperty(items=dimension_items, name="Dimension")
    stiffness = bpy.props.FloatProperty(name="Stiffness", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    ref_length = bpy.props.FloatProperty(name="Reference length", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    def assign(self, context):
        self.stiffness = self.entity.stiffness
        self.ref_length = self.entity.ref_length
        self.dimension = self.entity.dimension
    def store(self, context):
        self.entity.stiffness = self.stiffness
        self.entity.ref_length = self.ref_length
        self.entity.dimension = self.dimension
    def draw(self, context):
        layout = self.layout
        self.draw_dimension(layout)
        layout.prop(self, "stiffness")
        layout.prop(self, "ref_length")
    def create_entity(self):
        return InverseSquareElastic(self.name)

klasses[InverseSquareElasticOperator.bl_label] = InverseSquareElasticOperator

class LogElastic(Entity):
    def string(self):
        return "log elastic, " + FORMAT(self.stiffness)

class LogElasticOperator(Base):
    bl_label = "Log elastic"
    dimension_items = [("1D", "1D", ""), ]
    dimension = bpy.props.EnumProperty(items=dimension_items, name="Dimension")
    stiffness = bpy.props.FloatProperty(name="Stiffness", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    def assign(self, context):
        self.stiffness = self.entity.stiffness
        self.dimension = self.entity.dimension
    def store(self, context):
        self.entity.stiffness = self.stiffness
        self.entity.dimension = self.dimension
    def draw(self, context):
        layout = self.layout
        self.draw_dimension(layout)
        layout.prop(self, "stiffness")
    def create_entity(self):
        return LogElastic(self.name)

klasses[LogElasticOperator.bl_label] = LogElasticOperator

class LinearElasticBistop(Entity):
    def string(self):
        ret = "linear elastic bistop"
        if self.dimension == "1D":
            ret += ",\n\t\t\t" + FORMAT(self.stiffness)
        else:
            ret += ", " + self.links[2].string()
        ret += ",\n\t\t\tinitial status, " + self.initial_status
        for link in self.links[:2]:
            ret += ",\n\t\t\t" + link.string()
        return ret

class LinearElasticBistopOperator(Base):
    bl_label = "Linear elastic bistop"
    dimension_items = [("1D", "1D", ""), ("3D", "3D", ""), ("6D", "6D", "")]
    dimension = bpy.props.EnumProperty(items=dimension_items, name="Dimension")
    stiffness = bpy.props.FloatProperty(name="Stiffness", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    stiffness_matrix_3x3_name = bpy.props.EnumProperty(items=enum_matrix_3x3, name="Stiffness",
        update=lambda self, context: update_matrix(self, context, self.stiffness_matrix_3x3_name, "3x3"))
    stiffness_matrix_6x6_name = bpy.props.EnumProperty(items=enum_matrix_6x6, name="Stiffness",
        update=lambda self, context: update_matrix(self, context, self.stiffness_matrix_6x6_name, "6x6"))
    initial_status = bpy.props.EnumProperty(items=[("active", "Active", ""), ("inactive", "Inactive", "")], name="Initial status")
    activating_condition_name = bpy.props.EnumProperty(items=enum_drive, name="Activating condition",
        update=lambda self, context: update_drive(self, context, self.activating_condition_name))
    deactivating_condition_name = bpy.props.EnumProperty(items=enum_drive, name="Deactivating condition",
        update=lambda self, context: update_drive(self, context, self.deactivating_condition_name))
    def assign(self, context):
        self.dimension = self.entity.dimension
        self.initial_status = self.entity.initial_status
        self.activating_condition_name = self.entity.links[0].name
        self.deactivating_condition_name = self.entity.links[1].name
        if self.dimension == "1D":
            self.stiffness = self.entity.stiffness
        elif self.dimension == "3D":
            self.stiffness_matrix_3x3_name = self.entity.links[2].name
        else:
            self.stiffness_matrix_6x6_name = self.entity.links[2].name
    def store(self, context):
        self.entity.dimension = self.dimension
        self.entity.initial_status = self.initial_status
        self.entity.links.append(database.drive.get_by_name(self.activating_condition_name))
        self.entity.links.append(database.drive.get_by_name(self.deactivating_condition_name))
        if self.dimension == "1D":
            self.entity.stiffness = self.stiffness
        else:
            if self.dimension == "3D":
                self.entity.links.append(database.matrix.get_by_name(self.stiffness_matrix_3x3_name))
            else:
                self.entity.links.append(database.matrix.get_by_name(self.stiffness_matrix_6x6_name))
    def draw(self, context):
        self.basis = self.dimension
        layout = self.layout
        self.draw_dimension(layout)
        if self.dimension == "1D":
            layout.prop(self, "stiffness")
        elif self.dimension == "3D":
            layout.prop(self, "stiffness_matrix_3x3_name")
        else:
            layout.prop(self, "stiffness_matrix_6x6_name")
        layout.prop(self, "initial_status")
        for s in "activating deactivating".split():
            layout.prop(self, s + "_condition_name")
    def check(self, context):
        return self.basis != self.dimension
    def create_entity(self):
        return LinearElasticBistop(self.name)

klasses[LinearElasticBistopOperator.bl_label] = LinearElasticBistopOperator

class DoubleLinearElastic(Entity):
    def string(self):
        ret = "double linear elastic"
        if self.dimension == "1D":
            ret += ", " + FORMAT(self.stiffness_1)
            ret += ", " + FORMAT(self.upper_strain) + ", " + FORMAT(self.lower_strain)
            ret += ", " + FORMAT(self.stiffness_2)
        else:
            ret += "," + self.links[0].string()
            ret += ",\n\t\t\t" + FORMAT(self.upper_strain) + ", " + FORMAT(self.lower_strain)
            ret += "," + self.links[1].string()
        return ret

class DoubleLinearElasticOperator(Base):
    bl_label = "Double linear elastic"
    dimension_items = [("1D", "1D", ""), ("3D", "3D", "")]
    dimension = bpy.props.EnumProperty(items=dimension_items, name="Dimension")
    stiffness_1 = bpy.props.FloatProperty(name="Stiffness 1", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    stiffness_2 = bpy.props.FloatProperty(name="Stiffness 2", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    upper_strain = bpy.props.FloatProperty(name="Upper strain", description="", min=0.000001, max=9.9e10, precision=6)
    lower_strain = bpy.props.FloatProperty(name="Lower strain", description="", min=0.000001, max=9.9e10, precision=6)
    stiffness_matrix_3x1_1_name = bpy.props.EnumProperty(items=enum_matrix_3x1, name="Stiffness 1",
        update=lambda self, context: update_matrix(self, context, self.stiffness_matrix_3x1_1_name, "3x1"))
    stiffness_matrix_3x1_2_name = bpy.props.EnumProperty(items=enum_matrix_3x1, name="Stiffness 2",
        update=lambda self, context: update_matrix(self, context, self.stiffness_matrix_3x1_2_name, "3x1"))
    def assign(self, context):
        self.dimension = self.entity.dimension
        self.upper_strain = self.entity.upper_strain
        self.lower_strain = self.entity.lower_strain
        if self.dimension == "1D":
            self.stiffness_1 = self.entity.stiffness_1
            self.stiffness_2 = self.entity.stiffness_2
        else:
            self.stiffness_matrix_3x1_1_name = self.entity.links[0].name
            self.stiffness_matrix_3x1_2_name = self.entity.links[1].name
    def store(self, context):
        self.entity.dimension = self.dimension
        self.entity.upper_strain = self.upper_strain
        self.entity.lower_strain = self.lower_strain
        if self.dimension == "1D":
            self.entity.stiffness_1 = self.stiffness_1
            self.entity.stiffness_2 = self.stiffness_2
        else:
            self.entity.links.append(database.matrix.get_by_name(self.stiffness_matrix_3x1_1_name))
            self.entity.links.append(database.matrix.get_by_name(self.stiffness_matrix_3x1_2_name))
    def draw(self, context):
        self.basis = self.dimension
        layout = self.layout
        self.draw_dimension(layout)
        if self.dimension == "1D":
            for c in "12":
                layout.prop(self, "stiffness_" + c)
        else:
            for c in "12":
                layout.prop(self, "stiffness_matrix_3x1_" + c + "_name")
        layout.prop(self, "upper_strain")
        layout.prop(self, "lower_strain")
    def check(self, context):
        return self.basis != self.dimension
    def create_entity(self):
        return DoubleLinearElastic(self.name)

klasses[DoubleLinearElasticOperator.bl_label] = DoubleLinearElasticOperator

class IsotropicHardeningElastic(Entity):
    def string(self):
        ret = "isotropic hardening elastic"
        if self.dimension == "1D":
            ret += ",\n\t\t\t" + FORMAT(self.stiffness)
        else:
            ret += ", " + self.links[0].string()
        ret += ",\n\t\t\t" + FORMAT(self.reference_strain)
        if self.use_linear_stiffness:
            ret += ", linear stiffness, " + FORMAT(self.linear_stiffness)
        return ret

class IsotropicHardeningElasticOperator(Base):
    bl_label = "Isotropic hardening elastic"
    dimension_items = [("1D", "1D", ""), ("3D", "3D", ""), ("6D", "6D", "")]
    dimension = bpy.props.EnumProperty(items=dimension_items, name="Dimension")
    stiffness = bpy.props.FloatProperty(name="Stiffness", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    stiffness_matrix_3x3_name = bpy.props.EnumProperty(items=enum_matrix_3x3, name="Stiffness",
        update=lambda self, context: update_matrix(self, context, self.stiffness_matrix_3x3_name, "3x3"))
    stiffness_matrix_6x6_name = bpy.props.EnumProperty(items=enum_matrix_6x6, name="Stiffness",
        update=lambda self, context: update_matrix(self, context, self.stiffness_matrix_6x6_name, "3x3"))
    reference_strain = bpy.props.FloatProperty(name="Reference strain", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    use_linear_stiffness = bpy.props.BoolProperty("Use linear stiffness", default=False)
    linear_stiffness = bpy.props.FloatProperty(name="Reference strain", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    def assign(self, context):
        self.dimension = self.entity.dimension
        self.reference_strain = self.entity.reference_strain
        self.use_linear_stiffness = self.entity.use_linear_stiffness
        self.linear_stiffness = self.entity.linear_stiffness
        if self.dimension == "1D":
            self.stiffness = self.entity.stiffness
        elif self.dimension == "3D":
            self.stiffness_matrix_3x3_name = self.entity.links[0].name
        else:
            self.stiffness_matrix_6x6_name = self.entity.links[0].name
    def store(self, context):
        self.entity.dimension = self.dimension
        self.entity.reference_strain = self.reference_strain
        self.entity.use_linear_stiffness = self.use_linear_stiffness
        self.entity.linear_stiffness = self.linear_stiffness
        if self.dimension == "1D":
            self.entity.stiffness = self.stiffness
        else:
            if self.dimension == "3D":
                self.entity.links.append(database.matrix.get_by_name(self.stiffness_matrix_3x3_name))
            else:
                self.entity.links.append(database.matrix.get_by_name(self.stiffness_matrix_6x6_name))
    def draw(self, context):
        self.basis = (self.dimension, self.use_linear_stiffness)
        layout = self.layout
        self.draw_dimension(layout)
        if self.dimension == "1D":
            layout.prop(self, "stiffness")
        elif self.dimension == "3D":
            layout.prop(self, "stiffness_matrix_3x3_name")
        else:
            layout.prop(self, "stiffness_matrix_6x6_name")
        layout.prop(self, "reference_strain")
        layout.prop(self, "use_linear_stiffness")
        if self.use_linear_stiffness:
            layout.prop(self, "linear_stiffness")
    def check(self, context):
        return self.basis != (self.dimension, self.use_linear_stiffness)
    def create_entity(self):
        return IsotropicHardeningElastic(self.name)

klasses[IsotropicHardeningElasticOperator.bl_label] = IsotropicHardeningElasticOperator

class ScalarFunctionElasticIsotropic(Entity):
    def string(self):
        if self.dimension == "1D":
            return "scalar function elastic, \"" + self.links[0].name + "\""
        else:
            return "scalar function elastic isotropic, \"" + self.links[0].name + "\""

class ScalarFunctionElasticIsotropicOperator(Base):
    bl_label = "Scalar function elastic isotropic"
    dimension_items = [("1D", "1D", ""), ("3D", "3D", ""), ("6D", "6D", "")]
    dimension = bpy.props.EnumProperty(items=dimension_items, name="Dimension")
    function_name = bpy.props.EnumProperty(items=enum_function, name="Function",
        update=lambda self, context: update_function(self, context, self.function_name))
    def assign(self, context):
        self.dimension = self.entity.dimension
        self.function_name = self.entity.links[0].name
    def store(self, context):
        self.entity.dimension = self.dimension
        self.entity.links.append(database.function.get_by_name(self.function_name))
    def draw(self, context):
        layout = self.layout
        self.draw_dimension(layout)
        layout.prop(self, "function_name")
    def create_entity(self):
        return ScalarFunctionElasticIsotropic(self.name)

klasses[ScalarFunctionElasticIsotropicOperator.bl_label] = ScalarFunctionElasticIsotropicOperator

class ScalarFunctionElasticOrthotropic(Entity):
    def string(self):
        ret = "scalar function elastic"
        if self.dimension != "1D":
            ret += " orthotropic"
        for i in range(int(self.dimension[0])):
            if self.is_null[i]:
                ret += ",\n\t\t\tnull"
            else:
                ret += ",\n\t\t\t\"" + self.links[i].name + "\""
        return ret

class ScalarFunctionElasticOrthotropicOperator(Base):
    bl_label = "Scalar function elastic orthotropic"
    dimension_items = [("1D", "1D", ""), ("3D", "3D", ""), ("6D", "6D", "")]
    dimension = bpy.props.EnumProperty(items=dimension_items, name="Dimension")
    is_null = bpy.props.BoolVectorProperty(size=6, name="Null")
    function_names = bpy.props.CollectionProperty(type=BPY.FunctionNames, name="Functions")
    def prereqs(self, context):
        self.function_names.clear()
        for i in range(6):
            self.function_names.add()
    def assign(self, context):
        self.dimension = self.entity.dimension
        self.is_null = self.entity.is_null
        for i, link in enumerate(self.entity.links):
            self.function_names[i].enable_popups = False
            self.function_names[i].value = link.name
            self.function_names[i].enable_popups = True
    def store(self, context):
        self.entity.dimension = self.dimension
        self.entity.is_null = [v for v in self.is_null]
        for f in self.function_names[:int(self.dimension[0])]:
            self.entity.links.append(database.function.get_by_name(f.value))
    def draw(self, context):
        self.basis = (self.dimension, [v for v in self.is_null])
        layout = self.layout
        self.draw_dimension(layout)
        for i in range(int(self.dimension[0])):
            row = layout.row()
            row.prop(self, "is_null", index=i)
            if not self.is_null[i]:
                row.prop(self.function_names[i], "value", text="")
    def check(self, context):
        return self.basis[0] != self.dimension or [True for i, v in enumerate(self.basis[1]) if v != self.is_null[i]]
    def create_entity(self):
        return ScalarFunctionElasticOrthotropic(self.name)

klasses[ScalarFunctionElasticOrthotropicOperator.bl_label] = ScalarFunctionElasticOrthotropicOperator

class LinearViscous(Entity):
    def string(self):
        if self.dimension == "1D":
            return "linear viscous, " + FORMAT(self.viscosity)
        else:
            return "linear viscous isotropic, " + FORMAT(self.viscosity)

class LinearViscousOperator(Base):
    bl_label = "Linear viscous"
    dimension_items = [("1D", "1D", ""), ("3D", "3D", ""), ("6D", "6D", "")]
    dimension = bpy.props.EnumProperty(items=dimension_items, name="Dimension")
    viscosity = bpy.props.FloatProperty(name="Viscosity", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    def assign(self, context):
        self.viscosity = self.entity.viscosity
        self.dimension = self.entity.dimension
    def store(self, context):
        self.entity.viscosity = self.viscosity
        self.entity.dimension = self.dimension
    def draw(self, context):
        layout = self.layout
        self.draw_dimension(layout)
        layout.prop(self, "viscosity")
    def create_entity(self):
        return LinearViscous(self.name)

klasses[LinearViscousOperator.bl_label] = LinearViscousOperator

class LinearViscousGeneric(Entity):
    def string(self):
        if self.dimension == "1D":
            return "linear viscous generic, " + FORMAT(self.viscosity)
        else:
            return "linear viscous generic, " + self.links[0].string()

class LinearViscousGenericOperator(Base):
    bl_label = "Linear viscous generic"
    dimension_items = [("1D", "1D", ""), ("3D", "3D", ""), ("6D", "6D", "")]
    dimension = bpy.props.EnumProperty(items=dimension_items, name="Dimension")
    viscosity = bpy.props.FloatProperty(name="Viscosity", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    viscosity_matrix_3x3_name = bpy.props.EnumProperty(items=enum_matrix_3x3, name="Viscosity",
        update=lambda self, context: update_matrix(self, context, self.viscosity_matrix_3x3_name, "3x3"))
    viscosity_matrix_6x6_name = bpy.props.EnumProperty(items=enum_matrix_6x6, name="Viscosity",
        update=lambda self, context: update_matrix(self, context, self.viscosity_matrix_6x6_name, "6x6"))
    def assign(self, context):
        self.dimension = self.entity.dimension
        if self.dimension == "1D":
            self.viscosity = self.entity.viscosity
        elif self.dimension == "3D":
            self.viscosity_matrix_3x3_name = self.entity.links[0].name
        else:
            self.viscosity_matrix_6x6_name = self.entity.links[0].name
    def store(self, context):
        self.entity.dimension = self.dimension
        if self.dimension == "1D":
            self.entity.viscosity = self.viscosity
        else:
            if self.dimension == "3D":
                self.entity.links.append(database.matrix.get_by_name(self.viscosity_matrix_3x3_name))
            else:
                self.entity.links.append(database.matrix.get_by_name(self.viscosity_matrix_6x6_name))
    def draw(self, context):
        self.basis = self.dimension
        layout = self.layout
        self.draw_dimension(layout)
        if self.dimension == "1D":
            layout.prop(self, "viscosity")
        elif self.dimension == "3D":
            layout.prop(self, "viscosity_matrix_3x3_name")
        else:
            layout.prop(self, "viscosity_matrix_6x6_name")
    def check(self, context):
        return self.basis != self.dimension
    def create_entity(self):
        return LinearViscousGeneric(self.name)

klasses[LinearViscousGenericOperator.bl_label] = LinearViscousGenericOperator

class LinearViscoelastic(Entity):
    def string(self):
        ret = "linear viscoelastic"
        if self.dimension == "1D":
            ret += ", " + FORMAT(self.stiffness)
        else:
            ret += " isotropic, " + FORMAT(self.stiffness)
        if self.proportional:
            ret += ", proportional, " + FORMAT(self.factor)
        else:
            ret += ", " + FORMAT(self.viscosity)
        return ret

class LinearViscoelasticOperator(Base):
    bl_label = "Linear viscoelastic"
    dimension_items = [("1D", "1D", ""), ("3D", "3D", ""), ("6D", "6D", "")]
    dimension = bpy.props.EnumProperty(items=dimension_items, name="Dimension")
    stiffness = bpy.props.FloatProperty(name="Stiffness", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    proportional = bpy.props.BoolProperty(name="Proportional", default=False)
    factor = bpy.props.FloatProperty(name="Factor", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    viscosity = bpy.props.FloatProperty(name="Viscosity", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    def assign(self, context):
        self.dimension = self.entity.dimension
        self.stiffness = self.entity.stiffness
        self.proportional = self.entity.proportional
        self.factor = self.entity.factor
        self.viscosity = self.entity.viscosity
    def store(self, context):
        self.entity.dimension = self.dimension
        self.entity.stiffness = self.stiffness
        self.entity.proportional = self.proportional
        self.entity.factor = self.factor
        self.entity.viscosity = self.viscosity
    def draw(self, context):
        self.basis = self.proportional
        layout = self.layout
        self.draw_dimension(layout)
        layout.prop(self, "stiffness")
        row = layout.row()
        row.prop(self, "proportional")
        if self.proportional:
            row.prop(self, "factor")
        else:
            layout.prop(self, "viscosity")
    def check(self, context):
        return self.basis != self.proportional
    def create_entity(self):
        return LinearViscoelastic(self.name)

klasses[LinearViscoelasticOperator.bl_label] = LinearViscoelasticOperator

class LinearViscoelasticGeneric(Entity):
    def string(self):
        ret = "linear viscoelastic generic"
        if self.dimension == "1D":
            ret += ", " + FORMAT(self.stiffness)
        else:
            ret += ", " + self.links[0].string()
        if self.proportional:
            ret += ", proportional, " + FORMAT(self.factor)
        else:
            if self.dimension == "1D":
                ret += ", " + FORMAT(self.viscosity)
            else:
                ret += ", " + self.links[1].string()
        return ret

class LinearViscoelasticGenericOperator(Base):
    bl_label = "Linear viscoelastic generic"
    dimension_items = [("1D", "1D", ""), ("3D", "3D", ""), ("6D", "6D", "")]
    dimension = bpy.props.EnumProperty(items=dimension_items, name="Dimension")
    stiffness = bpy.props.FloatProperty(name="Stiffness", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    stiffness_matrix_3x3_name = bpy.props.EnumProperty(items=enum_matrix_3x3, name="Stiffness",
        update=lambda self, context: update_matrix(self, context, self.stiffness_matrix_3x3_name, "3x3"))
    stiffness_matrix_6x6_name = bpy.props.EnumProperty(items=enum_matrix_6x6, name="Stiffness",
        update=lambda self, context: update_matrix(self, context, self.stiffness_matrix_6x6_name, "3x3"))
    proportional = bpy.props.BoolProperty(name="Proportional", default=False)
    factor = bpy.props.FloatProperty(name="Factor", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    viscosity = bpy.props.FloatProperty(name="Viscosity", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    viscosity_matrix_3x3_name = bpy.props.EnumProperty(items=enum_matrix_3x3, name="Viscosity",
        update=lambda self, context: update_matrix(self, context, self.viscosity_matrix_3x3_name, "6x6"))
    viscosity_matrix_6x6_name = bpy.props.EnumProperty(items=enum_matrix_6x6, name="Viscosity",
        update=lambda self, context: update_matrix(self, context, self.viscosity_matrix_6x6_name, "6x6"))
    def assign(self, context):
        self.dimension = self.entity.dimension
        self.proportional = self.entity.proportional
        self.factor = self.entity.factor
        if self.dimension == "1D":
            self.stiffness = self.entity.stiffness
            if not self.proportional:
                self.viscosity = self.entity.viscosity
        elif self.dimension == "3D":
            self.stiffness_matrix_3x3_name = self.entity.links[0].name
            if not self.proportional:
                self.viscosity_matrix_3x3_name = self.entity.links[1].name
        else:
            self.stiffness_matrix_6x6_name = self.entity.links[0].name
            if not self.proportional:
                self.viscosity_matrix_6x6_name = self.entity.links[1].name
    def store(self, context):
        self.entity.dimension = self.dimension
        self.entity.proportional = self.proportional
        self.entity.factor = self.factor
        if self.dimension == "1D":
            self.entity.stiffness = self.stiffness
            if not self.proportional:
                self.entity.viscosity = self.viscosity
        else:
            if self.dimension == "3D":
                self.entity.links.append(database.matrix.get_by_name(self.stiffness_matrix_3x3_name))
                if not self.proportional:
                    self.entity.links.append(database.matrix.get_by_name(self.viscosity_matrix_3x3_name))
            else:
                self.entity.links.append(database.matrix.get_by_name(self.stiffness_matrix_6x6_name))
                if not self.proportional:
                    self.entity.links.append(database.matrix.get_by_name(self.viscosity_matrix_6x6_name))
    def draw(self, context):
        self.basis = (self.dimension, self.proportional)
        layout = self.layout
        self.draw_dimension(layout)
        if self.dimension == "1D":
            layout.prop(self, "stiffness")
        elif self.dimension == "3D":
            layout.prop(self, "stiffness_matrix_3x3_name")
        else:
            layout.prop(self, "stiffness_matrix_6x6_name")
        row = layout.row()
        row.prop(self, "proportional")
        if self.proportional:
            row.prop(self, "factor")
        else:
            if self.dimension == "1D":
                layout.prop(self, "viscosity")
            elif self.dimension == "3D":
                layout.prop(self, "viscosity_matrix_3x3_name")
            else:
                layout.prop(self, "viscosity_matrix_6x6_name")
    def check(self, context):
        return self.basis != (self.dimension, self.proportional)
    def create_entity(self):
        return LinearViscoelasticGeneric(self.name)

klasses[LinearViscoelasticGenericOperator.bl_label] = LinearViscoelasticGenericOperator

class LinearTimeVariantViscoelasticGeneric(Entity):
    def string(self):
        ret = "linear time variant viscoelastic generic"
        if self.dimension == "1D":
            ret += ", " + FORMAT(self.stiffness)
        else:
            ret += ", " + self.links[2].string()
        ret += ", " + self.links[0].string()
        if self.proportional:
            ret += ", proportional, " + FORMAT(self.factor)
        else:
            if self.dimension == "1D":
                ret += ", " + FORMAT(self.viscosity)
            else:
                ret += ", " + self.links[3].string()
        ret += ", " + self.links[1].string()
        return ret

class LinearTimeVariantViscoelasticGenericOperator(Base):
    bl_label = "Linear time variant viscoelastic generic"
    dimension_items = [("1D", "1D", ""), ("3D", "3D", ""), ("6D", "6D", "")]
    dimension = bpy.props.EnumProperty(items=dimension_items, name="Dimension")
    stiffness_scale_name = bpy.props.EnumProperty(items=enum_drive, name="Stiffness scale",
        update=lambda self, context: update_drive(self, context, self.stiffness_scale_name))
    viscosity_scale_name = bpy.props.EnumProperty(items=enum_drive, name="Viscosity scale",
        update=lambda self, context: update_drive(self, context, self.viscosity_scale_name))
    stiffness = bpy.props.FloatProperty(name="Stiffness", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    stiffness_matrix_3x3_name = bpy.props.EnumProperty(items=enum_matrix_3x3, name="Stiffness",
        update=lambda self, context: update_matrix(self, context, self.stiffness_matrix_3x3_name, "3x3"))
    stiffness_matrix_6x6_name = bpy.props.EnumProperty(items=enum_matrix_6x6, name="Stiffness",
        update=lambda self, context: update_matrix(self, context, self.stiffness_matrix_6x6_name, "6x6"))
    proportional = bpy.props.BoolProperty(name="Proportional", default=False)
    factor = bpy.props.FloatProperty(name="Factor", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    viscosity = bpy.props.FloatProperty(name="Viscosity", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    viscosity_matrix_3x3_name = bpy.props.EnumProperty(items=enum_matrix_3x3, name="Viscosity",
        update=lambda self, context: update_matrix(self, context, self.viscosity_matrix_3x3_name, "3x3"))
    viscosity_matrix_6x6_name = bpy.props.EnumProperty(items=enum_matrix_6x6, name="Viscosity",
        update=lambda self, context: update_matrix(self, context, viscosity_matrix_6x6_name, "6x6"))
    def assign(self, context):
        self.dimension = self.entity.dimension
        self.proportional = self.entity.proportional
        self.factor = self.entity.factor
        self.stiffness_scale_name = self.entity.links[0].name
        self.viscosity_scale_name = self.entity.links[1].name
        if self.dimension == "1D":
            self.stiffness = self.entity.stiffness
            if not self.proportional:
                self.viscosity = self.entity.viscosity
        elif self.dimension == "3D":
            self.stiffness_matrix_3x3_name = self.entity.links[2].name
            if not self.proportional:
                self.viscosity_matrix_3x3_name = self.entity.links[3].name
        else:
            self.stiffness_matrix_6x6_name = self.entity.links[2].name
            if not self.proportional:
                self.viscosity_matrix_6x6_name = self.entity.links[3].name
    def store(self, context):
        self.entity.dimension = self.dimension
        self.entity.proportional = self.proportional
        self.entity.factor = self.factor
        self.entity.links.append(database.drive.get_by_name(self.stiffness_scale_name))
        self.entity.links.append(database.drive.get_by_name(self.viscosity_scale_name))
        if self.dimension == "1D":
            self.entity.stiffness = self.stiffness
            if not self.proportional:
                self.entity.viscosity = self.viscosity
        else:
            if self.dimension == "3D":
                self.entity.links.append(database.matrix.get_by_name(self.stiffness_matrix_3x3_name))
                if not self.proportional:
                    self.entity.links.append(database.matrix.get_by_name(self.viscosity_matrix_3x3_name))
            else:
                self.entity.links.append(database.matrix.get_by_name(self.stiffness_matrix_6x6_name))
                if not self.proportional:
                    self.entity.links.append(database.matrix.get_by_name(self.viscosity_matrix_6x6_name))
    def draw(self, context):
        self.basis = (self.dimension, self.proportional)
        layout = self.layout
        self.draw_dimension(layout)
        if self.dimension == "1D":
            layout.prop(self, "stiffness")
        elif self.dimension == "3D":
            layout.prop(self, "stiffness_matrix_3x3_name")
        else:
            layout.prop(self, "stiffness_matrix_6x6_name")
        layout.prop(self, "stiffness_scale_name")
        row = layout.row()
        row.prop(self, "proportional")
        if self.proportional:
            row.prop(self, "factor")
        else:
            if self.dimension == "1D":
                layout.prop(self, "viscosity")
            elif self.dimension == "3D":
                layout.prop(self, "viscosity_matrix_3x3_name")
            else:
                layout.prop(self, "viscosity_matrix_6x6_name")
        layout.prop(self, "viscosity_scale_name")
    def check(self, context):
        return self.basis != (self.dimension, self.proportional)
    def create_entity(self):
        return LinearTimeVariantViscoelasticGeneric(self.name)

klasses[LinearTimeVariantViscoelasticGenericOperator.bl_label] = LinearTimeVariantViscoelasticGenericOperator

class LinearViscoelasticGenericAxialTorsionCoupling(Entity):
    def string(self):
        ret = "linear viscoelastic generic axial torsion coupling"
        ret += "," + self.links[0].string()
        if self.proportional:
            ret += ",\n\t\t\tproportional, " + FORMAT(self.factor)
        else:
            ret += "," + self.links[1].string()
        ret += ",\n\t\t\t" + FORMAT(self.coupling_coefficient)
        return ret

class LinearViscoelasticGenericAxialTorsionCouplingOperator(Base):
    bl_label = "Linear viscoelastic generic axial torsion coupling"
    dimension_items = [("6D", "6D", "")]
    dimension = bpy.props.EnumProperty(items=dimension_items, name="Dimension")
    coupling_coefficient = bpy.props.FloatProperty(name="Coupling coefficient", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    stiffness_matrix_6x1_name = bpy.props.EnumProperty(items=enum_matrix_6x1, name="Stiffness",
        update=lambda self, context: update_matrix(self, context, self.stiffness_matrix_6x1_name, "6x1"))
    proportional = bpy.props.BoolProperty(name="Proportional", default=False)
    factor = bpy.props.FloatProperty(name="Factor", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    viscosity_matrix_6x1_name = bpy.props.EnumProperty(items=enum_matrix_6x1, name="Viscosity",
        update=lambda self, context: update_matrix(self, context, self.viscosity_matrix_6x1_name, "6x1"))
    def assign(self, context):
        self.dimension = self.entity.dimension
        self.coupling_coefficient = self.entity.coupling_coefficient
        self.stiffness_matrix_6x1_name = self.entity.links[0].name
        self.proportional = self.entity.proportional
        self.factor = self.entity.factor
        if not self.proportional:
            self.stiffness_matrix_6x1_name = self.entity.links[1].name
    def store(self, context):
        self.entity.dimension = self.dimension
        self.entity.coupling_coefficient = self.coupling_coefficient
        self.entity.proportional = self.proportional
        self.entity.links.append(database.matrix.get_by_name(self.stiffness_matrix_6x1_name))
        self.entity.factor = self.factor
        if not self.proportional:
            self.entity.links.append(database.matrix.get_by_name(self.viscosity_matrix_6x1_name))
    def draw(self, context):
        self.basis = self.proportional
        layout = self.layout
        self.draw_dimension(layout)
        layout.prop(self, "stiffness_matrix_6x1_name")
        row = layout.row()
        row.prop(self, "proportional")
        if self.proportional:
            row.prop(self, "factor")
        else:
            layout.prop(self, "viscosity_matrix_6x1_name")
    def check(self, context):
        return self.basis != self.proportional
    def create_entity(self):
        return LinearViscoelasticGenericAxialTorsionCoupling(self.name)

klasses[LinearViscoelasticGenericAxialTorsionCouplingOperator.bl_label] = LinearViscoelasticGenericAxialTorsionCouplingOperator

class CubicViscoelasticGeneric(Entity):
    def string(self):
        ret = "cubic viscoelastic generic"
        if self.dimension == "1D":
            for stiffness in [self.stiffness_1, self.stiffness_2, self.stiffness_3]:
                ret += ", " + FORMAT(stiffness)
            ret += ", " + FORMAT(self.viscosity)
        else:
            for link in self.links:
                ret += "," + link.string()
        return ret

class CubicViscoelasticGenericOperator(Base):
    bl_label = "Cubic viscoelastic generic"
    dimension_items = [("1D", "1D", ""), ("3D", "3D", "")]
    dimension = bpy.props.EnumProperty(items=dimension_items, name="Dimension")
    stiffness_1 = bpy.props.FloatProperty(name="Stiffness 1", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    stiffness_2 = bpy.props.FloatProperty(name="Stiffness 2", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    stiffness_3 = bpy.props.FloatProperty(name="Stiffness 3", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    viscosity = bpy.props.FloatProperty(name="Viscosity", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    stiffness_matrix_3x1_1_name = bpy.props.EnumProperty(items=enum_matrix_3x1, name="Stiffness 1",
        update=lambda self, context: update_matrix(self, context, self.stiffness_matrix_3x1_1_name, "3x1"))
    stiffness_matrix_3x1_2_name = bpy.props.EnumProperty(items=enum_matrix_3x1, name="Stiffness 2",
        update=lambda self, context: update_matrix(self, context, self.stiffness_matrix_3x1_2_name, "3x1"))
    stiffness_matrix_3x1_3_name = bpy.props.EnumProperty(items=enum_matrix_3x1, name="Stiffness 3",
        update=lambda self, context: update_matrix(self, context, self.stiffness_matrix_3x1_3_name, "3x1"))
    viscosity_matrix_3x1_name = bpy.props.EnumProperty(items=enum_matrix_3x1, name="Viscosity",
        update=lambda self, context: update_matrix(self, context, self.viscosity_matrix_3x1_name, "3x1"))
    def assign(self, context):
        self.dimension = self.entity.dimension
        if self.dimension == "1D":
            self.stiffness_1 = self.entity.stiffness_1
            self.stiffness_2 = self.entity.stiffness_2
            self.stiffness_3 = self.entity.stiffness_3
            self.viscosity = self.entity.viscosity
        else:
            self.stiffness_matrix_3x1_1_name = self.entity.links[0].name
            self.stiffness_matrix_3x1_2_name = self.entity.links[1].name
            self.stiffness_matrix_3x1_3_name = self.entity.links[2].name
            self.viscosity_matrix_3x1_name = self.entity.links[3].name
    def store(self, context):
        self.entity.dimension = self.dimension
        if self.dimension == "1D":
            self.entity.stiffness_1 = self.stiffness_1
            self.entity.stiffness_2 = self.stiffness_2
            self.entity.stiffness_3 = self.stiffness_3
            self.entity.viscosity = self.viscosity
        else:
            for matrix_name in [self.stiffness_matrix_3x1_1_name, self.stiffness_matrix_3x1_2_name,
                self.stiffness_matrix_3x1_3_name, self.viscosity_matrix_3x1_name]:
                    self.entity.links.append(database.matrix.get_by_name(matrix_name))
    def draw(self, context):
        self.basis = self.dimension
        layout = self.layout
        self.draw_dimension(layout)
        if self.dimension == "1D":
            layout.prop(self, "stiffness_1")
            layout.prop(self, "stiffness_2")
            layout.prop(self, "stiffness_3")
            layout.prop(self, "viscosity")
        else:
            for c in "123":
                layout.prop(self, "stiffness_matrix_3x1_" + c + "_name")
            layout.prop(self, "viscosity_matrix_3x1_name")
    def check(self, context):
        return self.basis != self.dimension
    def create_entity(self):
        return CubicViscoelasticGeneric(self.name)

klasses[CubicViscoelasticGenericOperator.bl_label] = CubicViscoelasticGenericOperator

class DoubleLinearViscoelastic(Entity):
    def string(self):
        ret = "double linear viscoelastic"
        if self.dimension == "1D":
            ret += ", " + FORMAT(self.stiffness_1)
            ret += ", " + FORMAT(self.upper_strain) + ", " + FORMAT(self.lower_strain)
            ret += ", " + FORMAT(self.stiffness_2)
            ret += ", " + FORMAT(self.viscosity_1)
            if self.second_damping:
                ret += ", second damping, " + FORMAT(self.viscosity_1)
        else:
            ret += "," + self.links[0].string()
            ret += ",\n\t\t\t" + FORMAT(self.upper_strain) + ", " + FORMAT(self.lower_strain)
            ret += "," + self.links[1].string()
            ret += "," + self.links[2].string()
            if self.second_damping:
                ret += ", second damping, " + self.links[3].string()
        return ret

class DoubleLinearViscoelasticOperator(Base):
    bl_label = "Double linear viscoelastic"
    dimension_items = [("1D", "1D", ""), ("3D", "3D", "")]
    dimension = bpy.props.EnumProperty(items=dimension_items, name="Dimension")
    stiffness_1 = bpy.props.FloatProperty(name="Stiffness 1", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    stiffness_2 = bpy.props.FloatProperty(name="Stiffness 2", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    upper_strain = bpy.props.FloatProperty(name="Upper strain", description="", min=0.000001, max=9.9e10, precision=6)
    lower_strain = bpy.props.FloatProperty(name="Lower strain", description="", min=0.000001, max=9.9e10, precision=6)
    stiffness_matrix_3x1_1_name = bpy.props.EnumProperty(items=enum_matrix_3x1, name="Stiffness 1",
        update=lambda self, context: update_matrix(self, context, self.stiffness_matrix_3x1_1_name, "3x1"))
    stiffness_matrix_3x1_2_name = bpy.props.EnumProperty(items=enum_matrix_3x1, name="Stiffness 2",
        update=lambda self, context: update_matrix(self, context, self.stiffness_matrix_3x1_2_name, "3x1"))
    second_damping = bpy.props.BoolProperty("Second damping", default=False)
    viscosity_1 = bpy.props.FloatProperty(name="Viscosity 1", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    viscosity_2 = bpy.props.FloatProperty(name="Viscosity 2", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    viscosity_matrix_3x1_1_name = bpy.props.EnumProperty(items=enum_matrix_3x1, name="Viscosity 1",
        update=lambda self, context: update_matrix(self, context, self.viscosity_matrix_3x1_1_name, "3x1"))
    viscosity_matrix_3x1_2_name = bpy.props.EnumProperty(items=enum_matrix_3x1, name="Viscosity 2",
        update=lambda self, context: update_matrix(self, context, self.viscosity_matrix_3x1_2_name, "3x1"))
    def assign(self, context):
        self.dimension = self.entity.dimension
        self.upper_strain = self.entity.upper_strain
        self.lower_strain = self.entity.lower_strain
        self.second_damping = self.entity.second_damping
        if self.dimension == "1D":
            self.stiffness_1 = self.entity.stiffness_1
            self.stiffness_2 = self.entity.stiffness_2
            self.viscosity_1 = self.entity.viscosity_1
            self.viscosity_2 = self.entity.viscosity_2
        else:
            self.stiffness_matrix_3x1_1_name = self.entity.links[0].name
            self.stiffness_matrix_3x1_2_name = self.entity.links[1].name
            self.viscosity_matrix_3x1_1_name = self.entity.links[2].name
            if self.second_damping:
                self.viscosity_matrix_3x1_2_name = self.entity.links[3].name
    def store(self, context):
        self.entity.dimension = self.dimension
        self.entity.upper_strain = self.upper_strain
        self.entity.lower_strain = self.lower_strain
        self.entity.second_damping = self.second_damping
        if self.dimension == "1D":
            self.entity.stiffness_1 = self.stiffness_1
            self.entity.stiffness_2 = self.stiffness_2
            self.entity.viscosity_1 = self.viscosity_1
            self.entity.viscosity_2 = self.viscosity_2
        else:
            for matrix_name in [self.stiffness_matrix_3x1_1_name, self.stiffness_matrix_3x1_2_name, self.viscosity_matrix_3x1_1_name]:
                self.entity.links.append(database.matrix.get_by_name(matrix_name))
            if self.second_damping:
                self.entity.links.append(database.matrix.get_by_name(self.viscosity_matrix_3x1_2_name))
    def draw(self, context):
        self.basis = (self.dimension, self.second_damping)
        layout = self.layout
        self.draw_dimension(layout)
        if self.dimension == "1D":
            layout.prop(self, "stiffness_1")
            layout.prop(self, "stiffness_2")
            layout.prop(self, "viscosity_1")
            row = layout.row()
            row.prop(self, "second_damping")
            if self.second_damping:
                row.prop(self, "viscosity_2")
        else:
            for c in "12":
                layout.prop(self, "stiffness_matrix_3x1_" + c + "_name")
            layout.prop(self, "viscosity_matrix_3x1_1_name")
            row = layout.row()
            row.prop(self, "second_damping")
            if self.second_damping:
                row.prop(self, "viscosity_matrix_3x1_2_name")
        layout.prop(self, "upper_strain")
        layout.prop(self, "lower_strain")
    def check(self, context):
        return self.basis != (self.dimension, self.second_damping)
    def create_entity(self):
        return DoubleLinearViscoelastic(self.name)

klasses[DoubleLinearViscoelasticOperator.bl_label] = DoubleLinearViscoelasticOperator

class TurbulentViscoelastic(Entity):
    def string(self):
        ret = "turbulent viscoelastic, " + FORMAT(self.stiffness) + ", " + FORMAT(self.parabolic_viscosity)
        if self.use_threshold:
            ret += ", " + FORMAT(self.threshold)
            if self.use_linear_viscosity:
                ret += ", " + FORMAT(self.linear_viscosity)
        return ret

class TurbulentViscoelasticOperator(Base):
    bl_label = "Turbulent viscoelastic"
    dimension_items = [("1D", "1D", ""), ]
    dimension = bpy.props.EnumProperty(items=dimension_items, name="Dimension")
    stiffness = bpy.props.FloatProperty(name="Stiffness", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    parabolic_viscosity = bpy.props.FloatProperty(name="Parabolic viscosity", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    use_threshold = bpy.props.BoolProperty("Use threshold", default=False)
    threshold = bpy.props.FloatProperty(name="Threshold", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    use_linear_viscosity = bpy.props.BoolProperty("Use linear viscosity", default=False)
    linear_viscosity = bpy.props.FloatProperty(name="Linear viscosity", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    def assign(self, context):
        self.dimension = self.entity.dimension
        self.stiffness = self.entity.stiffness
        self.parabolic_viscosity = self.entity.parabolic_viscosity
        self.use_threshold = self.entity.use_threshold
        self.threshold = self.entity.threshold
        self.use_linear_viscosity = self.entity.use_linear_viscosity
        self.linear_viscosity = self.entity.linear_viscosity
    def store(self, context):
        self.entity.dimension = self.dimension
        self.entity.stiffness = self.stiffness
        self.entity.parabolic_viscosity = self.parabolic_viscosity
        self.entity.use_threshold = self.use_threshold
        self.entity.threshold = self.threshold
        self.entity.use_linear_viscosity = self.use_linear_viscosity
        self.entity.linear_viscosity = self.linear_viscosity
    def draw(self, context):
        self.basis = (self.dimension, self.use_threshold, self.use_linear_viscosity)
        layout = self.layout
        self.draw_dimension(layout)
        layout.prop(self, "stiffness")
        layout.prop(self, "parabolic_viscosity")
        layout.prop(self, "use_threshold")
        if self.use_threshold:
            layout.prop(self, "threshold")
            layout.prop(self, "use_linear_viscosity")
            if self.use_linear_viscosity:
                layout.prop(self, "linear_viscosity")
    def check(self, context):
        return self.basis != (self.dimension, self.use_threshold, self.use_linear_viscosity)
    def create_entity(self):
        return TurbulentViscoelastic(self.name)

klasses[TurbulentViscoelasticOperator.bl_label] = TurbulentViscoelasticOperator

class LinearViscoelasticBistop(Entity):
    def string(self):
        ret = "linear viscoelastic bistop"
        if self.dimension == "1D":
            ret += ",\n\t\t\t" + FORMAT(self.stiffness) + ", " + FORMAT(self.viscosity)
        else:
            ret += ", " + self.links[2].string() + ", " + self.links[3].string()
        ret += ",\n\t\t\tinitial status, " + self.initial_status
        for link in self.links[:2]:
            ret += ",\n\t\t\t" + link.string()
        return ret

class LinearViscoelasticBistopOperator(Base):
    bl_label = "Linear viscoelastic bistop"
    dimension_items = [("1D", "1D", ""), ("3D", "3D", ""), ("6D", "6D", "")]
    dimension = bpy.props.EnumProperty(items=dimension_items, name="Dimension")
    stiffness = bpy.props.FloatProperty(name="Stiffness", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    stiffness_matrix_3x3_name = bpy.props.EnumProperty(items=enum_matrix_3x3, name="Stiffness",
        update=lambda self, context: update_matrix(self, context, self.stiffness_matrix_3x3_name, "3x3"))
    stiffness_matrix_6x6_name = bpy.props.EnumProperty(items=enum_matrix_6x6, name="Stiffness",
        update=lambda self, context: update_matrix(self, context, self.stiffness_matrix_6x6_name, "6x6"))
    viscosity = bpy.props.FloatProperty(name="Viscosity", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    viscosity_matrix_3x3_name = bpy.props.EnumProperty(items=enum_matrix_3x3, name="Viscosity",
        update=lambda self, context: update_matrix(self, context, self.viscosity_matrix_3x3_name, "3x3"))
    viscosity_matrix_6x6_name = bpy.props.EnumProperty(items=enum_matrix_6x6, name="Viscosity",
        update=lambda self, context: update_matrix(self, context, self.viscosity_matrix_6x6_name, "6x6"))
    initial_status = bpy.props.EnumProperty(items=[("active", "Active", ""), ("inactive", "Inactive", "")], name="Initial status")
    activating_condition_name = bpy.props.EnumProperty(items=enum_drive, name="Activating condition",
        update=lambda self, context: update_drive(self, context, self.activating_condition_name))
    deactivating_condition_name = bpy.props.EnumProperty(items=enum_drive, name="Deactivating condition",
        update=lambda self, context: update_drive(self, context, self.deactivating_condition_name))
    def assign(self, context):
        self.dimension = self.entity.dimension
        self.initial_status = self.entity.initial_status
        self.activating_condition_name = self.entity.links[0].name
        self.deactivating_condition_name = self.entity.links[1].name
        if self.dimension == "1D":
            self.stiffness = self.entity.stiffness
            self.viscosity = self.entity.viscosity
        elif self.dimension == "3D":
            self.stiffness_matrix_3x3_name = self.entity.links[2].name
            self.viscosity_matrix_3x3_name = self.entity.links[3].name
        else:
            self.stiffness_matrix_6x6_name = self.entity.links[2].name
            self.viscosity_matrix_6x6_name = self.entity.links[3].name
    def store(self, context):
        self.entity.dimension = self.dimension
        self.entity.initial_status = self.initial_status
        self.entity.links.append(database.drive.get_by_name(self.activating_condition_name))
        self.entity.links.append(database.drive.get_by_name(self.deactivating_condition_name))
        if self.dimension == "1D":
            self.entity.stiffness = self.stiffness
            self.entity.viscosity = self.viscosity
        else:
            if self.dimension == "3D":
                self.entity.links.append(database.matrix.get_by_name(self.stiffness_matrix_3x3_name))
                self.entity.links.append(database.matrix.get_by_name(self.viscosity_matrix_3x3_name))
            else:
                self.entity.links.append(database.matrix.get_by_name(self.stiffness_matrix_6x6_name))
                self.entity.links.append(database.matrix.get_by_name(self.viscosity_matrix_6x6_name))
    def draw(self, context):
        self.basis = self.dimension
        layout = self.layout
        self.draw_dimension(layout)
        if self.dimension == "1D":
            layout.prop(self, "stiffness")
            layout.prop(self, "viscosity")
        elif self.dimension == "3D":
            for s in "stiffness viscosity".split():
                layout.prop(self, s + "_matrix_3x3_name")
        else:
            for s in "stiffness viscosity".split():
                layout.prop(self, s + "_matrix_6x6_name")
        layout.prop(self, "initial_status")
        for s in "activating deactivating".split():
            layout.prop(self, s+ "_condition_name")
    def check(self, context):
        return self.basis != self.dimension
    def create_entity(self):
        return LinearViscoelasticBistop(self.name)

klasses[LinearViscoelasticBistopOperator.bl_label] = LinearViscoelasticBistopOperator

for dimension in "1D 3D 6D".split():
    class Menu(bpy.types.Menu):
        bl_label = tree[0] + " " + dimension
        bl_idname = root_dot + "_".join(tree[0].lower().split()) + dimension
        def draw(self, context):
            layout = self.layout
            layout.operator_context = 'INVOKE_DEFAULT'
            for key in types:
                if [d for d in klasses[key].dimension_items if dimension in d[0]]:
                    op = layout.operator(root_dot + "c_" + "_".join(key.lower().split()))
                    op.dimension = dimension
    BPY.klasses.append(Menu)
