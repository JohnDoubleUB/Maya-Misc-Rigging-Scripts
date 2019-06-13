import maya.cmds as ma

## This script is used to construct a basic rig for an arm, including FKIK Switching, Pole vector and an Auto Shoulder

##Order of selection: jnts: shoulder, upper, lower, hand, controlGRPS: ikhand, pv, shoulder, upper, lower, hand, fkik

class armBuilder():
    
    ##Joints
    shoulderJnt = None
    upperArmJnt = None
    lowerArmJnt = None
    handJnt = None
    
    ##Controls Grp
    ikHandCtlGrp = None
    ikPVCtlGrp = None
    
    shoulderCtlGrp = None
    
    upperFKCtlGrp = None
    lowerFKCtlGrp = None
    handFKCtlGrp = None
    fkikCtlGrp = None
    
    ##Controls Ctl
    ikHandCtl = None
    ikPVCtl = None
    
    shoulderCtl = None
    
    upperFKCtl = None
    lowerFKCtl = None
    handFKCtl = None
    
    fkikCtl = None
    
    #Created Objects
    ikHNodes = None
    ikH = None
    
    def __init__(self, side="L", ctlPrefix="CTL", grpPrefix="GRP", ikhPrefix="IKH", jntPrefix="JNT"):
        self.side = side
        self.ctlPrefix = ctlPrefix
        self.grpPrefix = grpPrefix
        self.ikhPrefix = ikhPrefix
        self.jntPrefix = jntPrefix
        
        sel = ma.ls(sl=True)
        if len(sel) == 11:
            self.storeAllJntsNeeded(sel[0], sel[1], sel[2], sel[3])
            self.storeAllCtlsNeeded(sel[4], sel[5], sel[6], sel[7], sel[8], sel[9], sel[10])
        else:
            print "Unable to store values for arm object!"
        
        
    #Point and orient contstraints an object to another object automatically removing one from the other
    def pointAndOrientSelected(self, removal=True, item1=None, item2=None):
        pointTemp = ma.pointConstraint(item1, item2)
        orientTemp = ma.orientConstraint(item1, item2)
        if removal == True:
            print "Constraints Removed After Use!"
            ma.delete(pointTemp, orientTemp)
        else:
            print "Constraints not Removed After Use!"
            
    def storeAllJntsNeeded(self, shoulder, upperArm, lowerArm, hand):
        self.shoulderJnt = shoulder
        self.upperArmJnt = upperArm
        self.lowerArmJnt = lowerArm
        self.handJnt = hand
        
    def storeAllCtlsNeeded(self, ikhandCtl, ikPVCtl, shoulder, upperFK, lowerFK, handFK, fkik):
        self.ikHandCtlGrp = ikhandCtl
        self.ikPVCtlGrp = ikPVCtl
        self.shoulderCtlGrp = shoulder
        self.upperFKCtlGrp = upperFK
        self.lowerFKCtlGrp = lowerFK
        self.handFKCtlGrp = handFK
        self.fkikCtlGrp = fkik
        
        
    #Create arm IK
    ##Selection order: ik start,ik end, elbow, ik end control, ik poleVectorCtl
    def createArmIK(self):
        ##Create initial IK
        #even though the ik handle is given its start and end it still looks at what maya has selected and complains when more joints are selected, that is shit. autodesk wtf
        ma.select(cl=True)
        ma.select((self.upperArmJnt, self.handJnt))
     
        #Create IK handle
        self.ikHNodes = ma.ikHandle(self.upperArmJnt, self.handJnt)
        
        #Rename handle
        self.ikH = ma.rename(self.ikHNodes[0], self.side+"_armIK_"+self.ikhPrefix)
        
        #Rename control ik end control
        self.ikHandCtlGrp = ma.rename(self.ikHandCtlGrp, self.side+"_armIKCtl_"+self.grpPrefix)
        self.ikHandCtl = ma.listRelatives(self.ikHandCtlGrp, f=True)
        #Rename Curve
        self.ikHandCtl = ma.rename(self.ikHandCtl, self.side+"_armIK_"+self.ctlPrefix)
        
        #Move end control to object
        pointConTemp = ma.pointConstraint(self.handJnt, self.ikHandCtlGrp)
        ma.delete(pointConTemp) #delete uneeded constraint
        #Constrain handle to control
        ma.pointConstraint(self.ikHandCtl, self.ikH)
        
        ##Create a polevector
        
        #Rename control ik Pole Vector control
        self.ikPVCtlGrp = ma.rename(self.ikPVCtlGrp, self.side+"_armPVCtl_"+self.grpPrefix)
        self.ikPVCtl = ma.listRelatives(self.ikPVCtlGrp, f=True)
        #Rename Curve
        self.ikPVCtl = ma.rename(self.ikPVCtl, self.side+"_armPV_"+self.ctlPrefix)
        
        #Move end Pole Vector to object
        pointConTemp = ma.pointConstraint(self.lowerArmJnt, self.ikPVCtlGrp)
        #Aim down the arm, set up vector to objectRotationUp, and up object to ikStartJnt
        aimConTemp = ma.aimConstraint(self.handJnt, self.ikPVCtlGrp, wut="object", wuo=self.upperArmJnt)
        
        #delete uneeded constraint
        ma.delete(pointConTemp)
        #delete unneeded constraint
        ma.delete(aimConTemp)
        
        #Move pole vector backwards
        ma.move(0, -50, 0, self.ikPVCtlGrp, os=True, r=True)
        ma.rotate(0, 0, 0, self.ikPVCtlGrp)
        
        #pole vector constraint
        ma.poleVectorConstraint(self.ikPVCtl, self.ikH)
        
    
    #Selection order: fkik Ctl, IKHndl, upperJnt, lowerJnt, endJnt, upperCtl, lowerCtl, endJntCtl
    def createArmFK(self):
        #rename FKIK control and grp
        self.fkikCtlGrp = ma.rename(self.fkikCtlGrp, self.side+"_armFKIKCtl_"+self.grpPrefix)
        self.fkikCtl = ma.listRelatives(self.fkikCtlGrp, f=True)[0]
        self.fkikCtl = ma.rename(self.fkikCtl, self.side+"_armFKIK_"+self.ctlPrefix)
        
        #Add Attributes to FKIK control
        ma.addAttr(self.fkikCtl, ln="FKIK", min = 0, max = 1, dv= 0, k=True)
        ma.connectAttr(self.fkikCtl+".FKIK", self.ikH+".ikBlend")
        
        #Move FKIK GRP
        pointConTemp = ma.pointConstraint(self.handJnt, self.fkikCtlGrp)
        ma.delete(pointConTemp)
        
        ctlCount = 0
        lastCtl = None
        for jnt, ctlGrp in zip([self.upperArmJnt,self.lowerArmJnt,self.handJnt],[self.upperFKCtlGrp,self.lowerFKCtlGrp,self.handFKCtlGrp]):
            ctlCount = ctlCount + 1
            #Get name of joint removing the _JNT prefix
            newCtlName = str(jnt).replace("_"+self.jntPrefix,"")
            #rename CtlGrp
            ctlGrp = ma.rename(ctlGrp, newCtlName.replace("Ctl","FK")+"Ctl_"+self.grpPrefix)
            #rename CTL
            ctlCrv = ma.listRelatives(ctlGrp, f=True)[0]
            ctlCrv = ma.rename(ctlCrv, newCtlName.replace("Ctl","FK")+"_"+self.ctlPrefix)
            
            #Point and orient! deleting after
            pointAndOrientSelected(item1=jnt,item2=ctlGrp)
            
            #Make direct connections between rotation of ctls and jnts
            ma.connectAttr(ctlCrv+".rotate",jnt+".rotate")
            
            #Store information in class self variables
            if ctlCount == 1:
                self.upperFKCtlGrp = ctlGrp
                self.upperFKCtl = ctlCrv
            elif ctlCount == 2:
                self.lowerFKCtlGrp = ctlGrp
                self.lowerFKCtl = ctlCrv
            else:
                self.handFKCtlGrp = ctlGrp
                self.handFKCtl = ctlCrv
            
            #Parent in hierachy!
            if lastCtl != None:
                ma.parent(ctlGrp, lastCtl)
                lastCtl = ctlCrv
            else:
                lastCtl = ctlCrv
                
    def createShoulderCtl(self):
        #move shoulder into place
        
        self.pointAndOrientSelected(item1=self.shoulderJnt, item2=self.shoulderCtlGrp)
        
        #rename shoulder and ctl
        self.shoulderCtlGrp = ma.rename(self.shoulderCtlGrp, self.side+"_shldrCtl_"+self.grpPrefix)
        self.shoulderCtl = ma.listRelatives(self.shoulderCtlGrp, f=True)[0]
        self.shoulderCtl = ma.rename(self.shoulderCtl, self.side+"_shldr_"+self.ctlPrefix)
        
        #parent arm fk under shoulder
        ma.parent(self.upperFKCtlGrp, self.shoulderCtl)
        
        #parent constrain to the left shoulder ctl
        ma.parentConstraint(self.shoulderCtl, self.shoulderJnt)
        
        
what=armBuilder()

what.createArmIK()
what.createArmFK()
what.createShoulderCtl()
