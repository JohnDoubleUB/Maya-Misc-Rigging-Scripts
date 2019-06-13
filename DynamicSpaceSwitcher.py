import maya.cmds as ma

    
#Makes dynamic space switches, just select the group above a control for which it is needed and specify the spaces for the control

def makeDynamicSpaceSwitch(side="L", spacePrefix="armSpace", grpPrefix="GRP", conditNodePrefix ="CD", spaceArray=None):
    #If Space array is not defined nothing happens
    if spaceArray == None:
        return
    
    sel = ma.ls(sl=True,l=True)
    
    ctlSwitchGrp = sel[0]
    ctlSwitch = ma.listRelatives(ctlSwitchGrp, f=True)[0]
    spaceGrps = []
    conditionNodes = [] #Holds all condition nodes for connecting to the constraint
    spaceEnumString = "" #Holds the string for defining the enums in the enum attribute
    
    #Create all of the space groups and point and orient them to the ctl
    #Also store these name groups in a string for use in defining an enums list values (Separated by ":")
    #Also create each of the Condition Nodes and connect them
    incre = 0
    for spaceGrp in spaceArray:
        temp = ma.createNode("transform", n=side+"_"+spacePrefix+spaceGrp+"_"+grpPrefix)
        pointAndOrientSelected(item1=ctlSwitch, item2=temp)
        spaceGrps.append(temp)
        
        #Storing enum list as string
        incre = incre+1
        spaceEnumString = spaceEnumString+spaceGrp
        
        if incre != len(spaceArray):
            spaceEnumString = spaceEnumString+":"
              
    #Add spaceSwitchAttribute to switch CTL
    ma.addAttr(ctlSwitch, ln=spacePrefix, at="enum", en=spaceEnumString, dv= 0, k=True)
    
    incre = 0
    for spaceGrp in spaceArray:
        incre = incre+1
        #Create Condition Node and attatch space attribute to first term
        tempConN = ma.createNode("condition", n=side+"_"+spacePrefix+spaceGrp+"_"+conditNodePrefix)
               
        ma.setAttr(tempConN+".colorIfTrueR", 1)
        ma.setAttr(tempConN+".colorIfFalseR", 0)
        ma.setAttr(tempConN+".secondTerm", incre-1)
        
        ma.connectAttr(ctlSwitch+"."+spacePrefix, tempConN+".firstTerm")
        
        conditionNodes.append(tempConN)
        
    
    #Select each of the space groups and then the switchctlgrp!
    ma.select(cl=True)
    ma.select(spaceGrps)
    ma.select(ctlSwitchGrp, add=True)
    
    #Create parent constraint!
    spaceParentCon = ma.parentConstraint(mo=True)
    
    #attatch condition nodes to their respective space weightings
    incre = -1
    for conNode, spaceGrp in zip(conditionNodes, spaceGrps):
        incre = incre+1
        
        #Construct weighting attribute name
        weightingAttr = "."+spaceGrp+"W"+str(incre)
        
        #Connect condition node to its repective attribute
        ma.connectAttr(conNode+".outColor.outColorR", spaceParentCon[0]+weightingAttr)