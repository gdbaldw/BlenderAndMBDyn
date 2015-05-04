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
#    along with Foobar.  If not, see <http://www.gnu.org/licenses/>.
#
# ***** END GPL LICENCE BLOCK *****
# -------------------------------------------------------------------------- 

if "bpy" in locals():
    import imp
    imp.reload(bpy)
    imp.reload(Operator)
    imp.reload(Entity)
else:
    from .base import bpy, Operator, Entity

types = ["File"]

tree = ["Add Driver", types]

class Base(Operator):
    bl_label = "Drivers"
    bl_options = {'DEFAULT_CLOSED'}
    @classmethod
    def make_list(self, ListItem):
        bpy.types.Scene.driver_uilist = bpy.props.CollectionProperty(type = ListItem)
        bpy.types.Scene.driver_index = bpy.props.IntProperty(default=-1)
    @classmethod
    def delete_list(self):
        del bpy.types.Scene.driver_uilist
        del bpy.types.Scene.driver_index
    @classmethod
    def get_uilist(self, context):
        return context.scene.driver_index, context.scene.driver_uilist
    def set_index(self, context, value):
        context.scene.driver_index = value

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
            self.entity = self.database.driver[context.scene.driver_index]
        def store(self, context):
            self.entity = self.database.driver[context.scene.driver_index]
        def create_entity(self):
            return Entity(self.name)
    classes[t] = Tester

