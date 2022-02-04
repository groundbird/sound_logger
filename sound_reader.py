import numpy as np
from datetime import datetime, timezone
from pydub import AudioSegment # for mp3
import wave # for wave
import struct
from scipy import fromstring, int16
from scipy.signal import welch

FR = 44100 #Hz


ROOT_DIR = '/data/sueno'

def _readtime(str_time, timeformat = None):
        """
    Convert from string time to datetime

    Parameters
    ----------
    str_time : str or int
    timeformat : str or None
        If timeformat is None, str_time is unixtime(int).
        If timeformat is string, read time using datetime.strptime.

    Returns
    -------
    dt_time : datetime.datetime
    """
    if timeformat is None:
        return datetime.fromtimestamp(int(str_time), timezone.utc)
    fmt = timeformat
    st = str_time
    if not '%z' in fmt:
        fmt += '%z'
        st  += '+0000'
        pass
    return datetime.strptime(st, fmt).astimezone(timezone.utc)

def _select_region(data_list, key1, key2):
        """
    Pickup items between 'key1' to 'key2'

    Parameters
    ----------
    data_list  : list of str
    key1, key2 : str

    Returns
    -------
    index_of_start : int
    index_of_end   : int
    """
    _data_list = list(data_list) + [key1, key2]
    _data_list.sort()
    num1 = _data_list.index(key1)
    num2 = _data_list.index(key2)
    cnt2 = _data_list.count(key2)
    return num1, num2 + cnt2 - 2

def _region_to_paths(dt_start, dt_end, serial):
            """
    Pickup filenames between start_time and end_time
    Data directory:
        DATADIR_GB1  = '/home/gb/logger/bdata/accl/'
        DATADIR_GB2  = '/data/gb/logbdata/accl/'
        DATADIR_TEST = './bdata/accl/'

    Parameters
    ----------
    dt_start : datetime.datetime
    dt_end   : datetime.datetime

    Returns
    -------
    paths : list_of_filenames
    """
    #year
    dir_y = listdir(DATADIR)
    dir_y.sort()
    a, b = _select_region(dir_y, dt_start.strftime('%Y'), dt_end.strftime('%Y'))
    a = max(a-1, 0)
    dir_y = dir_y[a:b]

    #month
    dir_m = []
    for d in dir_y:
        dir_m += [d+'/'+dd for dd in listdir(DATADIR + '/' + d)]
    dir_m.sort()
    a, b = _select_region(dir_m, dt_start.strftime('%Y/%m'), dt_end.strftime('%Y/%m'))
    a = max(a-1, 0)
    dir_m = dir_m[a:b]

    #day
    dir_d = []
    for d in dir_m:
        dir_d += [d+'/'+dd for dd in listdir(DATADIR + '/' + d)]
    dir_d.sort()
    a, b = _select_region(dir_d, dt_start.strftime('%Y/%m/%d'), dt_end.strftime('%Y/%m/%d'))
    a = max(a-1, 0)
    dir_d = dir_d[a:b]

    #paths
    paths = []
    for d in dir_d:
        paths += [d+'/'+f for f in listdir(DATADIR + '/' + d) if f[-6:]=='dat.xz']
    paths.sort()

    # Accl: serial#
    if type(serial) is int:
        serial = f'LPMSRS2{serial:06d}'
    else:
        serial = f'{serial}'

    fname_format = '%Y/%m/%d/'+serial+'_%Y-%m%d-%H%M%S+0000.dat.xz'
    a, b = _select_region(paths, dt_start.strftime(fname_format), dt_end.strftime(fname_format))
    a = max(a-1, 0)
    paths = paths[a:b]
    paths = list(map(lambda x: DATADIR + x, paths))
    return paths

        

class SoundReader():
    def __init__(self, start, end, timeformat = None):
        """
        Parameters
        ----------
        start : str or int
        end   : str or int
        timeformat : str or None
            It read sound data from 'start' time to 'end' time
            If timeformat is None, 'start' and 'end' is unixtime.
            If timeformat is string, read time using datetime.strptime.
        """
        self.dt_start = _readtime(start, timeformat)
        self.dt_end   = _readtime(end,   timeformat)
        self.ut_start = datetime.timestamp(self.dt_start)
        self.ut_end   = datetime.timestamp(self.dt_end)
        self._paths = _region_to_paths(self.dt_start, self.dt_end)
        self._reader_file = None
        self.start_utime = None
        self.start_ts    = None
        self.fr = FR
        # read the first file
        while len(self._paths) > 0:
            self._set_next_file()
            try:
                self._reader_file.seek_by_date(self.ut_start)
                self.start_utime = self._reader_file.start_time
                self.start_ts    = self._reader_file.start_ts
                break
            except StopIteration:
                self._reader_file = None
                pass
            pass

        self.pathlist = []

    def read_wav(self):
        wavf = path
        wr = wave.open(wavf, 'r')

        # waveファイルが持つ性質を取得
        ch = wr.getnchannels()
        width = wr.getsampwidth()
        fr = wr.getframerate()
        fn = wr.getnframes()

        print("Channel: ", ch)
        print("Sample width: ", width)
        print("Frame Rate: ", fr)
        print("Frame num: ", fn)
        print("Params: ", wr.getparams())
        print("Total time: ", 1.0 * fn / fr)

        data = wr.readframes(wr.getnframes())
        wr.close()
        amp = fromstring(data, dtype=int16)
        time = np.arange(0, fn/fr, 1/fr)
        return amp, time


    def read_mp3(self):
        sound = AudioSegment.from_file(self.path, "mp3")

        # change NumPy array
        data = np.array(sound.get_array_of_samples())
        time = np.arange(0, int(len(data))/self.fr, 1/self.fr)
        return data
