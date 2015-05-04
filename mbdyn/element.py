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
#    Blender MBDyn is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Foobar.  If not, see <http://www.gnu.org/licenses/>.
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
    from mbdyn.common import (aerodynamic_types, beam_types, force_types, genel_types, joint_types, environment_types, node_types,
        structural_static_types, structural_dynamic_types, Ellipsoid, RhombicPyramid, Teardrop)
    from mbdyn.base import bpy, root_dot, Operator, Entity, enum_objects, enum_matrix_3x1, enum_matrix_3x3, enum_constitutive_6D, enum_drive, SelectedObjects
    import bmesh

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
            if Operator.database.element:
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
        def defaults(self, context):
            pass
        def assign(self, context):
            self.entity = self.database.element[context.scene.element_index]
        def store(self, context):
            self.entity = self.database.element[context.scene.element_index]
        def create_entity(self):
            return Entity(self.name)
    classes[t] = Tester

class Clamp(Entity):
    def write(self, text):
        text.write(
        '\tjoint: '+str(self.database.element.index(self))+', clamp,\n'+
        '\t\t'+str(self.database.node.index(self.objects[0]))+', node, node;\n')

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

