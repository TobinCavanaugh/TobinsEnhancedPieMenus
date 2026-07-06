import bpy
from bpy.types import Menu

# 1. Operator for MatCap Normals (SW Slot)
class VIEW3D_OT_set_matcap_normal(bpy.types.Operator):
    """Switch shading to Solid with MatCap Normals check map (for analyzing surface orientation)"""
    bl_idname = "view3d.set_matcap_normal"
    bl_label = "Switch to MatCap Normals"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        shading = context.space_data.shading
        shading.type = 'SOLID'
        shading.light = 'MATCAP'
        shading.studio_light = 'check_normal+y.exr'
        return {'FINISHED'}

# 2. Operator for Default Solid View (Right Slot)
class VIEW3D_OT_set_shading_solid_default(bpy.types.Operator):
    """Switch shading to standard Solid view with default studio lighting and Material colors"""
    bl_idname = "view3d.set_shading_solid_default"
    bl_label = "Switch to Default Solid"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        shading = context.space_data.shading
        shading.type = 'SOLID'
        shading.light = 'STUDIO'
        shading.studio_light = 'Default'
        shading.color_type = 'MATERIAL'
        return {'FINISHED'}

# 3. Operator for Random Color Solid View (SE Slot)
class VIEW3D_OT_set_shading_solid_random(bpy.types.Operator):
    """Switch shading to Solid view with random colors assigned to each object"""
    bl_idname = "view3d.set_shading_solid_random"
    bl_label = "Switch to Random Solid"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        shading = context.space_data.shading
        shading.type = 'SOLID'
        shading.light = 'STUDIO'
        shading.studio_light = 'Default'
        shading.color_type = 'RANDOM'
        return {'FINISHED'}

# 4. Operator for Eevee Engine (NW Slot)
class VIEW3D_OT_set_engine_eevee(bpy.types.Operator):
    """Switch the current scene render engine to Eevee"""
    bl_idname = "view3d.set_engine_eevee"
    bl_label = "Switch Engine to Eevee"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.scene.render.engine = 'BLENDER_EEVEE' 
        return {'FINISHED'}

# 5. Operator for Cycles Engine + GPU Auto-detection (NE Slot)
class VIEW3D_OT_set_engine_cycles(bpy.types.Operator):
    """Switch the current scene render engine to Cycles and auto-detect/enable GPU compute"""
    bl_idname = "view3d.set_engine_cycles"
    bl_label = "Switch Engine to Cycles (GPU)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        scene.render.engine = 'CYCLES'
        
        try:
            # Access the built-in Cycles addon preferences package
            cycles_prefs = context.preferences.addons['cycles'].preferences
            
            # Refresh list of hardware devices
            cycles_prefs.get_devices()
            
            # Find an available hardware device type that isn't 'NONE'
            # Iterates through standard options: ('OPTIX', 'CUDA', 'HIP', 'ONEAPI', 'METAL')
            best_type = 'NONE'
            for device_type in cycles_prefs.get_device_types(context):
                if device_type[0] != 'NONE':
                    best_type = device_type[0]
                    break
            
            # If a GPU toolkit backend is supported by the system, activate it
            if best_type != 'NONE':
                cycles_prefs.compute_device_type = best_type
                scene.cycles.device = 'GPU'
                self.report({'INFO'}, f"Cycles set to GPU Compute ({best_type})")
            else:
                scene.cycles.device = 'CPU'
                self.report({'WARNING'}, "No compatible GPU found. Defaulted to CPU.")
                
        except Exception as e:
            # Fallback direct assignment if preferences structure throws an error
            scene.cycles.device = 'GPU'
            print(f"GPU preferences fallback triggered: {e}")
            
        return {'FINISHED'}


# 6. Re-create the Shading Pie Menu
class CUSTOM_VIEW3D_MT_shading_pie(Menu):
    """Custom pie menu to quickly change shading types and switch render engines"""
    bl_label = "Shading / Engine"
    bl_idname = "VIEW3D_MT_shading_pie"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        shading = context.space_data.shading
        engine = context.scene.render.engine

        # --- STATE EVALUATION ---
        is_solid = (shading.type == 'SOLID')
        is_studio = (shading.light == 'STUDIO')
        
        state_matcap_normal = is_solid and (shading.light == 'MATCAP') and (shading.studio_light == 'check_normal+y.exr')
        state_solid_default = is_solid and is_studio and (shading.color_type != 'RANDOM')
        state_solid_random = is_solid and is_studio and (shading.color_type == 'RANDOM')
        
        state_eevee = (engine == 'BLENDER_EEVEE')
        state_cycles = (engine == 'CYCLES')

        # --- PIE MENU LAYOUT ---
        # Fixed Order: Left, Right, Bottom, Top, NW, NE, SW, SE
        
        # LEFT: Wireframe
        pie.prop_enum(shading, "type", value='WIREFRAME', text="Wireframe", icon='SHADING_WIRE')
        
        # RIGHT: Custom Default Solid
        pie.operator("view3d.set_shading_solid_default", text="Solid", icon='SHADING_SOLID', depress=state_solid_default)
        
        # BOTTOM: Material Preview
        pie.prop_enum(shading, "type", value='MATERIAL', text="Material Preview", icon='SHADING_TEXTURE')
        
        # TOP: Rendered
        pie.prop_enum(shading, "type", value='RENDERED', text="Rendered", icon='SHADING_RENDERED')
        
        # NORTHWEST: Set Eevee
        pie.operator("view3d.set_engine_eevee", text="Use Eevee", icon='RENDER_STILL', depress=state_eevee)
        
        # NORTHEAST: Set Cycles
        pie.operator("view3d.set_engine_cycles", text="Use Cycles", icon='PROPERTIES', depress=state_cycles)
        
        # SOUTHWEST: Custom MatCap Normals
        pie.operator("view3d.set_matcap_normal", text="MatCap Normals", icon='ANTIALIASED', depress=state_matcap_normal)
        
        # SOUTHEAST: Custom Random Colors
        pie.operator("view3d.set_shading_solid_random", text="Random Colors", icon='COLOR', depress=state_solid_random)


# Registration
classes = (
    VIEW3D_OT_set_matcap_normal,
    VIEW3D_OT_set_shading_solid_default,
    VIEW3D_OT_set_shading_solid_random,
    VIEW3D_OT_set_engine_eevee,
    VIEW3D_OT_set_engine_cycles,
    CUSTOM_VIEW3D_MT_shading_pie,
)

def register():
    try:
        bpy.utils.unregister_class(bpy.types.VIEW3D_MT_shading_pie)
    except Exception:
        pass
        
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except Exception as e:
            print(f"Failed to register {cls.__name__}: {e}")

def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass

if __name__ == "__main__":
    register()