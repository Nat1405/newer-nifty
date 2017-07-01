# -*- coding: utf-8 -*-
################################################################################
#                Import some useful Python utilities/modules                   #
################################################################################
import sys
import glob
import shutil
import getopt
import os
import time
import logging
import pexpect as p
from pyraf import iraf, iraffunctions
import pyfits
from pyfits import getdata, getheader
import numpy as np
from scipy.interpolate import interp1d
from scipy import arange, array, exp
import glob
import pylab as pl
import sgmllib
import urllib, sgmllib
import re
import traceback
# Import custom Nifty functions.
from nifs_defs import datefmt, listit, writeList, checkLists, writeCenters, makeSkyList, MEFarith, convertRAdec

def start(
    observationDirectoryList, calDirList, start, stop, tel, telinter, fluxcal,
    continuuminter, hlineinter, hline_method, spectemp, mag, over):
    """

    nifsReduce

    Reduces NIFS telluric and science frames and attempts a flux calibration.

    There are 10 steps.

    COMMAND LINE OPTIONS
    If you wish to skip this script for science data
    enter -n in the command line
    If you wish to skip this script for telluric data
    enter -k in the command line
    Specify a start value with -b (default is 1)
    Specify a stop value with -x (default is 10)

    INPUT:
    + Raw files
        - Science frames
        - Sky frames
    + Calibration files
        - MDF shift file
        - Bad Pixel Mask (BPM)
        - Flat field frame
        - Reduced arc frame
        - Reduced ronchi mask frame

    OUTPUT:
        - If telluric reduction a reduced and calibrated telluric frame
        - If science reduction a reduced science frame data cube. Eg: c(a)tfbrgnSCI.fits)

    Args:
        One of:
            telDirList:      list of paths to telluric observations. [‘path/obj/date/grat/Tellurics/obsid’]
            obsDirList:      list of paths to science observations. [‘path/obj/date/grat/obsid’]
            calDirList:      list of paths to calibrations. [‘path/obj/date/Calibrations_grating’]
        tel (bool):          Perform telluric correction. Default True.
        telinter (bool):     Perform an interactive Telluric Correction. Default True.

    """

    # Store current working directory for later use.
    path = os.getcwd()

    # Enable optional debugging pauses.
    debug = False

    # Set up the logging file.
    FORMAT = '%(asctime)s %(message)s'
    DATEFMT = datefmt()
    logging.basicConfig(filename='Nifty.log',format=FORMAT,datefmt=DATEFMT,level=logging.DEBUG)
    log = os.getcwd()+'/Nifty.log'

    logging.info('#################################################')
    logging.info('#                                               #')
    logging.info('# Start the NIFS Science and Telluric Reduction #')
    logging.info('#                                               #')
    logging.info('#################################################')

    print '\n#################################################'
    print '#                                               #'
    print '# Start the NIFS Science and Telluric Reduction #'
    print '#                                               #'
    print '#################################################\n'

    # Set up/prepare IRAF.
    iraf.gemini()
    iraf.nifs()
    iraf.gnirs()
    iraf.gemtools()

    # Reset to default parameters the used IRAF tasks.
    iraf.unlearn(iraf.gemini,iraf.gemtools,iraf.gnirs,iraf.nifs,iraf.imcopy)

    # Prepare the IRAF package for NIFS.
    # NSHEADERS lists the header parameters used by the various tasks in the
    # NIFS package (excluding headers values which have values fixed by IRAF or
    # FITS conventions).
    iraf.nsheaders("nifs",logfile=log)

    # From http://bishop.astro.pomona.edu/Penprase/webdocuments/iraf/beg/beg-image.html:
    # Before doing anything involving image display the environment variable
    # stdimage must be set to the correct frame buffer size for the display
    # servers (as described in the dev$graphcap file under the section "STDIMAGE
    # devices") or to the correct image display device. The task GDEVICES is
    # helpful for determining this information for the display servers.
    iraf.set(stdimage='imt2048')

    # Set clobber to 'yes' for the script. This still does not make the gemini
    # tasks overwrite files, so:
    # YOU WILL LIKELY HAVE TO REMOVE FILES IF YOU RE_RUN THE SCRIPT.
    user_clobber=iraf.envget("clobber")
    iraf.reset(clobber='yes')

    # nifsReduce has two nested loops that reduced data.
    # It loops through each science (or telluric) directory, and
    # runs through a series of calibrations steps on the data in that directory.

    # Loop through all the observation directories to perform a reduction on each one.
    for observationDirectory in observationDirectoryList:
        os.chdir(observationDirectory)
        tempObs = observationDirectory.split(os.sep)

        # Find the Calibrations_grating directory that corresponds to the observation date and grating.
        # The observation date and grating are found from directory paths.
        for calDir in calDirList:
            tempCal = calDir.split(os.sep)
            # Need two cases because science directory paths are shorter than telluric
            # directory paths.
            # For science observation directories:
            # IF dates in path names match AND gratings in path names match, break.
            if tempObs[-3]==tempCal[-2] and tempObs[-2] == tempCal[-1][-1]:
                calDir = calDir+'/'
                break
            # For telluric observation directories.
            # IF dates in path names match AND gratings in path names match, break.
            elif tempObs[-4]==tempCal[-2] and tempObs[-3] == tempCal[-1][-1]:
                calDir = calDir+'/'
                break

        obsid = tempObs[-1]

        # Change the iraf directory to the current directory.
        pwd = os.getcwd()
        iraffunctions.chdir(pwd)

        # Open and store the name of the MDF shift reference file from shiftfile into shift.
        shift = calDir+str(open(calDir+"shiftfile", "r").readlines()[0]).strip()
        # Open and store the name of the flat frame from flatfile in flat.
        flat = calDir+str(open(calDir+"flatfile", "r").readlines()[0]).strip()
        # Open and store the name of the reduced spatial correction ronchi flat frame name from ronchifile in ronchi.
        ronchi = open(calDir+"ronchifile", "r").readlines()[0].strip()
        # Copy the spatial calibration ronchi flat frame from Calibrations_grating to the observation directory.
        iraf.copy(calDir+ronchi+".fits",output="./")
        # Open and store the bad pixel mask name from sflat_bpmfile in sflat_bpm.
        sflat_bpm = calDir+str(open(calDir+"sflat_bpmfile", "r").readlines()[0]).strip()
        # Open and store the name of the reduced wavelength calibration arc frame from arclist in arc.
        arc = "wrgn"+str(open(calDir+"arclist", "r").readlines()[0]).strip()
        # Copy the wavelength calibration arc frame from Calibrations_grating to the observation directory.
        iraf.copy(calDir+arc+".fits",output="./")

        # Determine whether the data is science or telluric.
        if tempObs[-2]=='Tellurics':
            kind = 'Telluric'
            objlist = open('tellist', 'r').readlines()
            objlist = [frame.strip() for frame in objlist]
            try:
                skylist = open("skylist", "r").readlines()
                skylist = [frame.strip() for frame in skylist]
            except:
                print "\nNo sky frames were found for standard star. Please make a skylist in the telluric directory\n"
                raise SystemExit
            sky = skylist[0]
        else:
            kind = 'Object'
            objlist = open("objlist", "r").readlines()
            objlist = [frame.strip() for frame in objlist]
            skylist = open("skylist", "r").readlines()
            skylist = [frame.strip() for frame in skylist]
            sky = skylist[0]

        # Check to see if the number of sky frames matches the number of science frames.
        # IF NOT duplicate the sky frames and rewrite the sky file and skylist.
        if not len(skylist)==len(objlist):
            skylist = makeSkyList(skylist, objlist, observationDirectory)



        centers = writeCenters(objlist)



        # Make sure the database files are in place. Current understanding is that
        # these should be local to the reduction directory, so need to be copied from
        # the calDir.
        if os.path.isdir("./database"):
            if over:
                shutil.rmtree("./database")
                os.mkdir("./database")
        elif not os.path.isdir("./database"):
            os.mkdir('./database/')
        iraf.copy(input=calDir+'database/*', output="./database/")

        # Check start and stop values for reduction steps. Ask user for a correction if
        # input is not valid.
        valindex = start
        while valindex > stop  or valindex < 1 or stop > 6:
            print "\n#####################################################################"
            print "#####################################################################"
            print ""
            print "     WARNING in reduce: invalid start/stop values of observation"
            print "                           reduction steps."
            print ""
            print "#####################################################################"
            print "#####################################################################\n"

            valindex = int(raw_input("\nPlease enter a valid start value (1 to 10, default 1): "))
            stop = int(raw_input("\nPlease enter a valid stop value (1 to 10, default 10): "))


        # Print the current directory of data being reduced.
        print "\n#################################################################################"
        print "                                   "
        print "  Currently working on reductions in"
        print "  in ", observationDirectory
        print "                                   "
        print "#################################################################################\n"


        while valindex <= stop :

            ###########################################################################
            ##  STEP 1: Prepare raw data ->n                                         ##
            ###########################################################################

            if valindex == 1:
                objlist = prepare(objlist, shift, sflat_bpm, log, over)
                skylist = prepare(skylist, shift, sflat_bpm, log, over)
                print "\n##############################################################################"
                print ""
                print "  STEP 1: Prepare raw data ->n - COMPLETED "
                print ""
                print "##############################################################################\n"

            ###########################################################################
            ##  STEP 2: Combine multiple frames ->gn                                 ##
            ###########################################################################

            elif valindex == 2:
                if kind=='Object':
                    if len(skylist)>1:
                        combineImages(skylist, "gn"+sky, log, over)
                    else:
                        copyImage(skylist, 'gn'+sky+'.fits', over)
                else:
                    pass
                print "\n##############################################################################"
                print ""
                print "  STEP 2: Combine multiple frames ->gn - COMPLETED "
                print ""
                print "##############################################################################\n"


            ###########################################################################
            ##  STEP 3: Sky Subtraction ->gn                                         ##
            ###########################################################################

            elif valindex == 3:
                skySubtractObj(objlist, skylist, log, over)
                print "\n##############################################################################"
                print ""
                print "  STEP 3: Sky Subtraction ->gn - COMPLETED "
                print ""
                print "##############################################################################\n"

            ###########################################################################
            ##  STEP 4: Flat field, slice and subtract dark ->rgn                    ##
            ###########################################################################

            elif valindex == 4:
                applyFlat(objlist, flat, log, over, kind)
                print "\n##############################################################################"
                print ""
                print "  STEP 4: Flat field ->rgn - COMPLETED "
                print ""
                print "##############################################################################\n"

            ###########################################################################
            ##  STEP 5: Correct bad pixels ->brgn                                    ##
            ###########################################################################

            elif valindex == 5:
                fixBad(objlist, log, over)
                print "\n##############################################################################"
                print ""
                print "  STEP 5: Correct bad pixels ->brgn - COMPLETED "
                print ""
                print "##############################################################################\n"

            ###########################################################################
            ##  STEP 6: Derive 2D to 3D transformation ->fbrgn                       ##
            ###########################################################################

            elif valindex == 6:
                fitCoords(objlist, arc, ronchi, log, over, kind)
                print "\n##############################################################################"
                print ""
                print "  STEP 6: Derive 2D to 3D transformation ->fbrgn - COMPLETED "
                print ""
                print "##############################################################################\n"

            ###########################################################################
            ##  STEP 7: Apply transformation ->tfbrgn                                ##
            ###########################################################################

            elif valindex == 7:
                transform(objlist, log, over)
                logging.info('Apply transformation ->tfbrgn')
                print "\n##############################################################################"
                print ""
                print "  STEP 7: Apply transformation ->tfbrgn - COMPLETED "
                print ""
                print "##############################################################################\n"

            ###########################################################################
            ##  STEP 8a: For telluric data derive telluric correction ->gxtfbrgn    ##
            ##       8b: For science data apply telluric correction ->atfbrgn       ##
            ###########################################################################

            elif valindex == 8:
                if kind=='Telluric':
                    makeTelluric(objlist, log, over)
                elif kind=='Object' and tel and telinter=='no':
                    makeCube('tfbrgn', objlist, False, observationDirectory, log, over)
                    applyTelluric(objlist, obsid, skylist, telinter, log, over)
                elif kind=='Object' and tel and telinter=='yes':
                    applyTelluric(objlist, obsid, skylist, telinter, log, over)
                print "\n##############################################################################"
                print ""
                print "  STEP 8: Derive or apply telluric correction ->gxtfbrgn or ->atgbrgn - COMPLETED "
                print ""
                print "##############################################################################\n"

            ###########################################################################
            ##  STEP 9: Create a 3D cube from science data ->catfbrgn or ->ctfbrgn   ##
            ###########################################################################

            elif valindex == 9:
                if kind=='Object' and telinter=='yes' and tel:
                    # Make cube with telluric correction.
                    makeCube('atfbrgn', objlist, tel, observationDirectory, log, over)
                elif kind=='Object' and not tel and telinter=='yes':
                    # Make cube without telluric correction.
                    makeCube('tfbrgn', objlist, tel, observationDirectory, log, over)
                elif kind == "Telluric":
                   print "\nNo cube being made for tellurics.\n"
                print "\n##############################################################################"
                print ""
                print "  STEP 9: Create a 3D cube from science data ->catfbrgn or ->ctfbrgn - COMPLETED "
                print ""
                print "##############################################################################\n"

            ###########################################################################
            ##  STEP 10: Perform a flux calibration ->fcatfbrgn or ->fctfbrgn        ##
            ###########################################################################
            elif valindex == 10:
                if fluxcal:
                    if kind == 'Telluric':
                        logging.info('Flux Calibration')
                        fluxCalibrate(
                            observationDirectory, path, continuuminter, hlineinter,
                            hline_method, spectemp, mag, log, over)
                print "\n##############################################################################"
                print ""
                print "  STEP 10: Perform a flux calibration ->fcatfbrgn or ->fctfbrgn - COMPLETED "
                print ""
                print "##############################################################################\n"


            valindex += 1

        print "\n##############################################################################"
        print ""
        print "  COMPLETE - Reductions completed for ", observationDirectory
        print ""
        print "##############################################################################\n"

    # Return to directory script was begun from.
    os.chdir(path)
    return

##################################################################################################################
#                                                     FUNCTIONS                                                 #
##################################################################################################################

def prepare(inlist, shiftima, sflat_bpm, log, over):
    """Prepare list of frames using iraf.nfprepare. Output: -->n.

    Processing with NFPREPARE (this task is used only for NIFS data
    but other instruments have their own preparation tasks
    with similar actions) will rename the data extension and add
    variance and data quality extensions. By default (see NSHEADERS)
    the extension names are SCI for science data, VAR for variance, and
    DQ for data quality (0 = good). Generation of the data quality
    plane (DQ) is important in order to fix hot and dark pixels on the
    NIFS detector in subsequent steps in the data reduction process.
    Various header keywords (used later) are also added in NFPREPARE.
    NFPREPARE will also add an MDF file (extension MDF) describing the
    NIFS image slicer pattern and how the IFU maps to the sky field.

"""

    # Update frames with mdf offset value and generate variance and data quality extensions.
    for frame in inlist:
        if os.path.exists("n"+frame+".fits"):
            if over:
                os.remove("n"+frame+".fits")
            else:
                print "Output file exists and -over not set - skipping prepare_list"
                continue
        iraf.nfprepare(frame, rawpath="", shiftimage=shiftima, fl_vardq="yes", bpm=sflat_bpm, logfile=log)
    inlist = checkLists(inlist, '.', 'n', '.fits')
    return inlist


#--------------------------------------------------------------------------------------------------------------------------------#

def combineImages(inlist, out, log, over):
    """Gemcombine multiple frames. Output: -->gn."""

    if os.path.exists(out+".fits"):
        if over:
            iraf.delete(out+".fits")
        else:
            print "Output file exists and -over not set - skipping combine_ima"
            return

    iraf.gemcombine(listit(inlist,"n"),output=out,fl_dqpr='yes', fl_vardq='yes',masktype="none",logfile=log)

#--------------------------------------------------------------------------------------------------------------------------------#

def copyImage(input, output, over):
    """Copy an image (used to add the correct prefix when skipping steps)."""

    if os.path.exists(output):
        if over:
            iraf.delete(output)
        else:
            print "Output file exists and -over not set - skipping copy_ima"
            return

    iraf.copy('n'+input[0]+'.fits', output)

#--------------------------------------------------------------------------------------------------------------------------------#

def skySubtractObj(objlist, skylist, log, over):
    """"Sky subtraction for science using iraf.gemarith. Output: ->gn"""

    for i in range(len(objlist)):
        frame = str(objlist[i])
        sky = str(skylist[i])
        if os.path.exists("gn"+frame+".fits"):
           if over:
               os.remove("gn"+frame+".fits")
           else:
               print "Output file exists and -over not set - skipping skysub_list"
               continue
        iraf.gemarith ("n"+frame, "-", "n"+sky, "gn"+frame, fl_vardq="yes", logfile=log)

#--------------------------------------------------------------------------------------------------------------------------------#

def skySubtractTel(tellist, sky, log, over):
    """Sky subtraction for telluric using iraf.gemarith. Output: ->gn"""

    for frame in tellist:
        if os.path.exists("gn"+frame+".fits"):
            if over:
                os.remove("gn"+frame+".fits")
            else:
                print "Output file exists and -over not set - skipping skysub_list"
                continue
        iraf.gemarith ("n"+frame, "-", sky, "gn"+frame, fl_vardq="yes", logfile=log)

#--------------------------------------------------------------------------------------------------------------------------------#

def applyFlat(objlist, flat, log, over, kind, dark=""):
    """Flat field and cut the data with iraf.nsreduce. Output: ->rgn.

    NSREDUCE is used for basic reduction of raw data - it provides a
    single, unified interface to several tasks and also allows for
    the subtraction of dark frames and dividing by the flat. For
    NIFS reduction, NSREDUCE is used to call the NSCUT and NSAPPWAVE
    routines.

    """

    # By default don't subtract darks from tellurics.
    fl_dark = "no"
    if dark != "":
        fl_dark = "yes"

    for frame in objlist:
        frame = str(frame).strip()
        if os.path.exists("rgn"+frame+".fits"):
            if over:
                os.remove("rgn"+frame+".fits")
            else:
                print "Output file exists and -over not set - skipping apply_flat_list"
                continue
        # Only subtract darks from Telluric frames.
        if kind == 'Object':
            iraf.nsreduce("gn"+frame, fl_cut="yes", fl_nsappw="yes", fl_dark="no", fl_sky="no", fl_flat="yes", flatimage=flat, fl_vardq="yes",logfile=log)
        elif kind == "Telluric":
            iraf.nsreduce("gn"+frame, darki=dark, fl_cut="yes", fl_nsappw="no", fl_dark=fl_dark, fl_sky="no", fl_flat="yes", flatimage=flat, fl_vardq="yes",logfile=log)

#--------------------------------------------------------------------------------------------------------------------------------#

def fixBad(objlist, log, over):
    """Interpolate over bad pixels flagged in the DQ plane with iraf.nffixbad. Output: -->brgn.

    NFFIXBAD - Fix Hot/Cold pixels on the NIFS detector.

    This routine uses the information in the Data Quality
    extensions to fix hot and cold pixels in the NIFS science
    fields. NFFIXBAD is a wrapper script which calls the task
    FIXPIX, using the DQ plane to define the pixels to be corrected.

    """

    for frame in objlist:
        frame = str(frame).strip()
        if os.path.exists("brgn"+frame+".fits"):
            if over:
                os.remove("brgn"+frame+".fits")
            else:
                print "Output file exists and -over not set - skipping fixbad_list"
                continue
        iraf.nffixbad("rgn"+frame,logfile=log)

#--------------------------------------------------------------------------------------------------------------------------------#

def fitCoords(objlist, arc, ronchi, log, over, kind):
    """Derive the 2D to 3D spatial/spectral transformation with iraf.nsfitcoords.
    Output: -->fbrgn

    NFFITCOORDS - Compute 2D dispersion and distortion maps.

    This routine uses as inputs the output from the NSWAVELENGTH
    and NFSDIST routines. NFFITCOORDS takes the spatial and
    spectral rectification information from NSWAVELENGTH and
    NFSDIST and converts this into a calculation of where the data
    information should map to in a final IFU dataset.

    """

    for frame in objlist:
        frame = str(frame).strip()
        if os.path.exists("fbrgn"+frame+".fits"):
            if over:
                os.remove("fbrgn"+frame+".fits")
            else:
                print "Output file exists and -over not set - skipping fitcoord_list"
                continue
        if kind=='Object':
            iraf.nsfitcoords("brgn"+frame,lamptransf=arc, sdisttransf=ronchi,logfile=log)
        elif kind=='Telluric':
            iraf.nsfitcoords("brgn"+frame, fl_int='no', lamptransf=arc, sdisttransf=ronchi, lxorder=4, syorder=4, logfile=log)

#--------------------------------------------------------------------------------------------------------------------------------#

def transform(objlist, log, over):
    """Apply the transformation determined in iraf.nffitcoords with
    iraf.nstransform. Output: -->tfbrgn

    NSTRANSFORM - Spatially rectify and wavelength calibrate data.

    NFTRANSFORM applies the wavelength solution found by
    NSWAVELENGTH and the spatial correction found by NFSDIST,
    aligning all the IFU extensions consistently onto a common
    coordinate system. The output of this routine is still in 2D
    format, with each of the IFU slices represented by its own data
    extension.

    """

    for frame in objlist:
        frame = str(frame).strip()
        if os.path.exists("tfbrgn"+frame+".fits"):
            if over:
                iraf.delete("tfbrgn"+frame+".fits")
            else:
                print "Output file exists and -over not set - skipping transform_list"
                continue
        iraf.nstransform("fbrgn"+frame, logfile=log)

#--------------------------------------------------------------------------------------------------------------------------------#

def makeTelluric(objlist, log, over):
    """Extracts 1-D spectra with iraf.nfextract and combines them with iraf.gemcombine.
    iraf.nfextract is currently only done interactively. Output: -->xtfbrgn and gxtfbrgn

    NFEXTRACT - Extract NIFS spectra.

    This could be used to extract a 1D spectra from IFU data and is
    particularly useful for extracting the bright spectra of
    telluric calibrator stars. Note that this routine only works
    on data that has been run through NFTRANSFORM.

    """

    for frame in objlist:
        frame = str(frame).strip()
        if os.path.exists("xtfbrgn"+frame+".fits"):
            if over:
                iraf.delete("xtfbrgn"+frame+".fits")
            else:
                print "Output file exists and -over not set - skipping extraction in make_telluric"
                continue
        # Set aperture diameter in arcseconds.
        diam = 0.5
        try:
            iraf.nfextract("tfbrgn"+frame, outpref="x", diameter=diam, fl_int='yes', logfile=log)
        except Exception as e:
            # Directory is left in a very messy state if nfextract attempted without ds9 running.
            # Attempt to do a bit of clean up if this happens.
            iraf.delete("xtfbrgn"+frame+".fits")
            logging.error(traceback.format_exc())
            raise SystemExit("ERROR: ds9 or another image viewer is not running in the background.")

    # Combine all the 1D spectra to one final output file.
    telluric = str(objlist[0]).strip()
    if os.path.exists("gxtfbrgn"+telluric+".fits"):
        if over:
            iraf.delete("gxtfbrgn"+telluric+".fits")
        else:
            print "Output file exists and -over not set - skipping gemcombine in make_telluric"
            return

    iraf.gemcombine(listit(objlist,"xtfbrgn"),output="gxtfbrgn"+telluric, statsec="[*]", combine="median",logfile=log,masktype="none",fl_vardq="yes")

    # Put the name of the final telluric correction file into a text file called
    # telluricfile to be used by the pipeline later.
    open("telluricfile", "w").write("gxtfbrgn"+telluric)

#--------------------------------------------------------------------------------------------------------------------------------#

def applyTelluric(objlist, obsid, skylist, telinter, log, over):
    """Corrects the data for telluric absorption features with iraf.nftelluric.
    iraf.nftelluric is currently only run interactively. Output: -->atfbrgn

    NFTELLURIC

    NFTELLURIC uses input science and a 1D spectrum of a telluric
    calibrator to correct atmospheric absorption features.
    """

    observationDirectory = os.getcwd()
    os.chdir('../Tellurics')
    telDirList = glob.glob('*')

    if telinter=='no':
        telCor(observationDirectory, telDirList, over)
    else:
        for telDir in telDirList:
            if 'obs' in telDir:
                os.chdir(telDir)
                if os.path.exists('objtellist'):
                    objtellist = open("objtellist", "r").readlines()
                    objlist = [frame.strip() for frame in objtellist]
                else:
                    os.chdir('..')
                    continue
                try:
                    telluric = str(open('corrtellfile', 'r').readlines()[0]).strip()
                except:
                    print "No telluric spectrum found in ", telDir
                    os.chdir('..')
                    continue
                shutil.copy(telluric+'.fits', observationDirectory)

                '''
                continuum = str(open('continuumfile', 'r').readlines()[0]).strip()
                bblist = open('blackbodyfile', 'r').readlines()
                bblist = [frame.strip() for frame in bblist]
                '''

                os.chdir(observationDirectory)
                iraffunctions.chdir(observationDirectory)
                if obsid in objlist:
                    index = objlist.index(obsid)
                    i=index+1

                    while i<len(objlist) and 'obs' not in objlist[i]:
                        if os.path.exists("atfbrgn"+objlist[i]+".fits"):
                            if over:
                                iraf.delete("atfbrgn"+objlist[i]+".fits")
                                iraf.nftelluric('tfbrgn'+objlist[i], outprefix='a', calspec=telluric, fl_inter = 'yes', logfile=log)
                            else:
                                print "Output file exists and -over not set - skipping nftelluric in applyTelluric"
                        elif not os.path.exists('atfbrgn'+objlist[i]+'.fits'):
                            iraf.nftelluric('tfbrgn'+objlist[i], outprefix='a', calspec=telluric, fl_inter = 'yes', logfile=log)

                        '''
                        # remove continuum fit from reduced science image
                        if over:
                            if os.path.exists("cont"+objlist[i]+".fits"):
                                iraf.delete("cont"+objlist[i]+".fits")
                            MEFarithpy('atfbrgn'+objlist[i], '../Tellurics/'+telDir+'/'+continuum, 'divide', 'cont'+objlist[i]+'.fits')
                        elif not os.path.exists('cont'+objlist[i]+'.fits'):
                            MEFarithpy('atfbrgn'+objlist[i], '../Tellurics/'+telDir+'/'+continuum, 'divide', 'cont'+objlist[i]+'.fits')
                        else:
                            print "Output file exists and -over not set - skipping continuum division in applyTelluric"

                        # multiply science by blackbody
                        for bb in bblist:
                            objheader = pyfits.open(observationDirectory+'/'+objlist[i]+'.fits')
                            exptime = objheader[0].header['EXPTIME']
                            if str(int(exptime)) in bb:
                                if over:
                                    if os.path.exists('bbatfbrgn'+objlist[i]+'.fits'):
                                        os.remove('bbatfbrgn'+objlist[i]+'.fits')
                                    MEFarithpy('cont'+objlist[i], '../Tellurics/'+telDir+'/'+bb, 'multiply', 'bbatfbrgn'+objlist[i]+'.fits')
                                elif not os.path.exists('bbatfbrgn'+objlist[i]+'.fits'):
                                    MEFarithpy('cont'+objlist[i], '../Tellurics/'+telDir+'/'+bb, 'multiply', 'bbatfbrgn'+objlist[i]+'.fits')
                                else:
                                    print "Output file exists and -over- not set - skipping blackbody calibration in applyTelluric"
                        '''
                        i+=1
            os.chdir('../Tellurics')

#--------------------------------------------------------------------------------------------------------------------------------#

def makeCube(pre, objlist, tel, observationDirectory, log, over):
    """ Reformat the data into a 3-D datacube using iraf.nifcube. Output: If
    telluric correction to be applied, -->catfbrgn. Else, -->ctfbrgn.

    NIFCUBE - Construct 3D NIFS datacubes.

    NIFCUBE takes input from data output by either NFFITCOORDS or
    NFTRANSFORM and converts the 2D data images into data cubes
    that have coordinates of x, y, lambda.

    """

    os.chdir(observationDirectory)
    for frame in objlist:
        if os.path.exists("c"+pre+frame+".fits"):
            if over:
                iraf.delete("c"+pre+frame+".fits")
            else:
                print "Output file exists and -over not set - skipping make_cube_list"
                continue
        if tel:
            iraf.nifcube (pre+frame, outcubes = 'c'+pre+frame, logfile=log)
            hdulist = pyfits.open('c'+pre+frame+'.fits', mode = 'update')
#            hdulist.info()
            exptime = hdulist[0].header['EXPTIME']
            cube = hdulist[1].data
            gain = 2.8
            cube_calib = cube / (exptime * gain)
            hdulist[1].data = cube_calib
            hdulist.flush()
        else:
            iraf.nifcube (pre+frame, outcubes = 'c'+pre+frame, logfile=log)

#--------------------------------------------------------------------------------------------------------------------------------#

def fluxCalibrate(
    observationDirectory, path, continuuminter, hlineinter, hline_method, spectemp,
    mag, log, over):
    """FLUX CALIBRATION

    Consists of this start function and six required functions at the end of
    this file.


    COMMAND LINE OPTIONS
    If you wish to skip this script enter -g in the command line
    Specify a spectral type or temperature with -e
    Specify a magnitude with -f
    Specify an H line fitting method with -l (default is vega)
    Specify interactive H line fitting with -i (default inter=no)
    Specify interactive continuum fitting with -y (def inter=no)

    INPUT:
    - reduced and combined standard star spectra

    OUTPUT:
    - reduced (H line and continuum fit) standard star spectra
    - flux calibrated blackbody spectrum

    Args:
        telDirList: list of telluric directories.
        continuuminter (boolean): Interactive continuum fitting. Specified with -y
                                  at command line. Default False.
        hlineinter (boolean):     Interactive H line fitting. Specified with -i at
                                  command line. Default False.
        hline_method (string):    Method for removing H lines from the telluric spectra.
                                  Specified with -l or --hline at command line. Default is
                                  vega and choices are vega, linefit_auto, linefit_manual,
                                  vega_tweak, linefit_tweak, and none.
        spectemp:                 Spectral type or temperature. Specified at command line with -e or --stdspectemp.
        mag:                      The IR magnitude of the standard star.
                                  Specified at command line with -f or --stdmag.
        over:                     overwrite old files.
    """
    iraf.gemini(_doprint=0, motd="no")
    iraf.gnirs(_doprint=0)
    iraf.imutil(_doprint=0)
    iraf.onedspec(_doprint=0)
    iraf.nsheaders('nifs',Stdout='/dev/null')

    iraffunctions.chdir(observationDirectory)

    print ' I am starting to create telluric correction spectrum and blackbody spectrum'
    logging.info('I am starting to create telluric correction spectrum and blackbody spectrum ')

    # open and define standard star spectrum and its relevant header keywords
    try:
        standard = str(open('telluricfile', 'r').readlines()[0]).strip()
    except:
        print "No telluricfile found in ", observationDirectory
        return
    if not os.path.exists('objtellist'):
        print "No objtellist found in ", observationDirectory
        return

    telheader = pyfits.open(standard+'.fits')
    band = telheader[0].header['GRATING'][0]
    RA = telheader[0].header['RA']
    Dec = telheader[0].header['DEC']
    airmass_std = telheader[0].header['AIRMASS']
    temp1 = os.path.split(observationDirectory)
    temp2 = os.path.split(temp1[0])
    # make directory PRODUCTS above the Telluric observation directory
    # telluric_hlines.txt is stored there
    if not os.path.exists(temp1[0]+'/PRODUCTS'):
        os.mkdir(temp1[0]+'/PRODUCTS')

    # defines 'name' that is passed to mag2mass
    if '-' in str(Dec):
        name = str(RA)+'d'+str(Dec)+'d'
    else:
        name = str(RA)+'d+'+str(Dec)+'d'

    # find standard star spectral type, temperature, and magnitude
    mag2mass(name, path, spectemp, mag, band)
    print " list", name, path, spectemp, mag, band

    # File for recording shift/scale from calls to "telluric"
    t1 = open('telluric_hlines.txt', 'w')

    # Remove H lines from standard star
    no_hline = False
    if os.path.exists("ftell_nolines"+band+'.fits'):
        if over:
            iraf.delete("ftell_nolines"+band+'.fits')
        else:
            no_hline = True
            print "Output file exists and -over- not set - skipping H line removal"

    if hline_method == "none":
        #need to copy files so have right names for later use
        iraf.imcopy(input=standard+'[sci,'+str(1)+']', output="ftell_nolines"+band, verbose='no')

    #if hline_method == "none" and not no_hline:
    #    print ""
    #    print "***Removing intrinsic lines in standard star***"
    #    print ""

    if hline_method == "vega" and not no_hline:
        vega(standard, band, path, hlineinter, airmass_std, t1, log, over)

    if hline_method == "linefit_auto" and not no_hline:
        linefit_auto(standard, band)

    if hline_method == "linefit_manual" and not no_hline:
        linefit_manual(standard+'[sci,1]', band)

    if hline_method == "vega_tweak" and not no_hline:
        #run vega removal automatically first, then give user chance to interact with spectrum as well
        vega(standard,band, path, hlineinter, airmass_std, t1, log, over)
        linefit_manual("ftell_nolines"+band, band)

    if hline_method == "linefit_tweak" and not no_hline:
        #run Lorentz removal automatically first, then give user chance to interact with spectrum as well
        linefit_auto(standard,band)
        linefit_manual("ftell_nolines"+band, band)

    # make a list of exposure times from the science images that use this standard star spectrum for the telluric correction
    # used to make flux calibrated blackbody spectra
    objtellist = open('objtellist', 'r').readlines()
    objtellist = [frame.strip() for frame in objtellist]
    exptimelist = []
    for item in objtellist:
        if 'obs' in item:
            os.chdir(observationDirectory)
            os.chdir('../../'+item)
        else:
            objheader = pyfits.open(item+'.fits')
            exptime = objheader[0].header['EXPTIME']
            if not exptimelist or exptime not in exptimelist:
                exptimelist.append(int(exptime))

    os.chdir(observationDirectory)
    for tgt_exp in exptimelist:

        # Make blackbody spectrum to be used in nifsScience.py
        file = open('std_star.txt','r')
        lines = file.readlines()
        #Extract stellar temperature from std_star.txt file , for use in making blackbody
        star_kelvin = float(lines[0].replace('\n','').split()[3])
        #Extract mag from std_star.txt file and convert to erg/cm2/s/A, for a rough flux scaling

        try:
            #find out if a matching band mag exists in std_star.txt
            if band == 'K':
                star_mag = lines[0].replace('\n','').split()[2]
                star_mag = float(star_mag)
                flambda = 10**(-star_mag/2.5) * 4.28E-11
            if band == 'H':
                star_mag = lines[1].replace('\n','').split()[2]
                star_mag = float(star_mag)
                flambda = 10**(-star_mag/2.5) * 1.133E-10
            if band == 'J':
                star_mag = lines[2].replace('\n','').split()[2]
                star_mag = float(star_mag)
                flambda = 10**(-star_mag/2.5) * 3.129E-10
            print "flambda=", flambda

        except:
            #if not then just set to 1; no absolute flux cal. attempted
            flambda = 1
            print "No ", band, " magnitude found for this star. A relative flux calibration will be performed"
            print "star_kelvin=", star_kelvin
            print "star_mag=", star_mag

        effspec(observationDirectory, standard, 'ftell_nolines'+band+'.fits', star_mag, star_kelvin, over)



##################################################################################################################
#                                               TELLURIC FUNCTIONS                                               #
##################################################################################################################


def extrap1d(interpolator):
    xs = interpolator.x
    ys = interpolator.y

    def pointwise(x):
        if x < xs[0]:
            return ys[0]+(x-xs[0])*(ys[1]-ys[0])/(xs[1]-xs[0])
        elif x > xs[-1]:
            return ys[-1]+(x-xs[-1])*(ys[-1]-ys[-2])/(xs[-1]-xs[-2])
        else:
            return interpolator(x)

    def ufunclike(xs):
        return array(map(pointwise, array(xs)))

    return ufunclike

def readCube(cube):

    # read cube into an HDU list
    cube = pyfits.open(cube)

    # find the starting wavelength and the wavelength increment from the science header of the cube
    wstart = cube[1].header['CRVAL3']
    wdelt = cube[1].header['CD3_3']

    # initialize a wavelength array
    wavelength = np.zeros(2040)

    # create a wavelength array using the starting wavelength and the wavelength increment
    for i in range(2040):
        wavelength[i] = wstart+(wdelt*i)

    return cube, wavelength

def readSpec(spectrum, MEF=True):

    if MEF:

        # open the spectrum as an HDU list
        spec = pyfits.open(spectrum)

        # find the starting wavelength and the wavelength increment from the science header
        wstart = spec[1].header['CRVAL1']
        wdelt = spec[1].header['CD1_1']

    else:

        # open the spectrum as an HDU list
        spec = pyfits.open(spectrum)

        # find the starting wavelength and the wavelength increment from the science header
        wstart = spec[0].header['CRVAL1']
        wdelt = spec[0].header['CD1_1']

    # initialize a wavelength array
    wavelength = np.zeros(2040)

    # create a wavelength array using the starting wavelength and the wavelength increment
    for i in range(2040):
        wavelength[i] = wstart+(wdelt*i)

    return spec, wavelength

def telCor(obsDir, telDirList_temp, over):
    tempDir = os.path.split(obsDir)
    telDirList = []
    for telDir in telDirList_temp:
        telDirList.append(tempDir[0]+'/Tellurics/'+telDir)
    for telDir in telDirList:
        # change to the telluric directory
        os.chdir(telDir)

        # open the corrected telluric
        try:
            objlist = open('objtellist', 'r').readlines()
            objlist = [item.strip() for item in objlist]
        except:
            os.chdir('..')
            continue

        telluric = str(open('corrtellfile', 'r').readlines()[0]).strip()
        # read in telluric spectrum data
        telluric, effwave = readSpec(telluric+'.fits')
        effspec = telluric[1].data
        telairmass = telluric[0].header['AIRMASS']
        #continuum = str(open('continuumfile', 'r').readlines()[0]).strip()
        # read in continuum spectrum data
        #continuum, contwave = readSpec(continuum+'.fits', MEF=False)
        #contflux=continuum[0].data

        #bblist = open('blackbodyfile', 'r').readlines()
        #bblist = [frame.strip() for frame in bblist]


        tempDir = obsDir.split(os.sep)
        if tempDir[-1] in objlist:
            os.chdir(obsDir)
            scilist = glob.glob('c*.fits')
            for frame in scilist:
                if frame.replace('ctfbrgn','').replace('.fits', '') in objlist:
                    if os.path.exists(frame[0]+'p'+frame[1:]):
                        if not over:
                            print 'Output already exists and -over- not set - skipping telluric correction and flux calibration'
                            continue
                        if over:
                            os.remove(frame[0]+'p'+frame[1:])
                            pass
                    np.set_printoptions(threshold=np.nan)


                    # read in cube data
                    cube, cubewave = readCube(frame)

                    # interpolate a function using the telluric spectrum
                    func = interp1d(effwave, effspec, bounds_error = None, fill_value=0.)

                    # use the wavelength array of the cube to shift the telluric and continuum flux arrays
                    func2 = extrap1d(func)
                    effspec = func2(cubewave)

                    #func3 = interp1d(contwave, contflux, bounds_error = None, fill_value=0.)
                    #func4 = extrap1d(func3)
                    #contfluxi = func4(cubewave)

                    #pl.plot(telwave, telflux, 'r', cubewave, funcc(cubewave), 'g')
                    #pl.show()


                    exptime = cube[0].header['EXPTIME']

                    '''
                    try:
                        sciairmass = cube[0].header['AIRMASS']
                        airmcor = True
                    except:
                        print "No airmass found in header. No airmass correction being performed on "+frame
                        airmcor= False

                    if airmcor:
                        amcor = sciairmass/telairmass

                        for i in range(len(telflux)):
                            if telfluxi[i]>0. and telfluxi[i]<1.:
                                telfluxi[i] = np.log(telfluxi[i])
                                telfluxi[i] *=amcor
                                telfluxi[i] = np.exp(telfluxi[i])
                        '''

                    try:
                        sciairmass = cube[0].header['AIRMASS']
                        airmcor = True
                    except:
                        print "No airmass found in header. No airmass correction being performed on "+frame
                        airmcor= False

                    if airmcor:
                        amcor = sciairmass/telairmass

                    for i in range(len(effspec)):
                        if effspec[i]>0. and effspec[i]<1.:
                            effspec[i] = np.log(effspec[i])
                            effspec[i] *=amcor
                            effspec[i] = np.exp(effspec[i])

                    # divide each spectrum in the cubedata array by the efficiency spectrum
                    print frame
                    for i in range(cube[1].header['NAXIS2']):
                        for j in range(cube[1].header['NAXIS1']):
                            cube[1].data[:,i,j] /= (effspec*exptime)

                    '''
                    # divide each spectrum in the cubedata array by the telluric spectrum
                    for i in range(62):
                        for j in range(60):
                            cube[1].data[:,i,j] /= telfluxi

                    for i in range(62):
                        for j in range(60):
                            cube[1].data[:,i,j] /= contfluxi

                    for bb in bblist:
                        exptime = cube[0].header['EXPTIME']
                        if str(int(exptime)) in bb:
                            os.chdir(telDir)
                            blackbody, bbwave = readSpec(bb+'.fits', MEF=False)
                            bbflux = blackbody[0].data
                            for i in range(cube[0].header['NAXIS2']):
                                for j in range(cube[0].header['NAXIS1']):
                                    cube[1].data[:,i,j] *= bbflux
                        '''

                    os.chdir(obsDir)
                    cube.writeto(frame[0]+'p'+frame[1:], output_verify='ignore')


##################################################################################################################
#                                       FLUX CALIBRATION FUNCTIONS                                               #
##################################################################################################################

def mag2mass(name, path, spectemp, mag, band):
    """Find standard star spectral type, temperature, and magnitude. Write results
       to std_star.txt in cwd.

    Executes a SIMBAD query and parses the resulting html to find spectal type,
    temperature and/or magnitude.

        Args:
            name (string): RA, d, Dec, d (for negatives); RA, +d, Dec, d (for positives).
            path: current working directory (usually with Nifty files).
            spectemp: specified at command line with -e.
            mag: specified at command line with -f.
            band: from the telluric standard .fits file header. Eg 'J', 'K'.

    """

    starfile = 'std_star.txt'
    kelvinfile = path+'/starstemp.txt'

    sf = open(starfile,'w')
    klf = open (kelvinfile)
    Kmag = ''
    Jmag = ''
    Hmag = ''

    # check to see if a spectral type or temperature has been given
    if spectemp:
        if not isinstance(spectemp[0], int):
            spectral_type = spectemp
            specfind = False
            tempfind = True
        else:
            kelvin = spectemp
            tempfind = False
            specfind = False
    else:
        specfind = True
        tempfind = True
    if mag:
        magfind = False
        if band=='K':
            Kmag=mag
        if band=='H':
            Hmag=mag
        if band=='J':
            Jmag=mag
    else:
        magfind = True

    if specfind or tempfind or magfind:
        #Construct URL based on standard star coords, execute SIMBAD query to find spectral type
        name = name.replace("+","%2b")
        name = name.replace("-", "%2D")
        start_name='http://simbad.u-strasbg.fr/simbad/sim-coo?Coord='
        end_name = '&submit=submit%20query&Radius.unit=arcsec&Radius=10'
        www_page = start_name+name+end_name
        f = urllib.urlopen(www_page)
        html2 = f.read()
        html2 = html2.replace(' ','')
        search_error = str(html2.split('\n'))


        #Exit if the lookup found nothing.
        if 'Noastronomicalobjectfound' in search_error:
            print "ERROR: no object was found at the coordinates you entered. You'll need to supply information in a file; see the manual for instructions."

        #If >1 object found, decrease search radius and try again
        if 'Numberofrows:' in search_error:
            start_name='http://simbad.u-strasbg.fr/simbad/sim-coo?Coord='
            end_name = '&submit=submit%20query&Radius.unit=arcsec&Radius=1'
            www_page = start_name+name+end_name
            f = urllib.urlopen(www_page)
            html2 = f.read()
            html2 = html2.replace(' ','')
            search_error = str(html2.split('\n'))

        #If that didn't return anything, exit and let the user sort it out
        if 'Noastronomicalobjectfound' in search_error:
            print "ERROR: didn't find a star at your coordinates within a search radius of 10 or 1 arcsec. You'll need to supply information in a file; see the manual for instructions."
            sys.exit()


        # Split source by \n into a list
        html2 = html2.split('\n')



        if specfind:
            count = 0
            aux = 0
            for line in html2:
                if (line[0:13] == 'Spectraltype:') :
                    numi = aux + 5
                    count = 0
                    break
                else:
                    count += 1
                aux += 1
            print html2[aux:numi+1]
            spectral_type = str(html2[numi][0:3])
            if count > 0:
                print "ERROR: problem with SIMBAD output. You'll need to supply the spectral type or temperature in the command line prompt."
                sys.exit()


        if magfind:
            for line in html2:

                if 'Fluxes' in line:
                    i = html2.index(line)
                    break
            while 'IMGSRC' not in html2[i]:
                if all(s in html2[i] for s in ('K', '[', ']')):
                    if 'C' in html2[i+2]:
                        index = html2[i].index('[')
                        Kmag = html2[i][1:index]
                if all(s in html2[i] for s in ('H', '[', ']')):
                    if 'C' in html2[i+2]:
                        index = html2[i].index('[')
                        Hmag = html2[i][1:index]
                if all(s in html2[i] for s in ('J', '[', ']')):
                    if 'C' in html2[i+2]:
                        index = html2[i].index('[')
                        Jmag = html2[i][1:index]
                i+=1
                if i>len(html2):
                    print "ERROR: problem with SIMBAD output. You'll need to supply the magniture in the command line prompt."


        if not Kmag:
            Kmag = 'nothing'
        if not Jmag:
            Jmag = 'nothing'
        if not Hmag:
            Hmag = 'nothing'



        if tempfind:
            #Find temperature for this spectral type in kelvinfile
            count = 0
            for line in klf:
                if '#' in line:
                    continue
                else:
                    if	spectral_type in line.split()[0]:
                        kelvin = line.split()[1]
                        count = 0
                        break
                    else:
                        count+=1

            if count > 0:
                print "ERROR: can't find a temperature for spectral type", spectral_type,". You'll need to supply information in a file; see the manual for instructions."
                sys.exit()


        # Write results to std_star.txt
        if (Kmag or Jmag or Hmag) and Kmag!='x' and magfind:
            print "magnitudes retrieved OK"
            sf.write('k K '+Kmag+' '+kelvin+'\n')
            sf.write('h H '+Hmag+' '+kelvin+'\n')
            sf.write('j J '+Jmag+' '+kelvin+'\n')
            sf.write('j J '+Jmag+' '+kelvin+'\n')

        elif (Kmag or Jmag or Hmag) and Kmag!='x' and not magfind:
            sf.write('k K '+Kmag+' '+kelvin+'\n')
        elif Kmag=='x':
            print "WARNING: no magnitudes found for standard star. Doing relative flux calibration only."
            sf.write('k K N/A '+kelvin+' \n')
            sf.write('h H N/A '+kelvin+' \n')
            sf.write('j J N/A '+kelvin+' \n')
            sf.write('j J N/A '+kelvin+' \n')

    sf.close()
    klf.close()

#-------------------------------------------------------------------------------#

def write_line_positions(nextcur, var):
    """Write line x,y info to file containing Lorentz fitting commands for bplot

    """

    curfile = open(nextcur, 'w')
    i=-1
    for line in var:
        i+=1
        if i!=0:
            var[i]=var.split()
            var[i][2]=var[i][2].replace("',",'').replace("']", '')
        if not i%2 and i!=0:
            #even number, means RHS of H line
            #write x and y position to file, also "k" key
            curfile.write(var[i][0]+" "+var[i][2]+" 1 k \n")
            #LHS of line, write info + "l" key to file
            curfile.write(var[i-1][0]+" "+var[i-1][2]+" 1 l \n")
            #now repeat but writing the "-" key to subtract the fit
            curfile.write(var[i][0]+" "+var[i][2]+" 1 - \n")
            curfile.write(var[i-1][0]+" "+var[i-1][2]+" 1 - \n")
        curfile.write("0 0 1 i \n")
        curfile.write("0 0 q \n")
        curfile.close()

#-------------------------------------------------------------------------------#

def vega(spectrum, band, path, hlineinter, airmass, t1, log, over):
    """Use iraf.telluric to remove H lines from standard star, then remove
    normalization added by telluric with iraf.imarith.

    The extension for vega_ext.fits is specified from band (from header of
    telluricfile.fits).

    Args:
        spectrum (string): filename from 'telluricfile'.
        band: from telluricfile .fits header. Eg 'K', 'H', 'J'.
        path: usually top directory with Nifty scripts.
        hlineinter (boolean): Interactive H line fitting. Specified with -i at
                              command line. Default False.
        airmass: from telluricfile .fits header.
        t1: "pointer" to telluric_hlines.txt.
        log: path to logfile.
        over (boolean): overwrite old files. Specified at command line.

    """
    if band=='K':
        ext = '1'
    if band=='H':
        ext = '2'
    if band=='J':
        ext = '3'
    if band=='Z':
        ext = '4'
    if os.path.exists("tell_nolines"+band+".fits"):
            if over:
                os.remove("tell_nolines"+band+".fits")
                tell_info = iraf.telluric(input=spectrum+"[1]", output='tell_nolines'+band, cal=path+'/vega_ext.fits['+ext+']', answer='yes', ignoreaps='yes', xcorr='yes', airmass = airmass, tweakrms='yes', inter=hlineinter, threshold=0.1, lag=3, shift=0., dshift=0.05, scale=.75, dscale=0.05, offset=0., smooth=1, cursor='', mode='al', Stdout=1)
            else:
                print "Output file exists and -over not set - skipping H line correction"
    else:
        tell_info = iraf.telluric(input=spectrum+"[1]", output='tell_nolines'+band, cal=path+'/vega_ext.fits['+ext+']', answer='yes', ignoreaps='yes', xcorr='yes', airmass = airmass, tweakrms='yes', inter=hlineinter, threshold=0.1, lag=3, shift=0., dshift=0.05, scale=1., dscale=0.05, offset=0, smooth=1, cursor='', mode='al', Stdout=1)

    # record shift and scale info for future reference
    t1.write(str(tell_info)+'\n')
    # need this loop to identify telluric output containing warning about pix outside calibration limits (different formatting)
    if "limits" in tell_info[-1].split()[-1]:
        norm=tell_info[-2].split()[-1]
    else:
        norm=tell_info[-1].split()[-1]

    if os.path.exists("ftell_nolines"+band+".fits"):
        if over:
            os.remove("ftell_nolines"+band+".fits")
            iraf.imarith(operand1='tell_nolines'+band, op='/', operand2=norm, result='ftell_nolines'+band, title='', divzero=0.0, hparams='', pixtype='', calctype='', verbose='yes', noact='no', mode='al')
        else:
            print "Output file exists and -over not set - skipping H line normalization"
    else:
        iraf.imarith(operand1='tell_nolines'+band, op='/', operand2=norm, result='ftell_nolines'+band, title='', divzero=0.0, hparams='', pixtype='', calctype='', verbose='yes', noact='no', mode='al')

#-------------------------------------------------------------------------------#

def linefit_auto(spectrum, band):
    """automatically fit Lorentz profiles to lines defined in existing cur* files
    Go to x position in cursor file and use space bar to find spectrum at each of those points
    """

    specpos = iraf.bplot(images=spectrum+'[SCI,1]', cursor='cur'+band, Stdout=1, StdoutG='/dev/null')
    specpose = str(specpos).split("'x,y,z(x):")
    nextcur = 'nextcur'+band+'.txt'
    # Write line x,y info to file containing Lorentz fitting commands for bplot
    write_line_positions(nextcur, specpos)
    iraf.delete('ftell_nolines'+band+'.fits,Lorentz'+band,ver="no",go_ahead='yes',Stderr='/dev/null')
    # Fit and subtract Lorentz profiles. Might as well write output to file.
    iraf.bplot(images=spectrum+'[sci,1]',cursor='nextcur'+band+'.txt', new_image='ftell_nolines'+band, overwrite="yes",StdoutG='/dev/null',Stdout='Lorentz'+band)

#-------------------------------------------------------------------------------#

def linefit_manual(spectrum, band):
    """ Enter splot so the user can fit and subtract lorents (or, actually, any) profiles
    """

    iraf.splot(images=spectrum, new_image='ftell_nolines'+band, save_file='../PRODUCTS/lorentz_hlines.txt', overwrite='yes')
    # it's easy to forget to use the 'i' key to actually write out the line-free spectrum, so check that it exists:
    # with the 'tweak' options, the line-free spectrum will already exists, so this lets the user simply 'q' and move on w/o editing (too bad if they edit and forget to hit 'i'...)
    while True:
        try:
            with open("ftell_nolines"+band+".fits") as f: pass
            break
        except IOError as e:
            print "It looks as if you didn't use the if key to write out the lineless spectrum. We'll have to try again. --> Re-entering splot"
            iraf.splot(images=spectrum, new_image='ftell_nolines'+band, save_file='../PRODUCTS/lorentz_hlines.txt', overwrite='yes')

#-------------------------------------------------------------------------------#

def effspec(telDir, standard, telnolines, mag, T, over):
    """This flux calibration method was adapted to NIFS.

    Args:
        telDir: telluric directory.
        standard: "pointer" to file named in telluricfile.
        telnolines (string): filename.
        mag: IR magnitude of standard star.
        T: temperature in kelvin.
        over (boolean): overwrite old files.

    """

    # define constants
    c = 2.99792458e8
    h = 6.62618e-34
    k = 1.3807e-23

    f0emp = lambda p, T: p[0]*np.log(T)**2+p[1]*np.log(T)+p[2]
    fnu = lambda x, T: (2.*h*(x**3)*(c**(-2)))/(np.exp((h*x)/(k*T))-1)
    flambda = lambda x, T: (2.*h*(c**2)*(x**(-5)))/((np.exp((h*c)/(x*k*T)))-1)

    print 'Input Standard spectrum for flux calibration is ', standard

    if os.path.exists('c'+standard+'.fits'):
        if not over:
            print 'Output already exists and -over- not set - calculation of efficiency spectrum'
            return
        if over:
            os.remove('c'+standard+'.fits')
            pass
    telluric = pyfits.open(telnolines)
    telheader = pyfits.open(standard+'.fits')
    band = telheader[0].header['GRATING'][0]
    exptime = float(telheader[0].header['EXPTIME'])
    telfilter = telheader[0].header['FILTER']

    # define wavelength array
    telwave = np.zeros(telheader[1].header['NAXIS1'])
    wstart = telheader[1].header['CRVAL1']
    wdelt = telheader[1].header['CD1_1']
    for i in range(len(telwave)):
        telwave[i] = wstart+(i*wdelt)

    if 'HK' in telfilter:
        coeff =[1.97547589e-02, -4.19035839e-01, -2.30083083e+01]
        lamc = 22000.
    if 'JH' in telfilter:
        coeff = [1.97547589e-02, -4.19035839e-01,  -2.30083083e+01]
        lamc = 15700.
    if 'ZJ' in telfilter:
        coeff = [0.14903624, -3.14636068, -9.32675924]
        lamc = 11100.

    lamc = telheader[0].header['WAVELENG']
    f0 = np.exp(f0emp(coeff, T))

    # create black body spectrum at a given temperature
    blackbody = (flambda(telwave*1e-10, T))*1e-7

    lamc_ind = np.where(telwave==min(telwave, key=lambda x:abs(x-lamc)))

    tel_bb = telluric[0].data/blackbody
    csb = tel_bb[lamc_ind[0]]
    cs =  telluric[0].data[lamc_ind[0]]

    effspec =  (tel_bb/exptime)*(cs/csb)*(10**(0.4*mag))*(f0)**-1
    print 'effspec =', effspec

    telheader[1].data = effspec
    telheader.writeto('c'+standard+'.fits',  output_verify='ignore')
    writeList('c'+standard, 'corrtellfile', telDir)

#-------------------------------------------------------------------------------#

if __name__ == '__main__':
    print "nifsScience"
