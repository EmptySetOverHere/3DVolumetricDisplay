# Native modules
import cv2
import os
import asyncio
import numpy as np
from typing import *
from collections import deque
from concurrent.futures import ThreadPoolExecutor

# Third-party modules
import ajiledriver as aj

# Project modules
from utilities import *



PROJECT_TITLE: str = "DIP-Streaming"


def read_and_shrink_image(path_to_file: str) -> np.ndarray:
    """
    Load and process the image here
    This function will be executed in parallel later in the asynchronous call
    """
    cv_image = cv2.imread(path_to_file, cv2.IMREAD_GRAYSCALE)
    np_image = np.zeros((cv_image.shape[0], cv_image.shape[1], 1), dtype=np.uint8)
    np_image[:, :, 0] = cv_image[:, :]

    return np_image



async def load_images(image_directory: str = IMAGE_FOLDER_NAME) -> Deque[np.ndarray]:
    """
    async IO to load images and return them in a deque
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
                
        np_image = await asyncio.gather(*tasks)                   
        
    return deque(np_image)

    
def connect_device():    
    # connect to the device
    ajileSystem = aj.HostSystem()
    ajileSystem.SetConnectionSettingsStr(
        AJParameters.ipAddress, 
        AJParameters.netmask, 
        AJParameters.gateway, 
        AJParameters.port
    )
    
    ajileSystem.SetCommunicationInterface(AJParameters.commInterface)
    if ajileSystem.StartSystem() != aj.ERROR_NONE:
        print("Error starting AjileSystem.")
        sys.exit(-1)
    
    return ajileSystem


def retrieve_components(device_connected):
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
    project.AddSequence(aj.Sequence(AJParameters.sequenceID, project_title, device_type, aj.SEQ_TYPE_STREAM, 1, aj.SequenceItemList(), aj.RUN_STATE_PAUSED))

    return project


async def main():
    # connect to the device simultaneously with loading image into memory    
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=1) as executor:
        try_connect = loop.run_in_executor(executor, connect_device)

    device_connected, npImages = await asyncio.gather(try_connect, load_images())
    
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
    dmdImageSize = imageWidth * imageHeight / 8
    maxStreamingSequenceItems = 100
    frameNum = 1

    keyPress = '0'
    while keyPress != 'q' and keyPress != 'Q':
        if not driver.IsSequenceStatusQueueEmpty(dmdIndex):
            seqStatus = driver.GetNextSequenceStatus(dmdIndex);
        if driver.GetNumStreamingSequenceItems(dmdIndex) < maxStreamingSequenceItems:
            # generate a new image with OpenCV
            streamingImage = aj.Image()
            try:
                npImage = npImages.popleft()
            except:
                print("No more image")
                break

            streamingImage.ReadFromMemory(npImage, 8, aj.ROW_MAJOR_ORDER, deviceType)
            # create a new sequence item and frame to be streamed
            streamingSeqItem = aj.SequenceItem(AJParameters.sequenceID, 1)
            streamingFrame = aj.Frame(AJParameters.sequenceID, 0, aj.FromMSec(AJParameters.frameTime_ms), 0, 0, imageWidth, imageHeight);
            # attach the next streaming image to the streaming frame
            streamingFrame.SetStreamingImage(streamingImage)
            frameNum += 1
            # add the frame to the streaming sequence item
            streamingSeqItem.AddFrame(streamingFrame)
            
            # send the streaming sequence item to the device
            driver.AddStreamingSequenceItem(streamingSeqItem, dmdIndex)
        else:
            # when enough images have been preloaded start the streaming sequence
            if device_connected.GetDeviceState(dmdIndex).RunState() == aj.RUN_STATE_STOPPED:
                driver.StartSequence(AJParameters.sequenceID, dmdIndex)
            # check for a keypress to quit
            # cv2.imshow("AJILE Streaming DMD Example", npImage)
            keyPress = cv2.waitKey(10)
            keyPress = chr(keyPress%256) if keyPress%256 < 128 else '?'

    # stop the device when we are done
    driver.StopSequence(dmdIndex)
    print ("Waiting for the sequence to stop.\n")
    while device_connected.GetDeviceState(dmdIndex).RunState() == aj.RUN_STATE_RUNNING: pass

    return 0

if __name__ == "__main__":
    asyncio.run(main())