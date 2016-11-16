
import adsk.core, adsk.fusion, traceback

handlers = [] 

# Removes the command control and definition 
def cleanUpNavDropDownCommand(cmdId, DC_CmdId):
    
    objArrayNav = []
    dropDownControl_ = commandControlById_in_NavBar(DC_CmdId)
    commandControlNav_ = commandControlById_in_DropDown(cmdId, dropDownControl_)
        
    if commandControlNav_:
        objArrayNav.append(commandControlNav_)
    
    commandDefinitionNav_ = commandDefinitionById(cmdId)
    if commandDefinitionNav_:
        objArrayNav.append(commandDefinitionNav_)
        
    for obj in objArrayNav:
        destroyObject(obj)


# Finds command definition in active UI
def commandDefinitionById(cmdId):
    app = adsk.core.Application.get()
    ui = app.userInterface
    
    if not cmdId:
        ui.messageBox('Command Definition:  ' + cmdId + '  is not specified')
        return None
    commandDefinitions_ = ui.commandDefinitions
    commandDefinition_ = commandDefinitions_.itemById(cmdId)
    return commandDefinition_
    
def commandControlById_in_NavBar(cmdId):
    app = adsk.core.Application.get()
    ui = app.userInterface
    
    if not cmdId:
        ui.messageBox('Command Control:  ' + cmdId + '  is not specified')
        return None
    
    toolbars_ = ui.toolbars
    Nav_toolbar = toolbars_.itemById('NavToolbar')
    Nav_toolbarControls = Nav_toolbar.controls
    cmd_control = Nav_toolbarControls.itemById(cmdId)
    
    if cmd_control is not None:
        return cmd_control

# Get a commmand Control in a Nav Bar Drop Down    
def commandControlById_in_DropDown(cmdId, dropDownControl):   
    cmd_control = dropDownControl.controls.itemById(cmdId)
    
    if cmd_control is not None:
        return cmd_control

# Destroys a given object
def destroyObject(tobeDeleteObj):
    app = adsk.core.Application.get()
    ui = app.userInterface
    
    if ui and tobeDeleteObj:
        if tobeDeleteObj.isValid:
            tobeDeleteObj.deleteMe()
        else:
            ui.messageBox(tobeDeleteObj.id + 'is not a valid object')

# Returns the id of a Toolbar Panel in the given Workspace
def toolbarPanelById_in_Workspace(myWorkspaceID, myToolbarPanelID):
    app = adsk.core.Application.get()
    ui = app.userInterface
        
    Allworkspaces = ui.workspaces
    thisWorkspace = Allworkspaces.itemById(myWorkspaceID)
    allToolbarPanels = thisWorkspace.toolbarPanels
    ToolbarPanel_ = allToolbarPanels.itemById(myToolbarPanelID)
    
    return  ToolbarPanel_

# Returns the Command Control from the given panel
def commandControlById_in_Panel(cmdId, ToolbarPanel):
    
    app = adsk.core.Application.get()
    ui = app.userInterface
    
    if not cmdId:
        ui.messageBox('Command Control:  ' + cmdId + '  is not specified')
        return None
    
    cmd_control = ToolbarPanel.controls.itemById(cmdId)
    
    if cmd_control is not None:
        return cmd_control

# Base Class for creating Fusion 360 Commands
class Fusion360CommandBase:
    
    def __init__(self, commandName, commandDescription, commandResources, cmdId, myWorkspace, myToolbarPanelID, debug):
        self.commandName = commandName
        self.commandDescription = commandDescription
        self.commandResources = commandResources
        self.cmdId = cmdId
        self.myWorkspace = myWorkspace
        self.myToolbarPanelID = myToolbarPanelID
        self.debug = debug
        self.DC_CmdId = 'Show Hidden'
        
        # global set of event handlers to keep them referenced for the duration of the command
        self.handlers = []
        
        try:
            self.app = adsk.core.Application.get()
            self.ui = self.app.userInterface

        except:
            if self.ui:
                self.ui.messageBox('Couldn\'t get app or ui: {}'.format(traceback.format_exc()))
    
    def onPreview(self, command, inputs):
        pass 
    def onDestroy(self, command, inputs, reason_):    
        pass   
    def onInputChanged(self, command, inputs, changedInput):
        pass
    def onExecute(self, command, inputs):
        pass
    def onCreate(self, command, inputs):
        pass
     
    def onRun(self):
        global handlers

        try:
            app = adsk.core.Application.get()
            ui = app.userInterface
            commandDefinitions_ = ui.commandDefinitions
    
            toolbarPanel_ = toolbarPanelById_in_Workspace(self.myWorkspace, self.myToolbarPanelID)              
            allToolbarPanelControls_ = toolbarPanel_.controls               
            toolbarPanelControl_ = allToolbarPanelControls_.itemById(self.cmdId)

            if not toolbarPanelControl_:
                commandDefinition_ = commandDefinitions_.itemById(self.cmdId)
                if not commandDefinition_:
                    commandDefinition_ = commandDefinitions_.addButtonDefinition(self.cmdId, self.commandName, self.commandDescription, self.commandResources)
                
                onCommandCreatedHandler_ = CommandCreatedEventHandler(self)
                commandDefinition_.commandCreated.add(onCommandCreatedHandler_)
                handlers.append(onCommandCreatedHandler_)
                
                toolbarPanelControl_ = allToolbarPanelControls_.addCommand(commandDefinition_)
                toolbarPanelControl_.isVisible = True
        
        except:
            if ui:
                ui.messageBox('AddIn Start Failed: {}'.format(traceback.format_exc()))

    def onStop(self):
        try:
            app = adsk.core.Application.get()
            ui = app.userInterface

            toolbarPanel_ = toolbarPanelById_in_Workspace(self.myWorkspace, self.myToolbarPanelID)
            
            commandControlPanel_ = commandControlById_in_Panel(self.cmdId, toolbarPanel_)
            commandDefinitionPanel_ = commandDefinitionById(self.cmdId)
            destroyObject(commandControlPanel_)
            destroyObject(commandDefinitionPanel_)

        except:
            if ui:
                ui.messageBox('AddIn Stop Failed: {}'.format(traceback.format_exc()))

# Intended to create commands in a drop down menu in the nav bar    
class Fusion360NavCommandBase:
    
    def __init__(self, commandName, commandDescription, commandResources, cmdId, DC_CmdId, DC_Resources, debug):
        self.commandName = commandName
        self.commandDescription = commandDescription
        self.commandResources = commandResources
        self.cmdId = cmdId
        self.debug = debug
        self.DC_CmdId = DC_CmdId
        self.DC_Resources = DC_Resources
        
        # global set of event handlers to keep them referenced for the duration of the command
        self.handlers = []
        
        try:
            self.app = adsk.core.Application.get()
            self.ui = self.app.userInterface

        except:
            if self.ui:
                self.ui.messageBox('Couldn\'t get app or ui: {}'.format(traceback.format_exc()))

    def onPreview(self, command, inputs):
        pass
    
    def onDestroy(self, command, inputs, reason_):    
        pass
    
    def onInputChanged(self, command, inputs, changedInput):
        pass
    def onExecute(self, command, inputs):
        pass
    def onCreate(self, command, inputs):
        pass
     
    def onRun(self):
        global handlers

        try:
            app = adsk.core.Application.get()
            ui = app.userInterface
            commandDefinitions_ = ui.commandDefinitions
                
            toolbars_ = ui.toolbars
            navBar = toolbars_.itemById('NavToolbar')
            toolbarControlsNAV = navBar.controls
            
            dropControl = toolbarControlsNAV.itemById(self.DC_CmdId) 
            
            if not dropControl:             
                dropControl = toolbarControlsNAV.addDropDown(self.DC_CmdId, self.DC_Resources, self.DC_CmdId) 
            
            NAV_Control = toolbarControlsNAV.itemById(self.cmdId)
            
            if not NAV_Control:
                commandDefinition_ = commandDefinitions_.itemById(self.cmdId)
                if not commandDefinition_:
                    # commandDefinitionNAV = cmdDefs.addSplitButton(showAllBodiesCmdId, otherCmdDefs, True)
                    commandDefinition_ = commandDefinitions_.addButtonDefinition(self.cmdId, self.commandName, self.commandDescription, self.commandResources)
                
                onCommandCreatedHandler_ = CommandCreatedEventHandler(self)
                commandDefinition_.commandCreated.add(onCommandCreatedHandler_)
                handlers.append(onCommandCreatedHandler_)
                
                
                NAV_Control = dropControl.controls.addCommand(commandDefinition_)
                NAV_Control.isVisible = True
        
        except:
            if ui:
                ui.messageBox('AddIn Start Failed: {}'.format(traceback.format_exc()))

    
    def onStop(self):
        ui = None
        try:
            
            dropDownControl_ = commandControlById_in_NavBar(self.DC_CmdId)
            commandControlNav_ = commandControlById_in_DropDown(self.cmdId, dropDownControl_)
            commandDefinitionNav_ = commandDefinitionById(self.cmdId)
            destroyObject(commandControlNav_)
            destroyObject(commandDefinitionNav_)
            
            if dropDownControl_.controls.count == 0:
                commandDefinition_DropDown = commandDefinitionById(self.DC_CmdId)
                destroyObject(dropDownControl_)
                destroyObject(commandDefinition_DropDown)
             
        except:
            if ui:
                ui.messageBox('AddIn Stop Failed: {}'.format(traceback.format_exc()))


class ExecutePreviewHandler(adsk.core.CommandEventHandler):
    def __init__(self, myObject):
        super().__init__()
        self.myObject_ = myObject
    def notify(self, args):
        try:               
            app = adsk.core.Application.get()
            ui = app.userInterface
            command_ = args.firingEvent.sender
            inputs_ = command_.commandInputs
            if self.myObject_.debug:
                ui.messageBox('***Debug *** Preview: {} execute preview event triggered'.format(command_.parentCommandDefinition.id))
    
            self.myObject_.onPreview(command_, inputs_)
        except:
            if ui:
                ui.messageBox('Input changed event failed: {}'.format(traceback.format_exc()))
class DestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self, myObject):
        super().__init__()
        self.myObject_ = myObject
    def notify(self, args):
        # Code to react to the event.
        try:
            app = adsk.core.Application.get()
            ui = app.userInterface
            command_ = args.firingEvent.sender
            inputs_ = command_.commandInputs
            reason_ = args.terminationReason
            if self.myObject_.debug:
                ui.messageBox('***Debug ***Command: {} destroyed'.format(command_.parentCommandDefinition.id))
                ui.messageBox("***Debug ***Reason for termination= " + str(reason_))
            self.myObject_.onDestroy(command_, inputs_, reason_)
            
        except:
            if ui:
                ui.messageBox('Input changed event failed: {}'.format(traceback.format_exc()))

class InputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self, myObject):
        super().__init__()
        self.myObject_ = myObject
    def notify(self, args):
        try:
            app = adsk.core.Application.get()
            ui = app.userInterface
            command_ = args.firingEvent.sender
            inputs_ = command_.commandInputs
            changedInput_ = args.input 
            if self.myObject_.debug:
                ui.messageBox('***Debug ***Input: {} changed event triggered'.format(command_.parentCommandDefinition.id))
                ui.messageBox('***Debug ***The Input: {} was the command'.format(changedInput_.id))
   
            self.myObject_.onInputChanged(command_, inputs_, changedInput_)
        except:
            if ui:
                ui.messageBox('Input changed event failed: {}'.format(traceback.format_exc()))

class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self, myObject):
        super().__init__()
        self.myObject_ = myObject
    def notify(self, args):
        try:
            app = adsk.core.Application.get()
            ui = app.userInterface
            command_ = args.firingEvent.sender
            inputs_ = command_.commandInputs
            if self.myObject_.debug:
                ui.messageBox('***Debug ***command: {} executed successfully'.format(command_.parentCommandDefinition.id))
            self.myObject_.onExecute(command_, inputs_)
            
        except:
            if ui:
                ui.messageBox('command executed failed: {}'.format(traceback.format_exc()))

class CommandCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self, myObject):
        super().__init__()
        self.myObject_ = myObject
    def notify(self, args):
        try:
            global handlers
            
            app = adsk.core.Application.get()
            ui = app.userInterface
            command_ = args.command
            inputs_ = command_.commandInputs
            
            onExecuteHandler_ = CommandExecuteHandler(self.myObject_)
            command_.execute.add(onExecuteHandler_)
            handlers.append(onExecuteHandler_)
            
            onInputChangedHandler_ = InputChangedHandler(self.myObject_)
            command_.inputChanged.add(onInputChangedHandler_)
            handlers.append(onInputChangedHandler_)
            
            onDestroyHandler_ = DestroyHandler(self.myObject_)
            command_.destroy.add(onDestroyHandler_)
            handlers.append(onDestroyHandler_)
            
            onExecutePreviewHandler_ = ExecutePreviewHandler(self.myObject_)
            command_.executePreview.add(onExecutePreviewHandler_)
            handlers.append(onExecutePreviewHandler_)
            
            if self.myObject_.debug:
                ui.messageBox('***Debug ***Panel command created successfully')
            
            self.myObject_.onCreate(command_, inputs_)
        except:
                if ui:
                    ui.messageBox('Panel command created failed: {}'.format(traceback.format_exc()))