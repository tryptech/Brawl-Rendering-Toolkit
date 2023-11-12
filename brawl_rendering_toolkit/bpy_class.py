from . import modules
from . import operators
from . import props
from . import ui

#-----------------------------------------

classes = [
    modules.brawlImport.OBJECT_OT_brawlcrate_collada_import,
    modules.brawlImport.POSE_OT_brawlcrate_anim_import,
    operators.brtOps.DATA_OT_brt_init_polish_setup,
    operators.brtOps.DATA_OT_brt_purge,
    operators.brtOps.OBJECT_OT_brt_set_object_mods,
    operators.brtOps.OBJECT_OT_brt_toggle_proxy,
    operators.brtOps.OBJECT_OT_brt_init_quantize,
    operators.brtOps.OBJECT_OT_brt_quantize_and_normalize_weights,
    operators.brtOps.POSE_ARMATURE_OT_clear_to_bind,
    operators.brtOps.POSE_ARMATURE_OT_config_ik,
    operators.brtOps.POSE_ARMATURE_OT_bind_ik,
    operators.brtOps.POSE_ARMATURE_OT_unbind_ik,
    operators.brtOps.IMAGE_OT_reload_textures,
    operators.brtOps.IMAGE_OT_reload_and_render,
    operators.brtOps.IMAGE_OT_reload_and_render_all,
    operators.brtOps.IMAGE_OT_reload_and_render_anim,
    operators.brtOps.IMAGE_OT_reload_and_render_all_anim,
    props.renderProps.Toolkit_Settings,
    ui.panel.POSE_ARMATURE_PT_brt_panel,
    ui.panel.ARMATURES_PT_panel,
    ui.panel.IMPORT_PT_panel,
    ui.panel.POSING_PT_panel,
    ui.panel.RENDER_PT_panel,
    ui.panel.UTILITY_PT_panel,
    ui.panel.BLOP_PT_rigui_CSPUR,
    ui.panel.BLOP_PT_customprops_CSPUR
]

#-----------------------------------------