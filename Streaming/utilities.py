import sys
import time
from collections import deque
from typing import *

import ajiledriver as aj
from constants import *

def getImageSize(project, componentIndex):
    component = project.Components()[componentIndex]
    imageSize = component.NumRows() * component.NumColumns()
    if (component.DeviceType().HardwareType() == aj.DMD_4500_DEVICE_TYPE or
        component.DeviceType().HardwareType() == aj.DMD_3000_DEVICE_TYPE):
        imageSize = imageSize / 8
    return imageSize


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
def get_command_arguments() -> AJParameters:
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


class GaugedQueue(deque):
    
    def __init__(self, measure_per = 100):
        super().__init__()
        self.prev_put = None
        self.prev_get = None
        self.put_count = 0
        self.get_count = 0
        
        self.measure_per = measure_per
    
    def put(self, item: Any) -> None:
        
        if self.prev_put is None:
            self.prev_put = time.time() 
        
        elif self.put_count % self.measure_per == 0 and self.put_count != 0:
            now = time.time()
            print(f"Input frame rate: {self.measure_per  / (now - self.prev_put)} fps")
            self.prev_put = now
                
        self.put_count += 1
        super().append(item)


    def get(self) -> Any:
        
        if self.prev_get is None:
            self.prev_get = time.time() 
        
        elif self.get_count % self.measure_per == 0 and self.get_count != 0:
            now = time.time()
            print(f"Output frame rate: { self.measure_per  / (now - self.prev_get)} fps")
            self.prev_get = now
            print(f"No of remaining items: {len(self)}")

        
        self.get_count += 1
        return super().popleft()

if __name__ == "__main__":
    
    print(calc_frame_time_from_motor_speed(866.5))