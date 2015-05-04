if "bpy" in locals():
    import imp
    imp.reload(bpy)
    imp.reload(Operator)
    imp.reload(Entity)
else:
    from mbdyn.base import bpy, Operator, Entity

types = ["File"]

tree = ["Add Driver", types]

class Base(Operator):
    bl_label = "Drivers"
    bl_options = {'DEFAULT_CLOSED'}
    @classmethod
    def make_list(self, ListItem):
        bpy.types.Scene.driver_uilist = bpy.props.CollectionProperty(type = ListItem)
        bpy.types.Scene.driver_index = bpy.props.IntProperty(default=-1)
    @classmethod
    def delete_list(self):
        del bpy.types.Scene.driver_uilist
        del bpy.types.Scene.driver_index
    @classmethod
    def get_uilist(self, context):
        return context.scene.driver_index, context.scene.driver_uilist
    def set_index(self, context, value):
        context.scene.driver_index = value

classes = dict()

for t in types:
    class Tester(Base):
        bl_label = t
        def defaults(self, context):
            pass
        def assign(self, context):
            self.entity = self.database.driver[context.scene.driver_index]
        def store(self, context):
            self.entity = self.database.driver[context.scene.driver_index]
        def create_entity(self):
            return Entity(self.name)
    classes[t] = Tester

