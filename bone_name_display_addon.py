bl_info = {
    "name": "Bone Name Display",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (2, 82, 0),
    "location": "View3D > Sidebar > Bone Name",
    "description": "Shows the name of the selected bone(s) as on-screen text next to the bone, in Edit and Pose mode",
    "warning": "",
    "doc_url": "",
    "category": "3D View",
}

import bpy
import blf
from bpy_extras import view3d_utils


# module-level state (survives across operator calls, reset on addon reload)
_handle = None


def get_selected_bones_info(context):
    """Return a list of (name, world_position, is_active) for selected bones
    in Edit Armature or Pose mode of the active armature object."""
    result = []
    obj = context.active_object

    if not obj or obj.type != 'ARMATURE':
        return result

    mat_world = obj.matrix_world

    if context.mode == 'EDIT_ARMATURE':
        active_name = obj.data.edit_bones.active.name if obj.data.edit_bones.active else None
        for eb in obj.data.edit_bones:
            if eb.select or eb.select_head or eb.select_tail:
                pos = mat_world @ ((eb.head + eb.tail) / 2)
                result.append((eb.name, pos, eb.name == active_name))

    elif context.mode == 'POSE':
        active_name = obj.data.bones.active.name if obj.data.bones.active else None
        for pb in context.selected_pose_bones or []:
            pos = mat_world @ ((pb.head + pb.tail) / 2)
            result.append((pb.name, pos, pb.name == active_name))

    return result


def draw_callback_px():
    context = bpy.context
    region = context.region
    rv3d = context.region_data

    if region is None or rv3d is None:
        return

    bones_info = get_selected_bones_info(context)
    if not bones_info:
        return

    font_id = 0
    blf.size(font_id, 16, 72)  # Blender 2.82: blf.size(font_id, size, dpi)

    for name, world_pos, is_active in bones_info:
        coord_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, world_pos)
        if coord_2d is None:
            continue

        if is_active:
            blf.color(font_id, 1.0, 0.6, 0.0, 1.0)  # orange for active bone
        else:
            blf.color(font_id, 1.0, 1.0, 0.2, 1.0)  # yellow for other selected bones

        blf.position(font_id, coord_2d.x + 8, coord_2d.y + 8, 0)
        blf.draw(font_id, name)


class VIEW3D_OT_toggle_bone_name_display(bpy.types.Operator):
    """Toggle the bone name overlay in the 3D viewport"""
    bl_idname = "view3d.toggle_bone_name_display"
    bl_label = "Toggle Bone Name Display"

    def execute(self, context):
        global _handle

        if _handle is None:
            _handle = bpy.types.SpaceView3D.draw_handler_add(
                draw_callback_px, (), 'WINDOW', 'POST_PIXEL'
            )
            self.report({'INFO'}, "Bone name display enabled")
        else:
            bpy.types.SpaceView3D.draw_handler_remove(_handle, 'WINDOW')
            _handle = None
            self.report({'INFO'}, "Bone name display disabled")

        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        return {'FINISHED'}


class VIEW3D_PT_bone_name_display_panel(bpy.types.Panel):
    bl_label = "Bone Name Display"
    bl_idname = "VIEW3D_PT_bone_name_display"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bone Name"

    def draw(self, context):
        layout = self.layout
        enabled = _handle is not None
        text = "Disable" if enabled else "Enable"
        icon = 'HIDE_OFF' if enabled else 'HIDE_ON'
        layout.operator("view3d.toggle_bone_name_display", text=text, icon=icon)
        layout.label(text="Works in Edit Mode and Pose Mode.")


classes = (
    VIEW3D_OT_toggle_bone_name_display,
    VIEW3D_PT_bone_name_display_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    global _handle
    if _handle is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_handle, 'WINDOW')
        _handle = None

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
