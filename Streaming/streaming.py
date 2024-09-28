# Native modules
import cv2
import os
import asyncio
import numpy as np
import time
from typing import *
from collections import deque
from concurrent.futures import ThreadPoolExecutor

# Third-party modules
import ajiledriver as aj

# Project modules
from utilities import *
from constants import *

MESSAGE_QUEUE = GaugedQueue()

# Set-up parameters
PARAMS = get_command_arguments()

def find_region_of_interest(): ... # Unimplemented

def read_and_shrink_image(path_to_file: str) -> np.ndarray:
    """
    Load and process the image here
    This function will be executed in parallel later in the asynchronous call
    """
    # Read image in greyscale
    cv_image = cv2.imread(path_to_file, cv2.IMREAD_GRAYSCALE)
    
    # Convert to binary image
    # _, cv_image = cv2.threshold(cv_image, 127, 1, cv2.THRESH_BINARY) # This line causing problem
    required_shape = (cv_image.shape[0], cv_image.shape[1], 1)
    np_image = np.reshape(cv_image, newshape=required_shape)
    
    return np_image 


def prepare_streaming_sequence_item(np_image: np.array) -> Any:

    streamingImage = aj.Image()
    
    streamingImage.ReadFromMemory(np_image, 8, aj.ROW_MAJOR_ORDER, PARAMS.deviceType)
    # create a new sequence item and frame to be streamed
    streamingSeqItem = aj.SequenceItem(PARAMS.sequenceID, 1)
    streamingFrame = aj.Frame(PARAMS.sequenceID, 0, aj.FromMSec(PARAMS.frameTime_ms), 0, 0, PARAMS.imageWidth, PARAMS.imageHeight)
    # attach the next streaming image to the streaming frame
    streamingFrame.SetStreamingImage(streamingImage)
    # add the frame to the streaming sequence item
    streamingSeqItem.AddFrame(streamingFrame)
    
    return streamingSeqItem


def load_images_with_message_queue(stack_count: int = PARAMS.STACK_COUNT, image_directory: str = IMAGE_FOLDER_NAME) -> None:
    """
    synchronous IO to load images and append them in a deque
    """
    if not os.path.exists(image_directory):
        raise FileNotFoundError(f"Project Aborted: Unable to find target folder {image_directory}")
    
    for dirpath, _, files in os.walk(image_directory):
        
            for filename in files:
                path_to_file = os.path.join(dirpath, filename)
                img = read_and_shrink_image(path_to_file)
                seqItem = prepare_streaming_sequence_item(img)
                MESSAGE_QUEUE.put(seqItem)  
                
    
    for _ in range(stack_count): MESSAGE_QUEUE.extend(MESSAGE_QUEUE)
            
    print(f"Images are ready to send. Number of items: {len(MESSAGE_QUEUE)}")


async def load_images(image_directory: str = IMAGE_FOLDER_NAME) -> Deque[np.ndarray]:
    """
    Async IO to load images and return them in a deque
    TODO: This can be removed as it is testified that python does not implement true multithreading due to GIL
    """
    loop = asyncio.get_running_loop()
    tasks = []
    
    if not os.path.exists(image_directory):
        raise FileNotFoundError(f"Project Aborted: Unable to find target folder {image_directory}")
    

    with ThreadPoolExecutor() as executor:
        for dirpath, _, files in os.walk(image_directory):
            for filename in files:
                path_to_file = os.path.join(dirpath, filename)
                task = loop.run_in_executor(executor, read_and_shrink_image, path_to_file)
                tasks.append(task)
                
        np_images = await asyncio.gather(*tasks)
        
    return deque(np_images)

    
def connect_device():    
    # Connect with the DMD device
    
    ajileSystem = aj.HostSystem()
    ajileSystem.SetConnectionSettingsStr(
        PARAMS.ipAddress, 
        PARAMS.netmask, 
        PARAMS.gateway, 
        PARAMS.port
    )

    ajileSystem.SetUSB3DeviceNumber(PARAMS.deviceNumber)
    ajileSystem.SetCommunicationInterface(PARAMS.commInterface)
    if ajileSystem.StartSystem() != aj.ERROR_NONE:
        print("Error starting AjileSystem. Did you specify the correct interface with the command line arguments, e.g. \"--usb3\"?")
        return None
    
    print("Device connected. Waiting for a start. ")
    return ajileSystem


def retrieve_components(device_connected) -> Tuple[int, DeviceTypeEnum, int, int]:
    # set the project components and the image size based on the DMD type
    
    dmdIndex = device_connected.GetProject().GetComponentIndexWithDeviceType(aj.DMD_4500_DEVICE_TYPE)
    if dmdIndex < 0:
        dmdIndex = device_connected.GetProject().GetComponentIndexWithDeviceType(aj.DMD_3000_DEVICE_TYPE)
    
    imageWidth = device_connected.GetProject().Components()[dmdIndex].NumColumns()
    imageHeight = device_connected.GetProject().Components()[dmdIndex].NumRows()
    deviceType = device_connected.GetProject().Components()[dmdIndex].DeviceType().HardwareType()
    

    return dmdIndex, deviceType, imageWidth, imageHeight


def init_project(device_connected, device_type, project_title: str = PROJECT_TITLE):
    # create the project
    project = aj.Project(project_title)
    # get the connected devices from the project structure
    project.SetComponents(device_connected.GetProject().Components())
    # create the streaming sequence
    project.AddSequence(aj.Sequence(PARAMS.sequenceID, project_title, device_type, aj.SEQ_TYPE_STREAM, 1, aj.SequenceItemList(), aj.RUN_STATE_PAUSED))

    return project


def run_streaming_on(device_connected: Any):

    # Retrieve components from existing project
    dmdIndex, deviceType, imageWidth, imageHeight = retrieve_components(device_connected)
    
    # initialize the project
    project = init_project(device_connected, deviceType)

    driver = device_connected.GetDriver()

    # stop any existing project from running on the device
    driver.StopSequence(dmdIndex)
    print ("Waiting for the sequence to stop.")
    while device_connected.GetDeviceState(dmdIndex).RunState() != aj.RUN_STATE_STOPPED: pass
        
    # load the project
    driver.LoadProject(project)
    driver.WaitForLoadComplete(-1)

    # local variables used to generate DMD images
    maxStreamingSequenceItems = PARAMS.MaxStreamingMemoryUsage / getImageSize(project, dmdIndex)

    keyPress = '0'
    
    have_called = False # Ensure startSequence only get executed once
    
    while keyPress != 'q' and keyPress != 'Q' and len(MESSAGE_QUEUE) > 0:
        # if not driver.IsSequenceStatusQueueEmpty(dmdIndex):
        #     seqStatus = driver.GetNextSequenceStatus(dmdIndex)
        num_of_streaming_items = driver.GetNumStreamingSequenceItems(dmdIndex)
            
        if num_of_streaming_items < maxStreamingSequenceItems:
            streamingSeqItem = MESSAGE_QUEUE.get()
            # send the streaming sequence item to the device
            driver.AddStreamingSequenceItem(streamingSeqItem, dmdIndex)
            
        else:
            # when enough images have been preloaded start the streaming sequence
            if device_connected.GetDeviceState(dmdIndex).RunState() == aj.RUN_STATE_STOPPED and not have_called:
                print(f"Starting Sequence: {PARAMS.sequenceID}")
                driver.StartSequence(PARAMS.sequenceID, dmdIndex)
                have_called = True
            # check for a keypress to quit
            # cv2.imshow("AJILE Streaming DMD Example", npImage)
            keyPress = cv2.waitKey(10)
            keyPress = chr(keyPress % 256) if keyPress%256 < 128 else '?'

    # stop the device when we are done
    driver.StopSequence(dmdIndex)
    print ("Waiting for the sequence to stop.\n")
    
    while device_connected.GetDeviceState(dmdIndex).RunState() == aj.RUN_STATE_RUNNING: pass
    

async def test():
    # Will be using default parameters for local testing
    print("Device not detected running offline testing")
    
    load_images_with_message_queue()
    test_loop()

        
def test_loop():
    maxStreamingSequenceItems = 500
    num_of_streaming_items = 0

    while num_of_streaming_items < maxStreamingSequenceItems:
        time.sleep(0.01)
        if MESSAGE_QUEUE:
            item = MESSAGE_QUEUE.get()
            del item        
            num_of_streaming_items += 1

        
async def main():
    # connect to the device simultaneously with loading image into memory    
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=1) as executor:
        try_connect = loop.run_in_executor(executor, connect_device)
        prepare_images = loop.run_in_executor(executor, load_images_with_message_queue, 4)

    coroutines = [try_connect, prepare_images]
    device_connected, _ = await asyncio.gather(*coroutines)
    
    if device_connected is None: 
        print("Deviced undetected. Switch to test cases ")
        test()
        
    run_streaming_on(device_connected)
    
    print("Program ended without error")


if __name__ == "__main__":
    asyncio.run(main())