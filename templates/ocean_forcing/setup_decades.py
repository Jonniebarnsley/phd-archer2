#!/usr/bin/env python
import os


def replace(inFileName, outFileName, replacements):
    with open(inFileName, 'rt') as fin:
        with open(outFileName, 'wt') as fout:
            for line in fin:
                for orig in replacements:
                    line = line.replace(orig, replacements[orig])
                fout.write(line)


climFirstYear = 1995
climLastYear = 2014
climOutFolder = '{:04d}-{:04d}'.format(climFirstYear, climLastYear)
climFolders = ', '.join(['{:04d}'.format(year) for year in
                         range(climFirstYear, climLastYear+1)])

firstYears = list(range(1995, 2299, 20))

for firstYear in firstYears:
    lastYear = min(firstYear+19, 2299)

    outFolder = '{:04d}-{:04d}'.format(firstYear, lastYear)
    folders = ', '.join(['{:04d}'.format(year) for year in
                         range(firstYear, lastYear+1)])
    print(outFolder)
    try:
        os.makedirs(outFolder)
    except OSError:
        pass

    replacements = {'@outFolder': outFolder,
                    '@folders': folders,
                    '@years': outFolder,
                    '@tIndexMin': '{}'.format(firstYear-1995),
                    '@tIndexMax': '{}'.format(lastYear-1995),
                    '@climDecades': climOutFolder,
                    '@climFolders': climFolders,
                    '@climFirstTIndex': '0',
                    '@climLastTIndex': '{}'.format(climLastYear-climFirstYear)}
    templateFileName = 'config.combine_@model'
    outFileName = '{}/config.combine_@model'.format(outFolder)
    replace(templateFileName, outFileName, replacements)
