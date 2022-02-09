sound_logger
===
logging and reading GB usb_microphone

## Data directiory
- dodo and momo-pi:
    /home/gb/logger/bdata/sound/
- dodo and other servers for analysis:
    /data/gb/logbdata/sound

## Logging program
- `sound_logger.py`
The main program of logging. \
It runs by crontab in momo-pi. \
`00 * * * * python3 /home/gb/logger/sound_logger/sound_logger.py >>/home/gb/logger/sound_logger/sound_logger.log` \ 

the data is compressed by `xz` by using `bdata_xz_compress.py` \
It runs by crontab in momo-pi. \ 
`0-59/10 * * * * /usr/bin/nice /usr/bin/python3 /home/gb/logger/bdata_xz_compress/bdata_xz_compress.py >/dev/null 2>&1` \

## Status check program
- look plots
    - `python3 sound_data.py -p /data/gb/logbdata/sound/2022/02/01/_2022-0201-000001+0000.wav.xz`
    - save fig under `./fig/`

- listen sound
    - coming soon.

## Reading program
### `sound_data.py`
Module to read the sound data with path.

- to read the data from the path `/data/gb/logbdata/sound/2022/02/01/_2022-0201-000001+0000.wav.xz`
example for jupyter.
```
from sound_logger.sound_data import SoundData
path = '/data/gb/logbdata/sound/2022/02/01/_2022-0201-000001+0000.wav.xz'
sd = SoundData(path, nseg = 16, loginfo=True)
sd.plot()
```

The SoundData class has some information below.
- `self.amp`    : amplitude of rawdata.
- `self.time`   : time since logging started.
- `self.fr`     : sampling frequency.
- `self.psd_f`  : frequency for PSD.
- `self.psd_amp`: amplitude of PSD.
- `self.loginfo`: wheather dome and ptc and azimuth information are read or not
    - need `logreader.py` and `az_read.py`
    - `self.ptc_on`    : ON/OFF
    - `self.dome_open` : Opend/Closed of dome at letf upper
    - `self.rpm`       : rotation speed per min

### `sound_reader.py`
Module to read the sound data with start and end time.

- to read the data from '2022-0204-000000' to '2022-0204-110000'.
example for jupyter.
```
from sound_logger.sound_reader import SoundReader
st = '2022-0204-000000'
en = '2022-0204-110000'
fmt = '%Y-%m%d-%H%M%S'
sr = SoundReader(st, en, timeformat=fmt, loginfo=True)
```
`self.datas` : list of SoundData class.
