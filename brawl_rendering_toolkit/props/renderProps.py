import bpy

from bpy.types import Scene, PropertyGroup
from bpy.props import BoolProperty, PointerProperty, StringProperty

#-----------------------------------------

def register():
    Scene.BRT_Settings = PointerProperty(
        type=Toolkit_Settings
    )
    Scene.proxy = StringProperty(
        default=""
    )
    Scene.target = StringProperty(
        default=""
    )
    Scene.cspur = StringProperty(
        default=""
    )
    Scene.edit_mode = BoolProperty(
        default=False
    )

#-----------------------------------------

class Toolkit_Settings(PropertyGroup):
    batchRenderDone : BoolProperty(
        name="Batch Finished",
        description="Set when CameraManager finishes a render",
        default=False
    )

#-----------------------------------------