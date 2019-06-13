import maya.cmds as ma

#Allows you to batch parent constrain skeletons to one another without having to go through each bone manually

def constrainParentSelectedBatch():
    sel = ma.ls(sl=True)
    if len(sel) < 3:
        print "This tool is for parent constraining multiple joints in a chain at once!"
    else:
        if len(sel) % 2 == 0:
            ctlJnts = sel[:(len(sel)/2)]
            skelJnts = sel[(len(sel)/2):]
            print "Creating Parent Constraints: "
            for ctlJnt, skelJnt in zip(ctlJnts, skelJnts):
                print ctlJnt+" -> "+skelJnt
                ma.parentConstraint(ctlJnt,skelJnt)
        else:
            print "An even number of items must be selected in order for all items to be parent constrained properly!"
            
            
constrainParentSelectedBatch()