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
    from .base import bpy, Operator, Entity

types = [
	"Const",
	"Exp",
	"Log",
	"Pow",
	"Linear",
	"Cubic Natural Spline",
	"Multilinear",
	"Chebychev",
	"Sum",
	"Sub",
	"Mul",
	"Div"]

tree = ["Add Function", types]

classes = dict()

class Base(Operator):
    bl_label = "Functions"
    bl_options = {'DEFAULT_CLOSED'}
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
        def defaults(self, context):
            pass
        def assign(self, context):
            self.entity = self.database.function[context.scene.function_index]
        def store(self, context):
            self.entity = self.database.function[context.scene.function_index]
        def create_entity(self):
            return Entity(self.name)
    classes[t] = Tester

class Const(Entity):
    def write(self, text):
        text.write("scalar function: \""+self.name+"\", const, "+str(self.constant)+";\n")

class ConstOperator(Base):
    bl_label = "Const"
    constant = bpy.props.FloatProperty(name="Constant", description="", min=-9.9e10, max=9.9e10, precision=6)
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.constant = 1.0
    def assign(self, context):
        self.entity = self.database.function[context.scene.function_index]
        self.constant = self.entity.constant
    def store(self, context):
        self.entity = self.database.function[context.scene.function_index]
        self.entity.constant = self.constant
    def create_entity(self):
        return Const(self.name)

classes[ConstOperator.bl_label] = ConstOperator

