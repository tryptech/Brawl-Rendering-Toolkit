import bpy

from bpy.types import Scene, PropertyGroup
from bpy.props import BoolProperty, PointerProperty

#-----------------------------------------

def register():
    Scene.BRT_Settings = PointerProperty(type=Toolkit_Settings)

#-----------------------------------------

class Toolkit_Settings(PropertyGroup):
    batchRenderDone : BoolProperty(
        name="Batch Finished",
        description="Set when CameraManager finishes a render",
        default=False
    )

#-----------------------------------------