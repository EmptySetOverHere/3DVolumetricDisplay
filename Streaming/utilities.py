import math
import sys
from enum import Enum
from queue import Queue
from typing import *

import time
import ajiledriver as aj

# Specify the project name
PROJECT_TITLE: str = "DIP-Streaming"

# Specify the source folder of images we want to load 
IMAGE_FOLDER_NAME: str = "./wolfrunNEW_3blade1995"

class AJParameters:
    # default connection settings
    ipAddress = "192.168.200.1"
    netmask = "255.255.255.0"
    gateway = "0.0.0.0"
    port = 5005
    commInterface = aj.USB2_INTERFACE_TYPE
    deviceNumber = 0

    # default sequence settings
    repeatCount = 1 # repeat forever
    frameTime_ms = 0.150 # frame time in milliseconds
    sequenceID = 1

    # camera settings
    bitDepth = aj.CMV4000_BIT_DEPTH
    roiFirstRow = 0
    roiNumRows = aj.CMV4000_IMAGE_HEIGHT_MAX
    subsampleRowSkip = 0
    

class ErrorType(int, Enum):
    # Error type mapping for the defined errors in Ajile Driver
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

class RunState(int, Enum):
    # RunState mapping for defined RunState in Ajile Driver
    RUN_STATE_PARKED=1,
    RUN_STATE_STOPPED=2,
    RUN_STATE_RUNNING=3,
    RUN_STATE_PAUSED=4
    

class ControlInputsEnum(int, Enum):
    UNDEFINED_CONTROL_INPUT = 0
    START_FRAME = 1
    END_FRAME = 2
    START_LIGHTING = 3
    END_LIGHTING = 4
    START_SEQUENCE_ITEM = 5
    EXT_TRIGGER_OUTPUT_1 = 6
    EXT_TRIGGER_OUTPUT_2 = 7
    EXT_TRIGGER_OUTPUT_3 = 8
    EXT_TRIGGER_OUTPUT_4 = 9
    EXT_TRIGGER_OUTPUT_5 = 10
    EXT_TRIGGER_OUTPUT_6 = 11
    EXT_TRIGGER_OUTPUT_7 = 12
    EXT_TRIGGER_OUTPUT_8 = 13

class StateOutputsEnum(int, Enum):
    UNDEFINED_STATE_OUTPUT = 128
    NEXT_FRAME_READY = 129
    FRAME_STARTED = 130
    FRAME_ENDED = 131
    LIGHTING_STARTED = 132
    LIGHTING_ENDED = 133
    SEQUENCE_ITEM_STARTED = 134
    SEQUENCE_ITEM_ENDED = 135
    EXT_TRIGGER_INPUT_1 = 136
    EXT_TRIGGER_INPUT_2 = 137
    EXT_TRIGGER_INPUT_3 = 138
    EXT_TRIGGER_INPUT_4 = 139
    EXT_TRIGGER_INPUT_5 = 140
    EXT_TRIGGER_INPUT_6 = 141
    EXT_TRIGGER_INPUT_7 = 142
    EXT_TRIGGER_INPUT_8 = 143
    LIGHTING_ON = 150

class TriggerType(int, Enum):
    RISING_EDGE = 1
    FALLING_EDGE = 2
    ANY_EDGE = 3
    ACTIVE_HIGH_LEVEL = 4
    ACTIVE_LOW_LEVEL = 5

class DeviceTypeEnum(int, Enum):
    UNDEFINED_DEVICE_TYPE = 0
    PC_DEVICE_TYPE = 1
    AJILE_2PORT_CONTROLLER_DEVICE_TYPE = 2
    AJILE_3PORT_CONTROLLER_DEVICE_TYPE = 3
    DMD_3000_DEVICE_TYPE = 4
    DMD_4500_DEVICE_TYPE = 5
    CMV_4000_MONO_DEVICE_TYPE = 6
    CMV_2000_MONO_DEVICE_TYPE = 7
    AJILE_CONTROLLER_DEVICE_TYPE = 10
    LIGHTING_CONTROLLER_DEVICE_TYPE = 11
    DMD_CAMERA_CONTROLLER_DEVICE_TYPE = 12

class CommunicationInterfaceTypeEnum(int, Enum):
    UNDEFINED_COMMUNCATION_INTERFACE_TYPE = 0
    GIGE_INTERFACE_TYPE = 1
    USB2_INTERFACE_TYPE = 2
    USB3_INTERFACE_TYPE = 3
    PCIE_INTERFACE_TYPE = 4
    EMBEDDED_INTERFACE_TYPE = 5
    AJP_INTERFACE_TYPE = 6


def calc_frame_time_from_motor_speed(motor_speed: float, number_of_ticks: int = 1600) -> float:
    """
    It only works when motor_speed is in rev/min and it returns frametime in milliseconds  
    """
    frame_time = 60 * 1000 / (motor_speed * number_of_ticks)
    if 0 < frame_time < 1:
        raise f"Invalid frame time: {frame_time}ms. Please adjust motor speed or number of ticks per revolution"
    return frame_time

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
def get_command_arguments():
    # read command line arguments
    parameters = AJParameters
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

    return parameters


class GaugedQueue(Queue):
    
    def __init__(self, measure_per = 100):
        super().__init__()
        self.prev_put = None
        self.prev_get = None
        self.put_count = 0
        self.get_count = 0
        
        self.measure_per = measure_per
                    
    
    def put(self, item: Any, block: bool = True, timeout: Union[float, None] = None) -> None:
        
        if self.prev_put is None:
            self.prev_put = time.time() 
        
        elif self.put_count % self.measure_per == 0:
            now = time.time()
            print(f"Input frame rate: {self.measure_per  / (self.prev_put - now)} fps")
            self.prev_put = now
            
                
        self.put_count += 1
        return super().put(item, block, timeout)


    def get(self, block: bool = True, timeout: Union[float, None] = None) -> Any:
        if self.prev_get is None:
            self.prev_get = time.time() 
        
        elif self.get_count % self.measure_per == 0:
            now = time.time()
            print(f"Input frame rate: {self.measure_per  / (self.prev_put - now)} fps")
            self.prev_get = now

        self.get_count += 1
        return super().get(block, timeout)

if __name__ == "__main__":
    
    print(calc_frame_time_from_motor_speed(866.5))