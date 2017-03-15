import adsk.core, adsk.fusion, traceback

from . import Fusion360CommandBase

# Utility casts various inputs into appropriate Fusion 360 Objects
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

# Utility to get and format the various inputs
def getInputs(command, inputs):
    selectionInput = None

    for inputI in inputs:
        global commandId
        if inputI.id == command.parentCommandDefinition.id + '_selection':
            selectionInput = inputI
        elif inputI.id == command.parentCommandDefinition.id + '_plane':
            planeInput = inputI
        elif inputI.id == command.parentCommandDefinition.id + '_spacing':
            spacingInput = inputI
            spacing = spacingInput.value
        elif inputI.id == command.parentCommandDefinition.id + '_edge':
            edgeInput = inputI
        elif inputI.id == command.parentCommandDefinition.id + '_subAssy':
            subAssyInput = inputI
            subAssy = subAssyInput.value

    objects = getSelectedObjects(selectionInput)
    plane = getSelectedObjects(planeInput)[0]
    edge = adsk.fusion.BRepEdge.cast(edgeInput.selection(0).entity)

    if not objects or len(objects) == 0:
        # TODO this probably requires much better error handling
        return
    # return(objects, plane, edge, spacing, subAssy)

    return (objects, plane, edge, spacing)


# Creates a linked copy of all components in a new Sub Assembly
def createSubAssy(objects):
    app = adsk.core.Application.get()
    product = app.activeProduct
    design = adsk.fusion.Design.cast(product)

    # Get the root component and create a new component
    rootComp = design.rootComponent
    nestComp_Occ = rootComp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    nestComp = nestComp_Occ.component
    nestComp.name = "Nested Assembly"

    # Create a new empty collection to hold new references
    newFaces = adsk.core.ObjectCollection.create()

    # Iterate the selected face
    for originalFace in objects:

        # Get the native face from the proxy (selected face)
        nativeFace = originalFace.nativeObject

        # Copy the parent component of this face into the nested sub assy component
        newOccurence = nestComp.occurrences.addExistingComponent(originalFace.assemblyContext.component, adsk.core.Matrix3D.create())

        # Get the same face but in the context of the new occurrence
        newFace = nativeFace.createForAssemblyContext(newOccurence)

        # ADd the new face to the collection
        newFaces.add(newFace)

    return newFaces


# Create sliding planar joints between two faces
def createJoint(face1, face2):
    app = adsk.core.Application.get()
    ui = app.userInterface
    product = app.activeProduct
    design = adsk.fusion.Design.cast(product)

    # Get the root component of the active design
    rootComp = design.rootComponent

    if face1.assemblyContext == face2.assemblyContext:
        ui.messageBox("Faces are from the same Component.  Each part must be a component")
        adsk.terminate()

    elif not face2.assemblyContext:
        ui.messageBox("Face is from the root component.  Each part must be a component")
        adsk.terminate()

    elif not face1.assemblyContext:
        ui.messageBox("Face is from the root component.  Each part must be a component")
        adsk.terminate()

    else:
        # Create the joint geometry
        geo0 = adsk.fusion.JointGeometry.createByPlanarFace(face1, None, adsk.fusion.JointKeyPointTypes.CenterKeyPoint)
        geo1 = adsk.fusion.JointGeometry.createByPlanarFace(face2, None, adsk.fusion.JointKeyPointTypes.CenterKeyPoint)

        # Create joint input
        joints = rootComp.joints
        jointInput = joints.createInput(geo0, geo1)
        jointInput.setAsPlanarJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)

        # Create the joint
        joints.add(jointInput)

# Returns a normalized vector in positive XYZ space from a given edge
def getPositiveUnitVectorFromEdge(edge):
    # Set up a vector based on input edge
    (returnValue, startPoint, endPoint) = edge.geometry.evaluator.getEndPoints()
    directionVector = adsk.core.Vector3D.create(endPoint.x - startPoint.x,
                                           endPoint.y - startPoint.y,
                                           endPoint.z - startPoint.z )
    directionVector.normalize()

    if (directionVector.x < 0):
        directionVector.x *= -1
    if (directionVector.y < 0):
        directionVector.y *= -1
    if (directionVector.z < 0):
        directionVector.z *= -1

    return directionVector

# Returns the magnatude of the bounding box in the specified direction
def getBoundingBoxExtentInDirection(select, directionVector):
    maxPoint = select.boundingBox.maxPoint
    minPoint = select.boundingBox.minPoint
    deltaVector = adsk.core.Vector3D.create(maxPoint.x - minPoint.x,
                                            maxPoint.y - minPoint.y,
                                            maxPoint.z - minPoint.z )

    delta = deltaVector.dotProduct(directionVector)
    return delta

# Transforms an occurance along a specified vector by a specified amount
def transformAlongVector(select, directionVector, magnatude):

    # Create a vector for the translation
    vector = directionVector.copy()
    vector.scaleBy(magnatude)

    # Create a transform to do move
    transform = adsk.core.Matrix3D.cast(select.assemblyContext.transform)
    newTransform = adsk.core.Matrix3D.create()
    newTransform.translation = vector
    transform.transformBy(newTransform)

    # Transform Component
    select.assemblyContext.transform = transform

# Arranges components on a plane with a given spacing
def arrangeComponents(objects, plane, edge, spacing):

    app = adsk.core.Application.get()
#    ui = app.userInterface
    product = app.activeProduct
    design = adsk.fusion.Design.cast(product)

    # Get Placement Direction from Edge
    directionVector = getPositiveUnitVectorFromEdge(edge)

    # Get extents of stock in placement direction
    deltaPlane = getBoundingBoxExtentInDirection(plane, directionVector)

    # Set initial magnatude
    magnatude = 0.0
    magnatude -= deltaPlane / 2

    # Iterate and place components
    for select in objects:

        # Get extents of current component in placement direction
        delta = getBoundingBoxExtentInDirection(select, directionVector)

        # Increment magnatude by desired component size and spacing
        magnatude += spacing
        magnatude += delta / 2

        # Move component in specified direction by half its width
        transformAlongVector(select, directionVector, magnatude)

        # Increment spacing value for next component
        magnatude += delta / 2

    # Create Snapshot of current Component Positions
#    mysnapshots = design.snapshots
#    mysnapshots.add()

class NesterCommand(Fusion360CommandBase.Fusion360CommandBase):
    def onPreview(self, command, inputs):
        pass
    def onDestroy(self, command, inputs, reason_):
        pass
    def onInputChanged(self, command, inputs, changedInput):
        pass
    def onExecute(self, command, inputs):

        # Get Input values
        # (objects, plane, edge, spacing, subAssy) = getInputs(command, inputs)
        (objects, plane, edge, spacing) = getInputs(command, inputs)

        # # Create Sub-assembly
        # if subAssy:
        #     newFaces = createSubAssy(objects)
        # else:

        newFaces = objects

        # Apply Joints
        for face in newFaces:
            createJoint(face, plane)

        # Arrange Components
        arrangeComponents(newFaces, plane, edge, spacing)

    def onCreate(self, command, inputs):
        selectionPlaneInput = inputs.addSelectionInput(command.parentCommandDefinition.id + '_plane', 'Select Base Face', 'Select Face to mate to')
        selectionPlaneInput.setSelectionLimits(1,1)
        selectionPlaneInput.addSelectionFilter('PlanarFaces')

        selectionInput = inputs.addSelectionInput(command.parentCommandDefinition.id + '_selection', 'Select other faces', 'Select bodies or occurrences')
        selectionInput.setSelectionLimits(1,0)
        selectionInput.addSelectionFilter('PlanarFaces')

        selectionEdgeInput = inputs.addSelectionInput(command.parentCommandDefinition.id + '_edge', 'Select Direction (edge)', 'Select an edge to define spacing direction')
        selectionEdgeInput.setSelectionLimits(1,1)
        selectionEdgeInput.addSelectionFilter('LinearEdges')

        app = adsk.core.Application.get()
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        unitsMgr = design.unitsManager
        spacingInput = inputs.addValueInput(command.parentCommandDefinition.id + '_spacing', 'Component Spacing',
                                            unitsMgr.defaultLengthUnits,
                                                adsk.core.ValueInput.createByReal(2.54))
        # createSubAssyInput = inputs.addBoolValueInput(command.parentCommandDefinition.id + '_subAssy', "Create Sub-Assembly", True)
