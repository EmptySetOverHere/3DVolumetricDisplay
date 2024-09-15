import math
import sys
from enum import Enum
from typing import *

import ajiledriver as aj

IMAGE_FOLDER_NAME = "./wolfrunNEW_3blade1995"

class AJParameters:
    # default connection settings
    ipAddress = "192.168.200.1"
    netmask = "255.255.255.0"
    gateway = "0.0.0.0"
    port = 5005
    commInterface = aj.USB2_INTERFACE_TYPE

    # default sequence settings
    frameTime_ms = 10 # frame time in milliseconds
    sequenceID = 1
    

class ErrorType_e(int, Enum):
    ERROR_NONE=0,
    ERROR_WARNING=1,    
    ERROR_CRITICAL=-1,
    ERROR_OUTOFRANGE=-2,
    ERROR_CONNECTION=-3,
    ERROR_TIMEDOUT=-4,
    ERROR_WRONGDEVICE=-5,
    ERROR_INVALID=-6,
    ERROR_OUT_OF_MEMORY=-7,
    ERROR_FILENAME=-8,
    ERROR_DATA=-9,
    ERROR_STATE=-10


def calcFrameTimeFromMotorSpeed(motor_speed: float, number_of_ticks: int = 1600) -> float:
    """
    It only works when motor_speed is in rev/min and it returns frametime in milliseconds  
    """
    frametime = 60 * 1000 / (motor_speed * number_of_ticks)
    if 0 < frametime < 1:
        raise f"Invalid frametime: {frametime}ms. Please adjust motor speed or number of ticks per revolution"
    return frametime

# Provided method in the example helper
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

# Provided method in the example helper
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


    
    
    
    
if __name__ == "__main__":
    
    print(calcFrameTimeFromMotorSpeed(866.5))