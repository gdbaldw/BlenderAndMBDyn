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
    from .base import bpy, root_dot, database, Operator, Entity, Bundle, BPY, enum_drive, enum_element, SelectedObjects

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

klasses = dict()

for t in types:
    class DefaultOperator(Base):
        bl_label = t
        @classmethod
        def poll(cls, context):
            return False
        def defaults(self, context):
            pass
        def assign(self, context):
            self.entity = database.drive[context.scene.drive_index]
        def store(self, context):
            self.entity = database.drive[self.index]
        def create_entity(self):
            return Entity(self.name)
    klasses[t] = DefaultOperator

class NullDrive(Entity):
    def string(self, indent=False):
        ret = super().indent_drives*"\t" if indent else ""
        ret += "null"
        return ret

class DriveOperator(Base):
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        pass
    def assign(self, context):
        self.entity = database.drive[context.scene.drive_index]
    def store(self, context):
        self.entity = database.drive[self.index]

class NullDriveOperator(DriveOperator):
    bl_label = "Null drive"
    def create_entity(self):
        return NullDrive(self.name)

klasses[NullDriveOperator.bl_label] = NullDriveOperator

class DirectDrive(Entity):
    def string(self, indent=False):
        ret = super().indent_drives*"\t" if indent else ""
        ret += "direct"
        return ret

class DirectDriveOperator(DriveOperator):
    bl_label = "Direct drive"
    def create_entity(self):
        return DirectDrive(self.name)

klasses[DirectDriveOperator.bl_label] = DirectDriveOperator

class UnitDrive(Entity):
    def string(self, indent=False):
        ret = super().indent_drives*"\t" if indent else ""
        ret += "unit"
        return ret

class UnitDriveOperator(DriveOperator):
    bl_label = "Unit drive"
    def create_entity(self):
        return UnitDrive(self.name)

klasses[UnitDriveOperator.bl_label] = UnitDriveOperator

class ConstantDrive(Entity):
    def string(self, indent=False):
        ret = super().indent_drives*"\t" if indent else ""
        ret += str(round(self.constant, 5))
        return ret

class ConstantDriveOperator(Base):
    bl_label = "Constant drive"
    constant = bpy.props.FloatProperty(name="Constant", description="", min=-9.9e10, max=9.9e10, precision=6)
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.constant = 0.0
    def assign(self, context):
        self.entity = database.drive[context.scene.drive_index]
        self.constant = self.entity.constant
    def store(self, context):
        self.entity = database.drive[self.index]
        self.entity.constant = self.constant
    def create_entity(self):
        return ConstantDrive(self.name)

klasses[ConstantDriveOperator.bl_label] = ConstantDriveOperator

class TimeDrive(Entity):
    def string(self, indent=False):
        ret = super().indent_drives*"\t" if indent else ""
        ret += "time"
        return ret

class TimeDriveOperator(DriveOperator):
    bl_label = "Time drive"
    def create_entity(self):
        return TimeDrive(self.name)

klasses[TimeDriveOperator.bl_label] = TimeDriveOperator

class LinearDrive(Entity):
    def string(self, indent=False):
        ret = super().indent_drives*"\t" if indent else ""
        ret += "cubic"
        for v in [self.constant, self.linear]:
            ret += ", " + str(v)
        return ret

class LinearDriveOperator(Base):
    bl_label = "Linear drive"
    constant = bpy.props.FloatProperty(name="Constant", description="", min=-9.9e10, max=9.9e10, precision=6)
    linear = bpy.props.FloatProperty(name="Linear", description="", min=-9.9e10, max=9.9e10, precision=6)
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.constant = 0.0
        self.linear = 0.0
    def assign(self, context):
        self.entity = database.drive[context.scene.drive_index]
        self.constant = self.entity.constant
        self.linear = self.entity.linear
    def store(self, context):
        self.entity = database.drive[self.index]
        self.entity.constant = self.constant
        self.entity.linear = self.linear
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "constant")
        layout.prop(self, "linear")
    def create_entity(self):
        return LinearDrive(self.name)

klasses[LinearDriveOperator.bl_label] = LinearDriveOperator

class ParabolicDrive(Entity):
    def string(self, indent=False):
        ret = super().indent_drives*"\t" if indent else ""
        ret += "parabolic"
        for v in [self.constant, self.linear, self.parabolic]:
            ret += ", " + str(v)
        return ret

class ParabolicDriveOperator(Base):
    bl_label = "Parabolic drive"
    constant = bpy.props.FloatProperty(name="Constant", description="", min=-9.9e10, max=9.9e10, precision=6)
    linear = bpy.props.FloatProperty(name="Linear", description="", min=-9.9e10, max=9.9e10, precision=6)
    parabolic = bpy.props.FloatProperty(name="Parabolic", description="", min=-9.9e10, max=9.9e10, precision=6)
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.constant = 0.0
        self.linear = 0.0
        self.parabolic = 0.0
    def assign(self, context):
        self.entity = database.drive[context.scene.drive_index]
        self.constant = self.entity.constant
        self.linear = self.entity.linear
        self.parabolic = self.entity.parabolic
    def store(self, context):
        self.entity = database.drive[self.index]
        self.entity.constant = self.constant
        self.entity.linear = self.linear
        self.entity.parabolic = self.parabolic
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "constant")
        layout.prop(self, "linear")
        layout.prop(self, "parabolic")
    def create_entity(self):
        return ParabolicDrive(self.name)

klasses[ParabolicDriveOperator.bl_label] = ParabolicDriveOperator

class CubicDrive(Entity):
    def string(self, indent=False):
        ret = super().indent_drives*"\t" if indent else ""
        ret += "cubic"
        for v in [self.constant, self.linear, self.parabolic, self.cubic]:
            ret += ", " + str(v)
        return ret

class CubicDriveOperator(Base):
    bl_label = "Cubic drive"
    constant = bpy.props.FloatProperty(name="Constant", description="", min=-9.9e10, max=9.9e10, precision=6)
    linear = bpy.props.FloatProperty(name="Linear", description="", min=-9.9e10, max=9.9e10, precision=6)
    parabolic = bpy.props.FloatProperty(name="Parabolic", description="", min=-9.9e10, max=9.9e10, precision=6)
    cubic = bpy.props.FloatProperty(name="Cubic", description="", min=-9.9e10, max=9.9e10, precision=6)
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.constant = 0.0
        self.linear = 0.0
        self.parabolic = 0.0
        self.cubic = 0.0
    def assign(self, context):
        self.entity = database.drive[context.scene.drive_index]
        self.constant = self.entity.constant
        self.linear = self.entity.linear
        self.parabolic = self.entity.parabolic
        self.cubic = self.entity.cubic
    def store(self, context):
        self.entity = database.drive[self.index]
        self.entity.constant = self.constant
        self.entity.linear = self.linear
        self.entity.parabolic = self.parabolic
        self.entity.cubic = self.cubic
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "constant")
        layout.prop(self, "linear")
        layout.prop(self, "parabolic")
        layout.prop(self, "cubic")
    def create_entity(self):
        return CubicDrive(self.name)

klasses[CubicDriveOperator.bl_label] = CubicDriveOperator

class StepDrive(Entity):
    def string(self, indent=False):
        ret = super().indent_drives*"\t" if indent else ""
        ret += "step"
        for v in [self.initial_time, self.step_value, self.initial_value]:
            ret += ", " + str(v)
        return ret

class StepDriveOperator(Base):
    bl_label = "Step drive"
    initial_time = bpy.props.FloatProperty(name="Initial time", description="", min=0.0, max=9.9e10, precision=6)
    step_value = bpy.props.FloatProperty(name="Step value", description="", min=-9.9e10, max=9.9e10, precision=6)
    initial_value = bpy.props.FloatProperty(name="Initial value", description="", min=-9.9e10, max=9.9e10, precision=6)
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.initial_time = 0.0
        self.step_value = 0.0
        self.initial_value = 0.0
    def assign(self, context):
        self.entity = database.drive[context.scene.drive_index]
        self.initial_time = self.entity.initial_time
        self.step_value = self.entity.step_value
        self.initial_value = self.entity.initial_value
    def store(self, context):
        self.entity = database.drive[self.index]
        self.entity.initial_time = self.initial_time
        self.entity.step_value = self.step_value
        self.entity.initial_value = self.initial_value
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "initial_time")
        layout.prop(self, "step_value")
        layout.prop(self, "initial_value")
    def create_entity(self):
        return StepDrive(self.name)

klasses[StepDriveOperator.bl_label] = StepDriveOperator

class DoubleStepDrive(Entity):
    def string(self, indent=False):
        ret = super().indent_drives*"\t" if indent else ""
        ret += "double step"
        for v in [self.initial_time, self.final_time, self.step_value, self.initial_value]:
            ret += ", " + str(v)
        return ret

class DoubleStepDriveOperator(Base):
    bl_label = "Double step drive"
    initial_time = bpy.props.FloatProperty(name="Initial time", description="", min=0.0, max=9.9e10, precision=6)
    final_time = bpy.props.FloatProperty(name="Final time", description="", min=0.0, max=9.9e10, precision=6)
    step_value = bpy.props.FloatProperty(name="Step value", description="", min=-9.9e10, max=9.9e10, precision=6)
    initial_value = bpy.props.FloatProperty(name="Initial value", description="", min=-9.9e10, max=9.9e10, precision=6)
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.initial_time = 0.0
        self.final_time = 0.0
        self.step_value = 0.0
        self.initial_value = 0.0
    def assign(self, context):
        self.entity = database.drive[context.scene.drive_index]
        self.initial_time = self.entity.initial_time
        self.final_time = self.entity.final_time
        self.step_value = self.entity.step_value
        self.initial_value = self.entity.initial_value
    def store(self, context):
        self.entity = database.drive[self.index]
        self.entity.initial_time = self.initial_time
        self.entity.final_time = self.final_time
        self.entity.step_value = self.step_value
        self.entity.initial_value = self.initial_value
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "initial_time")
        layout.prop(self, "final_time")
        layout.prop(self, "step_value")
        layout.prop(self, "initial_value")
    def create_entity(self):
        return DoubleStepDrive(self.name)

klasses[DoubleStepDriveOperator.bl_label] = DoubleStepDriveOperator

class RampDrive(Entity):
    def string(self, indent=False):
        ret = super().indent_drives*"\t" if indent else ""
        ret += "ramp"
        for v in [self.slope, self.initial_time]:
            ret += ", " + str(v)
        if self.forever:
            ret += ", forever"
        else:
            ret += ", "+str(self.final_time)
        ret += ", "+str(self.initial_value)
        return ret

class RampDriveOperator(Base):
    bl_label = "Ramp drive"
    slope = bpy.props.FloatProperty(name="Slope", description="", min=-9.9e10, max=9.9e10, precision=6)
    initial_time = bpy.props.FloatProperty(name="Initial time", description="", min=0.0, max=9.9e10, precision=6)
    forever = bpy.props.BoolProperty(name="Forever", description="")
    final_time = bpy.props.FloatProperty(name="Final time", description="", min=0.0, max=9.9e10, precision=6)
    initial_value = bpy.props.FloatProperty(name="Initial value", description="", min=-9.9e10, max=9.9e10, precision=6)
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.slope = 0.0
        self.initial_time = 0.0
        self.forever = False
        self.final_time = 0.0
        self.initial_value = 0.0
    def assign(self, context):
        self.entity = database.drive[context.scene.drive_index]
        self.slope = self.entity.slope
        self.initial_time = self.entity.initial_time
        self.forever = self.entity.forever
        self.final_time = self.entity.final_time
        self.initial_value = self.entity.initial_value
    def store(self, context):
        self.entity = database.drive[self.index]
        self.entity.slope = self.slope
        self.entity.initial_time = self.initial_time
        self.entity.forever = self.forever
        self.entity.final_time = self.final_time
        self.entity.initial_value = self.initial_value
    def draw(self, context):
        self.basis = self.forever
        layout = self.layout
        layout.prop(self, "slope")
        layout.prop(self, "initial_time")
        layout.prop(self, "forever")
        if not self.forever:
            layout.prop(self, "final_time")
        layout.prop(self, "initial_value")
    def check(self, context):
        return self.basis != self.forever
    def create_entity(self):
        return RampDrive(self.name)

klasses[RampDriveOperator.bl_label] = RampDriveOperator

class PiecewiseLinearDrive(Entity):
    def string(self, indent=False):
        ret = super().indent_drives*"\t" if indent else ""
        ret += "piecewise linear, "+str(self.N)
        for i in range(self.N):
            ret += ",\n"+super().indent_drives*"\t" + str(self.T[i]) + ", " + str(self.X[i])
        return ret

class PiecewiseLinearDriveOperator(Base):
    bl_label = "Piecewise linear drive"
    N = bpy.props.IntProperty(name="Number of points", min=2, max=50, description="")
    T = bpy.props.CollectionProperty(name="Times", type = BPY.Floats)
    X = bpy.props.CollectionProperty(name="Values", type = BPY.Floats)
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.N = 2
        self.T.clear()
        self.X.clear()
        for i in range(50):
            self.T.add()
            self.X.add()
    def assign(self, context):
        self.entity = database.drive[context.scene.drive_index]
        self.N = self.entity.N
        self.T.clear()
        self.X.clear()
        for i in range(50):
            self.T.add()
            self.X.add()
        for i, value in enumerate(self.entity.T):
            self.T[i].value = value
        for i, value in enumerate(self.entity.X):
            self.X[i].value = value
    def store(self, context):
        self.entity = database.drive[self.index]
        self.entity.N = self.N
        self.entity.T = [t.value for t in self.T]
        self.entity.X = [x.value for x in self.X]
    def draw(self, context):
        self.basis = self.N
        layout = self.layout
        layout.prop(self, "N")
        row = layout.row()
        row.label("Time")
        row.label("Value")
        for i in range(self.N):
            row = layout.row()
            row.prop(self.T[i], "value", text="")
            row.prop(self.X[i], "value", text="")
    def check(self, context):
        return self.basis != self.N
    def create_entity(self):
        return PiecewiseLinearDrive(self.name)

klasses[PiecewiseLinearDriveOperator.bl_label] = PiecewiseLinearDriveOperator

class SineDrive(Entity):
    def string(self, indent=False):
        ret = super().indent_drives*"\t" if indent else ""
        ret += "sine"
        for v in [self.initial_time, self.omega, self.amplitude]:
            ret += ", " + str(v)
        if self.duration == "cycles":
            ret += ", " + str(self.cycles)
        else:
            ret += ", " + self.duration
        ret += ", "+str(self.initial_value)
        return ret

class PeriodicDriveOperator(Base):
    initial_time = bpy.props.FloatProperty(name="Initial time", description="", min=0.0, max=9.9e10, precision=6)
    omega = bpy.props.FloatProperty(name="Omega", description="", min=-9.9e10, max=9.9e10, precision=6)
    amplitude = bpy.props.FloatProperty(name="Amplitude", description="", min=-9.9e10, max=9.9e10, precision=6)
    cycles = bpy.props.IntProperty(name="Cycles", description="Number of full cycles")
    initial_value = bpy.props.FloatProperty(name="Initial value", description="", min=-9.9e10, max=9.9e10, precision=6)
    duration = bpy.props.EnumProperty(items=[("cycles", "N-cycles", ""), ("half", "Half cycle", ""), ("one", "Full cycle", ""), ("forever", "Infinite cycle", "")])
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.initial_time = 0.0
        self.omega = 0.0
        self.amplitude = 0.0
        self.cycles = 1
        self.initial_value = 0.0
        self.duration = "cycles"
    def assign(self, context):
        self.entity = database.drive[context.scene.drive_index]
        self.initial_time = self.entity.initial_time
        self.omega = self.entity.omega
        self.amplitude = self.entity.amplitude
        self.cycles = self.entity.cycles
        self.initial_value = self.entity.initial_value
        self.duration = self.entity.duration
    def store(self, context):
        self.entity = database.drive[self.index]
        self.entity.initial_time = self.initial_time
        self.entity.omega = self.omega
        self.entity.amplitude = self.amplitude
        self.entity.cycles = self.cycles
        self.entity.initial_value = self.initial_value
        self.entity.duration = self.duration
    def draw(self, context):
        self.basis = self.duration
        layout = self.layout
        layout.prop(self, "initial_time")
        layout.prop(self, "omega")
        layout.prop(self, "amplitude")
        layout.prop(self, "duration")
        if self.duration == "cycles":
            layout.prop(self, "cycles")
        layout.prop(self, "initial_value")
    def check(self, context):
        return self.basis != self.duration
    def create_entity(self):
        return SineDrive(self.name)

class SineDriveOperator(PeriodicDriveOperator):
    bl_label = "Sine drive"
    def create_entity(self):
        return SineDrive(self.name)

klasses[SineDriveOperator.bl_label] = SineDriveOperator

class CosineDrive(Entity):
    def string(self, indent=False):
        ret = super().indent_drives*"\t" if indent else ""
        ret += "cosine"
        for v in [self.initial_time, self.omega, self.amplitude]:
            ret += ", " + str(v)
        if self.duration == "cycles":
            ret += ", " + str(self.cycles)
        else:
            ret += ", " + self.duration
        ret += ", "+str(self.initial_value)
        return ret

class CosineDriveOperator(PeriodicDriveOperator):
    bl_label = "Cosine drive"
    def create_entity(self):
        return CosineDrive(self.name)

klasses[CosineDriveOperator.bl_label] = CosineDriveOperator

class TanhDrive(Entity):
    def string(self, indent=False):
        ret = super().indent_drives*"\t" if indent else ""
        ret += "tanh"
        for v in [self.initial_time, self.amplitude, self.slope, self.initial_value]:
            ret += ", " + str(v)
        return ret

class TanhDriveOperator(Base):
    bl_label = "Tanh drive"
    initial_time = bpy.props.FloatProperty(name="Initial time", description="", min=0.0, max=9.9e10, precision=6)
    amplitude = bpy.props.FloatProperty(name="Amplitude", description="", min=-9.9e10, max=9.9e10, precision=6)
    slope = bpy.props.FloatProperty(name="Slope", description="", min=-9.9e10, max=9.9e10, precision=6)
    initial_value = bpy.props.FloatProperty(name="Initial value", description="", min=-9.9e10, max=9.9e10, precision=6)
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.initial_time = 0.0
        self.amplitude = 0.0
        self.slope = 0.0
        self.initial_value = 0.0
    def assign(self, context):
        self.entity = database.drive[context.scene.drive_index]
        self.initial_time = self.entity.initial_time
        self.amplitude = self.entity.amplitude
        self.slope = self.entity.slope
        self.initial_value = self.entity.initial_value
    def store(self, context):
        self.entity = database.drive[self.index]
        self.entity.initial_time = self.initial_time
        self.entity.amplitude = self.amplitude
        self.entity.slope = self.slope
        self.entity.initial_value = self.initial_value
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "initial_time")
        layout.prop(self, "amplitude")
        layout.prop(self, "slope")
        layout.prop(self, "initial_value")
    def create_entity(self):
        return TanhDrive(self.name)

klasses[TanhDriveOperator.bl_label] = TanhDriveOperator

class FourierSeriesDrive(Entity):
    def string(self, indent=False):
        ret = super().indent_drives*"\t" if indent else ""
        ret += "fourier series"
        indenture = super().indent_drives*"\t"
        for v in [self.initial_time, self.omega, self.N]:
            ret += ", " + str(v)
        ret += ",\n" + indenture + str(self.A[0])
        for i in range(1, self.N):
            ret += ",\n" + indenture + str(self.A[i]) + ", " + str(self.B[i])
        if self.duration == "cycles":
            ret += ",\n" + indenture + str(self.cycles)
        else:
            ret += ",\n" + indenture + self.duration
        ret += ", " + str(self.initial_value)
        return ret

class FourierSeriesDriveOperator(Base):
    bl_label = "Fourier series drive"
    initial_time = bpy.props.FloatProperty(name="Initial time", description="", min=0.0, max=9.9e10, precision=6)
    omega = bpy.props.FloatProperty(name="Omega", description="", min=-9.9e10, max=9.9e10, precision=6)
    N = bpy.props.IntProperty(name="Number of terms", min=1, max=50, description="")
    cycles = bpy.props.IntProperty(name="Cycles", description="Number of full cycles")
    duration = bpy.props.EnumProperty(items=[("cycles", "N-cycles", ""), ("one", "Full cycle", ""), ("forever", "Infinite cycle", "")])
    initial_value = bpy.props.FloatProperty(name="Initial value", description="", min=-9.9e10, max=9.9e10, precision=6)
    A = bpy.props.CollectionProperty(name="A values", type = BPY.Floats)
    B = bpy.props.CollectionProperty(name="B values", type = BPY.Floats)
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.initial_time = 0.0
        self.omega = 0.0
        self.N = 1
        self.cycles = 1
        self.duration = "cycles"
        self.initial_value = 0.0
        self.A.clear()
        self.B.clear()
        for i in range(50):
            self.A.add()
            self.B.add()
    def assign(self, context):
        self.entity = database.drive[context.scene.drive_index]
        self.initial_time = self.entity.initial_time
        self.omega = self.entity.omega
        self.N = self.entity.N
        self.cycles = self.entity.cycles
        self.duration = self.entity.duration
        self.initial_value = self.entity.initial_value
        self.A.clear()
        self.B.clear()
        for i in range(50):
            self.A.add()
            self.B.add()
        for i, value in enumerate(self.entity.A):
            self.A[i].value = value
        for i, value in enumerate(self.entity.B):
            self.B[i].value = value
    def store(self, context):
        self.entity = database.drive[self.index]
        self.entity.initial_time = self.initial_time
        self.entity.omega = self.omega
        self.entity.N = self.N
        self.entity.cycles = self.cycles
        self.entity.duration = self.duration
        self.entity.initial_value = self.initial_value
        self.entity.A = [a.value for a in self.A]
        self.entity.B = [b.value for b in self.B]
    def draw(self, context):
        self.basis = (self.duration, self.N)
        layout = self.layout
        layout.prop(self, "initial_time")
        layout.prop(self, "omega")
        layout.prop(self, "duration")
        if self.duration == "cycles":
            layout.prop(self, "cycles")
        layout.prop(self, "initial_value")
        layout.prop(self, "N")
        row = layout.row()
        row.label("A:")
        row.label("B:")
        row = layout.row()
        row.prop(self.A[0], "value", text="")
        row.label("")
        for i in range(1, self.N):
            row = layout.row()
            row.prop(self.A[i], "value", text="")
            row.prop(self.B[i], "value", text="")
    def check(self, context):
        return self.basis != (self.duration, self.N)
    def create_entity(self):
        return FourierSeriesDrive(self.name)

klasses[FourierSeriesDriveOperator.bl_label] = FourierSeriesDriveOperator

class FrequencySweepDrive(Entity):
    def string(self, indent=False):
        ret = super().indent_drives*"\t" if indent else ""
        ret += "frequency sweep, " + str(self.initial_time)
        indenture = super().indent_drives*"\t"
        ret += ",\n" + self.links[0].string(True)
        ret += ",\n" + self.links[1].string(True)
        ret += ",\n" + indenture + str(self.initial_value)
        if self.forever:
            ret += ", forever"
        else:
            ret += ", " + str(self.final_time)
        ret += ", " + str(self.final_value)
        return ret

class FrequencySweepDriveOperator(Base):
    bl_label = "Frequency sweep drive"
    initial_time = bpy.props.FloatProperty(name="Initial time", description="", min=0.0, max=9.9e10, precision=6)
    angular_velocity_drive_name = bpy.props.EnumProperty(items=enum_drive, name="Angular velocity drive")
    angular_velocity_edit = bpy.props.BoolProperty(name="")
    amplitude_drive_name = bpy.props.EnumProperty(items=enum_drive, name="Amplitude drive")
    amplitude_drive_edit = bpy.props.BoolProperty(name="")
    initial_value = bpy.props.FloatProperty(name="Initial value", description="", min=-9.9e10, max=9.9e10, precision=6)
    forever = bpy.props.BoolProperty(name="Forever", description="")
    final_time = bpy.props.FloatProperty(name="Final time", description="", min=0.0, max=9.9e10, precision=6)
    final_value = bpy.props.FloatProperty(name="Final value", description="", min=-9.9e10, max=9.9e10, precision=6)
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.drive_exists(context)
        self.initial_time = 0.0
        self.initial_value = 0.0
        self.forever = False
        self.final_time = 0.0
        self.final_value = 0.0
    def assign(self, context):
        self.entity = database.drive[context.scene.drive_index]
        self.angular_velocity_drive_name = self.entity.links[0].name
        self.amplitude_drive_name = self.entity.links[0].name
        self.initial_time = self.entity.initial_time
        self.initial_value = self.entity.initial_value
        self.forever = self.entity.forever
        self.final_time = self.entity.final_time
        self.final_value = self.entity.final_value
    def store(self, context):
        self.entity = database.drive[self.index]
        self.entity.initial_time = self.initial_time
        self.entity.initial_value = self.initial_value
        self.entity.forever = self.forever
        self.entity.final_time = self.final_time
        self.entity.final_value = self.final_value
        self.entity.unlink_all()
        self.link_drive(context, self.angular_velocity_drive_name, self.angular_velocity_drive_edit)
        self.link_drive(context, self.amplitude_drive_name, self.amplitude_drive_edit)
        self.entity.increment_links()
    def draw(self, context):
        self.basis = self.forever
        layout = self.layout
        layout.prop(self, "initial_time")
        layout.prop(self, "initial_value")
        self.draw_link(layout, "angular_velocity_drive_name", "angular_velocity_drive_edit")
        self.draw_link(layout, "amplitude_drive_name", "amplitude_drive_edit")
        layout.prop(self, "forever")
        if not self.forever:
            layout.prop(self, "final_time")
            layout.prop(self, "final_value")
    def check(self, context):
        return self.basis != self.forever
    def create_entity(self):
        return FrequencySweepDrive(self.name)

klasses[FrequencySweepDriveOperator.bl_label] = FrequencySweepDriveOperator

class ExponentialDrive(Entity):
    def string(self, indent=False):
        ret = super().indent_drives*"\t" if indent else ""
        ret += "exponential"
        for v in [self.amplitude, self.time_constant, self.initial_time, self.initial_value]:
            ret += ", " + str(v)
        return ret

class ExponentialDriveOperator(Base):
    bl_label = "Exponential drive"
    amplitude = bpy.props.FloatProperty(name="Amplitude", description="", min=-9.9e10, max=9.9e10, precision=6)
    time_constant = bpy.props.FloatProperty(name="Time constant", description="", min=-9.9e10, max=9.9e10, precision=6)
    initial_time = bpy.props.FloatProperty(name="Initial time", description="", min=-9.9e10, max=9.9e10, precision=6)
    initial_value = bpy.props.FloatProperty(name="Initial value", description="", min=-9.9e10, max=9.9e10, precision=6)
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.amplitude = 0.0
        self.time_constant = 0.0
        self.initial_time = 0.0
        self.initial_value = 0.0
    def assign(self, context):
        self.entity = database.drive[context.scene.drive_index]
        self.amplitude = self.entity.amplitude
        self.time_constant = self.entity.time_constant
        self.initial_time = self.entity.initial_time
        self.initial_value = self.entity.initial_value
    def store(self, context):
        self.entity = database.drive[self.index]
        self.entity.amplitude = self.amplitude
        self.entity.time_constant = self.time_constant
        self.entity.initial_time = self.initial_time
        self.entity.initial_value = self.initial_value
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "amplitude")
        layout.prop(self, "time_constant")
        layout.prop(self, "initial_time")
        layout.prop(self, "initial_value")
    def create_entity(self):
        return ExponentialDrive(self.name)

klasses[ExponentialDriveOperator.bl_label] = ExponentialDriveOperator

class RandomDrive(Entity):
    def string(self, indent=False):
        ret = super().indent_drives*"\t" if indent else ""
        ret += "random"
        for v in [self.amplitude, self.mean, self.initial_time]:
            ret += ", " + str(v)
        if self.forever:
            ret += ", forever"
        else:
            ret += ", " + str(self.final_time)
        ret += ", steps, " + str(self.steps)
        if self.seed_type == "time_seed":
            ret += ", seed, time"
        else:
            ret += ", seed, " + str(self.specified_seed)
        return ret

class RandomDriveOperator(Base):
    bl_label = "Random drive"
    amplitude = bpy.props.FloatProperty(name="Amplitude", description="", min=-9.9e10, max=9.9e10, precision=6)
    mean = bpy.props.FloatProperty(name="Mean", description="", min=-9.9e10, max=9.9e10, precision=6)
    initial_time = bpy.props.FloatProperty(name="Initial time", description="", min=0.0, max=9.9e10, precision=6)
    forever = bpy.props.BoolProperty(name="Forever", description="")
    final_time = bpy.props.FloatProperty(name="Final time", description="", min=0.0, max=9.9e10, precision=6)
    steps = bpy.props.FloatProperty(name="Steps", description="", min=-9.9e10, max=9.9e10, precision=6)
    seed_type = bpy.props.EnumProperty(items=[("time_seed", "Time seed", ""), ("specified_seed", "Specified seed", "")], name="Seed type")
    specified_seed = bpy.props.FloatProperty(name="Specified seed", description="", min=0.0, max=9.9e10, precision=6)
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.amplitude = 0.0
        self.mean = 0.0
        self.initial_time = 0.0
        self.forever = False
        self.final_time = 0.0
        self.steps = 0.0
        self.seed_type = "specified_seed"
        self.specified_seed = 0.0
    def assign(self, context):
        self.entity = database.drive[context.scene.drive_index]
        self.amplitude = self.entity.amplitude
        self.mean = self.entity.mean
        self.initial_time = self.entity.initial_time
        self.forever = self.entity.forever
        self.final_time = self.entity.final_time
        self.steps = self.entity.steps
        self.seed_type = self.entity.seed_type
        self.specified_seed = self.entity.specified_seed
    def store(self, context):
        self.entity = database.drive[self.index]
        self.entity.amplitude = self.amplitude
        self.entity.mean = self.mean
        self.entity.initial_time = self.initial_time
        self.entity.forever = self.forever
        self.entity.final_time = self.final_time
        self.entity.steps = self.steps
        self.entity.seed_type = self.seed_type
        self.entity.specified_seed = self.specified_seed
    def draw(self, context):
        self.basis = (self.forever, self.seed_type)
        layout = self.layout
        layout.prop(self, "amplitude")
        layout.prop(self, "mean")
        layout.prop(self, "initial_time")
        layout.prop(self, "forever")
        if not self.forever:
            layout.prop(self, "final_time")
        layout.prop(self, "steps")
        layout.prop(self, "seed_type")
        if self.seed_type == "specified_seed":
            layout.prop(self, "specified_seed")
    def check(self, context):
        return self.basis != (self.forever, self.seed_type)
    def create_entity(self):
        return RandomDrive(self.name)

klasses[RandomDriveOperator.bl_label] = RandomDriveOperator

class MeterDrive(Entity):
    def string(self, indent=False):
        ret = super().indent_drives*"\t" if indent else ""
        ret += "meter, " + str(self.initial_time)
        if self.forever:
            ret += ", forever"
        else:
            ret += ", " + str(self.final_time)
        ret += ", steps, " + str(self.steps)
        return ret

class MeterDriveOperator(Base):
    bl_label = "Meter drive"
    initial_time = bpy.props.FloatProperty(name="Initial time", description="", min=0.0, max=9.9e10, precision=6)
    forever = bpy.props.BoolProperty(name="Forever", description="", default=True)
    final_time = bpy.props.FloatProperty(name="Final time", description="", min=0.0, max=9.9e10, precision=6)
    steps = bpy.props.IntProperty(name="Steps", description="", min=1, default=1)
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        pass
    def assign(self, context):
        self.entity = database.drive[context.scene.drive_index]
        self.initial_time = self.entity.initial_time
        self.forever = self.entity.forever
        self.final_time = self.entity.final_time
        self.steps = self.entity.steps
    def store(self, context):
        self.entity = database.drive[self.index]
        self.entity.initial_time = self.initial_time
        self.entity.forever = self.forever
        self.entity.final_time = self.final_time
        self.entity.steps = self.steps
    def draw(self, context):
        self.basis = self.forever
        layout = self.layout
        layout.prop(self, "initial_time")
        layout.prop(self, "forever")
        if not self.forever:
            layout.prop(self, "final_time")
        layout.prop(self, "steps")
    def check(self, context):
        return self.basis != self.forever
    def create_entity(self):
        return MeterDrive(self.name)

klasses[MeterDriveOperator.bl_label] = MeterDriveOperator

class StringDrive(Entity):
    def string(self, indent=False):
        ret = super().indent_drives*"\t" if indent else ""
        ret += "string, \"" + self.expression_string + "\""
        return ret

class StringDriveOperator(Base):
    bl_label = "String drive"
    expression_string = bpy.props.StringProperty(name="Expression string", maxlen=100)
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.expression_string = ""
    def assign(self, context):
        self.entity = database.drive[context.scene.drive_index]
        self.expression_string = self.entity.expression_string
    def store(self, context):
        self.entity = database.drive[self.index]
        self.entity.expression_string = self.expression_string
    def create_entity(self):
        return StringDrive(self.name)

klasses[StringDriveOperator.bl_label] = StringDriveOperator

class MultDrive(Entity):
    def string(self, indent=False):
        ret = super().indent_drives*"\t" if indent else ""
        ret += "mult"
        ret += ",\n" + self.links[0].string(True)
        ret += ",\n" + self.links[1].string(True)
        return ret

class MultDriveOperator(Base):
    bl_label = "Mult drive"
    drive_1_name = bpy.props.EnumProperty(items=enum_drive, name="Drive 1")
    drive_1_edit = bpy.props.BoolProperty(name="")
    drive_2_name = bpy.props.EnumProperty(items=enum_drive, name="Drive 2")
    drive_2_edit = bpy.props.BoolProperty(name="")
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.drive_exists(context)
    def assign(self, context):
        self.entity = database.drive[context.scene.drive_index]
        self.drive_1_name = self.entity.links[0].name
        self.drive_2_name = self.entity.links[0].name
    def store(self, context):
        self.entity = database.drive[self.index]
        self.entity.unlink_all()
        self.link_drive(context, self.drive_1_name, self.drive_1_edit)
        self.link_drive(context, self.drive_2_name, self.drive_2_edit)
        self.entity.increment_links()
    def draw(self, context):
        layout = self.layout
        self.draw_link(layout, "drive_1_name", "drive_1_edit")
        self.draw_link(layout, "drive_2_name", "drive_2_edit")
    def create_entity(self):
        return MultDrive(self.name)

klasses[MultDriveOperator.bl_label] = MultDriveOperator

class NodeDrive(Entity):
    def string(self, indent=False):
        ret = super().indent_drives*"\t" if indent else ""
        ret += "node"
        if self.objects[0] in database.node:
            ob = self.objects[0]
        elif self.objects[0] in database.rigid_dict:
            ob = database.rigid_dict[self.objects[0]]
        else:
            wm = bpy.context.window_manager
            wm.popup_menu(lambda self, c: self.layout.label(
                "Error: Node drive " + self.name + " is not assigned to a node"), title="MBDyn Error", icon='ERROR')
            print("Error: Node drive " + self.name + " is not assigned to a node")
            return
        if ob in (database.structural_dynamic_nodes | database.structural_static_nodes |
            database.structural_dummy_nodes):
            ret += ", "+str(database.node.index(ob))+", structural"
        if self.symbolic_name:
            ret += ", string, \""+self.symbolic_name+"\""
        ret += ",\n"+self.links[0].string(True)
        return ret

class NodeDriveOperator(Base):
    bl_label = "Node drive"
    symbolic_name = bpy.props.StringProperty(name="Symbolic name", maxlen=100,
        description="Private data of the structural node")
    drive_name = bpy.props.EnumProperty(items=enum_drive, name="Drive")
    drive_edit = bpy.props.BoolProperty(name="")
    @classmethod
    def poll(cls, context):
        obs = SelectedObjects(context)
        return cls.bl_idname.startswith(root_dot+"e_") or len(obs) == 1
    def defaults(self, context):
        self.drive_exists(context)
        self.symbolic_name = ""
    def assign(self, context):
        self.entity = database.drive[context.scene.drive_index]
        self.symbolic_name = self.entity.symbolic_name
        self.drive_name = self.entity.links[0].name
    def store(self, context):
        self.entity = database.drive[self.index]
        self.entity.objects = SelectedObjects(context)
        self.entity.symbolic_name = self.symbolic_name
        self.entity.unlink_all()
        self.link_drive(context, self.drive_name, self.drive_edit)
        self.entity.increment_links()
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "symbolic_name")
        self.draw_link(layout, "drive_name", "drive_edit")
    def create_entity(self):
        return NodeDrive(self.name)

klasses[NodeDriveOperator.bl_label] = NodeDriveOperator

class ElementDrive(Entity):
    def string(self, indent=False):
        ret = super().indent_drives*"\t" if indent else ""
        ret += "element, " + str(database.element.index(self.links[0])) + ", " + str(self.links[0].type)
        if self.symbolic_name:
            ret += ", string, \"" + selfsymbolic_name + "\""
        ret += ",\n" + self.links[1].string(True)
        return ret

class ElementDriveOperator(Base):
    bl_label = "Structural node drive"
    element_name = bpy.props.EnumProperty(items=enum_element, name="Element")
    element_edit = bpy.props.BoolProperty(name="")
    symbolic_name = bpy.props.StringProperty(name="Symbolic name", maxlen=100,
        description="Private data of the structural node")
    drive_name = bpy.props.EnumProperty(items=enum_drive, name="Drive")
    drive_edit = bpy.props.BoolProperty(name="")
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.element_exists(context)
        self.drive_exists(context)
        self.symbolic_name = ""
    def assign(self, context):
        self.entity = database.drive[context.scene.drive_index]
        self.symbolic_name = self.entity.symbolic_name
        self.element_name = self.entity.links[0].name
        self.drive_name = self.entity.links[1].name
    def store(self, context):
        self.entity = database.drive[self.index]
        self.symbolic_name = self.symbolic_name
        self.entity.unlink_all()
        self.link_drive(context, self.element_name, self.element_edit)
        self.link_drive(context, self.drive_name, self.drive_edit)
        self.entity.increment_links()
    def draw(self, context):
        layout = self.layout
        self.draw_link(layout, "element_name", "element_edit")
        layout.prop(self, "symbolic_name")
        self.draw_link(layout, "drive_name", "drive_edit")
    def create_entity(self):
        return ElementDrive(self.name)

klasses[ElementDriveOperator.bl_label] = ElementDriveOperator

class DriveDrive(Entity):
    def string(self, indent=False):
        ret = super().indent_drives*"\t" if indent else ""
        ret += "drive"
        ret += ",\n" + self.links[0].string(True)
        ret += ",\n" + self.links[1].string(True)
        return ret

class DriveDriveOperator(Base):
    bl_label = "Drive drive"
    drive_1_name = bpy.props.EnumProperty(items=enum_drive, name="Drive 1")
    drive_1_edit = bpy.props.BoolProperty(name="")
    drive_2_name = bpy.props.EnumProperty(items=enum_drive, name="Drive 2")
    drive_2_edit = bpy.props.BoolProperty(name="")
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.drive_exists(context)
    def assign(self, context):
        self.entity = database.drive[context.scene.drive_index]
        self.drive_1_name = self.entity.links[0].name
        self.drive_2_name = self.entity.links[0].name
    def store(self, context):
        self.entity = database.drive[self.index]
        self.entity.unlink_all()
        self.link_drive(context, self.drive_1_name, self.drive_1_edit)
        self.link_drive(context, self.drive_2_name, self.drive_2_edit)
        self.entity.increment_links()
    def draw(self, context):
        layout = self.layout
        self.draw_link(layout, "drive_1_name", "drive_1_edit")
        self.draw_link(layout, "drive_2_name", "drive_2_edit")
    def create_entity(self):
        return DriveDrive(self.name)

klasses[DriveDriveOperator.bl_label] = DriveDriveOperator

class ArrayDrive(Entity):
    def string(self, indent=False):
        ret = super().indent_drives*"\t" if indent else ""
        ret += "array, " + str(self.N)
        for i in range(self.N):
            ret += ',\n'+self.links[i].string(True)
        return ret

class ArrayDriveOperator(Base):
    bl_label = "Array drive"
    N = bpy.props.IntProperty(min=2, max=20)
    drive_names = bpy.props.CollectionProperty(name="Drive Names", type = BPY.DriveNames)
    @classmethod
    def poll(cls, context):
        return True
    def defaults(self, context):
        self.N = 2
        self.drive_exists(context)
        for i in range(20):
            self.drive_names.add()
    def assign(self, context):
        self.entity = database.drive[context.scene.drive_index]
        self.N = self.entity.N
        for i in range(20):
            self.drive_names.add()
        for i, link in enumerate(self.entity.links):
            self.drive_names[i].value = link.name
    def store(self, context):
        self.entity = database.drive[self.index]
        self.entity.N = self.N
        self.entity.unlink_all()
        for d in self.drive_names[:self.N]:
            self.link_drive(context, d.value, d.edit)
        self.entity.increment_links()
    def draw(self, context):
        self.basis = self.N
        layout = self.layout
        layout.prop(self, "N")
        for i in range(self.N):
            row = layout.row()
            row.prop(self.drive_names[i], "value", text="")
            row.prop(self.drive_names[i], "edit", toggle=True)
    def check(self, context):
        return self.basis != self.N
    def create_entity(self):
        return ArrayDrive(self.name)

klasses[ArrayDriveOperator.bl_label] = ArrayDriveOperator

bundle = Bundle(tree, Base, klasses, database.drive, "drive")
