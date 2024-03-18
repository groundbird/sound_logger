#!/usr/bin/python3

import os
from os.path import dirname, abspath, join
from pathlib import Path
import fcntl
import socket
import datetime
import time
import lzma
import numpy as np
from select import select
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formatdate
from email.message import EmailMessage

from logger_base.base import Base
from sound_reader import DATADIR,  _readtime, _region_to_paths
from sound_data import _read_wav

from obs_status import check_az, check_dome


address_list_file = join(dirname(abspath(__file__)), 'mail_address_list.conf')
server_name = 'Ringo-pi'

#SOUND_FMT = '/home/gb/logger/bdata/sound/%Y/%m/%d/_%Y-%m%d-%H%M%S%z.wav.xz'
SOUND_FMT = '/home/gb/logger/bdata/sound/%Y/%m/%d/%Y-%m%d-%H%M%S.wav.xz'

output_path = '/home/gb/logger/bdata/sound/%Y/%m/%d/_%Y-%m%d_sound.alert'
TIMEFORMAT = '%Y%m%d-%H%M%S'
THRESHOLD1 = 5000
#THRESHOLD1 = 12000
THRESHOLD2 = 8000
#THRESHOLD2 = 15000

lockfile = '/home/gb/.gb_lock/alert_sound.lock'
sockfile = '/home/gb/.gb_sock/alert_sound.sock'

INTERVAL_READ = 600. # sec
CNT_FREEZE_MAX = 10

class SoundAlert(Base):
    def __init__(self,
                 output_file_path = 'data/%y/%m/%Y%m%d.log',
                 file_header = '##  Localtime  Unixtime  Value\n',
                 tzone = None, # argument for pytz.timezone (ex. Asia/Tokyo)
                 lock_file = None,
                 sock_file = None,
                 sock_buff_size = 4096,
                 interval_read = 10, # sec
    ):
        super().__init__(output_file_path = output_file_path,
                         file_header = file_header,
                         tzone = tzone,
                         lock_file = lock_file,
                         sock_file = sock_file,
                         sock_buff_size = sock_buff_size)
        self.initialize()
        self._interval_read_ = interval_read
        self._cnt_freeze_max_ = CNT_FREEZE_MAX
        
    def initialize(self):
        self.write_data_to_file('== alert system start ==')
        # setting
        self.path = None
        self.ppath = None        
        self.to_list  = None
        self.alert_en = True
        self.alert_run = True
        return

    def send_alert(self, body, threshold=None, data_len=None, now=None, level=0):
        with open(address_list_file) as f:
            to_addrs = [_.strip() for _ in f if _[0] != '#']
        body += '\n'
        if now is not None:
            body += self._isotime_(now) + '\n'
        if threshold is not None:
            body += 'Threshold = {}'.format(threshold) + '\n'
        if data_len is not None:
            body += 'The number of data over threshold = {}'.format(data_len)

        # check az info
        azdate, azval, azspd = check_az()
        body += '\n Azimuth information \n date:{}, az={}, spd={}'.format(azdate, azval, azspd)

        # check dome info
        dome_info = check_dome()
        body += '\n Dome information \n'
        body += dome_info

        self.alert('bme280_dome_enclosure@gmail.com', to_addrs, body,
                   level=level, name= "Sound Logger",server_name=server_name)

    def finalize(self):
        self.write_data_to_file('== alert system stop ==')
        pass

    def freeze(self):
        self.send_alert('Emergency: no update data')
        return

    def control(self):
        print('--start control--')

        print('==check azinfo==')
        azdate, azval, azspd = check_az()
        if azspd < 0.8:
            print('No rotation : {}rpm'.format(azspd))
            return
        
        print(self.path)
        if self.path is None:
            st = datetime.datetime.now(tz=datetime.timezone.utc).strftime(TIMEFORMAT)
            self.dt_start = _readtime(st, TIMEFORMAT)
            self.dt_end   = _readtime(st, TIMEFORMAT)
            print(self.dt_start)
            print(self.dt_end)            
            self.path = _region_to_paths(self.dt_start, self.dt_end, SOUND_FMT)[0]

        if self.path.suffix == '.xz':
            self._fd = lzma.open(str(self.path), 'rb')
        else:
            self._fd = open(str(self.path), 'rb')
        self.amp, self.time, self.fr = _read_wav(self._fd)
        
        flag1 = (THRESHOLD1 < np.abs(self.amp))
        len_True1 = len(self.amp[flag1])
        flag2 = (THRESHOLD2 < np.abs(self.amp))
        len_True2 = len(self.amp[flag2])

        print('Maximum amplitude = {}'.format(np.max(self.amp)))
        print('Length of data over threshold1 = {}'.format(len_True1))
        print('Length of data over threshold2 = {}'.format(len_True2))        
        print('Standard deviation of amplitude = {}'.format(np.std(self.amp)))

        datestr = self.path.name.split('.')[0]
        date = datetime.datetime.strptime(datestr, '%Y-%m%d-%H%M%S')
        
        if len_True2 > 0:
            text = 'Sound_alert'
            level = 2
            self.send_alert(text, threshold = THRESHOLD2, data_len=len_True2, now=date, level=level)
            print('====send email with alert level2====')
            pass
        elif len_True1 > 0:
            text = 'Sound_alert'            
            level = 1
            self.send_alert(text, threshold = THRESHOLD1, data_len=len_True1, now=date, level=level)
            print('====send email with alert level1====')
            pass
        else:
            pass

    def run(self, isDebug = False):
        print('====start run=====')
        try:
            while True:
#                st = time.strftime(TIMEFORMAT)
                st = datetime.datetime.now(tz=datetime.timezone.utc).strftime(TIMEFORMAT)
                self.dt_start = _readtime(st, TIMEFORMAT)
                self.path = _region_to_paths(self.dt_start, self.dt_start, SOUND_FMT)[0]
                if self.path != self.ppath:
                    self._cnt_freeze_ = 0
                    self.control()
                if self._cnt_freeze_ < self._cnt_freeze_max_:
                    self._cnt_freeze_ += 1
                else:
                    self._cnt_freeze_ = 0
                    self.freeze()
                    pass
                self.ppath = self.path
                time.sleep(self._interval_read_)
                pass
        except Exception:
            if isDebug: raise
            pass
        finally:
            self.finalize()
            pass
        return
            

if __name__ == "__main__":
    sdalert = SoundAlert(output_file_path = output_path,
                          lock_file = lockfile,
                          sock_file = sockfile,
                          interval_read = INTERVAL_READ)
    #sdalert.control()
    #sdalert.send_alert(body = 'test')
    sdalert.run()
    
                
