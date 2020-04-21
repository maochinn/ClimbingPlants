import bpy


class ClimbingPlantPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_CLIMBING_PLANT"
    bl_label = "Climbing plant"
    bl_category = "Plant Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator('plant.seeding', text="Seeding")
        row = layout.row()
        row.operator('plant.growth', text="growing")
