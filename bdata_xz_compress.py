#!/usr/bin/env python3

from os import walk, system, stat
from os.path import join, isdir
from datetime import datetime as dt
import fcntl

TIME_THRESHOLD = 3600. # 1 hour
LOCK_FILE = '/home/gb/logger/sound_logger/.bdata_xz_compress.lock'
DATADIRS = [
    '/data/gb/logbdata/',
    '/home/gb/logger/bdata/'
    ]

try:
    lockf = open(LOCK_FILE, 'a')
    fcntl.lockf(lockf.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
except IOError:
    exit(1)
    pass

for datadir in DATADIRS:
    if isdir(datadir):
        DATADIR = datadir
        break
    
flist = []
for p, ds, fs in walk(DATADIR):
    for f in fs:
        if len(f) < 4 or f[-4:] != '.wav': continue
        path = join(p, f)
        delta = dt.timestamp(dt.now()) - stat(path).st_mtime
        if delta < TIME_THRESHOLD: continue
        print(path, delta)
        system('/usr/bin/xz ' + path)
        pass
    pass
