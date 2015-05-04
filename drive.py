if "bpy" in locals():
    import imp
    imp.reload(bpy)
    imp.reload(Operator)
    imp.reload(Entity)
else:
    from mbdyn.base import bpy, Operator, Entity

types = [
    "Array drive",
    "Constant drive",
    "Cosine drive",
    "Cubic drive",
    "Direct drive",
    "Dof drive",
    "Double ramp drive",
    "Double step drive",
    "Drive drive",
    "Element drive",
    "Exponential drive",
    "File drive",
    "Fourier series drive",
    "Frequency sweep drive",
    "Hints",
    "Linear drive",
    "Meter drive",
    "Mult drive",
    "Node drive",
    "Null drive",
    "Parabolic drive",
    "Piecewise linear drive",
    "Ramp drive",
    "Random drive",
    "Sine drive",
    "Step drive",
    "String drive",
    "Tanh drive",
    "Template drive",
    "Time drive",
    "Unit drive"]

tree = ["Add Drive", types]

class Base(Operator):
    bl_label = "Drives"
    bl_options = {'DEFAULT_CLOSED'}
    @classmethod
    def make_list(self, ListItem):
        bpy.types.Scene.drive_uilist = bpy.props.CollectionProperty(type = ListItem)
        bpy.types.Scene.drive_index = bpy.props.IntProperty(default=-1)
    @classmethod
    def delete_list(self):
        del bpy.types.Scene.drive_uilist
        del bpy.types.Scene.drive_index
    @classmethod
    def get_uilist(self, context):
        return context.scene.drive_index, context.scene.drive_uilist
    def set_index(self, context, value):
        context.scene.drive_index = value

classes = dict()

for t in types:
    class DefaultOperator(Base):
        bl_label = t
        def defaults(self, context):
            pass
        def assign(self, context):
            self.entity = self.database.drive[context.scene.drive_index]
        def store(self, context):
            self.entity = self.database.drive[context.scene.drive_index]
        def create_entity(self):
            return Entity(self.name)
    classes[t] = DefaultOperator

class UnitDrive(Entity):
    def string(self, indent=False):
        return "unit"

class UnitDriveOperator(Base):
    bl_label = "Unit drive"
    def defaults(self, context):
        pass
    def assign(self, context):
        self.entity = self.database.drive[context.scene.drive_index]
    def store(self, context):
        self.entity = self.database.drive[context.scene.drive_index]
    def create_entity(self):
        return UnitDrive(self.name)

classes[UnitDriveOperator.bl_label] = UnitDriveOperator

