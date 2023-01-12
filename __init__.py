# Load the script, or reload it

import bpy
import datetime

bl_info = {
    'name' : 'MRTrix3 tck format',
    'author' : 'Daniel Blezek',
    'description' : "Import .tck tractography streamline files",
    'support' : 'COMMUNITY',
    'category' : 'Import-Export',
    'version' : (1, 0, 0),
    'blender' : (3,0, 0)
}

if "bpy" in locals():
    import importlib
    if "export_ply" in locals():
        importlib.reload(export_ply)
    if "import_ply" in locals():
        importlib.reload(import_ply)


import bpy
from bpy.props import (
    CollectionProperty,
    StringProperty,
    BoolProperty,
    FloatProperty, IntProperty,
)
from bpy_extras.io_utils import (
    ImportHelper,
    ExportHelper,
    axis_conversion,
    orientation_helper,
)


class ImportTCK(bpy.types.Operator, ImportHelper):
    """Load a TCK geometry file"""
    bl_idname = "import_tck.tck"
    bl_label = "Import TCK"
    bl_options = {'UNDO'}

    files: CollectionProperty(
        name="File Path",
        description="File path used for importing the tck file",
        type=bpy.types.OperatorFileListElement,
    )

    # Hide opertator properties, rest of this is managed in C. See WM_operator_properties_filesel().
    # hide_props_region: BoolProperty(
    #     name="Hide Operator Properties",
    #     description="Collapse the region displaying the operator settings",
    #     default=False,
    # )

    directory: StringProperty()

    filename_ext = ".tck"
    filter_glob: StringProperty(default="*.tck", options={'HIDDEN'})

    skip_points:  IntProperty(name="Max points", description="limit the number of imported streamline points, 0 is use all",
                               default=0, min=0)
    radius: FloatProperty(name="Radius",
                          description="Radius of imported stremlines",
                          default=1,
                          min=0,
                          soft_max=10,
                          )
    in_mm: BoolProperty(
        name="In mm",
        description="Import in actual size in millimeters, if unchecked, import in meters",
        default=True
    )


    def execute(self, context):
        import os
        from . import import_tck

        context.window.cursor_set('WAIT')

        paths = [
            os.path.join(self.directory, name.name)
            for name in self.files
        ]

        if not paths:
            paths.append(self.filepath)

        for path in paths:
            import_tck.load(self, context, self.properties, path)

        context.window.cursor_set('DEFAULT')

        return {'FINISHED'}




def menu_func_import(self, context):
    self.layout.operator(ImportTCK.bl_idname, text="MRtrix streamlines (.tck)")


classes = (
    ImportTCK,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()