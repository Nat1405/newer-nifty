# -*- coding: utf-8 -*-

import sys
import glob
import shutil
import getopt
import os
import time
import logging
import pexpect as p
from pyraf import iraf
iraf.gemini()
iraf.nifs()
iraf.gnirs()
iraf.gemtools()
from pyraf import iraffunctions
import pyfits
from nifsDefs import datefmt, listit, writeList, checkLists, writeCenters, makeSkyList, MEFarith
from nifsTelluric import extrap1d, readCube, readSpec, telCor

#--------------------------------------------------------------------#
#                                                                    #
#     SCIENCE                                                        #
#                                                                    #
#     This module contains all the functions needed to reduce        #
#     the NIFS science images.                                       #
#                                                                    #
#    COMMAND LINE OPTIONS                                            #
#    If you wish to skip this script for science data                #
#    enter -n in the command line                                    #
#    If you wish to skip this script for telluric data               #
#    enter -k in the command line                                    #
#    Specify a start value with -b (default is 1)                    #
#    Specify a stop value with -x (default is 9)                     #
#                                                                    #
#     INPUT:                                                         #
#     + Raw files                                                    #
#       - Science frames                                             #
#       - Sky frames                                                 #
#       - Reference file                                             #
#       - Bad Pixel Mask                                             #
#       - Flat field                                                 #
#       - Reduced arc frame                                          #
#       - Reduced ronchi mask                                        #
#                                                                    #
#     OUTPUT:                                                        #
#     - Reduced science frame: data cube. (ie c(a)tfbrgnSCI.fits)    #
#                                                                    #
#--------------------------------------------------------------------#

def start(obsDirList, calDirList, start, stop, tel, telinter, over):
    """
    #--------------------------------------------------------------------#
    #                                                                    #
    #     SCIENCE                                                        #
    #                                                                    #
    #     This module contains all the functions needed to reduce        #
    #     the NIFS science images.                                       #
    #                                                                    #
    #    COMMAND LINE OPTIONS                                            #
    #    If you wish to skip this script for science data                #
    #    enter -n in the command line                                    #
    #    If you wish to skip this script for telluric data               #
    #    enter -k in the command line                                    #
    #    Specify a start value with -b (default is 1)                    #
    #    Specify a stop value with -x (default is 9)                     #
    #                                                                    #
    #     INPUT:                                                         #
    #     + Raw files                                                    #
    #       - Science frames                                             #
    #       - Sky frames                                                 #
    #       - Reference file                                             #
    #       - Bad Pixel Mask                                             #
    #       - Flat field                                                 #
    #       - Reduced arc frame                                          #
    #       - Reduced ronchi mask                                        #
    #                                                                    #
    #     OUTPUT:                                                        #
    #     - Reduced science frame: data cube. (ie c(a)tfbrgnSCI.fits)    #
    #                                                                    #
    #--------------------------------------------------------------------#

    Args:
        telDirList: [‘path/obj/date/grat/Tellurics/obsid’]
        calDirList: [‘path/obj/date/Calibrations’]
        tel (bool): Perform telluric correction. Default True.
        telinter (bool): Perform an interactive Telluric Correction. Default True.

    """
    path = os.getcwd()

    # set up log
    FORMAT = '%(asctime)s %(message)s'
    DATEFMT = datefmt()
    logging.basicConfig(filename='main.log',format=FORMAT,datefmt=DATEFMT,level=logging.DEBUG)
    log = os.getcwd()+'/main.log'


    # loops through all the observation directories to perform the science reduction on each one
    for obsDir in obsDirList:
        os.chdir(obsDir)
        tempObs = obsDir.split(os.sep)

        # finds the Calibrations directory that corresponds to the science observation date
        for calDir in calDirList:
            tempCal = calDir.split(os.sep)
            if tempObs[-3]==tempCal[-2]:
                calDir = calDir+'/'
                break
            elif tempObs[-4]==tempCal[-2]:
                calDir = calDir+'/'
                break

        obsid = tempObs[-1]

        # reset iraf tasks
        iraf.unlearn(iraf.gemini,iraf.gemtools,iraf.gnirs,iraf.nifs,iraf.imcopy)

        iraf.set(stdimage='imt2048')

        # change the iraf directory to the current directory
        pwd = os.getcwd()
        iraffunctions.chdir(pwd)
        iraf.nsheaders("nifs",logfile=log)

        # define all the necessary variables and lists for the calibration and science images
        shift = calDir+str(open(calDir+"shiftfile", "r").readlines()[0]).strip()
        flat = calDir+str(open(calDir+"flatfile", "r").readlines()[0]).strip()
        ronchi = open(calDir+"ronchifile", "r").readlines()[0].strip()
        iraf.copy(calDir+ronchi+".fits",output="./")
        sflat_bpm = calDir+str(open(calDir+"sflat_bpmfile", "r").readlines()[0]).strip()
        arcdark = calDir+str(open(calDir+"arcdarkfile", "r").readlines()[0]).strip()

        # copy wavelength calibrated arc to obsDir
        arc = "wrgn"+str(open(calDir+"arclist", "r").readlines()[0]).strip()
        iraf.copy(calDir+arc+".fits",output="./")

        # determines whether the data is science or telluric
        if tempObs[-2]=='Tellurics':
            kind = 'Telluric'
            objlist = open('tellist', 'r').readlines()
            objlist = [image.strip() for image in objlist]
            try:
                skylist = open("skylist", "r").readlines()
                skylist = [image.strip() for image in skylist]
            except:
                print "\nNo sky images were found for standard star. Please make a skylist in the telluric directory\n"
                raise SystemExit
            sky = skylist[0]
        else:
            kind = 'Object'
            objlist = open("objlist", "r").readlines()
            objlist = [image.strip() for image in objlist]
            skylist = open("skylist", "r").readlines()
            skylist = [image.strip() for image in skylist]
            sky = skylist[0]
            # check to see if the number of sky images matches the number of science images and if not duplicates sky images and rewrites the sky file and skylist
        if not len(skylist)==len(objlist):
            skylist = makeSkyList(skylist, objlist, obsDir)

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

        #=========================================================
        # Start main processing steps. Do this within a while loop
        # to allow the use of start and stop positions
        #=========================================================

        logging.info('############################')
        logging.info('                            ')
        logging.info('   Reducing Observations    ')
        logging.info('                            ')
        logging.info('############################')

        print '############################'
        print '                            '
        print '   Reducing Observations    '
        print '                            '
        print '############################'


        valindex = start
        if valindex > stop  or valindex < 1 or stop > 9:
            print "problem with start/stop values"
        while valindex <= stop :

            ####################
            ## Prepare raw data ->n
            logging.info('Prepare raw data ->n')
            if valindex == 1:
                objlist = prepare(objlist, shift, sflat_bpm, log, over)
                skylist = prepare(skylist, shift, sflat_bpm, log, over)

            #####################
            ## Combine multiple frames ->gn
            elif valindex == 2:
                if kind=='Object':
                    logging.info('Combine multiple frames ->gn')
                    if len(skylist)>1:
                        combineImages(skylist, "gn"+sky, log, over)
                    else:
                        copyImage(skylist, 'gn'+sky+'.fits', over)
                else:
                    pass

            ##################
            ## Sky Subtraction ->gn
            elif valindex == 3:
                skySubtractObj(objlist, skylist, log, over)
                logging.info('Sky Subtraction ->gn')

            #################
            ## Flat field ->rgn
            elif valindex == 4:
                applyFlat(objlist, flat, log, over, kind)
                logging.info('Flat field ->rgn')

            #################
            ## Correct bad pixels ->brgn
            elif valindex == 5:
                fixBad(objlist, log, over)
                logging.info('Correct bad pixels ->brgn')

            #################
            ## Derive 2D->3D transformation ->fbrgn
            elif valindex == 6:
                fitCoords(objlist, arc, ronchi, log, over, kind)
                logging.info('Derive 2D->3D transformation ->fbrgn')

            #################
            ## Apply transformation ->tfbrgn
            elif valindex == 7:
                transform(objlist, log, over)
                logging.info('Apply transformation ->tfbrgn')

            #################
            ## Derive or apply telluric correction ->atfbrgn
            elif valindex == 8:
                logging.info('Derive or apply telluric correction ->atfbrgn')
                if kind=='Telluric':
                    makeTelluric(objlist, log, over)
                elif kind=='Object' and tel and telinter=='no':
                    makeCube('tfbrgn', objlist, False, obsDir, log, over)
                    applyTelluric(objlist, obsid, skylist, telinter, log, over)
                elif kind=='Object' and tel and telinter=='yes':
                    applyTelluric(objlist, obsid, skylist, telinter, log, over)

            #################
            ## Create a 3D cube -> catfbrgn
            elif valindex == 9:
                if kind == "Telluric":
                   print "No cube being made for tellurics"
                elif telinter=='yes' and kind=='Object' and tel:
                    logging.info('Create a 3D cube -> catfbrgn')
                    makeCube('atfbrgn', objlist, tel, obsDir, log, over)
                elif kind=='Object' and not tel and telinter=='yes':
                    logging.info('Create a 3D cube -> ctfbrgn')
                    makeCube('tfbrgn', objlist, tel, obsDir, log, over)

            valindex += 1

    os.chdir(path)
    return

##################################################################################################################
#                                                     FUNCTIONS                                                 #
##################################################################################################################

def prepare(inlist, shiftima, sflat_bpm, log, over):
    """Prepare list of images using iraf.nfprepare. Output: -->n.

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

    for image in inlist:
        if os.path.exists("n"+image+".fits"):
            if over:
                os.remove("n"+image+".fits")
            else:
                print "Output file exists and -over not set - skipping prepare_list"
                continue
        iraf.nfprepare(image, rawpath="", shiftimage=shiftima, fl_vardq="yes", bpm=sflat_bpm, logfile=log)
    inlist = checkLists(inlist, '.', 'n', '.fits')
    return inlist


#--------------------------------------------------------------------------------------------------------------------------------#

def combineImages(inlist, out, log, over):
    """Gemcombine multiple frames. Output: -->gn."""
    print inlist
    if os.path.exists(out+".fits"):
        if over:
            iraf.delete(out+".fits")
        else:
            print "Output file exists and -over not set - skipping combine_ima"
            return
    iraf.gemcombine(listit(inlist,"n"),output=out,fl_dqpr='yes', fl_vardq='yes',masktype="none",logfile=log)

#--------------------------------------------------------------------------------------------------------------------------------#

def copyImage(input, output, over):
    """Copy an image (used to add the correct prefix)."""

    if os.path.exists(output):
        if over:
            iraf.delete(output)
        else:
            print "Output file exists and -over not set - skipping copy_ima"
            return
    iraf.copy('n'+input[0]+'.fits', output)

#--------------------------------------------------------------------------------------------------------------------------------#

def skySubtractObj(objlist, skylist, log, over):
    """"Sky subtraction for science using iraf.gemarith(). Output: -->gn"""

    for i in range(len(objlist)):
        image = str(objlist[i])
        sky = str(skylist[i])
        if os.path.exists("gn"+image+".fits"):
           if over:
               os.remove("gn"+image+".fits")
           else:
               print "Output file exists and -over not set - skipping skysub_list"
               continue
        iraf.gemarith ("n"+image, "-", "n"+sky, "gn"+image, fl_vardq="yes", logfile=log)

#--------------------------------------------------------------------------------------------------------------------------------#

def skySubtractTel(tellist, sky, log, over):
    """ sky subtraction for telluric"""

    for image in tellist:
        if os.path.exists("gn"+image+".fits"):
            if over:
                os.remove("gn"+image+".fits")
            else:
                print "Output file exists and -over not set - skipping skysub_list"
                continue
        iraf.gemarith ("n"+image, "-", sky, "gn"+image, fl_vardq="yes", logfile=log)

#--------------------------------------------------------------------------------------------------------------------------------#

def applyFlat(objlist, flat, log, over, kind, dark=""):
    """Flat field and cut the data with iraf.nsreduce(). Output: -->rgn.

    NSREDUCE - Process NearIR Spectral data (task resides in the GNIRS
    package)

    NSREDUCE is used for basic reduction of raw data - it provides a
    single, unified interface to several tasks and also allows for
    the subtraction of dark frames and dividing by the flat. For
    NIFS reduction, NSREDUCE is used to call the NSCUT and NSAPPWAVE
    routines.

    """

    fl_dark = "no"
    if dark != "":
        fl_dark = "yes"

    for image in objlist:
        image = str(image).strip()
        if os.path.exists("rgn"+image+".fits"):
            if over:
                os.remove("rgn"+image+".fits")
            else:
                print "Output file exists and -over not set - skipping apply_flat_list"
                continue
        if kind == 'Object':
            iraf.nsreduce("gn"+image, fl_cut="yes", fl_nsappw="yes", fl_dark="no", fl_sky="no", fl_flat="yes", flatimage=flat, fl_vardq="yes",logfile=log)
        elif kind == "Telluric":
            iraf.nsreduce("gn"+image, darki=dark, fl_cut="yes", fl_nsappw="no", fl_dark=fl_dark, fl_sky="no", fl_flat="yes", flatimage=flat, fl_vardq="yes",logfile=log)

#--------------------------------------------------------------------------------------------------------------------------------#

def fixBad(objlist, log, over):
    """Interpolate over bad pixels flagged in the DQ plane with iraf.nffixbad(). Output: -->brgn.

    NFFIXBAD - Fix Hot/Cold pixels on the NIFS detector

    This routine uses the information in the Data Quality
    extensions to fix hot and cold pixels in the NIFS science
    fields. NFFIXBAD is a wrapper script which calls the task
    FIXPIX, using the DQ plane to define the pixels to be corrected.

    """

    for image in objlist:
        image = str(image).strip()
        if os.path.exists("brgn"+image+".fits"):
            if over:
                os.remove("brgn"+image+".fits")
            else:
                print "Output file exists and -over not set - skipping fixbad_list"
                continue
        iraf.nffixbad("rgn"+image,logfile=log)

#--------------------------------------------------------------------------------------------------------------------------------#

def fitCoords(objlist, arc, sflat, log, over, kind):
    """ Derive the 2D to 3D spatial/spectral transformation with iraf.nsfitcoords().
    Output: -->fbrgn

    """

    for image in objlist:
        image = str(image).strip()
        if os.path.exists("fbrgn"+image+".fits"):
            if over:
                os.remove("fbrgn"+image+".fits")
            else:
                print "Output file exists and -over not set - skipping fitcoord_list"
                continue
        if kind=='Object':
            iraf.nsfitcoords("brgn"+image,lamptransf=arc, sdisttransf=sflat,logfile=log)
        elif kind=='Telluric':
            iraf.nsfitcoords("brgn"+image, fl_int='no', lamptransf=arc, sdisttransf=sflat, lxorder=4, syorder=4, logfile=log)

#--------------------------------------------------------------------------------------------------------------------------------#

def transform(objlist, log, over):
    """Apply the transformation determined in the iraf.nffitcoords() step with
    iraf.nstransform(). Output: -->tfbrgn

    NSTRANSFORM - Spatially rectify and wavelength calibrate data.

    NFTRANSFORM applies the wavelength solution found by
    NSWAVELENGTH and the spatial correction found by NFSDIST,
    aligning all the IFU extensions consistently onto a common
    coordinate system. The output of this routine is still in 2D
    format, with each of the IFU slices represented by its own data
    extension.

    """

    for image in objlist:
        image = str(image).strip()
        if os.path.exists("tfbrgn"+image+".fits"):
            if over:
                iraf.delete("tfbrgn"+image+".fits")
            else:
                print "Output file exists and -over not set - skipping transform_list"
                continue
        iraf.nstransform("fbrgn"+image, logfile=log)

#--------------------------------------------------------------------------------------------------------------------------------#

def makeTelluric(objlist, log, over):
    """ Extracts 1-D spectra with iraf.nfextract() and combines them with iraf.gemcombine().
    iraf.nfextract() is currently only done interactively. Output: -->atfbrgn

    NFEXTRACT - Extract NIFS spectra.

    This could be used to extract a 1D spectra from IFU data and is
    particularly useful for extracting the bright spectra of
    telluric calibrator stars. Note that this routine only works
    on data that has been run through NFTRANSFORM.
    """

    for image in objlist:
        image = str(image).strip()
        if os.path.exists("xtfbrgn"+image+".fits"):
            if over:
                iraf.delete("xtfbrgn"+image+".fits")
            else:
                print "Output file exists and -over not set - skipping extraction in make_telluric"
                continue
        diam = 0.5

        iraf.nfextract("tfbrgn"+image, outpref="x", diameter=diam, fl_int='yes', logfile=log)


    #combine all the 1D spectra to one final output file
    telluric = str(objlist[0]).strip()
    if os.path.exists("gxtfbrgn"+telluric+".fits"):
        if over:
            iraf.delete("gxtfbrgn"+telluric+".fits")
        else:
            print "Output file exists and -over not set - skipping gemcombine in make_telluric"
            return
    iraf.gemcombine(listit(objlist,"xtfbrgn"),output="gxtfbrgn"+telluric, statsec="[*]", combine="median",logfile=log,masktype="none",fl_vardq="yes")

    # Write the name of the final file to a standard file in the telluric directory
    open("telluricfile", "w").write("gxtfbrgn"+telluric)

#--------------------------------------------------------------------------------------------------------------------------------#

def applyTelluric(objlist, obsid, skylist, telinter, log, over):
    """ Corrects the data for telluric absorption features with iraf.nftelluric().
    iraf.nftelluric() is currently only run interactively. Output: -->atfbrgn

    NFTELLURIC

    NFTELLURIC uses input science and a 1D spectrum of a telluric
    calibrator to correct atmospheric absorption features.
    """

    obsDir = os.getcwd()
    os.chdir('../Tellurics')
    telDirList = glob.glob('*')

    if telinter=='no':
        telCor(obsDir, telDirList, over)
    else:
        for telDir in telDirList:
            if 'obs' in telDir:
                os.chdir(telDir)
                if os.path.exists('objtellist'):
                    objtellist = open("objtellist", "r").readlines()
                    objlist = [image.strip() for image in objtellist]
                else:
                    os.chdir('..')
                    continue
                try:
                    telluric = str(open('corrtellfile', 'r').readlines()[0]).strip()
                except:
                    print "No telluric spectrum found in ", telDir
                    os.chdir('..')
                    continue
                shutil.copy(telluric+'.fits', obsDir)

                '''
                continuum = str(open('continuumfile', 'r').readlines()[0]).strip()
                bblist = open('blackbodyfile', 'r').readlines()
                bblist = [image.strip() for image in bblist]
                '''

                os.chdir(obsDir)
                iraffunctions.chdir(obsDir)
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
                            objheader = pyfits.open(obsDir+'/'+objlist[i]+'.fits')
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

def makeCube(pre, objlist, tel, obsDir, log, over):
    """ Reformat the data into a 3-D datacube using iraf.nifcube(). Output: If
    telluric correction to be applied, -->catfbrgn. Else, -->ctfbrgn.

    NIFCUBE - Construct 3D NIFS datacubes.

    NIFCUBE takes input from data output by either NFFITCOORDS or
    NFTRANSFORM and converts the 2D data images into data cubes
    that have coordinates of x, y, lambda.

    """

    os.chdir(obsDir)
    for image in objlist:
        if os.path.exists("c"+pre+image+".fits"):
            if over:
                iraf.delete("c"+pre+image+".fits")
            else:
                print "Output file exists and -over not set - skipping make_cube_list"
                continue
        if tel:
            iraf.nifcube (pre+image, outcubes = 'c'+pre+image, logfile=log)
            hdulist = pyfits.open('c'+pre+image+'.fits', mode = 'update')
#            hdulist.info()
            exptime = hdulist[0].header['EXPTIME']
            cube = hdulist[1].data
            gain = 2.8
            cube_calib = cube / (exptime * gain)
            hdulist[1].data = cube_calib
            hdulist.flush()
        else:
            iraf.nifcube (pre+image, outcubes = 'c'+pre+image, logfile=log)

#--------------------------------------------------------------------------------------------------------------------------------#
