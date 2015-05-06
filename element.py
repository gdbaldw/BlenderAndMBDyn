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
    imp.reload(bmesh)
    imp.reload(root_dot)
    imp.reload(Operator)
    imp.reload(Entity)
    imp.reload(enum_objects)
    imp.reload(enum_matrix_3x3)
else:
    from .common import (aerodynamic_types, beam_types, force_types, genel_types, joint_types, environment_types, node_types,
        structural_static_types, structural_dynamic_types, Ellipsoid, RhombicPyramid, Teardrop, Cylinder, Sphere)
    from .base import bpy, root_dot, Operator, Entity, enum_objects, enum_matrix_3x1, enum_matrix_3x3, enum_constitutive_1D, enum_constitutive_3D, enum_constitutive_6D, enum_drive, enum_friction, SelectedObjects
    import bmesh
    from mathutils import Vector

types = aerodynamic_types + beam_types + ["Body"] + force_types + genel_types + joint_types + ["Rotor"] + environment_types + ["Driven"] + node_types

tree = ["Add Element",
    ["Aerodynamic", aerodynamic_types,
    ],["Beam", beam_types,
    ],["Body",
    ],["Force", force_types,
    ],["GENEL", genel_types,
    ],["Joint", joint_types,
    ],["Rotor",
    ],["Environment", environment_types,
    ],["Driven",
    ],["Node", node_types,
    ]]

class Base(Operator):
    bl_label = "Elements"
    @classmethod
    def base_poll(self, cls, context, N=None):
        obs = SelectedObjects(context)
        if N:
            test = len(obs) == N and not cls.database.element.filter(cls.bl_label, obs[0])
        else:
            test = not cls.database.element.filter(cls.bl_label)
        return cls.bl_idname.startswith(root_dot+"e_") or test
    @classmethod
    def make_list(self, ListItem):
        bpy.types.Scene.element_uilist = bpy.props.CollectionProperty(type = ListItem)
        def select_and_activate(self, context):
            if Operator.database.element and self.element_index < len(Operator.database.element):
                if hasattr(Operator.database.element[self.element_index], "objects"):
                    bpy.ops.object.select_all(action='DESELECT')
                    for ob in Operator.database.element[self.element_index].objects:
                        ob.select = True
                    context.scene.objects.active = Operator.database.element[self.element_index].objects[0]
                elif Operator.database.element[self.element_index].type in ["Gravity", "Air properties"]:
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

classes = dict()

for t in types:
    class Tester(Base):
        bl_label = t
        @classmethod
        def poll(cls, context):
            return False
        def defaults(self, context):
            pass
        def assign(self, context):
            self.entity = self.database.element[context.scene.element_index]
        def store(self, context):
            self.entity = self.database.element[context.scene.element_index]
        def create_entity(self):
            return Entity(self.name)
    classes[t] = Tester

class StructuralForce(Entity):
    def write(self, text):
        rot_0, globalV_0, Node_0 = self.rigid_offset(0)
        rotT_0 = self.objects[0].matrix_world.to_quaternion().to_matrix().transposed()
        relative_dir = rot_0*rotT_0*Vector((0., 0., 1.))
        relative_arm_0 = rot_0*globalV_0
        string = "\tforce: "+str(self.database.element.index(self))+", "
        if self.orientation == "follower":
            string += "follower"
            relative_dir = rot_0*rotT_0*Vector((0., 0., 1.))
        else:
            string += "absolute"
            relative_dir = rotT_0*Vector((0., 0., 1.))
        relative_dir = self.round_vector(relative_dir)
        relative_arm_0 = self.round_vector(relative_arm_0)
        text.write(string+
        ",\n\t\t"+str(Node_0)+
        ",\n\t\t\tposition, ")
        self.locationVector_write(relative_arm_0, text, ",\n\t\t\t")
        self.locationVector_write(relative_dir, text, ",\n\t\t")
        text.write(self.links[0].string(self)+";\n")

class StructuralForceOperator(Base):
    bl_label = "Structural force"
    orientation = bpy.props.EnumProperty(items=[("follower", "Follower", ""), ("absolute", "Absolute", "")], name="Force orientation")
    drive_name = bpy.props.EnumProperty(items=enum_drive, name="Drive")
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context, 1)
    def defaults(self, context):
        self.orientation = "follower"
        self.drive_exists(context)
    def assign(self, context):
        self.entity = self.database.element[context.scene.element_index]
        self.orientation = self.entity.orientation
        self.drive_name = self.entity.links[0].name
    def store(self, context):
        self.entity = self.database.element[context.scene.element_index]
        self.entity.objects = SelectedObjects(context)
        self.entity.orientation = self.orientation
        self.entity.unlink_all()
        self.link_drive(context, self.drive_name)
        self.entity.increment_links()
        RhombicPyramid(self.entity.objects[0])
    def create_entity(self):
        return StructuralForce(self.name)

classes[StructuralForceOperator.bl_label] = StructuralForceOperator

class StructuralInternalForce(Entity):
    def write(self, text):
        rot_0, globalV_0, Node_0 = self.rigid_offset(0)
        rotT_0 = self.objects[0].matrix_world.to_quaternion().to_matrix().transposed()
        relative_arm_0 = rot_0*globalV_0
        rot_1, globalV_1, Node_1 = self.rigid_offset(1)
        relative_arm_1 = rot_1*globalV_1
        string = "\tforce: "+str(self.database.element.index(self))+", "
        if self.orientation == "follower":
            string += "follower internal"
            relative_dir = rot_0*rotT_0*Vector((0., 0., 1.))
        else:
            string += "absolute internal"
            relative_dir = rotT_0*Vector((0., 0., 1.))
        text.write(string+
        ",\n\t\t"+str(Node_0)+",\n\t\t\t")
        self.locationVector_write(relative_dir, text, ",\n\t\t\t")
        self.locationVector_write(relative_arm_0, text, ",\n\t\t")
        text.write(str(Node_1)+",\n\t\t\t")
        self.locationVector_write(relative_arm_1, text, ",\n\t\t")
        text.write(self.links[0].string(self)+";\n")

class StructuralInternalForceOperator(Base):
    bl_label = "Structural internal force"
    orientation = bpy.props.EnumProperty(items=[("follower", "Follower", ""), ("absolute", "Absolute", "")], name="Force orientation")
    drive_name = bpy.props.EnumProperty(items=enum_drive, name="Drive")
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context, 2)
    def defaults(self, context):
        self.orientation = "follower"
        self.drive_exists(context)
    def assign(self, context):
        self.entity = self.database.element[context.scene.element_index]
        self.orientation = self.entity.orientation
        self.drive_name = self.entity.links[0].name
    def store(self, context):
        self.entity = self.database.element[context.scene.element_index]
        self.entity.objects = SelectedObjects(context)
        self.entity.orientation = self.orientation
        self.entity.unlink_all()
        self.link_drive(context, self.drive_name)
        self.entity.increment_links()
        RhombicPyramid(self.entity.objects[0])
    def create_entity(self):
        return StructuralInternalForce(self.name)

classes[StructuralInternalForceOperator.bl_label] = StructuralInternalForceOperator

class StructuralCouple(Entity):
    def write(self, text):
        rot_0, globalV_0, Node_0 = self.rigid_offset(0)
        rotT_0 = self.objects[0].matrix_world.to_quaternion().to_matrix().transposed()
        string = "\tcouple: "+str(self.database.element.index(self))+", "
        if self.orientation == "follower":
            string += "follower"
            relative_dir = rot_0*rotT_0*Vector((0., 0., 1.))
        else:
            string += "absolute"
            relative_dir = rotT_0*Vector((0., 0., 1.))
        text.write(string+
        ",\n\t\t"+str(Node_0)+",\n\t\t\t")
        self.locationVector_write(relative_dir, text, ",\n\t\t")
        text.write(self.links[0].string(self)+";\n")

class StructuralCoupleOperator(Base):
    bl_label = "Structural couple"
    orientation = bpy.props.EnumProperty(items=[("follower", "Follower", ""), ("absolute", "Absolute", "")], name="Force orientation")
    drive_name = bpy.props.EnumProperty(items=enum_drive, name="Drive")
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context, 1)
    def defaults(self, context):
        self.orientation = "follower"
        self.drive_exists(context)
    def assign(self, context):
        self.entity = self.database.element[context.scene.element_index]
        self.orientation = self.entity.orientation
        self.drive_name = self.entity.links[0].name
    def store(self, context):
        self.entity = self.database.element[context.scene.element_index]
        self.entity.objects = SelectedObjects(context)
        self.entity.orientation = self.orientation
        self.entity.unlink_all()
        self.link_drive(context, self.drive_name)
        self.entity.increment_links()
        RhombicPyramid(self.entity.objects[0])
    def create_entity(self):
        return StructuralCouple(self.name)

classes[StructuralCoupleOperator.bl_label] = StructuralCoupleOperator

class StructuralInternalCouple(Entity):
    def write(self, text):
        rot_0, globalV_0, Node_0 = self.rigid_offset(0)
        rotT_0 = self.objects[0].matrix_world.to_quaternion().to_matrix().transposed()
        rot_1, globalV_1, Node_1 = self.rigid_offset(1)
        string = "\tcouple: "+str(self.database.element.index(self))+", "
        if self.orientation == "follower":
            string += "follower internal"
            relative_dir = rot_0*rotT_0*Vector((0., 0., 1.))
        else:
            string += "absolute internal"
            relative_dir = rotT_0*Vector((0., 0., 1.))
        text.write(string+
        ",\n\t\t"+str(Node_0)+",\n\t\t\t")
        self.locationVector_write(relative_dir, text, ",\n\t\t")
        text.write(str(Node_1)+",\n"+self.links[0].string(True)+";\n")

class StructuralInternalCoupleOperator(Base):
    bl_label = "Structural internal couple"
    orientation = bpy.props.EnumProperty(items=[("follower", "Follower", ""), ("absolute", "Absolute", "")], name="Couple orientation")
    drive_name = bpy.props.EnumProperty(items=enum_drive, name="Drive")
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context, 2)
    def defaults(self, context):
        self.from_nodes = "follower"
        self.drive_exists(context)
    def assign(self, context):
        self.entity = self.database.element[context.scene.element_index]
        self.orientation = self.entity.orientation
        self.drive_name = self.entity.links[0].name
    def store(self, context):
        self.entity = self.database.element[context.scene.element_index]
        self.entity.objects = SelectedObjects(context)
        self.entity.orientation = self.orientation
        self.entity.unlink_all()
        self.link_drive(context, self.drive_name)
        self.entity.increment_links()
        RhombicPyramid(self.entity.objects[0])
    def create_entity(self):
        return StructuralInternalCouple(self.name)

classes[StructuralInternalCoupleOperator.bl_label] = StructuralInternalCoupleOperator

class AxialRotation(Entity):
    def write(self, text):
        self.write_hinge(text, "axial rotation")
        text.write(",\n"+self.links[0].string(True)+";\n")

class AxialRotationOperator(Base):
    bl_label = "Axial rotation"
    drive_name = bpy.props.EnumProperty(items=enum_drive, name="Drive")
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context, 2)
    def defaults(self, context):
        self.drive_exists(context)
    def assign(self, context):
        self.entity = self.database.element[context.scene.element_index]
        self.drive_name = self.entity.links[0].name
    def store(self, context):
        self.entity = self.database.element[context.scene.element_index]
        self.entity.objects = SelectedObjects(context)
        self.entity.unlink_all()
        self.link_drive(context, self.drive_name)
        self.entity.increment_links()
        Cylinder(self.entity.objects[0])
    def create_entity(self):
        return AxialRotation(self.name)

classes[AxialRotationOperator.bl_label] = AxialRotationOperator

class Clamp(Entity):
    def write(self, text):
        text.write(
        "\tjoint: "+str(self.database.element.index(self))+", clamp,\n"+
        "\t\t"+str(self.database.node.index(self.objects[0]))+", node, node;\n")

class ClampOperator(Base):
    bl_label = "Clamp"
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context, 1)
    def defaults(self, context):
        pass
    def assign(self, context):
        self.entity = self.database.element[context.scene.element_index]
    def store(self, context):
        self.entity = self.database.element[context.scene.element_index]
        self.entity.objects = SelectedObjects(context)
        Teardrop(self.entity.objects[0])
    def create_entity(self):
        return Clamp(self.name)

classes[ClampOperator.bl_label] = ClampOperator

class DeformableDisplacementJoint(Entity):
    def write(self, text):
        self.write_hinge(text, "deformable displacement joint")
        text.write(",\n\t\t"+self.links[0].string()+";\n")

class ConstitutiveOperator(Base):
    def assign(self, context):
        self.entity = self.database.element[context.scene.element_index]
        self.constitutive_name = self.entity.links[0].name
    def store(self, context):
        self.entity = self.database.element[context.scene.element_index]
        self.entity.objects = SelectedObjects(context)
        self.entity.unlink_all()
        self.link_constitutive(context, self.constitutive_name)
        self.entity.increment_links()
        Cylinder(self.entity.objects[0])

class DeformableDisplacementJointOperator(ConstitutiveOperator):
    bl_label = "Deformable displacement joint"
    constitutive_name = bpy.props.EnumProperty(items=enum_constitutive_3D, name="Constitutive")
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context, 2)
    def defaults(self, context):
        self.constitutive_exists(context, "3D")
    def create_entity(self):
        return DeformableDisplacementJoint(self.name)

classes[DeformableDisplacementJointOperator.bl_label] = DeformableDisplacementJointOperator

class DeformableHinge(Entity):
    def write(self, text):
        self.write_hinge(text, "deformable hinge", V1=False, V2=False)
        text.write(",\n\t\t"+self.links[0].string()+";\n")

class DeformableHingeOperator(ConstitutiveOperator):
    bl_label = "Deformable joint"
    constitutive_name = bpy.props.EnumProperty(items=enum_constitutive_3D, name="Constitutive")
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context, 2)
    def defaults(self, context):
        self.constitutive_exists(context, "3D")
    def create_entity(self):
        return DeformableJoint(self.name)

classes[DeformableHingeOperator.bl_label] = DeformableHingeOperator

class DeformableJoint(Entity):
    def write(self, text):
        self.write_hinge(text, "deformable joint")
        text.write(",\n\t\t"+self.links[0].string()+";\n")

class DeformableJointOperator(ConstitutiveOperator):
    bl_label = "Deformable joint"
    constitutive_name = bpy.props.EnumProperty(items=enum_constitutive_3D, name="Constitutive")
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context, 2)
    def defaults(self, context):
        self.constitutive_exists(context, "3D")
    def create_entity(self):
        return DeformableJoint(self.name)

classes[DeformableJointOperator.bl_label] = DeformableJointOperator

class Distance(Entity):
    def write(self, text):
        text.write("\tjoint: "+str(self.database.element.index(self))+", distance,\n")
        for i in range(2):
            self.write_node(text, i, node=True, position=True, p_label="position")
            text.write(",\n")
        if self.from_nodes:
            text.write("\t\tfrom nodes;\n")
        else:
            text.write(self.links[0].string(True)+";\n")

class DistanceOperator(Base):
    bl_label = "Distance"
    from_nodes = bpy.props.BoolProperty(name="From nodes", description="Constant distance from initial node positons")
    drive_name = bpy.props.EnumProperty(items=enum_drive, name="Drive")
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context, 2)
    def defaults(self, context):
        self.from_nodes = False
        self.drive_exists(context)
    def assign(self, context):
        self.entity = self.database.element[context.scene.element_index]
        self.from_nodes = self.entity.from_nodes
        if self.entity.links:
            self.drive_name = self.entity.links[0].name
    def store(self, context):
        self.entity = self.database.element[context.scene.element_index]
        self.entity.objects = SelectedObjects(context)
        self.entity.from_nodes = self.from_nodes
        if not self.from_nodes:
            self.entity.unlink_all()
            self.link_drive(context, self.drive_name)
            self.entity.increment_links()
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

classes[DistanceOperator.bl_label] = DistanceOperator

class InLine(Entity):
    def write(self, text):
        rot0, globalV0, iNode0 = self.rigid_offset(0)
        localV0 = rot0*globalV0
        rot_1, globalV_1, Node_1 = self.rigid_offset(1)
        to_point = rot_1*(globalV_1 + self.objects[0].matrix_world.translation - self.objects[1].matrix_world.translation)
        rot = self.objects[0].matrix_world.to_quaternion().to_matrix().transposed()
        text.write("\tjoint: "+str(self.database.element.index(self))+", inline,\n")
        self.write_node(text, 0, node=True, position=True, orientation=True)
        text.write(",\n\t\t"+str(Node_1))
        text.write(",\n\t\t\toffset, ")
        self.locationVector_write(to_point, text, ";\n")

class InLineOperator(Base):
    bl_label = "In line"
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context, 2)
    def defaults(self, context):
        pass
    def assign(self, context):
        self.entity = self.database.element[context.scene.element_index]
    def store(self, context):
        self.entity = self.database.element[context.scene.element_index]
        self.entity.objects = SelectedObjects(context)
        RhombicPyramid(self.entity.objects[0])
    def create_entity(self):
        return InLine(self.name)

classes[InLineOperator.bl_label] = InLineOperator

class InPlane(Entity):
    def write(self, text):
        rot0, globalV0, iNode0 = self.rigid_offset(0)
        localV0 = rot0*globalV0
        rot1, globalV1, iNode1 = self.rigid_offset(1)
        to_point = rot1*(globalV1 + self.objects[0].matrix_world.translation - self.objects[1].matrix_world.translation)
        rot = self.objects[0].matrix_world.to_quaternion().to_matrix().transposed()
        normal = rot*rot0*Vector((0., 0., 1.))
        text.write(
        "\tjoint: "+str(self.database.element.index(self))+", inplane,\n"+
        "\t\t"+str(iNode0)+",\n\t\t\t")
        self.locationVector_write(localV0, text, ",\n\t\t\t")
        self.locationVector_write(normal, text, ",\n\t\t")
        text.write(str(iNode1)+",\n\t\t\toffset, "+str(to_point[0])+", "+str(to_point[1])+", "+str(to_point[2])+";\n")

class InPlaneOperator(Base):
    bl_label = "In plane"
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context, 2)
    def defaults(self, context):
        pass
    def assign(self, context):
        self.entity = self.database.element[context.scene.element_index]
    def store(self, context):
        self.entity = self.database.element[context.scene.element_index]
        self.entity.objects = SelectedObjects(context)
        RhombicPyramid(self.entity.objects[0])
    def create_entity(self):
        return InPlane(self.name)

classes[InPlaneOperator.bl_label] = InPlaneOperator

class RevoluteHinge(Entity):
    def write(self, text):
        self.write_hinge(text, "revolute hinge")
        if self.enable_theta:
            text.write(",\n\t\tinitial theta, "+str(self.theta))
        if self.enable_friction:
            text.write(",\n\t\tfriction, "+str(self.average_radius))
            if self.enable_preload:
                text.write(",\n\t\t\tpreload, "+str(self.preload))
            text.write(",\n\t\t\t"+self.links[0].string())
        text.write(";\n")

class RevoluteHingeOperator(Base):
    bl_label = "Revolute hinge"
    enable_theta = bpy.props.BoolProperty(name="Enable theta", description="Enable use of initial theta")
    theta = bpy.props.FloatProperty(name="Theta", description="Initial theta", min=-9.9e10, max=9.9e10, precision=6)
    enable_friction = bpy.props.BoolProperty(name="Enable friction", description="Enable friction model")
    average_radius = bpy.props.FloatProperty(name="Radius", description="Average radius used in friction model", min=0.0, max=9.9e10, precision=6)
    enable_preload = bpy.props.BoolProperty(name="Enable preload", description="Enable preload")
    preload = bpy.props.FloatProperty(name="Preload", description="Preload used in friction model", min=0.0, max=9.9e10, precision=6)
    friction_name = bpy.props.EnumProperty(items=enum_friction, name="Friction")
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context, 2)
    def defaults(self, context):
        self.enable_theta = False
        self.theta = 0.0
        self.enable_friction = False
        self.average_radius = 1.0
        self.enable_preload = False
        self.preload = 1.0
        self.function_exists(context)
        self.friction_exists(context)
    def assign(self, context):
        self.entity = self.database.element[context.scene.element_index]
        self.enable_theta = self.entity.enable_theta
        self.theta = self.entity.theta
        self.enable_friction = self.entity.enable_friction
        self.average_radius = self.entity.average_radius
        self.enable_preload = self.entity.enable_preload
        self.preload = self.entity.preload
    def store(self, context):
        self.entity = self.database.element[context.scene.element_index]
        self.entity.objects = SelectedObjects(context)
        self.entity.enable_theta = self.enable_theta
        self.entity.theta = self.theta
        self.entity.enable_friction = self.enable_friction
        self.entity.average_radius = self.average_radius
        self.entity.enable_preload = self.enable_preload
        self.entity.preload = self.preload
        if self.enable_friction:
            self.entity.unlink_all()
            self.link_friction(context, self.friction_name)
            self.entity.increment_links()
        Cylinder(self.entity.objects[0])
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

classes[RevoluteHingeOperator.bl_label] = RevoluteHingeOperator

class Rod(Entity):
    def write(self, text):
        text.write("\tjoint: "+str(self.database.element.index(self))+", rod,\n")
        for i in range(2):
            self.write_node(text, i, node=True, position=True, p_label="position")
            text.write(",\n")
        text.write("\t\tfrom nodes,\n\t\t"+self.links[0].string()+";\n")

class RodOperator(ConstitutiveOperator):
    bl_label = "Rod"
    constitutive_name = bpy.props.EnumProperty(items=enum_constitutive_1D, name="Constitutive")
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context, 2)
    def defaults(self, context):
        self.constitutive_exists(context, "1D")
    def create_entity(self):
        return Rod(self.name)

classes[RodOperator.bl_label] = RodOperator

class SphericalHinge(Entity):
    def write(self, text):
        self.write_hinge(text, "spherical hinge")
        text.write(";\n")

class SphericalHingeOperator(Base):
    bl_label = "Spherical hinge"
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context, 2)
    def defaults(self, context):
        pass
    def assign(self, context):
        self.entity = self.database.element[context.scene.element_index]
    def store(self, context):
        self.entity = self.database.element[context.scene.element_index]
        self.entity.objects = SelectedObjects(context)
        Sphere(self.entity.objects[0])
    def create_entity(self):
        return SphericalHinge(self.name)

classes[SphericalHingeOperator.bl_label] = SphericalHingeOperator

class TotalJoint(Entity):
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
        text.write("\tjoint: "+str(self.database.element.index(self))+", total joint")
        if self.first == "rotate":
            text.write(",\n\t\t"+str(Node_0)+", position, ")
            self.locationVector_write(localV_0, text, ",\n\t\t\tposition orientation, matr,\n")
            self.rotationMatrix_write(rot_0*rot_position, text, "\t\t\t\t")
            text.write(",\n\t\t\trotation orientation, matr,\n")
            self.rotationMatrix_write(rot_0*rot, text, "\t\t\t\t")
        text.write(",\n\t\t"+str(Node_1)+", position, ")
        self.locationVector_write(to_joint, text, ",\n\t\t\tposition orientation, matr,\n")
        self.rotationMatrix_write(rot_1*rot_position, text, "\t\t\t\t")
        text.write(",\n\t\t\trotation orientation, matr,\n")
        self.rotationMatrix_write(rot_1*rot, text, "\t\t\t\t")
        if self.first == "displace":
            text.write(",\n\t\t"+str(Node_0)+", position, ")
            self.locationVector_write(localV_0, text, ",\n\t\t\tposition orientation, matr,\n")
            self.rotationMatrix_write(rot_0*rot_position, text, "\t\t\t\t")
            text.write(",\n\t\t\trotation orientation, matr,\n")
            self.rotationMatrix_write(rot_0*rot, text, "\t\t\t\t")
        text.write(",\n\t\t\tposition constraint")
        for b in [self.displacement_x, self.displacement_y, self.displacement_z]: 
            if b:
                text.write(", active")
            else:
                text.write(", inactive")
        text.write(", component")
        self.database.indent_drives += 2
        for i, b in enumerate([self.displacement_x, self.displacement_y, self.displacement_z]):
            if b:
                text.write(",\n"+self.links[i].string(True))
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
                text.write(",\n"+self.links[3+i].string(True))
            else:
                text.write(",\n\t\t\t\tinactive")
        self.database.indent_drives -= 2
        text.write(";\n")

class TotalJointOperator(Base):
    bl_label = "Total joint"
    first = bpy.props.EnumProperty(items=[("displace", "Displace first", ""), ("rotate", "Rotate first", "")])
    displacement_x = bpy.props.BoolProperty(name="Displacement-X", description="Displacement-X drive is active")
    displacement_x_drive_name = bpy.props.EnumProperty(items=enum_drive, name="Displacement-X Drive")
    displacement_y = bpy.props.BoolProperty(name="Displacement-Y", description="Displacement-Y drive is active")
    displacement_y_drive_name = bpy.props.EnumProperty(items=enum_drive, name="Displacement-Y Drive")
    displacement_z = bpy.props.BoolProperty(name="Displacement-Z", description="Displacement-Z drive is active")
    displacement_z_drive_name = bpy.props.EnumProperty(items=enum_drive, name="Displacement-Z Drive")
    angular_displacement_x = bpy.props.BoolProperty(name="Angular Displacement-X", description="Angular Displacement-X drive is active")
    angular_displacement_x_drive_name = bpy.props.EnumProperty(items=enum_drive, name="Angular Displacement-X Drive")
    angular_displacement_y = bpy.props.BoolProperty(name="Angular Displacement-Y", description="Angular Displacement-Y drive is active")
    angular_displacement_y_drive_name = bpy.props.EnumProperty(items=enum_drive, name="Angular Displacement-Y Drive")
    angular_displacement_z = bpy.props.BoolProperty(name="Angular Displacement-Z", description="Angular Displacement-Z drive is active")
    angular_displacement_z_drive_name = bpy.props.EnumProperty(items=enum_drive, name="Angular Displacement-Z Drive")
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context, 2)
    def defaults(self, context):
        self.first = "displace"
        self.displacement_x = False
        self.displacement_y = False
        self.displacement_z = False
        self.angular_displacement_x = False
        self.angular_displacement_y = False
        self.angular_displacement_z = False
        self.drive_exists(context)
    def assign(self, context):
        self.entity = self.database.element[context.scene.element_index]
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
        self.entity = self.database.element[context.scene.element_index]
        self.entity.objects = SelectedObjects(context)
        self.entity.first = self.first
        self.entity.displacement_x = self.displacement_x
        self.entity.displacement_y = self.displacement_y
        self.entity.displacement_z = self.displacement_z
        self.entity.angular_displacement_x = self.angular_displacement_x
        self.entity.angular_displacement_y = self.angular_displacement_y
        self.entity.angular_displacement_z = self.angular_displacement_z
        self.entity.unlink_all()
        self.link_drive(context, self.displacement_x_drive_name)
        self.link_drive(context, self.displacement_y_drive_name)
        self.link_drive(context, self.displacement_z_drive_name)
        self.link_drive(context, self.angular_displacement_x_drive_name)
        self.link_drive(context, self.angular_displacement_y_drive_name)
        self.link_drive(context, self.angular_displacement_z_drive_name)
        self.entity.increment_links()
        Sphere(self.entity.objects[0])
    def draw(self, context):
        self.basis = (self.displacement_x)
        layout = self.layout
        layout.prop(self, "displacement_x")
        layout.prop(self, "displacement_x_drive_name")
        layout.prop(self, "displacement_y")
        layout.prop(self, "displacement_y_drive_name")
        layout.prop(self, "displacement_z")
        layout.prop(self, "displacement_z_drive_name")
        layout.prop(self, "angular_displacement_x")
        layout.prop(self, "angular_displacement_x_drive_name")
        layout.prop(self, "angular_displacement_y")
        layout.prop(self, "angular_displacement_y_drive_name")
        layout.prop(self, "angular_displacement_z")
        layout.prop(self, "angular_displacement_z_drive_name")
    def create_entity(self):
        return TotalJoint(self.name)

classes[TotalJointOperator.bl_label] = TotalJointOperator

class ViscousBody(Entity):
    def write(self, text):
        text.write(
        "\tjoint: "+str(self.database.element.index(self))+", viscous body,\n\t\t"+
        str(self.database.node.index(self.objects[0]))+
        ",\n\t\tposition, reference, node, null"+
        ",\n\t\t"+self.links[0].string()+";\n")

class ViscousBodyOperator(ConstitutiveOperator):
    bl_label = "Viscous body"
    constitutive_name = bpy.props.EnumProperty(items=enum_constitutive_6D, name="Constitutive")
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context, 1)
    def defaults(self, context):
        self.constitutive_exists(context, "6D")
    def create_entity(self):
        return ViscousBody(self.name)

classes[ViscousBodyOperator.bl_label] = ViscousBodyOperator

class Body(Entity):
    def write(self, text):
        text.write("\tbody: "+str(self.database.element.index(self))+",\n")
        self.write_node(text, 0, node=True)
        text.write("\t\t\t"+str(self.mass)+",\n")
        self.write_node(text, 0, position=True, p_label="")
        text.write(", "+self.links[0].string())
        self.write_node(text, 0, orientation=True, o_label="inertial")
        text.write(";\n")

class BodyOperator(Base):
    bl_label = "Body"
    mass = bpy.props.FloatProperty(name="Mass", description="", min=0.000001, max=9.9e10, precision=6)
    matrix_name = bpy.props.EnumProperty(items=enum_matrix_3x3, name="Matrix")
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context, 1)
    def defaults(self, context):
        self.mass = 1.0
        self.matrix_exists(context, "3x3")
    def assign(self, context):
        self.entity = self.database.element[context.scene.element_index]
        self.mass = self.entity.mass
        self.matrix_name = self.entity.links[0].name
    def store(self, context):
        self.entity = self.database.element[context.scene.element_index]
        self.entity.objects = SelectedObjects(context)
        self.entity.mass = self.mass
        self.entity.unlink_all()
        self.link_matrix(context, self.matrix_name)
        self.entity.increment_links()
        Ellipsoid(self.entity.objects[0], self.entity.mass, self.entity.links[0])
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "mass")
        layout.prop(self, "matrix_name")
    def create_entity(self):
        return Body(self.name)

classes[BodyOperator.bl_label] = BodyOperator

class RigidOffset(Entity):
    pass

class RigidOffsetOperator(Base):
    bl_label = "Rigid offset"
    @classmethod
    def poll(cls, context):
        obs = SelectedObjects(context)
        test = len(obs) == 2 and not (cls.database.element.filter("Rigid offset", obs[0])
            or cls.database.element.filter("Dummy node", obs[0]))
        return cls.bl_idname.startswith(root_dot+"e_") or test
    def defaults(self, context):
        pass
    def assign(self, context):
        self.entity = self.database.element[context.scene.element_index]
    def store(self, context):
        self.entity = self.database.element[context.scene.element_index]
        self.entity.objects = SelectedObjects(context)
        RhombicPyramid(self.entity.objects[0])
    def create_entity(self):
        return RigidOffset(self.name)

classes[RigidOffsetOperator.bl_label] = RigidOffsetOperator

class DummyNode(Entity):
    pass

class DummyNodeOperator(Base):
    bl_label = "Dummy node"
    @classmethod
    def poll(cls, context):
        obs = SelectedObjects(context)
        test = len(obs) == 2 and not (cls.database.element.filter("Rigid offset", obs[0])
            or cls.database.element.filter("Dummy node", obs[0]))
        return cls.bl_idname.startswith(root_dot+"e_") or test
    def defaults(self, context):
        pass
    def assign(self, context):
        self.entity = self.database.element[context.scene.element_index]
    def store(self, context):
        self.entity = self.database.element[context.scene.element_index]
        self.entity.objects = SelectedObjects(context)
        RhombicPyramid(self.entity.objects[0])
    def create_entity(self):
        return DummyNode(self.name)

classes[DummyNodeOperator.bl_label] = DummyNodeOperator

class BeamSegment(Entity):
    ...

class BeamSegmentOperator(Base):
    bl_label = "Beam segment"
    constitutive_name = bpy.props.EnumProperty(items=enum_constitutive_6D, name="Constitutive")
    @classmethod
    def poll(cls, context):
        return super().base_poll(cls, context, 2)
    def defaults(self, context):
        self.constitutive_exists(context, "6D")
    def assign(self, context):
        self.entity = self.database.element[context.scene.element_index]
        self.constitutive_name = self.entity.links[0].name
    def store(self, context):
        self.entity = self.database.element[context.scene.element_index]
        self.entity.objects = SelectedObjects(context)
        self.entity.unlink_all()
        self.link_constitutive(context, self.constitutive_name)
        self.entity.increment_links()
    def create_entity(self):
        return BeamSegment(self.name)

classes[BeamSegmentOperator.bl_label] = BeamSegmentOperator

class Gravity(Entity):
    def write(self, text):
        text.write("\tgravity: "+self.links[0].string()+", "+self.links[1].string()+";\n")

class GravityOperator(Base):
    bl_label = "Gravity"
    matrix_name = bpy.props.EnumProperty(items=enum_matrix_3x1, name="Vector")
    drive_name = bpy.props.EnumProperty(items=enum_drive, name="Drive")
    @classmethod
    def poll(self, context):
        return (self.bl_idname.startswith(root_dot+"e_")
            or not self.database.element.filter("Gravity"))
    def defaults(self, context):
        self.matrix_exists(context, "3x1")
        self.drive_exists(context)
    def assign(self, context):
        self.entity = self.database.element[context.scene.element_index]
        self.matrix_name = self.entity.links[0].name
        self.drive_name = self.entity.links[1].name
    def store(self, context):
        self.entity = self.database.element[context.scene.element_index]
        self.entity.unlink_all()
        self.link_matrix(context, self.matrix_name)
        self.link_drive(context, self.drive_name)
        self.entity.increment_links()
    def create_entity(self):
        return Gravity(self.name)

classes[GravityOperator.bl_label] = GravityOperator

