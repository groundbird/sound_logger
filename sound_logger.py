import os
from os import makedirs
from os.path import isdir, join, exists
import fcntl
from time import sleep, strftime
import sys
import datetime

VERBOSE = False
DEBUG_MODE = False
ROOT_DIR = '/home/gb/logger/bdata'
if DEBUG_MODE:
    ROOT_DIR = '.'

class SoundLogger:
    def __init__(self, dev_card = 1, sampling_rate = 44100, duration = 60, verbose=VERBOSE):
        # setting
        self.dev_card = dev_card
        self.sampling_rate = sampling_rate
        self.duration = duration

        self.__VERBOSE = verbose 
        ## file name
        self.__OUTPUT_PATH  = ROOT_DIR + '/sound/%Y/%m/%d'
        #self.__FNAME_FORMAT = '_%Y-%m%d-%H%M%S+0000.wav'
        #self.__FNAME_FORMAT = '_%Y-%m%d-%H%M%S%z.wav'
        utcnow = datetime.datetime.now(tz=datetime.timezone.utc)
        #p = f'{utcnow.year:04}-{utcnow.month:02}{utcnow.day:02}-{utcnow.hour:02}{utcnow.minute:02}{utcnow.second:02}.wav'
        p = '{:04d}-{:02d}{:02d}-{:02d}{:02d}{:02d}.wav'.format(utcnow.year, utcnow.month, utcnow.day, utcnow.hour,utcnow.minute, utcnow.second)
        self.lockpath = '/home/gb/.gb_lock/'+'sound.lock'
        if self.__VERBOSE:
            print('lock file:' + self.lockpath)

        #self.__FILE_PATH = self.__OUTPUT_PATH + '/' + self.__FNAME_FORMAT
        self.__FILE_PATH = self.__OUTPUT_PATH + '/' + p
        if self.__VERBOSE:
            print('sounf file:' + self.__FILE_PATH)

    def write_to_wav(self):
        ## file making
        dname = strftime(self.__OUTPUT_PATH)
        if not isdir(dname): makedirs(dname)
        self.fname = strftime(self.__FILE_PATH)
        if self.__VERBOSE: print(self.fname)

        cmd = 'arecord --device plughw:' + str(self.dev_card) + ' -r ' + str(self.sampling_rate) + ' -d ' + str(self.duration) + ' -f S16_LE ' + self.fname
        print(cmd)
        os.system(cmd)
        pass

    def log_main(self):
        # check lock file
        try:
            print(self.lockpath)
            lockf = open(self.lockpath, 'w')
            print(lockf)
            fcntl.lockf(lockf.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except:
            print('Locked.')
            exit(1)
        # save start
        self.write_to_wav()
        # wait for save
        sleep(self.duration + int(10))
        sys.exit("save duration is finished")

            
def main():
    from argparse import ArgumentParser
    dev_card = 1
    sampling_rate = 44100
    #duration = 60
    duration = 15    
    
    parser = ArgumentParser()
    parser.add_argument('-dcard', '--dev_card', type=int, help='device card', default=dev_card)
    parser.add_argument('-sr', '--sampling_rate', type=int, help='sampling rate [Hz]', default=sampling_rate)
    parser.add_argument('-dr', '--duration', type=int, help='log duration [seconds]', default=duration)    
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose option')
    
    args = parser.parse_args()

    logger = SoundLogger(dev_card = args.dev_card, sampling_rate = args.sampling_rate, duration = args.duration, verbose=args.verbose)
    logger.log_main()

if __name__ == '__main__':
    main()
