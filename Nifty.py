#!/usr/bin/env python
################################################################################
#                Import some useful Python utilities/modules                   #
################################################################################
from optparse import OptionParser
from pyraf import iraf
import logging, os, sys
import json
from datetime import datetime
# Import major Nifty scripts. You can change the names here if you like.
import nifsSort as sortScript
import nifsBaselineCalibration as calibrateScript
import nifsReduce as reduceScript
import nifsMerge as mergeScript
import nifsDefs
# Import custom Nifty functions.
from nifsDefs import datefmt, writeList, loadSortSave

#                                +
#
#
#
#              +
#         +         +         +
#
#                     +      +
#
#
#      +       +   + + + + +    + + + +  + + + + +   +    +
#     + +     +       +        +            +         + +
#    +   +   +       +        + +          +           +
#   +     + +       +        +            +           +
#  +       +   + + + + +    +            +           +
#
#
#                                      +
#                                   +     +
#                                       +
#                                      +
#

# Welcome to Nifty, the nifs data reduction pipeline! My current version is:
__version__ = "v0.1.1"

# The time when Nifty was started is:
startTime = str(datetime.now())

def launch():

    # Format logging options.
    FORMAT = '%(asctime)s %(message)s'
    DATEFMT = datefmt()

    # Set up the logging file.
    logging.basicConfig(filename='Nifty.log',format=FORMAT,datefmt=DATEFMT,level=logging.DEBUG)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    # This lets us logging.info(to stdout AND a logfile. Cool, huh?
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Enable Debugging break points. Used for testing.
    debug = False

    logging.info("\n####################################")
    logging.info("#                                  #")
    logging.info("#             NIFTY                #")
    logging.info("#   NIFS Date Reduction Pipeline   #")
    logging.info("#         Version "+ __version__+ "           #")
    logging.info("#         July 25th, 2017          #")
    logging.info("#     Marie Lemoine-Busserolle     #")
    logging.info("# Gemini Observatory, Hilo, Hawaii #")
    logging.info("#                                  #")
    logging.info("####################################\n")

    # Make sure to change this if you change the default logfile.
    logging.info('The log file is Nifty.log.')

    parser = OptionParser()
    parser.add_option('-d', '--date', dest='to', type='string', action='store', help='specify the date when the data were observed; e.g. YYYYMMDD (used ONLY within the GEMINI network)')
    parser.add_option('-p', '--program', dest = 'prog', type = 'string', action = 'store', help = 'specify the program number of the observed data; e.g. GN-2013B-Q-109 (used ONLY within the GEMINI network)')
    parser.add_option('-q', '--path', dest='raw', type='string', action='store', help='specify the path of the rawPathectory where the raw files are stored; e.g. users/name/reduction/Raw')
    parser.add_option('-o', '--over', dest = 'over', default = False, action = 'store_true', help = 'overwrite old files')
    parser.add_option('-c', '--copy', dest = 'copy', default = False, action = 'store_true', help = 'copy raw data from /net/wikiwiki/dataflow (used ONLY within the GEMINI network)')
    parser.add_option('-s', '--sort', dest = 'sort', default = True, action = 'store_false', help = 'sort data')
    parser.add_option('-r', '--repeat', dest = 'repeat', default = False, action = 'store_true', help = 'Repeat the last data reduction, loading parameters from user_options.json.')
    parser.add_option('-k', '--notelred', dest = 'telred', default= 'True', action = 'store_false', help = 'don\'t reduce telluric data')
    parser.add_option('-g', '--fluxcal', dest = 'fluxcal', default = 'True', action = 'store_true', help = ' perform flux calibration')
    parser.add_option('-t', '--telcorr', dest = 'tel', default= 'False', action = 'store_true', help = 'perform telluric correction')
    parser.add_option('-e', '--stdspectemp', dest = 'spectemp', action = 'store', help = 'specify the spectral type or temperature of the standard star; e.g. for a spectral type -e A0V; for a temperature -e 8000')
    parser.add_option('-f', '--stdmag', dest = 'mag', action = 'store', help = 'specify the IR magnitude of the standard star; if you do not wish to do a flux calibration then enter -f x')
    parser.add_option('-l', '--load', dest = 'repeat', default = False, action = 'store_true', help = 'Load data reduction parameters from user_options.json. Equivalent to -r and --repeat.')
    parser.add_option('-i', '--hinter', dest = 'hinter', default = 'False', action = 'store_true', help = 'do the h line fitting interactively')
    parser.add_option('-y', '--continter', dest = 'continter', default = 'False', action = 'store_true', help = 'do the continuum fitting in the flux calibration interactively')
    parser.add_option('-a', '--redstart', dest = 'rstart',  type='int', action = 'store', help = 'choose the starting point of the daycal reduction; any integer from 1 to 6')
    parser.add_option('-z', '--redstop', dest = 'rstop',  type='int', action = 'store', help = 'choose the stopping point of the daycal reduction; any integer from 1 to 6')
    parser.add_option('-b', '--scistart', dest = 'start', type='int', action = 'store', help = 'choose the starting point of the science reduction; any integer from 1 to 9')
    parser.add_option('-x', '--scistop', dest = 'stop', type = 'int', action ='store', help = 'choose the stopping point of the science reduction; any integer from 1 to 9')
    parser.add_option('-w', '--telinter', dest = 'telinter', default = 'True', action = 'store_true', help = 'perform the telluric correction interactively. The interactive procedure is done in iraf and the non-interactive procedure is done in Python.')
    parser.add_option('-n', '--sci', dest = 'sci', default = 'True', action = 'store_false', help = 'reduce the science images')
    parser.add_option('-m', '--merge', dest = 'merge', default= 'True', action = 'store_false', help = 'create a merged cube')

    (options, args) = parser.parse_args()

    # Define command line options and set defaults.
    """date = options.to
    program = options.prog
    rawPath = options.raw
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
    telinter = options.telinter"""

    repeat = options.repeat
    date = None
    program = None
    rawPath = None
    over = False
    copy = False
    sort = False
    red = False
    sci = False
    merge = False
    tel = False
    telred = False
    spectemp = False
    mag = False
    fluxcal = False
    rstart = False
    rstop = False
    telStart = False
    telStop = False
    sciStart = False
    sciStop = False
    hline_method = False
    hline_inter = False
    continuuminter = False
    telluric_correction_method = False
    telinter = False

    # If a date or program is provided set copy to True. Used within Gemini network.

    if date or program:
        copy = True

    # Ask the user about what reduction steps and substeps they would like to perform.
    logging.info("\nGood day! Press enter to accept default reduction options.")
    if not repeat:
        fullRun = raw_input("\nDo a full data reduction with default settings? [no]: ")
        fullRun = fullRun or "no"
        if fullRun == "no":
            # "Select in". User has to turn individual steps on.
            sort = raw_input("Sort data? [no]: ")
            sort = sort or False
            if sort == "yes":
                rawPath = raw_input("Path to raw files directory? [~/data]: ")
                rawPath = rawPath or "~/data"
            tel = raw_input("Apply a telluric correction? [no]: ")
            tel = tel or False

            logging.info("\nReduction options: ")
            # See if we want to reduce the baseline calibrations. And if so, which substeps
            # to perform.
            red = raw_input("Reduce baseline calibrations? [no]: ")
            red = red or False
            # By default do all of them.
            rstart = raw_input("Starting point of baseline calibration reductions? [1]: ")
            rstart = rstart or 1
            rstop = raw_input("Stopping point of baseline calibration reductions? [4]: ")
            rstop = rstop or 4

            # Check for tellurics as well; by default do all reduction steps.
            telred = raw_input("Reduce telluric data? [no]:")
            telred = telred or False
            telStart = raw_input("Starting point of science and telluric reductions? [1]: ")
            telStart = telStart or 1
            telStop = raw_input("Stopping point of science and telluric reductions? [7]: ")
            telStop = telStop or 7
            # Set the telluric application correction method. Choices are iraf.telluric and a python variant.
            # Set the h-line removal method with the vega() function in nifsReduce as default.
            hline_method = raw_input("H-line removal method? [vega]: ")
            hline_method = hline_method or "vega"
            # Set yes or no for interactive the h line removal, telluric correction, and continuum fitting
            hlineinter = raw_input("Interative H-line removal? [no]: ")
            hlineinter = hlineinter or False
            continuuminter = raw_input("Interative telluric continuum fitting? [no]: ")
            continuuminter = continuuminter or False
            telluric_correction_method = raw_input("Telluric correction method? [python]: ")
            telluric_correction_method = telluric_correction_method or "python"
            telinter = raw_input("Interactive telluric correction? [no]: ")
            telinter = telinter or False
            # Check for science as well; by default do all reduction steps.
            sci = raw_input("Reduce science data? [no]:")
            sci = sci or False
            sciStart = raw_input("Starting point of science and telluric reductions? [1]: ")
            sciStart = sciStart or 1
            sciStop = raw_input("Stopping point of science and telluric reductions? [7]: ")
            sciStop = sciStop or 7

            fluxcal = raw_input("Do a flux calibration? [no]: ")
            fluxcal = fluxcal or False
            merge = raw_input("Produce one final 3D cube? [no]: ")
            merge = merge or False
            use_pq_offsets = raw_input("Use pq offsets to merge data cubes? [yes]: ")
            use_pq_offsets = use_pq_offsets or True

            # Serialize and save the options as a json file.
            options = {}
            options['__version__'] = __version__
            options['startTime'] = startTime
            options['date'] = date
            options['program'] = program
            options['rawPath'] = rawPath
            options['over'] = over
            options['copy'] = copy
            options['sort'] = sort
            options['red'] = red
            options['sci'] = sci
            options['merge'] = merge
            options['tel'] = tel
            options['telred'] = telred
            options['spectemp'] = spectemp
            options['mag'] = mag
            options['fluxcal'] = fluxcal
            options['rstart']= rstart
            options['rstop'] = rstop
            options['telStart'] = telStart
            options['telStop'] = telStop
            options['sciStart'] = sciStart
            options['sciStop'] = sciStop
            options['hline_method'] = hline_method
            options['hlineinter'] = hlineinter
            options['continuuminter'] = continuuminter
            options['telluric_correction_method'] = telluric_correction_method
            options['telinter'] = telinter
            options['use_pq_offsets'] = use_pq_offsets
            with open('user_options.json', 'w') as outfile:
                json.dump(options, outfile, indent=4)


        else:
            # Use default options provided here to attempt a data reduction.
            sort = "yes"
            if sort == "yes":
                rawPath = raw_input("Path to raw files directory? [~/data]: ")
                rawPath = rawPath or "~/data"
            tel = tel or "yes"

            red = "yes"
            # By default do all of them.
            if red == "yes":
                rstart = 1
                rstop = 4

            telred = "yes"
            if telred == "yes":
                telStart = 1
                telStop = 7
                telluric_correction_method = telluric_correction_method or "python"
                hline_method = "vega"
                hlineinter = False
                continuuminter = False
                telinter = False

    else:
        # Read options from last run from save file
        with open('user_options.json') as json_file:
            options = json.load(json_file)
            oldVersion = options['__version__']
            if oldVersion != __version__:
                logging.info("WARNING: different versions of Nifty being used!")
            date = options['date']
            program = options['program']
            rawPath = options['rawPath']
            over = options['over']
            copy = options['copy']
            sort = options['sort']
            red = options['red']
            sci = options['sci']
            merge = options['merge']
            tel = options['tel']
            telred = options['telred']
            spectemp = options['spectemp']
            mag = options['mag']
            fluxcal = options['fluxcal']
            rstart = options['rstart']
            rstop = options['rstop']
            telStart = options['telStart']
            telStop = options['telStop']
            sciStart = options['sciStart']
            sciStop = options['sciStop']
            hline_method = options['hline_method']
            hlineinter = options['hlineinter']
            continuuminter = options['continuuminter']
            telluric_correction_method = options['telluric_correction_method']
            telinter = options['telinter']
            use_pq_offsets = options['use_pq_offsets']

    # logging.info(user parameters for future reference.
    logging.info("\nUser parameters for this run (can also be found in user_options.json):")
    for i in options:
        logging.info(i, options[i])
    logging.info("")

    # Begin running indivual reduction scripts.

    ###########################################################################
    ##                      STEP 1: Sort the raw data.                       ##
    ###########################################################################

    if sort:
        # Sort the data and calibrations.
        obsDirList, calDirList, telDirList = sortScript.start(rawPath, tel, sort, over, copy, program, date)

    else:
        # Don't use sortScript at all; read the paths to data from textfiles.
        obsDirList, telDirList, calDirList = loadSortSave()

    logging.info("\nobsDirList : ")
    for i in range(len(obsDirList)):
        logging.info(obsDirList[i])
    logging.info("\ntelDirList : ")
    for i in range(len(telDirList)):
        logging.info(telDirList[i])
    logging.info("\ncalDirList : ")
    for i in range(len(calDirList)):
        logging.info(calDirList[i])

    # Here is where the work happens.
    # Five major reduction steps.

    ###########################################################################
    ##                STEP 2: Reduce baseline calibrations.                  ##
    ###########################################################################

    if red:
        if debug:
            a = raw_input('About to enter calibrate.py')
        calibrateScript.start(obsDirList, calDirList, over, rstart, rstop)

    ###########################################################################
    ##                STEP 3: Reduce telluric observations.                  ##
    ###########################################################################

    if tel:
        if debug:
            a = raw_input('About to enter reduce to reduce Telluric images, ',\
                           'create telluric correction spectrum and blackbody spectrum.')
        if telred:
            reduceScript.start(
                telDirList, calDirList, telStart, telStop, tel, telinter, fluxcal,\
                continuuminter, hlineinter, hline_method, spectemp, mag ,over,\
                telluric_correction_method)

    ###########################################################################
    ##                 STEP 4: Reduce science observations.                  ##
    ###########################################################################

    if sci:
        if debug:
            a = raw_input('About to enter reduce to reduce science images.')
        reduceScript.start(obsDirList, calDirList, sciStart, sciStop, tel, telinter, fluxcal,\
                           continuuminter, hlineinter, hline_method, spectemp, mag ,over,\
                           telluric_correction_method)

    ###########################################################################
    ##                      STEP 5: Merge data cubes.                        ##
    ###########################################################################

    if merge:
        if debug:
            a = raw_input('About to enter merge to merge cubes.')
        mergeScript.start(obsDirList, use_pq_offsets, over)

    logging.info('###############################')
    logging.info('#                             #')
    logging.info('#              FIN            #')
    logging.info('#                             #')
    logging.info('###############################')

    return

if __name__ == '__main__':
    launch()
