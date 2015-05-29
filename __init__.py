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

bl_info = {
    "name": "MBDyn Modeling and Simulation",
    "author": "G Douglas Baldwin",
    "version": (2, 0),
    "blender": (2, 72, 0),
    "location": "View3D",
    "description": "Provides an MBDyn multibody dynamic model design and presentation environment.",
    "warning": "",
    "wiki_url": "",
    "category": "STEM"}

if "bpy" in locals():
    import imp
    imp.reload(bpy)
    imp.reload(BPY)
    imp.reload(TreeMenu)
    imp.reload(Operators)
    imp.reload(UI)
    imp.reload(database)
    imp.reload(category)
    imp.reload(root_dot)
    imp.reload(element)
    imp.reload(drive)
    imp.reload(driver)
    imp.reload(friction)
    imp.reload(shape)
    imp.reload(function)
    imp.reload(ns_node)
    imp.reload(constitutive)
    imp.reload(matrix)
    imp.reload(frame)
    imp.reload(Matrix)
else:
    from .base import bpy, BPY, TreeMenu, Operators, UI, database, category, root_dot
    from . import element
    from . import drive
    from . import driver
    from . import friction
    from . import shape
    from . import function
    from . import ns_node
    from . import constitutive
    from . import matrix
    from . import frame
    from . import definition
    from . import simulator
    from mathutils import Matrix

from bpy_extras.io_utils import ImportHelper, ExportHelper
from subprocess import call, Popen
from tempfile import TemporaryFile
from time import sleep, clock
import os

class ImportFile(bpy.types.Operator):
    bl_idname = root_dot+"import"
    bl_options = {'REGISTER', 'INTERNAL'}
    bl_label = "Import .mov file"
    bl_description = "Import .mov file from externally run MBDyn model"
    def execute(self, context):
        return{'FINISHED'}

class AppendModel(bpy.types.Operator):
    bl_idname = root_dot+"append"
    bl_options = {'REGISTER', 'INTERNAL'}
    bl_label = "Append model"
    bl_description = "Append MBDyn model from .blend file"
    def execute(self, context):
        return{'FINISHED'}

class Actions(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = category
    bl_label = "Actions"
    bl_idname = "_".join([category, "actions"])
    bl_options = {'DEFAULT_CLOSED'}
    def draw(self, context):
        layout = self.layout
        layout.operator(root_dot+"import")
        layout.operator(root_dot+"append")

klasses = [] # [ImportFile, AppendModel, Actions]

modules = [element, constitutive, drive, driver, frame, friction, function, matrix, ns_node, shape, definition, simulator]

def register():
    BPY.register()
    for module in modules:
        module.bundle.register()
    for klass in klasses:
        bpy.utils.register_class(klass)

def unregister():
    BPY.unregister()
    for module in modules:
        module.bundle.unregister()
    for klass in klasses:
        bpy.utils.unregister_class(klass)

if __name__ == "__main__":
    register()
