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
    imp.reload(root_dot)
    imp.reload(Operator)
    imp.reload(Entity)
    imp.reload(enum_objects)
    imp.reload(enum_matrix_3x3)
else:
    from .common import (FORMAT, aerodynamic_types, beam_types, force_types, genel_types, joint_types, environment_types, node_types,
        structural_static_types, structural_dynamic_types, Ellipsoid, RhombicPyramid, Teardrop, Cylinder, Sphere)
    from .base import bpy, BPY, root_dot, database, Operator, Entity, Bundle, enum_objects, enum_matrix_3x1, enum_matrix_3x3, enum_constitutive_1D, enum_constitutive_3D, enum_constitutive_6D, enum_drive, enum_element, enum_friction, SelectedObjects
    from mathutils import Vector

types = aerodynamic_types + beam_types + ["Body"] + force_types + genel_types + joint_types + ["Rotor"] + environment_types + ["Driven"] + node_types

tree = ["Add Element",
    ["Aerodynamic", aerodynamic_types,
    "Beam", beam_types,
    "Body",
    "Force", force_types,
    "GENEL", genel_types,
    "Joint", joint_types,
    "Rotor",
    "Environment", environment_types,
    "Driven",
    "Node", node_types,
    ]]

class Base(Operator):
    bl_label = "Elements"
    @classmethod
    def base_poll(self, cls, context, N=None):
        obs = SelectedObjects(context)
        if N:
            test = len(obs) == N and not database.element.filter(cls.bl_label, obs[0])
        else:
            test = not database.element.filter(cls.bl_label)
        return cls.bl_idname.startswith(root_dot + "e_") or test
    def assign(self, context):
        self.entity = database.element[context.scene.element_index]
    def store(self, context):
        self.entity = database.element[self.index]
        self.entity.objects = SelectedObjects(context)
    @classmethod
    def make_list(self, ListItem):
        bpy.types.Scene.element_uilist = bpy.props.CollectionProperty(type = ListItem)
        def select_and_activate(self, context):
            if database.element and self.element_index < len(database.element):
                if hasattr(database.element[self.element_index], "objects"):
                    bpy.ops.object.select_all(action='DESELECT')
                    element = database.element[self.element_index]
                    for ob in element.objects:
                        ob.select = True
                    context.scene.objects.active = element.objects[0]
                    element.remesh()
                elif database.element[self.element_index].type in ["Gravity", "Air properties"]:
                    bpy.ops.object.select_all(action='DESELECT')
        bpy.types.Scene.element_index = bpy.props.IntProperty(default=-1, update=select_and_activate)
    @classmethod
    def delete_list(self):
        del bpy.types.Scene.element_uilist
        del bpy.types.Scene.element_index
    @classmethod
    def get_uilist(self, context):
        return context.scene.element_index, context.scene.element_uilist
    def set_index(self, context, value):
        context.scene.element_index = value
    def prereqs(self, context):
        pass
    def draw_panel_post(self, context, layout):
        obs = SelectedObjects(context)
        elements = [element for element in database.element if hasattr(element, "objects") and
            element.objects and element.objects[0] in obs]
        drives = [drive for drive in database.drive if hasattr(drive, "objects") and
            drive.objects and drive.objects[0] in obs]
        frames = [frame for frame in database.frame if frame.objects[0] in obs]
        if elements or drives or frames:
            layout.operator(root_dot + "duplicate_obs")
    def write_hinge(self, text, name, V1=True, V2=True, M1=True, M2=True):
        rot_0, globalV_0, Node_0 = self.rigid_offset(0)
        localV_0 = rot_0*globalV_0
        rot_1, globalV_1, Node_1 = self.rigid_offset(1)
        to_hinge = rot_1*(globalV_1 + self.objects[0].matrix_world.translation - self.objects[1].matrix_world.translation)
        rotT = self.objects[0].matrix_world.to_quaternion().to_matrix().transposed()
        text.write(
        "\tjoint: " + FORMAT(database.element.index(self)) + ", " + name + ",\n" +
        "\t\t" + FORMAT(Node_0))
        if V1:
            text.write(", ")
            self.write_vector(localV_0, text)
        if M1:
            text.write(",\n\t\t\thinge, matr,\n")
            self.write_matrix(rot_0*rotT, text, "\t\t\t\t")
        text.write(", \n\t\t" + FORMAT(Node_1))
        if V2:
            text.write(", ")
            self.write_vector(to_hinge, text)
        if M2:
            text.write(",\n\t\t\thinge, matr,\n")
            self.write_matrix(rot_1*rotT, text, "\t\t\t\t")

klasses = dict()

for t in types:
    class Tester(Base):
        bl_label = t
        @classmethod
        def poll(cls, context):
            return False
        def store(self, context):
            self.entity = database.element[self.index]
        def create_entity(self):
            return Entity(self.name)
    klasses[t] = Tester

class StructuralForce(Entity):
    elem_type = "force"
    def write(self, text):
        rot_0, globalV_0, Node_0 = self.rigid_offset(0)
        rotT_0 = self.objects[0].matrix_world.to_quaternion().to_matrix().transposed()
        relative_dir = rot_0*rotT_0*Vector((0., 0., 1.))
        relative_arm_0 = rot_0*globalV_0
        string = "\tforce: " + FORMAT(database.element.index(self)) + ", "
        if self.orientation == "follower":
            string += "follower"
            relative_dir = rot_0*rotT_0*Vector((0., 0., 1.))
        else:
            string += "absolute"
            relative_dir = rotT_0*Vector((0., 0., 1.))
        relative_dir = self.round_vector(relative_dir)
        relative_arm_0 = self.round_vector(relative_arm_0)
        text.write(string+
        ",\n\t\t" + FORMAT(Node_0)+
        ",\n\t\t\tposition, ")
        self.write_vector(relative_arm_0, text, ",\n\t\t\t")
        self.write_vector(relative_dir, text, ",\n\t\t")
        text.write(self.links[0].string(self) + ";\n")
    def remesh(self):
        RhombicPyramid(self.objects[0])

class ForceBase(Base):
    orientation = bpy.props.EnumProperty(items=[("follower", "Follower", ""), ("absolute", "Absolute", "")], name="Orientation", default="follower")
    drive_name = bpy.props.EnumProperty(items=enum_drive, name="Drive")
    drive_edit = bpy.props.BoolProperty(name="")
    def prereqs(self, context):
        self.drive_exists(context)
    def assign(self, context):
        self.entity = database.element[context.scene.element_index]
        self.orientation = self.entity.orientation
        self.drive_name = self.entity.links[0].name
    def store(self, context):
        self.entity = database.element[self.index]
        self.entity.objects = SelectedObjects(context)
        self.entity.orientation = self.orientation
        self.entity.unlink_all()
        self.link_drive(context, self.drive_name, self.drive_edit)
        self.entity.increment_links()
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "orientation")
        self.draw_link(layout, "drive_name", "drive_edit")

class StructuralForceOperator(ForceBase):
    bl_label = "Structural force"
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context, 1)
    def create_entity(self):
        return StructuralForce(self.name)

klasses[StructuralForceOperator.bl_label] = StructuralForceOperator

class StructuralInternalForce(Entity):
    elem_type = "force"
    def write(self, text):
        rot_0, globalV_0, Node_0 = self.rigid_offset(0)
        rotT_0 = self.objects[0].matrix_world.to_quaternion().to_matrix().transposed()
        relative_arm_0 = rot_0*globalV_0
        rot_1, globalV_1, Node_1 = self.rigid_offset(1)
        relative_arm_1 = rot_1*globalV_1
        string = "\tforce: " + FORMAT(database.element.index(self)) + ", "
        if self.orientation == "follower":
            string += "follower internal"
            relative_dir = rot_0*rotT_0*Vector((0., 0., 1.))
        else:
            string += "absolute internal"
            relative_dir = rotT_0*Vector((0., 0., 1.))
        text.write(string+
        ",\n\t\t" + FORMAT(Node_0) + ",\n\t\t\t")
        self.write_vector(relative_dir, text, ",\n\t\t\t")
        self.write_vector(relative_arm_0, text, ",\n\t\t")
        text.write(FORMAT(Node_1) + ",\n\t\t\t")
        self.write_vector(relative_arm_1, text, ",\n\t\t")
        text.write(self.links[0].string(self) + ";\n")
    def remesh(self):
        RhombicPyramid(self.objects[0])

class StructuralInternalForceOperator(ForceBase):
    bl_label = "Structural internal force"
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context, 2)
    def create_entity(self):
        return StructuralInternalForce(self.name)

klasses[StructuralInternalForceOperator.bl_label] = StructuralInternalForceOperator

class StructuralCouple(Entity):
    elem_type = "couple"
    def write(self, text):
        rot_0, globalV_0, Node_0 = self.rigid_offset(0)
        rotT_0 = self.objects[0].matrix_world.to_quaternion().to_matrix().transposed()
        string = "\tcouple: " + FORMAT(database.element.index(self)) + ", "
        if self.orientation == "follower":
            string += "follower"
            relative_dir = rot_0*rotT_0*Vector((0., 0., 1.))
        else:
            string += "absolute"
            relative_dir = rotT_0*Vector((0., 0., 1.))
        text.write(string+
        ",\n\t\t" + FORMAT(Node_0) + ",\n\t\t\t")
        self.write_vector(relative_dir, text, ",\n\t\t")
        text.write(self.links[0].string(self) + ";\n")
    def remesh(self):
        RhombicPyramid(self.objects[0])

class StructuralCoupleOperator(ForceBase):
    bl_label = "Structural couple"
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context, 1)
    def create_entity(self):
        return StructuralCouple(self.name)

klasses[StructuralCoupleOperator.bl_label] = StructuralCoupleOperator

class StructuralInternalCouple(Entity):
    elem_type = "couple"
    def write(self, text):
        rot_0, globalV_0, Node_0 = self.rigid_offset(0)
        rotT_0 = self.objects[0].matrix_world.to_quaternion().to_matrix().transposed()
        rot_1, globalV_1, Node_1 = self.rigid_offset(1)
        string = "\tcouple: " + FORMAT(database.element.index(self)) + ", "
        if self.orientation == "follower":
            string += "follower internal"
            relative_dir = rot_0*rotT_0*Vector((0., 0., 1.))
        else:
            string += "absolute internal"
            relative_dir = rotT_0*Vector((0., 0., 1.))
        text.write(string+
        ",\n\t\t" + FORMAT(Node_0) + ",\n\t\t\t")
        self.write_vector(relative_dir, text, ",\n\t\t")
        text.write(FORMAT(Node_1) + ",\n" + self.links[0].string(True) + ";\n")
    def remesh(self):
        RhombicPyramid(self.objects[0])

class StructuralInternalCoupleOperator(ForceBase):
    bl_label = "Structural internal couple"
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context, 2)
    def create_entity(self):
        return StructuralInternalCouple(self.name)

klasses[StructuralInternalCoupleOperator.bl_label] = StructuralInternalCoupleOperator

class AxialRotation(Entity):
    elem_type = "joint"
    def write(self, text):
        self.write_hinge(text, "axial rotation")
        text.write(",\n" + self.links[0].string(True) + ";\n")
    def remesh(self):
        Cylinder(self.objects[0])

class AxialRotationOperator(Base):
    bl_label = "Axial rotation"
    drive_name = bpy.props.EnumProperty(items=enum_drive, name="Drive")
    drive_edit = bpy.props.BoolProperty(name="")
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context, 2)
    def prereqs(self, context):
        self.drive_exists(context)
    def assign(self, context):
        self.entity = database.element[context.scene.element_index]
        self.drive_name = self.entity.links[0].name
    def store(self, context):
        self.entity = database.element[self.index]
        self.entity.objects = SelectedObjects(context)
        self.entity.unlink_all()
        self.link_drive(context, self.drive_name, self.drive_edit)
        self.entity.increment_links()
    def draw(self, context):
        layout = self.layout
        self.draw_link(layout, "drive_name", "drive_edit")
    def create_entity(self):
        return AxialRotation(self.name)

klasses[AxialRotationOperator.bl_label] = AxialRotationOperator

class Clamp(Entity):
    elem_type = "joint"
    def write(self, text):
        text.write(
        "\tjoint: " + FORMAT(database.element.index(self)) + ", clamp,\n" +
        "\t\t" + FORMAT(database.node.index(self.objects[0])) + ", node, node;\n")
    def remesh(self):
        Teardrop(self.objects[0])

class ClampOperator(Base):
    bl_label = "Clamp"
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context, 1)
    def create_entity(self):
        return Clamp(self.name)

klasses[ClampOperator.bl_label] = ClampOperator

class DeformableDisplacementJoint(Entity):
    elem_type = "joint"
    def write(self, text):
        self.write_hinge(text, "deformable displacement joint")
        text.write(",\n\t\t" + self.links[0].string() + ";\n")
    def remesh(self):
        Cylinder(self.objects[0])

class ConstitutiveBase(Base):
    def assign(self, context):
        self.entity = database.element[context.scene.element_index]
        self.constitutive_name = self.entity.links[0].name
    def store(self, context):
        self.entity = database.element[self.index]
        self.entity.objects = SelectedObjects(context)
        self.entity.unlink_all()
        self.link_constitutive(context, self.constitutive_name, self.constitutive_edit)
        self.entity.increment_links()
    def draw(self, context):
        layout = self.layout
        self.draw_link(layout, "constitutive_name", "constitutive_edit")

class DeformableDisplacementJointOperator(ConstitutiveBase):
    bl_label = "Deformable displacement joint"
    constitutive_name = bpy.props.EnumProperty(items=enum_constitutive_3D, name="Constitutive 3D")
    constitutive_edit = bpy.props.BoolProperty(name="")
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context, 2)
    def prereqs(self, context):
        self.constitutive_exists(context, "3D")
    def create_entity(self):
        return DeformableDisplacementJoint(self.name)

klasses[DeformableDisplacementJointOperator.bl_label] = DeformableDisplacementJointOperator

class DeformableHinge(Entity):
    elem_type = "joint"
    def write(self, text):
        self.write_hinge(text, "deformable hinge", V1=False, V2=False)
        text.write(",\n\t\t" + self.links[0].string() + ";\n")
    def remesh(self):
        Cylinder(self.objects[0])

class DeformableHingeOperator(ConstitutiveBase):
    bl_label = "Deformable joint"
    constitutive_name = bpy.props.EnumProperty(items=enum_constitutive_3D, name="Constitutive 3D")
    constitutive_edit = bpy.props.BoolProperty(name="")
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context, 2)
    def prereqs(self, context):
        self.constitutive_exists(context, "3D")
    def create_entity(self):
        return DeformableJoint(self.name)

klasses[DeformableHingeOperator.bl_label] = DeformableHingeOperator

class DeformableJoint(Entity):
    elem_type = "joint"
    def write(self, text):
        self.write_hinge(text, "deformable joint")
        text.write(",\n\t\t" + self.links[0].string() + ";\n")
    def remesh(self):
        Cylinder(self.objects[0])

class DeformableJointOperator(ConstitutiveBase):
    bl_label = "Deformable joint"
    constitutive_name = bpy.props.EnumProperty(items=enum_constitutive_3D, name="Constitutive 3D")
    constitutive_edit = bpy.props.BoolProperty(name="")
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context, 2)
    def prereqs(self, context):
        self.constitutive_exists(context, "3D")
    def create_entity(self):
        return DeformableJoint(self.name)

klasses[DeformableJointOperator.bl_label] = DeformableJointOperator

class Distance(Entity):
    elem_type = "joint"
    def write(self, text):
        text.write("\tjoint: " + FORMAT(database.element.index(self)) + ", distance,\n")
        for i in range(2):
            self.write_node(text, i, node=True, position=True, p_label="position")
            text.write(",\n")
        if self.from_nodes:
            text.write("\t\tfrom nodes;\n")
        else:
            text.write(self.links[0].string(True) + ";\n")

class DistanceOperator(Base):
    bl_label = "Distance"
    from_nodes = bpy.props.BoolProperty(name="From nodes", description="Constant distance from initial node positons", default=True)
    drive_name = bpy.props.EnumProperty(items=enum_drive, name="Drive")
    drive_edit = bpy.props.BoolProperty(name="")
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context, 2)
    def prereqs(self, context):
        self.drive_exists(context)
    def assign(self, context):
        self.entity = database.element[context.scene.element_index]
        self.from_nodes = self.entity.from_nodes
        if self.entity.links:
            self.drive_name = self.entity.links[0].name
    def store(self, context):
        self.entity = database.element[self.index]
        self.entity.objects = SelectedObjects(context)
        self.entity.from_nodes = self.from_nodes
        if not self.from_nodes:
            self.entity.unlink_all()
            self.link_drive(context, self.drive_name, self.drive_edit)
            self.entity.increment_links()
    def draw(self, context):
        self.basis = self.from_nodes
        layout = self.layout
        layout.prop(self, "from_nodes")
        if not self.from_nodes:
            self.draw_link(layout, "drive_name", "drive_edit")
    def check(self, context):
        return self.basis != self.from_nodes
    def create_entity(self):
        return Distance(self.name)

klasses[DistanceOperator.bl_label] = DistanceOperator

class InLine(Entity):
    elem_type = "joint"
    def write(self, text):
        rot0, globalV0, iNode0 = self.rigid_offset(0)
        localV0 = rot0*globalV0
        rot_1, globalV_1, Node_1 = self.rigid_offset(1)
        to_point = rot_1*(globalV_1 + self.objects[0].matrix_world.translation - self.objects[1].matrix_world.translation)
        rot = self.objects[0].matrix_world.to_quaternion().to_matrix().transposed()
        text.write("\tjoint: " + FORMAT(database.element.index(self)) + ", inline,\n")
        self.write_node(text, 0, node=True, position=True, orientation=True)
        text.write(",\n\t\t" + FORMAT(Node_1))
        text.write(",\n\t\t\toffset, ")
        self.write_vector(to_point, text, ";\n")
    def remesh(self):
        RhombicPyramid(self.objects[0])

class InLineOperator(Base):
    bl_label = "In line"
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context, 2)
    def create_entity(self):
        return InLine(self.name)

klasses[InLineOperator.bl_label] = InLineOperator

class InPlane(Entity):
    elem_type = "joint"
    def write(self, text):
        rot0, globalV0, iNode0 = self.rigid_offset(0)
        localV0 = rot0*globalV0
        rot1, globalV1, iNode1 = self.rigid_offset(1)
        to_point = rot1*(globalV1 + self.objects[0].matrix_world.translation - self.objects[1].matrix_world.translation)
        rot = self.objects[0].matrix_world.to_quaternion().to_matrix().transposed()
        normal = rot*rot0*Vector((0., 0., 1.))
        text.write(
        "\tjoint: " + FORMAT(database.element.index(self)) + ", inplane,\n" +
        "\t\t" + FORMAT(iNode0) + ",\n\t\t\t")
        self.write_vector(localV0, text, ",\n\t\t\t")
        self.write_vector(normal, text, ",\n\t\t")
        text.write(FORMAT(iNode1) + ",\n\t\t\toffset, " + FORMAT(to_point[0]) + ", " + FORMAT(to_point[1]) + ", " + FORMAT(to_point[2]) + ";\n")
    def remesh(self):
        RhombicPyramid(self.objects[0])

class InPlaneOperator(Base):
    bl_label = "In plane"
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context, 2)
    def create_entity(self):
        return InPlane(self.name)

klasses[InPlaneOperator.bl_label] = InPlaneOperator

class RevoluteHinge(Entity):
    elem_type = "joint"
    def write(self, text):
        self.write_hinge(text, "revolute hinge")
        if self.enable_theta:
            text.write(",\n\t\tinitial theta, " + FORMAT(self.theta))
        if self.enable_friction:
            text.write(",\n\t\tfriction, " + FORMAT(self.average_radius))
            if self.enable_preload:
                text.write(",\n\t\t\tpreload, " + FORMAT(self.preload))
            text.write(",\n\t\t\t" + self.links[0].string())
        text.write(";\n")
    def remesh(self):
        Cylinder(self.objects[0])

class RevoluteHingeOperator(Base):
    bl_label = "Revolute hinge"
    enable_theta = bpy.props.BoolProperty(name="Enable theta", description="Enable use of initial theta", default=False)
    theta = bpy.props.FloatProperty(name="Theta", description="Initial theta", min=-9.9e10, max=9.9e10, precision=6, default=0.0)
    enable_friction = bpy.props.BoolProperty(name="Enable friction", description="Enable friction model", default=False)
    average_radius = bpy.props.FloatProperty(name="Radius", description="Average radius used in friction model", min=0.0, max=9.9e10, precision=6, default=1.0)
    enable_preload = bpy.props.BoolProperty(name="Enable preload", description="Enable preload", default=False)
    preload = bpy.props.FloatProperty(name="Preload", description="Preload used in friction model", min=0.0, max=9.9e10, precision=6, default=1.0)
    friction_name = bpy.props.EnumProperty(items=enum_friction, name="Friction")
    friction_edit = bpy.props.BoolProperty(name="")
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context, 2)
    def prereqs(self, context):
        self.function_exists(context)
        self.friction_exists(context)
    def assign(self, context):
        self.entity = database.element[context.scene.element_index]
        self.enable_theta = self.entity.enable_theta
        self.theta = self.entity.theta
        self.enable_friction = self.entity.enable_friction
        self.average_radius = self.entity.average_radius
        self.enable_preload = self.entity.enable_preload
        self.preload = self.entity.preload
    def store(self, context):
        self.entity = database.element[self.index]
        self.entity.objects = SelectedObjects(context)
        self.entity.enable_theta = self.enable_theta
        self.entity.theta = self.theta
        self.entity.enable_friction = self.enable_friction
        self.entity.average_radius = self.average_radius
        self.entity.enable_preload = self.enable_preload
        self.entity.preload = self.preload
        if self.enable_friction:
            self.entity.unlink_all()
            self.link_friction(context, self.friction_name, self.friction_edit)
            self.entity.increment_links()
    def draw(self, context):
        self.basis = (self.enable_theta, self.enable_friction, self.enable_preload)
        layout = self.layout
        row = layout.row()
        row.prop(self, "enable_theta")
        if self.enable_theta:
            row.prop(self, "theta")
        row = layout.row()
        row.prop(self, "enable_friction")
        if self.enable_friction:
            row.prop(self, "average_radius")
            row = layout.row()
            row.prop(self, "enable_preload")
            if self.enable_preload:
                row.prop(self, "preload")
            self.draw_link(layout, "friction_name", "friction_edit")
    def check(self, context):
        return self.basis != (self.enable_theta, self.enable_friction, self.enable_preload)
    def create_entity(self):
        return RevoluteHinge(self.name)

klasses[RevoluteHingeOperator.bl_label] = RevoluteHingeOperator

class Rod(Entity):
    elem_type = "joint"
    def write(self, text):
        text.write("\tjoint: " + FORMAT(database.element.index(self)) + ", rod,\n")
        for i in range(2):
            self.write_node(text, i, node=True, position=True, p_label="position")
            text.write(",\n")
        text.write("\t\tfrom nodes,\n\t\t" + self.links[0].string() + ";\n")

class RodOperator(ConstitutiveBase):
    bl_label = "Rod"
    constitutive_name = bpy.props.EnumProperty(items=enum_constitutive_1D, name="Constitutive 1D")
    constitutive_edit = bpy.props.BoolProperty(name="")
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context, 2)
    def prereqs(self, context):
        self.constitutive_exists(context, "1D")
    def create_entity(self):
        return Rod(self.name)

klasses[RodOperator.bl_label] = RodOperator

class SphericalHinge(Entity):
    elem_type = "joint"
    def write(self, text):
        self.write_hinge(text, "spherical hinge")
        text.write(";\n")
    def remesh(self):
        Sphere(self.objects[0])

class SphericalHingeOperator(Base):
    bl_label = "Spherical hinge"
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context, 2)
    def create_entity(self):
        return SphericalHinge(self.name)

klasses[SphericalHingeOperator.bl_label] = SphericalHingeOperator

class TotalJoint(Entity):
    elem_type = "joint"
    def write(self, text):
        rot_0, globalV_0, Node_0 = self.rigid_offset(0)
        localV_0 = rot_0*globalV_0
        rot_1, globalV_1, Node_1 = self.rigid_offset(1)
        to_joint = rot_1*(globalV_1 + self.objects[0].matrix_world.translation - self.objects[1].matrix_world.translation)
        rot = self.objects[0].matrix_world.to_quaternion().to_matrix().transposed()
        if Node_1 == self.objects[1]:
            rot_position = rot
        else:
            rot_position = self.objects[1].matrix_world.to_quaternion().to_matrix().transposed()
        text.write("\tjoint: " + FORMAT(database.element.index(self)) + ", total joint")
        if self.first == "rotate":
            text.write(",\n\t\t" + FORMAT(Node_0) + ", position, ")
            self.write_vector(localV_0, text, ",\n\t\t\tposition orientation, matr,\n")
            self.write_matrix(rot_0*rot_position, text, "\t\t\t\t")
            text.write(",\n\t\t\trotation orientation, matr,\n")
            self.write_matrix(rot_0*rot, text, "\t\t\t\t")
        text.write(",\n\t\t" + FORMAT(Node_1) + ", position, ")
        self.write_vector(to_joint, text, ",\n\t\t\tposition orientation, matr,\n")
        self.write_matrix(rot_1*rot_position, text, "\t\t\t\t")
        text.write(",\n\t\t\trotation orientation, matr,\n")
        self.write_matrix(rot_1*rot, text, "\t\t\t\t")
        if self.first == "displace":
            text.write(",\n\t\t" + FORMAT(Node_0) + ", position, ")
            self.write_vector(localV_0, text, ",\n\t\t\tposition orientation, matr,\n")
            self.write_matrix(rot_0*rot_position, text, "\t\t\t\t")
            text.write(",\n\t\t\trotation orientation, matr,\n")
            self.write_matrix(rot_0*rot, text, "\t\t\t\t")
        text.write(",\n\t\t\tposition constraint")
        for b in [self.displacement_x, self.displacement_y, self.displacement_z]: 
            if b:
                text.write(", active")
            else:
                text.write(", inactive")
        text.write(", component")
        super().indent_drives += 2
        for i, b in enumerate([self.displacement_x, self.displacement_y, self.displacement_z]):
            if b:
                text.write(",\n" + self.links[i].string(True))
            else:
                text.write(",\n\t\t\t\tinactive")
        text.write(",\n\t\t\torientation constraint")
        for b in [self.angular_displacement_x, self.angular_displacement_y, self.angular_displacement_z]: 
            if b:
                text.write(", active")
            else:
                text.write(", inactive")
        text.write(", component")
        for i, b in enumerate([self.angular_displacement_x, self.angular_displacement_y, self.angular_displacement_z]):
            if b:
                text.write(",\n" + self.links[3+i].string(True))
            else:
                text.write(",\n\t\t\t\tinactive")
        super().indent_drives -= 2
        text.write(";\n")
    def remesh(self):
        Sphere(self.objects[0])

class TotalJointOperator(Base):
    bl_label = "Total joint"
    first = bpy.props.EnumProperty(items=[("displace", "Displace first", ""), ("rotate", "Rotate first", "")], default="displace")
    displacement_x = bpy.props.BoolProperty(name="", description="Displacement-X drive is active", default=False)
    displacement_x_drive_name = bpy.props.EnumProperty(items=enum_drive, name="Displacement-X Drive")
    displacement_x_drive_edit = bpy.props.BoolProperty(name="")
    displacement_y = bpy.props.BoolProperty(name="", description="Displacement-Y drive is active", default=False)
    displacement_y_drive_name = bpy.props.EnumProperty(items=enum_drive, name="Displacement-Y Drive")
    displacement_y_drive_edit = bpy.props.BoolProperty(name="")
    displacement_z = bpy.props.BoolProperty(name="", description="Displacement-Z drive is active", default=False)
    displacement_z_drive_name = bpy.props.EnumProperty(items=enum_drive, name="Displacement-Z Drive")
    displacement_z_drive_edit = bpy.props.BoolProperty(name="")
    angular_displacement_x = bpy.props.BoolProperty(name="", description="Angular Displacement-X drive is active", default=False)
    angular_displacement_x_drive_name = bpy.props.EnumProperty(items=enum_drive, name="Angular Displacement-X Drive")
    angular_displacement_x_drive_edit = bpy.props.BoolProperty(name="")
    angular_displacement_y = bpy.props.BoolProperty(name="", description="Angular Displacement-Y drive is active", default=False)
    angular_displacement_y_drive_name = bpy.props.EnumProperty(items=enum_drive, name="Angular Displacement-Y Drive")
    angular_displacement_y_drive_edit = bpy.props.BoolProperty(name="")
    angular_displacement_z = bpy.props.BoolProperty(name="", description="Angular Displacement-Z drive is active", default=False)
    angular_displacement_z_drive_name = bpy.props.EnumProperty(items=enum_drive, name="Angular Displacement-Z Drive")
    angular_displacement_z_drive_edit = bpy.props.BoolProperty(name="")
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context, 2)
    def prereqs(self, context):
        self.drive_exists(context)
    def assign(self, context):
        self.entity = database.element[context.scene.element_index]
        self.first = self.entity.first
        self.displacement_x = self.entity.displacement_x
        self.displacement_y = self.entity.displacement_y
        self.displacement_z = self.entity.displacement_z
        self.angular_displacement_x = self.entity.angular_displacement_x
        self.angular_displacement_y = self.entity.angular_displacement_y
        self.angular_displacement_z = self.entity.angular_displacement_z
        self.displacement_x_drive_name = self.entity.links[0].name
        self.displacement_y_drive_name = self.entity.links[1].name
        self.displacement_z_drive_name = self.entity.links[2].name
        self.angular_displacement_x_drive_name = self.entity.links[3].name
        self.angular_displacement_y_drive_name = self.entity.links[4].name
        self.angular_displacement_z_drive_name = self.entity.links[5].name
    def store(self, context):
        self.entity = database.element[self.index]
        self.entity.objects = SelectedObjects(context)
        self.entity.first = self.first
        self.entity.displacement_x = self.displacement_x
        self.entity.displacement_y = self.displacement_y
        self.entity.displacement_z = self.displacement_z
        self.entity.angular_displacement_x = self.angular_displacement_x
        self.entity.angular_displacement_y = self.angular_displacement_y
        self.entity.angular_displacement_z = self.angular_displacement_z
        self.entity.unlink_all()
        self.link_drive(context, self.displacement_x_drive_name, self.displacement_x_drive_edit)
        self.link_drive(context, self.displacement_y_drive_name, self.displacement_y_drive_edit)
        self.link_drive(context, self.displacement_z_drive_name, self.displacement_z_drive_edit)
        self.link_drive(context, self.angular_displacement_x_drive_name, self.angular_displacement_x_drive_edit)
        self.link_drive(context, self.angular_displacement_y_drive_name, self.angular_displacement_y_drive_edit)
        self.link_drive(context, self.angular_displacement_z_drive_name, self.angular_displacement_z_drive_edit)
        self.entity.increment_links()
    def draw(self, context):
        self.basis = (self.displacement_x)
        layout = self.layout
        for predicate in ["displacement_", "angular_displacement_"]:
            for c in "xyz":
                row = layout.row()
                row.prop(self, predicate + c)
                self.draw_link(row, predicate + c + "_drive_name", predicate + c + "_drive_edit")
    def create_entity(self):
        return TotalJoint(self.name)

klasses[TotalJointOperator.bl_label] = TotalJointOperator

class ViscousBody(Entity):
    elem_type = "joint"
    def write(self, text):
        text.write(
        "\tjoint: " + FORMAT(database.element.index(self)) + ", viscous body,\n\t\t" +
        FORMAT(database.node.index(self.objects[0]))+
        ",\n\t\tposition, reference, node, null" +
        ",\n\t\t" + self.links[0].string() + ";\n")
    def remesh(self):
        Sphere(self.objects[0])

class ViscousBodyOperator(ConstitutiveBase):
    bl_label = "Viscous body"
    constitutive_name = bpy.props.EnumProperty(items=enum_constitutive_6D, name="Constitutive 6D")
    constitutive_edit = bpy.props.BoolProperty(name="")
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context, 1)
    def prereqs(self, context):
        self.constitutive_exists(context, "6D")
    def create_entity(self):
        return ViscousBody(self.name)

klasses[ViscousBodyOperator.bl_label] = ViscousBodyOperator

class Body(Entity):
    elem_type = "body"
    def write(self, text):
        text.write("\tbody: " + FORMAT(database.element.index(self)) + ",\n")
        self.write_node(text, 0, node=True)
        text.write("\t\t\t" + FORMAT(self.mass) + ",\n")
        self.write_node(text, 0, position=True, p_label="")
        text.write(", " + self.links[0].string())
        self.write_node(text, 0, orientation=True, o_label="inertial")
        text.write(";\n")
    def remesh(self):
        Ellipsoid(self.objects[0], self.mass, self.links[0])

class BodyOperator(Base):
    bl_label = "Body"
    mass = bpy.props.FloatProperty(name="Mass", description="", min=0.000001, max=9.9e10, precision=6, default=1.0)
    matrix_name = bpy.props.EnumProperty(items=enum_matrix_3x3, name="Matrix")
    matrix_edit = bpy.props.BoolProperty(name="")
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context, 1)
    def prereqs(self, context):
        self.matrix_exists(context, "3x3")
    def assign(self, context):
        self.entity = database.element[context.scene.element_index]
        self.mass = self.entity.mass
        self.matrix_name = self.entity.links[0].name
    def store(self, context):
        self.entity = database.element[self.index]
        self.entity.objects = SelectedObjects(context)
        self.entity.mass = self.mass
        self.entity.unlink_all()
        self.link_matrix(context, self.matrix_name, self.matrix_edit)
        self.entity.increment_links()
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "mass")
        self.draw_link(layout, "matrix_name", "matrix_edit")
    def create_entity(self):
        return Body(self.name)

klasses[BodyOperator.bl_label] = BodyOperator

class RigidOffset(Entity):
    def remesh(self):
        RhombicPyramid(self.objects[0])

class RigidOffsetOperator(Base):
    bl_label = "Rigid offset"
    @classmethod
    def poll(cls, context):
        obs = SelectedObjects(context)
        test = len(obs) == 2 and not (database.element.filter("Rigid offset", obs[0])
            or database.element.filter("Dummy node", obs[0]))
        return cls.bl_idname.startswith(root_dot + "e_") or test
    def create_entity(self):
        return RigidOffset(self.name)

klasses[RigidOffsetOperator.bl_label] = RigidOffsetOperator

class DummyNode(Entity):
    def remesh(self):
        RhombicPyramid(self.objects[0])

class DummyNodeOperator(Base):
    bl_label = "Dummy node"
    @classmethod
    def poll(cls, context):
        obs = SelectedObjects(context)
        test = len(obs) == 2 and not (database.element.filter("Rigid offset", obs[0])
            or database.element.filter("Dummy node", obs[0]))
        return cls.bl_idname.startswith(root_dot + "e_") or test
    def create_entity(self):
        return DummyNode(self.name)

klasses[DummyNodeOperator.bl_label] = DummyNodeOperator

class BeamSegment(Entity):
        ...

class BeamSegmentOperator(ConstitutiveBase):
    bl_label = "Beam segment"
    constitutive_name = bpy.props.EnumProperty(items=enum_constitutive_6D, name="Constitutive 6D")
    constitutive_edit = bpy.props.BoolProperty(name="")
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context, 2)
    def prereqs(self, context):
        self.constitutive_exists(context, "6D")
    def create_entity(self):
        return BeamSegment(self.name)

klasses[BeamSegmentOperator.bl_label] = BeamSegmentOperator

class Gravity(Entity):
    elem_type = "gravity"
    def write(self, text):
        text.write("\tgravity: " + self.links[0].string() + ", " + self.links[1].string() + ";\n")

class GravityOperator(Base):
    bl_label = "Gravity"
    matrix_name = bpy.props.EnumProperty(items=enum_matrix_3x1, name="Vector")
    matrix_edit = bpy.props.BoolProperty(name="")
    drive_name = bpy.props.EnumProperty(items=enum_drive, name="Drive")
    drive_edit = bpy.props.BoolProperty(name="")
    @classmethod
    def poll(self, context):
        return (self.bl_idname.startswith(root_dot + "e_")
            or not database.element.filter("Gravity"))
    def prereqs(self, context):
        self.matrix_exists(context, "3x1")
        self.drive_exists(context)
    def assign(self, context):
        self.entity = database.element[context.scene.element_index]
        self.matrix_name = self.entity.links[0].name
        self.drive_name = self.entity.links[1].name
    def store(self, context):
        self.entity = database.element[self.index]
        self.entity.unlink_all()
        self.link_matrix(context, self.matrix_name, self.matrix_edit)
        self.link_drive(context, self.drive_name, self.drive_edit)
        self.entity.increment_links()
    def draw(self, context):
        layout = self.layout
        self.draw_link(layout, "matrix_name", "matrix_edit")
        self.draw_link(layout, "drive_name", "drive_edit")
    def create_entity(self):
        return Gravity(self.name)

klasses[GravityOperator.bl_label] = GravityOperator

class Driven(Entity):
    elem_type = "driven"
    def write(self, text):
        text.write("\tdriven: " + FORMAT(database.element.index(self.links[1])) + ",\n" +
        self.links[0].string(True) + ",\n" +
        "\t\texisting: " + self.links[1].elem_type + ", " + FORMAT(database.element.index(self.links[1])) + ";\n")

class DrivenOperator(Base):
    bl_label = "Driven"
    drive_name = bpy.props.EnumProperty(items=enum_drive, name="Drive")
    drive_edit = bpy.props.BoolProperty(name="")
    element_name = bpy.props.EnumProperty(items=enum_element, name="Element")
    element_edit = bpy.props.BoolProperty(name="")
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context) and context.scene.element_uilist
    def prereqs(self, context):
        self.drive_exists(context)
        self.element_name = context.scene.element_uilist[context.scene.element_index].name
    def assign(self, context):
        self.entity = database.element[context.scene.element_index]
        self.drive_name = self.entity.links[0].name
        self.element_name = self.entity.links[1].name
    def store(self, context):
        self.entity = database.element[self.index]
        self.entity.unlink_all()
        self.link_drive(context, self.drive_name, self.drive_edit)
        self.link_element(context, self.element_name, self.element_edit)
        self.entity.increment_links()
    def draw(self, context):
        layout = self.layout
        self.draw_link(layout, "drive_name", "drive_edit")
        self.draw_link(layout, "element_name", "element_edit")
    def create_entity(self):
        return Driven(self.name)

klasses[DrivenOperator.bl_label] = DrivenOperator

class Reassign(bpy.types.Operator):
    bl_label = "Reassign"
    bl_idname = root_dot + "reassign"
    bl_options = {'REGISTER', 'INTERNAL'}
    object_names = bpy.props.CollectionProperty(type=BPY.ObjectNames, name="Objects")
    @classmethod
    def poll(cls, context):
        return hasattr(database.element[context.scene.element_index], "objects")
    def invoke(self, context, event):
        self.entity = database.element[context.scene.element_index]
        self.object_names.clear()
        for obj in self.entity.objects:
            obj_name = self.object_names.add()
            obj_name.value = obj.name
        return context.window_manager.invoke_props_dialog(self)
    def execute(self, context):
        self.entity.objects = [context.scene.objects[obj_name.value] for obj_name in self.object_names]
        return {'FINISHED'}
    def draw(self, context):
        layout = self.layout
        for i, obj_name in enumerate(self.object_names):
            layout.prop(obj_name, "value", text="Obj-" + str(i))
BPY.klasses.append(Reassign)

class DuplicateObs(bpy.types.Operator):
    bl_label = "Duplicate Obs"
    bl_idname = root_dot + "duplicate_obs"
    bl_options = {'REGISTER', 'INTERNAL'}
    @classmethod
    def poll(cls, context):
        return SelectedObjects(context)
    def execute(self, context):
        obs = SelectedObjects(context)
        elements = [element for element in database.element if hasattr(element, "objects") and
            element.objects and element.objects[0] in obs]
        for element in database.element:
            if element.type == 'Driven' and element.links[1] in elements:
                elements.append(element)
        len_element = len(database.element)
        for element in elements:
            context.scene.element_index = database.element.index(element)
            exec("bpy.ops." + root_dot + "d_" + "_".join(element.type.lower().split()) + "()")
        drives = [drive for drive in database.drive if hasattr(drive, "objects") and
            drive.objects and drive.objects[0] in obs]
        len_drive = len(database.drive)
        for drive in drives:
            context.scene.drive_index = database.drive.index(drive)
            exec("bpy.ops." + root_dot + "d_" + "_".join(drive.type.lower().split()) + "()")
            for item in database.element + database.constitutive + database.drive:
                for i, link in enumerate(item.links):
                    if link == drive:
                        item.links[i] = database.drive[-1]
                        drive.users -= 1
                        database.drive[-1].users += 1
        new_obs = list()
        for ob in obs:
            bpy.ops.object.select_all(action='DESELECT')
            ob.select = True
            bpy.ops.object.duplicate()
            new_obs.append(context.selected_objects[0])
        items = elements + drives
        new_items = database.element[len_element:] + database.drive[len_drive:]
        for new_item in new_items:
            for i, ob in enumerate(new_item.objects):
                if ob in obs:
                    new_item.objects[i] = new_obs[obs.index(ob)]
            for i, link in enumerate(new_item.links):
                if link in items:
                    link.users -= 1
                    new_item.links[i] = new_items[items.index(link)]
                    new_item.links[i].users += 1
        frames = [frame for frame in database.frame if frame.objects[0] in obs]
        len_frame = len(database.frame)
        for frame in frames:
            context.scene.frame_index = database.frame.index(frame)
            exec("bpy.ops." + root_dot + "d_" + "_".join(frame.type.lower().split()) + "()")
        for new_frame in database.frame[len_frame:]:
            for i, ob in enumerate(new_frame.objects):
                if ob in obs:
                    new_frame.objects[i] = new_obs[obs.index(ob)]
        bpy.ops.object.select_all(action='DESELECT')
        for ob in new_obs:
            ob.animation_data_clear()
            ob.select = True
        context.scene.dirty_simulator = True
        return {'FINISHED'}
BPY.klasses.append(DuplicateObs)

bundle = Bundle(tree, Base, klasses, database.element, "element")
