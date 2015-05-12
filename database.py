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
from pickle import Pickler, Unpickler
from base64 import b64encode, b64decode
from mathutils import Vector

bpy.types.Scene.pickled_database = bpy.props.StringProperty()

class Entities(list):
    def filter(self, type_name, obj=None):
        return [e for e in self if e.type == type_name and 
            (not obj or (hasattr(e, "objects") and e.objects[0] == obj))]

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
        self.node = list()
        self.node_dict = dict()
        self.rigid_dict = dict()
        self.dummy_dict = dict()
        self.clear()
        self.defaults()
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
        self.node.clear()
        self.node_dict.clear()
        self.rigid_dict.clear()
        self.dummy_dict.clear()
        self.filepath = None
        self.scene = None
    def defaults(self):
        self.parameters = "default"
        self.datablocks = "overwrite"
        self.integrator = "initial value"
        self.t0 = 0.0
        self.tN = 0.0
        self.dt = 1.0e-3
        self.maxI = 10
        self.tol = 1.0e-6
        self.mod_test = False
        self.dTol = 2.0
        self.dC = 1.0e-3
        self.fps = 30
        self.precision = 6
        self.port = 5500
        self.hostname = "127.0.0.1"
        self.posixRT = False
    def pickle(self):
        if not self.scene:
            self.scene = bpy.context.scene
        def _repr(obj):
            return repr(obj) if repr(obj).startswith("bpy.data") else None
        with BytesIO() as f:
            p = Pickler(f)
            p.persistent_id = _repr
            p.dump(self)
            self.scene.pickled_database = b64encode(f.getvalue()).decode()
    def unpickle(self):
        self.clear()
        self.defaults()
        def _exec(_repr):
            exec("id_data = "+_repr)
            return locals()["id_data"]
        if bpy.context.scene.pickled_database:
            with BytesIO(b64decode(bpy.context.scene.pickled_database.encode())) as f:
                up = Unpickler(f)
                up.persistent_load = _exec
                for k, v in vars(up.load()).items():
                    if type(v) in [list, Entities]:
                        self.__dict__[k].extend(v)
                    elif type(v) is dict:
                        self.__dict__[k].update(v)
                    else:
                        self.__dict__[k] = v
    def replace(self):
        self.pickle()
        self.unpickle()
    def write(self, text):
        self.rigid_dict = {e.objects[0] : e.objects[1] for e in self.element.filter("Rigid offset")}
        nodes = set()
        self.structural_dynamic_nodes = set()
        self.structural_static_nodes = set()
        self.structural_dummy_nodes = set()
        for e in (e for e in self.element + self.drive if hasattr(e, "objects")):
            ob = self.rigid_dict[e.objects[0]] if e.objects[0] in self.rigid_dict else e.objects[0]
            nodes |= set([ob])
            if e.type in structural_dynamic_types:
                self.structural_dynamic_nodes |= set([ob])
            elif e.type in structural_static_types:
                self.structural_static_nodes |= set([ob])
            elif e.type == 'Dummy':
                self.structural_dummy_nodes |= set([ob])
                dummy_dict[ob] = e.objects[1]
        self.structural_static_nodes -= self.structural_dynamic_nodes | self.structural_dummy_nodes
        structural_node_count = len(
            self.structural_static_nodes | self.structural_dynamic_nodes | self.structural_dummy_nodes)
        self.node.clear()
        self.node.extend(list(nodes))
        self.node.sort(key = lambda x: x.name)
        frame_dict = dict()
        for i, f in enumerate(self.frame):
            frame_dict.update({ob : str(i) for ob in f.objects[1:]})
        joint_count = len([e for e in self.element if e.type in joint_types])
        force_count = len([e for e in self.element if e.type in force_types])
        rigid_body_count = len([e for e in self.element if e.type in rigid_body_types])
        aerodynamic_element_count = len([e for e in self.element if e.type in aerodynamic_types])
        rotor_count = len([e for e in self.element if e.type in ['Rotor']])
        genel_count = len([e for e in self.element if e.type in genel_types])
        beam_count = len([e for e in self.element if e.type in beam_types])
        air_properties = bool([e for e in self.element if e.type in ['Air properties']])
        gravity = bool([e for e in self.element if e.type in ['Gravity']])
        file_driver_count = 0
        bailout_upper = False
        upper_bailout_time = 0.0
        for driver in self.driver:
            driver.columns = list()
        drive_callers = list()
        for drive in self.drive:
            if drive.type == 'File drive':
                drive.links[0].columns.append(drive)
            if not drive.users:
                drive_callers.append(drive)
        for driver in self.driver:
            if driver.columns:
                file_driver_count += 1
                if driver.bailout_upper:
                    if driver.filename:
                        name = driver.filename.replace(' ', '')
                    else:
                        name = driver.name.replace(' ', '')
                    command = "tail -n 1 "+os.path.splitext(database.filepath)[0]+".echo_"+name+" | awk '{print $1}'"
                    f1 = TemporaryFile()
                    call(command, shell=True, stdout=f1)
                    try:
                        f1.seek(0)
                        upper_bailout_time = min(upper_bailout_time, float(f1.read()) - self.dt)
                    except:
                        pass
                    f1.close()
        if self.tN:
            self.final_time = self.tN
        elif upper_bailout_time:
            self.final_time = upper_bailout_time
        else:
            self.final_time = self.t0 + float(
                bpy.context.scene.frame_end - bpy.context.scene.frame_start)/float(self.fps)
        electric_node_count = len([e for e in self.ns_node if e.type in ["Electric"]])
        abstract_node_count = len([e for e in self.ns_node if e.type in ["Abstract"]])
        hydraulic_node_count = len([e for e in self.ns_node if e.type in ["Hydraulic"]])
        #parameter_node_count = len([e for e in self.ns_node if e.type in ["Parameter"]])
        text.write(
        '\n/* Label Indexes\n')
        if self.frame:
            text.write('\nreference frames:\n')
            for i, frame in enumerate(self.frame):
                text.write('\t'+str(i)+'\t- '+frame.objects[0].name+'\n')
        if self.node:
            text.write('\nnodes:\n')
            for i, entity in enumerate(self.node):
                text.write('\t'+str(i)+'\t- '+entity.name+'\n')
        for clas in 'ns_node drive driver element'.split():
            if eval('self.'+clas):
                text.write('\n'+clas+'s:\n')
                for i, entity in enumerate(eval('self.'+clas)):
                    text.write('\t'+str(i)+'\t- '+entity.name+' ('+entity.type)
                    if entity.users:
                        text.write(', users='+str(entity.users))
                    text.write(')')
                    if clas == 'element' and hasattr(entity, "objects"):
                        names = [o.name for o in entity.objects if o]
                        if names:
                            string = ' objects: '
                            for name in names:
                                string += name+', '
                            string = string[:-2]+'.'
                            text.write(string)
                    names = [l.name for l in entity.links if l]
                    if names:
                        string = ' links: '
                        for name in names:
                            string += name+', '
                        string = string[:-2]+'.'
                        text.write(string)
                    text.write('\n')
        text.write('\n*/\n\n')

        text.write(
        'begin: data;\n'+
        '\tproblem: '+self.integrator+';\n'+
        'end: data;\n\n'+
        'begin: '+self.integrator+';\n'+
        '\tinitial time: '+str(self.t0)+';\n'+
        '\tfinal time: '+str(self.final_time)+';\n'+
        '\ttime step: '+str(self.dt)+';\n'+
        '\tmax iterations: '+str(self.maxI)+';\n'+
        '\ttolerance: '+str(self.tol)+';\n'+
        '\tderivatives tolerance: '+str(self.dTol)+';\n'+
        '\tderivatives coefficient: '+str(self.dC)+';\n')
        if self.mod_test:
            text.write('\tmodify residual test;\n')
        text.write('#\toutput: none;\n')
        text.write(
        'end: '+str(self.integrator)+';\n\n'+
        'begin: control data;\n'+
        '\tdefault orientation: orientation matrix;\n'+
        '\toutput precision: '+str(self.precision)+';\n'+
        '\toutput meter: meter, 0., forever, steps, '+str(max([int(1./(self.fps*self.dt)), 1]))+';\n')
        if structural_node_count:
            text.write('\tstructural nodes: '+str(structural_node_count)+';\n')
        if electric_node_count:
            text.write('\telectric nodes: '+str(electric_node_count)+';\n')
        if abstract_node_count:
            text.write('\tabstract nodes: '+str(abstract_node_count)+';\n')
        if hydraulic_node_count:
            text.write('\thydraulic nodes: '+str(hydraulic_node_count)+';\n')
        if joint_count:
            text.write('\tjoints: '+str(joint_count)+';\n')
        if force_count:
            text.write('\tforces: '+str(force_count)+';\n')
        if genel_count:
            text.write('\tgenels: '+str(genel_count)+';\n')
        if beam_count:
            text.write('\tbeams: '+str(beam_count)+';\n')
        if rigid_body_count:
            text.write('\trigid bodies: '+str(rigid_body_count)+';\n')
        if air_properties:
            text.write('\tair properties;\n')
        if gravity:
            text.write('\tgravity;\n')
        if aerodynamic_element_count:
            text.write('\taerodynamic elements: '+str(aerodynamic_element_count)+';\n')
        if rotor_count:
            text.write('\trotors: '+str(rotor_count)+';\n')
        if file_driver_count:
            text.write('\tfile drivers: '+str(file_driver_count)+';\n')
        text.write('\tdefault output: accelerations;\n')

        text.write('end: control data;\n')
        if self.frame:
            text.write('\n')
        for i, frame in enumerate(self.frame):
            parent_label = 'global'
            for ip, parent_frame in enumerate(self.frame):
                if frame.objects[0] in parent_frame.objects[1:]:
                    parent_label = str(ip)
                    break
            rot = frame.objects[0].matrix_world.to_quaternion().to_matrix()
            vectors = list()
            for link in frame.links:
                if link.subtype in "null default".split():
                    vectors.append(rot*Vector([0., 0., 0.]))
                else:
                    vectors.append(rot*Vector(link.floats) * (link.factor if link.scale else 1))
            text.write('reference: '+str(i)+',\n'+'\treference, global, ')
            self.locationVector_write(list(frame.objects[0].matrix_world.translation), text, ',\n')
            text.write('\treference, global, matr,\n')
            self.rotationMatrix_write(rot, text, '\t\t')
            text.write(',\n\treference, '+parent_label+', ')
            self.locationVector_write(vectors[0], text, ',\n')
            text.write('\treference, '+parent_label+', ')
            self.locationVector_write(vectors[1], text, ';\n')
        text.write('\nbegin: nodes;\n')

        for i, node in enumerate(self.node):
                if node in self.structural_dynamic_nodes:
                    text.write('\tstructural: '+str(i)+', dynamic,\n')
                elif node in self.structural_static_nodes:
                    text.write('\tstructural: '+str(i)+', static,\n')
                else:
                    continue
                rot = node.matrix_world.to_quaternion().to_matrix()
                if node in frame_dict:
                    frame_label = frame_dict[node]
                else:
                    frame_label = 'global'
                text.write('\t\treference, global, ')
                self.locationVector_write(list(node.matrix_world.translation), text, ',\n')
                text.write('\t\treference, global, matr,\n')
                self.rotationMatrix_write(rot, text, '\t'*3)
                text.write(',\n'+
                    '\t\treference, '+frame_label+', null,\n'+
                    '\t\treference, '+frame_label+', null;\n')

        for i, node in enumerate(self.node):
            if node in self.structural_dummy_nodes:
                base_node = dummy_dict[node]
                rot = base_node.matrix_world.to_quaternion().to_matrix()
                globalV = node.matrix_world.translation - base_node.matrix_world.translation
                localV = rot*globalV
                rotT = node.matrix_world.to_quaternion().to_matrix().transposed()
                text.write('\tstructural: '+str(i)+', dummy,\n\t\t'+
                    str(self.node.index(base_node))+', offset,\n\t\t\t')
                self.locationVector_write(localV, text, ',\n\t\t\tmatr,\n')
                self.rotationMatrix_write(rot*rotT, text, '\t\t\t\t')
                text.write(';\n')

        """
        for i, ns_node in enumerate(self.ns_node):
            if ns_node.type == 'Electric':
                text.write('\telectric: '+str(i)+', value, '+str(ns_node._args[0]))
                if ns_node._args[1]: text.write(', derivative, '+str(ns_node._args[2]))
                text.write(';\n')
            if ns_node.type == 'Abstract':
                text.write('\tabstract: '+str(i)+', value, '+str(ns_node._args[0]))
                if ns_node._args[1]: text.write(', differential, '+str(ns_node._args[2]))
                text.write(';\n')
            if ns_node.type == 'Hydraulic':
                text.write('\thydraulic: '+str(i)+', value, '+str(ns_node._args[0])+';\n')
        """
        text.write('end: nodes;\n')

        if file_driver_count:
            text.write('\nbegin: drivers;\n')
            for driver in self.Driver:
                if driver.users:
                    driver.write(text)
            text.write('end: drivers;\n')

        self.indent_drives = 1
        if drive_callers:
            text.write('\n')
        for drive in drive_callers:
            name = drive.name.replace(' ', '').replace('.', '__')
            text.write('set: integer '+name+' = '+str(self.drive.index(drive))+';\n\tdrive caller: '+name+', '+drive.string()+';\n')
        if self.function:
            text.write('\n')
        for function in self.function:
            function.written = False
        for function in self.function:
            function.write(text)

        self.indent_drives = 2
        text.write('\nbegin: elements;\n')

        try:
            for element_type in aerodynamic_types + beam_types + ["Body"] + force_types + genel_types + joint_types + ["Rotor"] + environment_types + ["Driven"]:
                for element in self.element:
                    if element.type == element_type:
                        element.write(text)
        except Exception as e:
            print(e)
            text.write(str(e) + "\n")            
        text.write('end: elements;\n')


