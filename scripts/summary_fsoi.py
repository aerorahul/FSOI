#!/usr/bin/env python

###############################################################
# < next few lines under version control, D O  N O T  E D I T >
# $Date$
# $Revision$
# $Author$
# $Id$
###############################################################

'''
summary_fsoi.py - create a summary figure of all platforms
'''

__author__ = "Rahul Mahajan"
__email__ = "rahul.mahajan@noaa.gov"
__copyright__ = "Copyright 2016, NOAA / NCEP / EMC"
__license__ = "GPL"
__status__ = "Prototype"
__version__ = "0.1"

import os
import sys
import numpy as np
import pandas as pd
from argparse import ArgumentParser,ArgumentDefaultsHelpFormatter
from matplotlib import pyplot as plt

import lib_obimpact as loi
import lib_utils as lutils

if __name__ == '__main__':

    parser = ArgumentParser(description = 'Create and Plot Observation Impacts Statistics',formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('--center',help='originating center',type=str,required=True,choices=['EMC','GMAO','NRL','JMA_adj','JMA_ens','MET'])
    parser.add_argument('--norm',help='metric norm',type=str,default='dry',choices=['dry','moist'],required=False)
    parser.add_argument('--rootdir',help='root path to directory',type=str,default='/scratch3/NCEPDEV/stmp2/Rahul.Mahajan/test/Thomas.Auligne/FSOI',required=False)
    parser.add_argument('--platform',help='platform to plot',type=str,default='',required=False)
    parser.add_argument('--savefigure',help='save figures',action='store_true',required=False)
    parser.add_argument('--exclude',help='exclude platforms',type=str,nargs='+',required=False)
    parser.add_argument('--cycle',help='cycle to process',nargs='+',type=int,default=[0],choices=[0,6,12,18],required=False)

    args = parser.parse_args()

    rootdir = args.rootdir
    center = args.center
    norm = args.norm
    platform = args.platform
    exclude = args.exclude
    savefig = args.savefigure
    cycle = sorted(list(set(args.cycle)))

    cyclestr = ''.join('%02dZ' % c for c in cycle)

    fname = '%s/h5data/%s/bulk_stats.%s.h5' % (rootdir,center,norm)
    fpkl = '%s/work/%s/group_stats.%s.pkl' % (rootdir,center,norm)

    if os.path.isfile(fpkl):
        overwrite = raw_input('%s exists, OVERWRITE [y/N]: ' % fpkl)
    else:
        overwrite = 'Y'

    if overwrite.upper() in ['Y','YES']:
        df = lutils.readHDF(fname,'df')
        df = loi.accumBulkStats(df)
        platforms = loi.Platforms(center)
        df = loi.groupBulkStats(df,platforms)
        if os.path.isfile(fpkl):
            print 'OVERWRITING %s' % fpkl
            os.remove(fpkl)
        lutils.pickle(fpkl,df)
    else:
        df = lutils.unpickle(fpkl)

    # Filter by cycle
    print 'extracting data for cycle %s' % ' '.join('%02dZ' % c for c in cycle)
    indx = df.index.get_level_values('DATETIME').hour == -1
    for c in cycle:
        indx = np.ma.logical_or(indx,df.index.get_level_values('DATETIME').hour == c)
    df = df[indx]

    # Do time-averaging on the data
    df = loi.tavg_PLATFORM(df)

    if exclude is not None:
        if platform:
            print 'Excluding the following platforms:'
            exclude = map(int, exclude)
        else:
            print 'Excluding the following platforms:'
            if 'reference' in exclude:
                pref = loi.RefPlatform('full')
                pcenter = df.index.get_level_values('PLATFORM').unique()
                exclude = list(set(pcenter)-set(pref))
        print ", ".join('%s'% x for x in exclude)
        df.drop(exclude,inplace=True)

    df['ImpPerOb'] = df['ImpPerOb'] / df['TotImp'].sum() * 100.
    df['FracBenNeuObs'] = pd.Series(df['FracBenObs']+df['FracNeuObs'],index=df.index)

    for qty in ['TotImp','ImpPerOb','FracBenObs','FracNeuObs','FracBenNeuObs','FracImp','ObCnt']:
        plotOpt = loi.getPlotOpt(qty,cycle=cycle,center=center,savefigure=savefig,platform=platform)
        plotOpt['figname'] = '%s/plots/summary/%s/%s_%s' % (rootdir,center,plotOpt.get('figname'),cyclestr)
        loi.summaryplot(df,qty=qty,plotOpt=plotOpt)

    if not savefig:
        plt.show()

    sys.exit(0)
