#!/usr/bin/env python2
'''
Find line lengths at certain times,
in order to figure out what threshold value to set

Usage: python lineLength.py ptName [startTime]
'''
import sys
import numpy as np
from blackfynn import Blackfynn

CLIP_LENGTH = 60000000 # 1 minute in usec
PREDICTION_LAYER_NAME = 'UPenn_Line_Length_Detector'

timeseries_ids = { 
    'Old_Ripley': 'N:package:8d8ebbfd-56ac-463d-a717-d48f5d318c4c',
    'R950': 'N:package:6af7dd3b-50f6-43cd-84ad-e0b3af5b636a',
    'Ripley': 'N:package:401f556c-4747-4569-b1a8-9e6e50abf919',
    'UCD1': 'N:package:3d9de38c-5ab2-4cfe-8f5b-3ed64d1a6b6e',
    'UCD2': 'N:package:86985e61-c940-4404-afa7-94d0add8333f',
}

ptName = sys.argv[1]
bf = Blackfynn()
ts = bf.get(timeseries_ids[ptName])
segments = ts.segments()

try:
    startTime = int(sys.argv[2])
    for i, (a,b) in enumerate(segments):
        if b > startTime: break
    segments[:i] = []
    startTime = max(segments[0][0], startTime)
    print 'start time:', startTime
    segments[0] = (startTime, segments[0][1])
except:
    startTime = segments[0][0]

if ptName == 'Ripley':
    # Workaround since Ripley has 5 channels
    ch = [ 
        'N:channel:95f4fdf5-17bf-492b-87ec-462d31154549',
        'N:channel:c126f441-cbfe-4006-a08c-dc36bd309c38',
        'N:channel:23d29190-37e4-48b0-885c-cfad77256efe',
        'N:channel:07f7bcae-0b6e-4910-a723-8eda7423a5d2'
    ]
else:
    ch = None

def lineLength(clip):
    lengths = np.zeros(clip.shape[0]).astype('float64')
    for i in range(1, clip.shape[1]):
        lengths += np.abs(clip[:, i] - clip[:, i-1])

    # remove zero-length channels
    lengths = lengths[np.nonzero(lengths)] 
    if lengths.size == 0: return 0.0

    # take the mean and normalize by clip length
    length = np.median(lengths) / clip.shape[1] 
    return length

for seg in segments:
    pos = seg[0]
    while pos < seg[1]:
        try:
            clip = ts.get_data(start=pos, length=CLIP_LENGTH, channels=ch)
            # note: actual clip length may be shorter than CLIP_LENGTH
        except Exception as e:
            print 'Pull failed at time %d:' % pos, e
            continue
        startTime = clip.iloc[0].name.value / 1000 # convert to Unix epoch time, in usecs
        endTime = clip.iloc[-1].name.value / 1000
        clip.fillna(0, inplace=True) # replace NaNs with zeros

        clip = clip.transpose().values
        length = lineLength(clip)
        print 't', (startTime, endTime), '\tlength:', length
        raw_input()

        pos += CLIP_LENGTH