from typing import *
import sys
import ajiledriver as aj
import os.path
import cv2
import numpy

# # Python 2.x - 3.x workaround
# try:
#     input = raw_input
# except NameError:
#     pass


# fdsajfhdasjfhdsakjlfhjklsah

class ProjectorSettings:
    # default connection settings
    ipAddress = "192.168.200.1"
    netmask = "255.255.255.0"
    gateway = "0.0.0.0"
    port = 5005
    commInterface = aj.USB2_INTERFACE_TYPE
    deviceNumber = 0

    # default sequence settings
    repeatCount = 0 # repeat forever
    frameTime_ms = -1 # frame time in milliseconds
    sequenceID = 1

    # camera settings
    bitDepth = aj.CMV4000_BIT_DEPTH
    roiFirstRow = 0
    roiNumRows = aj.CMV4000_IMAGE_HEIGHT_MAX
    subsampleRowSkip = 0
    
def PrintUsage():
    print ("Usage: " + sys.argv[0] + " [options]")
    print ("Options:")
    print ("\t-h | --help:\t print this help message")
    print ("\t-i <IP address>:\t set the ip address")
    print ("\t-r <repeat count>:\t set the sequence repeat count")
    print ("\t-f <frame rate in ms>:\t set the frame rate, in milliseconds")
    print ("\t--usb3:\t use the USB3 interface (default is USB2)")
    print ("\t--pcie:\t use the PCIE interface (default is USB2)")
    print ("\t-d <deviceNumber>:\t use a different device number than device 0")
    print ("\t--roi <roiFirstRow> <roiNumRows>:\t set the region of interest (first row and number of rows) used by the camera")
    print ("\t--sub <subsampleRowSkip>:\t enable camera image subsampling, specifying the number of rows to skip between each row (e.g. 1 skips every other row so selects every 2nd row, 3 selects every 4th row, etc.")
    print("\t--bit <bit depth>:\t set the camera bit depth, either 10 (default) or 8")
    
def ParseCommandArguments(parameters):
    # read command line arguments
    i=1
    while i < len(sys.argv):
        if sys.argv[i] == "-h" or sys.argv[i] == "--help":
            PrintUsage()
        elif sys.argv[i] == "-i":
            parameters.ipAddress = sys.argv[i+1]
            i += 1
        elif sys.argv[i] == "-r":
            parameters.repeatCount = int(sys.argv[i+1])
            i += 1
        elif sys.argv[i] == "-f":
            parameters.frameTime_ms = float(sys.argv[i+1])
            i += 1
        elif sys.argv[i] == "--usb3":
            parameters.commInterface = aj.USB3_INTERFACE_TYPE
        elif sys.argv[i] == "--pcie":
            parameters.commInterface = aj.PCIE_INTERFACE_TYPE
        elif sys.argv[i] == "-d":
            parameters.deviceNumber = int(sys.argv[i+1])
            i += 1
        elif sys.argv[i] == "--roi":
            parameters.roiFirstRow = int(sys.argv[i+1])
            parameters.roiNumRows = int(sys.argv[i+2])
            i += 2
        elif sys.argv[i] == "--sub":
            parameters.subsampleRowSkip = int(sys.argv[i+1])
            i += 1
        elif sys.argv[i] == "--bit":
            parameters.bitDepth = int(sys.argv[i+1])
            i += 1
        else:
            PrintUsage()
            sys.exit(2)
        i += 1

def ConnectToDevice(ajileSystem, parameters):
    ajileSystem.SetConnectionSettingsStr(parameters.ipAddress, parameters.netmask, parameters.gateway, parameters.port)
    ajileSystem.SetCommunicationInterface(parameters.commInterface)
    ajileSystem.SetUSB3DeviceNumber(parameters.deviceNumber)
    if ajileSystem.StartSystem() != aj.ERROR_NONE:
        print ("Error starting AjileSystem. Did you specify the correct interface with the command line arguments, e.g. \"--usb3\"?")
        sys.exit(-1)

def RunExample(createFunction):
    return RunDmdExample(createFunction)
        
def RunDmdExample(createFunction):

    # read the input command line arguments
    parameters = ProjectorSettings()
    ParseCommandArguments(parameters)    

    # connect to the device
    ajileSystem = aj.HostSystem()
    ConnectToDevice(ajileSystem, parameters)
    print("Device has been connected")

    
    # create the project
    project = createFunction(parameters.sequenceID, parameters.repeatCount, parameters.frameTime_ms, ajileSystem.GetProject().Components())

    # get the first valid component index which will run the sequence
    sequence, wasFound = project.FindSequence(parameters.sequenceID)
    if not wasFound: sys.exit(-1)
    componentIndex = ajileSystem.GetProject().GetComponentIndexWithDeviceType(sequence.HardwareType())

    for component in ajileSystem.GetProject().Components():
        print(f"ImageMemorySize: {component.ImageMemorySize():x}")
    
    print(f"sequence size: {sequence.Size():x}")
   
    # stop any existing project from running on the device
    ajileSystem.GetDriver().StopSequence(componentIndex)

    # load the project to the device
    ajileSystem.GetDriver().LoadProject(project)
    ajileSystem.GetDriver().WaitForLoadComplete(-1)
    

    print("Project has been loaded")

    for sequenceID, sequence in project.Sequences().iteritems():
        # if using region-of-interest, switch to 'lite mode' to disable lighting/triggers and allow DMD to run faster
        roiWidthColumns = sequence.SequenceItems()[0].Frames()[0].RoiWidthColumns()
        if roiWidthColumns > 0 and roiWidthColumns < aj.DMD_3000_IMAGE_WIDTH_MAX:
            ajileSystem.GetDriver().SetLiteMode(True, componentIndex)
            
        # run the project
        if parameters.frameTime_ms > 0:
            print ("Starting sequence %d with frame rate %f and repeat count %d" % (sequence.ID(), parameters.frameTime_ms, parameters.repeatCount))

        error_type = ajileSystem.GetDriver().StartSequence(sequence.ID(), componentIndex)
        if error_type == -1:
            raise "error in starting the sequence"

        # wait for the sequence to start
        print ("Waiting for sequence %d to start" % (sequence.ID(),))
        while ajileSystem.GetDeviceState(componentIndex).RunState() != aj.RUN_STATE_RUNNING: pass

        if parameters.repeatCount == 0:
            input("Sequence repeating forever. Press Enter to stop the sequence")
            ajileSystem.GetDriver().StopSequence(componentIndex)

        print ("Waiting for the sequence to stop.")
        while ajileSystem.GetDeviceState(componentIndex).RunState() == aj.RUN_STATE_RUNNING: pass
