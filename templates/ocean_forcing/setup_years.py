#!/usr/bin/env python
import os

def replace(inFileName, outFileName, replacements):
    with open(inFileName, 'rt') as fin:
        with open(outFileName, 'wt') as fout:
            for line in fin:
                for orig in replacements:
                    line = line.replace(orig, replacements[orig])
                fout.write(line)


for tIndex, year in enumerate(range(1995, 2300)):
    yearString = '{:04d}'.format(year)
    print(yearString)
    try:
        os.makedirs(yearString)
    except OSError:
        pass

    replacements = {'@tIndex': '{}'.format(tIndex),
                    '@year': yearString}
    templateFileName = 'config.@model'
    outFileName = '{}/config.@model'.format(yearString)
    replace(templateFileName, outFileName, replacements)
