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
    imp.reload(Database)
    imp.reload(Common)
else:
    import bpy
    from .database import Database
    from .common import Common, method_types, nonlinear_solver_types
    from collections import OrderedDict
    from copy import copy

category = "MBDyn"
root_dot = "_".join(category.lower().split()) + "."
database = Database()

def enum_objects(self, context):
    return [(o.name, o.name, "") for o in context.scene.objects if o.type == 'MESH']
def enum_matrix(self, context, matrix_type):
    return [(m.name, m.name, "") for i, m in enumerate(context.scene.matrix_uilist)
        if database.matrix[i].type == matrix_type]
def enum_matrix_3x1(self, context):
    return enum_matrix(self, context, "3x1")
def enum_matrix_6x1(self, context):
    return enum_matrix(self, context, "6x1")
def enum_matrix_3x3(self, context):
    return enum_matrix(self, context, "3x3")
def enum_matrix_6x6(self, context):
    return enum_matrix(self, context, "6x6")
def enum_matrix_6xN(self, context):
    return enum_matrix(self, context, "6xN")
def enum_constitutive(self, context, dimension):
    return [(c.name, c.name, "") for i, c in enumerate(context.scene.constitutive_uilist)
        if dimension in database.constitutive[i].dimensions]
def enum_constitutive_1D(self, context):
    return enum_constitutive(self, context, "1D")
def enum_constitutive_3D(self, context):
    return enum_constitutive(self, context, "3D")
def enum_constitutive_6D(self, context):
    return enum_constitutive(self, context, "6D")
def enum_drive(self, context):
    return [(d.name, d.name, "") for d in context.scene.drive_uilist]
def enum_meter_drive(self, context):
    return [(d.name, d.name, "") for i, d in enumerate(context.scene.drive_uilist) if database.drive[i].type == "Meter drive"]
def enum_element(self, context):
    return [(e.name, e.name, "") for e in context.scene.element_uilist]
def enum_function(self, context):
    return [(f.name, f.name, "") for f in context.scene.function_uilist]
def enum_friction(self, context):
    return [(f.name, f.name, "") for f in context.scene.friction_uilist]
def enum_general_data(self, context):
    return [(d.name, d.name, "") for i, d in enumerate(context.scene.definition_uilist) if database.definition[i].type == "General data"]
def enum_method(self, context):
    return [(d.name, d.name, "") for i, d in enumerate(context.scene.definition_uilist) if database.definition[i].type in method_types]
def enum_nonlinear_solver(self, context):
    return [(d.name, d.name, "") for i, d in enumerate(context.scene.definition_uilist) if database.definition[i].type in nonlinear_solver_types]
def enum_eigenanalysis(self, context):
    return [(d.name, d.name, "") for i, d in enumerate(context.scene.definition_uilist) if database.definition[i].type == "Eigenanalysis"]
def enum_abort_after(self, context):
    return [(d.name, d.name, "") for i, d in enumerate(context.scene.definition_uilist) if database.definition[i].type == "Abort after"]
def enum_linear_solver(self, context):
    return [(d.name, d.name, "") for i, d in enumerate(context.scene.definition_uilist) if database.definition[i].type == "Linear solver"]
def enum_dummy_steps(self, context):
    return [(d.name, d.name, "") for i, d in enumerate(context.scene.definition_uilist) if database.definition[i].type == "Dummy steps"]
def enum_output_data(self, context):
    return [(d.name, d.name, "") for i, d in enumerate(context.scene.definition_uilist) if database.definition[i].type == "Output data"]
def enum_real_time(self, context):
    return [(d.name, d.name, "") for i, d in enumerate(context.scene.definition_uilist) if database.definition[i].type == "Real time"]
def enum_assembly(self, context):
    return [(d.name, d.name, "") for i, d in enumerate(context.scene.definition_uilist) if database.definition[i].type == "Assembly"]
def enum_job_control(self, context):
    return [(d.name, d.name, "") for i, d in enumerate(context.scene.definition_uilist) if database.definition[i].type == "Job control"]
def enum_default_output(self, context):
    return [(d.name, d.name, "") for i, d in enumerate(context.scene.definition_uilist) if database.definition[i].type == "Default output"]
def enum_default_aerodynamic_output(self, context):
    return [(d.name, d.name, "") for i, d in enumerate(context.scene.definition_uilist) if database.definition[i].type == "Default aerodynamic output"]
def enum_default_beam_output(self, context):
    return [(d.name, d.name, "") for i, d in enumerate(context.scene.definition_uilist) if database.definition[i].type == "Default beam output"]

@bpy.app.handlers.persistent
def load_post(*args, **kwargs):
    database.unpickle()
    for scene in bpy.data.scenes:
        scene.dirty_simulator = True

@bpy.app.handlers.persistent
def scene_update_post(*args, **kwargs):
    if bpy.context.scene != database.scene:
        database.replace()

@bpy.app.handlers.persistent
def save_pre(*args, **kwargs):
    database.pickle()

class BPY:
    class Floats(bpy.types.PropertyGroup):
        value = bpy.props.FloatProperty(min=-9.9e10, max=9.9e10, step=100, precision=6)
    class DriveNames(bpy.types.PropertyGroup):
        value = bpy.props.EnumProperty(items=enum_drive, name="Drive")
        edit = bpy.props.BoolProperty(name="")
    class FunctionNames(bpy.types.PropertyGroup):
        value = bpy.props.EnumProperty(items=enum_function, name="Function")
        edit = bpy.props.BoolProperty(name="")
    class ObjectNames(bpy.types.PropertyGroup):
        value = bpy.props.EnumProperty(items=enum_objects, name="Object")
    klasses = [Floats, DriveNames, FunctionNames, ObjectNames]
    @classmethod
    def register(cls):
        for klass in cls.klasses:
            bpy.utils.register_class(klass)
        bpy.app.handlers.load_post.append(load_post)
        bpy.app.handlers.scene_update_post.append(scene_update_post)
        bpy.app.handlers.save_pre.append(save_pre)
        bpy.types.Scene.dirty_simulator = bpy.props.BoolProperty(default=True)
        bpy.types.Scene.clean_log = bpy.props.BoolProperty(default=False)
    @classmethod
    def unregister(cls):
        for klass in cls.klasses:
            bpy.utils.unregister_class(klass)
        bpy.app.handlers.save_pre.append(save_pre)
        bpy.app.handlers.scene_update_post.remove(scene_update_post)
        bpy.app.handlers.load_post.remove(load_post)
        del bpy.types.Scene.dirty_simulator
        del bpy.types.Scene.clean_log

class Entity(Common):
    indent_drives = 1
    def __init__(self, name):
        self.type = name
        self.users = 0
        self.links = list()
    def unlink_all(self):
        for link in self.links:
            link.users -= 1
        self.links.clear()
    def increment_links(self):
        for link in self.links:
            link.users += 1
    def write(self, text):
        text.write("\t" + self.type + ".write(): FIXME please\n")
    def string(self):
        return self.type + ".string(): FIXME please\n"
    def remesh(self):
        pass
    def rigid_offset(self, i):
        if self.objects[i] in database.node:
            ob = self.objects[i]
        elif self.objects[i] in database.rigid_dict:
            ob = database.rigid_dict[self.objects[i]]
        else:
            name = self.objects[i].name
            bpy.context.window_manager.popup_menu(lambda self, c: self.layout.label(
                "Object " + name + " is not associated with a Node"),
                title="MBDyn Error", icon='ERROR')
            raise Exception("***Model Error: Object " + name + " is not associated with a Node")
        rot = ob.matrix_world.to_quaternion().to_matrix()
        globalV = self.objects[i].matrix_world.translation - ob.matrix_world.translation
        return rot, globalV, database.node.index(ob)
    def write_node(self, text, i, node=False, position=False, orientation=False, p_label="", o_label=""):
        rot_i, globalV_i, Node_i = self.rigid_offset(i)
        localV_i = rot_i*globalV_i
        rotT = self.objects[i].matrix_world.to_quaternion().to_matrix().transposed()
        if node:
            text.write("\t\t" + str(Node_i) + ",\n")
        if position:
            text.write("\t\t\t")
            if p_label:
                text.write(p_label + ", ")
            self.write_vector(localV_i, text)
        if orientation:
            text.write(",\n\t\t\t")
            if o_label:
                text.write(o_label + ", ")
            text.write("matr,\n")
            self.write_matrix(rot_i*rotT, text, "\t\t\t\t")
    def makecopy(self):
        newcopy = copy(self)
        if hasattr(self, "objects"):
            newcopy.objects = copy(self.objects)
        newcopy.links = copy(self.links)
        newcopy.increment_links()
        newcopy.users = 0
        return newcopy

class SelectedObjects(list):
    def __init__(self, context):
        self.extend([o for o in context.selected_objects if o.type == 'MESH'])
        active = context.active_object if context.active_object in self else None
        if active:
            self.remove(active)
            self.insert(0, active)
        else:
            self.clear()

class Operator:
    def matrix_exists(self, context, matrix_type):
        if not enum_matrix(self, context, matrix_type):
            exec("bpy.ops." + root_dot + "c_" + matrix_type + "()")
    def constitutive_exists(self, context, dimension):
        if not enum_constitutive(self, context, dimension):
            if dimension == "1D":
                exec("bpy.ops." + root_dot + "c_linear_elastic(dimensions = \"1D\")")
            else:
                exec("bpy.ops." + root_dot + "c_linear_elastic(dimensions = \"3D, 6D\")")
    def drive_exists(self, context):
        if not enum_drive(self, context):
            exec("bpy.ops." + root_dot + "c_unit_drive()")
    def meter_drive_exists(self, context):
        if not enum_meter_drive(self, context):
            exec("bpy.ops." + root_dot + "c_meter_drive()")
    def element_exists(self, context):
        if not enum_element(self, context):
            exec("bpy.ops." + root_dot + "c_gravity()")
    def function_exists(self, context):
        if not enum_function(self, context):
            exec("bpy.ops." + root_dot + "c_const()")
    def friction_exists(self, context):
        if not enum_friction(self, context):
            exec("bpy.ops." + root_dot + "c_modlugre()")
    def general_data_exists(self, context):
        if not enum_general_data(self, context):
            exec("bpy.ops." + root_dot + "c_general_data()")
    def method_exists(self, context):
        if not enum_method(self, context):
            exec("bpy.ops." + root_dot + "c_crank_nicolson()")
    def nonlinear_solver_exists(self, context):
        if not enum_nonlinear_solver(self, context):
            exec("bpy.ops." + root_dot + "c_newton_raphston()")
    def eigenanalysis_exists(self, context):
        if not enum_eigenanalysis(self, context):
            exec("bpy.ops." + root_dot + "c_eigenanalysis()")
    def abort_after_exists(self, context):
        if not enum_abort_after(self, context):
            exec("bpy.ops." + root_dot + "c_abort_after()")
    def linear_solver_exists(self, context):
        if not enum_linear_solver(self, context):
            exec("bpy.ops." + root_dot + "c_linear_solver()")
    def dummy_steps_exists(self, context):
        if not enum_dummy_steps(self, context):
            exec("bpy.ops." + root_dot + "c_dummy_steps()")
    def output_data_exists(self, context):
        if not enum_output_data(self, context):
            exec("bpy.ops." + root_dot + "c_output_data()")
    def real_time_exists(self, context):
        if not enum_real_time(self, context):
            exec("bpy.ops." + root_dot + "c_real_time()")
    def assembly_exists(self, context):
        if not enum_assembly(self, context):
            exec("bpy.ops." + root_dot + "c_assembly()")
    def job_control_exists(self, context):
        if not enum_job_control(self, context):
            exec("bpy.ops." + root_dot + "c_job_control()")
    def default_output_exists(self, context):
        if not enum_default_output(self, context):
            exec("bpy.ops." + root_dot + "c_default_output()")
    def default_aerodynamic_output_exists(self, context):
        if not enum_default_aerodynamic_output(self, context):
            exec("bpy.ops." + root_dot + "c_default_aerodynamic_output()")
    def default_beam_output_exists(self, context):
        if not enum_default_beam_output(self, context):
            exec("bpy.ops." + root_dot + "c_default_beam_output()")
    def link_matrix(self, context, matrix_name, edit=True):
        context.scene.matrix_index = next(i for i, x in enumerate(context.scene.matrix_uilist)
            if x.name == matrix_name)
        matrix = database.matrix[context.scene.matrix_index]
        if edit:
            exec("bpy.ops." + root_dot + "e_" + matrix.type + "('INVOKE_DEFAULT')")
        self.entity.links.append(matrix)
    def link_constitutive(self, context, constitutive_name, edit=True):
        context.scene.constitutive_index = next(i for i, x in enumerate(context.scene.constitutive_uilist)
            if x.name == constitutive_name)
        constitutive = database.constitutive[context.scene.constitutive_index]
        if edit:
            exec("bpy.ops." + root_dot + "e_" + "_".join(constitutive.type.lower().split()) + "('INVOKE_DEFAULT')")
        self.entity.links.append(constitutive)
    def link_drive(self, context, drive_name, edit=True):
        context.scene.drive_index = next(i for i, x in enumerate(context.scene.drive_uilist)
            if x.name == drive_name)
        drive = database.drive[context.scene.drive_index]
        if edit:
            exec("bpy.ops." + root_dot + "e_" + "_".join(drive.type.lower().split()) + "('INVOKE_DEFAULT')")
        self.entity.links.append(drive)
    def link_element(self, context, element_name, edit=True):
        context.scene.element_index = next(i for i, x in enumerate(context.scene.element_uilist)
            if x.name == element_name)
        element = database.element[context.scene.element_index]
        if edit:
            exec("bpy.ops." + root_dot + "e_" + "_".join(element.type.lower().split()) + "('INVOKE_DEFAULT')")
        self.entity.links.append(element)
    def link_function(self, context, function_name, edit=True):
        context.scene.function_index = next(i for i, x in enumerate(context.scene.function_uilist)
            if x.name == function_name)
        function = database.function[context.scene.function_index]
        if edit:
            exec("bpy.ops." + root_dot + "e_" + "_".join(function.type.lower().split()) + "('INVOKE_DEFAULT')")
        self.entity.links.append(function)
    def link_friction(self, context, friction_name, edit=True):
        context.scene.friction_index = next(i for i, x in enumerate(context.scene.friction_uilist)
            if x.name == friction_name)
        friction = database.friction[context.scene.friction_index]
        if edit:
            exec("bpy.ops." + root_dot + "e_" + "_".join(friction.type.lower().split()) + "('INVOKE_DEFAULT')")
        self.entity.links.append(friction)
    def link_definition(self, context, definition_name, edit=True):
        context.scene.definition_index = next(i for i, x in enumerate(context.scene.definition_uilist)
            if x.name == definition_name)
        definition = database.definition[context.scene.definition_index]
        if edit:
            exec("bpy.ops." + root_dot + "e_" + "_".join(definition.type.lower().split()) + "('INVOKE_DEFAULT')")
        self.entity.links.append(definition)
    def draw_link(self, layout, link_name, link_edit):
        row = layout.row()
        row.prop(self, link_name)
        row.prop(self, link_edit, toggle=True)
    def draw_panel_pre(self, context, layout):
        pass
    def draw_panel_post(self, context, layout):
        pass

class TreeMenu(list):
    def __init__(self, tree):
        self.leaf_maker(tree[0], tree[1])
    def leaf_maker(self, base, branch):
        is_a_leaf = OrderedDict()
        R = iter(range(len(branch)))
        for i in R:
            if isinstance(branch[i], list):
                assert isinstance(branch[i-1], str)
                is_a_leaf[branch[i-1]] = False
                self.leaf_maker(branch[i-1], branch[i])
            else:
                assert isinstance(branch[i], str)
                is_a_leaf[branch[i]] = True
        class Menu(bpy.types.Menu):
            bl_label = base
            bl_idname = root_dot + "_".join(base.lower().split())
            def draw(self, context):
                layout = self.layout
                layout.operator_context = 'INVOKE_DEFAULT'
                for name, leaf in is_a_leaf.items():
                    if leaf:
                        layout.operator(root_dot + "c_" + "_".join(name.lower().split()))
                    else:
                        layout.menu(root_dot + "_".join(name.lower().split()))
        self.append(Menu)
    def register(self):
        for klass in self:
            bpy.utils.register_class(klass)
    def unregister(self):
        for klass in self:
            bpy.utils.unregister_class(klass)

class Operators(list):
    def __init__(self, klasses, entity_list):
        for name, klass in klasses.items():
            klass.entity_list = entity_list
            klass.module = klass.__module__.split(".")[1]
            class Create(bpy.types.Operator, klass):
                bl_idname = root_dot + "c_" + "_".join(name.lower().split())
                bl_options = {'REGISTER', 'INTERNAL'}
                def invoke(self, context, event):
                    self.prereqs(context)
                    return context.window_manager.invoke_props_dialog(self)
                def execute(self, context):
                    index, uilist = self.get_uilist(context)
                    self.index = len(uilist)
                    uilist.add()
                    self.set_index(context, self.index)
                    self.entity_list.append(self.create_entity())
                    uilist[self.index].name = self.name
                    self.store(context)
                    context.scene.dirty_simulator = True
                    self.set_index(context, self.index)
                    return {'FINISHED'}
            class Edit(bpy.types.Operator, klass):
                bl_label = "Edit"
                bl_idname = root_dot + "e_" + "_".join(name.lower().split())
                bl_options = {'REGISTER', 'INTERNAL'}
                def invoke(self, context, event):
                    self.prereqs(context)
                    self.index, uilist = self.get_uilist(context)
                    self.assign(context)
                    return context.window_manager.invoke_props_dialog(self)
                def execute(self, context):
                    self.store(context)
                    context.scene.dirty_simulator = True
                    self.set_index(context, self.index)
                    return {'FINISHED'}
            class Duplicate(bpy.types.Operator, klass):
                bl_label = "Duplicate"
                bl_idname = root_dot + "d_" + "_".join(name.lower().split())
                bl_options = {'REGISTER', 'INTERNAL'}
                def execute(self, context):
                    index, uilist = self.get_uilist(context)
                    self.index = len(uilist)
                    uilist.add()
                    self.set_index(context, self.index)
                    entity = self.entity_list[index].makecopy()
                    self.entity_list.append(entity)
                    uilist[self.index].name = entity.name
                    context.scene.dirty_simulator = True
                    self.set_index(context, self.index)
                    return {'FINISHED'}
            class Menu(bpy.types.Menu, klass):
                bl_label = name
                bl_idname = root_dot + "m_" + "_".join(name.lower().split())
                def draw(self, context):
                    layout = self.layout
                    layout.operator_context = 'INVOKE_DEFAULT'
                    layout.operator(root_dot + "e_" + self.bl_idname[8:])
                    layout.operator(root_dot + "d_" + self.bl_idname[8:])
                    if self.module == "element":
                        layout.operator(root_dot + "reassign")
            self.extend([Create, Edit, Duplicate, Menu])
    def register(self):
        for klass in self:
            bpy.utils.register_class(klass)
    def unregister(self):
        for klass in self:
            bpy.utils.unregister_class(klass)

class UI(list):
    def __init__(self, entity_tree, klass, entity_list, entity_name):
        menu = root_dot + "_".join(entity_tree[0].lower().split())
        klass.entity_list = entity_list
        self.make_list = klass.make_list
        self.delete_list = klass.delete_list
        class ListItem(bpy.types.PropertyGroup, klass):
            def update(self, context):
                index, uilist = self.get_uilist(context)
                names = [e.name for i, e in enumerate(self.entity_list) if i != index]
                name = uilist[index].name
                if name in names:
                    if ".001" <= name[-4:] and name[-4:] <= ".999":
                        name = name[:-4]
                    if name in names:
                        name += "." + str(1).zfill(3)
                    qty = 1
                    while name in names:
                        qty += 1
                        name = name[:-4] + "." + str(qty).zfill(3)
                        if qty >=999:
                            raise ValueError(name)
                    uilist[index].name = name
                self.entity_list[index].name = name
            name = bpy.props.StringProperty(update=update)
        class List(bpy.types.UIList):
            bl_idname = entity_name
            def draw_item(self, context, layout, data, item, icon, active_data, active_property, index, flt_flag):
                layout.prop(item, "name", text="", emboss=False, icon='OBJECT_DATAMODE')
        class Delete(bpy.types.Operator, klass):
            bl_idname = entity_name + ".delete"
            bl_options = {'REGISTER', 'INTERNAL'}
            bl_label = "Delete"
            bl_description = "Delete the selected " + entity_name
            @classmethod
            def poll(self, context):
                index, uilist = super().get_uilist(context)
                return len(uilist) > 0 and not self.entity_list[index].users
            def execute(self, context):
                index, uilist = self.get_uilist(context)
                uilist.remove(index)
                for link in self.entity_list[index].links:
                    link.users -= 1
                self.entity_list.pop(index)
                context.scene.dirty_simulator = True
                self.set_index(context, 0 if index == 0 and 0 < len(uilist) else index-1)
                return{'FINISHED'}
        class Panel(bpy.types.Panel, klass):
            bl_space_type = 'VIEW_3D'
            bl_region_type = 'TOOLS'
            bl_category = category
            bl_idname = "_".join([category, entity_name])
            def draw(self, context):
                layout = self.layout
                self.draw_panel_pre(context, layout)
                scene = context.scene
                row = layout.row()
                row.template_list(entity_name, entity_name + "_list",
                    scene, entity_name + "_uilist", scene, entity_name + "_index" )
                col = row.column(align=True)
                col.menu(menu, icon='ZOOMIN', text="")
                col.operator(entity_name + ".delete", icon='ZOOMOUT', text="")
                index, uilist = self.get_uilist(context)
                if 0 < len(uilist):
                    col.menu(root_dot + "m_" +
                        "_".join(self.entity_list[index].type.lower().split()), icon='DOWNARROW_HLT', text="")
                self.draw_panel_post(context, layout)
        self.extend([ListItem, List, Delete, Panel])
    def register(self):
        for klass in self:
            bpy.utils.register_class(klass)
        self.make_list(self[0])
    def unregister(self):
        for klass in self:
            bpy.utils.unregister_class(klass)
        self.delete_list()

class Bundle(list):
    def __init__(self, tree, klass, klasses, entity_list, entity_name):
        self.append(UI(tree, klass, entity_list, entity_name))
        self.append(TreeMenu(tree))
        self.append(Operators(klasses, entity_list))
    def register(self):
        for ob in self:
            ob.register()
    def unregister(self):
        for ob in self:
            ob.unregister()
