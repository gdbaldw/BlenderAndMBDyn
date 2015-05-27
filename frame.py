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
    from .common import RhombicPyramid
    import bmesh

types = ["Reference frame",]

tree = ["Add Frame", types]

klasses = dict()

class Base(Operator):
    bl_label = "Frames"
    bl_options = {'DEFAULT_CLOSED'}
    @classmethod
    def make_list(self, ListItem):
        bpy.types.Scene.frame_uilist = bpy.props.CollectionProperty(type = ListItem)
        def select_and_activate(self, context):
            if database.frame  and self.frame_index < len(database.frame):
                bpy.ops.object.select_all(action='DESELECT')
                frame = database.frame[self.frame_index]
                for ob in frame.objects:
                    ob.select = True
                context.scene.objects.active = frame.objects[0]
                frame.remesh()
        bpy.types.Scene.frame_index = bpy.props.IntProperty(default=-1, update=select_and_activate)
    @classmethod
    def delete_list(self):
        del bpy.types.Scene.frame_uilist
        del bpy.types.Scene.frame_index
    @classmethod
    def get_uilist(self, context):
        return context.scene.frame_index, context.scene.frame_uilist
    def set_index(self, context, value):
        context.scene.frame_index = value

for t in types:
    class Tester(Base):
        bl_label = t
        @classmethod
        def poll(cls, context):
            return False
        def defaults(self, context):
            pass
        def assign(self, context):
            self.entity = database.frame[context.scene.frame_index]
        def store(self, context):
            self.entity = database.frame[self.index]
        def create_entity(self):
            return Entity(self.name)
    klasses[t] = Tester

class Frame(Entity):
    def write(self, text):
        text.write("\tbody: "+str(database.frame.index(self))+",\n")
        self.write_node(text, 0, node=True)
        text.write("\t\t\t"+str(self.mass)+",\n")
        self.write_node(text, 0, position=True, p_label="")
        text.write(", "+self.links[0].string())
        self.write_node(text, 0, orientation=True, o_label="inertial")
        text.write(";\n")
    def remesh(self):
        RhombicPyramid(self.objects[0])

class FrameOperator(Base):
    bl_label = "Reference frame"
    linear_velocity_name = bpy.props.EnumProperty(items=enum_matrix_3x1, name="Linear velocity vector")
    linear_velocity_edit = bpy.props.BoolProperty(name="")
    angular_velocity_name = bpy.props.EnumProperty(items=enum_matrix_3x1, name="Angular velocity vector")
    angular_velocity_edit = bpy.props.BoolProperty(name="")
    @classmethod
    def poll(self, context):
        if self.bl_idname.startswith(root_dot+"e_"):
            return True
        selected = SelectedObjects(context)
        overlapped = False in [set(selected[1:]).isdisjoint(set(f.objects[1:])) for f in database.frame]
        duplicate = True in [selected[0] == f.objects[0] for f in database.frame if hasattr(f, "objects")]
        if len(selected) < 2 or overlapped or duplicate:
            return False
        frames = [f.objects for f in database.frame]
        head, hold = selected[0], None
        while frames and head != hold:
            hold = head
            for frame in frames:
                if head in frame[1:]:
                    head = frame[0]
                    frames.remove(frame)
        return head not in selected[1:]
    def defaults(self, context):
        self.matrix_exists(context, "3x1")
    def assign(self, context):
        self.entity = database.frame[context.scene.frame_index]
        self.linear_velocity_name = self.entity.links[0].name
        self.angular_velocity_name = self.entity.links[1].name
    def store(self, context):
        self.entity = database.frame[self.index]
        self.entity.objects = SelectedObjects(context)
        self.entity.unlink_all()
        self.link_matrix(context, self.linear_velocity_name, self.linear_velocity_edit)
        self.link_matrix(context, self.angular_velocity_name, self.angular_velocity_edit)
        self.entity.increment_links()
    def draw(self, context):
        layout = self.layout
        self.draw_link(layout, "linear_velocity_name", "linear_velocity_edit")
        self.draw_link(layout, "angular_velocity_name", "angular_velocity_edit")
    def create_entity(self):
        return Frame(self.name)

klasses[FrameOperator.bl_label] = FrameOperator

bundle = Bundle(tree, Base, klasses, database.frame, "frame")
