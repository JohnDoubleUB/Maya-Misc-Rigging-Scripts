import maya.cmds as ma

###IK leg script!

#Builds a module group for a rig
def makeRigModule(side="L", partName="partName", grpPrefix="GRP"):
    moduleRoot = ma.createNode("transform", n="%s_%s_%s"%(side,partName,grpPrefix))
    
    for subGroup in ("Skel","Ctls","Parts","In","Out"):
        subGroupObj = ma.createNode("transform", n="%s_%s%s_%s"%(side,partName,subGroup,grpPrefix))
        ma.parent(subGroupObj, moduleRoot)




#Makes controls for finger and toe chains, returns the top most group for each finger/toe ctl for parenting along with a curl offset group for each control
def createFKJointCtls(controlBaseGrp, parentJntsArray, lettersArray, side="L", jntPrefix="JNT", grpPrefix="GRP", ctlPrefix="CTL", part="toe"):
    #Get information
    fkJntChains = parentJntsArray
    curlGrps = [] #Contains curl offset groups for each ctl
    rootCtlGrp = []
    incre = -1 #For toe lettering
    
    for jntChain in fkJntChains:
        incre2 = 0 #For down chain numbering
        incre = incre+1
        
        #Get all of a toes segments
        parentAndChildJntChain = returnParentAndChildren(jntChain,reverse=False)
        #Remove the end joint from the list
        del parentAndChildJntChain[len(parentAndChildJntChain)-1]
        
        #For each joint in each toe
        for jnt in parentAndChildJntChain:
            incre2 = incre2+1
            #Duplicate the controlBaseGrp
            newCtlGrp = ma.duplicate(controlBaseGrp)
            
            #Rename grp and ctl and return both
            newCtlGrp, newCtl = renameControl(newCtlGrp[0], (side+"_"+part+lettersArray[incre]+"FKCtl0"+str(incre2)+"_"+grpPrefix), (side+"_"+part+lettersArray[incre]+"FK0"+str(incre2)+"_"+ctlPrefix))
            
            #Lock unwanted attributes (all but rotation)
            for attr1 in (".translate", ".scale", ".visibility"):
                if attr1 != ".visibility":
                    for attr2 in ("X","Y","Z"):
                        ma.setAttr(str(newCtl)+attr1+attr2, l = True, k=False)
                else:
                    ma.setAttr(str(newCtl)+attr1, l = True, k=False)
            
            #point and orient to the current joint
            pointAndOrientSelected(item1=jnt, item2=newCtlGrp)
            
            
            #Duplicate point and orientated Grp for curl grp
            curlGrp = ma.duplicate(newCtlGrp, po=True, n=(side+"_"+part+lettersArray[incre]+"FKCurl0"+str(incre2)+"_"+grpPrefix))
            #parent group under original group then parent ctl under that
            ma.parent(newCtl, curlGrp)
            ma.parent(curlGrp, newCtlGrp)
            newCtl = findLastChild(newCtlGrp)
            
            
            #constrainCtlJnt to Ctl
            ma.orientConstraint(newCtl, jnt)
            
            if incre2 == 1:
                rootCtlGrp.append(newCtlGrp)
                parentCtl = newCtl
            else:
                #print str(newCtlGrp)+"  "+str(parentCtl)
                ma.parent(newCtlGrp, parentCtl)
                parentCtl = findLastChild(parentCtl)
                
    for rootJnt in rootCtlGrp:
        toeHierach = returnParentAndChildren(rootJnt,reverse=False)
        incre = 0
        incre2 = 0
        for jntTransform in toeHierach:
            if incre2 == 1:
                curlGrps.append(jntTransform)
                incre2 = incre2+1
            elif incre2 == 2:
                if incre == 2:
                    curlGrps.append(jntTransform)
                    incre = 0
                else:
                    incre = incre+1
            else:
                incre2 = incre2+1
    
    return rootCtlGrp, curlGrps #Return all the rootctlGrps, and curl offset grps



#point and orient selected then by default remove constraints
def pointAndOrientSelected(removal=True, item1=None, item2=None):
    if None in (item1, item2):
        sel = ma.ls(sl=True)
        item1 = sel[0]
        item2 = sel[1] 
        if len(sel) > 2:
            print "too many items selected!"
            return
    pointTemp = ma.pointConstraint(item1, item2)
    orientTemp = ma.orientConstraint(item1, item2)
    if removal == True:
        print "Constraints Removed After Use!"
        ma.delete(pointTemp, orientTemp)
    else:
        print "Constraints not Removed After Use!"


#Creates a duplicate chain for each of a parents child joints, removes any inbetween joints and parents the original child under the new duplicate (This is for IK in order to maintain fk toe ctls)
def dupAndParentChildChainStartEnd(jntParent, lettersArray, side="L", jntPrefix="JNT"):
    jntStarts = ma.listRelatives(jntParent, f=True)
    incr = -1
    jntStartEndArray = []
    for jntChain in jntStarts:
        incr = incr+1
        #Duplicate joint and underlying chain
        jntDupe = ma.duplicate(jntChain, n="L_toeIK"+lettersArray[incr]+"Ctl_"+jntPrefix, rc=True)
        #Rename last child
        ma.rename(findLastChild(jntDupe[0]), "L_toeIK"+lettersArray[incr]+"CtlEnd_"+jntPrefix)
        #Get children and parent of chain
        jntDupe = returnParentAndChildren(jntDupe[0], reverse=False)
        #Store start and end of chain
        startJnt = jntDupe[0]
        endJnt = jntDupe[-1]
        #Parent chain end under chain start
        ma.parent(endJnt, startJnt)
        #Delete the inbetween joints
        ma.delete(jntDupe[1])
        #Get the remaining jnts updated info
        jntDupe = returnParentAndChildren(startJnt, reverse=False)
        #Parent the original joints under these new duplicate chains
        ma.parent(jntChain, startJnt)
        jntStartEndArray.append(jntDupe)
    return jntStartEndArray

#returns true if a given object has children, returns false otherwise
def hasChildren(parent):
    #Type Transform added
    child = ma.listRelatives(parent, typ="transform")
    if child == None:
        return False
    else:
        return True
    
#returns parent and children of a given object, reverses the order by default (useful when trying to rename joints non destructively later)
def returnParentAndChildren(parent,reverse=True):
    parentChildArray = []
    if hasChildren(parent):
        parentChildArray.append(parent)
        #Type transform added
        child = ma.listRelatives(parent, f=True, typ="transform")
        parentChildArray.append(child[0])
    else:
        return None
    while hasChildren(child[0]):
        #Type transform added
        child = ma.listRelatives(child[0], f=True, typ="transform")
        parentChildArray.append(child[0])
    if reverse == True:
        tempArray = []
        for i in reversed(parentChildArray):
            tempArray.append(i)
        parentChildArray = tempArray
    return parentChildArray

#Creates a joint chain based on a list of postitions, returns all the joints in reverse order for non destructive renaming
def createJointChainOnPos(locationList, jntSize=0.5):
    ma.select(cl=True)
    parentJoint = None
    i = 0
    for loc in locationList:
        i=i+1
        if i == 1:
            parentJoint = ma.joint(p=loc, rad=jntSize)
        else:
            ma.joint(p=loc, rad=jntSize)
    ma.select(cl=True)
    return returnParentAndChildren(parentJoint)

#Renames control grp and control, returns both objects
def renameControl(ctlGroup, groupName, ctlName):
    ctlGroup = ma.rename(ctlGroup, groupName)
    ctl = ma.listRelatives(ctlGroup, f=True)
    ctl = ma.rename(ctl, ctlName)
    return ctlGroup, ctl

#Gets the last object in a hierachy
def findLastChild(parent):
    #Type transform added
    child = ma.listRelatives(parent, typ="transform")
    if child == None :
        return parent
    else:
        return findLastChild(child[0])

#Gets the children of a selected joint, appends arrays of start and end points for each of the children
def returnChildrenJntStartsAndEnds(jntParent):
    #Type transform added
    jntStarts = ma.listRelatives(jntParent, typ="transform")
    jntStartEndArray = []
    
    jntTempArray = []
    
    for jnt in jntStarts:
        jntTempArray.append(jnt)
        jntTempArray.append(findLastChild(jnt))
        jntStartEndArray.append(jntTempArray)
        jntTempArray = []
        
    return jntStartEndArray
    
###### Making IK FK LEG!
def createIKLeg(side = "L", grpPrefix = "GRP", ctlPrefix = "CTL", ikhPrefix = "IKH", jntPrefix = "JNT", masterToe=1, legStretchOffset=0.6):
    #Get selected
    sel = ma.ls(sl=True)
    
    #I didn't know how to get alphabetical letters for toe ik handles nicely, sue me
    #No one have this many toes on a single footJnt, but gotta be safe
    letters = ["A","B","C","D","E","F","G","H","I","J"]
    
    #List of floating point attributes to add to the ik control
    IKfootJntAttrs = ["toeEndTip","toeEndSwivel", "toeUpperTip", "heelTip", "heelSwivel"]
    
    #Store variables
    legStartJnt = sel[0]
    legMidJnt = sel[1]
    legEndJnt = sel[2]
    footJnt = sel[3]
    
    #IK Controls
    
    footJntIKCtlGrp = sel[4]
    footJntIKCtl = None
    
    legPVCtlGrp = sel[5]
    legPVCtl = None
    
    #FK Controls
    
    legFKUpperCtlGrp = sel[6]
    legFKUpperCtl = None
    
    legFKLowerCtlGrp = sel[7]
    legFKLowerCtl = None
    
    legFKHeelCtlGrp = sel[8]
    legFKHeelCtl = None
    
    legFKFootCtlGrp = sel[9]
    legFKFootCtl = None
    
    #FKIK switch
    
    fkIKCtlGrp = sel[10]
    fkIKCtl = None
    
    fkToeCtlGrp = sel[11] # Control is duped for each toe joint control
    
    
    toeStartEnd = [] # to hold all toe start and ends
    toeIKHs = [] #To hold all toe ik handles
    fkToeCtlGrps = [] #To hold all the fk toe controls
    fkToeJnts = [] #To Hold all toe jnt roots to be given fk ctls
    fkToeCurlGrps = [] #To hold the curl offset groups for the toes
    
    ### PREP FOR FK TOES
    #Make duplicate toes parent old joints to new and get new start and end 
    toeStartEnd = dupAndParentChildChainStartEnd(footJnt, letters, side, jntPrefix)
    
    #### MAKE IK ####
    
    #Create IK handle for leg itself
    ma.select(cl=True)
    ma.select((legStartJnt, legEndJnt))
    legIK = ma.ikHandle(sol="ikRPsolver")
    
    #Rename IK handle
    legIKH = ma.rename(legIK[0],side+"_leg_"+ikhPrefix)
    
    #Create IK handle for footJnt
    ma.select(cl=True)
    ma.select((legEndJnt, footJnt))
    footJntIK = ma.ikHandle(sol="ikSCsolver")
    footJntIKH = ma.rename(footJntIK[0],side+"_footJnt_"+ikhPrefix)
    
    #Create IK handle for toe
    ma.select(cl=True)
    ma.select((footJnt, toeStartEnd[masterToe][0]))
    toeIK = ma.ikHandle(sol="ikSCsolver")
    toeIKH = ma.rename(toeIK[0],side+"_toe_"+ikhPrefix)
    
    #Rename IK Control
    footJntIKCtlGrp, footJntIKCtl = renameControl(footJntIKCtlGrp, side+"_legIkCtl_"+grpPrefix, side+"_legIk_"+ctlPrefix)
    
    
    #Rename IK PV Control
    legPVCtlGrp, legPVCtl = renameControl(legPVCtlGrp, side+"_legPVCtl_"+grpPrefix, side+"_legPV_"+ctlPrefix)
    
    #lock and hide unwanted attributes on ikctl and pvCtl
    for fkCtlAttr in ("X", "Y", "Z"):
        ma.setAttr(footJntIKCtl+".scale"+fkCtlAttr, l= True, k=False)
        
        ma.setAttr(legPVCtl+".scale"+fkCtlAttr, l= True, k=False)
        ma.setAttr(legPVCtl+".rotate"+fkCtlAttr, l= True, k=False)
        
    ma.setAttr(footJntIKCtl+".visibility", l=True, k=False)
    ma.setAttr(legPVCtl+".visibility", l= True, k=False)
    
    #Move IK Contol
    pointConTemp = ma.pointConstraint(legEndJnt, footJntIKCtlGrp)
    ma.delete(pointConTemp)
    
    #Point contraint footJntIKH to footJntIKCtl
    #ma.pointConstraint(footJntIKCtl, legIKH)
    
    #Move PV Control
    pointConTemp = ma.pointConstraint(legMidJnt, legPVCtlGrp)
    ma.delete(pointConTemp)
    ma.move(0, 0, 50, legPVCtlGrp, os=True, r=True)
    
    #Create Pole Vector Constraint
    ma.poleVectorConstraint(legPVCtl, legIKH)
    
    ##Create each toe IK and store handle in toeIKHs!
    incr = -1
    for toe in toeStartEnd:
        incr = incr+1
        ma.select(cl=True)
        ma.select(toe[0], toe[1])
        ikTemp = ma.ikHandle(sol="ikSCsolver")
        ikTemp = ma.rename(ikTemp[0],side+"_toe"+letters[incr]+"IK_"+ikhPrefix)
        ma.setAttr(toe[1]+".visibility", 0)
        toeIKHs.append(ikTemp)
    
    #### Create FKIK Switch! ####
        
    #Name IKFK CTL
    fkIKCtlGrp, fkIKCtl = renameControl(fkIKCtlGrp, side+"_legFKIKCtl_"+grpPrefix, side+"_legFKIK_"+ctlPrefix)
    
    #Move IKFK Ctl
    pointConTemp = ma.pointConstraint(legEndJnt, fkIKCtlGrp)
    ma.delete(pointConTemp)
    
    #Add attribute to FKIK
    ma.addAttr(fkIKCtl, ln="FKIK", min = 0, max = 1, dv= 0, k=True)
    
    #FK Toe visibility (for use later!)
    ma.addAttr(fkIKCtl, ln="fkToeVisibility", min = 0, max = 1, dv= 0, k=True)
    
    #Connect attribute IKH ikblend attributes to FKIK
    #leg, foot, toe
    for hdl in (legIKH, footJntIKH, toeIKH):
        ma.connectAttr(fkIKCtl+".FKIK", hdl+".ikBlend")
    
    #toes
    for hdl in toeIKHs:
        ma.connectAttr(fkIKCtl+".FKIK", hdl+".ikBlend")
    
    #### Reverse footJnt Setup! ####
    
    #Create root joint reverse footJnt joint (Heel joint)
    ma.select(cl=True)
    rvHeelJnt = ma.joint(rad=0.5)
    rvHeelJnt = ma.rename(rvHeelJnt, side+"_footJntRV01_"+jntPrefix)
    
    #Move root reverse footJnt
    pointConTemp = ma.pointConstraint(legEndJnt, rvHeelJnt)
    ma.delete(pointConTemp)
    ma.move(0, rvHeelJnt, y=True)
    
    #make the rest of the reverse footJnt
    
    #Get locations for the reverse footJnt joints
    reversefootJntLocations = []
    for rvLocation in (toeStartEnd[masterToe][1], toeStartEnd[masterToe][0], footJnt, legEndJnt):
        reversefootJntLocations.append(tuple(ma.xform(rvLocation, q=True, ws=True, t=True)))
        
    #Create the IK toe joints
    rvJnts = createJointChainOnPos(reversefootJntLocations)
    
    #Rename all joints
    incr = len(rvJnts)+2
    for jnt in rvJnts:
        incr = incr-1
        
        if incr == 2:
            #If it is the second to last joint, parent it under the heel root
            ma.parent(ma.rename(jnt, side+"_footJntRV0"+str(incr)+"_"+jntPrefix),rvHeelJnt)
        else:
            ma.rename(jnt, side+"_footJntRV0"+str(incr)+"_"+jntPrefix)
    
    #Re obtain all the now children of rvHeelJnt, these are the rvJnts
    rvJnts = returnParentAndChildren(rvHeelJnt, reverse=False)
    
    #parent toesIKHs under the toe jnt on reverse footJnt rig
    for toeHandle in toeIKHs:
        ma.parent(toeHandle, rvJnts[1])
        
    #parent toeIKH under the first toe rvjnt
    ma.parent(toeIKH, rvJnts[2])
    
    #parent footJntIKH under footJnt rvjnt
    ma.parent(footJntIKH, rvJnts[3])
    
    #parent leg IKH under leg rvjnt
    ma.parent(legIKH, rvJnts[4])
    
    #Make custom attributes for footJnt IK control
    for attr in IKfootJntAttrs:
        ma.addAttr(footJntIKCtl, ln=attr, dv= 0, k=True)
        
    #Connect new attributes to their respective reverse footJnt joint attributes
    ma.connectAttr(footJntIKCtl+"."+IKfootJntAttrs[0], rvJnts[1]+".rotateX") #Toe End Tip
    ma.connectAttr(footJntIKCtl+"."+IKfootJntAttrs[1], rvJnts[1]+".rotateY") #Toe End End Swivel
    
    ma.connectAttr(footJntIKCtl+"."+IKfootJntAttrs[2], rvJnts[2]+".rotateX") #Toe Tip Upper
    
    ma.connectAttr(footJntIKCtl+"."+IKfootJntAttrs[3], rvJnts[3]+".rotateX") #Heel Tip
    ma.connectAttr(footJntIKCtl+"."+IKfootJntAttrs[4], rvJnts[3]+".rotateY") #Heel Swivel
    
    #Parent Constrain the root Reverse footJnt to the ikCtl
    ma.parentConstraint(footJntIKCtl, rvJnts[0], mo=True)
    
    #hide the RV foot
    ma.setAttr(rvJnts[0]+".visibility", 0)
    
    #### Attatching FK Leg Controls ####
    
    #rename controls
    legFKUpperCtlGrp, legFKUpperCtl = renameControl(legFKUpperCtlGrp,side+"_legFK01Ctl_"+grpPrefix, side+"_legFK01_"+ctlPrefix)
    legFKLowerCtlGrp, legFKLowerCtl = renameControl(legFKLowerCtlGrp,side+"_legFK02Ctl_"+grpPrefix, side+"_legFK02_"+ctlPrefix)
    legFKHeelCtlGrp, legFKHeelCtl = renameControl(legFKHeelCtlGrp,side+"_legFK03Ctl_"+grpPrefix, side+"_legFK03_"+ctlPrefix)
    legFKFootCtlGrp, legFKFootCtl = renameControl(legFKFootCtlGrp,side+"_legFK04Ctl_"+grpPrefix, side+"_legFK04_"+ctlPrefix)
    
    #position controls
    for fkJnt, fkCtlGrp, fkCtl in zip((legStartJnt, legMidJnt, legEndJnt, footJnt),(legFKUpperCtlGrp, legFKLowerCtlGrp, legFKHeelCtlGrp, legFKFootCtlGrp),(legFKUpperCtl, legFKLowerCtl, legFKHeelCtl, legFKFootCtl)):
        #Move ctls to joints
        pointAndOrientSelected(item1=fkJnt, item2=fkCtlGrp)
        
        #orientConstrain joints to ctls
        ma.orientConstraint(fkCtl, fkJnt)
    
    #Make an orient constraint group for each iktoe so that they have a default orient when not in ikblend 1
    ikToesOrientGrpCns = []
    
    incr = -1
    for ikToeJnt in toeStartEnd:
        incr = incr+1
        ikToeCnGrp = ma.createNode("transform", n=side+"_ikToe"+letters[incr]+"OrientCn_"+grpPrefix)
        pointAndOrientSelected(item1=ikToeJnt[0], item2=ikToeCnGrp)
        ma.orientConstraint(ikToeCnGrp, ikToeJnt[0])
        ikToesOrientGrpCns.append(ikToeCnGrp)
    
    #CreateToeOrientCnGrp to contain all toes orient constraint groups
    ikToesCnGrpGrp = ma.createNode("transform", n=side+"_ikToeOrientCnGrp_"+grpPrefix)
    for cnGrp in ikToesOrientGrpCns:
        ma.parent(cnGrp, ikToesCnGrpGrp)
    
    #parent grpgrp under last FKlegCtl
    ma.parent(ikToesCnGrpGrp,legFKFootCtl)
    
    for toe in toeStartEnd:
        fkToeJnts.append(ma.listRelatives(toe[0], f=True)[1])
        
    
    #parent fk controls in hierachy
    ma.parent(legFKFootCtlGrp, legFKHeelCtl)
    ma.parent(legFKHeelCtlGrp, legFKLowerCtl)
    ma.parent(legFKLowerCtlGrp, legFKUpperCtl)
    
    #### FK TOES CREATION! ####
    
    #Create FK toe ctls and curl offset grps
    fkToeCtlGrps, fkToeCurlGrps = createFKJointCtls(fkToeCtlGrp, fkToeJnts, letters, side, jntPrefix, grpPrefix, ctlPrefix)
    
    #Add attributes to FKIK Ctl
    ma.addAttr(fkIKCtl, ln="toeScrunch", dv=0, k=True)
    ma.addAttr(fkIKCtl, ln="toeSpread", dv=0, k=True)
    
    #linking up to scrunch, rotate Z
    incre = 0
    
    #Create reverse node for toe scrunch
    toeScrunchRVNode = ma.createNode("reverse", n=side+"_toeScrunch_RV")
    ma.connectAttr(fkIKCtl+".toeScrunch", toeScrunchRVNode+".inputX")
    for toeCurlGrp in fkToeCurlGrps:
        if incre == 0:
            incre = incre+1
            ma.connectAttr(fkIKCtl+".toeScrunch", toeCurlGrp+".rotateZ") #Toe End Tip
        elif incre == 2:
            incre = 0
            ma.connectAttr(toeScrunchRVNode+".outputX",toeCurlGrp+".rotateZ")
        else:
            incre = incre+1
            ma.connectAttr(toeScrunchRVNode+".outputX",toeCurlGrp+".rotateZ")
    #Linking up rotate Y for toe spread attr
    incre = 0
    
    #Create toe spread reverse node
    toeSpreadRVNode = ma.createNode("reverse", n=side+"_toeSpread_RV")
    
    #Create divide nodes
    toeSpreadRVDiv = ma.createNode("multiplyDivide", n=side+"_toeSpreadRV_MDV")
    toeSpreadDiv = ma.createNode("multiplyDivide", n=side+"_toeSpread_MDV")
    
    #Set divide node input 2X
    ma.setAttr(toeSpreadRVDiv+".operation", 2)
    ma.setAttr(toeSpreadDiv+".operation", 2)
    ma.setAttr(toeSpreadRVDiv+".input2X", 2)
    ma.setAttr(toeSpreadDiv+".input2X", 2)
    
    #Connect up divide and reverse nodes
    ma.connectAttr(fkIKCtl+".toeSpread", toeSpreadRVNode+".inputX")
    ma.connectAttr(fkIKCtl+".toeSpread", toeSpreadDiv+".input1X")
    ma.connectAttr(toeSpreadRVNode+".outputX", toeSpreadRVDiv+".input1X")
    
    #Attatch all the toe starts to spread
    for toeCurlGrp in fkToeCurlGrps:
        incre = incre+1
        if incre == 1:
            ma.connectAttr(toeSpreadRVDiv+".outputX",toeCurlGrp+".rotateY")
        elif incre == 4:
            ma.connectAttr(toeSpreadRVNode+".outputX",toeCurlGrp+".rotateY")
        elif incre == 7:
            ma.connectAttr(toeSpreadRVDiv+".outputX",toeCurlGrp+".rotateY")
        elif incre == 10:
            ma.connectAttr(toeSpreadDiv+".outputX",toeCurlGrp+".rotateY")
        elif incre == 13:
            ma.connectAttr(fkIKCtl+".toeSpread", toeCurlGrp+".rotateY")
        else:
            pass
            
    #### SETTING VISIBILITY, PARENTING ####
    
    #Create fkik reverse node and connect to fkik
    fkikRV = ma.createNode("reverse", n=side+"_fkIK_RV")
    ma.connectAttr(fkIKCtl+".FKIK", fkikRV+".inputX")
    
    #set visibility of IK foot
    #legFKUpperCtlGrp, footJntIKCtlGrp
    ma.connectAttr(fkIKCtl+".FKIK", footJntIKCtlGrp+".visibility")
    ma.connectAttr(fkIKCtl+".FKIK", legPVCtlGrp+".visibility")
    ma.connectAttr(fkikRV+".outputX", legFKUpperCtlGrp+".visibility")
            
    ## Parent constrain fkIKCtlGrp to the legEndJnt
    ma.parentConstraint(legEndJnt, fkIKCtlGrp, mo=True)
    
    #Create fkToeCtls_GRP to contain all the toe ctls
    fkToeCtlsGrp = ma.createNode("transform", n=side+"_fkToeCtls_"+grpPrefix)
    
    #parent constrain root toes toe their respective ik switching toe jnts
    for toe, toeRootGrp in zip(toeStartEnd, fkToeCtlGrps):
        ma.parentConstraint(toe[0], toeRootGrp)
        ma.connectAttr(fkIKCtl+".fkToeVisibility", toeRootGrp+".visibility")
        # Parent all toeRootGrps under fkToeCtlsGrp
        ma.parent(toeRootGrp, fkToeCtlsGrp)
    
    #### CREATE STRETCHY LEGS! ####
    
    #Create and name locators!
    legStretchStartLoc = ma.spaceLocator(n=side+"_legStartStretch_LOC")
    legStretchEndLoc = ma.spaceLocator(n=side+"_legEndStretch_LOC")
    
    #point constrain locators to start and end
    ma.pointConstraint(legStartJnt, legStretchStartLoc)
    ma.pointConstraint(footJntIKCtl, legStretchEndLoc)
    
    #Create a distance between node
    legStretchDst = ma.createNode("distanceBetween", n=side+"_legStretch_DST")
    ma.connectAttr(legStretchStartLoc[0]+".worldMatrix", legStretchDst+".inMatrix1")
    ma.connectAttr(legStretchEndLoc[0]+".worldMatrix", legStretchDst+".inMatrix2")
    
    #Create a divide node!
    legStretchDiv = ma.createNode("multiplyDivide", n=side+"_legStretchValue_MDV")
    ma.setAttr(legStretchDiv+".operation", 2)
    
    #Create worldscale divide node!
    worldScaleMult = ma.createNode("multiplyDivide", n=side+"_legWorldScale_MDV")
    #Set input2X to default distance (leaving 1X open for the world scale)
    ma.setAttr(worldScaleMult+".input2X", (ma.getAttr(legStretchDst+".distance")+legStretchOffset))
    ma.setAttr(worldScaleMult+".input1X", 1) # This will need to be attatched to the world scale later! 
    
    #Connect distance node to input1X and worldScaleMult to input2X
    ma.connectAttr(legStretchDst+".distance", legStretchDiv+".input1X")
    ma.connectAttr(worldScaleMult+".outputX", legStretchDiv+".input2X")
    
    #Create a condition node
    legStretchCon = ma.createNode("condition", n=side+"_legStretch_CN")
    
    #Create stretch attribute on ikfootctl
    ma.addAttr(footJntIKCtl, ln="stretch", min = 0, max = 1, dv= 0, k=True)
    
    #Create stretchSwitchAttrMDV and stretchSwitchFKIK
    legStretchSwitchMult = ma.createNode("multiplyDivide", n=side+"_legStretchSwitch_MDV")
    legStretchSwitchFKIKMult = ma.createNode("multiplyDivide", n=side+"_legStretchSwitchFKIK_MDV")
    
    #Connect stretch attribute to legStretchSwitchMult input1X
    ma.connectAttr(footJntIKCtl+".stretch", legStretchSwitchMult+".input1X")
    
    #Connect FKIK attribute to legStretchSwitchFKIKMult input1X
    ma.connectAttr(fkIKCtl+".FKIK", legStretchSwitchFKIKMult+".input1X")
    
    #Connect legStretchDiv to legStretchSwitchMult.input2X
    ma.connectAttr(legStretchDiv+".outputX", legStretchSwitchMult+".input2X")
    
    #Connect legStretchSwitchMult to legStretchSwitchFKIKMult.input2X
    ma.connectAttr(legStretchSwitchMult+".outputX", legStretchSwitchFKIKMult+".input2X")
    
    #Connect legStretchSwitchFKIKMult to firstTerm
    ma.connectAttr(legStretchSwitchFKIKMult+".outputX", legStretchCon+".firstTerm")
    
    #Connect MDV to the colorIfTrue.colorIfTrueR
    ma.connectAttr(legStretchDiv+".outputX", legStretchCon+".colorIfTrue.colorIfTrueR")
    
    #set second term and operation of legStretchCon
    ma.setAttr(legStretchCon+".secondTerm", 1)
    ma.setAttr(legStretchCon+".operation", 2)
    
    #Connect condition nodes outColor.outColorR to scaleX on legStartJnt and legMidJnt
    ma.connectAttr(legStretchCon+".outColor.outColorR", legStartJnt+".scaleX")
    ma.connectAttr(legStretchCon+".outColor.outColorR", legMidJnt+".scaleX")
    
    #Create a group to hold the two locators
    legStretchGrp = ma.createNode("transform", n=side+"_legStretch_"+grpPrefix)
    ma.parent(legStretchStartLoc[0], legStretchGrp)
    ma.parent(legStretchEndLoc[0], legStretchGrp)
    
    #createFKJointCtls(controlBaseGrp, parentJntsArray, lettersArray, side="L", jntPrefix="JNT", grpPrefix="GRP", ctlPrefix="CTL")
    
###### Making FK Fingers!

def createFingerFKCtls(side="L", grpPrefix="GRP", ctlPrefix="CTL"):
    sel = ma.ls(sl=True)
    
    fkCtlGrp = sel[0] #Stores the control to be duplicated and used on all the finger fks
    rootJnt = sel[2] #Holds the wrist joint
    
    handFKCtlGrp = sel[1]
    handFkCtl = None
    
    rootCtlGrps = [] #Stores all created FK root grps
    curlGrps = [] #Stores all created FK Curl grps
    
    
    #Rename the handFKCtlGrp
    handFKCtlGrp, handFKCtl = renameControl(handFKCtlGrp, side+"_handFKCtl_"+grpPrefix, side+"_handFK_"+ctlPrefix)
    
    #lock and hide all attributes on handFKCtl
    for attr1 in (".translate",".rotate",".scale", ".visibility"):
        if attr1 != ".visibility":
            for attr2 in ("X","Y","Z"):
                ma.setAttr(str(handFKCtl)+attr1+attr2, l = True, k=False)
        else:
            ma.setAttr(str(handFKCtl)+attr1, l = True, k=False)
    
    #Parent constrain the handFKCtl to the rootJnt
    ma.parentConstraint(rootJnt, handFKCtlGrp)
    
    #Get all of the fingers!
    wristJntChildren = ma.listRelatives(rootJnt, f=True, typ="joint") #Holds the first joint in each finger
    
    #Pass this information to the createFKJointCtls
    rootCtlGrps, curlGrps = createFKJointCtls(controlBaseGrp=fkCtlGrp, parentJntsArray=wristJntChildren,  lettersArray=["A","B","C","D","E","F","G"], part="finger",side=side)
        
    #Make visibility, curl and spread attributes on handFKCtl
    ma.addAttr(handFKCtl, ln="fkHandVisibility", min = 0, max = 1, dv= 0, k=True)
    ma.addAttr(handFKCtl, ln="fingerCurl", dv=0, k=True)
    ma.addAttr(handFKCtl, ln="thumbCurl", dv=0, k=True)
    ma.addAttr(handFKCtl, ln="fingerSpread", dv=0, k=True)
    
    #parent constrain each finger rootgrp to the root joint
    #Connect rootFinger Visibility withe the fkHandVisiblity Attribute on handFKCtl
    for ctlRootGrp in rootCtlGrps:
        ma.parentConstraint(rootJnt, ctlRootGrp, mo=True)
        ma.connectAttr(handFKCtl+".fkHandVisibility",ctlRootGrp+".visibility")
    incre = 0
    #Connect up the curl attribute
    for curlGrp in curlGrps:
        incre = incre+1
        if incre > 3:
            ma.connectAttr(handFKCtl+".fingerCurl", curlGrp+".rotateZ")       
        else:
            ma.connectAttr(handFKCtl+".thumbCurl", curlGrp+".rotateZ")
            
    #connect up finger spread attribute
    incre = 0
    incre2 = 0
    
    ##Create Supporting Nodes!
    
    #SpreadReverseNode and connect fingerSpread attribute to InputX
    spreadRV = ma.createNode("reverse", n=side+"_fingerSpread_RV")
    ma.connectAttr(handFKCtl+".fingerSpread", spreadRV+".inputX")
    
    #SpreadDivideNode and set to divide by 2 (For x and y)
    spreadMDV = ma.createNode("multiplyDivide", n=side+"_fingerSpread_MDV")
    ma.setAttr(spreadMDV+".operation", 2)
    
    ma.setAttr(spreadMDV+".input2X", 2) #For normal value
    
    ma.setAttr(spreadMDV+".input2Y", 2) #For reversed value
    
    #connect fingerSpread to input1X and spreadRV.outputX to input1Y
    ma.connectAttr(handFKCtl+".fingerSpread", spreadMDV+".input1X")
    ma.connectAttr(spreadRV+".outputX", spreadMDV+".input1Y")
    
    """
    There are now 4 spread values
    the normal one, normal/2, normal reversed, normal reversed/2:
        handFKCtl+".fingerSpread"
        spreadMDV+".outputX"
        spreadRV+".outputX"
        spreadMDV+".outputY"
    """
    
    for curlGrp in curlGrps[3:]:
        if incre == 0:
            incre2 = incre2+1
            print curlGrp
            if incre2 == 1:
                ma.connectAttr(handFKCtl+".fingerSpread", curlGrp+".rotateY")
            elif incre2 == 2:
                ma.connectAttr(spreadMDV+".outputX", curlGrp+".rotateY")
            elif incre2 == 3:
                ma.connectAttr(spreadMDV+".outputY", curlGrp+".rotateY")
            else:
                ma.connectAttr(spreadRV+".outputX", curlGrp+".rotateY")
                incre2 = 0
            incre = incre+1
        elif incre == 2:
            incre = 0
        else:
            incre = incre+1
            
    #Group up all of the finger fkCtls
    fingerCtlsGrpGrp = ma.createNode("transform", n = side+"_fingersGrp_"+grpPrefix)
    
    for fingerGrp in rootCtlGrps:
        ma.parent(fingerGrp, fingerCtlsGrpGrp)



#makeDynamicSpaceSwitch(spaceArray=["Chest","Body","World"]) 
#createFingerFKCtls(side="R")