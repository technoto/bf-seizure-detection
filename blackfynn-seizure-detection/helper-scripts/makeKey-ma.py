#!/usr/bin/env python2
'''
Takes in a MA Line Length log file (ll-new-XXX.out)
and makes an answer key and prediction file

Usage: python -m helper-scripts.makeLLNewkey ptName logFile
'''

import csv
from random import randint
import sys
from blackfynn import Blackfynn

from settings import PL_ROOT, TS_IDs

ptName = sys.argv[1]
logFile = sys.argv[2]

annotFile = PL_ROOT + '/annotations/' + ptName + '_annotations.txt'
bf = Blackfynn()
ts = bf.get(TS_IDs[ptName])
start = ts.start
end = ts.end

keyFile = ptName + '_key.csv'
predFile = ptName + '_preds.csv'

def isIctal(start, end):
    'Returns s: clip is a seizure, and e: clip is an early seizure'
    s = 0
    e = 0
    clipLength = end - start
    for ictal in ictals:
        # check if the middle of the seizure is inside the clip
        ictalMiddle = (ictal[1] + ictal[0]) / 2
        #if min(end, ictal[1]) - max(start, ictal[0]) >= clipLength / 2:
        if ictalMiddle > start and ictalMiddle < end:
            s = 1
            if start - ictal[0] < 15000000: e = 1
            break
    return s, e

# Read ictal annotations
ictals = []
with open(annotFile, 'rU') as f:
    for line in f.readlines():
        ictals.append(map(int, line.strip().split()))

# Create output key file
outfile_key = open(keyFile, 'wb')
key_writer = csv.writer(outfile_key, lineterminator='\n')
key_writer.writerow( ('clip', 'seizure') )

# Create csv of predictions
outfile_pred = open(predFile, 'wb')
pred_writer = csv.writer(outfile_pred, lineterminator='\n')
pred_writer.writerow( ('clip', 'seizure', 'score') )

with open(logFile, 'rU') as f:
    n = 1
    trend = None
    for line in f.readlines():
        split = line.strip().split()
        if split[0] == 'TREND:':
            trend = float(split[1])
            continue
        if len(split) != 4 or split[0] not in '+-' : continue
        pred = int(split[0] == '+')
        length = float(split[1])
        score = length / trend
        startTime = int(split[2].lstrip('(').rstrip(','))
        endTime = int(split[3].rstrip(')'))

        # Check if clip is ictal
        s, _ = isIctal(startTime, endTime)

        # Write output files
        clipname = '%s-%d-%d' % (ptName, startTime, endTime)
        key_writer.writerow( (clipname, s) )
        pred_writer.writerow( (clipname, pred, score) )
        n += 1

outfile_key.close()
outfile_pred.close()
