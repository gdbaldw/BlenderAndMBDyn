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
    imp.reload(aerodynamic_types, beam_types)
    imp.reload(force_types, genel_types)
    imp.reload(joint_types)
    imp.reload(environment_types)
    imp.reload(node_types)
    imp.reload(rigid_body_types)
    imp.reload(structural_static_types)
    imp.reload(structural_dynamic_types)
else:
    import bpy
    from .common import Common, aerodynamic_types, beam_types, force_types, genel_types, joint_types, environment_types, node_types, rigid_body_types, structural_static_types, structural_dynamic_types

from io import BytesIO
import pickle
from base64 import b64encode, b64decode
from mathutils import Vector
from collections import deque

class Pickler(pickle.Pickler):
    def persistent_id(self, obj):
        return repr(obj) if repr(obj).startswith("bpy.data") else None

class Unpickler(pickle.Unpickler):
    def persistent_load(self, pid):
        if not pid.startswith("bpy.data") and len(pid.split()) == 1:
            raise pickle.UnpicklingError(pid + " is forbidden")
        exec("id_data = " + pid)
        name = locals()["id_data"].mbdyn_name
        exec("id_data = " + pid.split("[")[0] + "[\"" + name + "\"]")
        return locals()["id_data"]
    def find_class(self, module, name):
        if module.startswith("BlenderAndMBDyn"):
            module = ".".join((__package__, module.split(".", 1)[1]))
        elif module == "builtins" and name in ("exec", "eval"):
            raise pickle.UnpicklingError("global " + ".".join((module, name)) + " is forbidden")
        return super().find_class(module, name)

bpy.types.Scene.pickled_database = bpy.props.StringProperty()

class EntityLookupError(LookupError):
    pass

class Entities(list):
    def filter(self, type_name, obj=None):
        return [e for e in self if e.type == type_name and 
            (not obj or (hasattr(e, "objects") and e.objects[0] == obj))]
    def get_by_name(self, name):
        if name != "New":
            for e in self:
                if e.name == name:
                    return e
        raise EntityLookupError

class Database(Common):
    def __init__(self):
        self.element = Entities()
        self.drive = Entities()
        self.driver = Entities()
        self.friction = Entities()
        self.shape = Entities()
        self.function = Entities()
        self.ns_node = Entities()
        self.constitutive = Entities()
        self.matrix = Entities()
        self.frame = Entities()
        self.definition = Entities()
        self.simulator = Entities()
        self.node = list()
        self.drive_callers = list()
        self.rigid_dict = dict()
        self.dummy_dict = dict()
        self.structural_dynamic_nodes = set()
        self.structural_static_nodes = set()
        self.structural_dummy_nodes = set()
        self.clear()
    def clear(self):
        self.element.clear()
        self.drive.clear()
        self.driver.clear()
        self.friction.clear()
        self.shape.clear()
        self.function.clear()
        self.ns_node.clear()
        self.constitutive.clear()
        self.matrix.clear()
        self.frame.clear()
        self.definition.clear()
        self.simulator.clear()
        self.node.clear()
        self.drive_callers.clear()
        self.rigid_dict.clear()
        self.dummy_dict.clear()
        self.structural_dynamic_nodes.clear()
        self.structural_static_nodes.clear()
        self.structural_dummy_nodes.clear()
        self.scene = None
    def all_entities(self):
        return (self.element + self.drive + self.driver + self.friction + self.shape + self.function +
            self.ns_node + self.constitutive + self.matrix + self.frame + self.definition + self.simulator)
    def entities_using(self, objects):
        set_objects = set(objects)
        entities = list()
        for entity in self.all_entities():
            if hasattr(entity, "objects"):
                if not set_objects.isdisjoint(set(entity.objects)):
                    entities.append(entity)
        for element in self.element:
            if element.type == 'Driven' and element.links[1] in elements:
                elements.append(element)
        return entities
    def entities_originating_from(self, objects):
        entities = list()
        for entity in self.all_entities():
            if hasattr(entity, "objects"):
                if entity.objects[0] in objects:
                    entities.append(entity)
        for element in self.element:
            if element.type == 'Driven' and element.links[1] in elements:
                elements.append(element)
        return entities
    def users_of(self, entity):
        return list({e for e in self.all_entities() if entity in e.links})
    def pickle(self):
        if not self.scene:
            self.scene = bpy.context.scene
        bpy.context.scene.mbdyn_name = bpy.context.scene.name
        for obj in bpy.context.scene.objects:
            obj.mbdyn_name = obj.name
        with BytesIO() as f:
            p = Pickler(f)
            p.dump(self)
            self.scene.pickled_database = b64encode(f.getvalue()).decode()
    def unpickle(self):
        self.clear()
        if bpy.context.scene.pickled_database:
            with BytesIO(b64decode(bpy.context.scene.pickled_database.encode())) as f:
                up = Unpickler(f)
                for k, v in vars(up.load()).items():
                    if type(v) in [list, Entities]:
                        self.__dict__[k].extend(v)
                    elif type(v) in [dict, set]:
                        self.__dict__[k].update(v)
                    else:
                        self.__dict__[k] = v
    def replace(self):
        self.pickle()
        self.unpickle()
    def write_indexes(self, f):
        self.structural_dynamic_nodes.clear()
        self.structural_static_nodes.clear()
        self.structural_dummy_nodes.clear()
        self.rigid_dict = {e.objects[0] : e.objects[1] for e in self.element.filter("Rigid offset")}
        nodes = set()
        for e in (e for e in self.element + self.drive if hasattr(e, "objects")):
            ob = self.rigid_dict[e.objects[0]] if e.objects[0] in self.rigid_dict else e.objects[0]
            nodes |= set([ob])
            if e.type in structural_dynamic_types:
                self.structural_dynamic_nodes |= set([ob])
            elif e.type in structural_static_types:
                self.structural_static_nodes |= set([ob])
            elif e.type == "Dummy":
                self.structural_dummy_nodes |= set([ob])
                dummy_dict[ob] = e.objects[1]
        self.structural_static_nodes -= self.structural_dynamic_nodes | self.structural_dummy_nodes
        self.node.clear()
        self.node.extend(list(nodes))
        self.node.sort(key = lambda x: x.name)
        f.write(
        "\n/* Label Indexes\n")
        if self.frame:
            f.write("\nreference frames:\n")
            for i, frame in enumerate(self.frame):
                f.write("\t" + str(i) + "\t- " + frame.objects[0].name + "\n")
        if self.node:
            f.write("\nnodes:\n")
            for i, entity in enumerate(self.node):
                f.write("\t" + str(i) + "\t- " + entity.name + "\n")
        for clas in "ns_node drive driver element".split():
            if eval("self." + clas):
                f.write("\n" + clas + "s:\n")
                for i, entity in enumerate(eval("self." + clas)):
                    f.write("\t" + str(i) + "\t- " + entity.name + " (" + entity.type)
                    if entity.users:
                        f.write(", users=" + str(entity.users))
                    f.write(")")
                    if clas == "element" and hasattr(entity, "objects"):
                        names = [o.name for o in entity.objects if o]
                        if names:
                            string = " objects: "
                            for name in names:
                                string += name + ", "
                            string = string[:-2] + "."
                            f.write(string)
                    names = [l.name for l in entity.links if l]
                    if names:
                        string = " links: "
                        for name in names:
                            string += name + ", "
                        string = string[:-2] + "."
                        f.write(string)
                    f.write("\n")
        f.write("\n*/\n\n")
    def write_control(self, f, context):
        structural_node_count = len(
            self.structural_static_nodes | self.structural_dynamic_nodes | self.structural_dummy_nodes)
        joint_count = len([e for e in self.element if e.type in joint_types])
        force_count = len([e for e in self.element if e.type in force_types])
        rigid_body_count = len([e for e in self.element if e.type in rigid_body_types])
        aerodynamic_element_count = len([e for e in self.element if e.type in aerodynamic_types])
        rotor_count = len([e for e in self.element if e.type in ["Rotor"]])
        genel_count = len([e for e in self.element if e.type in genel_types])
        beam_count = len([e for e in self.element if e.type in beam_types and not hasattr(e, "consumer")])
        air_properties = bool([e for e in self.element if e.type in ["Air properties"]])
        gravity = bool([e for e in self.element if e.type in ["Gravity"]])
        self.file_driver_count = 0
        bailout_upper = False
        upper_bailout_time = 0.0
        for driver in self.driver:
            driver.columns = list()
        self.drive_callers.clear()
        for drive in self.drive:
            if drive.type == "File drive":
                drive.links[0].columns.append(drive)
            if not drive.users:
                self.drive_callers.append(drive)
        for driver in self.driver:
            if driver.columns:
                self.file_driver_count += 1
                if driver.bailout_upper:
                    if driver.filename:
                        name = driver.filename.replace(" ", "")
                    else:
                        name = driver.name.replace(" ", "")
                    command = "tail -n 1 " + os.path.splitext(context.blend_data.filepath)[0] + ".echo_" + name + " | awk '{print $1}'"
                    f1 = TemporaryFile()
                    call(command, shell=True, stdout=f1)
                    try:
                        f1.seek(0)
                        upper_bailout_time = min(upper_bailout_time, float(f1.read()) - 1e-3)
                    except:
                        pass
                    f1.close()
        electric_node_count = len([e for e in self.ns_node if e.type in ["Electric"]])
        abstract_node_count = len([e for e in self.ns_node if e.type in ["Abstract"]])
        hydraulic_node_count = len([e for e in self.ns_node if e.type in ["Hydraulic"]])
        #parameter_node_count = len([e for e in self.ns_node if e.type in ["Parameter"]])
        if structural_node_count:
            f.write("\tstructural nodes: " + str(structural_node_count) + ";\n")
        if electric_node_count:
            f.write("\telectric nodes: " + str(electric_node_count) + ";\n")
        if abstract_node_count:
            f.write("\tabstract nodes: " + str(abstract_node_count) + ";\n")
        if hydraulic_node_count:
            f.write("\thydraulic nodes: " + str(hydraulic_node_count) + ";\n")
        if joint_count:
            f.write("\tjoints: " + str(joint_count) + ";\n")
        if force_count:
            f.write("\tforces: " + str(force_count) + ";\n")
        if genel_count:
            f.write("\tgenels: " + str(genel_count) + ";\n")
        if beam_count:
            f.write("\tbeams: " + str(beam_count) + ";\n")
        if rigid_body_count:
            f.write("\trigid bodies: " + str(rigid_body_count) + ";\n")
        if air_properties:
            f.write("\tair properties;\n")
        if gravity:
            f.write("\tgravity;\n")
        if aerodynamic_element_count:
            f.write("\taerodynamic elements: " + str(aerodynamic_element_count) + ";\n")
        if rotor_count:
            f.write("\trotors: " + str(rotor_count) + ";\n")
        if self.file_driver_count:
            f.write("\tfile drivers: " + str(self.file_driver_count) + ";\n")
    def write_structural_node(self, f, node, frame):
        frame_label = str(self.frame.index(frame)) if frame else "global"
        location, orientation = node.matrix_world.translation, node.matrix_world.to_quaternion().to_matrix()
        if frame:
            location = location - frame.objects[0].matrix_world.translation
            orientation = frame.objects[0].matrix_world.to_quaternion().to_matrix().transposed()*orientation
        f.write("\t\treference, " + frame_label + ", ")
        self.write_vector(location, f, ",\n")
        f.write("\t\treference, " + frame_label + ", matr,\n")
        self.write_matrix(orientation, f, "\t"*3)
        f.write(",\n" +
            "\t\treference, " + frame_label + ", null,\n" +
            "\t\treference, " + frame_label + ", null;\n")
    def write(self, f):
        frame_for, frames, parent_of = dict(), list(), dict()
        for frame in self.frame:
            frame_for.update({ob : frame for ob in frame.objects[1:]})
            frames.append(frame)
            parent_of.update({frame : parent for parent in self.frame if frame.objects[0] in parent.objects[1:]})
        if self.frame:
            f.write("\n")
        while frames:
            frame = frames.pop()
            if frame in parent_of and parent_of[frame] in frames:
                frames.appendleft(frame)
            else:
                parent = parent_of[frame] if frame in parent_of else None
                parent_label = str(self.frame.index(parent_of[frame])) if parent else "global"
                vectors = list()
                for link in frame.links:
                    if link.subtype in "null default".split():
                        vectors.append(Vector([0., 0., 0.]))
                    else:
                        vectors.append(Vector(link.floats) * (link.factor if link.scale else 1))
                location = frame.objects[0].matrix_world.translation - (parent.objects[0].matrix_world.translation if parent else Vector([0., 0., 0.]))
                rot = frame.objects[0].matrix_world.to_quaternion().to_matrix()
                rot_parent = parent_of[frame].objects[0].matrix_world.to_quaternion().to_matrix() if parent else rot
                orientation = rot_parent.transposed()*rot if parent else rot
                f.write("reference: " + str(self.frame.index(frame)) + ",\n" + "\treference, " + parent_label + ", ")
                self.write_vector(rot_parent.transposed()*location if parent else location, f, ",\n")
                f.write("\treference, " + parent_label + ", matr,\n")
                self.write_matrix(orientation, f, "\t\t")
                f.write(",\n\treference, " + parent_label + ", ")
                self.write_vector(orientation*vectors[0], f, ",\n")
                f.write("\treference, " + parent_label + ", ")
                self.write_vector(orientation*vectors[1], f, ";\n")
        if self.node:
            f.write("\nbegin: nodes;\n")
            for node in self.structural_static_nodes:
                f.write("\tstructural: " + str(self.node.index(node)) + ", static,\n")
                self.write_structural_node(f, node, frame_for[node] if node in frame_for else None)
            for node in self.structural_dynamic_nodes:
                f.write("\tstructural: " + str(self.node.index(node)) + ", dynamic,\n")
                self.write_structural_node(f, node, frame_for[node] if node in frame_for else None)
            for node in self.structural_dummy_nodes:
                base_node = dummy_dict[node]
                rot = base_node.matrix_world.to_quaternion().to_matrix()
                globalV = node.matrix_world.translation - base_node.matrix_world.translation
                localV = rot*globalV
                rotT = node.matrix_world.to_quaternion().to_matrix()
                f.write("\tstructural: " + str(self.node.index(node)) + ", dummy,\n\t\t" +
                    str(self.node.index(base_node)) + ", offset,\n\t\t\t")
                self.write_vector(localV, f, ",\n\t\t\tmatr,\n")
                self.write_matrix(rot*rotT, f, "\t\t\t\t")
                f.write(";\n")
            """
            for i, ns_node in enumerate(self.ns_node):
                if ns_node.type == "Electric":
                    f.write("\telectric: " + str(i) + ", value, " + str(ns_node._args[0]))
                    if ns_node._args[1]: f.write(", derivative, " + str(ns_node._args[2]))
                    f.write(";\n")
                if ns_node.type == "Abstract":
                    f.write("\tabstract: " + str(i) + ", value, " + str(ns_node._args[0]))
                    if ns_node._args[1]: f.write(", differential, " + str(ns_node._args[2]))
                    f.write(";\n")
                if ns_node.type == "Hydraulic":
                    f.write("\thydraulic: " + str(i) + ", value, " + str(ns_node._args[0]) + ";\n")
            """
            f.write("end: nodes;\n")
        if self.file_driver_count:
            f.write("\nbegin: drivers;\n")
            for driver in self.Driver:
                if driver.users:
                    driver.write(f)
            f.write("end: drivers;\n")
        self.drive_indenture = 1
        drive_callers = [drive for drive in self.drive_callers if drive.users]
        if drive_callers:
            f.write("\n")
            for drive in drive_callers:
                name = drive.name.replace(" ", "").replace(".", "__")
                f.write("set: integer " + name + " = " + str(self.drive.index(drive)) + ";\n\tdrive caller: " + name + ", " + drive.string() + ";\n")
        functions = [function for function in self.function if function.users]
        if functions:
            f.write("\n")
            for function in self.function:
                function.written = False
            for function in functions:
                function.write(f)
        if self.element:
            self.drive_indenture = 2
            f.write("\nbegin: elements;\n")
            try:
                for element_type in aerodynamic_types + beam_types + ["Body"] + force_types + genel_types + joint_types + ["Rotor"] + environment_types + ["Driven"]:
                    for element in self.element:
                        if element.type == element_type:
                            element.write(f)
            except Exception as e:
                print(e)
                f.write(str(e) + "\n")
            f.write("end: elements;\n")
        del self.drive_indenture
