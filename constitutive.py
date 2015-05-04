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

constitutive_1D = [
    "Linear elastic 1D",
    "Linear elastic generic 1D",
    "Cubic elastic generic 1D",
    "Log elastic 1D",
#    "Linear elastic bi-stop generic 1D",
    "Double linear elastic 1D",
    "Isotropic hardening elastic 1D",
    "Scalar function elastic 1D",
    "Scalar function elastic orthotropic 1D",
    "nlsf elastic 1D",
    "nlp elastic 1D",
    "Linear viscous 1D",
    "Linear viscous generic 1D",
    "nlsf viscous 1D",
    "nlp viscous 1D",
    "Linear viscoelastic 1D",
    "Linear viscoelastic generic 1D",
    "Cubic viscoelastic generic 1D",
    "Double linear viscoelastic 1D",
    "Turbulent viscoelastic 1D",
#    "Linear viscoelastic bi-stop generic 1D",
    "GRAALL damper 1D",
    "shock absorber 1D",
    "symbolic elastic 1D",
    "symbolic viscous 1D",
    "symbolic viscoelastic 1D",
    "ann elastic 1D",
    "ann viscoelastic 1D",
    "nlsf viscoelastic 1D",
    "nlp viscoelastic 1D"]

constitutive_3D = [
    "Linear elastic 3D",
    "Linear elastic generic 3D",
    "Cubic elastic generic 3D",
#    "Linear elastic bi-stop generic 3D",
    "Double linear elastic 3D",
    "Isotropic hardening elastic 3D",
    "Scalar function elastic 3D",
    "Scalar function elastic orthotropic 3D",
    "nlsf elastic 3D",
    "nlp elastic 3D",
    "Linear viscous 3D",
    "Linear viscous generic 3D",
    "nlsf viscous 3D",
    "nlp viscous 3D",
    "Linear viscoelastic 3D",
    "Linear viscoelastic generic 3D",
    "Cubic viscoelastic generic 3D",
    "Double linear viscoelastic 3D",
#    "Linear viscoelastic bi-stop generic 3D",
    "GRAALL damper 3D",
    "symbolic elastic 3D",
    "symbolic viscous 3D",
    "symbolic viscoelastic 3D",
    "ann elastic 3D",
    "ann viscoelastic 3D",
    "nlsf viscoelastic 3D",
    "nlp viscoelastic 3D",
    "invariant angular 3D"]

constitutive_6D = [
    "Linear elastic 6D",
    "Linear elastic generic 6D",
    "Linear elastic generic axial torsion coupling 6D",
#    "Linear elastic bi-stop generic 6D",
    "Isotropic hardening elastic 6D",
    "Scalar function elastic 6D",
    "Scalar function elastic orthotropic 6D",
    "nlsf elastic 6D",
    "nlp elastic 6D",
    "Linear viscous 6D",
    "Linear viscous generic 6D",
    "nlsf viscous 6D",
    "nlp viscous 6D",
    "Linear viscoelastic 6D",
    "Linear viscoelastic generic 6D",
    "Linear viscoelastic generic axial torsion coupling 6D",
#    "Linear viscoelastic bi-stop generic 6D",
    "GRAALL damper 6D",
    "symbolic elastic 6D",
    "symbolic viscous 6D",
    "symbolic viscoelastic 6D",
    "ann elastic 6D",
    "ann viscoelastic 6D",
    "nlsf viscoelastic 6D",
    "nlp viscoelastic 6D"]

types = constitutive_1D + constitutive_3D + constitutive_6D

tree = ["Add Constitutive",
    ["1D", constitutive_1D,
    ],["3D", constitutive_3D,
    ],["6D", constitutive_6D,
    ]]

classes = dict()

class Base(Operator):
    bl_label = "Constitutives"
    bl_options = {'DEFAULT_CLOSED'}
    @classmethod
    def make_list(self, ListItem):
        bpy.types.Scene.constitutive_uilist = bpy.props.CollectionProperty(type = ListItem)
        bpy.types.Scene.constitutive_index = bpy.props.IntProperty(default=-1)
    @classmethod
    def delete_list(self):
        del bpy.types.Scene.constitutive_uilist
        del bpy.types.Scene.constitutive_index
    @classmethod
    def get_uilist(self, context):
        return context.scene.constitutive_index, context.scene.constitutive_uilist
    def set_index(self, context, value):
        context.scene.constitutive_index = value

for t in types:
    class Tester(Base):
        bl_label = t
        @classmethod
        def poll(cls, context):
            return False
        def defaults(self, context):
            pass
        def assign(self, context):
            self.entity = self.database.constitutive[context.scene.constitutive_index]
        def store(self, context):
            self.entity = self.database.constitutive[context.scene.constitutive_index]
        def create_entity(self):
            return Entity(self.name)
    classes[t] = Tester

