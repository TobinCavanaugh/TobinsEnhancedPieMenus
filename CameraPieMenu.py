import bpy
from bpy.types import Menu, Operator, Panel
from mathutils import Vector


# --- Custom Operators ---

class VIEW3D_OT_align_selected_camera_to_view(Operator):
    """Align the active camera's position and rotation to match the current viewport perspective"""
    bl_idname = "view3d.align_selected_camera_to_view"
    bl_label = "Align Selected Camera to View"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return (
            context.active_object is not None 
            and context.active_object.type == 'CAMERA' 
            and context.region_data is not None
        )
    
    def execute(self, context):
        obj = context.active_object
        rv3d = context.region_data
        
        obj.matrix_world = rv3d.view_matrix.inverted()
        return {'FINISHED'}


class VIEW3D_OT_align_view_to_selected_camera(Operator):
    """Snap the viewport camera to look through the active camera without changing the active scene camera"""
    bl_idname = "view3d.align_view_to_selected_camera"
    bl_label = "Align View to Selected Camera"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (
            context.active_object is not None 
            and context.active_object.type == 'CAMERA' 
            and context.space_data is not None 
            and context.space_data.type == 'VIEW_3D'
        )

    def execute(self, context):
        obj = context.active_object
        space = context.space_data
        rv3d = context.region_data

        space.camera = obj
        rv3d.view_perspective = 'CAMERA'
        return {'FINISHED'}


class VIEW3D_OT_align_camera_to_cursor(Operator):
    """Rotate the active camera to point directly at the 3D Cursor"""
    bl_idname = "view3d.align_camera_to_cursor"
    bl_label = "Point Camera at 3D Cursor"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'CAMERA'

    def execute(self, context):
        camera = context.active_object
        cursor_loc = context.scene.cursor.location
        direction = cursor_loc - camera.location
        
        if direction.length_squared == 0.0:
            self.report({'WARNING'}, "Camera and 3D Cursor share the exact same location")
            return {'CANCELLED'}
        
        rot_quat = direction.to_track_quat('-Z', 'Y')
        camera.rotation_euler = rot_quat.to_euler()
        return {'FINISHED'}


class VIEW3D_OT_level_camera_horizon(Operator):
    """Reset camera roll (Z-axis rotation) to align it horizontally with the viewport horizon"""
    bl_idname = "view3d.level_camera_horizon"
    bl_label = "Level Camera Horizon"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'CAMERA'

    def execute(self, context):
        camera = context.active_object
        matrix = camera.matrix_world
        forward_vector = -matrix.col[2].to_3d().normalized()

        if abs(forward_vector.dot(Vector((0, 0, 1)))) > 0.999:
            self.report({'WARNING'}, "Camera is looking vertically straight up or down; horizon cannot be calculated safely")
            return {'CANCELLED'}

        rot_quat = forward_vector.to_track_quat('-Z', 'Y')
        camera.rotation_euler = rot_quat.to_euler()
        return {'FINISHED'}


class VIEW3D_OT_new_camera_from_view(Operator):
    """Create and select a brand new camera aligned to the current viewport perspective"""
    bl_idname = "view3d.new_camera_from_view"
    bl_label = "New Camera from View"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.region_data is not None

    def execute(self, context):
        rv3d = context.region_data
        bpy.ops.object.select_all(action='DESELECT')

        cam_data = bpy.data.cameras.new(name="Shot_Cam")
        cam_obj = bpy.data.objects.new(name="Shot_Cam", object_data=cam_data)
        context.collection.objects.link(cam_obj)

        cam_obj.matrix_world = rv3d.view_matrix.inverted()
        cam_obj.select_set(True)
        context.view_layer.objects.active = cam_obj

        self.report({'INFO'}, f"Created and active camera set to: {cam_obj.name}")
        return {'FINISHED'}


class VIEW3D_OT_toggle_lock_camera(Operator):
    """Toggle Lock Camera to View and automatically snap the viewport perspective to the active camera"""
    bl_idname = "view3d.toggle_lock_camera_and_align"
    bl_label = "Lock Camera to View"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (
            context.space_data is not None 
            and context.space_data.type == 'VIEW_3D'
            and context.active_object is not None
            and context.active_object.type == 'CAMERA'
        )

    def execute(self, context):
        space = context.space_data
        rv3d = context.region_data
        camera = context.active_object

        # Toggle the native lock state
        new_state = not space.lock_camera
        space.lock_camera = new_state

        # If we just locked it, ensure the viewport aligns to look through this camera
        if new_state:
            space.camera = camera
            if rv3d:
                rv3d.view_perspective = 'CAMERA'
            self.report({'INFO'}, f"Camera locked and view aligned to: {camera.name}")
        else:
            self.report({'INFO'}, "Camera lock disabled")

        return {'FINISHED'}


# --- UI Panels ---

class VIEW3D_PT_camera_quick_actions(Panel):
    """Simplified Camera Masking controls in the 3D Viewport Sidebar (N-panel)"""
    bl_label = "Camera Quick Actions"
    bl_idname = "VIEW3D_PT_camera_quick_actions"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Camera"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'CAMERA'

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        cam_data = obj.data

        col = layout.column(align=True)
        col.prop(cam_data, "show_passepartout", text="Show Mask")
        
        sub = col.column(align=True)
        sub.active = cam_data.show_passepartout
        sub.prop(cam_data, "passepartout_alpha", text="Opacity", slider=True)


class CAMERA_PT_quick_actions_properties(Panel):
    """Simplified Camera Masking controls in the Camera Properties Data tab"""
    bl_label = "Camera Quick Actions"
    bl_idname = "CAMERA_PT_quick_actions_properties"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        return context.camera is not None

    def draw(self, context):
        layout = self.layout
        cam_data = context.camera

        col = layout.column(align=True)
        col.prop(cam_data, "show_passepartout", text="Show Mask")
        
        sub = col.column(align=True)
        sub.active = cam_data.show_passepartout
        sub.prop(cam_data, "passepartout_alpha", text="Opacity", slider=True)


# --- Pie Menu ---

class VIEW3D_MT_camera_management_pie(Menu):
    bl_label = "Camera Actions"
    bl_idname = "VIEW3D_MT_camera_management_pie"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        # 1. WEST (Left)
        pie.operator("view3d.align_selected_camera_to_view", text="Align Camera to View")

        # 2. EAST (Right)
        pie.operator("view3d.align_view_to_selected_camera", text="Align View to Camera")

        # 3. SOUTH (Bottom) - Empty spacer
        pie.separator()

        # 4. NORTH (Top)
        pie.operator("view3d.align_camera_to_cursor", text="Point at 3D Cursor")

        # 5. NORTH-WEST (Top-Left) - Custom Toggle Lock & Align Operator
        space = context.space_data
        is_locked = space.lock_camera if space else False
        icon = 'LOCKED' if is_locked else 'UNLOCKED'
        pie.operator("view3d.toggle_lock_camera_and_align", text="Lock Camera to View", icon=icon)

        # 6. NORTH-EAST (Top-Right)
        pie.operator("view3d.new_camera_from_view", text="New Camera from View")

        # 7. SOUTH-WEST (Bottom-Left)
        pie.operator("view3d.level_camera_horizon", text="Level Horizon")

        # 8. SOUTH-EAST (Bottom-Right) - Simplified Passepartout Controls
        obj = context.active_object
        if obj and obj.type == 'CAMERA':
            box = pie.box()
            col = box.column(align=True)
            col.prop(obj.data, "show_passepartout", text="Show Mask")
            
            sub = col.column(align=True)
            sub.active = obj.data.show_passepartout
            sub.prop(obj.data, "passepartout_alpha", text="Opacity", slider=True)
        else:
            pie.separator()


# --- Registration & Keymaps ---

classes = (
    VIEW3D_OT_align_selected_camera_to_view,
    VIEW3D_OT_align_view_to_selected_camera,
    VIEW3D_OT_align_camera_to_cursor,
    VIEW3D_OT_level_camera_horizon,
    VIEW3D_OT_new_camera_from_view,
    VIEW3D_OT_toggle_lock_camera,
    VIEW3D_PT_camera_quick_actions,
    CAMERA_PT_quick_actions_properties,
    VIEW3D_MT_camera_management_pie,
)

addon_keymaps = []

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new('wm.call_menu_pie', 'C', 'PRESS', alt=True)
        kmi.properties.name = "VIEW3D_MT_camera_management_pie"
        addon_keymaps.append((km, kmi))

def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    for cls in classes:
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass


if __name__ == "__main__":
    unregister()
    register()