bl_info = {
    "name": "Armature Import/Export",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (2, 82, 0),
    "location": "File > Import/Export",
    "description": "Import and Export Armature bones with hierarchy",
    "warning": "",
    "doc_url": "",
    "category": "Import-Export",
}

import bpy
import os
import json
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy.props import StringProperty, BoolProperty


class ArmatureIO(object):
    """Class to handle importing and exporting of an armature. 
    Handles bones and bone parenting only."""
    
    def __init__(self):
        pass

    def exportArmature(self, armature=None, export_dir='/tmp', bones=[], file_name=''):
        """
        @param armature - name for armature the data object name
        @param export_dir - directory in which to save armature json. if this is a full path to a file name it uses this instead of the file_name argument
        @param bones - optional list of bones to export. if empty it exports all bones in armature
        @param file_name - optional name for json file to save such as Armature.json. if it is not provided it uses the armature name
        """
        if not os.path.isdir(export_dir) and not os.path.isfile(export_dir):
            print("could not find export path %s. enter one that exists" % export_dir)
            return
            
        if not armature in bpy.data.objects:
            print("requires an armature name. the data object name to exist")
            return
        
        dat_dict = {}  # what we want to export
        
        # need to have armature selected
        self._selectOnlyThing(thing=armature)
        
        # compiling the data for armature
        bpy.ops.object.mode_set(mode='EDIT')
        bone_names = [eb.name for eb in bpy.data.objects[armature].data.edit_bones]  # default to all bones in armature
        if bones:
            bone_names = bones
        
        for bone in bone_names:
            edit_bone_data = {}
            pose_bone_data = {}
            
            # edit bone data
            # need to be in edit mode for getting parent - assumes armature is selected
            bpy.ops.object.mode_set(mode='EDIT')
            eb = bpy.data.objects[armature].data.edit_bones[bone]
            
            # adding edit bone attributes here
            edit_bone_data['head'] = tuple(eb.head)  # (0,3,5)
            edit_bone_data['tail'] = tuple(eb.tail)
            edit_bone_data['roll'] = eb.roll  # in radians
            edit_bone_data['parent'] = eb.parent.name if eb.parent else ''
            ##
            
            # pose bone data
            bpy.ops.object.mode_set(mode='POSE')
            pb = bpy.data.objects[armature].pose.bones[bone]
            
            # adding pose bone attributes here
            pose_bone_data['location'] = tuple(pb.location)  # (4,5,6)
            pose_bone_data['scale'] = tuple(pb.scale)
            pose_bone_data['rotation_mode'] = pb.rotation_mode
            pose_bone_data['rotation'] = tuple(pb.rotation_euler)
            if pb.rotation_mode == 'QUATERNION':
                pose_bone_data['rotation'] = tuple(pb.rotation_quaternion)
            pose_bone_data['custom_shape'] = pb.custom_shape.name if pb.custom_shape else ''  # animator curve for bone
            pose_bone_data['custom_shape_scale'] = pb.custom_shape_scale
            ##
            
            dat_dict[bone] = {'edit_bone_data': edit_bone_data, 'pose_bone_data': pose_bone_data}
        
        # exporting armature to json
        ##
        # if directory provided is a full path to a file name use it
        export_fullpath = ''
        if os.path.isfile(export_dir):
            export_fullpath = export_dir
        else:
            # use the file_name if it exists
            export_file_name = ''
            if file_name:
                export_file_name = file_name
            else:
                # use the armature name to figure out file name
                armature_edit = armature.replace(' ', '_')
                export_file_name = armature_edit + '.json'
                
            export_fullpath = os.path.join(export_dir, export_file_name)
        
        ##
        outDir = os.path.dirname(export_fullpath)
        if not os.path.exists(outDir):
            print('Requires an out directory that exists to write armature file %s' % outDir)
            return
        ##
        
        ## adding armature name
        output_dict = {}
        output_dict["armature"] = armature
        output_dict["bones"] = dat_dict
        ##
        
        print("exporting >>> %s to file name: %s" % (output_dict, export_fullpath))
        
        with open(export_fullpath, "w") as outf:
            json.dump(output_dict, outf, indent=4)

        return True
        
    def _importMakeArmature(self, armatureName):
        """
        @param armatureName - str data object name for armature
        """
        if not armatureName:
            print("_importMakeArmature requires an armature name")
            return
            
        if armatureName in bpy.data.objects:
            return
        # make the armature
        arm_dat = bpy.data.armatures.new(armatureName)
        arm_obj = bpy.data.objects.new(armatureName, arm_dat)
        arm_obj.data = arm_dat
        # Blender 2.80+ way to link objects
        bpy.context.collection.objects.link(arm_obj)
        bpy.context.view_layer.objects.active = arm_obj
        
    
    def importArmature(self, file_path=''):
        """
        @param file_path - str file path to import
        """
        if not os.path.exists(file_path):
            print("could not find %s skipping" % file_path)
            return False
    
        info_dict = {}
        with open(file_path) as f:
            info_dict = json.load(f)
        print("read armature info>>", info_dict)
        
        # check if armature exists if it doesnt make an empty one
        armature = info_dict.get("armature")
        if not armature:
            print("using default armature name")
            armature = "na_default_armature"  # temp for backwards compatibility
            
        if not armature in bpy.data.objects:
            print("making armature because it doesnt exist")
            self._importMakeArmature(armature)
        
        return self.importArmatureFromDict(armature=armature, data_dict=info_dict.get("bones"))
    
    
    def importArmatureFromDict(self, armature=None, data_dict=None, use_bones=[]):
        """
        @param armature - armature name - the data object name
        @param data_dict - see export for the format it is a dictionary with edit bone and pose bone information
        @param use_bones - when specified it limits import to only provide bone names
        """
        if not data_dict:
            print("requires data dictionary with bone information")
            return False
    
        if not armature in bpy.data.objects:
            print("couldnt find armature - so making one")
            self._importMakeArmature(armature)
            
            
        dat_dict = {}
        dat_dict = data_dict
        print("using armature info>>", dat_dict)
        
    
        # ensure in edit mode of armature - Blender 2.80+ way
        bpy.context.view_layer.objects.active = bpy.data.objects[armature]
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
            
        for bone, dat in dat_dict.items():
            
            # only import specified bones in input parameter
            if use_bones:
                if bone not in use_bones:
                    continue
            
            print(bone)
            edit_bone_data = dat.get('edit_bone_data') or None
            head = edit_bone_data.get('head') or None
            tail = edit_bone_data.get('tail') or None
            roll = edit_bone_data.get('roll') or 0.0
            
            pose_bone_data = dat.get('pose_bone_data') or None
            location = pose_bone_data.get('location') or None
            scale = pose_bone_data.get('scale') or None
            rotation_mode = pose_bone_data.get('rotation_mode') or None
            rotation = pose_bone_data.get('rotation') or None
            custom_shape = pose_bone_data.get('custom_shape') or ''
            custom_shape_scale = pose_bone_data.get('custom_shape_scale') or 1.0
            
            bpy.ops.object.mode_set(mode='EDIT', toggle=False)
            bone_obj = None
            # if it exists already use it.
            if bone in bpy.data.objects[armature].data.edit_bones:
                bone_obj = bpy.data.objects[armature].data.edit_bones[bone]
            if not bone_obj:
                # make edit bone from scratch
                bone_obj = bpy.data.objects[armature].data.edit_bones.new(bone)
                
            # position edit bone
            bone_obj.head = head
            bone_obj.tail = tail
            bone_obj.roll = roll
            
            # position pose bone
            bpy.ops.object.mode_set(mode='POSE')
            pb = bpy.data.objects[armature].pose.bones[bone]
            pb.location = location
            pb.scale = scale
            pb.rotation_mode = rotation_mode
            if rotation_mode != 'QUATERNION':
                pb.rotation_euler = rotation
            else:
                pb.rotation_quaternion = rotation
            # if custom shape doesnt exist dont try to add it to bone
            if custom_shape in bpy.data.objects:
                pb.custom_shape = bpy.data.objects[custom_shape]
                pb.custom_shape_scale = custom_shape_scale
                bpy.data.objects[armature].data.bones[bone].show_wire = True  # show wire
    
    
        # do the bone parenting at end so have all bones created
        # ensure in edit mode of armature
        bpy.context.view_layer.objects.active = bpy.data.objects[armature]
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        
        for bone, dat in dat_dict.items():
            # only import specified bones in input parameter
            # if use_bones:
            #    if bone not in use_bones:
            #        continue
            
            # allowing any existing bone to be considered for parenting to support successive build workflow
            if not bone in bpy.data.objects[armature].data.edit_bones:
                continue
                
            bone_obj = bpy.data.objects[armature].data.edit_bones[bone]
            edit_bone_data = dat.get('edit_bone_data') or None
            parent = edit_bone_data.get('parent') or None
            
            # skip parenting to parent if cannot find it in scene
            if not parent:
                continue
                
            if not parent in bpy.data.objects[armature].data.edit_bones:
                continue
                
            if parent:
                bone_obj.parent = bpy.data.objects[armature].data.edit_bones[parent]
        
        bpy.ops.object.mode_set(mode='OBJECT')
        return True


    def _selectOnlyThing(self, thing=None):
        # might need to be in object mode
        bpy.ops.object.mode_set(mode="OBJECT")
        if thing:
            thing_obj = bpy.data.objects.get(thing)
            if not thing_obj:
                print("couldn't find {0} to select".format(thing))
                return
            # make it only selection
            bpy.ops.object.select_all(action='DESELECT')
            thing_obj.select_set(True)  # Blender 2.80+ API
            bpy.context.view_layer.objects.active = thing_obj


# ======================== EXPORT OPERATOR ========================

class EXPORT_OT_armature(bpy.types.Operator, ExportHelper):
    """Export Armature bones to JSON"""
    bl_idname = "export_armature.json"
    bl_label = "Export Armature (.json)"
    bl_options = {'PRESET'}
    
    filename_ext = ".json"
    filter_glob: StringProperty(
        default="*.json",
        options={'HIDDEN'},
        maxlen=255,
    )

    def execute(self, context):
        # Get the selected armature
        obj = context.active_object
        
        if not obj or obj.type != 'ARMATURE':
            self.report({'ERROR'}, "Please select an Armature object")
            return {'FINISHED'}
        
        arm_io = ArmatureIO()
        try:
            arm_io.exportArmature(
                armature=obj.name,
                export_dir=self.filepath
            )
            self.report({'INFO'}, f"Armature exported to {self.filepath}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Export failed: {str(e)}")
            return {'FINISHED'}


# ======================== IMPORT OPERATOR ========================

class IMPORT_OT_armature(bpy.types.Operator, ImportHelper):
    """Import Armature bones from JSON"""
    bl_idname = "import_armature.json"
    bl_label = "Import Armature (.json)"
    bl_options = {'PRESET'}
    
    filename_ext = ".json"
    filter_glob: StringProperty(
        default="*.json",
        options={'HIDDEN'},
        maxlen=255,
    )

    def execute(self, context):
        arm_io = ArmatureIO()
        try:
            result = arm_io.importArmature(file_path=self.filepath)
            if result:
                self.report({'INFO'}, f"Armature imported from {self.filepath}")
            else:
                self.report({'ERROR'}, "Import failed")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Import failed: {str(e)}")
            return {'FINISHED'}


# ======================== MENU FUNCTIONS ========================

def menu_export(self, context):
    self.layout.operator(EXPORT_OT_armature.bl_idname, text="Armature (.json)")


def menu_import(self, context):
    self.layout.operator(IMPORT_OT_armature.bl_idname, text="Armature (.json)")


# ======================== ADDON REGISTRATION ========================

classes = (
    EXPORT_OT_armature,
    IMPORT_OT_armature,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.TOPBAR_MT_file_export.append(menu_export)
    bpy.types.TOPBAR_MT_file_import.append(menu_import)


def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(menu_export)
    bpy.types.TOPBAR_MT_file_import.remove(menu_import)
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
