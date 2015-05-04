if "bpy" in locals():
    import imp
    imp.reload(bpy)
    imp.reload(Operator)
    imp.reload(Entity)
else:
    from mbdyn.base import bpy, Operator, Entity

types = ["Modlugre", "Discrete Coulomb"]

tree = ["Add Friction", types]

classes = dict()

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
        def defaults(self, context):
            pass
        def assign(self, context):
            self.entity = self.database.friction[context.scene.friction_index]
        def store(self, context):
            self.entity = self.database.friction[context.scene.friction_index]
        def create_entity(self):
            return Entity(self.name)
    classes[t] = Tester

