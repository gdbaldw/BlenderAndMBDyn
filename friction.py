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
else:
    from .base import bpy, database, Operator, Entity, Bundle, enum_function
    from .base import update_function
    from .common import FORMAT

types = ["Modlugre", "Discrete Coulomb"]

tree = ["Add Friction", types]

klasses = dict()

class Base(Operator):
    bl_label = "Frictions"
    bl_options = {'DEFAULT_CLOSED'}
    @classmethod
    def poll(cls, context):
        return True
    @classmethod
    def make_list(self, ListItem):
        bpy.types.Scene.friction_uilist = bpy.props.CollectionProperty(type = ListItem)
        bpy.types.Scene.friction_index = bpy.props.IntProperty(default=-1)
    @classmethod
    def delete_list(self):
        del bpy.types.Scene.friction_uilist
        del bpy.types.Scene.friction_index
    @classmethod
    def get_uilist(self, context):
        return context.scene.friction_index, context.scene.friction_uilist
    def set_index(self, context, value):
        context.scene.friction_index = value
    def prereqs(self, context):
        pass

for t in types:
    class Tester(Base):
        bl_label = t
        @classmethod
        def poll(cls, context):
            return False
        def create_entity(self):
            return Entity(self.name)
    klasses[t] = Tester

class Modlugre(Entity):
	def string(self):
		string = ("modlugre, " + FORMAT(self.sigma0) + ", " + FORMAT(self.sigma1) + ", " + FORMAT(self.sigma2) + ", " + FORMAT(self.kappa) + ",\n" +
		"\t\t\t\"" + self.links[0].name + "\", ")
		if self.plane_hinge:
			string += "simple plane hinge, " + FORMAT(self.radius)
		else:
			string += "simple"
		return string

class ModlugreOperator(Base):
    bl_label = "Modlugre"
    sigma0 = bpy.props.FloatProperty(name="Sigma 0", description="", min=-9.9e10, max=9.9e10, precision=6, default=0.0)
    sigma1 = bpy.props.FloatProperty(name="Sigma 1", description="", min=-9.9e10, max=9.9e10, precision=6, default=0.0)
    sigma2 = bpy.props.FloatProperty(name="Sigma 2", description="", min=-9.9e10, max=9.9e10, precision=6, default=0.0)
    kappa = bpy.props.FloatProperty(name="Kappa", description="", min=-9.9e10, max=9.9e10, precision=6, default=0.0)
    plane_hinge = bpy.props.BoolProperty(name="Plane hinge", description="Simple plane hinge (else just simple shape function)", default=False)
    radius = bpy.props.FloatProperty(name="Radius", description="", min=0.0, max=9.9e10, precision=6, default=0.0)
    function_name = bpy.props.EnumProperty(items=enum_function, name="Shape Function",
        update=lambda self, context: update_function(self, context, self.function_name))
    def assign(self, context):
        self.sigma0 = self.entity.sigma0
        self.sigma1 = self.entity.sigma1
        self.sigma2 = self.entity.sigma2
        self.kappa = self.entity.kappa
        self.plane_hinge = self.entity.plane_hinge
        self.radius = self.entity.radius
        self.function_name = self.entity.links[0].name
    def store(self, context):
        self.entity.sigma0 = self.sigma0
        self.entity.sigma1 = self.sigma1
        self.entity.sigma2 = self.sigma2
        self.entity.kappa = self.kappa
        self.entity.plane_hinge = self.plane_hinge
        self.entity.radius = self.radius
        self.entity.links.append(database.function.get_by_name(self.function_name))
    def draw(self, context):
        self.basis = self.plane_hinge
        layout = self.layout
        layout.prop(self, "sigma0")
        layout.prop(self, "sigma1")
        layout.prop(self, "sigma2")
        layout.prop(self, "kappa")
        row = layout.row()
        row.prop(self, "plane_hinge")
        if self.plane_hinge:
            row.prop(self, "radius")
        layout.prop(self, "function_name")
    def create_entity(self):
        return Modlugre(self.name)

klasses[ModlugreOperator.bl_label] = ModlugreOperator

bundle = Bundle(tree, Base, klasses, database.friction, "friction")
