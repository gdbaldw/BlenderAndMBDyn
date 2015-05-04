if "bpy" in locals():
    import imp
    imp.reload(bpy)
    imp.reload(Operator)
    imp.reload(Entity)
else:
    from mbdyn.base import bpy, Operator, Entity

types = [
	"Const",
	"Exp",
	"Log",
	"Pow",
	"Linear",
	"Cubic Natural Spline",
	"Multilinear",
	"Chebychev",
	"Sum",
	"Sub",
	"Mul",
	"Div"]

tree = ["Add Function", types]

classes = dict()

class Base(Operator):
    bl_label = "Functions"
    bl_options = {'DEFAULT_CLOSED'}
    @classmethod
    def make_list(self, ListItem):
        bpy.types.Scene.function_uilist = bpy.props.CollectionProperty(type = ListItem)
        bpy.types.Scene.function_index = bpy.props.IntProperty(default=-1)
    @classmethod
    def delete_list(self):
        del bpy.types.Scene.function_uilist
        del bpy.types.Scene.function_index
    @classmethod
    def get_uilist(self, context):
        return context.scene.function_index, context.scene.function_uilist
    def set_index(self, context, value):
        context.scene.function_index = value

for t in types:
    class Tester(Base):
        bl_label = t
        def defaults(self, context):
            pass
        def assign(self, context):
            self.entity = self.database.function[context.scene.function_index]
        def store(self, context):
            self.entity = self.database.function[context.scene.function_index]
        def create_entity(self):
            return Entity(self.name)
    classes[t] = Tester

