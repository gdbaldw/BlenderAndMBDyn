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

bl_info = {
    "name": "MBDyn Modeling and Simulation",
    "author": "G Douglas Baldwin",
    "version": (0, 1),
    "blender": (2, 72, 0),
    "location": "View3D",
    "description": "Provides an MBDyn multibody dynamic model design and presentation environment.",
    "warning": "",
    "wiki_url": "",
    "category": "STEM"}

if "bpy" in locals():
    import imp
    imp.reload(bpy)
    imp.reload(Props)
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
    from .base import bpy, Props, TreeMenu, Operators, UI, database, category, root_dot
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
    from mathutils import Matrix

from bpy_extras.io_utils import ImportHelper, ExportHelper
from subprocess import call, Popen
from tempfile import TemporaryFile
from time import sleep, clock
import os

obs = list()
for module, entity_list, entity_name in [
    (element, database.element, "element"),
    (drive, database.drive, "drive"),
    (driver, database.driver, "driver"),
    (friction, database.friction, "friction"),
    (shape, database.shape, "shape"),
    (function, database.function, "function"),
    (ns_node, database.ns_node, "ns_node"),
    (constitutive, database.constitutive, "constitutive"),
    (matrix, database.matrix, "matrix"),
    (frame, database.frame, "frame")]:
        obs.append(UI(module.tree, module.Base, entity_list, entity_name))
        obs.append(TreeMenu(module.tree))
        obs.append(Operators(module.classes, entity_list))

class MBDynFile(bpy.types.Operator, ExportHelper):
    bl_idname = root_dot+"file"
    bl_options = {'REGISTER', 'INTERNAL'}
    bl_label = "MBDyn File"
    bl_description = "Generate the MBDyn input file"
    filename_ext = ".mbd"
    filter_glob = bpy.props.StringProperty(
            default="*.mbd",
            options={'HIDDEN'},
            )
    parameters = bpy.props.EnumProperty(items=[("default", "Default parameters", ""), ("custom", "Custom parameters", "")])
    integrator = bpy.props.EnumProperty(items=[("initial value", "initial value", ""), ("inverst dynamics", "inverse dynamics", "")])
    t0 = bpy.props.FloatProperty(min=0, max=9.9e10, precision=6, description="initial time")
    tN = bpy.props.FloatProperty(min=0, max=1.0e6, precision=6, description="final time (tN==0. => Use Blender animation range)")
    dt = bpy.props.FloatProperty(min=1.0e-3, max=1.0e3, description="time step")
    maxI = bpy.props.IntProperty(min=1, max=2000, description="max iterations")
    tol = bpy.props.FloatProperty(min=1.0e-6, max=1.0e9, precision=6, description="tolerance")
    mod_test = bpy.props.BoolProperty(description="Modify the residual test taking in account the rate of change of the status")
    dTol = bpy.props.FloatProperty(min=1.0e-3, max=1.0e3, description="deriatives tolerance")
    dC = bpy.props.FloatProperty(min=1.0e-6, max=1.0e6, precision=6, description="derivatives coefficient")
    fps = bpy.props.IntProperty(min=1, max=1000, description="frames per second: used to format output")
    precision = bpy.props.IntProperty(min=1, max=16, description="Significant digits of most output file values")
    port = bpy.props.IntProperty(min=1024, max=49151, description="First sequential socket port number")
    hostname = bpy.props.StringProperty(maxlen=30, description="Name or IP of Game Blender Console")
    posixRT = bpy.props.BoolProperty(description="When using File Driver in Game Blender, run in POSIX Real Time Mode (WARNING: controls system clock)")
    def invoke(self, context, event):
        wm = context.window_manager
        directory = os.path.splitext(context.blend_data.filepath)[0]
        if not directory:
            wm.popup_menu(lambda self, c: self.layout.label(
                "Must first save the Blender file."), title="MBDyn Error", icon='ERROR')
            return {'CANCELLED'}
        if not os.path.exists(directory):
            os.mkdir(directory)
        self.filepath = os.path.join(directory, context.scene.name+".mbd")
        self.parameters = database.parameters
        self.integrator = database.integrator
        self.t0 = database.t0
        self.tN = database.tN
        self.dt = database.dt
        self.maxI = database.maxI
        self.tol = database.tol
        self.mod_test = database.mod_test
        self.dTol = database.dTol
        self.dC = database.dC
        self.fps = database.fps
        self.precision = database.precision
        self.port = database.port
        self.hostname = database.hostname
        self.posixRT = database.posixRT
        return ExportHelper.invoke(self, context, event)
    def save(self, context):
        database.parameters = self.parameters
        database.integrator = self.integrator
        database.t0 = self.t0
        database.tN = self.tN
        database.dt = self.dt
        database.maxI = self.maxI
        database.tol = self.tol
        database.mod_test = self.mod_test
        database.dTol = self.dTol
        database.dC = self.dC
        database.fps = self.fps
        database.precision = self.precision
        database.port = self.port
        database.hostname = self.hostname
        database.posixRT = self.posixRT
        pickle_database(context)
    def execute(self, context):
        if self.parameters == "default":
            database.defaults()
        elif self.parameters == "custom":
            self.save(context)
        with open(self.filepath, 'w') as f:
            database.write(f)
        database.filepath = self.filepath
        return{'FINISHED'}
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "parameters")
        if self.parameters == "custom":
            for prop in "integrator t0 tN dt maxI tol mod_test dTol dC fps precision port hostname posixRT".split():
                layout.prop(self, prop)

class RunMBDyn(bpy.types.Operator):
    bl_idname = root_dot+"run"
    bl_options = {'REGISTER', 'INTERNAL'}
    bl_label = "Run MBDyn"
    bl_description = "Run MBDyn for the input file"
    timer = None
    count = 0.01
    def modal(self, context, event):
        if event.type != 'TIMER':
            return {'PASS_THROUGH'}
        wm = context.window_manager
        if self.t_hold < database.tN and self.t_hold != self.t_now:
            self.t_hold = self.t_now
            call(self.command, shell=True, stdout=self.f2)
            try:
                self.f2.seek(0)
                self.t_now = float(self.f2.read().splitlines()[-1])
                percent = 100.*(1.-(database.tN - self.t_now)/self.t_range)
                wm.progress_update(percent)
            except:
                pass
            return {'PASS_THROUGH'}
        else:
            self.f2.close()
            if self.t_hold < database.tN:
                wm.popup_menu(lambda self, c: self.layout.label("Check console for message"), title="MBDyn Error", icon='INFO')
            if self.f1:
                self.f1.seek(0)
                print(self.f1.read())
            self.f1.close()
            wm.event_timer_remove(self.timer)
            wm.progress_end()
            return {'FINISHED'}
    def execute(self, context):
        command = 'mbdyn -s -f '+database.filepath+' &'
        print(command)
        self.f1 = TemporaryFile()
        process = Popen(command, shell=True, stdout=self.f1)
        out_file = os.path.splitext(database.filepath)[0]+".out"
        self.command = "tail -n 1 "+out_file+" | awk '{print $3}'"
        print(self.command)
        self.t_hold, self.t_now, self.t_range = -float("inf"), database.t0, database.tN - database.t0
        call("touch "+out_file, shell=True)
        self.f2 = TemporaryFile()
        wm = context.window_manager
        wm.progress_begin(0., 100.)
        self.timer = wm.event_timer_add(0.0001, context.window)
        wm.modal_handler_add(self)
        return{'RUNNING_MODAL'}


class DisplayResults(bpy.types.Operator, ImportHelper):
    bl_idname = root_dot+"display"
    bl_options = {'REGISTER', 'INTERNAL'}
    bl_label = "Display Results"
    bl_description = "Import results into Blender animation starting at the next frame"
    filename_ext = ".log"
    filter_glob = bpy.props.StringProperty(
            default="*.log",
            options={'HIDDEN'},
            )
    def invoke(self, context, event):
        self.filepath = os.path.splitext(database.filepath)[0]+".log"
        return ImportHelper.invoke(self, context, event)
    def execute(self, context):
        scene = context.scene
        frame_initial = scene.frame_current
        database.node_dict = dict()
        with open(os.path.splitext(self.filepath)[0]+".log") as f:
            split_lines = (line.split() for line in f.readlines())
            nodes = ((int(fields[2]), fields[6]) for fields in split_lines if fields[:2] == ["structural", "node:"])
            for i, node in enumerate(nodes):
                database.node_dict[node[0]] = i
                for data_path in "location rotation_euler".split():
                    database.node[i].keyframe_insert(data_path)
        with open(os.path.splitext(self.filepath)[0]+".mov") as f:
            lines = f.readlines()
        marker = int(lines[0].split()[0])
        wm = context.window_manager
        wm.progress_begin(0., 100.)
        N = float(len(lines))
        for n, line in enumerate(lines):
            wm.progress_update(100.*float(n)/N)
            fields = line.split()
            node_label = int(fields[0])
            if node_label == marker:
                scene.frame_current += 1
            i = database.node_dict[node_label]
            fields = [float(field) for field in fields[1:13]]
            euler = Matrix([fields[3:6], fields[6:9], fields[9:12]]).to_euler()
            database.node[i].location = fields[:3]
            database.node[i].rotation_euler = euler[0], euler[1], euler[2]    
            for data_path in "location rotation_euler".split():
                database.node[i].keyframe_insert(data_path)
        scene.frame_current = frame_initial + 1
        wm.progress_end()
        return{'FINISHED'}

class ParentRigids(bpy.types.Operator):
    bl_idname = root_dot+"rigids"
    bl_options = {'REGISTER', 'INTERNAL'}
    bl_label = "Parent Rigids"
    bl_description = "Parent rigids"
    def execute(self, context):
        return{'FINISHED'}

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
        layout.operator(root_dot+"file")
        layout.operator(root_dot+"run")
        layout.operator(root_dot+"display")
        layout.operator(root_dot+"rigids")
        layout.operator(root_dot+"import")
        layout.operator(root_dot+"append")

klasses = [MBDynFile, RunMBDyn, DisplayResults, ParentRigids, ImportFile, AppendModel, Actions]

@bpy.app.handlers.persistent
def load_post(junk):
    database.unpickle()

@bpy.app.handlers.persistent
def scene_update_post(junk):
    if bpy.context.scene != database.scene:
        database.replace()

def register():
    Props.register()
    for o in obs:
        o.register()
    for klass in klasses:
        bpy.utils.register_class(klass)
    bpy.app.handlers.load_post.append(load_post)
    bpy.app.handlers.scene_update_post.append(scene_update_post)

def unregister():
    bpy.app.handlers.scene_update_post.remove(scene_update_post)
    bpy.app.handlers.load_post.remove(load_post)
    Props.unregister()
    for o in obs:
        o.unregister()
    for klass in klasses:
        bpy.utils.unregister_class(klass)

if __name__ == "__main__":
    register()
