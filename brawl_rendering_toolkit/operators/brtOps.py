import bpy

from math import radians
from bpy.types import Operator
from bpy.props import BoolProperty
from mathutils import Quaternion
from ..modules import brawlImport

if hasattr(bpy.types, "MYBIGBUTTONTAB_PT_MyBigButton"):
    from render_button import SCENECAMERA_OT_BatchRenderAll as bra

#-----------------------------------------

def unlink_obj_from_collections(obj):
    for collection in obj.users_collection:
        collection.objects.unlink(obj)
    return obj

def check_controls():
    if not brawlImport.check_collections('Controls'):
        collection = bpy.data.collections.new('Controls')
        bpy.context.scene.collection.children.link(collection)

    if bpy.data.objects.get('Con.Proxy') is None:
        if bpy.data.objects.get('Empty') is None:
            o = bpy.data.objects.new("Con.Proxy", None )
            o.empty_display_type = 'SPHERE'
            o.location=(2.0,0.0,6.0)
            bpy.data.collections['Controls'].objects.link(o)
        else:
            bpy.data.objects['Empty'].name = 'Con.Proxy'
            bpy.data.objects['Con.Proxy'].parent = None

    if bpy.data.objects.get('Con.Scale') is None:
        if bpy.data.objects.get('SCALE') is None:
            o = bpy.data.objects.new("Con.Scale", None )
            o.empty_display_type = 'PLAIN_AXES'
            o.location=(0,0.0,0.0)
            bpy.data.collections['Controls'].objects.link(o)
        else:
            bpy.data.objects['SCALE'].name = 'Con.Scale'
            bpy.data.objects['Con.Scale'].parent = None
    
    if bpy.data.objects.get('Lbl.Proxy') is None:
        if bpy.data.objects.get('Text') is None:
            myFontCurve = bpy.data.curves.new(type="FONT",name="Text")
            myFontOb = bpy.data.objects.new("Lbl.Proxy",myFontCurve)
            myFontOb.location = 0.0,0.0,5.0
            myFontOb.rotation_euler = (1.5707963705062866,0,0)
            myFontOb.data.body = "PROXY ON       PROXY OFF"
            myFontOb.data.align_x = 'CENTER'
            bpy.data.collections['Controls'].objects.link(myFontOb)
        else:
            bpy.data.objects['Text'].name = 'Lbl.Proxy'
    
    return True

#-----------------------------------------

def set_obj_mods(obj, context):
    mesh = obj.data
    if obj.type == 'MESH':
        mesh.use_auto_smooth = False
    context.view_layer.objects.active = obj
    context.view_layer.objects.active.modifiers.clear()

    subd = context.view_layer.objects.active.modifiers.new('Subdivision Subsurface', 'SUBSURF')
    subd.render_levels = 2

    arm1 = context.view_layer.objects.active.modifiers.new('Proxy Armature','ARMATURE')
    arm1.object = context.scene.objects.get("DAE_Armature")

def initRig(context):
    bind_list_head = [
        ['CFG.Hip','HipN'],
        ['CFG.Waist','BodyN'],
        ['CFG.Waist','WaistN'],
        ['CFG.Bust','BustN'],
        ['CFG.Neck','NeckN'],
        ['CFG.Head','HeadN'],
        ['CFG.Leg.Start.L','LLegJ'],
        ['CFG.Knee.L','LKneeJ'],
        ['CFG.Ankle.L','LFootJ'],
        ['CFG.Toe.L','LToeN'],
        ['CFG.Shoulder.Start.L','LShoulderN'],
        ['CFG.Shoulder.L','LShoulderJ'],
        ['CFG.Elbow.L','LArmJ'],
        ['CFG.Hand.L','LHandN'],
        ['CFG.Thumb.1.L','LThumbNa'],
        ['CFG.Thumb.2.L','LThumbNb'],
        ['CFG.FingerIndex.1.L','L1stNa'],
        ['CFG.FingerIndex.2.L','L1stNb'],
        ['CFG.FingerMiddle.1.L','L2ndNa'],
        ['CFG.FingerMiddle.2.L','L2ndNb'],
        ['CFG.FingerRing.1.L','L3rdNa'],
        ['CFG.FingerRing.2.L','L3rdNb'],
        ['CFG.FingerPinky.1.L','L4thNa'],
        ['CFG.FingerPinky.2.L','L4thNb']
    ]
    bind_list_tail = [
        ['CFG.Thumb.Tip.L','LThumbNb'],
        ['CFG.FingerIndex.Tip.L','L1stNb'],
        ['CFG.FingerMiddle.Tip.L','L2ndNb'],
        ['CFG.FingerRing.Tip.L','L3rdNb'],
        ['CFG.FingerPinky.Tip.L','L4thNb']
    ]

    scene = context.scene
    cspur = None
    target = None
    objects = [obj for obj in context.scene.objects if "BRT" in obj]
    for obj in objects :
        if obj["BRT"] == "CSPUR":
            cspur = obj
        if obj["BRT"] == "TARGET":
            target = obj

    cursor_mat_original = scene.cursor.matrix
    context.view_layer.objects.active = cspur
    if context.mode != 'POSE':
        bpy.ops.object.mode_set(mode='POSE', toggle=False)

    tog_bone = cspur.pose.bones.get('CFG.Toggle')
    tog_bone.rotation_mode = 'XYZ'
    tog_bone.rotation_euler = [0, radians(-45), 0]

    for bone_pair in bind_list_head:
        csp_bone = cspur.pose.bones.get(bone_pair[0])
        target_bone = target.pose.bones.get(bone_pair[1])
        if not [var for var in (csp_bone, target_bone) if var is None]:
            bpy.ops.pose.select_all(action='DESELECT')
            csp_bone.bone.select = True
            context.object.data.bones.active = csp_bone.bone
            scene.cursor.location = (target.matrix_world @ target_bone.matrix).to_translation()
            mat_world = context.object.convert_space(pose_bone=csp_bone, matrix=csp_bone.matrix, from_space='POSE', to_space='WORLD')
            mat_world.translation = scene.cursor.location
            csp_bone.matrix = context.object.convert_space(pose_bone=csp_bone, matrix=mat_world, from_space='WORLD', to_space='POSE')
        else:
            print(bone_pair[1] + " doesn't exist. Skipping...")
    
    for bone_pair in bind_list_tail:
        csp_bone = cspur.pose.bones.get(bone_pair[0])
        target_bone = target.pose.bones.get(bone_pair[1])
        if not [var for var in (csp_bone, target_bone) if var is None]:
            bpy.ops.pose.select_all(action='DESELECT')
            csp_bone.bone.select = True
            context.object.data.bones.active = csp_bone.bone
            scene.cursor.location = target.matrix_world @ target_bone.tail
            mat_world = context.object.convert_space(pose_bone=csp_bone, matrix=csp_bone.matrix, from_space='POSE', to_space='WORLD')
            mat_world.translation = scene.cursor.location
            csp_bone.matrix = context.object.convert_space(pose_bone=csp_bone, matrix=mat_world, from_space='WORLD', to_space='POSE')
        else:
            print(bone_pair[1] + " doesn't exist. Skipping...")

    scene.cursor.matrix = cursor_mat_original
    bpy.ops.pose.select_all(action='DESELECT')
    cspur.data.layers[0] = True

def bindToIK(context):
    scene = context.scene
    cspur = None
    target = None
    proxy = None
    objects = [obj for obj in context.scene.objects if "BRT" in obj]
    for obj in objects :
        if obj["BRT"] == "CSPUR":
            cspur = obj
            print(f"cspur: {cspur.name}")
        if obj["BRT"] == "TARGET":
            target = obj
            print(f"target: {target.name}")
        if obj["BRT"] == "PROXY":
            proxy = obj
            print(f"proxy: {proxy.name}")
    
    tog_bone = cspur.pose.bones.get('CFG.Toggle')
    matched_bone = False

    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    bpy.ops.object.select_all(action='DESELECT')
    cspur.select_set(True)
    context.view_layer.objects.active = cspur

    bpy.ops.object.mode_set(mode='POSE', toggle=False)
    bpy.ops.pose.select_all(action='DESELECT')
    cspur.data.layers[2] = True
    for i in range(32):
        if i != 2:
            cspur.data.layers[i] = False
    for bone in cspur.pose.bones:
        if bone.bone.layers[2] == True:
            bone.bone.select = True
    bpy.ops.pose.armature_apply(selected=True)
    bpy.ops.pose.select_all(action='DESELECT')
    tog_bone.bone.select = True
    bpy.ops.pose.rot_clear()
    bpy.ops.pose.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    
    bpy.ops.object.select_all(action='DESELECT')
    target.select_set(state=True)
    context.view_layer.objects.active = target
    bpy.ops.object.mode_set(mode='POSE', toggle=False)
    bpy.ops.pose.select_all(action='SELECT')
    for bone in target.pose.bones:
        context.object.data.bones.active = bone.bone
        for cspb in cspur.pose.bones:
            if cspb.name == bone.name:
                matched_bone = True
                for constraint in {'COPY_LOCATION', 'COPY_ROTATION', 'COPY_SCALE'}:
                    name =''
                    constraint_exists = False
                    if constraint == 'COPY_LOCATION':
                        name = "BRT Copy Location"
                    elif constraint == 'COPY_ROTATION':
                        name = "BRT Copy Rotation"
                    elif constraint == 'COPY_SCALE':
                        name = "BRT Copy Scale"
                    for con in bone.constraints:
                        if con.name == name:
                            constraint_exists = True
                    if not constraint_exists:
                        c = bone.constraints.new(constraint)
                        c.name = "BRT " + c.name
                    else:
                        c = bone.constraints.get(name)
                    c.target = cspur
                    c.subtarget = cspb.name
                    if constraint == 'COPY_SCALE':
                        c.use_offset = True
                    d = c.driver_add('enabled').driver
                    d.type = 'SCRIPTED'
                    var = d.variables.new()
                    var.name = 'loc'
                    var.targets[0].id = bpy.data.objects['Con.Proxy']
                    var.targets[0].data_path='location.x'
                    if constraint == 'COPY_SCALE':
                        d.expression = ' loc >= 0.01'
                    else:
                        d.expression = ' loc >= 0'
    for i in range(32):
        if any(i == layer for layer in {8, 9, 10, 11, 12, 13, 14}):
            cspur.data.layers[i] = True
        else:
            cspur.data.layers[i] = False
    cspur.data.layers[2] = False
    if context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    target.hide_select=True
    target.hide_viewport=True
    proxy.hide_viewport=True
    return matched_bone

def clearRig(context):
    scene = context.scene
    target = None
    if context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    print("Searching for target")
    objects = [obj for obj in context.scene.objects if "BRT" in obj]
    for obj in objects :
        if obj["BRT"] == "TARGET":
            print("Target found")
            target = obj
        else:
            print(f"{obj.name} is not target")
            obj.select_set(state=False)
    if target is not None:    
        print("Deselecting all objects")
        bpy.ops.object.select_all(action='DESELECT')
        print("Selecting target")
        target.select_set(state=True)
        context.view_layer.objects.active = target
        print("Switching to target mode")
        if context.mode != 'POSE':
            bpy.ops.object.posemode_toggle()
        print("Removing constraints")
        for bone in target.pose.bones:
            if hasattr(bone, "constraints"):
                constraints = [constraint for constraint in bone.constraints]
                for constraint in constraints:
                    try:
                        print(f"Removed constraint {constraint.name} from bone {bone.name}")
                        bone.constraints.remove(constraint)
                    except:
                        print(f"Error removing constraint {constraint.name} from bone {bone.name}")
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        return True
    else:
        return False

def paths_update():
    if bpy.ops.pose.paths_update.poll():
        bpy.ops.pose.paths_update()

def menu_func_import(self, context):
    self.layout.operator(brawlImport.OBJECT_OT_brawlcrate_collada_import.bl_idname,text='Model (.dae)')
    self.layout.operator(brawlImport.POSE_OT_brawlcrate_anim_import.bl_idname,text='Animation (.anim)')

def update_images():
    for img in bpy.data.images:
        img.reload()

#-----------------------------------------

class DATA_OT_brt_init_polish_setup(Operator):
    bl_idname = "brt.setup"
    bl_label = "Setup DAE for polish"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):    
        return ('proxy' in context.scene)

    def execute(self, context):
        #replace with check_controls
        if bpy.data.objects.get('Con.Proxy') is None:
            o = bpy.data.objects.new( "Con.Proxy", None )
            o.empty_display_type = 'SPHERE'
            o.location=(2.0,0.0,6.0)
            bpy.data.collections['Controls'].objects.link(o)

        for obj in bpy.context.selected_objects:
            obj.select_set(False)
        context.view_layer.objects.active = bpy.data.objects[context.scene.proxy].children[0]
        bpy.ops.object.select_hierarchy(direction='CHILD',extend=False)

        for obj in context.scene.objects.get("DAE_Armature").children:
            unlink_obj_from_collections(obj)
            if not brawlImport.obj_in_collection(obj, 'Model'):
                bpy.data.collections['Model'].objects.link(obj)
            set_obj_mods(obj, context)

        self.report({'INFO'}, "Initial polish done")
        return {'FINISHED'}

class OBJECT_OT_brt_set_object_mods(Operator):
    bl_idname = "brt.mod"
    bl_label = "Apply Default Modifiers to Mesh Object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        is_not_mesh = False
        selected = context.selected_objects
        if len(selected) == 0:
            return False
        for obj in selected:
            if obj.type != 'MESH':
                is_not_mesh = True
        
        return not is_not_mesh

    def execute(self, context):
        for obj in context.selected_objects:
            set_obj_mods(obj, context)
        return {'FINISHED'}

class OBJECT_OT_brt_toggle_proxy(Operator):
    bl_idname = "brt.toggle_proxy"
    bl_label = "Toggle use of proxy armature"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        if check_controls():
            bpy.data.objects['Con.Proxy'].location[0] = (bpy.data.objects['Con.Proxy'].location[0] * -1)
        
        return {'FINISHED'}

class POSE_ARMATURE_OT_clear_to_bind(Operator):
    bl_idname = "brawlcrate.clear_to_bind"
    bl_label = "Clear To Bind"
    bl_options = {'REGISTER', 'UNDO'}
    bl_context = "posemode"

    clear_location : BoolProperty(name='Location',default=True)
    clear_rotation : BoolProperty(name='Rotation',default=True)
    clear_scale : BoolProperty(name='Scale',default=True)

    @classmethod
    def poll(cls,context):
        return context.selected_pose_bones is not None and len(context.selected_pose_bones) > 0 and context.mode == 'POSE'

    def execute(self,context):
        pose_bones = context.selected_pose_bones

        for pose_bone in pose_bones:
            if 'brawl_local_bind_pose' in pose_bone:
                loc,rot,scale = brawlImport.matrix_from_sequence(pose_bone['brawl_local_bind_pose']).decompose()
                if  self.clear_location:
                    pose_bone.location = loc
                    
                if self.clear_rotation:
                    pose_bone.rotation_euler = rot.to_euler('XYZ')
                    pose_bone.rotation_quaternion = rot#.to_quaternion()
                    
                if self.clear_scale:
                    pose_bone.scale = scale
            else:
                if  self.clear_location:
                    pose_bone.location = (0,0,0)
                    
                if self.clear_rotation:
                    pose_bone.rotation_euler = (0,0,0)
                    pose_bone.rotation_quaternion = Quaternion((1,0,0,0))
                    
                if self.clear_scale:
                    pose_bone.scale = (1,1,1)

        if bpy.context.scene.tool_settings.use_keyframe_insert_auto:
            bpy.ops.anim.keyframe_insert_menu(type='__ACTIVE__', confirm_success=True)

        paths_update()

        return {'FINISHED'}

class POSE_ARMATURE_OT_config_ik(Operator):
    bl_idname = "brt.config_ik"
    bl_label = "Configure IK Rig"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        csp_rig = False
        target_rig = False
        objects = [obj for obj in context.scene.objects if "BRT" in obj]
        for obj in objects :
            if obj["BRT"] == 'CSPUR':
                csp_rig = True
            if obj["BRT"] == 'TARGET':
                target_rig = True
        return csp_rig and target_rig

    def execute(self,context):
        print("Adjusting IK Rig to target")
        initRig(context)
        return {'FINISHED'}

class POSE_ARMATURE_OT_bind_ik(Operator):
    bl_idname = "brt.bind_ik"
    bl_label = "Bind IK Rig"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        csp_rig = False
        target_rig = False
        objects = [obj for obj in context.scene.objects if "BRT" in obj]
        for obj in objects :
            if obj["BRT"] == 'CSPUR':
                csp_rig = True
            if obj["BRT"] == 'TARGET':
                target_rig = True
        return csp_rig and target_rig

    def execute(self,context):
        print("Binding IK Rig to target")
        bindToIK(context)
        
        return {'FINISHED'}

class POSE_ARMATURE_OT_unbind_ik(Operator):
    bl_idname = "brt.unbind_ik"
    bl_label = "Unbind IK Rig"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        target_rig = False
        objects = [obj for obj in context.scene.objects if "BRT" in obj]
        for obj in objects :
            if obj["BRT"] == 'TARGET':
                target_rig = True
        return target_rig
    
    def execute(self,context):
        print("Removing IK Rig from target")
        result = clearRig(context)
        if not result:
            print("Did not successfully remove IK Rig from target")
        return {'FINISHED'}

class IMAGE_OT_reload_textures(Operator):
    bl_idname = "brt.reload_textures"
    bl_label = "Reload all texture images"
    
    def execute(self, context):
        update_images()
        return {'FINISHED'}

class DATA_OT_brt_purge(Operator):
    bl_idname = "brt.purge"
    bl_label = "Purge Un-used data"

    def execute(self, context):
        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
        return {'FINISHED'}

class IMAGE_OT_reload_and_render(Operator):
    bl_idname = "brt.reload_and_render"
    bl_label = "Reload all textures and render active camera on the current frame"
    
    def execute(self, context):
        update_images()
        if hasattr(bpy.types, "MYBIGBUTTONTAB_PT_MyBigButton"):
            if not hasattr(bpy.data.images,'Render Result'):
                bpy.ops.image.new(name='Render Result', width=1920, height=1920)
            bpy.ops.cameramanager.render_scene_camera()
        return{'FINISHED'}
        
class IMAGE_OT_reload_and_render_all(Operator):
    bl_idname = "brt.reload_and_render_all"
    bl_label = "Reload all textures and render all cameras on the current frame"
    
    def execute(self,context):
        update_images()
        if hasattr(bpy.types, "MYBIGBUTTONTAB_PT_MyBigButton"):
            if not hasattr(bpy.data.images,'Render Result'):
                bpy.ops.image.new(name='Render Result', width=1920, height=1920)
            bpy.ops.cameramanager.render_all_camera()
        return{'FINISHED'}

class IMAGE_OT_reload_and_render_anim(Operator):
    bl_idname = "brt.reload_and_render_anim"
    bl_label = "Reload all textures and render active camera for the entire animation"
    
    def execute(self, context):
        update_images()
        if hasattr(bpy.types, "MYBIGBUTTONTAB_PT_MyBigButton"):
            if not hasattr(bpy.data.images,'Render Result'):
                bpy.ops.image.new(name='Render Result', width=1920, height=1920)
            bpy.ops.cameramanager.render_scene_animation()
        return{'FINISHED'}

class IMAGE_OT_reload_and_render_all_anim(Operator):
    bl_idname = "brt.reload_and_render_all_anim"
    bl_label = "Reload all textures and render all cameras for the entire animation"

    _timer = None
    path = path_root = ""
    rsSIBF = False
    start_frame = end_frame = current_frame = 0
    start_camera = ''

    def __init__(self):
        print("Start")
        update_images()

    def __del__(self):
        print("End")

    def modal_wrap(self, modal_func, thrd=None):
        def wrap(self, context, event):
            ret, = retset = modal_func(self, context, event)
            if ret in {'FINISHED', 'CANCELLED'}:
                s = context.scene
                tk = s.BRT_Settings
                tk.batchRenderDone = True
            return retset
        return wrap

    def updateFilePath(self, context):
        s = context.scene

        frame_string = ""
        frame_length = max(len(str(self.end_frame)),2)
        current_frame_str = str(self.current_frame)
        for i in range(frame_length - len(current_frame_str)):
            frame_string += "0"
        frame_string += str(self.current_frame)
        frame_string += "_"
        s.render.filepath = self.path_root + frame_string

    def execute(self, context):
        print('EXECUTING')
        if hasattr(bpy.types, "MYBIGBUTTONTAB_PT_MyBigButton"):
            if not hasattr(bpy.data.images,'Render Result'):
                bpy.ops.image.new(name='Render Result', width=1920, height=1920)
        bpy.ops.cameramanager.render_all_camera()
        return {'FINISHED'}

    def modal(self, context, event):
        s = context.scene
        tk = s.BRT_Settings
        rs = s.RBTab_Settings

        if event.type == 'TIMER':
            if tk.batchRenderDone:
                if self.current_frame >= self.end_frame:
                    self.current_frame -= 1
                    s.frame_current  = self.current_frame
                    s.render.filepath = self.path_root
                    rs.saveInBlendFolder = self.rsSIBF
                    return {'FINISHED'}
                else:
                    self.current_frame += 1
                    s.frame_current = self.current_frame
                    tk.batchRenderDone = False
                    self.updateFilePath(context)
                    self.execute(context)

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        print("INVOKING")

        bra._modal_org = bra.modal
        bra.modal = self.modal_wrap(bra.modal)

        s = context.scene
        tk = s.BRT_Settings
        rs = s.RBTab_Settings

        self.path = s.render.filepath
        tk.batchRenderDone = False

        self.rsSIBF = rs.saveInBlendFolder
        rs.saveInBlendFolder = False

        self.start_frame = s.frame_preview_start if s.use_preview_range else s.frame_start
        self.end_frame = s.frame_preview_end if s.use_preview_range else s.frame_end
        isDS = True if self.path == '//' else False
        localPath = bpy.path.abspath(self.path)

        s.frame_current = self.start_frame
        self.path_root = localPath if isDS else self.path
        self.updateFilePath(context)
        self.execute(context)

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.25, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

#-----------------------------------------