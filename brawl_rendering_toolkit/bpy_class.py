from . import modules
from . import operators
from . import props
from . import ui

classes = [
    modules.brawlImport.OBJECT_OT_brawlcrate_collada_import,
    modules.brawlImport.POSE_OT_brawlcrate_anim_import,
    ui.panel.POSE_ARMATURE_PT_brt_panel,
    ui.panel.ARMATURES_PT_panel,
    ui.panel.IMPORT_PT_panel,
    ui.panel.POSING_PT_panel,
    ui.panel.RENDER_PT_panel,
    ui.panel.UTILITY_PT_panel,
    ui.panel.BLOP_PT_rigui_CSPUR,
    ui.panel.BLOP_PT_customprops_CSPUR
]