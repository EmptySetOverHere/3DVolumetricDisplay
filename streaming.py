import cv2
import numpy as np
import os
import time 
import asyncio
from typing import *
import math

import ajiledriver as aj

from utilities import *


async def loadImagesFromFile(image_directory: str = IMAGE_FOLDER_NAME) -> List[np.ndarray]:
    """
    The function return list of numpy images
    """
    npImages = []
        
    if os.path.exists(image_directory):
        imageCount = 0
        for dirpath, dirname, files in os.walk(image_directory):
            for filename in files:
                filename = files[imageCount] 
                cvImage = cv2.imread(os.path.join(dirpath, filename), cv2.IMREAD_GRAYSCALE) # this generate 2D image
                npImage = np.zeros((cvImage.shape[0], cvImage.shape[1], 1), dtype=np.uint8)
                npImage[:, :, 0] = cvImage[:, :]
                npImages.append(npImages)
                imageCount += 1
    else:
        raise (f"Project Aborted: Unable to find target folder {image_directory}")


async def RunStreaming():

    # connect to the device
    ajileSystem = aj.HostSystem()
    driver = ajileSystem.GetDriver()
    ajileSystem.SetConnectionSettingsStr(ipAddress, netmask, gateway, port)
    ajileSystem.SetCommunicationInterface(commInterface)
    if ajileSystem.StartSystem() != aj.ERROR_NONE:
        print ("Error starting AjileSystem.")
        sys.exit(-1)

    # create the project
    project = aj.Project("dmd_binary_streaming_example")
    # get the connected devices from the project structure
    project.SetComponents(ajileSystem.GetProject().Components())

    dmdIndex = ajileSystem.GetProject().GetComponentIndexWithDeviceType(aj.DMD_4500_DEVICE_TYPE)
    if dmdIndex < 0:
        dmdIndex = ajileSystem.GetProject().GetComponentIndexWithDeviceType(aj.DMD_3000_DEVICE_TYPE)
    
    # stop any existing project from running on the device
    driver.StopSequence(dmdIndex)

    print ("Waiting for the sequence to stop.")
    while ajileSystem.GetDeviceState(dmdIndex).RunState() != aj.RUN_STATE_STOPPED: pass

    # set the project components and the image size based on the DMD type
    imageWidth = ajileSystem.GetProject().Components()[dmdIndex].NumColumns()
    imageHeight = ajileSystem.GetProject().Components()[dmdIndex].NumRows()
    deviceType = ajileSystem.GetProject().Components()[dmdIndex].DeviceType().HardwareType()
    
    # create the streaming sequence
    project.AddSequence(aj.Sequence(sequenceID, "dmd_binary_streaming_example", deviceType, aj.SEQ_TYPE_STREAM, 1, aj.SequenceItemList(), aj.RUN_STATE_PAUSED))

    # load the project
    driver.LoadProject(project)
    driver.WaitForLoadComplete(-1)

    # local variables used to generate DMD images
    dmdImageSize = imageWidth * imageHeight / 8
    maxStreamingSequenceItems = 100
    frameNum = 1

    imageGenerator = getImageInNP()

    keyPress = '0'
    while keyPress != 'q' and keyPress != 'Q':
        if not driver.IsSequenceStatusQueueEmpty(dmdIndex):
            seqStatus = driver.GetNextSequenceStatus(dmdIndex);
        if driver.GetNumStreamingSequenceItems(dmdIndex) < maxStreamingSequenceItems:
            # generate a new image with OpenCV
            
            streamingImage = aj.Image(frameNum)
            try:
                npImage = next(imageGenerator) # get the next numpy from wolfrun
            except:
                print("No more image from the image generator")
                break
            # print(npImage)
            # time.sleep(1)            
            
            if npImage is None:
                raise "Running out of images. Should Stop Streaming"
            
            streamingImage.ReadFromMemory(npImage, 8, aj.ROW_MAJOR_ORDER, deviceType)
            # create a new sequence item and frame to be streamed
            streamingSeqItem = aj.SequenceItem(sequenceID, 1)
            streamingFrame = aj.Frame( sequenceID, 0, aj.FromMSec(frameTime_ms), 0, 0, imageWidth, imageHeight);
            # attach the next streaming image to the streaming frame
            streamingFrame.SetStreamingImage(streamingImage)
            frameNum += 1
            # add the frame to the streaming sequence item
            streamingSeqItem.AddFrame(streamingFrame)
            
            # send the streaming sequence item to the device
            driver.AddStreamingSequenceItem(streamingSeqItem, dmdIndex)
        else:
            # when enough images have been preloaded start the streaming sequence
            if ajileSystem.GetDeviceState(dmdIndex).RunState() == aj.RUN_STATE_STOPPED:
                driver.StartSequence(sequenceID, dmdIndex)
            # check for a keypress to quit
            # cv2.imshow("AJILE Streaming DMD Example", npImage)
            keyPress = cv2.waitKey(10)
            keyPress = chr(keyPress%256) if keyPress%256 < 128 else '?'

    # stop the device when we are done
    driver.StopSequence(dmdIndex)
    print ("Waiting for the sequence to stop.\n")
    while ajileSystem.GetDeviceState(dmdIndex).RunState() == aj.RUN_STATE_RUNNING: pass

    return 0

if __name__ == "__main__":

    import sys
    sys.path.insert(0, "../../common/python/")

    asyncio.create_task(RunStreaming)
