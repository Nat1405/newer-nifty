import logging
from pyraf import iraf
iraf.gemini()
iraf.nifs()
iraf.gnirs()
iraf.gemtools()
from pyraf import iraffunctions
import pyfits
import logging, os
from nifsDefs import datefmt, listit, checkLists

#--------------------------------------------------------------------#
#                                                                    #
#     REDUCE                                                         #
#                                                                    #
#     This module contains all the functions needed to reduce        #
#     the NIFS calibrations (reducing the images is done in the      #
#     science reduction scripts). The reduction steps were made      #
#     according to                                                   #
#                                                                    #
#   http://www.gemini.edu/sciops/instruments/nifs/NIFS_Basecalib.py  #
#                                                                    #
#     COMMAND LINE OPTIONS                                           #
#     If you wish to skip this step enter -r in the command line     #
#     Specify a start value with -a (default is 1)                   #
#     Specify a stop value with -z (default is 6)                    #
#                                                                    #
#     INPUT:                                                         #
#     + Raw files                                                    #
#       - Flats (lamps on)                                           #
#       - Flats (lamps off)                                          #
#       - Arcs                                                       #
#       - Darks                                                      #
#       - Ronchi masks                                               #
#                                                                    #
#     OUTPUT:                                                        #
#     - Shift file. (ie sCALFLAT.fits)                               #
#     - Bad Pixel Mask. (ie rgnCALFLAT_sflat_bmp.pl)                 #
#     - Flat field. (ie rgnCALFLAT_flat.fits)                        #
#     - Reduced arc frame. (ie wrgnARC.fits)                         #
#     - Reduced ronchi mask. (ie. rgnRONCHI.fits)                    #
#     - Reduced dark frame. (ie. rgnARCDARK.fits)                    #
#                                                                    #
#--------------------------------------------------------------------#

def start(obsDirList, calDirList, over, start, stop):

    # Set up the logging file
    FORMAT = '%(asctime)s %(message)s'
    DATEFMT = datefmt()
    logging.basicConfig(filename='main.log',format=FORMAT,datefmt=DATEFMT,level=logging.DEBUG)
    log = os.getcwd()+'/main.log'

    logging.info('###############################')
    logging.info('#                             #')
    logging.info('# Start Calibration Reduction #')
    logging.info('#                             #')
    logging.info('###############################')
    
    print '###############################'
    print '#                             #'
    print '# Start Calibration Reduction #'
    print '#                             #'
    print '###############################'
    
    # Unlearn the used tasks
    iraf.unlearn(iraf.gemini,iraf.gemtools,iraf.gnirs,iraf.nifs)
    
    # Prepare the package for NIFS
    iraf.nsheaders("nifs",logfile=log)

    iraf.set(stdimage='imt2048')
    user_clobber=iraf.envget("clobber")
    iraf.reset(clobber='yes')

    path = os.getcwd()

    # loop over the Calibrations directories and reduce the day cals in each one
    for calpath in calDirList:
        os.chdir(calpath)
        pwdDir = os.getcwd()+"/"
        iraffunctions.chdir(pwdDir)

        # define the cals lists and images
        flatlist = open('flatlist', "r").readlines()
        flatdarklist = open("flatdarklist", "r").readlines()
        arcdarklist = open("arcdarklist", "r").readlines()
        arclist = open("arclist", "r").readlines()
        ronchilist = open("ronchilist", "r").readlines()
    
        calflat = (flatlist[0].strip()).rstrip('.fits')
        flatdark = (flatdarklist[0].strip()).rstrip('.fits')
        arcdark = (arcdarklist[0].strip()).rstrip('.fits')
        arc = (arclist[0].strip()).rstrip('.fits')
        ronchiflat = (ronchilist[0].strip()).rstrip('.fits')

        # check start and stop values for reduction steps
        valindex = start
        if valindex > stop  or valindex < 1 or stop > 6:
            print "problem with start/stop values"
            print(valindex,start,stop)
        while valindex <= stop :

            ####################
            ## Prepare raw data
        
            if valindex == 1:
                getShift(calflat, over, log)    

            ####################
            ## Make flat

            elif valindex == 2:
                makeFlat(flatlist, flatdarklist, calflat, flatdark, over, log)
            
            ####################
            ## Combine arc darks

            elif valindex == 3:
                makeArcDark(arcdarklist, arcdark, calflat, over, log)

            ####################
            ##  Combine and flat field arcs

            elif valindex == 4:
                reduceArc(arclist, arc, log, over)

            ####################
            ##  Determine the wavelength of the observation and set the arc coordinate file

            elif valindex == 5:
                wavecal("rgn"+arc, log, over)
                
            ####################
            ## Combine arc darks

            elif valindex == 6:
                ronchi(ronchilist, ronchiflat, calflat, over, flatdark, log)
            else:
                print "No step associated to this value"
                
            valindex += 1
    os.chdir(path)
    return

#####################################################################################
#                                        FUNCTIONS                                  #
#####################################################################################

def getShift(calflat, over, log):
    # Determine the shift to the MDF file

    if os.path.exists('s'+calflat+'.fits'):
        if over:
            os.remove('s'+calflat+'.fits')
        else:
            return
    iraf.nfprepare(calflat,rawpath="",outpref="s", shiftx='INDEF', shifty='INDEF',fl_vardq='no',fl_corr='no',fl_nonl='no', logfile=log)
        
    open("shiftfile", "w").write("s"+calflat)

#---------------------------------------------------------------------------------------------------------------------------------------#

def makeFlat(flatlist, flatdarklist, calflat, flatdark, over, log):
    # make flat and bad pixel mask
    
    for image in flatlist:
        image = str(image).strip()
        if os.path.exists('n'+image+'.fits'):
            if over:
                os.remove('n'+image+'.fits')
                iraf.nfprepare(image+'.fits',rawpath='.',shiftim="s"+calflat, fl_vardq='yes',fl_int='yes',fl_corr='no',fl_nonl='no', logfile=log)
            else:
                print "Output exists and -over- not set - skipping nfprepare of flats"
        else:
            iraf.nfprepare(image+'.fits',rawpath='.',shiftim="s"+calflat, fl_vardq='yes',fl_int='yes',fl_corr='no',fl_nonl='no', logfile=log)
    flatlist = checkLists(flatlist, '.', 'n', '.fits')

    for image in flatdarklist:
        image = str(image).strip()
        if os.path.exists('n'+image+'.fits'):
            if over:
                iraf.delete('n'+image+'.fits')
                iraf.nfprepare(image+'.fits',rawpath='.',shiftim="s"+calflat, fl_vardq='yes',fl_int='yes',fl_corr='no',fl_nonl='no', logfile=log)
            else:
                print "Output exists and -over- not set - skipping nfprepare of flatdarks"
        else:
            iraf.nfprepare(image+'.fits',rawpath='.',shiftim="s"+calflat, fl_vardq='yes',fl_int='yes',fl_corr='no',fl_nonl='no', logfile=log)
    flatdarklist = checkLists(flatdarklist, '.', 'n', '.fits')

    if os.path.exists('gn'+calflat+'.fits'):    
        if over:
            iraf.delete("gn"+calflat+".fits")
            iraf.gemcombine(listit(flatlist,"n"),output="gn"+calflat,fl_dqpr='yes', fl_vardq='yes',masktype="none",logfile=log)
        else:
            print "Output exists and -over- not set - skipping gemcombine of flats"
    else:
        iraf.gemcombine(listit(flatlist,"n"),output="gn"+calflat,fl_dqpr='yes', fl_vardq='yes',masktype="none",logfile=log)

    if os.path.exists('gn'+flatdark+'.fits'):
        if over:
            iraf.delete("gn"+flatdark+".fits")
            iraf.gemcombine(listit(flatdarklist,"n"),output="gn"+flatdark,fl_dqpr='yes', fl_vardq='yes',masktype="none",logfile=log)
        else:
            print "Output exists and -over- not set - skipping gemcombine of flatdarks"
    else:
        iraf.gemcombine(listit(flatdarklist,"n"),output="gn"+flatdark,fl_dqpr='yes', fl_vardq='yes',masktype="none",logfile=log)

    if os.path.exists('rgn'+calflat+'.fits'):
        if over:
            iraf.delete("rgn"+calflat+".fits")
            iraf.nsreduce ("gn"+calflat,fl_cut='yes',fl_nsappw='yes',fl_vardq='yes', fl_sky='no',fl_dark='no',fl_flat='no',logfile=log)
        else:
            print "Output exists and -over- not set - skipping"
    else:
        iraf.nsreduce ("gn"+calflat,fl_cut='yes',fl_nsappw='yes',fl_vardq='yes', fl_sky='no',fl_dark='no',fl_flat='no',logfile=log)

    if over:
        iraf.delete("rgn"+flatdark+".fits")
    iraf.nsreduce ("gn"+flatdark,fl_cut='yes',fl_nsappw='yes',fl_vardq='yes', fl_sky='no',fl_dark='no',fl_flat='no',logfile=log)


    if over:
        iraf.delete("rgn"+flatdark+"_dark.fits")
        iraf.delete("rgn"+calflat+"_sflat.fits")
        iraf.delete("rgn"+calflat+"_sflat_bpm.pl")
    iraf.nsflat("rgn"+calflat,darks="rgn"+flatdark,flatfile="rgn"+calflat+"_sflat", darkfile="rgn"+flatdark+"_dark",fl_save_dark='yes',process="fit", thr_flo=0.15,thr_fup=1.55,fl_vardq='yes',logfile=log) 
        
    #rectify the flat for slit function differences - make the final flat.

    if over:
        iraf.delete("rgn"+calflat+"_flat.fits")
    iraf.nsslitfunction("rgn"+calflat,"rgn"+calflat+"_flat", flat="rgn"+calflat+"_sflat",dark="rgn"+flatdark+"_dark",combine="median", order=3,fl_vary='no',logfile=log)


    # Put the name of the distortion file into a file of fixed name to be used by the pipeline

    open("flatfile", "w").write("rgn"+calflat+"_flat")
    open("sflatfile", "w").write("rgn"+calflat+"_sflat")
    open("sflat_bpmfile", "w").write("rgn"+calflat+"_sflat_bpm.pl")
#---------------------------------------------------------------------------------------------------------------------------------------#
    
def makeArcDark(arcdarklist, arcdark, calflat, over, log):
    # combine the daytime arc darks
    for image in arcdarklist:
        image = str(image).strip()
        if over:
            iraf.delete("n"+image+".fits")
        iraf.nfprepare(image, rawpath='./', shiftimage="s"+calflat, bpm="rgn"+calflat+"_sflat_bpm.pl",fl_vardq='yes',fl_corr='no',fl_nonl='no', logfile=log)
    arcdarklist = checkLists(arcdarklist, '.', 'n', '.fits')
    
    if over:
        iraf.delete("gn"+arcdark+".fits")
    if len(arcdarklist) > 1:
        iraf.gemcombine(listit(arcdarklist,"n"),output="gn"+arcdark, fl_dqpr='yes',fl_vardq='yes',masktype="none",logfile=log)
    else:
        iraf.copy('n'+arcdark+'.fits', 'gn'+arcdark+'.fits')

    open("arcdarkfile", "w").write("gn"+arcdark)
    
#--------------------------------------------------------------------------------------------------------------------------------#

def reduceArc(arclist, arc, log, over):
    # flat field and cut the arc data

    shiftima = open("shiftfile", "r").readlines()[0].strip()
    sflat_bpm = open("sflat_bpmfile", "r").readlines()[0].strip()
    flat = open("flatfile", "r").readlines()[0].strip()
    dark = open("arcdarkfile", "r").readlines()[0].strip()
    
    for image in arclist:
        image = str(image).strip()
        if os.path.exists("n"+image+".fits"):
            if over:
                iraf.delete("n"+image+".fits")
            else:
                print "Output file exists and -over not set - skipping combine_ima"
                return
        iraf.nfprepare(image, rawpath="", shiftimage=shiftima, fl_vardq="yes", bpm=sflat_bpm, logfile=log)
        
        if os.path.exists("gn"+image+".fits"):
            if over:
                iraf.delete("gn"+image+".fits")
            else:
                print "Output file exists and -over not set - skipping apply_flat_arc"
                return
    arclist = checkLists(arclist, '.', 'n', '.fits')
            
    if len(arclist)>1:
        iraf.gemcombine(listit(arclist,"n"),output="gn"+arc,fl_dqpr='yes', fl_vardq='yes',masktype="none",logfile=log)
    else:
        iraf.copy("n"+arc+".fits", "gn"+arc+".fits")
        
    if os.path.exists("rgn"+image+".fits"):
        if over:
            iraf.delete("rgn"+image+".fits")
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
    # Determine the wavelength of the observation and set the arc coordinate
    # file.  If the user wishes to change the coordinate file to a different
    # one, they need only to change the "clist" variable to their line list
    # in the coordli= parameter in the nswavelength call.

    if os.path.exists("w"+arc+".fits"):
        if over:
            iraf.delete("w"+arc+".fits")
        else:
            print "Output file exists and -over not set - skipping wavecal"
            return

    hdulist = pyfits.open(arc+".fits")
    band = hdulist[0].header['GRATING'][0:1]

    if band == "Z":
        clist="nifs$data/ArXe_Z.dat"
        my_thresh=100.0
    elif band == "K":
        clist="gnirs$data/argon.dat"
        my_thresh=50.0
    else:
        clist="gnirs$data/argon.dat"
        my_thresh=100.0

    iraf.nswavelength(arc, coordli=clist, nsum=10, thresho=my_thresh, trace='yes', fwidth=2.0, match=-6,cradius=8.0,fl_inter='no',nfound=10,nlost=10,logfile=log)

#--------------------------------------------------------------------------------------------------------------------------------#

def ronchi(ronchilist, ronchiflat, calflat, over, flatdark, log):
    
    for image in ronchilist:
        image = str(image).strip()
        if over:
            iraf.delete("n"+image+'.fits')
        iraf.nfprepare(image,rawpath="", shiftimage="s"+calflat, bpm="rgn"+calflat+"_sflat_bpm.pl", fl_vardq="yes",fl_corr="no",fl_nonl="no", logfile=log)
    ronchilist = checkLists(ronchilist, '.', 'n', '.fits')
        
    # Determine the number of input Ronchi calibration mask files so that
    # the routine runs automatically for single or multiple files.
    
    if over:
        iraf.delete("gn"+ronchiflat+".fits")
    if len(ronchilist) > 1:
        iraf.gemcombine(listit(ronchilist,"n"),output="gn"+ronchiflat,fl_dqpr="yes", masktype="none",fl_vardq="yes",logfile=log)
    else:
        iraf.copy("n"+ronchiflat+".fits","gn"+ronchiflat+".fits")
        
    if over:
        iraf.delete("rgn"+ronchiflat+".fits")
    iraf.nsreduce("gn"+ronchiflat, outpref="r",dark="rgn"+flatdark+"_dark", flatimage="rgn"+calflat+"_flat",fl_cut="yes", fl_nsappw="yes",fl_flat="yes", fl_sky="no", fl_dark="yes", fl_vardq="no", logfile=log)

    if over:
        iraf.delete("brgn"+ronchiflat+".fits")
    iraf.nfsdist("rgn"+ronchiflat,fwidth=6.0, cradius=8.0, glshift=2.8, minsep=6.5, thresh=2000.0, nlost=3, fl_inter="no",logfile=log)

    # Put the name of the distortion file into a file of fixed name to be
    # used by the pipeline

    open("ronchifile", "w").write("rgn"+ronchiflat)

#---------------------------------------------------------------------------------------------------------------------------------------#
    
