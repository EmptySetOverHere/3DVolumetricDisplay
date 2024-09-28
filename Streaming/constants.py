"""
Here we define the constants and settings required by the project 
"""

from enum import IntEnum
import ajiledriver as aj

# Specify the project name
PROJECT_TITLE: str = "DIP-Streaming"

# Specify the source folder of images we want to load 
IMAGE_FOLDER_NAME: str = "./wolfrunNEW_3blade1995"

class ErrorType(IntEnum):
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

class RunState(IntEnum):
    # RunState mapping for defined RunState in Ajile Driver
    RUN_STATE_PARKED=1,
    RUN_STATE_STOPPED=2,
    RUN_STATE_RUNNING=3,
    RUN_STATE_PAUSED=4
    

class ControlInputsEnum(IntEnum):
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

class StateOutputsEnum(IntEnum):
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

class TriggerType(IntEnum):
    RISING_EDGE = 1
    FALLING_EDGE = 2
    ANY_EDGE = 3
    ACTIVE_HIGH_LEVEL = 4
    ACTIVE_LOW_LEVEL = 5

class DeviceTypeEnum(IntEnum):
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

class CommunicationInterfaceTypeEnum(IntEnum):
    UNDEFINED_COMMUNCATION_INTERFACE_TYPE = 0
    GIGE_INTERFACE_TYPE = 1
    USB2_INTERFACE_TYPE = 2
    USB3_INTERFACE_TYPE = 3
    PCIE_INTERFACE_TYPE = 4
    EMBEDDED_INTERFACE_TYPE = 5
    AJP_INTERFACE_TYPE = 6
    
class AJParameters:
    # This is a static class stores default parameters
    
    # default connection settings
    ipAddress = "192.168.200.1"
    netmask = "255.255.255.0"
    gateway = "0.0.0.0"
    port = 5005
    commInterface = aj.USB2_INTERFACE_TYPE
    deviceNumber = 0

    # Default Components
    deviceType = DeviceTypeEnum.DMD_4500_DEVICE_TYPE
    imageWidth = 1140
    imageHeight = 912
    dmdIndex = 0

    # default sequence settings
    repeatCount = 1
    frameTime_ms = 0.150 # frame time in milliseconds
    sequenceID = 1
    
    STACK_COUNT = 1 # Number of time the Message Queue stacking itself, each time doubles it size
    
    MaxStreamingMemoryUsage = 0x80000000 # 2024 MB
    MaxStreamingFIFOSize = 0x02000000  # 32 M
    
    DMDGrayscaleFrameTime = [15000, 30000, 60000, 120000, 240000, 480000, 960000, 1920000]
    DMDGrayscaleLEDTimes = [15000, 30000, 60000, 120000, 240000, 480000, 960000, 1920000]
    
    

