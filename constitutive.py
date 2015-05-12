# --------------------------------------------------------------------------
# Blender MBDyn
# Copyright (C) 2015 G. Douglas Baldwin - http://www.baldwintechnology.com
# --------------------------------------------------------------------------
# ***** BEGIN GPL LICENSE BLOCK *****
#
#    This file is part of Blender MBDyn.
#
#    Blender MBDyn is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Blender MBDyn is distributed in the hope that it will be useful,
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
    from .base import bpy, root_dot, Operator, Entity, Props, enum_drive, enum_function, enum_matrix_3x1, enum_matrix_6x1, enum_matrix_3x3, enum_matrix_6x6, enum_matrix_6xN 

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

tree = ["Add Constitutive", types]

classes = dict()

class Base(Operator):
    bl_label = "Constitutives"
    bl_options = {'DEFAULT_CLOSED'}
    @classmethod
    def make_list(self, ListItem):
        bpy.types.Scene.constitutive_uilist = bpy.props.CollectionProperty(type = ListItem)
        bpy.types.Scene.constitutive_index = bpy.props.IntProperty(default=-1)
    @classmethod
    def delete_list(self):
        del bpy.types.Scene.constitutive_uilist
        del bpy.types.Scene.constitutive_index
    @classmethod
    def get_uilist(self, context):
        return context.scene.constitutive_index, context.scene.constitutive_uilist
    def set_index(self, context, value):
        context.scene.constitutive_index = value
    def draw_dimensions(self, layout):
        if self.bl_idname.endswith("c_" + "_".join(self.name.lower().split())):
            layout.prop(self, "dimensions")
        else:
            layout.label(self.dimensions)

for t in types:
    class Tester(Base):
        bl_label = t
        @classmethod
        def poll(cls, context):
            return False
        def defaults(self, context):
            pass
        def assign(self, context):
            self.entity = self.database.constitutive[context.scene.constitutive_index]
        def store(self, context):
            self.entity = self.database.constitutive[context.scene.constitutive_index]
        def create_entity(self):
            return Entity(self.name)
    classes[t] = Tester

class LinearElastic(Entity):
    def string(self):
        if self.dimensions == "1D":
            return "linear elastic, "+str(self.stiffness)
        else:
            return "linear elastic isotropic, "+str(self.stiffness)

class LinearElasticOperator(Base):
    bl_label = "Linear elastic"
    dimensions = bpy.props.EnumProperty(items=[("1D", "1D", ""), ("3D, 6D", "3D, 6D", "")], name="Dimension(s)")
    stiffness = bpy.props.FloatProperty(name="Stiffness", description="", min=0.000001, max=9.9e10, precision=6)
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.stiffness = 1.0
    def assign(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.stiffness = self.entity.stiffness
        self.dimensions = self.entity.dimensions
    def store(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.entity.stiffness = self.stiffness
        self.entity.dimensions = self.dimensions
    def draw(self, context):
        layout = self.layout
        self.draw_dimensions(layout)
        layout.prop(self, "stiffness")
    def create_entity(self):
        return LinearElastic(self.name)

classes[LinearElasticOperator.bl_label] = LinearElasticOperator

class LinearElasticGeneric(Entity):
    def string(self):
        if self.dimensions == "1D":
            return "linear elastic generic, " + str(self.stiffness)
        else:
            return "linear elastic generic, " + self.links[0].string()

class LinearElasticGenericOperator(Base):
    bl_label = "Linear elastic generic"
    dimensions = bpy.props.EnumProperty(items=[("1D", "1D", ""), ("3D", "3D", ""), ("6D", "6D", "")], name="Dimension(s)")
    stiffness = bpy.props.FloatProperty(name="Stiffness", description="", min=0.000001, max=9.9e10, precision=6)
    stiffness_matrix_3x3_name = bpy.props.EnumProperty(items=enum_matrix_3x3, name="Stiffness")
    stiffness_matrix_6x6_name = bpy.props.EnumProperty(items=enum_matrix_6x6, name="Stiffness")
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.stiffness = 1.0
        self.matrix_exists(context, "3x3")
        self.matrix_exists(context, "6x6")
    def assign(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.dimensions = self.entity.dimensions
        if self.dimensions == "1D":
            self.stiffness = self.entity.stiffness
        elif self.dimensions == "3D":
            self.stiffness_matrix_3x3_name = self.entity.links[0].name
        else:
            self.stiffness_matrix_6x6_name = self.entity.links[0].name
    def store(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.entity.dimensions = self.dimensions
        if self.dimensions == "1D":
            self.entity.stiffness = self.stiffness
        else:
            self.entity.unlink_all()
            if self.dimensions == "3D":
                self.link_matrix(context, self.stiffness_matrix_3x3_name)
            else:
                self.link_matrix(context, self.stiffness_matrix_6x6_name)
            self.entity.increment_links()
    def draw(self, context):
        self.basis = self.dimensions
        layout = self.layout
        self.draw_dimensions(layout)
        if self.dimensions == "1D":
            layout.prop(self, "stiffness")
        elif self.dimensions == "3D":
            layout.prop(self, "stiffness_matrix_3x3_name")
        else:
            layout.prop(self, "stiffness_matrix_6x6_name")
    def check(self, context):
        return self.basis != self.dimensions
    def create_entity(self):
        return LinearElasticGeneric(self.name)

classes[LinearElasticGenericOperator.bl_label] = LinearElasticGenericOperator

class LinearElasticGenericAxialTorsionCoupling(Entity):
    def string(self):
        return "linear elastic generic axial torsion coupling," + self.links[0].string() + ",\n\t\t\t" + str(self.coupling_coefficient)
                
class LinearElasticGenericAxialTorsionCouplingOperator(Base):
    bl_label = "Linear elastic generic axial torsion coupling"
    dimensions = bpy.props.EnumProperty(items=[("6D", "6D", "")], name="Dimension(s)")
    coupling_coefficient = bpy.props.FloatProperty(name="Coupling coefficient", description="", min=0.000001, max=9.9e10, precision=6)
    stiffness_matrix_6x1_name = bpy.props.EnumProperty(items=enum_matrix_6x1, name="Stiffness")
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.coupling_coefficient = 1.0
        self.matrix_exists(context, "6x1")
    def assign(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.dimensions = self.entity.dimensions
        self.coupling_coefficient = self.entity.coupling_coefficient
        self.stiffness_matrix_6x1_name = self.entity.links[0].name
    def store(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.entity.dimensions = self.dimensions
        self.entity.coupling_coefficient = self.coupling_coefficient
        self.entity.unlink_all()
        self.link_matrix(context, self.stiffness_matrix_6x1_name)
        self.entity.increment_links()
    def draw(self, context):
        self.basis = self.dimensions
        layout = self.layout
        self.draw_dimensions(layout)
        layout.prop(self, "coupling_coefficient")
        layout.prop(self, "stiffness_matrix_6x1_name")
    def create_entity(self):
        return LinearElasticGenericAxialTorsionCoupling(self.name)

classes[LinearElasticGenericAxialTorsionCouplingOperator.bl_label] = LinearElasticGenericAxialTorsionCouplingOperator

class CubicElasticGeneric(Entity):
    def string(self):
        ret = "cubic elastic generic"
        if self.dimensions == "1D":
            for stiffness in [self.stiffness_1, self.stiffness_2, self.stiffness_3]:
                ret += ", " + str(stiffness)
        else:
            for link in self.links:
                ret += "," + link.string()
        return ret

class CubicElasticGenericOperator(Base):
    bl_label = "Cubic elastic generic"
    dimensions = bpy.props.EnumProperty(items=[("1D", "1D", ""), ("3D", "3D", "")], name="Dimension(s)")
    stiffness_1 = bpy.props.FloatProperty(name="Stiffness 1", description="", min=0.000001, max=9.9e10, precision=6)
    stiffness_2 = bpy.props.FloatProperty(name="Stiffness 2", description="", min=0.000001, max=9.9e10, precision=6)
    stiffness_3 = bpy.props.FloatProperty(name="Stiffness 3", description="", min=0.000001, max=9.9e10, precision=6)
    stiffness_matrix_3x1_1_name = bpy.props.EnumProperty(items=enum_matrix_3x1, name="Stiffness 1")
    stiffness_matrix_3x1_2_name = bpy.props.EnumProperty(items=enum_matrix_3x1, name="Stiffness 2")
    stiffness_matrix_3x1_3_name = bpy.props.EnumProperty(items=enum_matrix_3x1, name="Stiffness 3")
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.stiffness_1 = 1.0
        self.stiffness_2 = 1.0
        self.stiffness_3 = 1.0
        self.matrix_exists(context, "3x1")
    def assign(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.dimensions = self.entity.dimensions
        if self.dimensions == "1D":
            self.stiffness_1 = self.entity.stiffness_1
            self.stiffness_2 = self.entity.stiffness_2
            self.stiffness_3 = self.entity.stiffness_3
        else:
            self.stiffness_matrix_3x1_1_name = self.entity.links[0].name
            self.stiffness_matrix_3x1_2_name = self.entity.links[1].name
            self.stiffness_matrix_3x1_3_name = self.entity.links[2].name
    def store(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.entity.dimensions = self.dimensions
        if self.dimensions == "1D":
            self.entity.stiffness_1 = self.stiffness_1
            self.entity.stiffness_2 = self.stiffness_2
            self.entity.stiffness_3 = self.stiffness_3
        else:
            self.entity.unlink_all()
            self.link_matrix(context, self.stiffness_matrix_3x1_1_name)
            self.link_matrix(context, self.stiffness_matrix_3x1_2_name)
            self.link_matrix(context, self.stiffness_matrix_3x1_3_name)
            self.entity.increment_links()
    def draw(self, context):
        self.basis = self.dimensions
        layout = self.layout
        self.draw_dimensions(layout)
        if self.dimensions == "1D":
            layout.prop(self, "stiffness_1")
            layout.prop(self, "stiffness_2")
            layout.prop(self, "stiffness_3")
        else:
            layout.prop(self, "stiffness_matrix_3x1_1_name")
            layout.prop(self, "stiffness_matrix_3x1_2_name")
            layout.prop(self, "stiffness_matrix_3x1_3_name")
    def check(self, context):
        return self.basis != self.dimensions
    def create_entity(self):
        return CubicElasticGeneric(self.name)

classes[CubicElasticGenericOperator.bl_label] = CubicElasticGenericOperator

class InverseSquareElastic(Entity):
    def string(self):
        return "inverse square elastic, " + str(self.stiffness) + ", " + str(self.ref_length)

class InverseSquareElasticOperator(Base):
    bl_label = "Inverse square elastic"
    dimensions = bpy.props.EnumProperty(items=[("1D", "1D", ""), ], name="Dimension(s)")
    stiffness = bpy.props.FloatProperty(name="Stiffness", description="", min=0.000001, max=9.9e10, precision=6)
    ref_length = bpy.props.FloatProperty(name="Reference length", description="", min=0.000001, max=9.9e10, precision=6)
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.stiffness = 1.0
        self.ref_length = 1.0
    def assign(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.stiffness = self.entity.stiffness
        self.ref_length = self.entity.ref_length
        self.dimensions = self.entity.dimensions
    def store(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.entity.stiffness = self.stiffness
        self.entity.ref_length = self.ref_length
        self.entity.dimensions = self.dimensions
    def draw(self, context):
        layout = self.layout
        self.draw_dimensions(layout)
        layout.prop(self, "stiffness")
        layout.prop(self, "ref_length")
    def create_entity(self):
        return InverseSquareElastic(self.name)

classes[InverseSquareElasticOperator.bl_label] = InverseSquareElasticOperator

class LogElastic(Entity):
    def string(self):
        return "log elastic, " + str(self.stiffness)

class LogElasticOperator(Base):
    bl_label = "Log elastic"
    dimensions = bpy.props.EnumProperty(items=[("1D", "1D", ""), ], name="Dimension(s)")
    stiffness = bpy.props.FloatProperty(name="Stiffness", description="", min=0.000001, max=9.9e10, precision=6)
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.stiffness = 1.0
    def assign(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.stiffness = self.entity.stiffness
        self.dimensions = self.entity.dimensions
    def store(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.entity.stiffness = self.stiffness
        self.entity.dimensions = self.dimensions
    def draw(self, context):
        layout = self.layout
        self.draw_dimensions(layout)
        layout.prop(self, "stiffness")
    def create_entity(self):
        return LogElastic(self.name)

classes[LogElasticOperator.bl_label] = LogElasticOperator

class LinearElasticBistop(Entity):
    def string(self):
        ret = "linear elastic bistop"
        if self.dimensions == "1D":
            ret += ",\n\t\t\t" + str(self.stiffness)
        else:
            ret += ", " + self.links[2].string()
        ret += ",\n\t\t\tinitial status, " + self.initial_status
        for link in self.links[:2]:
            ret += ",\n\t\t\t" + link.string()
        return ret

class LinearElasticBistopOperator(Base):
    bl_label = "Linear elastic bistop"
    dimensions = bpy.props.EnumProperty(items=[("1D", "1D", ""), ("3D", "3D", ""), ("6D", "6D", "")], name="Dimension(s)")
    stiffness = bpy.props.FloatProperty(name="Stiffness", description="", min=0.000001, max=9.9e10, precision=6)
    stiffness_matrix_3x3_name = bpy.props.EnumProperty(items=enum_matrix_3x3, name="Stiffness")
    stiffness_matrix_6x6_name = bpy.props.EnumProperty(items=enum_matrix_6x6, name="Stiffness")
    initial_status = bpy.props.EnumProperty(items=[("active", "Active", ""), ("inactive", "Inactive", "")], name="Initial status")
    activating_condition_name = bpy.props.EnumProperty(items=enum_drive, name="Activating condition")
    deactivating_condition_name = bpy.props.EnumProperty(items=enum_drive, name="Deactivating condition")
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.stiffness = 1.0
        self.matrix_exists(context, "3x3")
        self.matrix_exists(context, "6x6")
        self.drive_exists(context)
    def assign(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.dimensions = self.entity.dimensions
        self.initial_status = self.entity.initial_status
        self.activating_condition_name = self.entity.links[0].name
        self.deactivating_condition_name = self.entity.links[1].name
        if self.dimensions == "1D":
            self.stiffness = self.entity.stiffness
        elif self.dimensions == "3D":
            self.stiffness_matrix_3x3_name = self.entity.links[2].name
        else:
            self.stiffness_matrix_6x6_name = self.entity.links[2].name
    def store(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.entity.dimensions = self.dimensions
        self.entity.initial_status = self.initial_status
        self.entity.unlink_all()
        self.link_drive(context, self.activating_condition_name)
        self.link_drive(context, self.deactivating_condition_name)
        if self.dimensions == "1D":
            self.entity.stiffness = self.stiffness
        else:
            if self.dimensions == "3D":
                self.link_matrix(context, self.stiffness_matrix_3x3_name)
            else:
                self.link_matrix(context, self.stiffness_matrix_6x6_name)
        self.entity.increment_links()
    def draw(self, context):
        self.basis = self.dimensions
        layout = self.layout
        self.draw_dimensions(layout)
        if self.dimensions == "1D":
            layout.prop(self, "stiffness")
        elif self.dimensions == "3D":
            layout.prop(self, "stiffness_matrix_3x3_name")
        else:
            layout.prop(self, "stiffness_matrix_6x6_name")
        layout.prop(self, "initial_status")
        layout.prop(self, "activating_condition_name")
        layout.prop(self, "deactivating_condition_name")
    def check(self, context):
        return self.basis != self.dimensions
    def create_entity(self):
        return LinearElasticBistop(self.name)

classes[LinearElasticBistopOperator.bl_label] = LinearElasticBistopOperator

class DoubleLinearElastic(Entity):
    def string(self):
        ret = "double linear elastic"
        if self.dimensions == "1D":
            ret += ", " + str(self.stiffness_1)
            ret += ", " + str(self.upper_strain) + ", " + str(self.lower_strain)
            ret += ", " + str(self.stiffness_2)
        else:
            ret += "," + self.links[0].string()
            ret += ",\n\t\t\t" + str(self.upper_strain) + ", " + str(self.lower_strain)
            ret += "," + self.links[1].string()
        return ret

class DoubleLinearElasticOperator(Base):
    bl_label = "Double linear elastic"
    dimensions = bpy.props.EnumProperty(items=[("1D", "1D", ""), ("3D", "3D", "")], name="Dimension(s)")
    stiffness_1 = bpy.props.FloatProperty(name="Stiffness 1", description="", min=0.000001, max=9.9e10, precision=6)
    stiffness_2 = bpy.props.FloatProperty(name="Stiffness 2", description="", min=0.000001, max=9.9e10, precision=6)
    upper_strain = bpy.props.FloatProperty(name="Upper strain", description="", min=0.000001, max=9.9e10, precision=6)
    lower_strain = bpy.props.FloatProperty(name="Lower strain", description="", min=0.000001, max=9.9e10, precision=6)
    stiffness_matrix_3x1_1_name = bpy.props.EnumProperty(items=enum_matrix_3x1, name="Stiffness 1")
    stiffness_matrix_3x1_2_name = bpy.props.EnumProperty(items=enum_matrix_3x1, name="Stiffness 2")
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.stiffness_1 = 1.0
        self.stiffness_2 = 1.0
        self.matrix_exists(context, "3x1")
    def assign(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.dimensions = self.entity.dimensions
        self.upper_strain = self.entity.upper_strain
        self.lower_strain = self.entity.lower_strain
        if self.dimensions == "1D":
            self.stiffness_1 = self.entity.stiffness_1
            self.stiffness_2 = self.entity.stiffness_2
        else:
            self.stiffness_matrix_3x1_1_name = self.entity.links[0].name
            self.stiffness_matrix_3x1_2_name = self.entity.links[1].name
    def store(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.entity.dimensions = self.dimensions
        self.entity.upper_strain = self.upper_strain
        self.entity.lower_strain = self.lower_strain
        if self.dimensions == "1D":
            self.entity.stiffness_1 = self.stiffness_1
            self.entity.stiffness_2 = self.stiffness_2
        else:
            self.entity.unlink_all()
            self.link_matrix(context, self.stiffness_matrix_3x1_1_name)
            self.link_matrix(context, self.stiffness_matrix_3x1_2_name)
            self.entity.increment_links()
    def draw(self, context):
        self.basis = self.dimensions
        layout = self.layout
        self.draw_dimensions(layout)
        if self.dimensions == "1D":
            layout.prop(self, "stiffness_1")
            layout.prop(self, "stiffness_2")
        else:
            layout.prop(self, "stiffness_matrix_3x1_1_name")
            layout.prop(self, "stiffness_matrix_3x1_2_name")
        layout.prop(self, "upper_strain")
        layout.prop(self, "lower_strain")
    def check(self, context):
        return self.basis != self.dimensions
    def create_entity(self):
        return DoubleLinearElastic(self.name)

classes[DoubleLinearElasticOperator.bl_label] = DoubleLinearElasticOperator

class IsotropicHardeningElastic(Entity):
    def string(self):
        ret = "isotropic hardening elastic"
        if self.dimensions == "1D":
            ret += ",\n\t\t\t" + str(self.stiffness)
        else:
            ret += ", " + self.links[0].string()
        ret += ",\n\t\t\t" + str(self.reference_strain)
        if self.use_linear_stiffness:
            ret += ", linear stiffness, " + str(self.linear_stiffness)
        return ret

class IsotropicHardeningElasticOperator(Base):
    bl_label = "Isotropic hardening elastic"
    dimensions = bpy.props.EnumProperty(items=[("1D", "1D", ""), ("3D", "3D", ""), ("6D", "6D", "")], name="Dimension(s)")
    stiffness = bpy.props.FloatProperty(name="Stiffness", description="", min=0.000001, max=9.9e10, precision=6)
    stiffness_matrix_3x3_name = bpy.props.EnumProperty(items=enum_matrix_3x3, name="Stiffness")
    stiffness_matrix_6x6_name = bpy.props.EnumProperty(items=enum_matrix_6x6, name="Stiffness")
    reference_strain = bpy.props.FloatProperty(name="Reference strain", description="", min=0.000001, max=9.9e10, precision=6)
    use_linear_stiffness = bpy.props.BoolProperty("Use linear stiffness")
    linear_stiffness = bpy.props.FloatProperty(name="Reference strain", description="", min=0.000001, max=9.9e10, precision=6)
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.stiffness = 1.0
        self.reference_strain = 1.0
        self.use_linear_stiffness = False
        self.linear_stiffness = 1.0
        self.matrix_exists(context, "3x3")
        self.matrix_exists(context, "6x6")
    def assign(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.dimensions = self.entity.dimensions
        self.reference_strain = self.entity.reference_strain
        self.use_linear_stiffness = self.entity.use_linear_stiffness
        self.linear_stiffness = self.entity.linear_stiffness
        if self.dimensions == "1D":
            self.stiffness = self.entity.stiffness
        elif self.dimensions == "3D":
            self.stiffness_matrix_3x3_name = self.entity.links[0].name
        else:
            self.stiffness_matrix_6x6_name = self.entity.links[0].name
    def store(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.entity.dimensions = self.dimensions
        self.entity.reference_strain = self.reference_strain
        self.entity.use_linear_stiffness = self.use_linear_stiffness
        self.entity.linear_stiffness = self.linear_stiffness
        if self.dimensions == "1D":
            self.entity.stiffness = self.stiffness
        else:
            self.entity.unlink_all()
            if self.dimensions == "3D":
                self.link_matrix(context, self.stiffness_matrix_3x3_name)
            else:
                self.link_matrix(context, self.stiffness_matrix_6x6_name)
            self.entity.increment_links()
    def draw(self, context):
        self.basis = (self.dimensions, self.use_linear_stiffness)
        layout = self.layout
        self.draw_dimensions(layout)
        if self.dimensions == "1D":
            layout.prop(self, "stiffness")
        elif self.dimensions == "3D":
            layout.prop(self, "stiffness_matrix_3x3_name")
        else:
            layout.prop(self, "stiffness_matrix_6x6_name")
        layout.prop(self, "reference_strain")
        layout.prop(self, "use_linear_stiffness")
        if self.use_linear_stiffness:
            layout.prop(self, "linear_stiffness")
    def check(self, context):
        return self.basis != (self.dimensions, self.use_linear_stiffness)
    def create_entity(self):
        return IsotropicHardeningElastic(self.name)

classes[IsotropicHardeningElasticOperator.bl_label] = IsotropicHardeningElasticOperator

class ScalarFunctionElasticIsotropic(Entity):
    def string(self):
        if self.dimensions == "1D":
            return "scalar function elastic, \"" + self.links[0].name + "\""
        else:
            return "scalar function elastic isotropic, \"" + self.links[0].name + "\""

class ScalarFunctionElasticIsotropicOperator(Base):
    bl_label = "Scalar function elastic isotropic"
    dimensions = bpy.props.EnumProperty(items=[("1D", "1D", ""), ("3D, 6D", "3D, 6D", "")], name="Dimension(s)")
    function_name = bpy.props.EnumProperty(items=enum_function, name="Function")
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.function_exists(context)
    def assign(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.dimensions = self.entity.dimensions
        self.function_name = self.entity.links[0].name
    def store(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.entity.dimensions = self.dimensions
        self.entity.unlink_all()
        self.link_function(context, self.function_name)
        self.entity.increment_links()
    def draw(self, context):
        layout = self.layout
        self.draw_dimensions(layout)
        layout.prop(self, "function_name")
    def create_entity(self):
        return ScalarFunctionElasticIsotropic(self.name)

classes[ScalarFunctionElasticIsotropicOperator.bl_label] = ScalarFunctionElasticIsotropicOperator

class ScalarFunctionElasticOrthotropic(Entity):
    def string(self):
        ret = "scalar function elastic"
        if self.dimensions != "1D":
            ret += " orthotropic"
        for i in range(int(self.dimensions[0])):
            if self.is_null[i]:
                ret += ",\n\t\t\tnull"
            else:
                ret += ",\n\t\t\t\"" + self.links[i].name + "\""
        return ret

class ScalarFunctionElasticOrthotropicOperator(Base):
    bl_label = "Scalar function elastic orthotropic"
    dimensions = bpy.props.EnumProperty(items=[("1D", "1D", ""), ("3D", "3D", ""), ("6D", "6D", "")], name="Dimension(s)")
    is_null = bpy.props.BoolVectorProperty(size=6, name="Null")
    function_names = bpy.props.CollectionProperty(type = Props.FunctionNames, name="Functions")
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.function_exists(context)
        for i in range(6):
            self.function_names.add()
    def assign(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.dimensions = self.entity.dimensions
        self.is_null = self.entity.is_null
        for i in range(6):
            self.function_names.add()
        for i, link in enumerate(self.entity.links):
            self.function_names[i].value = link.name
    def store(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.entity.dimensions = self.dimensions
        self.entity.is_null = [v for v in self.is_null]
        self.entity.unlink_all()
        for f in self.function_names[:int(self.dimensions[0])]:
            self.link_function(context, f.value)
        self.entity.increment_links()
    def draw(self, context):
        self.basis = (self.dimensions, [v for v in self.is_null])
        layout = self.layout
        self.draw_dimensions(layout)
        for i in range(int(self.dimensions[0])):
            row = layout.row()
            row.prop(self, "is_null", index=i)
            if not self.is_null[i]:
                row.prop(self.function_names[i], "value", text="")
    def check(self, context):
        return self.basis[0] != self.dimensions or [True for i, v in enumerate(self.basis[1]) if v != self.is_null[i]]
    def create_entity(self):
        return ScalarFunctionElasticOrthotropic(self.name)

classes[ScalarFunctionElasticOrthotropicOperator.bl_label] = ScalarFunctionElasticOrthotropicOperator

class LinearViscous(Entity):
    def string(self):
        if self.dimensions == "1D":
            return "linear viscous, " + str(self.viscosity)
        else:
            return "linear viscous isotropic, " + str(self.viscosity)

class LinearViscousOperator(Base):
    bl_label = "Linear viscous"
    dimensions = bpy.props.EnumProperty(items=[("1D", "1D", ""), ("3D, 6D", "3D, 6D", "")], name="Dimension(s)")
    viscosity = bpy.props.FloatProperty(name="Viscosity", description="", min=0.000001, max=9.9e10, precision=6)
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.viscosity = 1.0
    def assign(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.viscosity = self.entity.viscosity
        self.dimensions = self.entity.dimensions
    def store(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.entity.viscosity = self.viscosity
        self.entity.dimensions = self.dimensions
    def draw(self, context):
        layout = self.layout
        self.draw_dimensions(layout)
        layout.prop(self, "viscosity")
    def create_entity(self):
        return LinearViscous(self.name)

classes[LinearViscousOperator.bl_label] = LinearViscousOperator

class LinearViscousGeneric(Entity):
    def string(self):
        if self.dimensions == "1D":
            return "linear viscous generic, " + str(self.viscosity)
        else:
            return "linear viscous generic, " + self.links[0].string()

class LinearViscousGenericOperator(Base):
    bl_label = "Linear viscous generic"
    dimensions = bpy.props.EnumProperty(items=[("1D", "1D", ""), ("3D", "3D", ""), ("6D", "6D", "")], name="Dimension(s)")
    viscosity = bpy.props.FloatProperty(name="Viscosity", description="", min=0.000001, max=9.9e10, precision=6)
    viscosity_matrix_3x3_name = bpy.props.EnumProperty(items=enum_matrix_3x3, name="Viscosity")
    viscosity_matrix_6x6_name = bpy.props.EnumProperty(items=enum_matrix_6x6, name="Viscosity")
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.viscosity = 1.0
        self.matrix_exists(context, "3x3")
        self.matrix_exists(context, "6x6")
    def assign(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.dimensions = self.entity.dimensions
        if self.dimensions == "1D":
            self.viscosity = self.entity.viscosity
        elif self.dimensions == "3D":
            self.viscosity_matrix_3x3_name = self.entity.links[0].name
        else:
            self.viscosity_matrix_6x6_name = self.entity.links[0].name
    def store(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.entity.dimensions = self.dimensions
        if self.dimensions == "1D":
            self.entity.viscosity = self.viscosity
        else:
            self.entity.unlink_all()
            if self.dimensions == "3D":
                self.link_matrix(context, self.viscosity_matrix_3x3_name)
            else:
                self.link_matrix(context, self.viscosity_matrix_6x6_name)
            self.entity.increment_links()
    def draw(self, context):
        self.basis = self.dimensions
        layout = self.layout
        self.draw_dimensions(layout)
        if self.dimensions == "1D":
            layout.prop(self, "viscosity")
        elif self.dimensions == "3D":
            layout.prop(self, "viscosity_matrix_3x3_name")
        else:
            layout.prop(self, "viscosity_matrix_6x6_name")
    def check(self, context):
        return self.basis != self.dimensions
    def create_entity(self):
        return LinearViscousGeneric(self.name)

classes[LinearViscousGenericOperator.bl_label] = LinearViscousGenericOperator

class LinearViscoelastic(Entity):
    def string(self):
        ret = "linear viscoelastic"
        if self.dimensions == "1D":
            ret += ", " + str(self.stiffness)
        else:
            ret += " isotropic, " + str(self.stiffness)
        if self.proportional:
            ret += ", proportional, " + str(self.factor)
        else:
            ret += ", " + str(self.viscosity)
        return ret

class LinearViscoelasticOperator(Base):
    bl_label = "Linear viscoelastic"
    dimensions = bpy.props.EnumProperty(items=[("1D", "1D", ""), ("3D, 6D", "3D, 6D", "")], name="Dimension(s)")
    stiffness = bpy.props.FloatProperty(name="Stiffness", description="", min=0.000001, max=9.9e10, precision=6)
    proportional = bpy.props.BoolProperty(name="Proportional")
    factor = bpy.props.FloatProperty(name="Factor", description="", min=0.000001, max=9.9e10, precision=6)
    viscosity = bpy.props.FloatProperty(name="Viscosity", description="", min=0.000001, max=9.9e10, precision=6)
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.stiffness = 1.0
        self.proportional = False
        self.factor = 1.0
        self.viscosity = 1.0
    def assign(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.dimensions = self.entity.dimensions
        self.stiffness = self.entity.stiffness
        self.proportional = self.entity.proportional
        self.factor = self.entity.factor
        self.viscosity = self.entity.viscosity
    def store(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.entity.dimensions = self.dimensions
        self.entity.stiffness = self.stiffness
        self.entity.proportional = self.proportional
        self.entity.factor = self.factor
        self.entity.viscosity = self.viscosity
    def draw(self, context):
        self.basis = self.proportional
        layout = self.layout
        self.draw_dimensions(layout)
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

classes[LinearViscoelasticOperator.bl_label] = LinearViscoelasticOperator

class LinearViscoelasticGeneric(Entity):
    def string(self):
        ret = "linear viscoelastic generic"
        if self.dimensions == "1D":
            ret += ", " + str(self.stiffness)
        else:
            ret += ", " + self.links[0].string()
        if self.proportional:
            ret += ", proportional, " + str(self.factor)
        else:
            if self.dimensions == "1D":
                ret += ", " + str(self.viscosity)
            else:
                ret += ", " + self.links[1].string()
        return ret

class LinearViscoelasticGenericOperator(Base):
    bl_label = "Linear viscoelastic generic"
    dimensions = bpy.props.EnumProperty(items=[("1D", "1D", ""), ("3D", "3D", ""), ("6D", "6D", "")], name="Dimension(s)")
    stiffness = bpy.props.FloatProperty(name="Stiffness", description="", min=0.000001, max=9.9e10, precision=6)
    stiffness_matrix_3x3_name = bpy.props.EnumProperty(items=enum_matrix_3x3, name="Stiffness")
    stiffness_matrix_6x6_name = bpy.props.EnumProperty(items=enum_matrix_6x6, name="Stiffness")
    proportional = bpy.props.BoolProperty(name="Proportional")
    factor = bpy.props.FloatProperty(name="Factor", description="", min=0.000001, max=9.9e10, precision=6)
    viscosity = bpy.props.FloatProperty(name="Viscosity", description="", min=0.000001, max=9.9e10, precision=6)
    viscosity_matrix_3x3_name = bpy.props.EnumProperty(items=enum_matrix_3x3, name="Viscosity")
    viscosity_matrix_6x6_name = bpy.props.EnumProperty(items=enum_matrix_6x6, name="Viscosity")
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.stiffness = 1.0
        self.proportional = False
        self.factor = 1.0
        self.matrix_exists(context, "3x3")
        self.matrix_exists(context, "6x6")
    def assign(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.dimensions = self.entity.dimensions
        self.proportional = self.entity.proportional
        self.factor = self.entity.factor
        if self.dimensions == "1D":
            self.stiffness = self.entity.stiffness
            if not self.proportional:
                self.viscosity = self.entity.viscosity
        elif self.dimensions == "3D":
            self.stiffness_matrix_3x3_name = self.entity.links[0].name
            if not self.proportional:
                self.viscosity_matrix_3x3_name = self.entity.links[1].name
        else:
            self.stiffness_matrix_6x6_name = self.entity.links[0].name
            if not self.proportional:
                self.viscosity_matrix_6x6_name = self.entity.links[1].name
    def store(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.entity.dimensions = self.dimensions
        self.entity.proportional = self.proportional
        self.entity.factor = self.factor
        if self.dimensions == "1D":
            self.entity.stiffness = self.stiffness
            if not self.proportional:
                self.entity.viscosity = self.viscosity
        else:
            self.entity.unlink_all()
            if self.dimensions == "3D":
                self.link_matrix(context, self.stiffness_matrix_3x3_name)
                if not self.proportional:
                    self.link_matrix(context, self.viscosity_matrix_3x3_name)
            else:
                self.link_matrix(context, self.stiffness_matrix_6x6_name)
                if not self.proportional:
                    self.link_matrix(context, self.viscosity_matrix_6x6_name)
            self.entity.increment_links()
    def draw(self, context):
        self.basis = (self.dimensions, self.proportional)
        layout = self.layout
        self.draw_dimensions(layout)
        if self.dimensions == "1D":
            layout.prop(self, "stiffness")
        elif self.dimensions == "3D":
            layout.prop(self, "stiffness_matrix_3x3_name")
        else:
            layout.prop(self, "stiffness_matrix_6x6_name")
        row = layout.row()
        row.prop(self, "proportional")
        if self.proportional:
            row.prop(self, "factor")
        else:
            if self.dimensions == "1D":
                layout.prop(self, "viscosity")
            elif self.dimensions == "3D":
                layout.prop(self, "viscosity_matrix_3x3_name")
            else:
                layout.prop(self, "viscosity_matrix_6x6_name")
    def check(self, context):
        return self.basis != (self.dimensions, self.proportional)
    def create_entity(self):
        return LinearViscoelasticGeneric(self.name)

classes[LinearViscoelasticGenericOperator.bl_label] = LinearViscoelasticGenericOperator

class LinearTimeVariantViscoelasticGeneric(Entity):
    def string(self):
        ret = "linear time variant viscoelastic generic"
        if self.dimensions == "1D":
            ret += ", " + str(self.stiffness)
        else:
            ret += ", " + self.links[2].string()
        ret += ", " + self.links[0].string()
        if self.proportional:
            ret += ", proportional, " + str(self.factor)
        else:
            if self.dimensions == "1D":
                ret += ", " + str(self.viscosity)
            else:
                ret += ", " + self.links[3].string()
        ret += ", " + self.links[1].string()
        return ret

class LinearTimeVariantViscoelasticGenericOperator(Base):
    bl_label = "Linear time variant viscoelastic generic"
    dimensions = bpy.props.EnumProperty(items=[("1D", "1D", ""), ("3D", "3D", ""), ("6D", "6D", "")], name="Dimension(s)")
    stiffness_scale_name = bpy.props.EnumProperty(items=enum_drive, name="Stiffness scale")
    viscosity_scale_name = bpy.props.EnumProperty(items=enum_drive, name="Viscosity scale")
    stiffness = bpy.props.FloatProperty(name="Stiffness", description="", min=0.000001, max=9.9e10, precision=6)
    stiffness_matrix_3x3_name = bpy.props.EnumProperty(items=enum_matrix_3x3, name="Stiffness")
    stiffness_matrix_6x6_name = bpy.props.EnumProperty(items=enum_matrix_6x6, name="Stiffness")
    proportional = bpy.props.BoolProperty(name="Proportional")
    factor = bpy.props.FloatProperty(name="Factor", description="", min=0.000001, max=9.9e10, precision=6)
    viscosity = bpy.props.FloatProperty(name="Viscosity", description="", min=0.000001, max=9.9e10, precision=6)
    viscosity_matrix_3x3_name = bpy.props.EnumProperty(items=enum_matrix_3x3, name="Viscosity")
    viscosity_matrix_6x6_name = bpy.props.EnumProperty(items=enum_matrix_6x6, name="Viscosity")
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.stiffness = 1.0
        self.proportional = False
        self.factor = 1.0
        self.matrix_exists(context, "3x3")
        self.matrix_exists(context, "6x6")
    def assign(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.dimensions = self.entity.dimensions
        self.proportional = self.entity.proportional
        self.factor = self.entity.factor
        self.stiffness_scale_name = self.entity.links[0].name
        self.viscosity_scale_name = self.entity.links[1].name
        if self.dimensions == "1D":
            self.stiffness = self.entity.stiffness
            if not self.proportional:
                self.viscosity = self.entity.viscosity
        elif self.dimensions == "3D":
            self.stiffness_matrix_3x3_name = self.entity.links[2].name
            if not self.proportional:
                self.viscosity_matrix_3x3_name = self.entity.links[3].name
        else:
            self.stiffness_matrix_6x6_name = self.entity.links[2].name
            if not self.proportional:
                self.viscosity_matrix_6x6_name = self.entity.links[3].name
    def store(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.entity.dimensions = self.dimensions
        self.entity.proportional = self.proportional
        self.entity.factor = self.factor
        self.entity.unlink_all()
        self.link_drive(context, self.stiffness_scale_name)
        self.link_drive(context, self.viscosity_scale_name)
        if self.dimensions == "1D":
            self.entity.stiffness = self.stiffness
            if not self.proportional:
                self.entity.viscosity = self.viscosity
        else:
            if self.dimensions == "3D":
                self.link_matrix(context, self.stiffness_matrix_3x3_name)
                if not self.proportional:
                    self.link_matrix(context, self.viscosity_matrix_3x3_name)
            else:
                self.link_matrix(context, self.stiffness_matrix_6x6_name)
                if not self.proportional:
                    self.link_matrix(context, self.viscosity_matrix_6x6_name)
        self.entity.increment_links()
    def draw(self, context):
        self.basis = (self.dimensions, self.proportional)
        layout = self.layout
        self.draw_dimensions(layout)
        if self.dimensions == "1D":
            layout.prop(self, "stiffness")
        elif self.dimensions == "3D":
            layout.prop(self, "stiffness_matrix_3x3_name")
        else:
            layout.prop(self, "stiffness_matrix_6x6_name")
        layout.prop(self, "stiffness_scale_name")
        row = layout.row()
        row.prop(self, "proportional")
        if self.proportional:
            row.prop(self, "factor")
        else:
            if self.dimensions == "1D":
                layout.prop(self, "viscosity")
            elif self.dimensions == "3D":
                layout.prop(self, "viscosity_matrix_3x3_name")
            else:
                layout.prop(self, "viscosity_matrix_6x6_name")
        layout.prop(self, "viscosity_scale_name")
    def check(self, context):
        return self.basis != (self.dimensions, self.proportional)
    def create_entity(self):
        return LinearTimeVariantViscoelasticGeneric(self.name)

classes[LinearTimeVariantViscoelasticGenericOperator.bl_label] = LinearTimeVariantViscoelasticGenericOperator

class LinearViscoelasticGenericAxialTorsionCoupling(Entity):
    def string(self):
        ret = "linear viscoelastic generic axial torsion coupling"
        ret += "," + self.links[0].string()
        if self.proportional:
            ret += ",\n\t\t\tproportional, " + str(self.factor)
        else:
            ret += "," + self.links[1].string()
        ret += ",\n\t\t\t" + str(self.coupling_coefficient)
        return ret

class LinearViscoelasticGenericAxialTorsionCouplingOperator(Base):
    bl_label = "Linear viscoelastic generic axial torsion coupling"
    dimensions = bpy.props.EnumProperty(items=[("6D", "6D", "")], name="Dimension(s)")
    coupling_coefficient = bpy.props.FloatProperty(name="Coupling coefficient", description="", min=0.000001, max=9.9e10, precision=6)
    stiffness_matrix_6x1_name = bpy.props.EnumProperty(items=enum_matrix_6x1, name="Stiffness")
    proportional = bpy.props.BoolProperty(name="Proportional")
    factor = bpy.props.FloatProperty(name="Factor", description="", min=0.000001, max=9.9e10, precision=6)
    viscosity_matrix_6x1_name = bpy.props.EnumProperty(items=enum_matrix_6x1, name="Viscosity")
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.coupling_coefficient = 1.0
        self.proportional = False
        self.factor = 1.0
        self.matrix_exists(context, "6x1")
    def assign(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.dimensions = self.entity.dimensions
        self.coupling_coefficient = self.entity.coupling_coefficient
        self.stiffness_matrix_6x1_name = self.entity.links[0].name
        self.proportional = self.entity.proportional
        self.factor = self.entity.factor
        if not self.proportional:
            self.stiffness_matrix_6x1_name = self.entity.links[1].name
    def store(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.entity.dimensions = self.dimensions
        self.entity.coupling_coefficient = self.coupling_coefficient
        self.entity.proportional = self.proportional
        self.entity.unlink_all()
        self.link_matrix(context, self.stiffness_matrix_6x1_name)
        self.entity.factor = self.factor
        if not self.proportional:
            self.link_matrix(context, self.viscosity_matrix_6x1_name)
        self.entity.increment_links()
    def draw(self, context):
        self.basis = self.proportional
        layout = self.layout
        self.draw_dimensions(layout)
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

classes[LinearViscoelasticGenericAxialTorsionCouplingOperator.bl_label] = LinearViscoelasticGenericAxialTorsionCouplingOperator

class CubicViscoelasticGeneric(Entity):
    def string(self):
        ret = "cubic viscoelastic generic"
        if self.dimensions == "1D":
            for stiffness in [self.stiffness_1, self.stiffness_2, self.stiffness_3]:
                ret += ", " + str(stiffness)
            ret += ", " + str(self.viscosity)
        else:
            for link in self.links:
                ret += "," + link.string()
        return ret

class CubicViscoelasticGenericOperator(Base):
    bl_label = "Cubic viscoelastic generic"
    dimensions = bpy.props.EnumProperty(items=[("1D", "1D", ""), ("3D", "3D", "")], name="Dimension(s)")
    stiffness_1 = bpy.props.FloatProperty(name="Stiffness 1", description="", min=0.000001, max=9.9e10, precision=6)
    stiffness_2 = bpy.props.FloatProperty(name="Stiffness 2", description="", min=0.000001, max=9.9e10, precision=6)
    stiffness_3 = bpy.props.FloatProperty(name="Stiffness 3", description="", min=0.000001, max=9.9e10, precision=6)
    viscosity = bpy.props.FloatProperty(name="Viscosity", description="", min=0.000001, max=9.9e10, precision=6)
    stiffness_matrix_3x1_1_name = bpy.props.EnumProperty(items=enum_matrix_3x1, name="Stiffness 1")
    stiffness_matrix_3x1_2_name = bpy.props.EnumProperty(items=enum_matrix_3x1, name="Stiffness 2")
    stiffness_matrix_3x1_3_name = bpy.props.EnumProperty(items=enum_matrix_3x1, name="Stiffness 3")
    viscosity_matrix_3x1_name = bpy.props.EnumProperty(items=enum_matrix_3x1, name="Viscosity")
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.stiffness_1 = 1.0
        self.stiffness_2 = 1.0
        self.stiffness_3 = 1.0
        self.viscosity = 1.0
        self.matrix_exists(context, "3x1")
    def assign(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.dimensions = self.entity.dimensions
        if self.dimensions == "1D":
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
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.entity.dimensions = self.dimensions
        if self.dimensions == "1D":
            self.entity.stiffness_1 = self.stiffness_1
            self.entity.stiffness_2 = self.stiffness_2
            self.entity.stiffness_3 = self.stiffness_3
            self.entity.viscosity = self.viscosity
        else:
            self.entity.unlink_all()
            self.link_matrix(context, self.stiffness_matrix_3x1_1_name)
            self.link_matrix(context, self.stiffness_matrix_3x1_2_name)
            self.link_matrix(context, self.stiffness_matrix_3x1_3_name)
            self.link_matrix(context, self.viscosity_matrix_3x1_name)
            self.entity.increment_links()
    def draw(self, context):
        self.basis = self.dimensions
        layout = self.layout
        self.draw_dimensions(layout)
        if self.dimensions == "1D":
            layout.prop(self, "stiffness_1")
            layout.prop(self, "stiffness_2")
            layout.prop(self, "stiffness_3")
            layout.prop(self, "viscosity")
        else:
            layout.prop(self, "stiffness_matrix_3x1_1_name")
            layout.prop(self, "stiffness_matrix_3x1_2_name")
            layout.prop(self, "stiffness_matrix_3x1_3_name")
            layout.prop(self, "viscosity_matrix_3x1_name")
    def check(self, context):
        return self.basis != self.dimensions
    def create_entity(self):
        return CubicViscoelasticGeneric(self.name)

classes[CubicViscoelasticGenericOperator.bl_label] = CubicViscoelasticGenericOperator

class DoubleLinearViscoelastic(Entity):
    def string(self):
        ret = "double linear viscoelastic"
        if self.dimensions == "1D":
            ret += ", " + str(self.stiffness_1)
            ret += ", " + str(self.upper_strain) + ", " + str(self.lower_strain)
            ret += ", " + str(self.stiffness_2)
            ret += ", " + str(self.viscosity_1)
            if self.second_damping:
                ret += ", second damping, " + str(self.viscosity_1)
        else:
            ret += "," + self.links[0].string()
            ret += ",\n\t\t\t" + str(self.upper_strain) + ", " + str(self.lower_strain)
            ret += "," + self.links[1].string()
            ret += "," + self.links[2].string()
            if self.second_damping:
                ret += ", second damping, " + self.links[3].string()
        return ret

class DoubleLinearViscoelasticOperator(Base):
    bl_label = "Double linear viscoelastic"
    dimensions = bpy.props.EnumProperty(items=[("1D", "1D", ""), ("3D", "3D", "")], name="Dimension(s)")
    stiffness_1 = bpy.props.FloatProperty(name="Stiffness 1", description="", min=0.000001, max=9.9e10, precision=6)
    stiffness_2 = bpy.props.FloatProperty(name="Stiffness 2", description="", min=0.000001, max=9.9e10, precision=6)
    upper_strain = bpy.props.FloatProperty(name="Upper strain", description="", min=0.000001, max=9.9e10, precision=6)
    lower_strain = bpy.props.FloatProperty(name="Lower strain", description="", min=0.000001, max=9.9e10, precision=6)
    stiffness_matrix_3x1_1_name = bpy.props.EnumProperty(items=enum_matrix_3x1, name="Stiffness 1")
    stiffness_matrix_3x1_2_name = bpy.props.EnumProperty(items=enum_matrix_3x1, name="Stiffness 2")
    second_damping = bpy.props.BoolProperty("Second damping")
    viscosity_1 = bpy.props.FloatProperty(name="Viscosity 1", description="", min=0.000001, max=9.9e10, precision=6)
    viscosity_2 = bpy.props.FloatProperty(name="Viscosity 2", description="", min=0.000001, max=9.9e10, precision=6)
    viscosity_matrix_3x1_1_name = bpy.props.EnumProperty(items=enum_matrix_3x1, name="Viscosity 1")
    viscosity_matrix_3x1_2_name = bpy.props.EnumProperty(items=enum_matrix_3x1, name="Viscosity 2")
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.stiffness_1 = 1.0
        self.stiffness_2 = 1.0
        self.second_damping = False
        self.viscosity_1 = 1.0
        self.viscosity_2 = 1.0
        self.matrix_exists(context, "3x1")
    def assign(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.dimensions = self.entity.dimensions
        self.upper_strain = self.entity.upper_strain
        self.lower_strain = self.entity.lower_strain
        self.second_damping = self.entity.second_damping
        if self.dimensions == "1D":
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
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.entity.dimensions = self.dimensions
        self.entity.upper_strain = self.upper_strain
        self.entity.lower_strain = self.lower_strain
        self.entity.second_damping = self.second_damping
        if self.dimensions == "1D":
            self.entity.stiffness_1 = self.stiffness_1
            self.entity.stiffness_2 = self.stiffness_2
            self.entity.viscosity_1 = self.viscosity_1
            self.entity.viscosity_2 = self.viscosity_2
        else:
            self.entity.unlink_all()
            self.link_matrix(context, self.stiffness_matrix_3x1_1_name)
            self.link_matrix(context, self.stiffness_matrix_3x1_2_name)
            self.link_matrix(context, self.viscosity_matrix_3x1_1_name)
            if self.second_damping:
                self.link_matrix(context, self.viscosity_matrix_3x1_2_name)
            self.entity.increment_links()
    def draw(self, context):
        self.basis = (self.dimensions, self.second_damping)
        layout = self.layout
        self.draw_dimensions(layout)
        if self.dimensions == "1D":
            layout.prop(self, "stiffness_1")
            layout.prop(self, "stiffness_2")
            layout.prop(self, "viscosity_1")
            row = layout.row()
            row.prop(self, "second_damping")
            if self.second_damping:
                row.prop(self, "viscosity_2")
        else:
            layout.prop(self, "stiffness_matrix_3x1_1_name")
            layout.prop(self, "stiffness_matrix_3x1_2_name")
            layout.prop(self, "viscosity_matrix_3x1_1_name")
            row = layout.row()
            row.prop(self, "second_damping")
            if self.second_damping:
                row.prop(self, "viscosity_matrix_3x1_2_name")
        layout.prop(self, "upper_strain")
        layout.prop(self, "lower_strain")
    def check(self, context):
        return self.basis != (self.dimensions, self.second_damping)
    def create_entity(self):
        return DoubleLinearViscoelastic(self.name)

classes[DoubleLinearViscoelasticOperator.bl_label] = DoubleLinearViscoelasticOperator

class TurbulentViscoelastic(Entity):
    def string(self):
        ret = "turbulent viscoelastic, " + str(self.stiffness) + ", " + str(self.parabolic_viscosity)
        if self.use_threshold:
            ret += ", " + str(self.threshold)
            if self.use_linear_viscosity:
                ret += ", " + str(self.linear_viscosity)
        return ret

class TurbulentViscoelasticOperator(Base):
    bl_label = "Turbulent viscoelastic"
    dimensions = bpy.props.EnumProperty(items=[("1D", "1D", ""), ], name="Dimension(s)")
    stiffness = bpy.props.FloatProperty(name="Stiffness", description="", min=0.000001, max=9.9e10, precision=6)
    parabolic_viscosity = bpy.props.FloatProperty(name="Parabolic viscosity", description="", min=0.000001, max=9.9e10, precision=6)
    use_threshold = bpy.props.BoolProperty("Use threshold")
    threshold = bpy.props.FloatProperty(name="Threshold", description="", min=0.000001, max=9.9e10, precision=6)
    use_linear_viscosity = bpy.props.BoolProperty("Use linear viscosity")
    linear_viscosity = bpy.props.FloatProperty(name="Linear viscosity", description="", min=0.000001, max=9.9e10, precision=6)
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.stiffness = 1.0
        self.parabolic_viscosity = 1.0
        self.use_threshold = False
        self.threshold = 1.0
        self.use_linear_viscosity = False
        self.linear_viscosity = 1.0
    def assign(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.dimensions = self.entity.dimensions
        self.stiffness = self.entity.stiffness
        self.parabolic_viscosity = self.entity.parabolic_viscosity
        self.use_threshold = self.entity.use_threshold
        self.threshold = self.entity.threshold
        self.use_linear_viscosity = self.entity.use_linear_viscosity
        self.linear_viscosity = self.entity.linear_viscosity
    def store(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.entity.dimensions = self.dimensions
        self.entity.stiffness = self.stiffness
        self.entity.parabolic_viscosity = self.parabolic_viscosity
        self.entity.use_threshold = self.use_threshold
        self.entity.threshold = self.threshold
        self.entity.use_linear_viscosity = self.use_linear_viscosity
        self.entity.linear_viscosity = self.linear_viscosity
    def draw(self, context):
        self.basis = (self.dimensions, self.use_threshold, self.use_linear_viscosity)
        layout = self.layout
        self.draw_dimensions(layout)
        layout.prop(self, "stiffness")
        layout.prop(self, "parabolic_viscosity")
        layout.prop(self, "use_threshold")
        if self.use_threshold:
            layout.prop(self, "threshold")
            layout.prop(self, "use_linear_viscosity")
            if self.use_linear_viscosity:
                layout.prop(self, "linear_viscosity")
    def check(self, context):
        return self.basis != (self.dimensions, self.use_threshold, self.use_linear_viscosity)
    def create_entity(self):
        return TurbulentViscoelastic(self.name)

classes[TurbulentViscoelasticOperator.bl_label] = TurbulentViscoelasticOperator

class LinearViscoelasticBistop(Entity):
    def string(self):
        ret = "linear viscoelastic bistop"
        if self.dimensions == "1D":
            ret += ",\n\t\t\t" + str(self.stiffness) + ", " + str(self.viscosity)
        else:
            ret += ", " + self.links[2].string() + ", " + self.links[3].string()
        ret += ",\n\t\t\tinitial status, " + self.initial_status
        for link in self.links[:2]:
            ret += ",\n\t\t\t" + link.string()
        return ret

class LinearViscoelasticBistopOperator(Base):
    bl_label = "Linear viscoelastic bistop"
    dimensions = bpy.props.EnumProperty(items=[("1D", "1D", ""), ("3D", "3D", ""), ("6D", "6D", "")], name="Dimension(s)")
    stiffness = bpy.props.FloatProperty(name="Stiffness", description="", min=0.000001, max=9.9e10, precision=6)
    stiffness_matrix_3x3_name = bpy.props.EnumProperty(items=enum_matrix_3x3, name="Stiffness")
    stiffness_matrix_6x6_name = bpy.props.EnumProperty(items=enum_matrix_6x6, name="Stiffness")
    viscosity = bpy.props.FloatProperty(name="Viscosity", description="", min=0.000001, max=9.9e10, precision=6)
    viscosity_matrix_3x3_name = bpy.props.EnumProperty(items=enum_matrix_3x3, name="Viscosity")
    viscosity_matrix_6x6_name = bpy.props.EnumProperty(items=enum_matrix_6x6, name="Viscosity")
    initial_status = bpy.props.EnumProperty(items=[("active", "Active", ""), ("inactive", "Inactive", "")], name="Initial status")
    activating_condition_name = bpy.props.EnumProperty(items=enum_drive, name="Activating condition")
    deactivating_condition_name = bpy.props.EnumProperty(items=enum_drive, name="Deactivating condition")
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.stiffness = 1.0
        self.viscosity = 1.0
        self.matrix_exists(context, "3x3")
        self.matrix_exists(context, "6x6")
        self.drive_exists(context)
    def assign(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.dimensions = self.entity.dimensions
        self.initial_status = self.entity.initial_status
        self.activating_condition_name = self.entity.links[0].name
        self.deactivating_condition_name = self.entity.links[1].name
        if self.dimensions == "1D":
            self.stiffness = self.entity.stiffness
            self.viscosity = self.entity.viscosity
        elif self.dimensions == "3D":
            self.stiffness_matrix_3x3_name = self.entity.links[2].name
            self.viscosity_matrix_3x3_name = self.entity.links[3].name
        else:
            self.stiffness_matrix_6x6_name = self.entity.links[2].name
            self.viscosity_matrix_6x6_name = self.entity.links[3].name
    def store(self, context):
        self.entity = self.database.constitutive[context.scene.constitutive_index]
        self.entity.dimensions = self.dimensions
        self.entity.initial_status = self.initial_status
        self.entity.unlink_all()
        self.link_drive(context, self.activating_condition_name)
        self.link_drive(context, self.deactivating_condition_name)
        if self.dimensions == "1D":
            self.entity.stiffness = self.stiffness
            self.entity.viscosity = self.viscosity
        else:
            if self.dimensions == "3D":
                self.link_matrix(context, self.stiffness_matrix_3x3_name)
                self.link_matrix(context, self.viscosity_matrix_3x3_name)
            else:
                self.link_matrix(context, self.stiffness_matrix_6x6_name)
                self.link_matrix(context, self.viscosity_matrix_6x6_name)
        self.entity.increment_links()
    def draw(self, context):
        self.basis = self.dimensions
        layout = self.layout
        self.draw_dimensions(layout)
        if self.dimensions == "1D":
            layout.prop(self, "stiffness")
            layout.prop(self, "viscosity")
        elif self.dimensions == "3D":
            layout.prop(self, "stiffness_matrix_3x3_name")
            layout.prop(self, "viscosity_matrix_3x3_name")
        else:
            layout.prop(self, "stiffness_matrix_6x6_name")
            layout.prop(self, "viscosity_matrix_6x6_name")
        layout.prop(self, "initial_status")
        layout.prop(self, "activating_condition_name")
        layout.prop(self, "deactivating_condition_name")
    def check(self, context):
        return self.basis != self.dimensions
    def create_entity(self):
        return LinearViscoelasticBistop(self.name)

classes[LinearViscoelasticBistopOperator.bl_label] = LinearViscoelasticBistopOperator

