import bpy

from bpy.types import Object, Panel, PoseBone
from ..modules import brawlImport
from ..operators import brtOps 

blm_rig_id = "CSPUR"

#-----------------------------------------

class POSE_ARMATURE_PT_brt_panel(Panel):
    bl_idname = "POSE_ARMATURE_PT_brt_panel"
    bl_label = "Brawl Rendering Toolkit"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Brawl"

    
    def draw(self,context):
        
        '''
        user:readme: Since the animation rig's pose identity is equal to world identity, 
        the user can't just do Alt-R/G/S to get back to the T-Pose. The operators below
        are the recreated functionality. (3DView->Tools->Animation->BrawlCrate->Clear)
        '''

class ARMATURES_PT_panel(Panel): 
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Brawl"
    bl_parent_id = "POSE_ARMATURE_PT_brt_panel"
    bl_options = {"DEFAULT_CLOSED"}
    bl_idname = "ARMATURES_PT_panel"
    bl_label = "Armatures"
    
    def draw(self, context):
        layout = self.layout.column(align=True)
        scene = bpy.context.scene

        row = layout.column(align = True)
        row.prop_search(
            scene, 'proxy', bpy.data, "objects", text='Proxy', icon='ARMATURE_DATA' 
        )

class IMPORT_PT_panel(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Brawl"
    bl_parent_id = "POSE_ARMATURE_PT_brt_panel"
    bl_options = {"DEFAULT_CLOSED"}
    bl_idname = "IMPORT_PT_panel"
    bl_label = "Import"
    
    def draw(self, context):
        layout = self.layout.column(align=True)
        scene = bpy.context.scene
        
        row = layout.row(align=True)
        op = row.operator(brawlImport.OBJECT_OT_brawlcrate_collada_import.bl_idname,text='DAE')
        op = row.operator(brawlImport.POSE_OT_brawlcrate_anim_import.bl_idname,text='ANIM')
        
        layout.row().separator()
        layout.row().separator()
        row = layout.column(align=True)
        op = row.operator(brtOps.DATA_OT_brt_init_polish_setup.bl_idname,text='Setup for Manual Polish',icon='SPHERE')
        op = row.operator(brtOps.OBJECT_OT_brt_set_object_mods.bl_idname,text='Apply Default Modfiers',icon='MODIFIER')
        
        layout.row().separator()
        layout.row().separator()
        row = layout.column(align=True)
        op = row.operator(brtOps.POSE_ARMATURE_OT_config_ik.bl_idname,text='Configure IK',icon='POSE_HLT')
        op = row.operator(brtOps.POSE_ARMATURE_OT_bind_ik.bl_idname,text='Bind IK Rig',icon='LINKED')
        op = row.operator(brtOps.POSE_ARMATURE_OT_unbind_ik.bl_idname,text='Unbind IK Rig',icon='UNLINKED')

class POSING_PT_panel(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Brawl"
    bl_parent_id = "POSE_ARMATURE_PT_brt_panel"
    bl_options = {"DEFAULT_CLOSED"}
    bl_idname = "POSING_PT_panel"
    bl_label = "Posing"
    
    def draw(self, context):
        layout = self.layout.column(align=True)
        scene = bpy.context.scene
        
        column = layout.column(align=True)
        op = column.operator(brtOps.OBJECT_OT_brt_toggle_proxy.bl_idname,text='Toggle Proxy')
        op = column.operator(brtOps.POSE_ARMATURE_OT_clear_to_bind.bl_idname,text='Reset Proxy')
        op.clear_location=True
        op.clear_rotation=True
        op.clear_scale=True

class RENDER_PT_panel(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Brawl"
    bl_parent_id = "POSE_ARMATURE_PT_brt_panel"
    bl_options = {"DEFAULT_CLOSED"}
    bl_idname = "RENDER_PT_panel"
    bl_label = "Render"

    def draw(self, context):
        layout = self.layout.column(align=True)
        scene = bpy.context.scene
        rs = scene.RBTab_Settings
        anim_render = rs.switchStillAnim_prop
        saveInLocalFolder = rs.saveInBlendFolder

        if bpy.data.is_saved == False:
            layout.use_property_split = False
            row = layout.row(align=True)
            row.alignment='CENTER'
            row.alert = True
            row.label(text=' Save Blend File First  --->', icon='INFO')
            row.operator('wm.save_mainfile', text='', icon='FILE_TICK')
            row.alert = False
        else:
            if hasattr(bpy.types, "MYBIGBUTTONTAB_PT_MyBigButton"):
                row = layout.row(align=True)

                row.prop(rs,'saveInBlendFolder',text='Save in blend folder' if saveInLocalFolder else 'Save in custom path',icon='FILE_FOLDER' if saveInLocalFolder else 'BLENDER')

                row = layout.row(align=True)

                if saveInLocalFolder == False:
                    row.prop(scene.render, "filepath", text="")
                    row = layout.row(align=True)

                layout.row().separator()
                layout.row().separator()
                row = layout.row(align=True)

                row.prop(scene, "frame_float" if scene.show_subframe else "frame_current", text="Frame/Color")
                row.prop(rs, "switchStillAnim_prop", text="",icon='RENDER_ANIMATION')

                if anim_render:
                    row = layout.row(align=True)
                    sub = row.row(align=True)

                    sub.prop(scene, "frame_preview_start" if scene.use_preview_range else "frame_start", text="Start")
                    sub.prop(scene, "frame_preview_end" if scene.use_preview_range else "frame_end", text="End")

                layout.row().separator()
                layout.row().separator()
                row = layout.column(align=True)

                if anim_render:
                    row.operator(brtOps.IMAGE_OT_reload_and_render_anim.bl_idname,text="Render Current Camera w/ Recolors", icon='FILE_IMAGE')
                    row.operator(brtOps.IMAGE_OT_reload_and_render_all_anim.bl_idname,text="Render All Cameras w/ Recolors", icon='RENDER_RESULT')
                else:
                    row.operator(brtOps.IMAGE_OT_reload_and_render.bl_idname,text="Render Current Camera", icon='FILE_IMAGE')
                    row.operator(brtOps.IMAGE_OT_reload_and_render_all.bl_idname,text="Render All Cameras", icon='RENDER_RESULT')

class UTILITY_PT_panel(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Brawl"
    bl_parent_id = "POSE_ARMATURE_PT_brt_panel"
    bl_options = {"DEFAULT_CLOSED"}
    bl_idname = "UTILITY_PT_panel"
    bl_label = "Utility"
    
    def draw(self, context):
        layout = self.layout.column(align=True)
        scene = bpy.context.scene

        row = layout.column(align=True)
        op = row.operator(brtOps.DATA_OT_brt_purge.bl_idname,text='Clean Unused Data',icon='TRASH') 
        op = row.operator(brtOps.IMAGE_OT_reload_textures.bl_idname,text='Reload Textures',icon='FILE_REFRESH')

        layout.row().separator()
        layout.row().separator()
        row = layout.column(align=True)
		
        if "QuantizeSteps" in context.active_object and "QuantizeMaxBones" in context.active_object:
            op = row.prop(context.active_object, '["QuantizeMaxBones"]', text="Max Bones")
            op = row.prop(context.active_object, '["QuantizeSteps"]', text="Quantize Steps")
            op = row.operator(brtOps.OBJECT_OT_brt_quantize_and_normalize_weights.bl_idname,text='Quantize Weights',icon='SNAP_ON')
        else:
            op = row.operator(brtOps.OBJECT_OT_brt_init_quantize.bl_idname,text='Set up quantization',icon='SNAP_ON')

class BLOP_PT_rigui_CSPUR(Panel):
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Brawl'
	bl_label = "CSPUR UI"
	bl_idname = "BLOP_PT_rigui_CSPUR"

	@classmethod
	def poll(self, context):
		try:
			return (context.active_object.data.get("blm_rig_id") == blm_rig_id)
		except (AttributeError, KeyError, TypeError):
			return False

	def draw(self, context):
		layout = self.layout
		col = layout.column()


		row = col.row(align=True)
		row.prop(context.active_object.data,'layers', index=8, toggle=True, text='Center')

		row = col.row(align=True)
		row.prop(context.active_object.data,'layers', index=9, toggle=True, text='Right Arm')
		row.prop(context.active_object.data,'layers', index=12, toggle=True, text='Left Arm')

		row = col.row(align=True)
		row.prop(context.active_object.data,'layers', index=10, toggle=True, text='Right Hand')
		row.prop(context.active_object.data,'layers', index=13, toggle=True, text='Left Hand')

		row = col.row(align=True)
		row.prop(context.active_object.data,'layers', index=11, toggle=True, text='Right Foot')
		row.prop(context.active_object.data,'layers', index=14, toggle=True, text='Left Foot')

		row = col.row(align=True)
		row.prop(context.active_object.data,'layers', index=15, toggle=True, text='Fine Controls')

		row = col.row(align=True)
		row.prop(context.active_object.data,'layers', index=0, toggle=True, text='Config')
		row.prop(context.active_object.data,'layers', index=2, toggle=True, text='Apply')

		row = col.row(align=True)
		row.prop(context.active_object.data,'layers', index=30, toggle=True, text='Deform Tweak')

class BLOP_PT_customprops_CSPUR(Panel):
	bl_category = 'Brawl'
	bl_label = "CSPUR Properties"
	bl_idname = "BLOP_PT_customprops_CSPUR"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_options = {'DEFAULT_CLOSED'}

	@classmethod
	def poll(self, context):
		if context.active_object:
			if hasattr(context.active_object.data, 'blm_rig_id'):
				pose_bones = context.selected_pose_bones
				props = None
				rna_properties = {prop.identifier for prop in PoseBone.bl_rna.properties if prop.is_runtime}
				if context.selected_pose_bones:
					bones = context.selected_pose_bones
	
				elif context.selected_editable_bones:
					bones = [pose_bones[bone.name] for bone in context.selected_editable_bones]
	
				elif context.mode == 'OBJECT':
					bones = context.active_object.pose.bones
	
				else:
					return False
				if bones:
					props = [[prop for prop in bone.items() if prop not in rna_properties] for bone in bones]
	
				if props and bones:
					return (context.active_object.data.get("blm_rig_id") == blm_rig_id)
				else:
					return False
	
			else:
				return False

	def draw(self, context):
		layout = self.layout
		pose_bones = context.active_object.pose.bones
		if context.selected_pose_bones:
			bones = context.selected_pose_bones

		elif context.selected_editable_bones:
			bones = [pose_bones[bone.name] for bone in context.selected_editable_bones]

		else:
			bones = context.active_object.pose.bones

		def assign_props(row, val, key):
			row.property = key
			row.data_path = "active_pose_bone"
			try:
				row.value = str(val)
			except:
				pass

		rna_properties = {
			prop.identifier for prop in PoseBone.bl_rna.properties
			if prop.is_runtime
		}

	# make scripts backwards compatible
		skip = 0
		skip_keys = rna_properties
		if bpy.app.version < (3, 0, 0):
			skip_keys = rna_properties.union({"_RNA_UI"})
			skip = 1
	# Iterate through selected bones add each prop property of each bone to the panel.

		for bone in context.selected_pose_bones:
			if len(bone.keys()) > skip:
				box = layout.box()
			for key in sorted(bone.keys()):
				if key not in skip_keys:
					val = bone.get(key, "value")
					row = box.row()
					split = row.split(align=True, factor=0.7)
					row = split.row(align=True)
					row.label(text=key, translate=False)
					row = split.row(align=True)
					row.prop(bone, f'["{key}"]', text = "", slider=True)

#-----------------------------------------