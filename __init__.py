bl_info = {
    "name" : "AutoBackup",
    "author" : "HydraBladeZ",
    "description" : "A simple and configurable addon to backup your blend file.",
    "blender" : (3, 5, 0),
    "version" : (1, 0, 0),
    "location" : "View3D",
    "warning" : "",
    "category" : "Object"
}

import bpy
import os
import time


class AUTO_BACKUP_PT_Panel(bpy.types.Panel):
    bl_label = "AutoBackup"
    bl_idname = "AUTO_BACKUP_PT_Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AutoBackup"

    def draw(self, context):
        layout = self.layout
        props = context.scene.AutoBackupProperties

        #Start/Stop
        if context.scene.AutoBackupProperties.Backup:
            row = layout.row()
            row.operator("object.autobackup", text="Stop Auto Backup", icon="PAUSE")
            self.layout.label(text="Auto Backup is running.")
        else:
            row = layout.row()
            row.operator("object.autobackup", text="Start Auto Backup", icon="PLAY")
            row = layout.row()
            row.prop(context.scene.AutoBackupProperties, "FileName")
            row = layout.row()
            row.prop(context.scene.AutoBackupProperties, "SavePath")
        
        row = layout.row()
        row.prop(context.scene.AutoBackupProperties, "SaveInterval")
        row = layout.row()
        row.prop(context.scene.AutoBackupProperties, "MaxBackups")




class AutoBackupProperties(bpy.types.PropertyGroup):
    FileName: bpy.props.StringProperty(
        name="File Name",
        description="The name of the backup file, if left empty, the name of the current file will be used",
        default="",
    )
    SavePath: bpy.props.StringProperty(
        name="Save Path",
        description="The path where the backup files will be saved",
        default="",
        subtype="DIR_PATH",
    )
    SaveInterval: bpy.props.IntProperty(
        name="Save Interval",
        description="The interval between each backup in seconds",
        default=300,
        min=60,
    )
    MaxBackups: bpy.props.IntProperty(
        name="Max Backups",
        description="The maximum number of backups to keep\n IF THE NUMBER OF BACKUPS IS GREATER THAN THIS NUMBER, THE OLDEST BACKUP WILL BE DELETED",
        default=10,
        min=1,
    )
    Backup: bpy.props.BoolProperty(
        name="Backup",
        description="Start making backups.",
        default=False,
    )


class AutoBackup(bpy.types.Operator):
    bl_idname = "object.autobackup"
    bl_label = "AutoBackup"
    bl_description = "Start making backups."

    def execute(self, context):
        props = context.scene.AutoBackupProperties
        if props.Backup == True:
            props.Backup = False
            bpy.ops.wm.autobackup_timer('INVOKE_DEFAULT')
        else:
            #check if the path is valid
            if os.path.isdir(props.SavePath):
                props.Backup = True
                bpy.ops.wm.autobackup_timer('INVOKE_DEFAULT')
                self.report({'INFO'}, "Auto Backup started.")
            else:
                self.report({'ERROR'}, "Invalid path.")
                return {'CANCELLED'}
            
        return {'FINISHED'}
    
        
class AutoBackupTimer(bpy.types.Operator):
    bl_idname = "wm.autobackup_timer"
    bl_label = "AutoBackupTimer"
    bl_description = "AutoBackupTimer"

    _timer = None
    _last_save = 0

    def modal(self, context, event):
        props = context.scene.AutoBackupProperties
        if not props.Backup:
            self.cancel(context)
            return {'CANCELLED'}
        if event.type == 'TIMER':
            if time.time() - self._last_save > props.SaveInterval:
                self.save(context, props)
                self._last_save = time.time()
        return {'PASS_THROUGH'}
    

    def save(self, context, props):
        name = ''
        if props.FileName == '':
            if bpy.data.filepath == '':
                name = 'untitled'
            else:
                name = bpy.path.display_name_from_filepath(bpy.data.filepath)
        else:
            name = props.FileName

        fullPath = f"{props.SavePath}/{name}_{time.strftime('%Y-%m-%d_%H-%M-%S')}.blend"

        #check if the number of backups is greater than the max
        if len(os.listdir(props.SavePath)) > props.MaxBackups:
            #delete the oldest backup by date of creation
            oldest = min(os.listdir(props.SavePath), key=lambda f: os.path.getctime(os.path.join(props.SavePath, f)))
            os.remove(f"{props.SavePath}/{oldest}")

        #save the file as a copy
        bpy.ops.wm.save_as_mainfile(filepath=fullPath, copy=True)
        self._last_save = 0
        self.report({'INFO'}, "Auto Backup saved.")

    
    def invoke(self, context, event):
        props = context.scene.AutoBackupProperties
        self._timer = context.window_manager.event_timer_add(props.SaveInterval, window=context.window)
        self._last_save = time.time()
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    

    def cancel(self, context):
        context.window_manager.event_timer_remove(self._timer)
        self._timer = None
        self.report({'INFO'}, "Auto Backup stopped.")        

    
def register():
    bpy.utils.register_class(AutoBackup)
    bpy.utils.register_class(AUTO_BACKUP_PT_Panel)
    bpy.utils.register_class(AutoBackupProperties)
    bpy.types.Scene.AutoBackupProperties = bpy.props.PointerProperty(type=AutoBackupProperties)
    bpy.utils.register_class(AutoBackupTimer)



def unregister():
    bpy.utils.unregister_class(AutoBackup)
    bpy.utils.unregister_class(AUTO_BACKUP_PT_Panel)
    bpy.utils.unregister_class(AutoBackupProperties)
    bpy.utils.unregister_class(AutoBackupTimer)
    
    del bpy.types.Scene.AutoBackupProperties
