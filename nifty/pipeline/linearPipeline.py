#!/usr/bin/env python
# -*- coding: utf-8 -*-

# MIT License

# Copyright (c) 2015, 2017 Marie Lemoine-Busserolle

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

################################################################################
#                Import some useful Python utilities/modules                   #
################################################################################

# STDLIB

import logging, os, sys, shutil, pkg_resources, argparse
from datetime import datetime

# LOCAL

# Import major Nifty scripts.
import nifsSort as nifsSort
import nifsBaselineCalibration as nifsBaselineCalibration
import nifsReduce as nifsReduce
import nifsUtils as nifsUtils
# Import config parsing.
from configobj.configobj import ConfigObj
# Import custom Nifty functions.
from nifsUtils import datefmt, printDirectoryLists, writeList, getParam, getUserInput

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

# Welcome to Nifty, the nifs data reduction pipeline!

# The current version:
# TODO(nat): fix this to work as a proper package. This should not be hardcoded.
__version__ = "1.0.0"

# The time when Nifty was started is:
startTime = str(datetime.now())

def start(args):
    """

    NIFTY

    This script launches a nifs data reduction.

    It does two things; it:
        - gets data reduction parameters; either from an interactive input session or
          an input file
        - launches appropriate scripts to do the work. It can call up to 3 scripts directly:
                1) nifsSort.py
                2) nifsBaselineCalibration.py
                3) nifsReduce.py

    """
    # Save path for later use and change one directory up.
    path = os.getcwd()

    # Get paths to Nifty data.
    RECIPES_PATH = pkg_resources.resource_filename('nifty', 'recipes/')
    RUNTIME_DATA_PATH = pkg_resources.resource_filename('nifty', 'runtimeData/')

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

    logging.info("\n####################################")
    logging.info("#                                  #")
    logging.info("#             NIFTY                #")
    logging.info("#   NIFS Data Reduction Pipeline   #")
    logging.info("#         Version "+ __version__+ "            #")
    logging.info("#         July 25th, 2017          #")
    logging.info("#     Marie Lemoine-Busserolle     #")
    logging.info("# Gemini Observatory, Hilo, Hawaii #")
    logging.info("#                                  #")
    logging.info("####################################\n")

    # Make sure to change this if you change the default logfile.
    logging.info('The log file is Nifty.log.')

    # Parse command line options.
    parser = argparse.ArgumentParser(description='Do a Gemini NIFS data reduction.')
    # Create a configuration file interactively
    parser.add_argument('-i', '--interactive', dest = 'interactive', default = False, action = 'store_true', help = 'Create a config.cfg file interactively.')
    # Ability to repeat the last data reduction
    parser.add_argument('-r', '--repeat', dest = 'repeat', default = False, action = 'store_true', help = 'Repeat the last data reduction, loading saved reduction parameters from runtimeData/config.cfg.')
    # Ability to load a built-in configuration file (recipe)
    parser.add_argument('-l', '--recipe', dest = 'recipe', action = 'store', help = 'Load data reduction parameters from the a provided recipe. Default is default_input.cfg.')
    # Ability to load your own configuration file
    parser.add_argument(dest = 'inputfile', nargs='?', action = 'store', help = 'Load data reduction parameters from <inputfile>.cfg.')
    # Ability to do a quick and dirty fully automatic data reduction with no user input
    # TODO(nat): make it so Nifty does this when you type "niftyRun" with no options
    parser.add_argument('-f', '--fullReductionPathOrProgramID', dest = 'fullReduction', default = False, action = 'store', help = 'Do a quick reduction from recipes/defaultConfig.cfg, specifying path to raw data or program ID.')

    args = parser.parse_args(args)

    interactive = args.interactive
    repeat = args.repeat
    fullReduction = args.fullReduction
    inputfile = args.inputfile

    if inputfile:
        # Load input from a .cfg file user specified at command line.
        if inputfile != "config.cfg" and os.path.exists('./config.cfg'):
            os.remove('./config.cfg')
            shutil.copy(inputfile, './config.cfg')
        logging.info("\nPipeline configuration for this data reduction was read from " + str(inputfile) + \
        ", and if not named config.cfg, copied to ./config.cfg.")

    # Check if the user specified at command line to repeat the last Reduction, do a full default data reduction from a
    # recipe file or do a full data reduction from a handmade file.
    if interactive:
        # Get user input interactively.
        logging.info('\nInteractively creating a ./config.cfg configuration file.')
        fullReduction = getUserInput()

    if fullReduction:
        # Copy default input and use it
        shutil.copy(RECIPES_PATH+'defaultConfig.cfg', './config.cfg')
        # Update default config file with path to raw data or program ID.
        with open('./config.cfg', 'r') as config_file:
            config = ConfigObj(config_file, unrepr=True)
            sortConfig = config['sortConfig']
            if fullReduction[0] == "G":
                # Treat it as a program ID.
                sortConfig['program'] = fullReduction
                sortConfig['rawPath'] = ""
            else:
                # Else treat it as a path.
                sortConfig['program'] = ""
                sortConfig['rawPath'] = fullReduction
        with open('./config.cfg', 'w') as outfile:
            config.write(outfile)

        logging.info("\nData reduction parameters for this reduction were copied from recipes/defaultConfig.cfg to ./config.cfg.")

    if repeat:
        logging.info("\nOverwriting ./config.cfg with saved config from most recent data reduction.")
        if os.path.exists('./config.cfg'):
            os.remove('./config.cfg')
        shutil.copy(RUNTIME_DATA_PATH+'config.cfg', './config.cfg')

    # Print data reduction parameters for a user's peace-of-mind.
    logging.info("\nSaving data reduction parameters.")
    if os.path.exists(RUNTIME_DATA_PATH+'config.cfg'):
        os.remove(RUNTIME_DATA_PATH+'config.cfg')
    shutil.copy('./config.cfg', RUNTIME_DATA_PATH+'config.cfg')


    logging.info("\nParameters for this data reduction as read from ./config.cfg:\n")
    with open('./config.cfg') as config_file:
        config = ConfigObj(config_file, unrepr=True)
        for i in config:
            logging.info(str(i) + " " + str(config[i]))
    logging.info("")

    # Define parameters used by this script:
    with open('./config.cfg') as config_file:
        # Load general config.
        config = ConfigObj(config_file, unrepr=True)
        manualMode = config['manualMode']

        # Load pipeline specific config.
        linearPipelineConfig = config['linearPipelineConfig']

        sort = linearPipelineConfig['sort']
        calibrationReduction = linearPipelineConfig['calibrationReduction']
        telluricReduction = linearPipelineConfig['telluricReduction']
        scienceReduction = linearPipelineConfig['scienceReduction']

    ###########################################################################
    ##                         SETUP COMPLETE                                ##
    ##                      BEGIN DATA REDUCTION                             ##
    ##                                                                       ##
    ##        Four Main Steps:                                               ##
    ##          1) Sort the Raw Data - nifsSort.py                           ##
    ##          2) Reduce baseline calibrations - nifsBaselineCalibration.py ##
    ##          3) Reduce telluric observations - nifsReduce.py              ##
    ##          4) Reduce science observations - nifsReduce.py               ##
    ##                                                                       ##
    ###########################################################################

    ###########################################################################
    ##                      STEP 1: Sort the raw data.                       ##
    ###########################################################################

    if sort:
        if manualMode:
            a = raw_input('About to enter sort.')
        nifsSort.start()
    printDirectoryLists()

    ###########################################################################
    ##                STEP 2: Reduce baseline calibrations.                  ##
    ###########################################################################

    if calibrationReduction:
        if manualMode:
            a = raw_input('About to enter calibrate.')
        nifsBaselineCalibration.start()

    ###########################################################################
    ##                STEP 3: Reduce telluric observations.                  ##
    ###########################################################################

    if telluricReduction:
        if manualMode:
            a = raw_input('About to enter reduce to reduce Telluric images, create telluric correction spectrum and blackbody spectrum.')
        nifsReduce.start('Telluric')

    ###########################################################################
    ##                 STEP 4: Reduce science observations.                  ##
    ###########################################################################

    if scienceReduction:
        if manualMode:
            a = raw_input('About to enter reduce to reduce science images.')
        nifsReduce.start('Science')

    ###########################################################################
    ##                    Data Reduction Complete!                           ##
    ##                  Good luck with your science!                         ##
    ###########################################################################

    logging.info('#########################################')
    logging.info('#                                       #')
    logging.info('#        DATA REDUCTION COMPLETE        #')
    logging.info('#     Good luck with your science!      #')
    logging.info('#        Check out ??                   #')
    logging.info('#   For docs, recipes and examples.     #')
    logging.info('#                                       #')
    logging.info('#########################################')

    return

if __name__ == '__main__':
    # If running ./linearPipeline or python linearPipeline.py, call start.
    #Currently broken... Have to supply options somehow!
    #start()
    pass
