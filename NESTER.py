#Author-Autodesk Inc.
#Description-Apply an appearance to selected faces, bodies or occurrences.

import adsk.core, adsk.fusion, traceback

app = None
ui  = None
commandId = 'ApplyAppearanceToSelectionCommand'
commandName = 'ApplyAppearanceToSelection'
commandDescription = 'Apply an appearance to selected bodies or occurrences'

# global set of event handlers to keep them referenced for the duration of the command
handlers = []
appearancesMap = {}
        
def clearAllItems(cmdInput):
    cmdInput.listItems.add('None', True, '')
    while cmdInput.listItems.count > 1:
        if cmdInput.listItems[0].name != 'None':
            cmdInput.listItems[0].deleteMe()
        else:
            cmdInput.listItems[1].deleteMe()
            
def replaceItems(cmdInput, newItems):
    clearAllItems(cmdInput)
    if len(newItems) > 0:
        for item in newItems:
            cmdInput.listItems.add(item, False, '')
        cmdInput.listItems[1].isSelected = True
        cmdInput.listItems[0].deleteMe()

    
def getSelectedObjects(selectionInput):
    objects = []
    for i in range(0, selectionInput.selectionCount):
        selection = selectionInput.selection(i)
        selectedObj = selection.entity
        if adsk.fusion.BRepBody.cast(selectedObj) or \
           adsk.fusion.BRepFace.cast(selectedObj) or \
           adsk.fusion.Occurrence.cast(selectedObj):
           objects.append(selectedObj)
    return objects

def applyAppearanceToObjects(appearance, objects):
    for obj in objects:
        obj.appearance = appearance
        
def createJoint(face1, face2):
    product = app.activeProduct
    design = adsk.fusion.Design.cast(product)

    # Get the root component of the active design
    rootComp = design.rootComponent# Create the first joint geometry with the end face
    geo0 = adsk.fusion.JointGeometry.createByPlanarFace(face1, None, adsk.fusion.JointKeyPointTypes.CenterKeyPoint)
    
    # Create the second joint geometry with the sketch line
    geo1 = adsk.fusion.JointGeometry.createByPlanarFace(face2, None, adsk.fusion.JointKeyPointTypes.CenterKeyPoint)
    
    # Create joint input
    joints = rootComp.joints
    jointInput = joints.createInput(geo0, geo1)
    
    jointInput.setAsPlanarJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)

    
    # Create the joint
    joint = joints.add(jointInput)
        
class NesterInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            cmd = args.firingEvent.sender
            inputs = cmd.commandInputs

        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class NesterExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            cmd = args.firingEvent.sender
            inputs = cmd.commandInputs
            selectionInput = None

            for inputI in inputs:
                global commandId
                if inputI.id == commandId + '_selection':
                    selectionInput = inputI
                elif inputI.id == commandId + '_plane':
                    planeInput = inputI
                elif inputI.id == commandId + '_spacing':
                    spacingInput = inputI
            
            objects = getSelectedObjects(selectionInput)
            plane = getSelectedObjects(planeInput)
            if not objects or len(objects) == 0:
                return
            
            product = app.activeProduct
            design = adsk.fusion.Design.cast(product)
    
            movement = 0.0
            
            
            for select in objects:
                createJoint(select, plane[0])
            ui.messageBox('made joints')

            for select in objects:
                
                # Problem with Bounding Box Logic
                # Need to get Bounding box in frame of Assembly reference not in frame of body
                # delta = select.assemblyContext.component.bRepBodies[0].boundingBox.maxPoint.y 
                #        - select.assemblyContext.component.bRepBodies[0].boundingBox.minPoint.y       
                # movement += delta                
                
                # Create a transform to do move
                vector = adsk.core.Vector3D.create(0.0, movement, 0.0)
                transform = adsk.core.Matrix3D.cast(select.assemblyContext.transform)
                newTransform = adsk.core.Matrix3D.create()
                newTransform.translation = vector
                transform.transformBy(newTransform)
                
                # Create a transform to do move
                # transform = adsk.core.Matrix3D.cast(select.assemblyContext.transform)
                # transform.setCell(0,3,movement)
               
                # Transform Component
                select.assemblyContext.transform = transform
                
                # Increment Spacing Value
                movement += spacingInput.value
                
            # Snapshots are currently not working
            # Would update this and uncomment if bug is fixed
            # mysnapshots = design.snapshots
            # mysnapshots.add()
            
            

        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class NesterDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            # when the command is done, terminate the script
            # this will release all globals which will remove all event handlers
            adsk.terminate()
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class NesterCreatedHandler(adsk.core.CommandCreatedEventHandler):    
    def __init__(self):
        super().__init__()        
    def notify(self, args):
        try:
            cmd = args.command
            onExecute = NesterExecuteHandler()
            cmd.execute.add(onExecute)
            
            onDestroy = NesterDestroyHandler()
            cmd.destroy.add(onDestroy)
            onInputChanged = NesterInputChangedHandler()
            cmd.inputChanged.add(onInputChanged)
            # keep the handler referenced beyond this function
            handlers.append(onExecute)
            handlers.append(onDestroy)
            handlers.append(onInputChanged)
            inputs = cmd.commandInputs
            global commandId
            selectionPlaneInput = inputs.addSelectionInput(commandId + '_plane', 'Select Base Face', 'Select Face to mate to')
            selectionPlaneInput.setSelectionLimits(1)
            selectionPlaneInput.addSelectionFilter('PlanarFaces')
            
            selectionInput = inputs.addSelectionInput(commandId + '_selection', 'Select other faces', 'Select bodies or occurrences')
            selectionInput.setSelectionLimits(0)
            selectionInput.addSelectionFilter('PlanarFaces')
            
            spacingInput = inputs.addValueInput(commandId + '_spacing', 'Component Spacing', 'in', adsk.core.ValueInput.createByReal(2.54))        
            
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def main():
    try:
        global app
        app = adsk.core.Application.get()
        global ui
        ui = app.userInterface

        global commandId
        global commandName
        global commandDescription
        
        cmdDef = ui.commandDefinitions.itemById(commandId)
        if not cmdDef:
            cmdDef = ui.commandDefinitions.addButtonDefinition(commandId, commandName, commandDescription) # no resource folder is specified, the default one will be used

        onCommandCreated = NesterCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        # keep the handler referenced beyond this function
        handlers.append(onCommandCreated)

        inputs = adsk.core.NamedValues.create()
        cmdDef.execute(inputs)

        # prevent this module from being terminate when the script returns, because we are waiting for event handlers to fire
        adsk.autoTerminate(False)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

main()
