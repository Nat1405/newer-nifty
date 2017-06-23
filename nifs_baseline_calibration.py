################################################################################
#                Import some useful Python utilities/modules                   #
################################################################################
import logging
from pyraf import iraf
from pyraf import iraffunctions
import pyfits
import logging, os
# Import custom Nifty functions
from nifs_defs import datefmt, listit, checkLists

def start(obsDirList, calDirList, over, start, stop):
    """
         nifs_baseline_calibration

         This module contains all the functions needed to reduce
         NIFS GENERAL BASELINE CALIBRATIONS

         COMMAND LINE OPTIONS
         If you wish to skip this step enter -r in the command line
         Specify a start value with -a (default is 1) in command line
         Specify a stop value with -z (default is 6) in command line

         INPUT FILES FOR EACH BASELINE CALIBRATION:

         + Raw files
           - Flats images (lamps on)
           - Flats images (lamps off)
           - Arcs images
           - Arcs Darks images
           - Ronchi masks images

         OUTPUT FILES:
         - Shift file. (ie sCALFLAT.fits)
         - Bad Pixel Mask. (ie rgnCALFLAT_sflat_bmp.pl)
         - Flat field. (ie rgnCALFLAT_flat.fits)
         - Reduced arc frame. (ie wrgnARC.fits)
         - Reduced ronchi mask. (ie. rgnRONCHI.fits)
         - Reduced dark frame. (ie. rgnARCDARK.fits)

    Args:
        obsDirList:      list of paths to science observations. ['path/obj/date/grat/obsid']
        calDirList:      list of paths to calibrations. ['path/obj/date/calibrations']
        over (boolean):  overwrite old files. Default: False.
        start (int):     starting step of daycal reduction. Specified at command line with -a. Default: 1.
        stop (int):      stopping step of daycal reduction. Specified at command line with -z. Default: 6.

    Directory structure after Calibration:

    --->cwd/
        --->Nifty files (eg Main.py, sort.py, Nifty.log)
            --->objectname/ (Science target name- found from .fits file headers).
                --->date/ (YYYYMMDD)
                    --->Calibrations/
                        --->N*.fits (calibration .fits files)
                        --->nN*.fits
                        --->nN*.fits
                        --->nN*.fits
                        --->nN*.fits
                        --->gnN*.fits
                        --->gnN*.fits
                        --->gnN*.fits
                        --->gnN*.fits
                        --->rgnN*.fits
                        --->rgnN*.fits
                        --->rgnN*.fits
                        --->rgnN*_sflat.fits
                        --->rgnN*_sflat.bpm.pl
                        --->rgnN*_flat.fits
                        --->brgnN*.fits
                        --->wrgnN*.fits
                        --->arcdarkfile (text file storing name of the arcdark file)
                        --->arcdarklist (list of .fits files)
                        --->arclist (list of .fits files)
                        --->database/
                        --->idrgn_SCI_[i]_
                        --->idwrgn_SCI_[i]_
                        --->flatdarklist (list of .fits files)
                        --->flatlist (list of .fits files)
                        --->ronchilist (list of .fits files)
                        --->sN*.fits (raw .fits file. Eg sN20100410S0362.fits)
                        --->ronchifile (textfile storing name of raw file)
                        --->shiftfile (textfile storing name of raw shiftfile).
                        --->flatfile (textfile storing name of raw _flat image)
                        --->sflatfile (textile storing name of raw _sflat image)
                        --->sflat_bpmfile (storing name of sflat_bpm.pl)
                    --->grating_or_filter/ (eg, K, H)
                        --->ot_observation_name/ (Science images)
                            --->N*.fits (raw .fits image files)
                            --->objlist (text file of image names. N*\n)
                            --->skylist (text file of image names. N*\n)
                        --->Tellurics/
                            --->ot_observation_name/
                            -->N*.fits (telluric .fits files)
                            --->objtellist (text file matching telluric and science data.
                                            See comments in telSort() for more info.)
                            --->skylist (text file of image names. N*\n)
                            --->tellist (text file of image names. N*\n)

    """

    # Store current working directory for later use.
    path = os.getcwd()

    # Enable optional debugging pauses
    debug = False

    # Set up the logging file
    FORMAT = '%(asctime)s %(message)s'
    DATEFMT = datefmt()
    logging.basicConfig(filename='Nifty.log',format=FORMAT,datefmt=DATEFMT,level=logging.DEBUG)
    log = os.getcwd()+'/Nifty.log'

    logging.info('#################################################')
    logging.info('#                                               #')
    logging.info('# Start the NIFS Baseline Calibration Reduction #')
    logging.info('#                                               #')
    logging.info('#################################################')

    print '\n#################################################'
    print '#                                               #'
    print '# Start the NIFS Baseline Calibration Reduction #'
    print '#                                               #'
    print '#################################################\n'

    # Set up/prepare IRAF
    iraf.gemini()
    iraf.nifs()
    iraf.gnirs()
    iraf.gemtools()

    # Reset to default parameters the used IRAF tasks
    iraf.unlearn(iraf.gemini,iraf.gemtools,iraf.gnirs,iraf.nifs)

    # Prepare the IRAF package for NIFS
    # NSHEADERS lists the header parameters used by the various tasks in the
    # NIFS package (excluding headers values which have values fixed by IRAF or
    # FITS conventions).
    iraf.nsheaders("nifs",logfile=log)

    # Before doing anything involving image display the environment variable
    # stdimage must be set to the correct frame buffer size for the display
    # servers (as described in the dev$graphcap file under the section "STDIMAGE
    # devices") or to the correct image display device. The task GDEVICES is
    # helpful for determining this information for the display servers.
    iraf.set(stdimage='imt2048')

    # Set clobber to 'yes' for the script. This still does not make the gemini
    # tasks overwrite files, so you will likely have to remove files if you
    # re-run the script.
    user_clobber=iraf.envget("clobber")
    iraf.reset(clobber='yes')

    ################################################################################
    # Define Variables, Reduction Lists AND identify/run number of reduction steps #
    ################################################################################

    # Loop over the Calibrations directories and reduce the day calibrations in each one.
    for calpath in calDirList:
        os.chdir(calpath)
        pwdDir = os.getcwd()+"/"
        iraffunctions.chdir(pwdDir)

        # Create lists of each type of calibration from textfiles in Calibrations directory.
        flatlist = open('flatlist', "r").readlines()
        flatdarklist = open("flatdarklist", "r").readlines()
        arcdarklist = open("arcdarklist", "r").readlines()
        arclist = open("arclist", "r").readlines()
        ronchilist = open("ronchilist", "r").readlines()

        # Store the name of the first image of each calibration-type-list in
        # a variable for later use (Eg: calflat). Do this partly because tasks like gemcombine will
        # merge a list of files (Eg: "n"+flatlist) and the output will have the same
        # name as the first file in the list (Eg: calflat).
        calflat = (flatlist[0].strip()).rstrip('.fits')
        flatdark = (flatdarklist[0].strip()).rstrip('.fits')
        arcdark = (arcdarklist[0].strip()).rstrip('.fits')
        arc = (arclist[0].strip()).rstrip('.fits')
        ronchiflat = (ronchilist[0].strip()).rstrip('.fits')

        # Check start and stop values for reduction steps. Ask user for a correction if
        # input is not valid.
        valindex = start
        while valindex > stop  or valindex < 1 or stop > 6:
            print "\nProblem with start/stop step values in nifs_baseline_calibration."
            print "\nSteps 1 to 6 are valid options."
            valindex = int(raw_input("\nPlease enter a valid start value (1 to 6, default 1): "))
            stop = int(raw_input("\nPlease enter a valid stop value (1 to 6, default 6): "))

        # Print the current directory of calibrations being processed
        print "\nCurrently working on calibrations in: \n", calpath

        while valindex <= stop :

            ###########################################################################
            ##  STEP 1: Determine the shift to the MDF (mask definition file)        ##
            ##          using nfprepare (nsoffset). e. g. locate the spectra         ##
            ##  Output: First image in flatlist with "s" prefix                      ##
            ###########################################################################

            if valindex == 1:
                getShift(calflat, over, log)
                print "\nSTEP 1: Determine the shift to the MDF - COMPLETED\n"

            ############################################################################
            ##  STEP 2: Create Flat Field image and BPM (Bad Pixels Mask) image       ##
            ##  Ouput:  Flat Field image with spatial and spectral information        ##
            ##          First image in flatlist with  "rgn" prefix and "_flat" suffix ##
            ############################################################################

            elif valindex == 2:
                makeFlat(flatlist, flatdarklist, calflat, flatdark, over, log)
                print "\nSTEP 2: Create Flat Field image and BPM image - COMPLETED\n"

            ############################################################################
            ##  STEP 3: NFPREPARE and Combine arc darks                                ##
            ############################################################################

            elif valindex == 3:
                makeArcDark(arcdarklist, arcdark, calflat, over, log)
                print "\nSTEP 3: NFPREPARE and Combine arc darks - COMPLETED\n"

            ############################################################################
            ##  STEP 4: NFPREPARE, Combine and flat field arcs                        ##
            ############################################################################
            elif valindex == 4:
                reduceArc(arclist, arc, log, over)
                print "\nSTEP 4: NFPREPARE, Combine and flat field arcs - COMPLETED\n"

            ###########################################################################
            ##  Step 5: Determine the wavelength solution and create the wavelength  ##
            ##          referenced arc                                               ##
            ###########################################################################

            elif valindex == 5:
                wavecal(arc, log, over)
                print "\nStep 5: Determine the wavelength solution and create the wavelenght ref. arc - COMPLETED\n"

            #####################################################################################
            ##  Step 6: Trace the spatial curvature and spectral distortion in the Ronchi flat  #
            #####################################################################################

            elif valindex == 6:
                ronchi(ronchilist, ronchiflat, calflat, over, flatdark, log)
                print "\nStep 6: Trace the spatial curvature and spectral distortion in the Ronchi flat - COMPLETED\n"

            else:
                print "\nERROR in nifs_baseline_calibration: step ", valindex, " is not valid.\n"
                raise SystemExit

            valindex += 1

    # Return to directory script was begun from.
    os.chdir(path)
    return

#####################################################################################
#                                        FUNCTIONS                                  #
#####################################################################################

def getShift(calflat, over, log):
    """Determine the shift to the MDF file.

    Run NFPREPARE on a single "lamps on" flat to  determine  the
    shift  between  your IFU data and the definition of the Image Slicer
    position in the MDF file.  The output from this step  will  be  used
    in all subsequent calls to NFPREPARE as the "shiftimage".

    Args:
        calflat: The first lamps-on flat from flatlist
    """

    # This code structure checks if iraf output files already exist. If output files exist and
    # over (overwrite) is specified, iraf output is overwritten.
    if os.path.exists('s'+calflat+'.fits'):
        if over:
            os.remove('s'+calflat+'.fits')
        else:
            return

    iraf.nfprepare(calflat,rawpath="",outpref="s", shiftx='INDEF', shifty='INDEF',fl_vardq='no',fl_corr='no',fl_nonl='no', logfile=log)

    # Put the name of the reference shift file into a text file called
    # shiftfile to be used by the pipeline later.
    open("shiftfile", "w").write("s"+calflat)

#---------------------------------------------------------------------------------------------------------------------------------------#

def makeFlat(flatlist, flatdarklist, calflat, flatdark, over, log):
    """Make flat and bad pixel mask.

    Use NFPREPARE on the lamps on/lamps off flats to update the
    raw data headers and attach the mask  definition  file  (MDF)  as  a
    binary  table  on all files.  Note that dark frames will not have an
    MDF attached by default.  Instead, the appropriate MDF is  added  in
    NSREDUCE or NSFLAT to match the data being reduced.

    Use  NSREDUCE to cut the calibration (flat/arc) spectra to
    the size specified by the  MDF,  placing  different  IFU  slices  in
    separate image extensions.

    Use  NSFLAT  to generate a normalized flat field (for each
    IFU slice or cross-dispersed order) from lamp flats.  A  mask  (BPM)
    will  also  be  generated by thresholding - this can be used to flag
    bad pixels in other data.

    Use NSSLITFUNCTION to produce the final flat.

    """

    # Update lamps on flat images with offset value and generate variance and data quality extensions
    for image in flatlist:
        image = str(image).strip()
        if os.path.exists('n'+image+'.fits'):
            if over:
                os.remove('n'+image+'.fits')
                iraf.nfprepare(image+'.fits',rawpath='.',shiftim="s"+calflat, fl_vardq='yes',fl_int='yes',fl_corr='no',fl_nonl='no', logfile=log)
            else:
                print "Output exists and -over- not set - skipping nfprepare of lamps on flats"
        else:
            iraf.nfprepare(image+'.fits',rawpath='.',shiftim="s"+calflat, fl_vardq='yes',fl_int='yes',fl_corr='no',fl_nonl='no', logfile=log)
    flatlist = checkLists(flatlist, '.', 'n', '.fits')

    # Update lamps off flat images with offset value and generate variance and data quality extensions
    for image in flatdarklist:
        image = str(image).strip()
        if os.path.exists('n'+image+'.fits'):
            if over:
                iraf.delete('n'+image+'.fits')
                iraf.nfprepare(image+'.fits',rawpath='.',shiftim="s"+calflat, fl_vardq='yes',fl_int='yes',fl_corr='no',fl_nonl='no', logfile=log)
            else:
                print "\nOutput exists and -over- not set - skipping nfprepare of lamps off flats."
        else:
            iraf.nfprepare(image+'.fits',rawpath='.',shiftim="s"+calflat, fl_vardq='yes',fl_int='yes',fl_corr='no',fl_nonl='no', logfile=log)
    flatdarklist = checkLists(flatdarklist, '.', 'n', '.fits')

    # Combine lamps on flat images "n"+image+".fits". Output combined file will have name of the first flat file with "gn" prefix.
    if os.path.exists('gn'+calflat+'.fits'):
        if over:
            iraf.delete("gn"+calflat+".fits")
            iraf.gemcombine(listit(flatlist,"n"),output="gn"+calflat,fl_dqpr='yes', fl_vardq='yes',masktype="none",logfile=log)
        else:
            print "\nOutput exists and -over- not set - skipping gemcombine of lamps on flats."
    else:
        iraf.gemcombine(listit(flatlist,"n"),output="gn"+calflat,fl_dqpr='yes', fl_vardq='yes',masktype="none",logfile=log)

    # Combine lamps off flat images "n"+image+".fits". Output combined file will have name of the first darkflat file with "gn" prefix.
    if os.path.exists('gn'+flatdark+'.fits'):
        if over:
            iraf.delete("gn"+flatdark+".fits")
            iraf.gemcombine(listit(flatdarklist,"n"),output="gn"+flatdark,fl_dqpr='yes', fl_vardq='yes',masktype="none",logfile=log)
        else:
            print "\nOutput exists and -over- not set - skipping gemcombine of lamps off flats."
    else:
        iraf.gemcombine(listit(flatdarklist,"n"),output="gn"+flatdark,fl_dqpr='yes', fl_vardq='yes',masktype="none",logfile=log)

    # NSREDUCE on lamps on flat images "gn"+calflat+".fits" to extract the slices and apply an approximate wavelength calibration.
    if os.path.exists('rgn'+calflat+'.fits'):
        if over:
            iraf.delete("rgn"+calflat+".fits")
            iraf.nsreduce ("gn"+calflat,fl_cut='yes',fl_nsappw='yes',fl_vardq='yes', fl_sky='no',fl_dark='no',fl_flat='no',logfile=log)
        else:
            print "\nOutput exists and -over- not set - skipping nsreduce of lamps on flats."
    else:
        iraf.nsreduce ("gn"+calflat,fl_cut='yes',fl_nsappw='yes',fl_vardq='yes', fl_sky='no',fl_dark='no',fl_flat='no',logfile=log)

    # NSREDUCE on lamps off flat iamges "gn"+flatdark+".fits" to extract the slices and apply an approximate wavelength calibration.
    if os.path.exists('rgn'+flatdark+'.fits'):
        if over:
            iraf.delete("rgn"+flatdark+".fits")
            iraf.nsreduce ("gn"+flatdark,fl_cut='yes',fl_nsappw='yes',fl_vardq='yes', fl_sky='no',fl_dark='no',fl_flat='no',logfile=log)
        else:
            print "\nOutput exists and -over- not set - skipping nsreduce of lamps off flats."
    else:
        iraf.nsreduce ("gn"+flatdark,fl_cut='yes',fl_nsappw='yes',fl_vardq='yes', fl_sky='no',fl_dark='no',fl_flat='no',logfile=log)

    # Create slice-by-slice flat field image and BPM image from the darkflats, using NFLAT.
    # Lower and upper limit of bad pxiels are 0.15 and 1.55.
    if over:
        iraf.delete("rgn"+flatdark+"_dark.fits")
        iraf.delete("rgn"+calflat+"_sflat.fits")
        iraf.delete("rgn"+calflat+"_sflat_bpm.pl")
    iraf.nsflat("rgn"+calflat,darks="rgn"+flatdark,flatfile="rgn"+calflat+"_sflat", darkfile="rgn"+flatdark+"_dark",fl_save_dark='yes',process="fit", thr_flo=0.15,thr_fup=1.55,fl_vardq='yes',logfile=log)

    # Renormalize the slices to account for slice-to-slice variations using NSSLITFUNCTION - make the final flat field image.

    if over:
        iraf.delete("rgn"+calflat+"_flat.fits")
    iraf.nsslitfunction("rgn"+calflat,"rgn"+calflat+"_flat", flat="rgn"+calflat+"_sflat",dark="rgn"+flatdark+"_dark",combine="median", order=3,fl_vary='no',logfile=log)

    # Put the name of the final flat field and bad pixel mask (BPM) into text files of fixed name to be used by the pipeline later.

    open("flatfile", "w").write("rgn"+calflat+"_flat")              # Final flat field
    open("sflatfile", "w").write("rgn"+calflat+"_sflat")            # Flat field before renormalization (before nsslitfunction)
    open("sflat_bpmfile", "w").write("rgn"+calflat+"_sflat_bpm.pl") # BPM

#---------------------------------------------------------------------------------------------------------------------------------------#

def makeArcDark(arcdarklist, arcdark, calflat, over, log):
    """" Prepare with iraf.nfprepare() and combine the daytime arc darks.

    Processing with NFPREPARE will rename the data extension and add
    variance and data quality extensions. By default (see NSHEADERS)
    the extension names are SCI for science data, VAR for variance, and
    DQ for data quality (0 = good). Generation of the data quality
    plane (DQ) is important in order to fix hot and dark pixels on the
    NIFS detector in subsequent steps in the data reduction process.
    Various header keywords (used later) are also added in NFPREPARE.
    NFPREPARE will also add an MDF file (extension MDF) describing the
    NIFS image slicer pattern and how the IFU maps to the sky field.
    """

    # Update arc darks images with offset value and generate variance and data quality extensions.
    for image in arcdarklist:
        image = str(image).strip()
        if over:
            iraf.delete("n"+image+".fits")
        iraf.nfprepare(image, rawpath='./', shiftimage="s"+calflat, bpm="rgn"+calflat+"_sflat_bpm.pl",fl_vardq='yes',fl_corr='no',fl_nonl='no', logfile=log)
    arcdarklist = checkLists(arcdarklist, '.', 'n', '.fits')

    # Combine arc darks images "n"+image+".fits". Output combined file will have the name of the first arc dark file.
    if over:
        iraf.delete("gn"+arcdark+".fits")
    if len(arcdarklist) > 1:
        iraf.gemcombine(listit(arcdarklist,"n"),output="gn"+arcdark, fl_dqpr='yes',fl_vardq='yes',masktype="none",logfile=log)
    else:
        iraf.copy('n'+arcdark+'.fits', 'gn'+arcdark+'.fits')

    # Put the name of the combined and prepared arc dark "gn"+arcdark into a text
    # file called arcdarkfile to be used by the pipeline later.
    open("arcdarkfile", "w").write("gn"+arcdark)

#--------------------------------------------------------------------------------------------------------------------------------#

def reduceArc(arclist, arc, log, over):
    """ Flat field and cut the arc data with iraf.nfprepare() and
    iraf.nsreduce().

    Processing with NFPREPARE will rename the data extension and add
    variance and data quality extensions. By default (see NSHEADERS)
    the extension names are SCI for science data, VAR for variance, and
    DQ for data quality (0 = good). Generation of the data quality
    plane (DQ) is important in order to fix hot and dark pixels on the
    NIFS detector in subsequent steps in the data reduction process.
    Various header keywords (used later) are also added in NFPREPARE.
    NFPREPARE will also add an MDF file (extension MDF) describing the
    NIFS image slicer pattern and how the IFU maps to the sky field.

    NSREDUCE - Process NearIR Spectral data (task resides in the GNIRS
    package)

    NSREDUCE is used for basic reduction of raw data - it provides a
    single, unified interface to several tasks and also allows for
    the subtraction of dark frames and dividing by the flat. For
    NIFS reduction, NSREDUCE is used to call the NSCUT and NSAPPWAVE
    routines.

    """

    # Store the name of the shift image in "shiftima".
    shiftima = open("shiftfile", "r").readlines()[0].strip()
    # Store the name of the bad pixel mask in "sflat_bpm".
    sflat_bpm = open("sflat_bpmfile", "r").readlines()[0].strip()
    # Store the name of the first flat image in flatfile in "flat".
    flat = open("flatfile", "r").readlines()[0].strip()
    # Store the name of the first arc dark image in arcdarkfile in "dark".
    dark = open("arcdarkfile", "r").readlines()[0].strip()

    # Update arc images with offset value and generate variance and data
    # quality extensions. Results in "n"+image+".fits"
    for image in arclist:
        image = str(image).strip()
        if os.path.exists("n"+image+".fits"):
            if over:
                iraf.delete("n"+image+".fits")
            else:
                print "\nOutput file exists and -over not set - skipping nfprepare of arcs."
                continue
        iraf.nfprepare(image, rawpath="", shiftimage=shiftima, fl_vardq="yes", bpm=sflat_bpm, logfile=log)

    # Check that output files for all arc images exists from nfprepare; if output does not
    # exist remove corresponding arc images from arclist.
    arclist = checkLists(arclist, '.', 'n', '.fits')

    # Combine arc images "n"+image+".fits". Output combined file will have the name of the first arc file.
    if len(arclist)>1:
        if os.path.exists("gn"+arc+".fits"):
            if over:
                iraf.delete("gn"+arc+".fits")
                iraf.gemcombine(listit(arclist,"n"),output="gn"+arc,fl_dqpr='yes', fl_vardq='yes',masktype="none",logfile=log)
            else:
                print "\nOutput file exists and -over not set - skipping gemcombine of arcs."
        else:
            iraf.gemcombine(listit(arclist,"n"),output="gn"+arc,fl_dqpr='yes', fl_vardq='yes',masktype="none",logfile=log)

    else:
        if os.path.exists("gn"+arc+".fits"):
            if over:
                iraf.delete("gn"+arc+".fits")
                iraf.copy("n"+arc+".fits", "gn"+arc+".fits")
            else:
                print "Output file exists and -over not set - skipping apply_flat_arc"
        else:
            iraf.copy("n"+arc+".fits", "gn"+arc+".fits")

    # NSREDUCE on arc images "gn"+arc+".fits" to extract the slices and apply an approximate
    # wavelength calibration. Results in "rgn"+image+".fits"
    if os.path.exists("rgn"+arc+".fits"):
        if over:
            iraf.delete("rgn"+arc+".fits")
        else:
            print "Output file exists and -over not set - skipping apply_flat_arc"
            return
    fl_dark = "no"
    if dark != "":
        fl_dark = "yes"
    hdulist = pyfits.open(arc+'.fits')
    if 'K_Long' in hdulist[0].header['GRATING']:
        iraf.nsreduce("gn"+arc, darki=dark, fl_cut="yes", fl_nsappw="yes", crval = 23000., fl_dark="yes", fl_sky="no", fl_flat="yes", flatimage=flat, fl_vardq="no",logfile=log)
    else:
        iraf.nsreduce("gn"+arc, darki=dark, fl_cut="yes", fl_nsappw="yes", fl_dark="yes", fl_sky="no", fl_flat="yes", flatimage=flat, fl_vardq="no",logfile=log)

#--------------------------------------------------------------------------------------------------------------------------------#

def wavecal(arc, log, over):
    """ Determine the wavelength of the observation and set the arc coordinate
    file.

    If the user wishes to change the coordinate file to a different
    one, they need only to change the "clist" variable to their line list
    in the coordli= parameter in the nswavelength call.

    Uses  NSWAVELENGTH to calibrate arc data (after cutting and
    optionally applying a flatfield with NSREDUCE in a previous step).

	###########################################################################
	#  DATA REDUCTION HINT -                                                  #
	# For the nswavelength call, the different wavelength settings            #
	# use different vaues for some of the parameters. For optimal auto        #
	# results, use:                                                           #
	#                                                                         #
	# K-band: thresho=50.0, cradius=8.0   -->  (gives rms of 0.1 to 0.3)      #
	# H-band: thresho=100.0, cradius=8.0  -->  (gives rms of 0.05 to 0.15)    #
	# J-band: thresho=100.0               -->  (gives rms of 0.03 to 0.09)    #
	# Z-band: Currently not working very well for non-interactive mode        #
	#                                                                         #
	# Note that better RMS fits can be obtained by running the wavelength     #
	# calibration interactively and identifying all of the lines              #
	# manually.  Tedious, but will give more accurate results than the        #
	# automatic mode (i.e., fl_inter-).  Use fl_iner+ for manual mode.        #
	#                                                                         #
	###########################################################################

    """

    if os.path.exists("wrgn"+arc+".fits"):
        if over:
            iraf.delete("wrgn"+arc+".fits")
        else:
            print "\nOutput file exists and -over not set - ",\
            "not determining wavelength solution and recreating the wavelength reference arc.\n"
            return

    # Determine the wavelength setting
    hdulist = pyfits.open("rgn"+arc+".fits")
    band = hdulist[0].header['GRATING'][0:1]

    # Variable to set interactive mode. Default False (True for non-standard wavelength configurations ).
    interactive = 'no'

    if band == "Z":
        clist="nifs$data/ArXe_Z.dat"
        my_thresh=100.0
    elif band == "K":
        clist="gnirs$data/argon.dat"
        my_thresh=50.0
    else:
        clist="gnirs$data/argon.dat"
        my_thresh=100.0
        interactive = 'yes'

    # Output : A series of files in a "database/" directory containing the wavelength
    # solutions of each slice. And a reduced arc frame (Eg: wrgnARC.fits).
    iraf.nswavelength("rgn"+arc, coordli=clist, nsum=10, thresho=my_thresh, trace='yes', fwidth=2.0, match=-6,cradius=8.0,fl_inter=interactive,nfound=10,nlost=10,logfile=log)

#--------------------------------------------------------------------------------------------------------------------------------#

def ronchi(ronchilist, ronchiflat, calflat, over, flatdark, log):
    """Spacial rectification. Combine arc darks. Calls iraf.nfsdist().

    NFSDIST - Establish a spatial calibration

    NFSDIST uses the information in the "Ronchi" Calibration images
    to calibrate the spatial dimension of the NIFS IFU field. The
    Ronchi frame is a dispersed flat field image with a slit-mask
    in the field so that the illumination on the IFU is in a
    pattern of ~10 different slitlets that are stackedin the
    y-dimension on the field. Proper alignment of the slits across
    the image slicer pattern can be used for spatial rectification
    of the on-sky science data. The spatial solution determined by
    NFSDIST is linked to the science data in NFFITCOORDS.
    """

    # Update ronchi flat images with offset value and generate variance and data quality extensions.
    for image in ronchilist:
        image = str(image).strip()
        if over:
            iraf.delete("n"+image+'.fits')
        iraf.nfprepare(image,rawpath="", shiftimage="s"+calflat, bpm="rgn"+calflat+"_sflat_bpm.pl", fl_vardq="yes",fl_corr="no",fl_nonl="no", logfile=log)
    ronchilist = checkLists(ronchilist, '.', 'n', '.fits')

    # Combine ronchi flat images "n"+image+".fits". Output combined file will
    # have the name of the first ronchi flat file.
    if over:
        iraf.delete("gn"+ronchiflat+".fits")
    if len(ronchilist) > 1:
        iraf.gemcombine(listit(ronchilist,"n"),output="gn"+ronchiflat,fl_dqpr="yes", masktype="none",fl_vardq="yes",logfile=log)
    else:
        iraf.copy("n"+ronchiflat+".fits","gn"+ronchiflat+".fits")

    # NSREDUCE on ronchi "gn"+ronchi+".fits" to extract the slices and apply an approximate wavelength calibration.
    if over:
        iraf.delete("rgn"+ronchiflat+".fits")
    iraf.nsreduce("gn"+ronchiflat, outpref="r",dark="rgn"+flatdark+"_dark", flatimage="rgn"+calflat+"_flat",fl_cut="yes", fl_nsappw="yes",fl_flat="yes", fl_sky="no", fl_dark="yes", fl_vardq="no", logfile=log)

    if over:
        iraf.delete("brgn"+ronchiflat+".fits")

    # Determine the spatial distortion correction.

    iraf.nfsdist("rgn"+ronchiflat,fwidth=6.0, cradius=8.0, glshift=2.8, minsep=6.5, thresh=2000.0, nlost=3, fl_inter='no',logfile=log)

    # Put the name of the spatially referenced ronchi flat "rgn"+ronchiflat into a
    # text file called ronchifile to be used by the pipeline later. Also associated files
    # are in the "database/" directory.

    open("ronchifile", "w").write("rgn"+ronchiflat)

#---------------------------------------------------------------------------------------------------------------------------------------#

if __name__ == '__main__':
    print "nifs_baseline_calibration"
