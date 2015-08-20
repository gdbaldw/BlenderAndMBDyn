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
    imp.reload(enum_matrix_3x3)
else:
    from .common import (FORMAT, Type, aerodynamic_types, beam_types, force_types, genel_types, joint_types, environment_types, node_types,
        structural_static_types, structural_dynamic_types, Ellipsoid, RhombicPyramid, Teardrop, Cylinder, Sphere, RectangularCuboid)
    from .base import bpy, BPY, root_dot, database, Operator, Entity, Bundle, enum_scenes, enum_matrix_3x1, enum_matrix_3x3, enum_constitutive_1D, enum_constitutive_3D, enum_constitutive_6D, enum_drive, enum_element, enum_friction, SelectedObjects
    from .base import update_constitutive, update_drive, update_element, update_friction, update_matrix, update_scene
    from mathutils import Vector
    from copy import copy
    import os
    import subprocess
    from tempfile import TemporaryFile
    from pickle import Pickler
    from io import StringIO

types = aerodynamic_types + beam_types + ["Body"] + force_types + genel_types + joint_types + environment_types + ["Driven"] + node_types

tree = ["Add Element",
    ["Aerodynamic", aerodynamic_types,
    "Beam", beam_types,
    Type("Body", 1),
    "Force", force_types,
    "GENEL", genel_types,
    "Joint", joint_types,
    "Environment", environment_types,
    "Driven",
    "Node", node_types,
    ]]

class Base(Operator):
    bl_label = "Element"
    exclusive = False
    N_objects = 2
    @classmethod
    def poll(cls, context):
        obs = SelectedObjects(context)
        return ((cls.N_objects == 0 and not (cls.exclusive and database.element.filter(cls.bl_label)))
            or len(obs) == cls.N_objects - 1
            or (len(obs) == cls.N_objects and not (cls.exclusive and database.element.filter(cls.bl_label, obs[0]))))
    def sufficient_objects(self, context):
        objects = SelectedObjects(context)
        if len(objects) == self.N_objects - 1:
            bpy.ops.mesh.primitive_cube_add()
            for obj in objects:
                obj.select = True
            objects.insert(0, context.active_object)
            if 1 < len(objects):
                objects[0].location = objects[1].location
            exec("bpy.ops." + root_dot + "object_specifications('INVOKE_DEFAULT')")
        return objects
    def store(self, context):
        self.entity.objects = self.sufficient_objects(context)
    @classmethod
    def make_list(self, ListItem):
        bpy.types.Scene.element_uilist = bpy.props.CollectionProperty(type = ListItem)
        def select_and_activate(self, context):
            if database.element and self.element_index < len(database.element):
                bpy.ops.object.select_all(action='DESELECT')
                element = database.element[self.element_index]
                if hasattr(element, "objects"):
                    for ob in element.objects:
                        ob.select = True
                    if element.objects and element.objects[0].name in context.scene.objects:
                        context.scene.objects.active = element.objects[0]
                    element.remesh()
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
    def draw_panel_post(self, context, layout):
        selected_obs = set(SelectedObjects(context))
        if selected_obs:
            used_obs = set()
            for e in database.element + database.drive + database.input_card:
                if hasattr(e, "objects"):
                    used_obs.update(set(e.objects))
            if selected_obs.intersection(used_obs):
                layout.menu(root_dot + "selected_objects")
            else:
                layout.operator_context = 'EXEC_DEFAULT'
                layout.operator("object.delete")

klasses = dict()

class StructuralForce(Entity):
    elem_type = "force"
    file_ext = "frc"
    labels = "node Fx Fy Fz X Y Z".split()
    def write(self, text):
        rot_0, globalV_0, Node_0 = self.rigid_offset(0)
        rotT_0 = self.objects[0].matrix_world.to_quaternion().to_matrix()
        relative_dir = rot_0*rotT_0*Vector((0., 0., 1.))
        relative_arm_0 = rot_0*globalV_0
        string = "\tforce: " + FORMAT(database.element.index(self)) + ", " + self.orientation
        if self.orientation == "follower":
            relative_dir = rot_0*rotT_0*Vector((0., 0., 1.))
        else:
            relative_dir = rotT_0*Vector((0., 0., 1.))
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
    drive_name = bpy.props.EnumProperty(items=enum_drive, name="Drive",
        update=lambda self, context: update_drive(self, context, self.drive_name))
    def assign(self, context):
        self.orientation = self.entity.orientation
        self.drive_name = self.entity.links[0].name
    def store(self, context):
        self.entity.orientation = self.orientation
        self.entity.links.append(database.drive.get_by_name(self.drive_name))
        self.entity.objects = self.sufficient_objects(context)
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "orientation")
        layout.prop(self, "drive_name")

class StructuralForceOperator(ForceBase):
    bl_label = "Structural force"
    N_objects = 1
    def create_entity(self):
        return StructuralForce(self.name)

klasses[StructuralForceOperator.bl_label] = StructuralForceOperator

class StructuralInternalForce(Entity):
    elem_type = "force"
    file_ext = "frc"
    labels = "node1 F1x F1y F1z X1 Y1 Z1 node2 F2x F2y F2z X2 Y2 Z2".split()
    def write(self, text):
        rot_0, globalV_0, Node_0 = self.rigid_offset(0)
        rotT_0 = self.objects[0].matrix_world.to_quaternion().to_matrix()
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
    def create_entity(self):
        return StructuralInternalForce(self.name)

klasses[StructuralInternalForceOperator.bl_label] = StructuralInternalForceOperator

class StructuralCouple(Entity):
    elem_type = "couple"
    file_ext = "frc"
    labels = "node Mx My Mz".split()
    def write(self, text):
        rot_0, globalV_0, Node_0 = self.rigid_offset(0)
        rotT_0 = self.objects[0].matrix_world.to_quaternion().to_matrix()
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
    N_objects = 1
    def create_entity(self):
        return StructuralCouple(self.name)

klasses[StructuralCoupleOperator.bl_label] = StructuralCoupleOperator

class StructuralInternalCouple(Entity):
    elem_type = "couple"
    file_ext = "frc"
    labels = "node1 M1x M1y M1z node2 M2x M2y M2z".split()
    def write(self, text):
        rot_0, globalV_0, Node_0 = self.rigid_offset(0)
        rotT_0 = self.objects[0].matrix_world.to_quaternion().to_matrix()
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
    def create_entity(self):
        return StructuralInternalCouple(self.name)

klasses[StructuralInternalCoupleOperator.bl_label] = StructuralInternalCoupleOperator

class Joint(Entity):
    elem_type = "joint"
    file_ext = "jnt"
    labels = "Fx Fy Fz Mx My Mz FX FY FZ MX MY MZ".split()

class Hinge(Joint):
    def write_hinge(self, text, name, V1=True, V2=True, M1=True, M2=True):
        rot_0, globalV_0, Node_0 = self.rigid_offset(0)
        localV_0 = rot_0*globalV_0
        rot_1, globalV_1, Node_1 = self.rigid_offset(1)
        to_hinge = rot_1*(globalV_1 + self.objects[0].matrix_world.translation - self.objects[1].matrix_world.translation)
        rotT = self.objects[0].matrix_world.to_quaternion().to_matrix()
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

class AxialRotation(Hinge):
    def write(self, text):
        self.write_hinge(text, "axial rotation")
        text.write(",\n" + self.links[0].string(True) + ";\n")
    def remesh(self):
        Cylinder(self.objects[0])

class AxialRotationOperator(Base):
    bl_label = "Axial rotation"
    drive_name = bpy.props.EnumProperty(items=enum_drive, name="Drive",
        update=lambda self, context: update_drive(self, context, self.drive_name))
    def assign(self, context):
        self.drive_name = self.entity.links[0].name
    def store(self, context):
        self.entity.links.append(database.drive.get_by_name(self.drive_name))
        self.entity.objects = self.sufficient_objects(context)
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "drive_name")
    def create_entity(self):
        return AxialRotation(self.name)

klasses[AxialRotationOperator.bl_label] = AxialRotationOperator

class Clamp(Joint):
    def write(self, text):
        text.write(
        "\tjoint: " + FORMAT(database.element.index(self)) + ", clamp,\n" +
        "\t\t" + FORMAT(database.node.index(self.objects[0])) + ", node, node;\n")
    def remesh(self):
        Teardrop(self.objects[0])

class ClampOperator(Base):
    bl_label = "Clamp"
    exclusive = True
    N_objects = 1
    def create_entity(self):
        return Clamp(self.name)

klasses[ClampOperator.bl_label] = ClampOperator

class DeformableDisplacementJoint(Hinge):
    labels = "Fx Fy Fz Mx My Mz FX FY FZ MX MY MZ ex ey ez ex_dot ey_dot ez_dot".split()
    def write(self, text):
        self.write_hinge(text, "deformable displacement joint")
        text.write(",\n\t\t" + self.links[0].string() + ";\n")
    def remesh(self):
        Cylinder(self.objects[0])

class ConstitutiveBase(Base):
    dimension = "3D"
    def assign(self, context):
        self.constitutive_name = self.entity.links[0].name
    def store(self, context):
        self.entity.links.append(database.input_card.get_by_name(self.constitutive_name))
        self.entity.objects = self.sufficient_objects(context)
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "constitutive_name")

class DeformableDisplacementJointOperator(ConstitutiveBase):
    bl_label = "Deformable displacement joint"
    constitutive_name = bpy.props.EnumProperty(items=enum_constitutive_3D, name="Constitutive 3D",
        update=lambda self, context: update_constitutive(self, context, self.constitutive_name))
    def create_entity(self):
        return DeformableDisplacementJoint(self.name)

klasses[DeformableDisplacementJointOperator.bl_label] = DeformableDisplacementJointOperator

class DeformableHinge(Hinge):
    def write(self, text):
        self.write_hinge(text, "deformable hinge", V1=False, V2=False)
        text.write(",\n\t\t" + self.links[0].string() + ";\n")
    def remesh(self):
        Sphere(self.objects[0])

class DeformableHingeOperator(ConstitutiveBase):
    bl_label = "Deformable hinge"
    constitutive_name = bpy.props.EnumProperty(items=enum_constitutive_3D, name="Constitutive 3D",
        update=lambda self, context: update_constitutive(self, context, self.constitutive_name))
    def create_entity(self):
        return DeformableJoint(self.name)

klasses[DeformableHingeOperator.bl_label] = DeformableHingeOperator

class DeformableJoint(Hinge):
    labels = "Fx Fy Fz Mx My Mz FX FY FZ MX MY MZ ex ey ez".split()
    def write(self, text):
        self.write_hinge(text, "deformable joint")
        text.write(",\n\t\t" + self.links[0].string() + ";\n")
    def remesh(self):
        Sphere(self.objects[0])

class DeformableJointOperator(ConstitutiveBase):
    bl_label = "Deformable joint"
    constitutive_name = bpy.props.EnumProperty(items=enum_constitutive_3D, name="Constitutive 3D",
        update=lambda self, context: update_constitutive(self, context, self.constitutive_name))
    def create_entity(self):
        return DeformableJoint(self.name)

klasses[DeformableJointOperator.bl_label] = DeformableJointOperator

class Distance(Joint):
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
    exclusive = True
    from_nodes = bpy.props.BoolProperty(name="From nodes", description="Constant distance from initial node positons", default=True)
    drive_name = bpy.props.EnumProperty(items=enum_drive, name="Drive",
        update=lambda self, context: update_drive(self, context, self.drive_name))
    def assign(self, context):
        self.from_nodes = self.entity.from_nodes
        if self.entity.links:
            self.drive_name = self.entity.links[0].name
    def store(self, context):
        self.entity.from_nodes = self.from_nodes
        if not self.from_nodes:
            self.entity.links.append(database.drive.get_by_name(self.drive_name))
        self.entity.objects = self.sufficient_objects(context)
    def draw(self, context):
        self.basis = self.from_nodes
        layout = self.layout
        layout.prop(self, "from_nodes")
        if not self.from_nodes:
            layout.prop(self, "drive_name")
    def check(self, context):
        return self.basis != self.from_nodes
    def create_entity(self):
        return Distance(self.name)

klasses[DistanceOperator.bl_label] = DistanceOperator

class InLine(Joint):
    def write(self, text):
        rot0, globalV0, iNode0 = self.rigid_offset(0)
        localV0 = rot0*globalV0
        rot_1, globalV_1, Node_1 = self.rigid_offset(1)
        to_point = rot_1*(globalV_1 + self.objects[0].matrix_world.translation - self.objects[1].matrix_world.translation)
        rot = self.objects[0].matrix_world.to_quaternion().to_matrix()
        text.write("\tjoint: " + FORMAT(database.element.index(self)) + ", inline,\n")
        self.write_node(text, 0, node=True, position=True, orientation=True)
        text.write(",\n\t\t" + FORMAT(Node_1))
        text.write(",\n\t\t\toffset, ")
        self.write_vector(to_point, text, ";\n")
    def remesh(self):
        RhombicPyramid(self.objects[0])

class InLineOperator(Base):
    bl_label = "Inline"
    def create_entity(self):
        return InLine(self.name)

klasses[InLineOperator.bl_label] = InLineOperator

class InPlane(Joint):
    def write(self, text):
        rot0, globalV0, iNode0 = self.rigid_offset(0)
        localV0 = rot0*globalV0
        rot1, globalV1, iNode1 = self.rigid_offset(1)
        to_point = rot1*(globalV1 + self.objects[0].matrix_world.translation - self.objects[1].matrix_world.translation)
        rot = self.objects[0].matrix_world.to_quaternion().to_matrix()
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
    bl_label = "Inplane"
    def create_entity(self):
        return InPlane(self.name)

klasses[InPlaneOperator.bl_label] = InPlaneOperator

class RevoluteHinge(Hinge):
    labels = "Fx Fy Fz Mx My Mz FX FY FZ MX MY MZ ex ey ez Ax Ay Az Ax_dot Ay_dot Az_dot".split()
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
    friction_name = bpy.props.EnumProperty(items=enum_friction, name="Friction",
        update=lambda self, context: update_friction(self, context, self.friction_name))
    def assign(self, context):
        self.enable_theta = self.entity.enable_theta
        self.theta = self.entity.theta
        self.enable_friction = self.entity.enable_friction
        self.average_radius = self.entity.average_radius
        self.enable_preload = self.entity.enable_preload
        self.preload = self.entity.preload
    def store(self, context):
        self.entity.enable_theta = self.enable_theta
        self.entity.theta = self.theta
        self.entity.enable_friction = self.enable_friction
        self.entity.average_radius = self.average_radius
        self.entity.enable_preload = self.enable_preload
        self.entity.preload = self.preload
        if self.enable_friction:
            self.entity.links.append(database.friction.get_by_name(self.friction_name))
        self.entity.objects = self.sufficient_objects(context)
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
            layout.prop(self, "friction_name")
    def check(self, context):
        return self.basis != (self.enable_theta, self.enable_friction, self.enable_preload)
    def create_entity(self):
        return RevoluteHinge(self.name)

klasses[RevoluteHingeOperator.bl_label] = RevoluteHingeOperator

class Rod(Joint):
    labels = "Fx Fy Fz Mx My Mz FX FY FZ MX MY MZ l ux uy uz l_dot".split()
    def write(self, text):
        text.write("\tjoint: " + FORMAT(database.element.index(self)) + ", rod,\n")
        for i in range(2):
            self.write_node(text, i, node=True, position=True, p_label="position")
            text.write(",\n")
        text.write("\t\tfrom nodes,\n\t\t" + self.links[0].string() + ";\n")

class RodOperator(ConstitutiveBase):
    bl_label = "Rod"
    dimension = "1D"
    constitutive_name = bpy.props.EnumProperty(items=enum_constitutive_1D, name="Constitutive 1D",
        update=lambda self, context: update_constitutive(self, context, self.constitutive_name))
    def create_entity(self):
        return Rod(self.name)

klasses[RodOperator.bl_label] = RodOperator

class SphericalHinge(Hinge):
    def write(self, text):
        self.write_hinge(text, "spherical hinge")
        text.write(";\n")
    def remesh(self):
        Sphere(self.objects[0])

class SphericalHingeOperator(Base):
    bl_label = "Spherical hinge"
    def create_entity(self):
        return SphericalHinge(self.name)

klasses[SphericalHingeOperator.bl_label] = SphericalHingeOperator

class TotalJoint(Joint):
    labels = "Fx Fy Fz Mx My Mz FX FY FZ MX MY MZ dx dy dz dAx dAy dAz u v w dAx_dor dAy_dot dAz_dot".split()
    def write(self, text):
        rot_0, globalV_0, Node_0 = self.rigid_offset(0)
        localV_0 = rot_0*globalV_0
        rot_1, globalV_1, Node_1 = self.rigid_offset(1)
        to_joint = rot_1*(globalV_1 + self.objects[0].matrix_world.translation - self.objects[1].matrix_world.translation)
        rot = self.objects[0].matrix_world.to_quaternion().to_matrix()
        if Node_1 == self.objects[1]:
            rot_position = rot
        else:
            rot_position = self.objects[1].matrix_world.to_quaternion().to_matrix()
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
        database.drive_indenture += 2
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
        database.drive_indenture -= 2
        text.write(";\n")
    def remesh(self):
        Sphere(self.objects[0])

class TotalJointOperator(Base):
    bl_label = "Total joint"
    first = bpy.props.EnumProperty(items=[("displace", "Displace first", ""), ("rotate", "Rotate first", "")], default="displace")
    displacement_x = bpy.props.BoolProperty(name="", description="Displacement-X drive is active", default=False)
    displacement_x_drive_name = bpy.props.EnumProperty(items=enum_drive, name="Displacement-X Drive",
        update=lambda self, context: update_drive(self, context, self.displacement_x_drive_name))
    displacement_y = bpy.props.BoolProperty(name="", description="Displacement-Y drive is active", default=False)
    displacement_y_drive_name = bpy.props.EnumProperty(items=enum_drive, name="Displacement-Y Drive",
        update=lambda self, context: update_drive(self, context, self.displacement_y_drive_name))
    displacement_z = bpy.props.BoolProperty(name="", description="Displacement-Z drive is active", default=False)
    displacement_z_drive_name = bpy.props.EnumProperty(items=enum_drive, name="Displacement-Z Drive",
        update=lambda self, context: update_drive(self, context, self.displacement_z_drive_name))
    angular_displacement_x = bpy.props.BoolProperty(name="", description="Angular Displacement-X drive is active", default=False)
    angular_displacement_x_drive_name = bpy.props.EnumProperty(items=enum_drive, name="Angular Displacement-X Drive",
        update=lambda self, context: update_drive(self, context, self.angular_displacement_x_drive_name))
    angular_displacement_y = bpy.props.BoolProperty(name="", description="Angular Displacement-Y drive is active", default=False)
    angular_displacement_y_drive_name = bpy.props.EnumProperty(items=enum_drive, name="Angular Displacement-Y Drive",
        update=lambda self, context: update_drive(self, context, self.angular_displacement_y_drive_name))
    angular_displacement_z = bpy.props.BoolProperty(name="", description="Angular Displacement-Z drive is active", default=False)
    angular_displacement_z_drive_name = bpy.props.EnumProperty(items=enum_drive, name="Angular Displacement-Z Drive",
        update=lambda self, context: update_drive(self, context, self.angular_displacement_z_drive_name))
    def assign(self, context):
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
        self.entity.first = self.first
        self.entity.displacement_x = self.displacement_x
        self.entity.displacement_y = self.displacement_y
        self.entity.displacement_z = self.displacement_z
        self.entity.angular_displacement_x = self.angular_displacement_x
        self.entity.angular_displacement_y = self.angular_displacement_y
        self.entity.angular_displacement_z = self.angular_displacement_z
        for drive_name in [self.displacement_x_drive_name, self.displacement_y_drive_name,
            self.displacement_z_drive_name, self.angular_displacement_x_drive_name,
            self.angular_displacement_y_drive_name, self.angular_displacement_z_drive_name]:
                self.entity.links.append(database.drive.get_by_name(drive_name))
        self.entity.objects = self.sufficient_objects(context)
    def draw(self, context):
        self.basis = (self.displacement_x)
        layout = self.layout
        for predicate in ["displacement_", "angular_displacement_"]:
            for c in "xyz":
                row = layout.row()
                row.prop(self, predicate + c)
                row.prop(self, predicate + c + "_drive_name")
    def create_entity(self):
        return TotalJoint(self.name)

klasses[TotalJointOperator.bl_label] = TotalJointOperator

class ViscousBody(Joint):
    def write(self, text):
        text.write(
        "\tjoint: " + FORMAT(database.element.index(self)) + ", viscous body,\n\t\t" +
        FORMAT(database.node.index(self.objects[0]))+
        ",\n\t\tposition, reference, node, null" +
        ",\n\t\t" + self.links[0].string() + ";\n")
    def remesh(self):
        Sphere(self.objects[0])

class ViscousBodyOperator(Base):
    bl_label = "Viscous body"
    N_objects = 1
    constitutive_name = bpy.props.EnumProperty(items=enum_constitutive_6D, name="Constitutive 6D",
        update=lambda self, context: update_constitutive(self, context, self.constitutive_name))
    def assign(self, context):
        self.constitutive_name = self.entity.links[0].name
        self.object = self.entity.objects[0]
    def store(self, context):
        self.entity.links.append(database.input_card.get_by_name(self.constitutive_name))
        self.entity.objects = self.sufficient_objects(context)
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "constitutive_name")
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
    N_objects = 1
    mass = bpy.props.FloatProperty(name="Mass", description="Mass of the body", min=0.000001, max=9.9e10, precision=6, default=1.0)
    matrix_name = bpy.props.EnumProperty(items=enum_matrix_3x3, name="Matrix", description="Matrix of inertia",
        update=lambda self, context: update_matrix(self, context, self.matrix_name, "3x3"))
    def assign(self, context):
        self.mass = self.entity.mass
        self.matrix_name = self.entity.links[0].name
    def store(self, context):
        self.entity.mass = self.mass
        self.entity.links.append(database.matrix.get_by_name(self.matrix_name))
        self.entity.objects = self.sufficient_objects(context)
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "mass")
        layout.prop(self, "matrix_name")
    def create_entity(self):
        return Body(self.name)

klasses[BodyOperator.bl_label] = BodyOperator

class RigidOffset(Entity):
    def remesh(self):
        RhombicPyramid(self.objects[0])

class RigidOffsetOperator(Base):
    bl_label = "Rigid offset"
    exclusive = True
    def store(self, context):
        self.entity.objects = self.sufficient_objects(context)
        self.entity.objects[0].parent = self.entity.objects[1]
        self.entity.objects[0].matrix_parent_inverse = self.entity.objects[1].matrix_basis.inverted()
    def create_entity(self):
        return RigidOffset(self.name)

klasses[RigidOffsetOperator.bl_label] = RigidOffsetOperator

class DummyNode(Entity):
    def remesh(self):
        RhombicPyramid(self.objects[0])

class DummyNodeOperator(Base):
    bl_label = "Dummy node"
    exclusive = True
    def create_entity(self):
        return DummyNode(self.name)

klasses[DummyNodeOperator.bl_label] = DummyNodeOperator

class BeamSegment(Entity):
    elem_type = "beam2"
    file_ext = "act"
    labels = "Fx Fy Fz Mx My Mz".split()
    def write(self, text):
        if [e for e in database.element if e.type == "Three node beam" and self in e.links]:
            return
        text.write("\tbeam2: " + str(database.element.index(self)) + ",\n")
        for i in range(len(self.objects)):
            self.write_node(text, i, node=True, position=True, orientation=True, p_label="position", o_label="orientation")
            text.write(",\n")
        text.write("\t\tfrom nodes, " + self.links[0].string() + ";\n")
    def remesh(self):
        for obj in self.objects:
            RectangularCuboid(obj)

class BeamSegmentOperator(ConstitutiveBase):
    bl_label = "Beam segment"
    dimension = "6D"
    constitutive_name = bpy.props.EnumProperty(items=enum_constitutive_6D, name="Constitutive 6D",
        update=lambda self, context: update_constitutive(self, context, self.constitutive_name, "6D"))
    def create_entity(self):
        return BeamSegment(self.name)

klasses[BeamSegmentOperator.bl_label] = BeamSegmentOperator

class SegmentPair:
    @classmethod
    def segments(cls, context, segment_type="Beam segment"):
        segments = list()
        for ob in SelectedObjects(context):
            segments.extend(database.element.filter(segment_type, ob))
        if len(segments) == 2 and not segments[0].objects[1] == segments[1].objects[0]:
            segments.reverse()
        if len(segments) != 2 or not segments[0].objects[1] == segments[1].objects[0]:
            return list()
        return segments

class ThreeNodeBeam(Entity):
    elem_type = "beam3"
    file_ext = "act"
    labels = "F1x F1y F1z M1x M1y M1z F2x F2y F2z M2x M2y M2z".split()
    def write(self, text):
        text.write("\tbeam3: " + str(database.element.index(self)) + ",\n")
        self.objects = self.links[0].objects + self.links[1].objects[1:]
        for i in range(3):
            self.write_node(text, i, node=True, position=True, orientation=True, p_label="position", o_label="orientation")
            text.write(",\n")
        text.write("\t\tfrom nodes, " + self.links[0].links[0].string())
        text.write(",\n\t\tfrom nodes, " + self.links[1].links[0].string() + ";\n")
        del self.objects
    def remesh(self):
        for link in self.links:
            link.remesh()

class ThreeNodeBeamOperator(Base, SegmentPair):
    bl_label = "Three node beam"
    N_objects = 0
    edit = bpy.props.BoolVectorProperty(name="", size=2)
    @classmethod
    def poll(cls, context):
        segments = cls.segments(context, "Beam segment")
        ret = True if segments else False
        for s in segments:
            if hasattr(s, "consumer") and not database.element.index(s.consumer) == context.scene.element_index:
                ret = False
        return ret
    def prereqs(self, context):
        self.beam_segments = self.segments(context, "Beam segment")
    def store(self, context):
        for segment, edit in zip(self.beam_segments, self.edit):
            self.entity.links.append(segment)
            segment.consumer = self.entity
            if edit:
                update_element(self, context, segment.name)
        self.entity.objects = self.beam_segments[0].objects + self.beam_segments[1].objects[1:]
    def draw(self, context):
        layout = self.layout
        for i, element in enumerate(self.beam_segments):
            row = layout.row()
            row.prop(self, "edit", index=i, toggle=True)
            row.label(element.name)
    def create_entity(self):
        return ThreeNodeBeam(self.name)

klasses[ThreeNodeBeamOperator.bl_label] = ThreeNodeBeamOperator

class Gravity(Entity):
    elem_type = "gravity"
    file_ext = "grv"
    labels = "X_dotdot Y_dotdot Z_dotdot".split()
    def write(self, text):
        text.write("\tgravity: " + self.links[0].string() + ", " + self.links[1].string() + ";\n")

class GravityOperator(Base):
    bl_label = "Gravity"
    matrix_name = bpy.props.EnumProperty(items=enum_matrix_3x1, name="Vector",
        update=lambda self, context: update_matrix(self, context, self.matrix_name, "3x1"))
    drive_name = bpy.props.EnumProperty(items=enum_drive, name="Drive",
        update=lambda self, context: update_drive(self, context, self.drive_name))
    @classmethod
    def poll(cls, context):
        return cls.bl_idname.startswith(root_dot+"e_") or not database.element.filter("Gravity")
    def assign(self, context):
        self.matrix_name = self.entity.links[0].name
        self.drive_name = self.entity.links[1].name
    def store(self, context):
        self.entity.links.append(database.matrix.get_by_name(self.matrix_name))
        self.entity.links.append(database.drive.get_by_name(self.drive_name))
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "matrix_name")
        layout.prop(self, "drive_name")
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
    drive_name = bpy.props.EnumProperty(items=enum_drive, name="Drive",
        update=lambda self, context: update_drive(self, context, self.drive_name))
    element_name = bpy.props.EnumProperty(items=enum_element, name="Element",
        update=lambda self, context: update_element(self, context, self.element_name))
    @classmethod
    def poll(cls, context):
        return context.scene.element_uilist
    def prereqs(self, context):
        self.element_name = context.scene.element_uilist[context.scene.element_index].name
    def assign(self, context):
        self.drive_name = self.entity.links[0].name
        self.element_name = self.entity.links[1].name
    def store(self, context):
        self.entity.links.append(database.drive.get_by_name(self.drive_name))
        self.entity.links.append(database.element.get_by_name(self.element_name))
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "drive_name")
        layout.prop(self, "element_name")
    def create_entity(self):
        return Driven(self.name)

klasses[DrivenOperator.bl_label] = DrivenOperator

class Plot:
    bl_options = {'REGISTER', 'INTERNAL'}
    prereqs_met = bpy.props.BoolProperty(default=False)
    label_names = bpy.props.CollectionProperty(type=BPY.Names, name="Users")
    def load(self, context, exts, pd):
        if not self.prereqs_met:
            for prereq in "pandas matplotlib.pyplot".split():
                if subprocess.call(("python", "-c", "import " + prereq)):
                    raise ImportError("No module named " + prereq)
            self.prereqs_met = True
        self.base = os.path.join(os.path.splitext(context.blend_data.filepath)[0], context.scene.name)
        if 'frequency' not in BPY.plot_data:
            with open(".".join((self.base, "log")), 'r') as f:
                for line in f:
                    if line.startswith("output frequency:"):
                        BPY.plot_data['frequency'] = int(line.split()[-1])
                        break
        if 'out' not in BPY.plot_data:
            BPY.plot_data['out'] = pd.read_table(".".join((self.base, 'out')), sep=" ", skiprows=2, usecols=[i for i in range(2, 9)])
            BPY.plot_data['timeseries'] = BPY.plot_data['out']['Time'][::BPY.plot_data['frequency']]
        for ext in exts:
            if ext not in BPY.plot_data:
                df = pd.read_csv(".".join((self.base, ext)), sep=" ", header=None, skipinitialspace=True, names=[i for i in range(50)], lineterminator="\n")
                value_counts = df[0].value_counts()
                p = dict()
                for node_label in df[0].unique():
                    p[str(int(node_label))] = df.ix[df[0]==node_label, 1:].dropna(1, 'all')
                    p[str(int(node_label))].index = [i for i in range(value_counts[node_label])]
                BPY.plot_data[ext] = pd.Panel(p)
    def execute(self, context):
        select = [name.select for name in self.label_names]
        if True in select:
            dataframe = self.dataframe.T[select].T.rename(BPY.plot_data['timeseries'])
            dataframe.columns = [name.value for name in self.label_names if name.select]
            plot_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plot.py")
            with TemporaryFile('w') as f:
                f.write(self.entity.name + "\n")
                dataframe.to_csv(f)
                f.seek(0)
                subprocess.Popen(("python", plot_script), stdin=f)
        elif self.label_names:
            self.report({'ERROR'}, "None selected.")
        return{'FINISHED'}
    def draw(self, context):
        layout = self.layout
        for name in self.label_names:
            row = layout.row()
            row.prop(name, "select")
            row.label(name.value)

class PlotElement(bpy.types.Operator, Plot):
    bl_label = "Plot output"
    bl_idname = root_dot + "plot_element"
    @classmethod
    def poll(cls, context):
        return context.scene.clean_log and hasattr(database.element[context.scene.element_index], "file_ext")
    def invoke(self, context, event):
        self.entity = database.element[context.scene.element_index]
        import pandas as pd
        self.load(context, [self.entity.file_ext], pd)
        self.label_names.clear()
        key = "1" if self.entity.file_ext == "grv" else str(database.element.index(self.entity))
        self.dataframe = BPY.plot_data[self.entity.file_ext][key].dropna(1, 'all')
        for i in range(self.dataframe.shape[1]):
            name = self.label_names.add()
            name.value = self.entity.labels[i] if i < len(self.entity.labels) else str(i + 2)
            name.select = False
        return context.window_manager.invoke_props_dialog(self)
BPY.klasses.append(PlotElement)

class PlotNode(bpy.types.Operator, Plot):
    bl_label = "Plot the node"
    bl_idname = root_dot + "plot_node"
    @classmethod
    def poll(cls, context):
        obs = SelectedObjects(context)
        return context.scene.clean_log and len(obs) == 1 and obs[0] in database.node
    def invoke(self, context, event):
        self.entity = SelectedObjects(context)[0]
        import pandas as pd
        self.load(context, "ine mov".split(), pd)
        node_label = str(database.node.index(SelectedObjects(context)[0]))
        self.dataframe = BPY.plot_data['mov'][node_label].dropna(1, 'all')
        #self.dataframe.columns = "X Y Z Phi_x Phi_y Phi_z U V W Omega_x Omega_y Omeda_z dU/dt dV/dt dW/dt dOmega_x/dt dOmega_y/dt dOmega_z/dt 20 21 22 23 24 25".split()[:self.dataframe.shape[1]]
        self.dataframe.columns = "X Y Z".split() + [str(i) for i in range(5, self.dataframe.shape[1] + 2)]
        if node_label in BPY.plot_data['ine']:
            df = BPY.plot_data['ine'][node_label].dropna(1, 'all')
            df.columns = "px py pz Lx Ly Lz dpx/dt dpy/dt dpz/dt dLx/dt dLy/dt dLz/dt".split()
            self.dataframe = self.dataframe.join(df)
        self.label_names.clear()
        for label in self.dataframe.columns:
            name = self.label_names.add()
            name.value = label
            name.select = False
        return context.window_manager.invoke_props_dialog(self)
BPY.klasses.append(PlotNode)

class DuplicateObjects(bpy.types.Operator):
    bl_label = "Duplicate"
    bl_idname = root_dot + "duplicate_objects"
    bl_options = {'REGISTER', 'INTERNAL'}
    full_copy = bpy.props.BoolProperty(default=False, name="Full copy")
    to_scene = bpy.props.EnumProperty(items=enum_scenes, name="Scene",
        update=lambda self, context: update_scene(self, context, self.to_scene))
    entity_names = bpy.props.CollectionProperty(type=BPY.Names, name="Users")
    @classmethod
    def poll(cls, context):
        return SelectedObjects(context)
    def invoke(self, context, event):
        self.full_copy = False
        self.entity_names.clear()
        self.users = database.entities_originating_from(SelectedObjects(context))
        for user in self.users:
            name = self.entity_names.add()
            name.value = user.name
            name.select = True
        return context.window_manager.invoke_props_dialog(self)
    def execute(self, context):
        obs = SelectedObjects(context)
        elements, drives, frames = list(), list(), list()
        for user in [u for u, n in zip(self.users, self.entity_names) if n.select]:
            module = user.__module__.split(".")[-1]
            if user.type == "Reference frame":
                frames.append(user)
            elif module == "drive":
                drives.append(user)
            else:
                elements.append(user)
        #elements = [element for element in database.element if hasattr(element, "objects") and
        #    element.objects and element.objects[0] in obs]
        #for element in database.element:
        #    if element.type == 'Driven' and element.links[1] in elements:
        #        elements.append(element)
        len_element = len(database.element)
        for element in elements:
            context.scene.element_index = database.element.index(element)
            exec("bpy.ops." + root_dot + "d_" + "_".join(element.type.lower().split()) + "()")
        #drives = [drive for drive in database.drive if hasattr(drive, "objects") and
        #    drive.objects and drive.objects[0] in obs]
        len_drive = len(database.drive)
        for drive in drives:
            context.scene.drive_index = database.drive.index(drive)
            exec("bpy.ops." + root_dot + "d_" + "_".join(drive.type.lower().split()) + "()")
            for entity in database.element + database.input_card + database.drive:
                for i, link in enumerate(entity.links):
                    if link == drive:
                        entity.links[i] = database.drive[-1]
                        drive.users -= 1
                        database.drive[-1].users += 1
        new_obs = dict()
        for ob in obs:
            bpy.ops.object.select_all(action='DESELECT')
            ob.select = True
            bpy.ops.object.duplicate()
            new_obs[ob] = context.selected_objects[0]
        #frames = [frame for frame in database.frame if frame.objects[0] in obs]
        len_input_card = len(database.input_card)
        for frame in frames:
            context.scene.input_card_index = database.input_card.index(frame)
            exec("bpy.ops." + root_dot + "d_" + "_".join(frame.type.lower().split()) + "()")
        new_frames = database.input_card[len_input_card:]
        for frame in new_frames:
            old_objects = frame.objects
            frame.objects = [new_obs[ob] for ob in old_objects if ob in obs]
        entities = elements + drives
        new_entities = database.element[len_element:] + database.drive[len_drive:]
        for entity in new_entities:
            if hasattr(entity, "objects"):
                for i, ob in enumerate(entity.objects):
                    if ob in obs:
                        entity.objects[i] = new_obs[ob]
            for i, link in enumerate(entity.links):
                if link in entities:
                    link.users -= 1
                    entity.links[i] = new_entities[entities.index(link)]
                    entity.links[i].users += 1
                if hasattr(link, "consumer"):
                    link.consumer = entity
            if entity.type == "Rigid offset":
                entity.objects[0].parent = entity.objects[1]
                entity.objects[0].matrix_parent_inverse = entity.objects[1].matrix_basis.inverted()
        if self.full_copy:
            new_links = dict()
            may_have_links = copy(new_entities + new_frames)
            while may_have_links:
                entity = may_have_links.pop()
                for i, link in enumerate(entity.links):
                    if link not in entities and not hasattr(link, "consumer"):
                        link.users -= 1
                        if link not in new_links:
                            database.to_be_duplicated = link
                            exec("bpy.ops." + root_dot + "d_" + "_".join(link.type.lower().split()) + "(attach_duplicate=True)")
                            new_links[link] = database.dup
                            del database.dup
                        entity.links[i] = new_links[link]
                        entity.links[i].users += 1
                    may_have_links.extend(link.links)
        bpy.ops.object.select_all(action='DESELECT')
        for ob in new_obs.values():
            ob.animation_data_clear()
            ob.select = True
        if self.to_scene != context.scene.name:
            parent = dict()
            for ob in new_obs.values():
                parent[ob] = ob.parent
            for ob in new_obs.values():
                context.scene.objects.unlink(ob)
            for entity in new_entities + new_frames + list(new_links.values()):
                database.to_be_unlinked = entity
                exec("bpy.ops." + root_dot + "u_" + "_".join(entity.type.lower().split()) + "()")
            context.screen.scene = bpy.data.scenes[self.to_scene]
            database.pickle()
            for entity in new_entities + new_frames + list(new_links.values()):
                database.to_be_linked = entity
                exec("bpy.ops." + root_dot + "l_" + "_".join(entity.type.lower().split()) + "()")
            for ob in new_obs.values():
                context.scene.objects.link(ob)
            for ob in new_obs.values():
                ob.parent = parent[ob]
        context.scene.dirty_simulator = True
        return {'FINISHED'}
    def draw(self, context):
        self.basis = self.full_copy
        layout = self.layout
        row = layout.row()
        row.prop(self, "full_copy")
        if self.full_copy:
            row.prop(self, "to_scene")
        for name in self.entity_names:
            row = layout.row()
            row.prop(name, "select", toggle=True)
            row.label(name.value)
    def check(self, context):
        return self.basis != self.full_copy
BPY.klasses.append(DuplicateObjects)

class Users(bpy.types.Operator):
    bl_label = "Users"
    bl_idname = root_dot + "users"
    bl_options = {'REGISTER', 'INTERNAL'}
    entity_names = bpy.props.CollectionProperty(type=BPY.Names, name="Users")
    @classmethod
    def poll(cls, context):
        return SelectedObjects(context)
    def invoke(self, context, event):
        self.entity_names.clear()
        self.users = database.entities_using(SelectedObjects(context))
        for user in self.users:
            name = self.entity_names.add()
            name.value = user.name
        return context.window_manager.invoke_props_dialog(self)
    def execute(self, context):
        for name, user in zip(self.entity_names, self.users):
            if name.select:
                context.scene[user.__module__.split(".")[-1] + "_index"] = user.entity_list.index(user)
                exec("bpy.ops." + root_dot + "e_" + "_".join(user.type.lower().split()) + "('INVOKE_DEFAULT')")
        return {'FINISHED'}
    def draw(self, context):
        layout = self.layout
        for name in self.entity_names:
            row = layout.row()
            row.prop(name, "select", toggle=True)
            row.label(name.value)
    def check(self, context):
        return False
BPY.klasses.append(Users)

class ObjectSpecifications(bpy.types.Operator):
    bl_label = "Object specifications"
    bl_idname = root_dot + "object_specifications"
    bl_options = {'REGISTER', 'INTERNAL'}
    @classmethod
    def poll(cls, context):
        return SelectedObjects(context)
    def invoke(self, context, event):
        self.objects = SelectedObjects(context)
        return context.window_manager.invoke_props_dialog(self)
    def execute(self, context):
        return {'FINISHED'}
    def draw(self, context):
        self.basis = [obj.rotation_mode for obj in self.objects]
        layout = self.layout
        for i, obj in enumerate(self.objects):
            layout.label("")
            layout.prop(obj, "name", text="")
            layout.prop(obj, "location")
            if obj.rotation_mode == 'QUATERNION':
                layout.prop(obj, "rotation_quaternion")
            elif obj.rotation_mode == 'AXIS_ANGLE':
                layout.prop(obj, "rotation_axis_angle")
            else:
                layout.prop(obj, "rotation_euler")
            layout.prop(obj, "rotation_mode")
    def check(self, context):
        return self.basis != [obj.rotation_mode for obj in self.objects]
BPY.klasses.append(ObjectSpecifications)

class Menu(bpy.types.Menu):
    bl_label = "Selected Objects"
    bl_idname = root_dot + "selected_objects"
    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator(root_dot + "users")
        layout.operator(root_dot + "duplicate_objects")
        layout.operator(root_dot + "plot_node")
BPY.klasses.append(Menu)

for t in types:
    class Tester(Base):
        bl_label = t[0] if isinstance(t, tuple) else t
        @classmethod
        def poll(cls, context):
            return False
        def create_entity(self):
            return Entity(self.name)
    if Tester.bl_label not in klasses:
        klasses[Tester.bl_label] = Tester

bundle = Bundle(tree, Base, klasses, database.element, "element")
