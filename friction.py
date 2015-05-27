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

types = ["Modlugre", "Discrete Coulomb"]

tree = ["Add Friction", types]

klasses = dict()

class Base(Operator):
    bl_label = "Frictions"
    bl_options = {'DEFAULT_CLOSED'}
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

for t in types:
    class Tester(Base):
        bl_label = t
        @classmethod
        def poll(cls, context):
            return False
        def defaults(self, context):
            pass
        def assign(self, context):
            self.entity = database.friction[context.scene.friction_index]
        def store(self, context):
            self.entity = database.friction[self.index]
        def create_entity(self):
            return Entity(self.name)
    klasses[t] = Tester

class Modlugre(Entity):
	def string(self):
		string = ("modlugre, "+str(self.sigma0)+", "+str(self.sigma1)+", "+str(self.sigma2)+", "+str(self.kappa)+",\n"+
		"\t\t\t\""+self.links[0].name+"\", ")
		if self.plane_hinge:
			string += "simple plane hinge, "+str(self.radius)
		else:
			string += "simple"
		return string

class ModlugreOperator(Base):
    bl_label = "Modlugre"
    sigma0 = bpy.props.FloatProperty(name="Sigma 0", description="", min=-9.9e10, max=9.9e10, precision=6)
    sigma1 = bpy.props.FloatProperty(name="Sigma 1", description="", min=-9.9e10, max=9.9e10, precision=6)
    sigma2 = bpy.props.FloatProperty(name="Sigma 2", description="", min=-9.9e10, max=9.9e10, precision=6)
    kappa = bpy.props.FloatProperty(name="Kappa", description="", min=-9.9e10, max=9.9e10, precision=6)
    plane_hinge = bpy.props.BoolProperty(name="Plane hinge", description="Simple plane hinge (else just simple shape function)")
    radius = bpy.props.FloatProperty(name="Radius", description="", min=0.0, max=9.9e10, precision=6)
    function_name = bpy.props.EnumProperty(items=enum_function, name="Shape Function")
    function_edit = bpy.props.BoolProperty(name="")
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.sigma0 = 1.0
        self.sigma1 = 1.0
        self.sigma2 = 1.0
        self.kappa = 1.0
        self.plane_hinge = False
        self.radius = 1.0
        self.function_exists(context)
    def assign(self, context):
        self.entity = database.friction[context.scene.friction_index]
        self.sigma0 = self.entity.sigma0
        self.sigma1 = self.entity.sigma1
        self.sigma2 = self.entity.sigma2
        self.kappa = self.entity.kappa
        self.plane_hinge = self.entity.plane_hinge
        self.radius = self.entity.radius
        self.function_name = self.entity.links[0].name
    def store(self, context):
        self.entity = database.friction[self.index]
        self.entity.sigma0 = self.sigma0
        self.entity.sigma1 = self.sigma1
        self.entity.sigma2 = self.sigma2
        self.entity.kappa = self.kappa
        self.entity.plane_hinge = self.plane_hinge
        self.entity.radius = self.radius
        self.entity.unlink_all()
        self.link_function(context, self.function_name, self.function_edit)
        self.entity.increment_links()
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
        self.draw_link(layout, "function_name", "function_edit")
    def create_entity(self):
        return Modlugre(self.name)

klasses[ModlugreOperator.bl_label] = ModlugreOperator

bundle = Bundle(tree, Base, klasses, database.friction, "friction")
