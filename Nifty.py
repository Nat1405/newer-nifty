#!/usr/bin/env python
################################################################################
#                Import some useful Python utilities/modules                   #
################################################################################
from optparse import OptionParser
from pyraf import iraf
import logging, os, sys, shutil
import json
from datetime import datetime
# Import major Nifty scripts. You can change the names here if you like.
import nifsSort as sortScript
import nifsBaselineCalibration as calibrateScript
import nifsReduce as reduceScript
import nifsMerge as mergeScript
import nifsDefs
# Import custom Nifty functions.
from nifsDefs import datefmt, writeList, loadSortSave, getParam

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
    debug = True

    logging.info("\n####################################")
    logging.info("#                                  #")
    logging.info("#             NIFTY                #")
    logging.info("#   NIFS Data Reduction Pipeline   #")
    logging.info("#         Version "+ __version__+ "           #")
    logging.info("#         July 25th, 2017          #")
    logging.info("#     Marie Lemoine-Busserolle     #")
    logging.info("# Gemini Observatory, Hilo, Hawaii #")
    logging.info("#                                  #")
    logging.info("####################################\n")

    # Make sure to change this if you change the default logfile.
    logging.info('The log file is Nifty.log.')


    parser = OptionParser()
    #parser.add_option('-d', '--date', dest='to', type='string', action='store', help='specify the date when the data were observed; e.g. YYYYMMDD (used ONLY within the GEMINI network)')
    #parser.add_option('-p', '--program', dest = 'prog', type = 'string', action = 'store', help = 'specify the program number of the observed data; e.g. GN-2013B-Q-109 (used ONLY within the GEMINI network)')
    #parser.add_option('-q', '--path', dest='raw', type='string', action='store', help='specify the path of the rawPathectory where the raw files are stored; e.g. users/name/reduction/Raw')
    #parser.add_option('-o', '--over', dest = 'over', default = False, action = 'store_true', help = 'overwrite old files')
    #parser.add_option('-c', '--copy', dest = 'copy', default = False, action = 'store_true', help = 'copy raw data from /net/wikiwiki/dataflow (used ONLY within the GEMINI network)')
    #parser.add_option('-s', '--sort', dest = 'sort', default = True, action = 'store_false', help = 'sort data')
    parser.add_option('-r', '--repeat', dest = 'repeat', default = False, action = 'store_true', help = 'Repeat the last data reduction, loading parameters from runtimeData/user_options.json.')
    #parser.add_option('-k', '--notelred', dest = 'telred', default= 'True', action = 'store_false', help = 'don\'t reduce telluric data')
    #parser.add_option('-g', '--efficiencySpectrumCorrection', dest = 'efficiencySpectrumCorrection', default = 'True', action = 'store_true', help = ' perform flux calibration')
    #parser.add_option('-t', '--telcorr', dest = 'tel', default= 'False', action = 'store_true', help = 'perform telluric correction')
    #parser.add_option('-e', '--stdspectemp', dest = 'spectemp', action = 'store', help = 'specify the spectral type or temperature of the standard star; e.g. for a spectral type -e A0V; for a temperature -e 8000')
    #parser.add_option('-f', '--stdmag', dest = 'mag', action = 'store', help = 'specify the IR magnitude of the standard star; if you do not wish to do a flux calibration then enter -f x')
    parser.add_option('-l', '--load', dest = 'repeat', default = False, action = 'store_true', help = 'Load data reduction parameters from runtimeData/user_options.json. Equivalent to -r and --repeat.')
    parser.add_option('-f', '--fullReduction', dest = 'fullReduction', default = False, action = 'store_true', help = 'Do a full Reduction from default_input.json')
    #parser.add_option('-y', '--continter', dest = 'continter', default = 'False', action = 'store_true', help = 'do the continuum fitting in the flux calibration interactively')
    #parser.add_option('-a', '--redstart', dest = 'rstart',  type='int', action = 'store', help = 'choose the starting point of the daycal reduction; any integer from 1 to 6')
    #parser.add_option('-z', '--redstop', dest = 'rstop',  type='int', action = 'store', help = 'choose the stopping point of the daycal reduction; any integer from 1 to 6')
    #parser.add_option('-b', '--scistart', dest = 'start', type='int', action = 'store', help = 'choose the starting point of the science reduction; any integer from 1 to 9')
    #parser.add_option('-x', '--scistop', dest = 'stop', type = 'int', action ='store', help = 'choose the stopping point of the science reduction; any integer from 1 to 9')
    #parser.add_option('-w', '--telinter', dest = 'telinter', default = 'True', action = 'store_true', help = 'perform the telluric correction interactively. The interactive procedure is done in iraf and the non-interactive procedure is done in Python.')
    #parser.add_option('-n', '--sci', dest = 'sci', default = 'True', action = 'store_false', help = 'reduce the science images')
    #parser.add_option('-m', '--merge', dest = 'merge', default= 'True', action = 'store_false', help = 'create a merged cube')

    (options, args) = parser.parse_args()

    # Gemini sort parameters.
    date = None
    program = None
    copy = None
    spectemp = None

    repeat = options.repeat
    fullReduction = options.fullReduction

    # Ask the user about what reduction steps and substeps they would like to perform.
    logging.info("\nGood day! Press enter to accept default reduction options.")
    # Check if the user specified at command line to repeat the last Reduction or do a full default data reduction.
    if not repeat and not fullReduction:
        fullReduction = getParam(
                    "Do a full data reduction with default parameters loaded from \nruntimeData/default_input.json? [no]: ",
                    False,
                    "Type yes to start Nifty with data reduction input parameters \nloaded from runtimeData/default_input.json file."
        )
        if fullReduction == False:
            # "Select in". User has to turn individual steps on.
            sort = getParam(
            "Sort data? [no]: ",
            False
            )
            rawPath = getParam(
            "Path to raw files directory? [~/data]: ",
            "~/data"
            )
            tel = getParam(
            "Apply a telluric correction? [no]: ",
            False
            )
            # See if we want to reduce the baseline calibrations. And if so, which substeps
            # to perform.
            red = getParam(
            "Reduce baseline calibrations? [no]: ",
            False
            )
            # By default do all of them.
            rstart = getParam(
            "Starting point of baseline calibration reductions? [1]: ",
            1
            )
            rstop = getParam(
            "Stopping point of baseline calibration reductions? [4]: ",
            4
            )

            # Check for tellurics as well; by default do all reduction steps.
            telred = getParam(
            "Reduce telluric data? [no]: ",
            False
            )
            telStart = getParam(
            "Starting point of science and telluric reductions? [1]: ",
            1
            )
            telStop = getParam(
            "Stopping point of science and telluric reductions? [6]: ",
            6
            )
            # Set the telluric application correction method. Choices are iraf.telluric and a python variant.
            # Set the h-line removal method with the vega() function in nifsReduce as default.
            hline_method = getParam(
            "H-line removal method? [vega]: ",
            "vega"
            )
            # Set yes or no for interactive the h line removal, telluric correction, and continuum fitting
            hlineinter = getParam(
            "Interative H-line removal? [no]: ",
            False
            )
            continuuminter = getParam(
            "Interative telluric continuum fitting? [no]: ",
            False
            )
            telluric_correction_method = getParam(
            "Telluric correction method? [python]: ",
            "python"
            )
            telinter = getParam(
            "Interactive telluric correction? [no]: ",
            False
            )
            # Check for science as well.
            sci = getParam(
            "Reduce science data? [no]: ",
            False
            )
            sciStart = getParam(
            "Starting point of science and telluric reductions? [1]: ",
            1
            )
            sciStop = getParam(
            "Stopping point of science and telluric reductions? [6]: ",
            6
            )
            efficiencySpectrumCorrection = getParam(
            "Do a flux calibration? [no]: ",
            False
            )
            spectemp = getParam(
            "Effective temperature in kelvin of telluric standard star? [None]: ",
            None
            )
            mag = getParam(
            "Magnitude of standard star? [None]: ",
            None
            )
            merge = getParam(
            "Produce one final 3D cube? [no]: ",
            False
            )
            use_pq_offsets = getParam(
            "Use pq offsets to merge data cubes? [yes]: ",
            True
            )
            im3dtran = getParam(
            "Transpose cubes for faster merging? [no]: ",
            False
            )
            over = getParam(
            "Overwrite old files? [no]: ",
            False
            )

            # Serialize and save the options as a .json file.
            options = {}
            options['__version__'] = __version__
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
            options['efficiencySpectrumCorrection'] = efficiencySpectrumCorrection
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
            options['im3dtran'] = im3dtran
            with open('runtimeData/user_options.json', 'w') as outfile:
                json.dump(options, outfile, indent=4)

    if repeat or fullReduction:
        # Read and use parameters of the last Reduction from runtimeData/user_options.json.
        if fullReduction:
            f = './recipes/default_input.json'
            logging.info("\nData reduction parameters for this reduction were copied from ./recipes/default_input.json.")
        else:
            f = 'runtimeData/user_options.json'
            logging.info("\nData reduction parameters for this reduction were copied from runtimeData/user_options.json.")
        with open(f) as json_file:
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
            efficiencySpectrumCorrection = options['efficiencySpectrumCorrection']
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
            im3dtran = options['im3dtran']

        # Make sure to overwrite runtimeData/user_options.json with the latest parameters!
        # shutil.copy('./recipes/default_input.json', 'runtimeData/user_options.json')

    # If a date or program is provided set copy to True. Used within Gemini network.
    #if date or program:
    #    copy = True

    # logging.info(user parameters for future reference.
    logging.info("\nUser parameters for this Reduction:\n")
    for i in options:
        logging.info(str(i) + " " + str(options[i]))
    logging.info("")
    logging.info("These parameters have been written to runtimeData/user_options.json.")

    # Begin running individual reduction scripts.

    ###########################################################################
    ##                      STEP 1: Sort the raw data.                       ##
    ###########################################################################

    if sort:
        # Sort the data and calibrations.
        obsDirList, calDirList, telDirList = sortScript.start(rawPath, tel, over, copy, program, date)

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
        if telred:
            if debug:
                a = raw_input('About to enter reduce to reduce Telluric images, create telluric correction spectrum and blackbody spectrum.')
            reduceScript.start(
                telDirList, calDirList, telStart, telStop, tel, telinter, efficiencySpectrumCorrection,\
                continuuminter, hlineinter, hline_method, spectemp, mag ,over,\
                telluric_correction_method)

    ###########################################################################
    ##                 STEP 4: Reduce science observations.                  ##
    ###########################################################################

    if sci:
        if debug:
            a = raw_input('About to enter reduce to reduce science images.')
        reduceScript.start(obsDirList, calDirList, sciStart, sciStop, tel, telinter, efficiencySpectrumCorrection,\
                           continuuminter, hlineinter, hline_method, spectemp, mag ,over,\
                           telluric_correction_method, use_pq_offsets, merge, im3dtran)

    logging.info('###############################')
    logging.info('#                             #')
    logging.info('#              FIN            #')
    logging.info('#                             #')
    logging.info('###############################')

    return

if __name__ == '__main__':
    launch()
