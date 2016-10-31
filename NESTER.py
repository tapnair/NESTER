from . import f360NesterCommand

commandName1 = 'f360Nester'
commandDescription1 = 'Basic Nesting for Fusion 360'
commandResources1 = './resources'
cmdId1 = 'cmdID_f360Nester'
myWorkspace1 = 'FusionSolidEnvironment'
myToolbarPanelID1 = 'SolidScriptsAddinsPanel'

debug = False

newCommand1 = f360NesterCommand.f360NesterCommand(commandName1, commandDescription1, commandResources1, cmdId1, myWorkspace1, myToolbarPanelID1, debug)



def run(context):
    newCommand1.onRun()
def stop(context):
    newCommand1.onStop()
    
