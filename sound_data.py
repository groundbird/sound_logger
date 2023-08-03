#!/usr/bin/env python3
'''Module to read sound encoder data
'''
import numpy as np
import datetime
from pathlib import Path
import lzma
import wave # need install for reading wave format file
#from scipy import fromstring, int16
#from scipy.signal import welch
import re
import sys

#FR = 44100 #Hz
FR = 44000 #Hz
DATADIR = '/data/gb/logbdata/sound/'
DOME_FMT = '/data/gb/logdata/dome/%Y/%m/%Y%m%d_dome.dat'
PTC_FMT = '/data/gb/logdata/ptc/%Y/%m/%Y%m%d.dat'
AZ_FMT = '%Y-%m%d-%H%M%S'

def _read_wav(path, out = False):
    wr = wave.open(path, 'r')

    # waveファイルが持つ性質を取得
    ch = wr.getnchannels()
    width = wr.getsampwidth()
    fr = wr.getframerate()
    fn = wr.getnframes()

    if out:
        print("Channel: ", ch)
        print("Sample width: ", width)
        print("Frame Rate: ", fr)
        print("Frame num: ", fn)
        print("Params: ", wr.getparams())
        print("Total time: ", 1.0 * fn / fr)

    data = wr.readframes(wr.getnframes())
    wr.close()
    #amp = fromstring(data, dtype=int16)
    amp = np.fromstring(data, dtype=np.int16)    
    time = np.arange(0, fn/fr, 1/fr)
    return amp, time, fr

#def _read_mp3(path):
#    from pydub import AudioSegment # for mp3
#    sound = AudioSegment.from_file(path, "mp3")
#
#    # change NumPy array
#    data = np.array(sound.get_array_of_samples())
#    time = np.arange(0, int(len(data))/self.fr, 1/self.fr)
#    return data, time

def _region_to_paths(dt_start, dt_end, fname_format):
    """
    Pickup filenames between start_time and end_time

    Parameters
    ----------
    dt_start : datetime.datetime
    dt_end   : datetime.datetime
    fname_format : format for strftime

    Returns
    -------
    paths : list_of_filenames
    """
    fmts = [Path(fname_format)]
    for p in fmts[0].parents:
        if '%' not in str(p):
            paths = [p]
            break
        else:
            fmts.append(p)
    fmts.reverse()
    for fmt in fmts:
        #print('fmt', fmt)
        check_format = re.sub(r'%[a-zA-Z]', '*', str(fmt.name))
        check_format = re.sub(r'\*+', '*', check_format)
        paths_child = []
        for p in paths:
            if not p.is_dir(): continue
            paths_child += list(p.glob(check_format))
        paths = np.array(paths_child)
        paths.sort()
        start_path = Path(dt_start.strftime(str(fmt)))
        end_path = Path(dt_end.strftime(str(fmt)))
        a = paths.searchsorted(start_path)
        b = paths.searchsorted(end_path, side = 'right')
        a = max(a-1, 0)
        paths = paths[a:b]
        #print(paths)
    #print(paths)
    return paths


class SoundData():
    def __init__(self, path, nseg = 16, loginfo = True):
        self._path = Path(path)
        fmt = '_%Y-%m%d-%H%M%S%z'
        self.file_time = datetime.datetime.strptime(str(self._path).split('/')[-1].split('.')[0], fmt)
        self._fd = None
        self.loginfo = loginfo
        if self._path.suffix == '.xz':
            self._fd = lzma.open(self._path, 'rb')
            self._isxz = True
        else:
            self._fd = open(self._path, 'rb')
            self._isxz = False

        #read data
        self.amp, self.time, self.fr = _read_wav(self._fd)
        if not self.fr == FR:
            print('fr is not 44100 Hz')
        #calc. PSD
        self.psd_f, self.psd_amp = welch(self.amp,self.fr, nperseg = len(self.amp)/nseg)

        if self.loginfo:
            # get other logdata
            ## dome
            sys.path.append('/data/sueno/home/workspace/script')
            from logreader.dome_data import DomeData
            pathd = _region_to_paths(self.file_time, self.file_time, DOME_FMT)
            datads = [DomeData(ipath) for ipath in pathd]
            self.dome_status = datads[0].get_status_at(self.file_time)
            self.dome_open = str(self.dome_status[self.dome_status.keys()[2]]).split('.')[1]
            #print(self.dome_status)

            ## ptc
            from logreader.ptc_data import PTCData
            pathp = _region_to_paths(self.file_time, self.file_time, PTC_FMT)
            dataps = [PTCData(ipath) for ipath in pathp]
            self.ptc_status = dataps[0].get_status_at(self.file_time)
            if self.ptc_status[self.ptc_status.keys()[7]]:
                self.ptc_on = 'ON'
            else:
                self.ptc_on = 'OFF'
            #print(self.ptc_status)
            
            ## azimuth
            from az_read.RotLog import RotLog
            az_fmt = datetime.datetime.strftime(self.file_time, AZ_FMT)
            az_fmt_en = datetime.datetime.strftime(self.file_time + datetime.timedelta(seconds = 3), AZ_FMT)
            rot = RotLog(az_fmt, az_fmt_en, AZ_FMT, angle_output_by_radian = True)
            rot_list = list(rot)
            self.ang = np.rad2deg(np.array([i[2] for i in rot_list]))
            reset_index = None
            for i, iang in enumerate(self.ang[:-1]):
                # get index
                if (self.ang[i+1] - self.ang[i]) < 0:
                    reset_index = i
                else:
                    pass
            if reset_index is None:
                self.rpm = (self.ang[-1] - self.ang[0]) * 20
            else:
                for i, iang in enumerate(self.ang):
                    if i > reset_index:
                        self.ang[i] = iang+360
                    else:
                        pass
                self.rpm = round(((self.ang[-1] - self.ang[0]) * 20)/360)


        
    def plot(self, save = False):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(2,1, figsize = (10,8))

        ax[0].plot(self.time, self.amp)
        ax[0].set_xlabel('time [s]')
        ax[0].set_ylabel('amplitude [a.u.]')
        ax[1].semilogx(self.psd_f, 10*np.log10(self.psd_amp))
        ax[1].set_xlabel('frequency [Hz]')
        ax[1].set_ylabel('PSD [dBc/Hz]')
        ax[1].grid()
        if self.loginfo:
            ax[0].set_title('Date : ' +  datetime.datetime.strftime(self.file_time, '%Y-%m%d-%H%M%S') + ', Dome : ' + self.dome_open + ', PTC : ' + self.ptc_on + ', RPM : {}'.format(self.rpm))
        else:
            ax[0].set_title('Date : ' +  datetime.datetime.strftime(self.file_time, '%Y-%m%d-%H%M%S'))
        plt.tight_layout()

        if save:
            import os
            if not os.path.isdir('./fig'):
                os.mkdir('fig')
            plt.savefig('fig/' + datetime.datetime.strftime(self.file_time, '%Y-%m%d-%H%M%S') + '.jpg')



if __name__ == '__main__' :
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p', '--path', type=str, help='data path', default='/data/gb/logbdata/sound/2022/02/01/_2022-0201-000001+0000.wav.xz')
    
    args = parser.parse_args()

    sd = SoundData(args.path)
    sd.plot(save = True)
