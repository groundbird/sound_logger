import numpy as np
from pathlib import Path
import datetime
from os import listdir
import wave # for wave
import struct
#from scipy import fromstring, int16
#from scipy.signal import welch
import sys
sys.path.append('/home/gb/logger/sound_logger/')
from sound_data import SoundData
import re

FR = 44100 #Hz
DATADIR = '/data/gb/logbdata/sound/'
SOUND_FMT = '/data/gb/logbdata/sound/%Y/%m/%d/_%Y-%m%d-%H%M%S%z.wav.xz'

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
        return datetime.datetime.fromtimestamp(int(str_time), datetime.timezone.utc)
    fmt = timeformat
    st = str_time
    if not '%z' in fmt:
        fmt += '%z'
        st  += '+0000'
        pass
    return datetime.datetime.strptime(st, fmt).astimezone(datetime.timezone.utc)

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

class SoundReader():
    def __init__(self, start, end, timeformat = None, nseg = 16, loginfo = True):
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
        self.ut_start = datetime.datetime.timestamp(self.dt_start)
        self.ut_end   = datetime.datetime.timestamp(self.dt_end)
        self._paths = _region_to_paths(self.dt_start, self.dt_end, SOUND_FMT)
        self.fr = FR
        # read the first file
        self.datas = [SoundData(str(ipath), nseg =nseg, loginfo = loginfo) for ipath in self._paths]
