from optparse import OptionParser
from optparse import OptionParser
from pyraf import iraf
import nifsSort, nifsReduce, nifsFluxCalib, nifsScience, nifsMerge
from nifsDefs import datefmt
import logging, os

#--------------------------------------------------------------------#
#                                                                    #
#                             Nifty                                  #
#                                                                    #
#     This is the python data reduction script for NIFS              #
#                                                                    #
#     Calls the following scripts:                                   #
#     nifsSort.py                                                    #
#     nifsReduce.py                                                  #
#     nifsScience.py                                                 #
#     nifsMerge.py                                                   #
#     nifsDefs.py                                                    #
#                                                                    #
#     To run:                                                        #
#     python Main.py *command line options* (see below)              #
#     EXAMPLE: python Main.py -d 20121212                            #
#     Version 1 - June 2015   Marie Lemoine-Busserolle               #
#     mrlb05@googlemail.com                                          #
#                                                                    #
#--------------------------------------------------------------------#

def main():

    # Format logging options
    FORMAT = '%(asctime)s %(message)s'
    DATEFMT = datefmt()

    # Set up the logging file
    logging.basicConfig(filename='main.log',format=FORMAT,datefmt=DATEFMT,level=logging.DEBUG)
    logger = logging.getLogger()
    logging.info('Login file is main.log')

    parser = OptionParser()
    parser.add_option('-d', '--date', dest='to', type='string', action='store', help='specify the date when the data were observed; e.g. YYYYMMDD (used ONLY within the GEMINI network)')
    parser.add_option('-p', '--program', dest = 'prog', type = 'string', action = 'store', help = 'specify the program number of the observed data; e.g. GN-2013B-Q-109 (used ONLY within the GEMINI network)')
    parser.add_option('-q', '--path', dest='raw', type='string', action='store', help='pecify the path of the directory where the raw files are stored; e.g. users/name/reduction/Raw')
    parser.add_option('-o', '--over', dest = 'over', default = False, action = 'store_true', help = 'overwrite old files')
    parser.add_option('-c', '--nocopy', dest = 'copy', default = True, action = 'store_false', help = 'don\'t copy raw data from /net/wikiwiki/dataflow (used ONLY within the GEMINI network)')
    parser.add_option('-s', '--nosort', dest = 'sort', default = True, action = 'store_false', help = 'don\'t sort data')
    parser.add_option('-r', '--noreduce', dest = 'red', default = True, action = 'store_false', help = 'don\'t reduce the baseline calibrations')
    parser.add_option('-k', '--notelred', dest = 'telred', default= 'True', action = 'store_false', help = 'don\'t reduce telluric data')
    parser.add_option('-g', '--fluxcal', dest = 'fluxcal', default = 'True', action = 'store_true', help = ' perform flux calibration')
    parser.add_option('-t', '--notelcorr', dest = 'tel', default= 'True', action = 'store_false', help = 'don\'t perform telluric correction')
    parser.add_option('-e', '--stdspectemp', dest = 'spectemp', action = 'store', help = 'specify the spectral type or temperature of the standard star; e.g. for a spectral type -e A0V; for a temperature -e 8000')
    parser.add_option('-f', '--stdmag', dest = 'mag', action = 'store', help = 'specify the IR magnitude of the standard star; if you do not wish to do a flux calibration then enter -f x')
    parser.add_option('-l', '--hline', dest = 'hline', type = 'string', action = 'store', help = 'choose a method for removing H lines from the telluric spectra. The default is vega and the choices are vega, linefit_auto, linefit_manual, vega_tweak, linefit_tweak, and none')
    parser.add_option('-i', '--hinter', dest = 'hinter', default = 'False', action = 'store_true', help = 'do the h line fitting interactively')
    parser.add_option('-y', '--continter', dest = 'continter', default = 'False', action = 'store_true', help = 'do the continuum fitting in the flux calibration interactively')
    parser.add_option('-a', '--redstart', dest = 'rstart',  type='int', action = 'store', help = 'choose the starting point of the daycal reduction; any integer from 1 to 6')
    parser.add_option('-z', '--redstop', dest = 'rstop',  type='int', action = 'store', help = 'choose the stopping point of the daycal reduction; any integer from 1 to 6')
    parser.add_option('-b', '--scistart', dest = 'start', type='int', action = 'store', help = 'choose the starting point of the science reduction; any integer from 1 to 9')
    parser.add_option('-x', '--scistop', dest = 'stop', type = 'int', action ='store', help = 'choose the stopping point of the science reduction; any integer from 1 to 9')
    parser.add_option('-w', '--telinter', dest = 'telinter', default = 'True', action = 'store_true', help = 'perform the telluric correction interactively. The interactive procedure is done in iraf and the non-interactive procedure is done in Python.')
    parser.add_option('-n', '--nosci', dest = 'sci', default = 'True', action = 'store_false', help = 'don\'t reduce the science images')
    parser.add_option('-m', '--nomerge', dest = 'merge', default= 'True', action = 'store_false', help = 'don\'t create a merged cube')

    (options, args) = parser.parse_args()

    # Define command line options

    date = options.to
    program = options.prog
    dir = options.raw
    over = options.over
    copy = options.copy
    sort = options.sort
    red = options.red
    sci = options.sci
    merge = options.merge
    tel = options.tel
    telred = options.telred
    spectemp = options.spectemp
    mag = options.mag
    fluxcal = options.fluxcal
    telinter = options.telinter

    # set the starting step of science reduction to 1
    if not options.start:
        start = 1
    else:
        start = options.start

    # set the stopping step of science reduction to 9
    if not options.stop:
        stop = 9
    else:
        stop = options.stop

    # set the starting step of calibration reduction to 1
    if not options.rstart:
        rstart = 1
    else:
        rstart = options.rstart

    # set the stopping step of calibration reduction to 6
    if not options.rstop:
        rstop = 6
    else:
        rstop = options.rstop

    print 'Starting point is', start
    logging.info('Starting point is %s', start)

    print 'Starting point is', stop
    logging.info('Stopping point is %s', stop)

    # set the H line removal method
    if not options.hline:
       hline = 'vega'
    else:
        hline = options.hline
        print 'H line removal method is', hline
        logging.info('H line removal method is %s', hline)


    # set yes or no for interactive the h line removal, telluric correction, and continuum fitting
    if options.hinter==True:
        hlineinter = 'yes'
    else:
        hlineinter = 'no'
    print 'H line removal method is set to interactive ? ', hlineinter
    logging.info('H line removal method is set to interactive ? %s', hlineinter)

    if options.continter==True:
        continuuminter = 'yes'
    else:
        continuuminter = 'no'
    print 'telluric continuum fitting is set to interactive ? ', continuuminter
    logging.info('telluric continuum fitting is set to interactive ? %s', continuuminter)

    if options.telinter==True:
        telinter = 'yes'
    else:
        telinter = 'no'
    print 'telluric correction is set to interactive ? ', telinter
    logging.info('telluric correction is set to interactive ? %s', telinter)

    if options.fluxcal==True:
        fluxcal = 'yes'
    else:
        fluxcal = 'no'
    print 'Flux calibration is performed  ? ', fluxcal
    logging.info('Flux calibration is performed ? %s', fluxcal)

    # sort the data and calibrations
    obsDirList, calDirList, telDirList = nifsSort.start(program, date, dir, tel, over, copy, sort)
    print 'I am sorting the data'
    logging.info(' I am sorting the data ')
    logging.info('obsDirList : %s', obsDirList)
    logging.info('telDirList : %s', telDirList)
    print 'obsDirList : ', obsDirList
    print 'telDirList : ', telDirList

    # reduce the calibrations
    print ' I am starting to reduce the calibrations '
    logging.info('I am starting to reduce the calibrations ')
    if red:
        nifsReduce.start(obsDirList, calDirList, over, rstart, rstop)

    if tel:
        # reduce the telluric images
        print ' I am starting to reduce the telluric images '
        logging.info('I am starting to reduce the telluric images')
        if telred:
            nifsScience.start(telDirList, calDirList, start, stop, tel, telinter, over)

        # create telluric correction spectrum and blackbody spectrum
        print ' I am starting to create telluric correction spectrum and blackbody spectrum'
        logging.info('I am starting to create telluric correction spectrum and blackbody spectrum ')
        if fluxcal:
            nifsFluxCalib.start(telDirList, continuuminter, hlineinter, hline, spectemp, mag, over)

    # reduce the science images
    print ' I am starting to reduce the science images '
    logging.info('I am starting to reduce the science images')
    if sci:
        nifsScience.start(obsDirList, calDirList, start, stop, tel, telinter, over)

    # merge all cubes
    print ' I am starting to merge all cubes '
    logging.info('I am starting to merge all cubes')
    if merge:
        nifsMerge.start(obsDirList, over)
        print obsDirList

    return

if __name__ == '__main__':
    main()
