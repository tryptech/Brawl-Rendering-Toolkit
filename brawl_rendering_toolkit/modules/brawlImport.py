'''
Collada Stability purposes (using colladas that weren't necessarily exported by BC):
    -don't use Name_array's id or float_array's id to get bone names and bind matrices. Read <joints>'s input semantics for JOINT and INV_BIND_MATRIX instead 

'''
#.anim format
#https://knowledge.autodesk.com/support/maya/learn-explore/caas/CloudHelp/cloudhelp/2016/ENU/Maya/files/GUID-87541258-2463-497A-A3D7-3DEA4C852644-htm.html 

import bpy, math, os, re
import xml.etree.ElementTree as ET

from bpy.props import BoolProperty, EnumProperty, StringProperty, CollectionProperty
from bpy.types import Operator, OperatorFileListElement, Armature
from bpy_extras.io_utils import ImportHelper
from math import pi, tan
from mathutils import  Matrix, Vector

#-----------------------------------------

class ContextOverride(dict):
    '''
    allows me to treat context overrides the same as non overrides:

        ctx0 = Context_Override(context.copy())
        #works
        obj = ctx0.active_object
        #error
        obj = context.copy().active_object

        just be careful to avoid overwriting existing dictionary attributes
    '''
    def __init__(self, context, *args, **kwargs):
        super(ContextOverride, self).__init__(*args, **kwargs)
        self.__dict__ = self
        self.update(context.copy())

class enumerate_start:
    def __init__(self, start_index, collection):
        self.current_index = start_index
        self.collection = collection
        self.end_index = len(collection)

    def __iter__(self):
        return self

    def __next__(self): # Python 3: def __next__(self)
        if self.current_index >= self.end_index:
            raise StopIteration
        else:
            current_element = self.collection[self.current_index]
            result = (self.current_index, current_element)
            self.current_index += 1

            return result
    # python2.x compatibility.
    next = __next__

def trim_comments(anim_file_lines):
    result = []
    for line in anim_file_lines:
        if not line.startswith(r'//'):
            result.append(line)
    return result

def read_until(start_index, lines, break_symbol):
    result = []
    for i, line in enumerate_start(start_index, lines):

        if break_symbol in line:
            break
        else:
            result.append(line)

    return i, result

def line_value_int(line):
    #assumes line in format of 'identifier value'
    return int(line.split(' ')[1])

def line_value_str(line):
    #assumes line in format of 'identifier value'
    return line.split(' ')[1]

def get_root_edit_bone(active_object):
    root_name = active_object['brawl_root']
    brawl_root = None

    try:
        brawl_root = active_object.data.edit_bones[root_name]#[bone for bone in active_object.data.edit_bones if (bone.name == root_name)]
    except Exception as _:
        raise Exception('missing \'brawl_root\' bone name in custom property of active object.')

    return brawl_root

def get_filename(path):
    return os.path.splitext(os.path.basename(path))[0]

#-----------------------------------------

def calculate_local_bind_matrices(active_object):
    bind_matrices = {}
    root = get_root_edit_bone(active_object)
    root_children_recursive = [child for child in root.children_recursive if 'brawl_bind' in child]
    
    for bone in root_children_recursive:
        bind_matrices[bone.name] = matrix_from_sequence(bone.parent['brawl_bind']).inverted() @ matrix_from_sequence(bone['brawl_bind'])
    bind_matrices[root.name] = matrix_from_sequence(root['brawl_bind'])

    return bind_matrices

def keyframe_bindpose(context,bind_frame):
    pre_mode = context.mode
    pre_frame = context.scene.frame_current

    bpy.ops.object.mode_set(mode='EDIT')
    bind_matrices = calculate_local_bind_matrices(context.active_object)

    bpy.ops.object.mode_set( mode='POSE')
    pose_bones = context.active_object.pose.bones

    context.scene.frame_set(bind_frame)
    

    #BC wont export a key if the xform is equal to the bind pose
    #so missing keys are imported as identity
    #but they should be equal to bind so we fix that here.
    for bone_name,bone_bind in bind_matrices.items():
        pose_bone = pose_bones[bone_name]
        pose_bone.matrix_basis = bone_bind
        pose_bone.keyframe_insert(data_path='location',group=bone_name)
        pose_bone.keyframe_insert(data_path='rotation_euler',group=bone_name)
        pose_bone.keyframe_insert(data_path='scale',group=bone_name)

    context.scene.frame_set(pre_frame)
    bpy.ops.object.mode_set(mode=pre_mode)

def update_scene_frame_set():
    context = bpy.context
    frame = context.scene.frame_current
    context.scene.frame_set(frame-1)
    context.scene.frame_set(frame)

def apply_bind_pose_to_action(context, remove_bind_pose=True):
    
    bpy.ops.object.mode_set(context, mode='EDIT')
    context.mode = 'EDIT'
    context.object = context.active_object
    context.selected_objects = [context.active_object]
    
    bind_matrices = calculate_local_bind_matrices(context.active_object)
    root = get_root_edit_bone(context.active_object)
    root_children_recursive = root.children_recursive

    '''
    brawl bones keys are relative to the parent.
    Blender bone keys are relative to the bone's rest pose.

    When applying the bindpose for animation export,
    we must convert from Blender's [local to rest] to [local to parent].
    '''

    #edit_bone matrix is in armature space
    #need to get it in parent space (local to parent)
    #for edit_bone in root_children_recursive:
    #    bind_matrices[edit_bone.name] = edit_bone.parent.matrix.inverted() * edit_bone.matrix
    #bind_matrices[root.name] = root.matrix
    
    #for key, val in bind_matrices.items(): 
    #    bind_matrices[key] = val.copy()

    '''
    IMPORTANT: ... blender matrices aren't like C# structs... they're more like a reference.
                    Thus, we need to create a copy, otherwise the desired matrix values won't be cached.
    '''
    #for key, val in bind_matrices.items():
    #    bind_matrices[key] = val.copy()


    context.view_layer.objects.active  = context.active_object
    context.active_object.select_set(True)
    
    inv_scales_arm = {}
    inv_scales_local = {}
    for bone in root_children_recursive:
        scale = bone['brawl_bind_inv_scale']
        inv_scales_arm[bone.name] = Matrix.Scale(1/(scale[0]),4,(1,0,0)) *  Matrix.Scale(1/(scale[1]),4,(0,1,0)) *  Matrix.Scale(1/(scale[2]),4,(0,0,1))

    scale = root['brawl_bind_inv_scale']
    inv_scales_arm[root.name] = Matrix.Scale(1/(scale[0]),4,(1,0,0)) *  Matrix.Scale(1/(scale[1]),4,(0,1,0)) *  Matrix.Scale(1/(scale[2]),4,(0,0,1))

    for bone in root_children_recursive:
        inv_scales_local[bone.name] = inv_scales_arm[bone.parent.name].inverted() *inv_scales_arm[bone.name]
    inv_scales_local[root.name]=inv_scales_arm[root.name]

    bpy.ops.object.mode_set(mode= 'POSE')

    root = get_root_pose_bone(context.active_object)
    pose_bones = [root]
    pose_bones.extend(root.children_recursive)
    
    if remove_bind_pose:
        for pose_bone in pose_bones:
            bind_matrices[pose_bone.name].invert()
        
    bpy.ops.pose.select_all(context, action='SELECT')
    keying_set = [s for s in context.scene.keying_sets_all if s.bl_idname == 'LocRotScale'][0]

    #...for now... I'll just go to each frame and re-key it instead of calculating only necessary keys
    frame_start = context.scene.frame_preview_start
    frame_end = context.scene.frame_preview_end

    if remove_bind_pose:
        for frame_current in reversed(range(frame_start, frame_end + 1)):
            context.scene.frame_set(frame_current)
            
            for pose_bone in pose_bones:
                bind =  bind_matrices[pose_bone.name]
                matrix =  pose_bone.matrix_basis

                #rescale the pose spaces so the (ex) translation magnitudes are correct, necessar since Blender editbones don't store scales.
                pose_bone.matrix_basis =   inv_scales_arm[pose_bone.name].inverted()  * bind  * matrix * inv_scales_arm[pose_bone.name]
               
            bpy.ops.anim.keyframe_insert_menu(type=keying_set.bl_idname, confirm_success=False)
    else:
        for frame_current in reversed(range(frame_start, frame_end + 1)):
            context.scene.frame_set(frame_current)
            
            for pose_bone in pose_bones:
                bind =  bind_matrices[pose_bone.name]
                matrix =  pose_bone.matrix_basis

                #rescale the pose spaces so the (ex) translation magnitudes are correct, necessar since Blender editbones don't store scales. 
                matrix = inv_scales_arm[pose_bone.name] * matrix * inv_scales_arm[pose_bone.name].inverted() 

                pose_bone.matrix_basis = bind * matrix

            bpy.ops.anim.keyframe_insert_menu(type=keying_set.bl_idname, confirm_success=False)

def poll_bindpose_import(context):
    return (context.active_object is not None) and (isinstance(context.active_object.data, Armature))

def update_import_items(self, context):
    if ('MODEL' not in self.import_items) and (not poll_bindpose_import(context)):
        self.msg_to_user = 'ERROR: Brawl armature not active selection'
    else:
        self.msg_to_user = ''

def filepath_utf8(filepath):
    as_bytes = os.fsencode(filepath)
    as_utf8 = as_bytes.decode('utf-8', "replace")
    return as_utf8

def collada_read_bone_binds(context, filepath):

    #https://docs.python.org/3.5/library/xml.etree.elementtree.html#xml.etree.ElementTree.Element.itertext

    dae = ET.parse(filepath)
    root = dae.getroot()

    xmlns = re.match(r'{.*}',root.tag).group(0)

    tag_skin = xmlns + 'skin'
    tag_source = xmlns + 'source'
    tag_name_array = xmlns + 'Name_array'
    tag_float_array = xmlns + 'float_array'

    id_postfix_joint = '_JointArr'
    id_postfix_matrices = '_MatArr'

    skin_nodes = [node for node in root.iter(tag_skin)]
    skin_datas = {}
    for skin_node in skin_nodes:
        polygon_name = skin_node.attrib['source']
        #print()
        #print(repr(polygon_name))

        bone_names = []
        bone_bind_matrices = []
        for skin_child_node in skin_node:
            #print(repr(skin_child_node))
            if skin_child_node.tag == tag_source:
                for source_child_node in skin_child_node:
                    #print('-->' + repr(source_child_node))
                    if  source_child_node.tag == tag_name_array and source_child_node.attrib['id'].endswith(id_postfix_joint):
                        bone_names = source_child_node.text.split(' ')
                    if source_child_node.tag == tag_float_array and source_child_node.attrib['id'].endswith(id_postfix_matrices):
                        float_array = [float(float_str) for float_str in source_child_node.text.split(' ')]
                        matrix_count = int(source_child_node.attrib['count']) // 16

                        for i in range(0,matrix_count):
                            k = i * 16
                            bone_bind_matrices.append((float_array[k+0:k+4],float_array[k+4:k+8],float_array[k+8:k+12],float_array[k+12:k+16]))
        
        bind_data = {}
        for i in range(0,len(bone_names)):
            bone_name = bone_names[i]
            bind_matrix_floats = bone_bind_matrices[i]

            #print(repr(bone_name))
            #print(repr(bind_matrix_floats))
            bind_data[bone_name] = bind_matrix_floats
        
        skin_datas[polygon_name] = bind_data

    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = context.active_object.data.edit_bones

    for polygon_name,bind_datas in skin_datas.items():
        for bone_name,bind_matrix in bind_datas.items():

            #bug: i don't know why the collada importer fails to import HeadItmN for kirby...
            if bone_name not in edit_bones:
                print('>>warning: collada failed to import bone: ' +bone_name)
                continue
            else:
                edit_bones[bone_name]['bind_'+polygon_name] = bind_matrix

    context.active_object['bind_polygons'] = ['bind_' + name for name in skin_datas]
    
    bpy.ops.object.mode_set(mode='OBJECT')

def matrix_trs(translation, quaternion, scale):
    return Matrix.Translation(translation) @ quaternion.to_matrix().to_4x4() @ Matrix.Scale(scale[0],4,(1,0,0))@ Matrix.Scale(scale[1],4,(0,1,0))@ Matrix.Scale(scale[2],4,(0,0,1))

def matrix_to_sequence(matrix):
    return (*matrix[0],*matrix[1],*matrix[2],*matrix[3])

def action_from_maya_anim_format(context, anim_name, anim_file_lines,from_maya):


    #this code fixes the problem where the imported animation may be offseted (rot, loc and/or scale)
    #if the character is not already in rest pose. I don't know why it happens.
    prev_auto = context.scene.tool_settings.use_keyframe_insert_auto
    context.scene.tool_settings.use_keyframe_insert_auto = False

    bpy.ops.object.mode_set(mode='POSE')

    bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.pose.loc_clear()
    bpy.ops.pose.rot_clear()
    bpy.ops.pose.scale_clear()


    context.scene.tool_settings.use_keyframe_insert_auto = prev_auto


    #remove comments, semicolons and leading and trailing whitespace
    anim_file_lines = trim_comments(anim_file_lines)

    for i, line in enumerate_start(0, anim_file_lines):
        anim_file_lines[i] = line.replace(';', '').strip()

    print('extracting header attributes')
    #group the lines into more convenient structures
    anim_start_index, header_lines = read_until(0, anim_file_lines, 'anim ')

    '''
    treats start/endTime and Unitless variations as equivalent to frame index.
    only supports 'deg' and 'rad' angular units
    '''
    frame_start_line = ''
    frame_end_line = ''
    angular_unit_line = ''
    for line in header_lines:
        if line.startswith('startTime') or line.startswith('startUnitless'):
            frame_start_line = line
        elif line.startswith('endTime') or line.startswith('endUnitless'):
            frame_end_line = line
        elif line.startswith('angularUnit'):
            angular_unit_line = line

    print('extracting animation datas')
    #(anim_line, [animData attribute lines],[animData key lines] )
    anim_info_lines = []
    iterator = enumerate_start(anim_start_index, anim_file_lines)
    for i, line in iterator:
        if line.startswith('anim ') and (len(line.split(' ')) >= 7):
            #T: added a check for any anim lines without animData since it changed from 2014 to 2015 .anim files
            anim_line = line
            animData_attr_lines = None
            animData_key_lines = None

            if anim_file_lines[i+1].startswith('animData'):
                '''if exists, animData must follow the anim line  according to format specs'''
                #use same iterator so the current_index of both loops are affected
                #note that entering this loop gives the next line after 'animData {' as desired
                i, animData_attr_lines = read_until(i + 2, anim_file_lines,'keys')
                #note: the next i+1 skips the ' keys' line
                '''assumes keys open-bracket occurs on same line'''
                i, animData_key_lines = read_until(i + 1, anim_file_lines,'}')

                iterator.current_index = i + 1

            anim_info_lines.append((anim_line, animData_attr_lines, animData_key_lines))


    print('parsing header')

    frame_start = line_value_int(frame_start_line)
    frame_end = line_value_int(frame_end_line)
    angular_unit = line_value_str(angular_unit_line)
    angle_scaling = math.pi/180.0 if 'deg' in angular_unit else 1
    
    print('parsing animation datas')

    attr_to_component = {'translate' : 'location',\
                         'rotate' : 'rotation_euler',\
                         'scale' : 'scale'}
    #allows conversion of rads to degrees w/o affecting conversion of translation and scale.
    component_scaling = {'translate' : 1,\
                         'rotate' : angle_scaling,\
                         'scale' : 1}
    axis_to_index = {'X': 0,'x':0, 'Y':1,'y':1,'Z':2,'z':2 , 'W':3,'w':3}
    handle_type = {'fixed' : 'FREE', 'auto' : 'AUTO', 'linear':'AUTO'}

    #(bone_name, channel data path, channel array_index, [key infos])
    #keyinfo: (key, handle_left, handle_right)
    #handle: (type, angle, weight)
    parsed_anim_infos = []
    for anim_info in anim_info_lines:
        anim_line = anim_info[0]
        animData_key_lines = anim_info[2]

        anim_line_split = anim_line.split(' ')
        anim_line_split_len = len(anim_line_split)

        if anim_line_split_len < 7:
            '''not supported. Insufficient info to determine joint to animate'''
            print('warning: line format not supported ({0})'.format(anim_line))
        #if anim_line_split_len == 5:
        #    '''not supported. Insufficient info to determine joint to animate'''
        #    #name may be an attribute name.. or a node name, according to docs
        #    #tag, name, row, child, attr_index = anim_line_split
        #    print('warning: line format not supported ({0})'.format(anim_line))
        #elif anim_line_split_len == 4:
        #    '''not supported. Insufficient info to determine joint to animate'''
        #    #tag, row, child, attr_index = anim_line_split
        #    print('warning: line format not supported ({0})'.format(anim_line))
        #elif anim_line_split_len == 3:
        #    '''not supported. Insufficient info to determine joint to animate'''
        #    #tag, row, child, attr_index = anim_line_split
        #    print('warning: line format not supported ({0})'.format(anim_line))

        else:
            _, _, attr_leaf_name, node_name, _, _, _ = anim_line_split

            attr_name = attr_leaf_name[:-1]
            array_index = axis_to_index[attr_leaf_name[-1]]
            if array_index == 3:
                component = 'rotation_quaternion'
            else:
                
                if attr_name not in attr_to_component:
                    print('attribute not supported, skipped: ' + anim_line )
                    continue 

                component = attr_to_component[attr_name]
            key_value_scaling = component_scaling[attr_name]
            data_path = 'pose.bones[\"{0}\"].{1}'.format(node_name, component)

            '''
            currently, i'm going to assume that the imported rotation type and order matches the imported armature data.
            ...also just going to assume the rotation is euler and order:XYZ ...
            '''
            parsed_keyinfos = []

            #(bone_name, channel data path, channel array_index, [key infos])
            parsed_anim_infos.append((node_name, data_path, array_index, parsed_keyinfos))
            for key_line in animData_key_lines:
                key_line_split = key_line.split(' ')
                #key_line_len = len(key_line_split)
                splice_offset = 0
                frame, value, type_left, type_right, _, _, _= key_line_split[0 + splice_offset: 7 + splice_offset]

                angle_left = '0'
                weight_left = '0'
                angle_right = '0'
                weight_right = '0'

                if type_left == 'fixed':
                    angle_left, weight_left = key_line_split[7 + splice_offset:9 + splice_offset]

                    if type_right == 'fixed':
                        angle_right, weight_right = key_line_split[9 + splice_offset:12 + splice_offset]

                elif type_right == 'fixed':
                    angle_right, weight_right = key_line_split[7 + splice_offset:9 + splice_offset]

                #if node_name == 'HipN' and data_path == 'pose.bones["HipN"].location' and array_index==1:
                #    print('angle:{0} weight:{1}'.format(angle_left,weight_left))
                #(key, handle_left, handle_right)    
                parsed_keyinfos.append(((int(frame),float(value) * key_value_scaling),\
                                        (handle_type[type_left],float(angle_left)* angle_scaling, float(weight_left)),\
                                        (handle_type[type_right],float(angle_right)* angle_scaling, float(weight_right))))


    print('creating animation datas')

    #..this operator does not work..
    #bpy.ops.action.new(context_override)
    action = context.blend_data.actions.new(anim_name)

    if context.active_object.animation_data is None:
        context.active_object.animation_data_create()

    context.active_object.animation_data.action = action

    context.scene.frame_preview_start = frame_start
    context.scene.frame_preview_end = frame_end
    context.scene.use_preview_range = True

    '''
    unique_bone_names = set([info[0] for info in parsed_anim_infos])
    creating bone groups and fcurves done automatically when bindpose is keyframed. 
    no need to do that manually anymore.
    '''
    #bone_groups = {}
    #for bone_name in unique_bone_names:
    #    anim_group = action.groups.new(bone_name)
    #    anim_group.name = bone_name
    #    bone_groups[bone_name] = anim_group

    #for channel_info in parsed_anim_infos:
    #    bone_name = channel_info[0]
    #    channel_data_path = channel_info[1]
    #    channel_array_index = channel_info[2]

    #    channel_curve = action.fcurves.new(channel_data_path, index=channel_array_index, action_group=bone_groups[bone_name].name)
    

    #replace missing keyframes for the first key of each bone with the bind pose value
    #since BrawlCrate doesn't export the bindpose as a keyframe, it treats bindpose as identity
    #afterwards, imported keys will overwrite bindpose keys. Missing keyframes will leave the bindpose keys.
    #-
    #for exported animations, since BC treats missing keys as bind, we don't have to do so manually again
    keyframe_bindpose(context,frame_start)
    
    for channel_info in parsed_anim_infos:
        bone_name = channel_info[0]
        channel_data_path = channel_info[1]
        channel_array_index = channel_info[2]
        channel_keyinfos = channel_info[3]


        #user:readme:todo:bug: sometimes collada importer misses some bones? Ex: Kirby's HeadItmN bone isn't imported...
        #since that bone seems unimportant, i'm not too worried about it. 
        if bone_name not in action.groups:
            continue 

        channel_curve = [fcurve for fcurve in action.groups[bone_name].channels if ((fcurve.data_path == channel_data_path) and (fcurve.array_index == channel_array_index ))][0]
        #print('{0} {1} {2}'.format(bone_name, channel_data_path, channel_array_index))
        for key_info in channel_keyinfos:
            
            #print(key_info)
            key = key_info[0]
            handle_left, handle_right = (key_info[1], key_info[2])
            handle_left_angle, handle_right_angle = (handle_left[1], handle_right[1])
            weight_left, weight_right = (handle_left[2], handle_right[2])

            #for rotation componemnts, blender treats writes as if they're in radians, the unit of the rotation component., yet (i think) the ratio is already in degrees/frames
            handle_left_offset =  [-1, -tan(handle_left_angle)]
            handle_right_offset = [1, tan(handle_right_angle)]
 
            
            #I think the tangent is given in units of degrees, so we have to convert to rads for blender?
            if channel_data_path.endswith('rotation_euler'):
                handle_left_offset[1] = handle_left_offset[1] * (math.pi/180.0)
                handle_right_offset[1] = handle_right_offset[1] * (math.pi/180.0)
                
            #maya testing
            if from_maya:
                #https://download.autodesk.com/us/maya/2010help/API/class_m_fn_anim_curve.html
                ''' 
                 One important note is how the outgoing and incoming tangents directions for a key are saved internally and in the Maya Ascii file format.
                 Instead of being specified as points, the tangent directions are specified as vectors. The outgoing tangent direction at P1 is specified and 
                 saved as the vector 3*(P2 - P1) and the incoming tangent direction is specified and saved as the vector 3*(P4 - P3).
                '''
                #(tan1,weight1) -> 3 * (p4-p3) -> 3*(current_co - handle_left)
                #(tan2,weight2) -> 3 * (p2-p1) -> 3*(handle_right - current_co)
                #in_vec = Vector((weight_left,handle_left_angle))
                #out_vec = Vector((weight_right,handle_right_angle))
                #handle_left_offset = -(in_vec * (1.0/3.0))  
                #handle_right_offset = (out_vec * (1.0/3.0))  
                handle_left_offset =  Vector((-1, -tan(handle_left_angle) ))
                handle_right_offset = Vector((1, tan(handle_right_angle) ))
    
                handle_left_offset = handle_left_offset.normalized()* weight_left
                handle_right_offset = handle_right_offset.normalized()* weight_right
                
                if channel_data_path.endswith('rotation_euler'):
                    handle_left_offset[1] = handle_left_offset[1] * (math.pi/180.0)
                    handle_right_offset[1] = handle_right_offset[1] * (math.pi/180.0)
                
            #if bone_name == 'HipN' and channel_data_path == 'pose.bones["HipN"].rotation_euler' and channel_array_index==1:
            #    print('F{3} angle:{0} weight:{1} yoffset:{2} '.format(handle_left_angle * 180.0/math.pi,(weight_left-1),handle_left_offset[1],key[0]))



            key_frame = channel_curve.keyframe_points.insert(key[0],key[1])
            key_frame.interpolation ='BEZIER'# 'CONSTANT'#'BEZIER'
            key_frame.co = key
            #print(key_frame.co)
            key_frame.handle_left_type = handle_left[0]
            key_frame.handle_right_type = handle_right[0]
            
            if handle_left[0] != 'AUTO':
                key_frame.handle_left = (key[0] + handle_left_offset[0], key[1] + handle_left_offset[1])
            if handle_right[0] != 'AUTO':
                key_frame.handle_right = (key[0] + handle_right_offset[0], key[1] + handle_right_offset[1])

                
        if not from_maya:
            for i in range(0,len(channel_curve.keyframe_points)):
                keyframe = channel_curve.keyframe_points[i]
                co = keyframe.co 

                if keyframe.handle_left_type != 'AUTO' and i > 0:
                    keyframe_left = channel_curve.keyframe_points[i-1]
                    offset = abs(co[0] - keyframe_left.co[0]) 
                    keyframe.handle_left = (co[0] - (1.0/3.0) * offset ,co[1] + (keyframe.handle_left[1] - co[1]) * offset/3.0 ) 
                if  keyframe.handle_right_type != 'AUTO' and i < len(channel_curve.keyframe_points) - 1:
                    keyframe_right = channel_curve.keyframe_points[i+1]
                    offset = abs(co[0] - keyframe_right.co[0])
                    keyframe.handle_right = (keyframe_right.co[0] - (2.0/3.0) * (keyframe_right.co[0] - co[0]),co[1] + (keyframe.handle_right[1] - co[1]) * offset/3.0)


    print('.. finished parsing maya animation')

    return action

def check_collections(search_name):
    found = False
    for collection in bpy.data.collections:
        if collection.name == search_name:
            found = True
    return found

def obj_in_collection(obj, col):
    in_collection = False
    for collection in obj.users_collection:
        if collection.name == col:
            in_collection = True
    return in_collection

#-----------------------------------------

def bind_matrices_get(context, filepath):
    collada_read_bone_binds(context,filepath)

    #https://docs.python.org/3.5/library/xml.etree.elementtree.html#xml.etree.ElementTree.Element.itertext

    dae = ET.parse(filepath)
    root = dae.getroot()

    xmlns = re.match(r'{.*}',root.tag).group(0)
    tag_node = xmlns + 'node'

    #assumes first joint in dae is root, since xml nodes follow a heirarchy
    root_name = [node for node in root.iter(tag_node) if node.attrib['type'] == 'JOINT'][0].attrib['name']
    context.active_object['brawl_root'] = root_name

    bpy.ops.object.mode_set(mode='EDIT')
    edit_root = context.active_object.data.edit_bones[root_name]
    edit_bones = [edit_root]
    edit_bones.extend(edit_root.children_recursive)

    
    bind_polygon_name = context.active_object['bind_polygons'][0]
    #apply the imported bindpose
    for bone in edit_bones:
        basis_matrix =Matrix(bone[bind_polygon_name]).inverted()

        bind_loc,bind_rot,bind_scale = basis_matrix.decompose()
        # attempt to fix scaling problem (with expectation that animated scales and distance wont be correct but rotation will: didn't work. a mirrored body part has wrong rotation)bind_loc.x,bind_loc.y,bind_loc.z = bind_loc.x / bind_scale.x,bind_loc.y/ bind_scale.y,bind_loc.z/ bind_scale.z
        basis_matrix = matrix_trs(bind_loc,bind_rot,bind_scale)
        #although BC frame 0 may show (1,1,1) bone scales, their bind matrices may have scaling anyways. This would show that for debugging purposes. (non-identity scales are not supported and wont be)
        #print('{0} scale:{1}'.format(bone.name,bind_scale))

        bone.length=1
        bone.matrix=  basis_matrix.copy()
        basis_matrix = basis_matrix
        bone['brawl_bind'] = matrix_to_sequence(basis_matrix)
        bone['brawl_bind_inv_scale'] = bind_scale

def get_root_pose_bone(active_object):
    root_name = active_object['brawl_root']
    brawl_root = None#[pose_bone for pose_bone in active_object.pose.bones if (pose_bone.name == root_name)]

    try:
        brawl_root = active_object.pose.bones[root_name]
    except Exception as _:
        raise Exception('missing \'brawl_root\' bone name in custom property of active object.')

    return brawl_root

def create_identityRigBC(context):
    active_object = context.active_object
    
    bpy.ops.object.mode_set(mode='EDIT')
    edit_root = get_root_edit_bone(active_object)
    bones = [bone.name for bone in edit_root.children_recursive]
    bones.append(edit_root.name)
    parents = {bone.name: bone.parent.name for bone in active_object.data.bones if bone.parent}
    
    bind_matrices = calculate_local_bind_matrices(context.active_object)
    arm_bind_matrices = {}
    for editbone in active_object.data.edit_bones:
        arm_bind_matrices[editbone.name] = matrix_from_sequence(editbone['brawl_bind'])
    
    bpy.ops.object.mode_set(mode='OBJECT')
    dummy_armature = bpy.data.armatures.new(name='Proxy_' +active_object.data.name)
    dummy_object = bpy.data.objects.new(name='Proxy_' + active_object.name,object_data = dummy_armature)
    dummy_object["BRT"] = "PROXY"
    context.scene.proxy = 'Proxy_' + active_object.name
    #context.scene.objects.link(dummy_object)
    context.view_layer.active_layer_collection.collection.objects.link(dummy_object)
    dummy_object.matrix_world = active_object.matrix_world.copy()
    dummy_object.show_in_front=True

    context.view_layer.objects.active  = dummy_object
    dummy_object.select_set(True)

    bpy.ops.object.mode_set(mode='EDIT')
    matrix_identity = Matrix.Scale(1,4,Vector((0,1,0)))
    
    for bone_name in bones:
        new_edit_bone = dummy_armature.edit_bones.new(bone_name)
        new_edit_bone.select = new_edit_bone.select_head=new_edit_bone.select_tail=True
        new_edit_bone.tail = (0,1,0)
        new_edit_bone.matrix = matrix_identity.copy()
        new_edit_bone['brawl_bind'] =matrix_to_sequence( arm_bind_matrices[bone_name])
        
    #print(repr(parents))
    for bone_name in bones:
        if bone_name in parents:
            parent_name = parents[bone_name]
            dummy_armature.edit_bones[bone_name].parent = dummy_armature.edit_bones[parent_name]

    bpy.ops.object.mode_set(mode='POSE')
    
    dummy_pose_bones = dummy_object.pose.bones
    active_pose_bones = active_object.pose.bones

    arm_matrices = {}
    for bone_name in bones:
        pose_bone = dummy_pose_bones[bone_name]
        bind = bind_matrices[bone_name]
        pose_bone.matrix_basis = bind
        pose_bone.rotation_mode = 'XYZ'
        #used for clearing loc/rot/scale
        pose_bone['brawl_local_bind_pose'] = matrix_to_sequence(bind)
        #pose_bone['brawl_bind'] = matrix_to_sequence( arm_bind_matrices[bone_name])

    update_scene_frame_set()
    context.view_layer.depsgraph.update()
    #context.scene.update()
    for bone_name in bones:
        arm_matrices[bone_name] = dummy_pose_bones[bone_name].matrix.copy()
    
    context.view_layer.objects.active  = active_object
    bpy.ops.object.mode_set(mode='POSE')
    
    for bone_name in bones:
        active_pose_bone = active_pose_bones[bone_name]
        
        #constraints works fine since both rigs have same world-space TPose
        con  =active_pose_bone.constraints.new('COPY_LOCATION')
        con.influence=1
        con.mute=False
        #con.active=True
        con.target= dummy_object
        con.subtarget = bone_name
        con.owner_space = 'WORLD'
        con.target_space='WORLD'
        con.use_x = True
        con.use_y = True
        con.use_z = True

        con_drv = con.driver_add('enabled').driver
        con_drv.type = 'SCRIPTED'
        var = con_drv.variables.new()
        var.name = 'loc'
        var.targets[0].id = bpy.data.objects['Con.Proxy']
        var.targets[0].data_path='location.x'
        con_drv.expression = ' loc < 0'

        con  =active_pose_bone.constraints.new('COPY_ROTATION')
        con.influence=1
        con.mute=False
        #con.active=True
        con.target= dummy_object
        con.subtarget = bone_name
        con.owner_space = 'WORLD'
        con.target_space='WORLD'
        con.use_x = True
        con.use_y = True
        con.use_z = True

        con_drv = con.driver_add('enabled').driver
        con_drv.type = 'SCRIPTED'
        var = con_drv.variables.new()
        var.name = 'loc'
        var.targets[0].id = bpy.data.objects['Con.Proxy']
        var.targets[0].data_path='location.x'
        con_drv.expression = ' loc < 0'

        #the constrained armature's world pose bones do not have the bind scale
        #Using an offset=bindscale with a copyscale is insufficient since .. for w/e reason, Blender combines the scales as a sum, instead of the expected multiplication 
        #con  =active_pose_bone.constraints.new('COPY_SCALE')
        #con.influence=1
        #con.mute=False
        ##con.active=True
        #con.target= dummy_object
        #con.subtarget = bone_name
        #con.owner_space = 'WORLD'
        #con.target_space='WORLD'
        #con.use_x = True
        #con.use_y = True
        #con.use_z = True
 
        #the transform constraint, with extrapolation, allows the multiplied scaling result, along with accounting for the missing owner posebone bind scale.
        con  =active_pose_bone.constraints.new('TRANSFORM')
        _,_,bscale = arm_bind_matrices[bone_name].decompose()
        con.influence=1
        con.mute=False
        #con.active=True
        con.target= dummy_object
        con.subtarget = bone_name
        con.owner_space = 'WORLD'
        con.target_space='WORLD'
        con.map_from = 'SCALE'
        con.map_to = 'SCALE'
        con.use_motion_extrapolate= True
        con.map_to_x_from = 'X'
        con.map_to_y_from = 'Y'
        con.map_to_z_from = 'Z'
        con.from_min_x_scale = 0
        con.from_min_y_scale = 0
        con.from_min_z_scale = 0
        con.from_max_x_scale = bscale.x
        con.from_max_y_scale = bscale.y
        con.from_max_z_scale = bscale.z
        con.to_min_x_scale = 0
        con.to_min_y_scale = 0
        con.to_min_z_scale = 0
        con.to_max_x_scale = 1
        con.to_max_y_scale = 1
        con.to_max_z_scale = 1

        con_drv = con.driver_add('enabled').driver
        con_drv.type = 'SCRIPTED'
        var = con_drv.variables.new()
        var.name = 'loc'
        var.targets[0].id = bpy.data.objects['Con.Proxy']
        var.targets[0].data_path='location.x'
        con_drv.expression = ' loc < 0.01'

    context.view_layer.objects.active  = dummy_object
    dummy_object['brawl_root'] = active_object['brawl_root']
    dummy_object.select_set(True)

    active_object.parent = dummy_object
    active_object.parent_type = 'OBJECT'
    active_object.matrix_local = Matrix.Identity(4)
    #active_object.hide_select=True
    #active_object.hide_viewport=True
    active_object.select_set(False)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    dummy_object.select_set(True)

def brawlcrate_anim_import(context, filepath,from_maya):
    '''
    imports action directly
    '''

    filename = get_filename(filepath)

    print('reading in file..' + filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        anim_file_lines = f.readlines()
    print('finished reading file')

    print("converting to action..")
    action = action_from_maya_anim_format(context, filename, anim_file_lines,from_maya)
    print("... finished converting to action")

    print('.. finished importing maya animation: ' + filename)

    return action

def matrix_from_sequence(sequence):
    return Matrix((sequence[0:4],sequence[4:8],sequence[8:12],sequence[12:16]))

#-----------------------------------------

class OBJECT_OT_brawlcrate_collada_import(Operator, ImportHelper):

    bl_idname = "brawlcrate.collada_import"
    bl_label = "BrawlCrate Collada Import"
    bl_options = {'REGISTER', 'UNDO'}

    # ExportHelper mixin class uses this
    filename_ext = '.dae'
    

    filter_glob : StringProperty(
            default='*.dae',
            options={'HIDDEN'},
            maxlen=255,
            )
    import_units : BoolProperty(
            default=True,
            name='Import Units'
            )
    import_items : EnumProperty(
            name='Import',
            default= {'MODEL','BIND_POSE'},
            options = {'ENUM_FLAG'},
            items=[
                ('MODEL', 'model',''),
                ('BIND_POSE','bind pose','')
            ],
            update=update_import_items
            )
    msg_to_user : StringProperty(
            name='',
            default = '',
    )
    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        import_items = self.import_items
        filepath = self.filepath

        if 'MODEL' in import_items:
            bpy.ops.wm.collada_import(filepath=filepath,find_chains=False, import_units=self.import_units)
            
            #the importer selects all imported objects
            #need to select the armature for the bind_pose_import()
            #todo:bug: if there are multiple armatures in the .dae, then the wrong armature may be chosen. (Lucariosk)
            root_object = [obj for obj in context.selected_objects if obj.parent is None and isinstance(obj.data,bpy.types.Armature)]
            #todo: whats the point of len(root_object) > 0? typo? should be 1?
            if len(root_object) > 0:
                root_object = root_object[0]

            if not check_collections('Proxy'):
                collection = bpy.data.collections.new('Proxy')
                bpy.context.scene.collection.children.link(collection)

            if not check_collections('Model'):
                collection = bpy.data.collections.new('Model')
                bpy.context.scene.collection.children.link(collection)

            collections = bpy.context.view_layer.layer_collection.children

            for collection in collections:
                if collection.name == 'Proxy':
                    bpy.context.view_layer.active_layer_collection = collection

            for obj in context.selected_objects:
                if obj.type == 'ARMATURE':
                    if not obj_in_collection(obj, 'Proxy'):
                        bpy.data.collections['Proxy'].objects.link(obj)
                else:
                    if not obj_in_collection(obj, 'Model'):
                        bpy.data.collections['Model'].objects.link(obj)

            
            root_object.select_set(True)
            #set as active object so that mode_set works as intended
            context.view_layer.objects.active = root_object
            #context.scene.objects.active = root_object
            #print('model imported')
            #print()
            root_object.name = "DAE_Armature"
            root_object["BRT"] = "TARGET"

        if 'BIND_POSE' in import_items:

            if not poll_bindpose_import(context):
                raise Exception('ERROR: Brawl armature needs to be the active selection')
        
            print('parsing dae for bindpose: ' ,filepath_utf8(filepath))
            bind_matrices_get(context, filepath)
            
            #assumes brawl rotations are all euler and XYZ ordered
            bpy.ops.object.mode_set(mode='POSE')
            pose_brawl_root = get_root_pose_bone(context.active_object)
            pose_bones = [pose_brawl_root]
            pose_bones.extend(pose_brawl_root.children_recursive)
            for pose_bone in pose_bones:
                pose_bone.rotation_mode = 'XYZ'

            print('finished applying bindpose.')
            
            #user:readme: this is the rig to import to, export from, animate with
            create_identityRigBC(context)

            if not check_collections('Proxy'):
                collection = bpy.data.collections.new('Proxy')
                bpy.context.scene.collection.children.link(collection)

            for obj in context.selected_objects:
                if not obj_in_collection(obj, 'Proxy'):
                    bpy.data.collections['Proxy'].objects.link(obj)
        
        bpy.context.active_object.parent = bpy.data.objects['Con.Scale']

        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                for region in area.regions:
                    if region.type == 'WINDOW':
                        override = {'area': area, 'region': region, 'edit_object': bpy.context.edit_object}
                        bpy.ops.view3d.view_selected(override)
        return {'FINISHED'}

class POSE_OT_brawlcrate_anim_import(Operator, ImportHelper):
    bl_idname = "brawlcrate.anim_import"
    bl_label = "BrawlCrate .Anim Import"
    bl_options = {'REGISTER', 'UNDO'}
    
    files : CollectionProperty(
        name="File Path",
        type=OperatorFileListElement,
        )
    directory : StringProperty(
            subtype='DIR_PATH',
            )
    # ExportHelper mixin class uses this
    filename_ext = ".anim"

    filter_glob : StringProperty(
            default="*.anim",
            options={'HIDDEN'},
            maxlen=255,  # Max internal buffer length, longer would be clamped.
            )
    #anim_from_maya = BoolProperty(name='ANIM From Maya',default=False)

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None) and isinstance(context.active_object.data, Armature)

    def execute(self, context):
        
        directory = self.directory
        filepaths = [os.path.join(directory, file_elem.name) for file_elem in self.files if os.path.isfile(os.path.join(directory, file_elem.name))]
        
        for filepath in filepaths:
            brawlcrate_anim_import(context, filepath,False)#self.anim_from_maya)
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                for region in area.regions:
                    if region.type == 'WINDOW':
                        override = {'area': area, 'region': region, 'edit_object': bpy.context.edit_object}
                        bpy.ops.view3d.view_selected(override)
        return {'FINISHED'}

#-----------------------------------------