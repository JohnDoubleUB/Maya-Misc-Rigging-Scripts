import maya.cmds as ma


#Create custom properties for rigs in order for them to be baked down using an animation bake down tool (This is part of preparing rig animation for use on the CFX rig)
def makeRigAsset(assetType=None,charName=None,rigType=None,lockAllAttrs=True):
    sel = ma.ls(sl=True)
    animRig = sel[0]
    nameDataArray = [assetType, charName, rigType, ma.date(d=True), ma.date(t=True)]
    stringDataArray = ["ASSET_TYPE", "CHAR_NAME", "RIG_TYPE", "CREATION_DATE", "CREATION_TIME"]
    
    for stringData,nameData in zip(stringDataArray,nameDataArray):
        ma.addAttr(animRig, ln=stringData, dt="string", k=True)
        if nameData != None:
            if nameData == ma.date(d=True) or nameData == ma.date(t=True) or lockAllAttrs:
                ma.setAttr(animRig+"."+stringData, str(nameData), type="string", l=True)
            else:
                ma.setAttr(animRig+"."+stringData, str(nameData), type="string")
        
#Bake out animation

def bakeRigAnimation():
    sel = ma.ls(sl=True)
    rigGrp = sel[0]
    
    #Check whether this is a rig or not by checking for the attributes created by makeRigAsset Function
    
    #Check if object is an asset
    if not ma.objExists(rigGrp+".ASSET_TYPE"):
        raise Exception("Selected top level group is NOT considered an Asset!")
    
    assetType = ma.getAttr(rigGrp+".ASSET_TYPE")
    charName = ma.getAttr(rigGrp+".CHAR_NAME")
    rigType = ma.getAttr(rigGrp+".RIG_TYPE")
    
    #Check if asset is a rig
    if assetType != "RIG":
        raise Exception("Selected top level group is NOT considered a RIG!")
        
    
    #Get geometry and skeleton group
    
    geoGrp, skelGrp = None, None
    
    for item in ma.listRelatives(rigGrp, type="transform"):
        if item == "geo_GRP":
            geoGrp = item
        elif item == "skel_GRP":
            skelGrp = item
    
    #Get all joints from skel group!
    joints = ma.listRelatives(skelGrp, ad=True, type="joint")
    
    #Get all geometry from geo group!
    #Get shapes
    geoShapes = ma.listRelatives(geoGrp, ad=True, type="mesh")
    
    #Store all geometry transforms that have meshes under them, but if a geotransform name already exists in the list, continue to the next one
    geos = []
    for geoShape in geoShapes:
        parent = ma.listRelatives(geoShape,p=True, type="transform")
        if parent[0] in geos:
            continue
        geos.append(parent[0])
        
    #all variables needed for animation bake have been stored!
    
    startTime = ma.playbackOptions(min=True,q=True)
    endTime = ma.playbackOptions(max=True, q=True)
    ma.bakeResults(joints,t=(startTime, endTime))
    
    #Parent skel root and geometry to the world
    ma.parent(joints[-1], w=True)
    ma.parent(geos, w=True)
    
    ma.delete(rigGrp)
    
    print "{0} {1} rig ready for export!".format(charName,rigType)
    
    