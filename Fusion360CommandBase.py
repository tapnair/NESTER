
import adsk.core, adsk.fusion, traceback

handlers = [] 

class Fusion360CommandBase:
    
    def __init__(self, commandName, commandDescription, commandResources, cmdId, myWorkspace, myToolbarPanelID, debug):
        self.commandName = commandName
        self.commandDescription = commandDescription
        self.commandResources = commandResources
        self.cmdId = cmdId
        self.myWorkspace = myWorkspace
        self.myToolbarPanelID = myToolbarPanelID
        self.debug = debug
        
        # global set of event handlers to keep them referenced for the duration of the command
        self.handlers = []
        
        try:
            self.app = adsk.core.Application.get()
            self.ui = self.app.userInterface

        except:
            if self.ui:
                self.ui.messageBox('Couldn\'t get app or ui: {}'.format(traceback.format_exc()))
    
    # FInds command definition in active UI
    def commandDefinitionById(self, id):

        if not id:
            self.ui.messageBox('commandDefinition id is not specified')
            return None
        commandDefinitions_ = self.ui.commandDefinitions
        commandDefinition_ = commandDefinitions_.itemById(id)
        return commandDefinition_
    
    
    def toolbarPanelByID(self, id, myWorkspaceID, myToolbarPanelID):

        if not id:
            self.ui.messageBox('commandControl id is not specified')
            return None
        Allworkspaces = self.ui.workspaces
        thisWorkspace = Allworkspaces.itemById(myWorkspaceID)
        allToolbarPanels = thisWorkspace.toolbarPanels
        thisToolbarPanel = allToolbarPanels.itemById(myToolbarPanelID)
        
        return  thisToolbarPanel
    
    def commandControlByIdForPanel(self, id):
        
        if not id:
            self.ui.messageBox('commandControl id is not specified')
            return None
        Allworkspaces = self.ui.workspaces
        thisWorkspace = Allworkspaces.itemById(self.myWorkspace)
        allToolbarPanels = thisWorkspace.toolbarPanels
        myToolbarPanel = allToolbarPanels.itemById(self.myToolbarPanelID)
        allToolbarControls = myToolbarPanel.controls
        
        return  allToolbarControls.itemById(id)
        
    def destroyObject(self, uiObj, tobeDeleteObj):
        if uiObj and tobeDeleteObj:
            if tobeDeleteObj.isValid:
                tobeDeleteObj.deleteMe()
            else:
                uiObj.messageBox('tobeDeleteObj is not a valid object')

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
    
            toolbarPanel_ = self.toolbarPanelByID(id, self.myWorkspace, self.myToolbarPanelID)              
            allToolbarPanelControls_ = toolbarPanel_.controls               
            toolbarPanelControl_ = allToolbarPanelControls_.itemById(self.cmdId)
            

            if not toolbarPanelControl_:
                commandDefinition_ = commandDefinitions_.itemById(self.cmdId)
                if not commandDefinition_:
                    commandDefinition_ = commandDefinitions_.addButtonDefinition(self.cmdId, self.commandName, self.commandDescription, self.commandResources)
                
                onCommandCreatedHandler_ = CommandCreatedEventHandlerPanel(self)
                commandDefinition_.commandCreated.add(onCommandCreatedHandler_)
                handlers.append(onCommandCreatedHandler_)
                
                toolbarPanelControl_ = allToolbarPanelControls_.addCommand(commandDefinition_)
                toolbarPanelControl_.isVisible = True
                    
        except:
            if ui:
                ui.messageBox('AddIn Start Failed: {}'.format(traceback.format_exc()))

    
    def onStop(self):
        ui = None
        try:
            app = adsk.core.Application.get()
            ui = app.userInterface
            objArray = []
    
            commandControl_ = self.commandControlByIdForPanel(self.cmdId)
            if commandControl_:
                objArray.append(commandControl_)
    
            commandDefinitionPanel_ = self.commandDefinitionById(self.cmdId)
            if commandDefinitionPanel_:
                objArray.append(commandDefinitionPanel_)
    
            for obj in objArray:
                self.destroyObject(ui, obj)
    
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
                ui.messageBox('***New *** Preview: {} execute preview event triggered'.format(command_.parentCommandDefinition.id))
    
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
                ui.messageBox('***New ***Command: {} destroyed'.format(command_.parentCommandDefinition.id))
                ui.messageBox("***New ***Reason for termination= " + str(reason_))
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
                ui.messageBox('***New ***Input: {} changed event triggered'.format(command_.parentCommandDefinition.id))
                ui.messageBox('***New ***The Input: {} was the command'.format(changedInput_.id))
   
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
                ui.messageBox('***New ***command: {} executed successfully'.format(command_.parentCommandDefinition.id))
            self.myObject_.onExecute(command_, inputs_)
            
        except:
            if ui:
                ui.messageBox('command executed failed: {}'.format(traceback.format_exc()))

class CommandCreatedEventHandlerPanel(adsk.core.CommandCreatedEventHandler):
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
                ui.messageBox('***New ***Panel command created successfully')
            
            self.myObject_.onCreate(command_, inputs_)
        except:
                if ui:
                    ui.messageBox('Panel command created failed: {}'.format(traceback.format_exc()))