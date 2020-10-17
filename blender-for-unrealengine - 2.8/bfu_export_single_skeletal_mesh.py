#====================== BEGIN GPL LICENSE BLOCK ============================
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.	 If not, see <http://www.gnu.org/licenses/>.
#  All rights reserved.
#
#======================= END GPL LICENSE BLOCK =============================


import bpy
import time
import math

import importlib
from . import bfu_WriteText
importlib.reload(bfu_WriteText)

from . import bfu_Basics
importlib.reload(bfu_Basics)
from .bfu_Basics import *

from . import bfu_Utils
importlib.reload(bfu_Utils)
from .bfu_Utils import *

from . import bfu_ExportUtils
importlib.reload(bfu_ExportUtils)
from .bfu_ExportUtils import *

def ExportSingleSkeletalMesh(originalScene, dirpath, filename, obj):
	'''
	#####################################################
			#SKELETAL MESH
	#####################################################
	'''
	#Export a single Mesh

	scene = bpy.context.scene
	addon_prefs = bpy.context.preferences.addons["blender-for-unrealengine"].preferences
	
	filename = ValidFilenameForUnreal(filename)
	s = CounterStart()
	
	if	bpy.ops.object.mode_set.poll():
		bpy.ops.object.mode_set(mode = 'OBJECT')

	
	SelectParentAndDesiredChilds(obj)
	AddSocketsTempName(obj)
	DuplicateSelectForExport()	
			
	if addon_prefs.correctExtremUVScale == True:
		SavedSelect = GetCurrentSelect()
		if GoToMeshEditMode() == True:
			CorrectExtremeUV(2)
		bpy.ops.object.mode_set(mode = 'OBJECT')
		SetCurrentSelect(SavedSelect)
		
	ApplyNeededModifierToSelect()
		
		
	UpdateNameHierarchy(GetAllCollisionAndSocketsObj(bpy.context.selected_objects))
	active = bpy.context.view_layer.objects.active
	if active.ExportAsProxy == True:
		ApplyProxyData(active)
	
	ApplyExportTransform(active)
	
	##This will recale the rig and unit scale to get a root bone egal to 1
	ShouldRescaleRig = GetShouldRescaleRig()
	if ShouldRescaleRig == True:
				
		rrf = GetRescaleRigFactor() #rigRescaleFactor
		savedUnitLength = bpy.context.scene.unit_settings.scale_length
		bpy.context.scene.unit_settings.scale_length *= 1/rrf
		ApplySkeletalExportScale(active, rrf)
		

	absdirpath = bpy.path.abspath(dirpath)
	VerifiDirs(absdirpath)
	fullpath = os.path.join( absdirpath , filename )
	meshType = GetAssetType(active)
			
	SetSocketsExportTransform(active)
	RemoveDuplicatedSocketsTempName(active)
	TryToApplyCustomSocketsName(active)

	
	#Set rename temporarily the Armature as "Armature"
	oldArmatureName = RenameArmatureAsExportName(active)
	
	RemoveAllConsraints(active)
	bpy.context.object.data.pose_position = 'REST'
	
	bpy.ops.export_scene.fbx(
		filepath=fullpath,
		check_existing=False,
		use_selection=True,
		global_scale=GetObjExportScale(active),
		object_types={'ARMATURE', 'EMPTY', 'CAMERA', 'LIGHT', 'MESH', 'OTHER'},
		use_custom_props=addon_prefs.exportWithCustomProps,
		mesh_smooth_type="FACE",
		add_leaf_bones=False,
		use_armature_deform_only=active.exportDeformOnly,
		bake_anim=False,
		use_metadata=addon_prefs.exportWithMetaData,
		primary_bone_axis = active.exportPrimaryBaneAxis,
		secondary_bone_axis = active.exporSecondaryBoneAxis,	
		axis_forward = active.exportAxisForward,
		axis_up = active.exportAxisUp,
		bake_space_transform = False
		)
	
	##This will recale the rig and unit scale to get a root bone egal to 1
	if ShouldRescaleRig == True:
		#Reset Curve an unit
		bpy.context.scene.unit_settings.scale_length = savedUnitLength
		
	#Reset armature name

	ResetArmatureName(active, oldArmatureName)
	CleanDeleteObjects(bpy.context.selected_objects)
	
	RemoveSocketsTempName(obj)
	
	exportTime = CounterEnd(s)
	MyAsset = originalScene.UnrealExportedAssetsList.add()
	MyAsset.assetName = filename
	MyAsset.assetType = meshType
	MyAsset.exportPath = absdirpath
	MyAsset.exportTime = exportTime
	MyAsset.object = obj
	return MyAsset