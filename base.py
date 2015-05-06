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
    imp.reload(Database)
    imp.reload(Common)
else:
    import bpy
    from .database import Database
    from .common import Common

category = "MBDyn"
root_dot = "_".join(category.lower().split())+"."
database = Database()

class Props:
    class Floats(bpy.types.PropertyGroup):
        value = bpy.props.FloatProperty(min=-9.9e10, max=9.9e10, step=100, precision=6)
    @classmethod
    def register(self):
        bpy.utils.register_class(Props.Floats)
    @classmethod
    def unregister(self):
        bpy.utils.unregister_class(Props.Floats)

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
def enum_constitutive(self, context, constitutive_dimension):
    return [(c.name, c.name, "") for i, c in enumerate(context.scene.constitutive_uilist)
        if database.constitutive[i].type.split()[-1] == constitutive_dimension]
def enum_constitutive_1D(self, context):
    return enum_constitutive(self, context, "1D")
def enum_constitutive_3D(self, context):
    return enum_constitutive(self, context, "3D")
def enum_constitutive_6D(self, context):
    return enum_constitutive(self, context, "6D")
def enum_drive(self, context):
    return [(d.name, d.name, "") for d in context.scene.drive_uilist]
def enum_function(self, context):
    return [(f.name, f.name, "") for f in context.scene.function_uilist]
def enum_friction(self, context):
    return [(f.name, f.name, "") for f in context.scene.friction_uilist]

class Entity(Common):
    database = database
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
        text.write("\t"+self.type+".write(): FIXME please\n")

class SelectedObjects(list):
    def __init__(self, context):
        super().__init__()
        self.extend([o for o in context.selected_objects if o.type == 'MESH'])
        active = context.active_object if context.active_object.type == 'MESH' else None
        if self and active:
            self.remove(active)
            self.insert(0, active)

class Operator:
    database = database
    def matrix_exists(self, context, matrix_type):
        if not enum_matrix(self, context, matrix_type):
            exec("bpy.ops."+root_dot+"c_"+matrix_type+"()")
    def constitutive_exists(self, context, constitutive_dimension):
        if not enum_constitutive(self, context, constitutive_dimension):
            exec("bpy.ops."+root_dot+"c_linear_elastic_"+constitutive_dimension.lower()+"()")
    def drive_exists(self, context):
        if not enum_drive(self, context):
            exec("bpy.ops."+root_dot+"c_unit_drive()")
    def function_exists(self, context):
        if not enum_function(self, context):
            exec("bpy.ops."+root_dot+"c_const()")
    def friction_exists(self, context):
        if not enum_friction(self, context):
            exec("bpy.ops."+root_dot+"c_modlugre()")
    def link_matrix(self, context, matrix_name):
        context.scene.matrix_index = next(i for i, x in enumerate(context.scene.matrix_uilist)
            if x.name == matrix_name)
        matrix = self.database.matrix[context.scene.matrix_index]
        exec("bpy.ops."+root_dot+"e_"+matrix.type+"('INVOKE_DEFAULT')")
        self.entity.links.append(matrix)
    def link_constitutive(self, context, constitutive_name):
        context.scene.constitutive_index = next(i for i, x in enumerate(context.scene.constitutive_uilist)
            if x.name == constitutive_name)
        constitutive = self.database.constitutive[context.scene.constitutive_index]
        exec("bpy.ops."+root_dot+"e_"+"_".join(constitutive.type.lower().split())+"('INVOKE_DEFAULT')")
        self.entity.links.append(constitutive)
    def link_drive(self, context, drive_name):
        context.scene.drive_index = next(i for i, x in enumerate(context.scene.drive_uilist)
            if x.name == drive_name)
        drive = self.database.drive[context.scene.drive_index]
        exec("bpy.ops."+root_dot+"e_"+"_".join(drive.type.lower().split())+"('INVOKE_DEFAULT')")
        self.entity.links.append(drive)
    def link_function(self, context, function_name):
        context.scene.function_index = next(i for i, x in enumerate(context.scene.function_uilist)
            if x.name == function_name)
        function = self.database.function[context.scene.function_index]
        exec("bpy.ops."+root_dot+"e_"+"_".join(function.type.lower().split())+"('INVOKE_DEFAULT')")
        self.entity.links.append(function)
    def link_friction(self, context, friction_name):
        context.scene.friction_index = next(i for i, x in enumerate(context.scene.friction_uilist)
            if x.name == friction_name)
        friction = self.database.friction[context.scene.friction_index]
        exec("bpy.ops."+root_dot+"e_"+"_".join(friction.type.lower().split())+"('INVOKE_DEFAULT')")
        self.entity.links.append(friction)

class TreeMenu(list):
    def __init__(self, entity_tree):
        self.leaves = list()
        self.tree_maker(entity_tree)
    def tree_maker(self, tree):
        name_is_a_leaf = list()
        for branch in tree[1:]:
            if isinstance(branch, list):
                if len(branch) == 2 and isinstance(branch[1], list):
                    name_is_a_leaf.append((branch[0], False))
                    self.tree_maker(branch)
                else:
                    for j in branch:
                        name_is_a_leaf.append((j, True))
            else:
                name_is_a_leaf.append((branch, True))
        class Menu(bpy.types.Menu):
            bl_label = tree[0]
            bl_idname = root_dot+"_".join(tree[0].lower().split())
            def draw(self, context):
                layout = self.layout
                layout.operator_context = 'INVOKE_DEFAULT'
                for name, is_a_leaf in name_is_a_leaf:
                    if is_a_leaf:
                        op = layout.operator(root_dot+"c_"+"_".join(name.lower().split()))
                    else:
                        layout.menu(root_dot+"_".join(name.lower().split()))
        self.append(Menu)
        self.leaves.extend([name for name, is_a_leaf in name_is_a_leaf if is_a_leaf])
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
            class Op:
                def select_and_activate(self, context):
                    if hasattr(self.entity, "objects") and self.entity.objects:
                        bpy.ops.object.select_all(action='DESELECT')
                        for ob in self.entity.objects:
                            ob.select = True
                        context.scene.objects.active = self.entity.objects[0]
            class Create(bpy.types.Operator, klass, Op):
                bl_idname = root_dot+"c_"+"_".join(name.lower().split())
                bl_options = {'REGISTER', 'INTERNAL'}
                def invoke(self, context, event):
                    self.defaults(context)
                    return context.window_manager.invoke_props_dialog(self)
                def execute(self, context):
                    index, uilist = self.get_uilist(context)
                    self.index = len(uilist)
                    uilist.add()
                    self.set_index(context, self.index)
                    self.entity_list.append(self.create_entity())
                    uilist[self.index].name = self.name
                    self.entity_name = uilist[self.index].name
                    self.store(context)
                    self.select_and_activate(context)
                    database.pickle()
                    return {'FINISHED'}
            class Edit(bpy.types.Operator, klass, Op):
                bl_idname = root_dot+"e_"+"_".join(name.lower().split())
                bl_options = {'REGISTER', 'INTERNAL'}
                def invoke(self, context, event):
                    self.assign(context)
                    self.select_and_activate(context)
                    return context.window_manager.invoke_props_dialog(self)
                def execute(self, context):
                    self.store(context)
                    self.select_and_activate(context)
                    database.pickle()
                    return {'FINISHED'}
            self.extend([Create, Edit])
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
                    if '.001' <= name[-4:] and name[-4:] <= '.999':
                        name = name[:-4]
                    if name in names:
                        name += '.'+str(1).zfill(3)
                    qty = 1
                    while name in names:
                        qty += 1
                        name = name[:-4]+'.'+str(qty).zfill(3)
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
            bl_idname = entity_name+".delete"
            bl_options = {'REGISTER', 'INTERNAL'}
            bl_label = "Delete"
            bl_description = "Delete the selected "+entity_name
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
                self.set_index(context, index-1)
                return{'FINISHED'}
        class Panel(bpy.types.Panel, klass):
            bl_space_type = "VIEW_3D"
            bl_region_type = "TOOLS"
            bl_category = category
            bl_idname = "_".join([category, entity_name])
            def draw(self, context):
                layout = self.layout
                scene = context.scene
                row = layout.row()
                row.template_list(entity_name, entity_name+"_list",
                    scene, entity_name+"_uilist", scene, entity_name+"_index" )
                col = row.column(align=True)
                col.menu(menu, icon='ZOOMIN', text="")
                col.operator(entity_name+".delete", icon='ZOOMOUT', text="")
                index, uilist = self.get_uilist(context)
                if 0 < len(uilist):
                    op = col.operator(root_dot+"e_"+
                        '_'.join(self.entity_list[index].type.lower().split()), icon='DOWNARROW_HLT', text="")
        self.extend([ListItem, List, Delete, Panel])
    def register(self):
        for cls in self:
            bpy.utils.register_class(cls)
        self.make_list(self[0])
    def unregister(self):
        for cls in self:
            bpy.utils.unregister_class(cls)
        self.delete_list()

