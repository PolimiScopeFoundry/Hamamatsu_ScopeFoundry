""" Written by Vipin Balan (Polimi).
    2024
"""
import numpy
import time

from hamamatsu.dcam import copy_frame, dcam, Stream, EWaitEvent #copy_dual_frame

try: from hamamatsu.dcam import copy_dual_frame
except: print("no dual frame support, do not use sensor modes 14 or 16")

class camera:
    def __init__(self):

        self.dcam = None
        self.stream = None
        self.tstream = None
        self.frame=None
        self.newest_frame_index=None

        self.size=(2048,2048)

        # here you will initialize all necessary variables # <----moved from line 30

    def camera_open(self):

        self.dcam = dcam.__enter__()
        self.camera = dcam[0].__enter__()
        # self.stream = Stream(self.camera,self.frames_number)

    def close(self):

        self.camera.__exit__(0, 0, 0)
        self.dcam.__exit__(0, 0, 0)                 # require 3 attributes so just tested 0,0,0 and it seems to work

    def set_all_parameters(self, sensor_mode=12.0, exposure_time=0.002, trigger_source=1, subarray_mode=2,
                            hsize=1024, vsize=2048, trigger_delay=0, internal_line_interval=10e-06,
                            subarray_hpos=0, subarray_vpos=0, parameter=None, value=None):

        self.camera._buf_release()
        self.camera["sensor_mode"] = sensor_mode        #12
        self.camera["exposure_time"] = exposure_time
        self.camera["trigger_source"] = trigger_source  #1
        self.camera["subarray_mode"] = subarray_mode    #2
        self.camera["subarray_hpos"] = 0    #512
        self.camera["subarray_vpos"] = 0
        self.camera["subarray_hsize"] = 2048
        self.camera["subarray_vsize"] = 1024
        print("value set to camera",hsize,vsize,subarray_hpos,subarray_vpos)
        self.camera["subarray_hsize"] = hsize
        self.camera["subarray_vsize"] = vsize
        self.camera["subarray_hpos"] = subarray_hpos    #512
        self.camera["subarray_vpos"] = subarray_vpos
        self.size = (vsize, hsize)
        self.camera["trigger_delay"] = trigger_delay
        self.camera["internal_line_interval"] = internal_line_interval #9.74436090225564e-06*2

    def get_one_parameter(self,parameter_name):
        return self.camera[parameter_name].read()

    def get_one_parameter_limits(self,parameter_name):
        parameter=self.camera[parameter_name]
        return parameter["min_value"],parameter["max_value"]

    def set_one_parameter(self,parameter_name,parameter_value):
        # self.camera[parameter_name] = parameter_value
        self.camera[parameter_name] = parameter_value
        if parameter_name == "subarray_hsize":
            self.size = (parameter_value, self.size[1])
        if parameter_name == "subarray_vsize":
            self.size = (self.size[0], parameter_value)

    def prepare_acquisition(self, number_of_frames=10):
        self.frames_number = number_of_frames
        nb_frames = number_of_frames
        self.frame = numpy.zeros((nb_frames, self.size[0], self.size[1]), dtype="uint16")
        self.camera._buf_release()

        self.stream=Stream(self.camera, nb_frames)

    def acquire_sequence(self):
        t = time.perf_counter()
        self.camera.start()
        for i, frame_buffer in enumerate(self.stream):
            if i ==0:
                t=time.perf_counter()-t
                print("started for real", t)
            if self.camera["sensor_mode"].read() in [1,12]:
                self.frame[i] = copy_frame(frame_buffer).reshape(self.size)
            elif self.camera["sensor_mode"].read() in [14,16]:
                self.frame[i] = copy_dual_frame(frame_buffer).reshape(self.size)
        self.camera.stop()

        return self.frame
        # return sequence #rewithe the function completely from example code from hamamatsu

    def start_live(self): #TODO: set number of frames not always 50
        time.sleep(1.5)
        self.camera._buf_release()
        self.stream = Stream(self.camera, 50)          # look what is this doing
        self.tstream = self.camera.transfer_stream()            # look what is this doing
        self.camera.start(live=True)
        i = 0
        while self.stream.event_stream.__next__() is not EWaitEvent.CAP_FRAMEREADY:
            time.sleep(0.0001)
            i = i+1

    def get_last_live_frame(self): #TODO: add timeout
        current_frame_index=next(self.tstream).nNewestFrameIndex
        while current_frame_index==self.newest_frame_index:
            time.sleep(0.001)
            current_frame_index = next(self.tstream).nNewestFrameIndex
        self.newest_frame_index = current_frame_index
        if self.camera["sensor_mode"].read() in [1, 12]:
            return copy_frame(self.camera._lock_frame_index(current_frame_index))
        elif self.camera["sensor_mode"].read() in [14, 16]:
            return copy_dual_frame(self.camera._lock_frame_index(current_frame_index))

    def get_last_sequence_frame(self):
        current_frame_index=next(self.tstream).nNewestFrameIndex
        while current_frame_index==self.newest_frame_index:
            time.sleep(0.001)
            current_frame_index = next(self.tstream).nNewestFrameIndex
        if self.newest_frame_index==None:
            self.newest_frame_index=current_frame_index
        else:
            self.newest_frame_index += 1
            if self.newest_frame_index>49:
                self.newest_frame_index=0
        if self.camera["sensor_mode"].read() in [1, 12]:
            return copy_frame(self.camera._lock_frame_index(current_frame_index))
        elif self.camera["sensor_mode"].read() in [14, 16]:
            return copy_dual_frame(self.camera._lock_frame_index(current_frame_index))

    def stop_live(self):
        self.camera.stop()


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    cam = camera()
    cam.camera_open()
    # print("trying to set parameters")
    # cam.set_all_parameters()
    # print("parameters set")
    # print(cam.get_one_parameter('internal_line_interval'))
    #cam.camera["sensor_mode"] = 14
    for par in cam.camera:
        if "enum_values" in cam.camera[par].keys():
            print(cam.camera[par]["uname"],cam.camera[par]['enum_values'],cam.camera[par]['default_value'])
        else:
            print(cam.camera[par]["uname"],cam.camera[par]['min_value'],cam.camera[par]['max_value'],cam.camera[par]['default_value'])
    for i in range(21):
        try:
            print(i)
            d=float(i)
            cam.camera["readout_direction"]=d
        except:
            print("failed")
    # cam.start_live()
    # for source in range(1,4):
    #     for i in range(1,7):
    #         for j in range(1,4):
    #             try:
    #                 print(source,i,j)
    #                 cam.set_one_parameter("trigger_source", source)
    #                 cam.set_one_parameter("trigger_mode",i)
    #                 cam.set_one_parameter("trigger_active", j)
    #
    #                 for k in range(20):
    #                     image=cam.get_last_live_frame()
    #                     print(numpy.mean(image))
    #             except:
    #                 pass
    # cam.stop_live()
    # print("acquiring sequence")
    # t=time.perf_counter()
    # print(t)
    cam.prepare_acquisition(300)
    a = cam.acquire_sequence()
    plt.imshow(a[10])
    plt.show()
    for i in range(a.shape[0]):
        print(numpy.mean(a[i]))
    print(time.perf_counter(), a.shape)

    cam.prepare_acquisition(300)
    a = cam.acquire_sequence()
    for i in range(a.shape[0]):
        print(numpy.mean(a[i]))
    print(time.perf_counter(), a.shape)

    cam.close()


