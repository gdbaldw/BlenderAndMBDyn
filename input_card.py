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
    imp.reload(enum_matrix_3x1)
    imp.reload(bmesh)
    imp.reload(subsurf)
else:
    from .base import bpy, root_dot, database, Operator, Entity, Bundle, enum_matrix_3x1, SelectedObjects
    from .base import update_matrix
    from .common import RhombicPyramid
    import bmesh
    from copy import copy

types = ["c81 data", "Hydraulic fluid", "Include", "Module load", "Print symbol table", "Reference frame", "Remark", "Set", "Setenv"]

tree = ["Input Card", types]

klasses = dict()

class Base(Operator):
    bl_label = "Input Cards"
    bl_options = {'DEFAULT_CLOSED'}
    @classmethod
    def poll(cls, context):
        return True
    @classmethod
    def make_list(self, ListItem):
        bpy.types.Scene.input_card_uilist = bpy.props.CollectionProperty(type = ListItem)
        def select_and_activate(self, context):
            if database.input_card and self.input_card_index < len(database.input_card) and hasattr(database.input_card[self.input_card_index], "objects"):
                bpy.ops.object.select_all(action='DESELECT')
                input_card = database.input_card[self.input_card_index]
                for ob in input_card.objects:
                    ob.select = True
                context.scene.objects.active = input_card.objects[0]
                input_card.remesh()
        bpy.types.Scene.input_card_index = bpy.props.IntProperty(default=-1, update=select_and_activate)
    @classmethod
    def delete_list(self):
        del bpy.types.Scene.input_card_uilist
        del bpy.types.Scene.input_card_index
    @classmethod
    def get_uilist(self, context):
        return context.scene.input_card_index, context.scene.input_card_uilist
    def set_index(self, context, value):
        context.scene.input_card_index = value

for t in types:
    class Tester(Base):
        bl_label = t
        @classmethod
        def poll(cls, context):
            return False
        def create_entity(self):
            return Entity(self.name)
    klasses[t] = Tester

class ReferenceFrame(Entity):
    def remesh(self):
        RhombicPyramid(self.objects[0])

class ReferenceFrameOperator(Base):
    bl_label = "Reference frame"
    linear_velocity_name = bpy.props.EnumProperty(items=enum_matrix_3x1, name="Linear velocity vector",
        update=lambda self, context: update_matrix(self, context, self.linear_velocity_name, "3x1"))
    angular_velocity_name = bpy.props.EnumProperty(items=enum_matrix_3x1, name="Angular velocity vector",
        update=lambda self, context: update_matrix(self, context, self.angular_velocity_name, "3x1"))
    @classmethod
    def poll(self, context):
        frames = copy(database.input_card.filter("Reference frame"))
        if self.bl_idname.startswith(root_dot + "e_"):
            frames.pop(context.scene.input_card_index)
        selected = SelectedObjects(context)
        overlapped = False in [set(selected[1:]).isdisjoint(set(f.objects[1:])) for f in frames]
        duplicate = True in [selected[0] == f.objects[0] for f in frames if hasattr(f, "objects")]
        if len(selected) < 2 or overlapped or duplicate:
            return False
        frame_objects = [f.objects for f in frames]
        head, hold = selected[0], None
        while frame_objects and head != hold:
            hold = head
            for objects in frame_objects:
                if head in objects[1:]:
                    head = objects[0]
                    frame_objects.remove(objects)
        return head not in selected[1:]
    def assign(self, context):
        self.linear_velocity_name = self.entity.links[0].name
        self.angular_velocity_name = self.entity.links[1].name
    def store(self, context):
        self.entity.objects = SelectedObjects(context)
        self.entity.links.append(database.matrix.get_by_name(self.linear_velocity_name))
        self.entity.links.append(database.matrix.get_by_name(self.angular_velocity_name))
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "linear_velocity_name")
        layout.prop(self, "angular_velocity_name")
    def create_entity(self):
        return ReferenceFrame(self.name)

klasses[ReferenceFrameOperator.bl_label] = ReferenceFrameOperator

bundle = Bundle(tree, Base, klasses, database.input_card, "input_card")
