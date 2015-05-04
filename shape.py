if "bpy" in locals():
    import imp
    imp.reload(bpy)
    imp.reload(Operator)
    imp.reload(Entity)
else:
    from mbdyn.base import bpy, Operator, Entity

types = [
	"Const shape",
	"Linear shape",
	"Piecewise linear shape",
	"Parabolic shape"]

tree = ["Add Shape", types]

classes = dict()

class Base(Operator):
    bl_label = "Shapes"
    bl_options = {'DEFAULT_CLOSED'}
    @classmethod
    def make_list(self, ListItem):
        bpy.types.Scene.shape_uilist = bpy.props.CollectionProperty(type = ListItem)
        bpy.types.Scene.shape_index = bpy.props.IntProperty(default=-1)
    @classmethod
    def delete_list(self):
        del bpy.types.Scene.shape_uilist
        del bpy.types.Scene.shape_index
    @classmethod
    def get_uilist(self, context):
        return context.scene.shape_index, context.scene.shape_uilist
    def set_index(self, context, value):
        context.scene.shape_index = value

for t in types:
    class Tester(Base):
        bl_label = t
        def defaults(self, context):
            pass
        def assign(self, context):
            self.entity = self.database.shape[context.scene.shape_index]
        def store(self, context):
            self.entity = self.database.shape[context.scene.shape_index]
        def create_entity(self):
            return Entity(self.name)
    classes[t] = Tester

