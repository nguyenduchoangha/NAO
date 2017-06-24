#! /usr/bin/env python
# -*- encoding: UTF-8 -*-

"""Example: Get Signal from Front Microphone & Calculate its rms Power"""


import qi
import argparse
import sys
import time
import numpy as np
import os
import speech_recognition as sr
import pyaudio
import Queue
import copy



class NaoMicrophone(sr.AudioSource):
    def __init__(self):
        self.format = pyaudio.paInt16  # 16-bit int sampling
        self.SAMPLE_WIDTH = pyaudio.get_sample_size(self.format)  # size of each sample
        self.SAMPLE_RATE = 16000  # sampling rate in Hertz
        self.CHUNK = 1024  # number of frames stored in each buffer

        self.stream = NaoMicStream()

class NaoMicStream():
    def __init__(self):
        self.queue = Queue.Queue()
        self.buf = b""

    def is_ready(self, size):
        #print("len of buf: ", len(self.buf))
        while (size > len(self.buf)):
            d = b""
            if self.queue.empty():
                return False
            else:
                d = self.queue.get()

            
            self.buf += d

        return True

    def read(self, size):
        if size > len(self.buf):
            return None
        # enough data for reading
        d = self.buf[0:size]         
        self.buf = self.buf[size:]       
        return d

    def topup_data(self,d):
        print("data len: ", len(d))
        self.queue.put(d)


class SoundProcessingModule(object):
    """
    A simple get signal from the front microphone of Nao & calculate its rms power.
    It requires numpy.
    """

    def __init__( self, app):
        """
        Initialise services and variables.
        """
        super(SoundProcessingModule, self).__init__()
        app.start()
        session = app.session

        # Get the service ALAudioDevice.
        self.audio_service = session.service("ALAudioDevice")
        self.isProcessingDone = False
        self.nbOfFramesToProcess = 100
        self.framesCount=0
        self.micFront = []
        self.module_name = "SoundProcessingModule"

    def startProcessing(self):
        """
        Start processing
        """
        # ask for the front microphone signal sampled at 16kHz
        # if you want the 4 channels call setClientPreferences(self.module_name, 48000, 0, 0)
        self.audio_service.setClientPreferences(self.module_name, 48000, 0, 0)
        self.audio_service.subscribe(self.module_name)

        buf = ''
        count = 0
        while self.isDone() == False:
            if mic.stream.is_ready(1024*4):
                data = mic.stream.read(1024*4)
                buf += data
                count += 1
                print("data size: ", len(data))
                if count == 150:
                    break
            else:
                time.sleep(0.07)
            #time.sleep(1)
        
        with open("a.raw",'wb') as f:
            f.write(buf)


        self.audio_service.unsubscribe(self.module_name)

    def isDone(self):
        return os.path.isfile(".done")


    def processRemote(self, nbOfChannels, nbOfSamplesByChannel, timeStamp, inputBuffer):
        """
        Compute RMS from mic.
        """
        self.framesCount = self.framesCount + 1
        #print(self.framesCount)
        d = copy.deepcopy(inputBuffer)
        global mic
        mic.stream.topup_data(d)
        #print(self.framesCount)

        # if (self.framesCount <= self.nbOfFramesToProcess):
        #if True:
        # convert inputBuffer to signed integer as it is interpreted as a string by python
        # self.micFront=self.convertStr2SignedInt(inputBuffer)
        #data = sr.AudioData()
        #compute the rms level on front mic
        # rmsMicFront = self.calcRMSLevel(self.micFront)
        # print "rms level mic front = " + str(rmsMicFront)
        #else :
        #    self.isProcessingDone=True

    def calcRMSLevel(self,data) :
        """
        Calculate RMS level
        """
        rms = 20 * np.log10( np.sqrt( np.sum( np.power(data,2) / len(data)  )))
        return rms

    def convertStr2SignedInt(self, data) :
        """
        This function takes a string containing 16 bits little endian sound
        samples as input and returns a vector containing the 16 bits sound
        samples values converted between -1 and 1.
        """
        signedData=[]
        ind=0;
        for i in range (0,len(data)/2) :
            signedData.append(data[ind]+data[ind+1]*256)
            ind=ind+2

        for i in range (0,len(signedData)) :
            if signedData[i]>=32768 :
                signedData[i]=signedData[i]-65536

        for i in range (0,len(signedData)) :
            signedData[i]=signedData[i]/32768.0

        return signedData


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, default="127.0.0.1",
                        help="Robot IP address. On robot or Local Naoqi: use '127.0.0.1'.")
    parser.add_argument("--port", type=int, default=9559,
                        help="Naoqi port number")

    args = parser.parse_args()
    try:
        # Initialize qi framework.
        connection_url = "tcp://" + args.ip + ":" + str(args.port)
        app = qi.Application(["SoundProcessingModule", "--qi-url=" + connection_url])
    except RuntimeError:
        print ("Can't connect to Naoqi at ip \"" + args.ip + "\" on port " + str(args.port) +".\n"
               "Please check your script arguments. Run with -h option for help.")
        sys.exit(1)
    MySoundProcessingModule = SoundProcessingModule(app)
    app.session.registerService("SoundProcessingModule", MySoundProcessingModule)
    global s2t
    global mic
    #s2t = sr.Recognizer()
    mic = NaoMicrophone()

    MySoundProcessingModule.startProcessing()
