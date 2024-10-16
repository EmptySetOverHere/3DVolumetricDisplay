import serial
import serial.tools.list_ports

import time
import asyncio

from IPython.display import display

import numpy as np

class STmic:
    #motor related consts
    HIGH_VOLTAGE_THRESHOLD = 3.0 #CONST #threshold before the voltage becomes high from undefined
    LOW_VOLTAGE_THRESHOLD = 0.5 #CONST #theshold before the voltage becomes undefined
    HALL_SENSOR_COUNT = 3200

    def __init__(self, motor_RPM = 900):
        ports=serial.tools.list_ports.comports()
        for p in ports:
            if p.vid==61525 and p.pid==38912:
                self.device=serial.Serial(p.device,baudrate=115200)
        if not hasattr(self,'device'):
            raise Exception('No controller unit detected')
        self.previous_voltage_state = 0 #0 for low voltage 1 for high voltage
        self.motor_phase_enum = 0 #0-3199 for each hall sensor
        self.motor_RPM = motor_RPM
        #projector related variables
        self.current_image = 0 #current image index
        self.projection_state = 0 #1 for start, 0 for stop(terminate), 2 for starting(projector is ready), 3 for initialising(projector is starting up)
        self.image_lengths = [] #image_lengths = [1,3,3] means image 0 exposure duration is 1, image 1 exposure duration is 3,image 3 exposure duration is 3
        self.exposure_counts = 0 #number of exposures the current image has already experienced
        self.frames_backlog = 0
            
    def __del__(self):
        self.device.close()
    
    #this method reads voltage for 2v scale
    def read_voltage(self):
        cmd = "m1"+"200000"+ "1" + "160" + "130" + "1" + "160" + "130"+ "\r"
        bytedata=bytearray(4*4)
        self.device.reset_output_buffer()
        self.device.reset_input_buffer()
        self.device.write(bytes(cmd,'utf-8'))
        self.device.readline()
        self.device.readinto(bytedata)
        data=np.frombuffer(bytedata,dtype='uint16').reshape((2,4))
        raw1=7.9000*(1.94-1.5*data[0,:]/1700)
        return raw1
    
    def is_valid_slice_count(self):
        return 3200 % sum(b for a, b in self.image_lengths) == 0
    
    def normalise_frames(self):
        multiplier = 3200 / sum(b for a, b in self.image_lengths)
        self.image_lengths = [b * multiplier for b in self.image_lengths]
        return

    def get_frame_time(self):
        if not self.is_valid_slice_count():
            raise ValueError("invalid slice count, must be a factor of 3200")
        self.normalise_frames()
        # motor_RPS = (self.motor_RPM / 60)
        # motor_SPR = 1/motor_RPS
        # seconds_per_tick = motor_SPR/3200
        seconds_per_tick = (60/self.motor_RPM) / 3200 
        return seconds_per_tick
    
    def read_voltage_avg(self):
        return float(np.array(self.read_voltage(),dtype=np.float64).mean())
        
    #function digitises voltages level, outputs -1 for undefined voltage levels
    #https://cdn.phidgets.com/docs/images/thumb/0/00/LogicLevel_visualization.jpg/450px-LogicLevel_visualization.jpg
    def digitise_voltage(self,voltage):
        if voltage >= self.HIGH_VOLTAGE_THRESHOLD:
            return 1
        if voltage <= self.LOW_VOLTAGE_THRESHOLD:
            return 0
        else:
            return -1
    
    #also updates the previous voltage state when called if changed
    def is_voltage_changed(self):
        detected_voltage = self.controller.read_voltage_avg()
        if (detected_voltage > self.HIGH_VOLTAGE_THRESHOLD and self.previous_voltage_state == 0) or (detected_voltage < self.LOW_VOLTAGE_THRESHOLD and previous_voltage_state == 1):
            previous_voltage_state = 1 - previous_voltage_state
            return 1
        else:
            return 0


    def send_trigger_group(self, seconds_per_tick, is_start = True, is_end = True):
        pulse_duration = seconds_per_tick/5
        def pulse_else_sleep(which_wire, pulse_duration, is_pulse):
            if is_pulse:
                self.send_trigger(1,pulse_duration)
            else:
                time.sleep(pulse_duration)

        pulse_else_sleep(1, pulse_duration, is_start)
        pulse_else_sleep(2, pulse_duration, True)
        pulse_else_sleep(3, pulse_duration, True)
        pulse_else_sleep(4, pulse_duration, is_end)

        self.frames_backlog -= 1

    def reset_projector(self):
        self.projection_state = 0
        self.exposure_counts = 0
        self.current_image = 0

    def reset_motor(self):
        self.previous_voltage_state = 0
        self.motor_phase_enum = 0
        pass


    def send_trigger(self,which_wire,pulse_duration):
        if which_wire == 1:
            self.controller.generate_wave(1,0.2,1000)
            self.controller.generate_wave(2,0.2,1000)
            self.controller.set_vdc(0.2)
            time.wait(pulse_duration) #pulse_duration to be determined, test with 2 microsecond 
            self.controller.set_vdc(3.5)            
        
        if which_wire == 2:
            self.controller.generate_wave(1,0.2,1000)
            self.controller.generate_wave(2,3.5,1000)
            self.controller.set_vdc(0.2)
            time.wait(pulse_duration) #pulse_duration to be determined, test with 2 microsecond 
            self.controller.set_vdc(3.5)
        
        if which_wire == 3:
            self.controller.generate_wave(1,3.5,1000)
            self.controller.generate_wave(2,0.2,1000)
            self.controller.set_vdc(0.2)
            time.wait(pulse_duration) #pulse_duration to be determined, test with 2 microsecond 
            self.controller.set_vdc(3.5)    

        if which_wire == 4:
            self.controller.generate_wave(1,3.5,1000)
            self.controller.generate_wave(2,0.2,1000)
            self.controller.set_vdc(0.2)
            time.wait(pulse_duration) #pulse_duration to be determined, test with 2 microsecond 
            self.controller.set_vdc(3.5)

    #this function is called when projector sends "image ready signal"
    def initiate_pulses(self):
        self.motor_state = 2
        
    def start_operation(self):
        frametime = self.get_frame_time()
        while self.projection_state != 0:
            if self.projection_state == 0:
                self.reset_projector()
                break
            if self.projection_state == 2 and self.motor_phase_enum == 1:
                self.projection_state == 1
            if self.is_voltage_changed(): #if voltage changed, the motor has moved.
                self.motor_phase_enum += 1
                if self.motor_phase_enum >= self.HALL_SENSOR_COUNT: #upon full revolution, reset the motor count to 0
                    self.motor_phase_enum = 0
                if self.projection_state == 1:
                    is_start = (self.exposure_counts == 0)
                    self.exposure_counts += 1
                    is_end = (self.exposure_counts >= self.image_lengths[self.current_image])
                    self.send_trigger_group(frametime, is_start, is_end)
                if self.exposure_counts >= self.image_lengths[self.current_image]:
                    self.current_image += 1
                    self.exposure_counts = 0
        print("operation ended")
        return