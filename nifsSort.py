from xml.dom.minidom import parseString
import urllib
from pyraf import iraf
import pyfits
import os, shutil, glob, math, logging
import numpy as np
from nifsDefs import getUrlFiles, getFitsHeader, FitsKeyEntry, stripString, stripNumber, datefmt, checkOverCopy, checkQAPIreq, checkDate, writeList, checkEntry, timeCalc

#--------------------------------------------------------------------#
#                                                                    #
#     SORT                                                           #
#                                                                    #
#     This module contains all the functions needed to copy and      #
#     sort the NIFS raw data.                                        #
#                                                                    #
#                                                                    #
#    If running this from the Gemini North network, data can be      #
#    copied from /net/wikiwiki/dataflow by entering a program id,    #
#    date, or both. If data does not need to be copied or the        #
#    script is being run outside of the network, a path to the raw   #
#    files must be entered.                                          #
#                                                                    #
#    COMMAND LINE OPTIONS                                            #
#    If you wish to skip the copy procedure enter -c in the command  #
#    line and if you wish to skip the sort procedure enter -s.       #
#                                                                    #
#                                                                    #
#     INPUT:                                                         #
#     + Raw files                                                    #
#       - Science frames                                             #
#       - Calibration frames                                         #
#       - Telluric frames                                            #
#       - Acquisition frames (optional, but if data is copied        #
#         from archive then acquisition frames will be copied and    #
#         sorted)                                                    #
#                                                                    #
#     OUTPUT:                                                        #
#     - Sorted data                                                  #
#     - List of paths to the calibrations and science frames         #
#                                                                    #
#--------------------------------------------------------------------#

def start(dir, tel, sort, over, copy, program, date):
    """ copy and sort data based on command line input

    Parameters:
        dir: local path to raw files directory. Specified with -q at command line.
        tel (boolean): specified with -t at command line. If yes no
                        telluric corrections will be executed. Default: True.
        over (boolean): Specified with -o at command line. If yes
                        old files will be overwritten during data reduction. Default: False.
        sort (boolean): Specified with -s or --sort at command line. If True data will be
                        sorted. Default: True.

            FOR INTERNAL GEMINI USE:
        copy (boolean): Specified with -c or --copy at command line. If True data
                        will be copied from gemini network. Default: False.
        program: specied with -p at command line. Used only within Gemini network.
        date: specified with -d at command line. Used only within Gemini network.

    """

    # Set up the logging file
    FORMAT = '%(asctime)s %(message)s'
    DATEFMT = datefmt()
    logging.basicConfig(filename='main.log',format=FORMAT,datefmt=DATEFMT,level=logging.DEBUG)
    log = os.getcwd()+'/main.log'

    path = os.getcwd()

    # Sort data if a local raw directory path is given with -q at command line.
    if dir and sort and not copy:
        allfilelist, arclist, arcdarklist, flatlist, flatdarklist, ronchilist, objDateList, skylist, telskylist, obsidDateList = makeSortFiles(dir)
        objDirList, obsDirList, telDirList = sortObs(allfilelist, skylist, telskylist, dir)
        calDirList = sortCals(arcdarklist, arclist, flatlist, flatdarklist, ronchilist, objDateList, objDirList, obsidDateList, dir)
        # if a telluric correction will be performed sort the science and telluric images based on time between observations
        if tel:
            telSort(telDirList, obsDirList)

    # When copy and sort are not performed, create a list of data directory paths
    # This will be executed if -c False, -s False and -q <path to raw image files>
    # are specified at command line.
    elif not copy and not sort:
        allfilelist, arclist, arcdarklist, flatlist, flatdarklist, ronchilist, objDateList, skylist, telskylist, obsidDateList = makeSortFiles(dir)
        obsDirList, calDirList, telDirList = getPaths(allfilelist, objDateList, dir)

    # When copy not performed sort data
    elif not copy and sort:
        allfilelist, arclist, arcdarklist, flatlist, flatdarklist, ronchilist, objDateList, skylist, telskylist, obsidDateList = makeSortFiles(dir)
        # Sort and get data from Gemini Internal Network
        if program or date:
            objDateList, objDirList, obsDirList, telDirList = sortObsGem(allfilelist, skylist, telskylist)
            calDirList = sortCalsGem(arcdarklist, arclist, flatlist, flatdarklist, ronchilist, objDateList, objDirList, obsidDateList)
        # if a telluric correction will be performed sort the science and telluric images based on time between observations
        if tel:
            telSort(telDirList, obsDirList)


    # copy data when sort not performed
    elif copy and not sort:
        # when a program is given (looks for program using http://fits/xmlfilelist/summary/NIFS)
        if program:
            allfilelist, filelist, skylist, telskylist = getProgram(program, date, over)
            arclist, arcdarklist, flatlist, flatdarklist, ronchilist, obsidDateList  = getCals(filelist, over)
            allfilelist, arclist, arcdarklist, flatlist, flatdarklist, ronchilist, objDateList, skylist, telskylist, obsidDateList = makeSortFiles(dir)
            obsDirList, calDirList, telDirList = getPaths(allfilelist, objDateList, dir)
        # when a date is given (looks for data using http://fits/xmlfilelist/summary/NIFS)
        elif date:
            allfilelist, filelist, skylist, telskylist = getScience(date, over)
            arclist, arcdarklist, flatlist, flatdarklist, ronchilist, obsidDateList  = getCals(filelist, over)
            allfilelist, arclist, arcdarklist, flatlist, flatdarklist, ronchilist, objDateList, skylist, telskylist, obsidDateList = makeSortFiles(dir)
            obsDirList, calDirList, telDirList = getPaths(allfilelist, objDateList, dir)
        if dir:
            allfilelist, arclist, arcdarklist, flatlist, flatdarklist, ronchilist, objDateList, skylist, telskylist, obsidDateList = makeSortFiles(dir)
            obsDirList, calDirList, telDirList = getPaths(allfilelist, objDateList, dir)


# Copy from Gemini Internal network and sort. Specified with -c at command line.
    elif copy and sort:
        # copy data from archives and sort if a program is given
        if program:
            allfilelist, filelist, skylist, telskylist = getProgram(program, date, over)
            arclist, arcdarklist, flatlist, flatdarklist, ronchilist, obsidDateList  = getCals(filelist, over)
            objDateList, objDirList, obsDirList, telDirList = sortObsGem(allfilelist, skylist, telskylist)
            calDirList = sortCalsGem(arcdarklist, arclist, flatlist, flatdarklist, ronchilist, objDateList, objDirList, obsidDateList)
            # if a telluric correction will be performed sort the science and telluric images based on time between observations
            if tel:
                telSort(telDirList, obsDirList)
        # copy data from archives and sort if a date is given
        if date:
           allfilelist, filelist, skylist, telskylist = getScience(date, over)
           arclist, arcdarklist, flatlist, flatdarklist, ronchilist, obsidDateList = getCals(filelist, over)
           objDateList, objDirList, obsDirList, telDirList = sortObsGem(allfilelist, skylist, telskylist)
           calDirList = sortCalsGem(arcdarklist, arclist, flatlist, flatdarklist, ronchilist, objDateList, objDirList, obsidDateList)
           # if a telluric correction will be performed sort the science and telluric images based on time between observations
           if tel:
               telSort(telDirList, obsDirList)

    # exit if no or incorrectly formatted input is given
    else:
        print "\n Enter a program ID, observation date, or directory where the raw files are located.\n"
        raise SystemExit

    os.chdir(path)

    return obsDirList, calDirList, telDirList

##################################################################################################################
#                                                     FUNCTIONS                                                  #
##################################################################################################################

def getProgram(program, date, over):

    ### copies all the science, acquisition, and telluric images for a given program to the Raw directory

    rawfiles = []
    missingRaw = []
    filelist = []
    skylist = []
    telskylist = []

    if date:
        url = 'http://fits/xmlfilelist/summary/NIFS/'+program+'/'+date+'/OBJECT'
    else:
        # internal site where observations can be found
        url = 'http://fits/xmlfilelist/summary/NIFS/'+program+'/OBJECT'

    # find and create a list of all the .fits files from a given night
    allfilelist = checkQAPIreq(getUrlFiles(url, 'file'))

    if allfilelist:
        # check to make sure that the program ID matches the OBSID in the science headers
        checkEntry(program, 'program', allfilelist)
    else:
        print '\n Either no files found or the PI and QI requirements have not been met. \n'
        raise SystemExit

    # check to make sure that all telluric and acquisition files were taken on the same night as science data and removes the ones that weren't
    removelist = checkDate(allfilelist)
    if removelist:
        for entry in removelist:
            allfilelist.remove(entry)

    # make a directory called Raw if one does not already exist
    path = os.getcwd()

    if not os.path.exists(path+'/Raw'):
        os.mkdir(path+'/Raw')
    Raw = path+'/Raw'

    # copy the files in allfilelist to the Raw directory, first checking if over is set and if the files have already been copied
    checkOverCopy(allfilelist, Raw, over)

    # make a list of all images excluding acq images (getCals cannot use acq images)
    for entry in allfilelist:
        fitsKeyWords= ["OBSCLASS", "DATE"]
        headerList = getFitsHeader(entry,fitsKeyWords)
        if not headerList[1]=='acq':
            filelist.append(entry)

    # make a list of all the sky images (science and telluric)
    for entry in allfilelist:
        fitsKeyWords = ['OBSCLASS', 'POFFSET', 'QOFFSET']
        header = getFitsHeader(entry, fitsKeyWords)
        if header[1] == 'science':
            rad = math.sqrt(header[2]**2 + header[3]**2)
            if rad > 3.0:
                skylist.append(entry)
        if header[1] == 'partnerCal':
            rad = math.sqrt(header[2]**2 + header[3]**2)
            if rad > 2.5:
                telskylist.append(entry)

    return allfilelist, filelist, skylist, telskylist

#----------------------------------------------------------------------------------------#

def getScience(date, over):

    ### copies all the science, acquisition, and telluric images for a given date to the Raw directory

    allfilelist = []
    filelist = []
    templist = []
    datelist = []
    skylist = []
    telskylist = []

    # internal site where observations can be found
    url = 'http://fits/xmlfilelist/summary/'+date+'/NIFS/OBJECT'

    # find and create a list of all the .fits files from a given night, checking the QA and PI requirements
    templist = checkQAPIreq(getUrlFiles(url, 'file'))

    # identify the images by obsclass makes a listed list of filename, obsclass, and obsid
    fitsKeyWords = ['OBSCLASS', 'OBSID', 'DATE', 'OBJECT']
    for entry in templist:
        header = getFitsHeader(entry, fitsKeyWords)
        if header[1] == 'science':
            obsid = header[2]
            break

    url2 = 'http://fits/xmlfilelist/summary/'+date+'/NIFS/OBJECT/'+obsid[:-2]
    allfilelist = checkQAPIreq(getUrlFiles(url, 'file'))

    # check to make sure that all telluric and acquisition files were taken on the same night as science data and removes the ones that weren't
    removelist = checkDate(allfilelist)
    if removelist:
        for entry in removelist:
            allfilelist.remove(entry)

    # make a list of all the sky images
    for entry in allfilelist:
        fitsKeyWords = ['OBSCLASS', 'POFFSET', 'QOFFSET']
        header = getFitsHeader(entry, fitsKeyWords)
        if header[1] == 'science':
            rad = math.sqrt(header[2]**2 + header[3]**2)
            if rad > 3.0:
                skylist.append(entry)
        if header[1] == 'partnerCal':
            rad = math.sqrt(header[2]**2 + header[3]**2)
            if rad > 2.5:
                telskylist.append(entry)
        if header[1]!='acq':
            filelist.append(entry)

    # path to data archive
    raw = '/net/wikiwiki/dataflow'


    # make a directory called Raw if one does not already exist
    path = os.getcwd()

    if not os.path.exists(path+'/Raw'):
        Raw = os.mkdir(path+'/Raw')

    Raw = path+'/Raw'

    # copy all science images from a given night into ./Raw/
    checkOverCopy(allfilelist, Raw, over)

    return allfilelist, filelist, skylist, telskylist

#----------------------------------------------------------------------------------------#

def getCals(filelist, over):

    ### copies the necessary calibration files to the Raw directory using http://fits/calmgr to match calibrations frames to science frames

    # path to data archive
    raw = '/net/wikiwiki/dataflow'

    # make a directory called Raw if one does not already exist
    path = os.getcwd()

    if os.path.exists(path+'/Raw'):
        Raw = path+'/Raw'
    else:
       Raw = os.mkdir(path+'/Raw')

    # find lamps on, lamps off, and ronchi flats
    flatlist, flatdarklist, ronchilist, obsidlist, obsidDateList = getFlat(filelist)
    # copy flats and  to Calibrations
    checkOverCopy(flatlist, Raw, over)
    checkOverCopy(flatdarklist, Raw, over)
    checkOverCopy(ronchilist, Raw, over)

    # find arc and arc darks
    arclist, arcdarklist = getArc(filelist, obsidlist)
    # copy arc to Calibrations
    checkOverCopy(arclist, Raw, over)
    checkOverCopy(arcdarklist, Raw, over)

    templist = flatlist+flatdarklist
    flatlist = []
    flatdarklist = []
    for entry in templist:
        header = pyfits.open(Raw+'/'+entry)

        obstype = header[0].header['OBSTYPE'].strip()  # used to sort out the acqs and acqCals in the trap
        aper = header[0].header['APERTURE']

        if obstype == 'FLAT' and not aper=='Ronchi_Screen_G5615':
            # open the image and store pixel values in an array
            array = pyfits.getdata(Raw+'/'+entry)
            # then this takes the mean of all of them
            mean_counts = np.mean(array)

            # once we've stored that to the variable we can use this conditional
            # to check whether the frame is a sky or an object based on the counts
            # 2000.0 is an arbitrary threshold that appears to work well.
            if mean_counts < 2000.0:
                flatdarklist.append(entry)
            else:
                flatlist.append(entry)

    return arclist, arcdarklist, flatlist, flatdarklist, ronchilist, obsidDateList

#----------------------------------------------------------------------------------------#

def getArc(filelist, obsidlist):

    ### finds and returns a list of arcs and arc darks to use to reduce the science data

    templist = []
    arclist = []
    arcdarklist = []
    obsid2list = []

    # find all the different obsid's
    for i in range(len(filelist)):
        url = 'http://fits/calmgr/arc/'+filelist[i]
        file1 = getUrlFiles(url, 'calibration')
        if i==0 or not arclist[-1]==file1[0]:
            arclist.append(file1[0])

    fitsKeyWords= ["OBSID", "RAWPIREQ","RAWGEMQA", 'DATE']

    # find all the obsid's and dates of the arcs
    for entry in templist:
        headerList = getFitsHeader(entry,fitsKeyWords)
        obsid2 = headerList[1]
        obsid2list.append(obsid2)
        datelist.append(headerList[4].replace('-',''))

    # check to make sure that the arcs meet the PI and QA requirements
    for entry in arclist:
        headerList = getFitsHeader(entry, fitsKeyWords)
        rawPIreq = headerList[2]
        rawGemQA = headerList[3]
        if rawPIreq in ["YES","UNKNOWN"] and rawGemQA in ["USABLE","UNKNOWN"]:
            pass
        else:
            print 'Arc\'s QA not PASS or UNKNOWN so skipped'

    # find arc darks
    # first check if there are arc darks in the same observing program as the arc(s)
    for obsid2 in obsid2list:
        for date in datelist:
            url = 'http://fits/xmlfilelist/summary/'+obsid2+'/DARK/'+date
            tempdarklist = getUrlFiles(url, 'file')
            for item in tempdarklist:
                arcdarklist.append(item)

    # if not arc darks were found above, use the arc darks taken in the daycal program
    if not arcdarklist:
        for obsid in obsidlist:
            url = 'http://fits/xmlfilelist/summary/'+obsid+'/DARK'
            tempdarklist = getUrlFiles(url, 'file')
            for item in tempdarklist:
                arcdarklist.append(item)

    return arclist, arcdarklist

#----------------------------------------------------------------------------------------#

def getFlat(filelist):

    # finds and returns a list of flats (lamps on, lamps off, and ronchi) to use to reduce the science data

    templist = []
    flatlist = []
    flatdarklist = []
    obsidlist = []
    ronchilist = []
    flattemp = []
    obsidDateList = []

    fitsKeyWords = ['DATE', 'OBSID']

    #find first flat for each image and record the obsids of the science image and the flat
    for i in range(len(filelist)):
        url = 'http://fits/calmgr/flat/'+filelist[i]
        file1 = str(getUrlFiles(url, 'calibration'))
        file1 = file1[2:-2]
        if i==0 or not templist[-1]==file1:
            templist.append(file1)
        header1 = getFitsHeader(filelist[i], fitsKeyWords)
        header2 = getFitsHeader(file1, fitsKeyWords)
        date = header1[1]
        obsid = header2[2]
        list1 = [date.replace('-',''), obsid]
        if date!=header2[2]:
            if not obsidDateList or not obsidDateList[-1]==list1:
                obsidDateList.append(list1)

    for entry in templist:
        fitsKeyWords = ['OBSID', 'GCALSHUT', 'OBSCLASS']
        headerList = getFitsHeader(entry, fitsKeyWords)
        obsid = headerList[1]
        obsidlist.append(obsid)
        url2 = 'http://fits/xmlfilelist/summary/'+obsid+'/FLAT'
        tempflatlist = getUrlFiles(url2, 'file')
        for item in tempflatlist:
            flattemp.append(item)

    # use the obsid of the first flat to find the other lamps on flats and lamps off flats
    for entry in flattemp:
       fitsKeyWords = ['GCALSHUT']
       header = getFitsHeader(entry, fitsKeyWords)
       # differentiate between lamps on and lamps off flats by looking for "OPEN"(lamps on) or "CLOSED"(lamps off) for GCALSHUT in the fits header
       if header[1] == 'OPEN':
           flatlist.append(entry)
       else:
           flatdarklist.append(entry)

    # use the obsid to find ronchi flats
    for obsid in obsidlist:
        url3 = 'http://fits/xmlfilelist/summary/'+obsid+'/RONCHI'
        tempronchilist = getUrlFiles(url3, 'file')
        for item in tempronchilist:
            ronchilist.append(item)

    return flatlist, flatdarklist, ronchilist, obsidlist, obsidDateList

#----------------------------------------------------------------------------------------#

def makeSortFiles(dir):

    ### creates lists of file names necessary for sorting the files into the proper directories

    allfilelist = []
    flatlist = []
    flatdarklist = []
    ronchilist = []
    arclist = []
    arcdarklist = []
    objDateList = []
    skylist = []
    telskylist = []
    obsidDateList = []
    sciDateList = []

    path = os.getcwd()
    if dir:
        Raw = dir
    else:
        Raw = path+'/Raw'

    os.chdir(Raw)

    # make a list of all the files in the Raw directory
    rawfiles = glob.glob('N*.fits')

    # sort the files into lists (allfilelist and cal lists)
    for entry in rawfiles:
        header = pyfits.open(entry)

        obstype = header[0].header['OBSTYPE'].strip()    # determines which files are ARCS
        ID = header[0].header['OBSID']           # 1st sorting criterion
        date = header[0].header[ 'DATE'].replace('-','')         # 1st CAL sorting criterion
        aper = header[0].header['APERTURE']      # used to sort the GCAL flats
        obsclass = header[0].header['OBSCLASS']  # used to sort out the acqs and acqCals in the trap
        objname = header[0].header['OBJECT'].replace(' ', '')     # used to sort the flats
        poff = header[0].header['POFFSET']       # used to sort sky frames
        qoff = header[0].header['QOFFSET']       # used to sort sky frames


        if obstype == 'OBJECT' and (obsclass == 'science' or obsclass == 'acq' or obsclass == 'acqCal' or obsclass == 'partnerCal'):
            allfilelist.append(entry)
            # differentiating between on target and sky frames
            rad = math.sqrt(poff**2 + qoff**2)
            # if the offsets are outside a circle of 5.0 units in radius
            if obsclass == 'science':
                if rad > 3.0:
                    skylist.append(entry)
            if obsclass == 'partnerCal':
                if rad > 2.5:
                    telskylist.append(entry)
            if obsclass == 'science':
                if not sciDateList or not sciDateList[-1]==date:
                    sciDateList.append(date)

        if obstype == 'ARC':
            arclist.append(entry)

        if obstype == 'DARK':
            arcdarklist.append(entry)

        if obstype == 'FLAT':
            if aper == 'Ronchi_Screen_G5615':
                ronchilist.append(entry)
            else:
                # open the image and store pixel values in an array
                array = pyfits.getdata(entry)
                # then this takes the mean of all of them
                mean_counts = np.mean(array)

                # once we've stored that to the variable we can use this conditional
                # to check whether the frame is a sky or an object based on the counts
                # 2000.0 is an arbitrary threshold that appears to work well.
                if mean_counts < 2000.0:
                    flatdarklist.append(entry)
                else:
                    flatlist.append(entry)

    # make a list of all the different observation dates (to be used in sortCals)
    for i in range(len(rawfiles)):
        header = pyfits.open(rawfiles[i])
        date = header[0].header['DATE'].replace('-','')
        obsclass = header[0].header['OBSCLASS']
        obj = header[0].header['OBJECT'].replace(' ', '')
        obstype = header[0].header['OBSTYPE'].strip()
        obsid = header[0].header['OBSID']

        if obsclass == 'science':
            list1 = [obj, date]
            if not objDateList or not objDateList[-1]==list1:
                objDateList.append(list1)
    n=0
    for flat in flatlist:
        header = pyfits.open(flat)
        obsid = header[0].header['OBSID']
        date = header[0].header['DATE'].replace('-','')
        if flatlist.index(flat)==0 or not oldobsid==obsid:
            if date in sciDateList:
                list1 = [date, obsid]
            else:
                list1 = [sciDateList[n], obsid]
            obsidDateList.append(list1)
            n+=1
        oldobsid = obsid

    os.chdir(path)

    return allfilelist, arclist, arcdarklist, flatlist, flatdarklist, ronchilist, objDateList, skylist, telskylist, obsidDateList

#----------------------------------------------------------------------------------------#

def sortObsGem(allfilelist, skylist, telskylist):

    ### sorts the science images, tellurics and acquisitions into the appropriate directories based on date, grating, obsid, obsclass; called when sorting in the Gemini network

    path = os.getcwd()
    Raw = path+'/Raw'
    pathlist = []
    pathlist2 = []
    objDirList = []
    objDateList = []
    obsDirList = []
    telDirList = []

    fitsKeyWords = ['OBSID', 'OBJECT', 'OBSCLASS', 'DATE', 'GRATING', 'POFFSET', 'QOFFSET']

    for entry in allfilelist:
        header = getFitsHeader(entry, fitsKeyWords)
        header[2] = header[2].replace(' ', '')
        DATE = header[4].replace('-','')
        if header[3]=='science':
            # create the object directory (name of target) in the current directory
            if not os.path.exists(path+'/'+header[2]):
                os.mkdir(path+'/'+header[2])
                objDir = path+'/'+header[2]
            # append object directory list (used in sortCalsGem)
                if not objDirList or not objDirList[-1]==objDir:
                    objDirList.append(objDir)
            else:
                objDir = path+'/'+header[2]
                if not objDirList or not objDirList[-1]==objDir:
                     objDirList.append(objDir)

    # append object date list of the form objDateList = [[obj1, DATE1],[obj2, DATE1]...] (used in sortCalsGem)
    for entry in allfilelist:
        header = getFitsHeader(entry, fitsKeyWords)
        DATE = header[4].replace('-','')
        obj = header[2]
        if header[3]=='science':
            list1 = [obj, DATE]
            if not objDateList or not objDateList[-1]==list1:
                objDateList.append(list1)

    for entry in allfilelist:
        header = getFitsHeader(entry, fitsKeyWords)
        DATE = header[4].replace('-','')
        objDir = path+'/'+header[2]
        obsid = header[1][-3:].replace('-','')
        if header[3]=='science':
            # create a directory for each observation date (YYYYMMDD) in objDir/
            if not os.path.exists(objDir+'/'+DATE):
                os.mkdir(objDir+'/'+DATE)
            # create a directory for each grating used in objDir/YYYYMMDD/
            if not os.path.exists(objDir+'/'+DATE+'/'+header[5][0]):
                os.mkdir(objDir+'/'+DATE+'/'+header[5][0])
            # create a directory for each obsid (eg. obs25) in objDir/YYYYMMDD/grating/
            if not os.path.exists(objDir+'/'+DATE+'/'+header[5][0]+'/obs'+obsid):
                os.mkdir(objDir+'/'+DATE+'/'+header[5][0]+'/obs'+obsid)
            # append obsid directory list; a list of all the different observation directories (used in nifsScience.py and nifsMerge.py)
                obsDirList.append(objDir+'/'+DATE+'/'+header[5][0]+'/obs'+obsid)
            elif not obsDirList or not obsDirList[-1]==objDir+'/'+DATE+'/'+header[5][0]+'/obs'+obsid:
                obsDirList.append(objDir+'/'+DATE+'/'+header[5][0]+'/obs'+obsid)

    # copy science, telluric, and acquisition images to the appropriate folder
    for i in range(len(allfilelist)):
        header = getFitsHeader(allfilelist[i], fitsKeyWords)
        DATE = header[4].replace('-','')
        obsid = header[1][-3:].replace('-','')
        if header[3]=='science':
            objDir = path+'/'+header[2]
            shutil.copy(Raw+'/'+allfilelist[i], objDir+'/'+DATE+'/'+header[5][0]+'/obs'+obsid+'/')
            # make an objlist in the relevant directory
            if allfilelist[i] not in skylist:
                writeList(allfilelist[i], 'objlist', objDir+'/'+DATE+'/'+header[5][0]+'/obs'+obsid+'/')
            # make a skylist in the relevant directory
            if allfilelist[i] in skylist:
               writeList(allfilelist[i], 'skylist', objDir+'/'+DATE+'/'+header[5][0]+'/obs'+obsid+'/')

        if header[3]=='partnerCal':
            # create a Tellurics directory in objDir/YYYYMMDD/grating
            for objDir in objDirList:
                if not os.path.exists(objDir+'/'+DATE+'/'+header[5][0]+'/Tellurics'):
                    os.mkdir(objDir+'/'+DATE+'/'+header[5][0]+'/Tellurics')
                if not os.path.exists(objDir+'/'+DATE+'/'+header[5][0]+'/Tellurics/obs'+obsid):
                    os.mkdir(objDir+'/'+DATE+'/'+header[5][0]+'/Tellurics/obs'+obsid)
                    telDirList.append(objDir+'/'+DATE+'/'+header[5][0]+'/Tellurics/obs'+obsid)
                elif not telDirList or not telDirList[-1]==objDir+'/'+DATE+'/'+header[5][0]+'/Tellurics/obs'+obsid:
                    telDirList.append(objDir+'/'+DATE+'/'+header[5][0]+'/Tellurics/obs'+obsid)
                shutil.copy(Raw+'/'+allfilelist[i], objDir+'/'+DATE+'/'+header[5][0]+'/Tellurics/obs'+obsid+'/')
                # make a tellist in the relevant directory
                if allfilelist[i] not in telskylist:
                    writeList(allfilelist[i], 'tellist', objDir+'/'+DATE+'/'+header[5][0]+'/Tellurics/obs'+obsid+'/')
                # make a skylist in the relevant telluric directory
                if allfilelist[i] in telskylist:
                    writeList(allfilelist[i], 'skylist', objDir+'/'+DATE+'/'+header[5][0]+'/Tellurics/obs'+obsid+'/')

        if i!=(len(allfilelist)-1):
            header2= getFitsHeader(allfilelist[i+1], fitsKeyWords)
        if header[3]=='acq' and header2[3]=='science': #or header[3]=='acqCal' and header2[3]=='partnerCal':
            # create an Acquisitions directory in objDir/YYYYMMDD/grating
            if not os.path.exists(header2[2]+'/'+DATE+'/'+header[5][0]+'/Acquisitions/'):
                os.mkdir(header2[2]+'/'+DATE+'/'+header[5][0]+'/Acquisitions/')
            shutil.copy(Raw+'/'+allfilelist[i], header2[2]+'/'+DATE+'/'+header[5][0]+'/Acquisitions/')

    os.chdir(path)

    return objDateList, objDirList, obsDirList, telDirList

#----------------------------------------------------------------------------------------#

def sortCalsGem(arcdarklist, arclist, flatlist, flatdarklist, ronchilist, dateObjList, objDirList, obsidDateList):

    ### sort calibrations into the appropriate directory based on date

    calDirList = []

    path = os.getcwd()
    Raw = path+'/Raw'

    fitsKeyWords = ['OBSID', 'OBSCLASS', 'DATE']

    # create Calibrations directories in each of the observation date directories (ie. YYYYMMDD/Calibrations)
    for item in dateObjList:
        if not os.path.exists(path+'/'+item[0]+'/'+item[1]+'/Calibrations'):
            os.mkdir(path+'/'+item[0]+'/'+item[1]+'/Calibrations')
            calDirList.append(path+'/'+item[0]+'/'+item[1]+'/Calibrations')
        elif not calDirList or not calDirList[-1]==path+'/'+item[0]+'/'+item[1]+'/Calibrations':
            calDirList.append(path+'/'+item[0]+'/'+item[1]+'/Calibrations')



    # sort lamps on flats
    for entry in flatlist:
        header = getFitsHeader(entry, fitsKeyWords)
        DATE = header[3].replace('-','')
        for obj in objDirList:
            if obsidDateList:
                for item in obsidDateList:
                    if header[1] in item:
                        DATE = item[0]
            path1 = obj+'/'+DATE+'/Calibrations/'
            shutil.copy(Raw+'/'+entry, path1)
            # create a flatlist in the relevant directory
            writeList(entry, 'flatlist', path1)

    # sort lamps off flats
    for entry in flatdarklist:
        header = getFitsHeader(entry, fitsKeyWords)
        DATE = header[3].replace('-','')
        for obj in objDirList:
            if obsidDateList:
                for item in obsidDateList:
                    if header[1] in item:
                        DATE = item[0]
            path1 = obj+'/'+DATE+'/Calibrations/'
            shutil.copy(Raw+'/'+entry, path1)
            # create a flatdarklist in the relevant directory
            writeList(entry, 'flatdarklist', path1)

    # sort ronchi flats
    for entry in ronchilist:
        header = getFitsHeader(entry, fitsKeyWords)
        DATE = header[3].replace('-','')
        for obj in objDirList:
            if obsidDateList:
                for item in obsidDateList:
                    if header[1] in item:
                        DATE = item[0]
            path1 = obj+'/'+DATE+'/Calibrations/'
            shutil.copy(Raw+'/'+entry, path1)
            # create a ronchilist in the relevant directory
            writeList(entry, 'ronchilist', path1)

    # sort arcs
    for entry in arclist:
        header = getFitsHeader(entry, fitsKeyWords)
        DATE = header[3].replace('-','')
        for obj in objDirList:
            path1 = obj+'/'+DATE+'/Calibrations/'
            shutil.copy(Raw+'/'+entry,path1)
            # create an arclist in the relevant directory
            writeList(entry, 'arclist', path1)

    # sort arc darks
    for entry in arcdarklist:
        header = getFitsHeader(entry, fitsKeyWords)
        DATE = header[3].replace('-','')
        for obj in objDirList:
            if obsidDateList:
                for item in obsidDateList:
                    if header[1] in item:
                        DATE = item[0]
            path1 = obj+'/'+DATE+'/Calibrations/'
            shutil.copy(Raw+'/'+entry,path1)
            # create an arcdarklist in the relevant directory
            writeList(entry, 'arcdarklist', path1)

    os.chdir(path)

    return calDirList

#----------------------------------------------------------------------------------------#

def sortObs(allfilelist, skylist, telskylist, dir):

    ### sorts the science images, tellurics and acquisitions into the appropriate directories based on date, grating, obsid, obsclass, when not using the Gemini network

    objDirList = []
    obsDirList = []
    telDirList = []

    path = os.getcwd()
    if dir:
        Raw = dir
    else:
        Raw = path+'/Raw'

    for entry in allfilelist:
        header = pyfits.open(Raw+'/'+entry)

        objname = header[0].header['OBJECT'].replace(' ', '')
        obsclass = header[0].header['OBSCLASS']
        date = header[0].header[ 'DATE'].replace('-','')         # 1st CAL sorting criterion

        if obsclass=='science':
            # create the object directory (name of target) in the current directory
            if not os.path.exists(path+'/'+objname):
                os.mkdir(path+'/'+objname)
            if not os.path.exists(path+'/'+objname+'/'+date):
                os.mkdir(path+'/'+objname+'/'+date)
                objDir = path+'/'+objname+'/'+date
                if not objDirList or not objDirList[-1]==objDir:
                    objDirList.append(objDir)
            else:
                objDir = path+'/'+objname+'/'+date
                if not objDirList or not objDirList[-1]==objDir:
                    objDirList.append(objDir)


    for entry in allfilelist:
        header = pyfits.open(Raw+'/'+entry)

        obstype = header[0].header['OBSTYPE'].strip()    # determines which files are ARCS
        obsid = header[0].header['OBSID'][-3:].replace('-','')
        grat = header[0].header['GRATING'][0:1]  # this is so we can trim the string using indexing
        date = header[0].header[ 'DATE'].replace('-','')         # 1st CAL sorting criterion
        obsclass = header[0].header['OBSCLASS']  # used to sort out the acqs and acqCals in the trap
        obj = header[0].header['OBJECT'].replace(' ','')

        if obsclass=='science':
            objDir = path+'/'+obj
            # create a directory for each observation date (YYYYMMDD) in objDir/
            if not os.path.exists(objDir+'/'+date):
                os.mkdir(objDir+'/'+date)
            # create a directory for each grating used in objDir/YYYYMMDD/
            if not os.path.exists(objDir+'/'+date+'/'+grat):
                os.mkdir(objDir+'/'+date+'/'+grat)
            # create a directory for each obsid (eg. obs25) in objDir/YYYYMMDD/grating/
            if not os.path.exists(objDir+'/'+date+'/'+grat+'/obs'+obsid):
                os.mkdir(objDir+'/'+date+'/'+grat+'/obs'+obsid)
                obsDirList.append(objDir+'/'+date+'/'+grat+'/obs'+obsid)
            elif not obsDirList or not obsDirList[-1]==objDir+'/'+date+'/'+grat+'/obs'+obsid:
                obsDirList.append(objDir+'/'+date+'/'+grat+'/obs'+obsid)

    # copy science, telluric, and acquisition images to the appropriate folder
    for i in range(len(allfilelist)):
        header = pyfits.open(Raw+'/'+allfilelist[i])

        obstype = header[0].header['OBSTYPE'].strip()    # determines which files are ARCS
        obsid = header[0].header['OBSID'][-3:].replace('-','')
        grat = header[0].header['GRATING'][0:1]  # this is so we can trim the string using indexing
        date = header[0].header[ 'DATE'].replace('-','')         # 1st CAL sorting criterion
        obsclass = header[0].header['OBSCLASS']  # used to sort out the acqs and acqCals in the trap
        obj = header[0].header['OBJECT'].replace(' ', '')

        if i!=len(allfilelist)-1:
            header2 = pyfits.open(Raw+'/'+allfilelist[i+1])
            obsclass2 = header2[0].header['OBSCLASS']
            obj2 = header2[0].header['OBJECT'].replace(' ','')


        if obsclass=='science':
            objDir = path+'/'+obj
            shutil.copy(Raw+'/'+allfilelist[i], objDir+'/'+date+'/'+grat+'/obs'+obsid+'/')
            # create an objlist in the relevant directory
            if allfilelist[i] not in skylist:
                writeList(allfilelist[i], 'objlist', objDir+'/'+date+'/'+grat+'/obs'+obsid+'/')
            # create a skylist in the relevant directory
            if allfilelist[i] in skylist:
                writeList(allfilelist[i], 'skylist', objDir+'/'+date+'/'+grat+'/obs'+obsid+'/')

        if obsclass=='partnerCal':
            for objDir in objDirList:
                tempDir = objDir.split(os.sep)
                if date in tempDir:
                    # create a Tellurics directory in objDir/YYYYMMDD/grating
                    if not os.path.exists(objDir+'/'+grat+'/Tellurics'):
                        os.mkdir(objDir+'/'+grat+'/Tellurics')
                    # create an obsid (eg. obs25) directory in the Tellurics directory
                    if not os.path.exists(objDir+'/'+grat+'/Tellurics/obs'+obsid):
                        os.mkdir(objDir+'/'+grat+'/Tellurics/obs'+obsid)
                        telDirList.append(objDir+'/'+grat+'/Tellurics/obs'+obsid)
                    elif not telDirList or not telDirList[-1]==objDir+'/'+grat+'/Tellurics/obs'+obsid:
                        telDirList.append(objDir+'/'+grat+'/Tellurics/obs'+obsid)
                    shutil.copy(Raw+'/'+allfilelist[i], objDir+'/'+grat+'/Tellurics/obs'+obsid+'/')
                    # create an objlist in the relevant directory
                    if allfilelist[i] not in telskylist:
                        writeList(allfilelist[i], 'tellist', objDir+'/'+grat+'/Tellurics/obs'+obsid+'/')
                    # create a skylist in the relevant directory
                    if allfilelist[i] in telskylist:
                        writeList(allfilelist[i], 'skylist', objDir+'/'+grat+'/Tellurics/obs'+obsid+'/')

        if obsclass=='acq' and obsclass2=='science':
            # create an Acquisitions directory in objDir/YYYYMMDD/grating
            if not os.path.exists(path+'/'+obj2+'/'+date+'/'+grat+'/Acquisitions/'):
                os.mkdir(path+'/'+obj2+'/'+date+'/'+grat+'/Acquisitions/')
            shutil.copy(Raw+'/'+allfilelist[i], path+'/'+obj2+'/'+date+'/'+grat+'/Acquisitions/')

    os.chdir(path)

    return objDirList, obsDirList, telDirList

#----------------------------------------------------------------------------------------#

def sortCals(arcdarklist, arclist, flatlist, flatdarklist, ronchilist, objDateList, objDirList, obsidDateList, dir):

    ### sort calibrations into the appropriate directory based on date

    calDirList = []
    filelist = ['arclist', 'arcdarklist', 'flatlist', 'ronchilist', 'flatdarklist']

    path1 = os.getcwd()
    if dir:
        Raw = dir
    else:
        Raw = path1+'/Raw'

    os.chdir(Raw)

    # create Calibrations directories in each of the observation date directories (ie. YYYYMMDD/Calibrations)
    for item in objDateList:
        if not os.path.exists(path1+'/'+item[0]+'/'+item[1]+'/Calibrations'):
            os.mkdir(path1+'/'+item[0]+'/'+item[1]+'/Calibrations')
            calDirList.append(path1+'/'+item[0]+'/'+item[1]+'/Calibrations')
        else:
            calDirList.append(path1+'/'+item[0]+'/'+item[1]+'/Calibrations')
            for list in filelist:
                if os.path.exists('./'+list):
                    os.remove('./'+list)

    # sort lamps on flats
    for entry in flatlist:
        header = pyfits.open(entry)
        obsid = header[0].header['OBSID']
        for objDir in objDirList:
            for item in obsidDateList:
                if obsid in item:
                    date = item[0]
                    tempDir = objDir.split(os.sep)
                    if date in objDir:
                        shutil.copy('./'+entry, objDir+'/Calibrations/')
                        path = objDir+'/Calibrations/'
                        # create a flatlist in the relevant directory
                        writeList(entry, 'flatlist', path)

    # sort lamps off flats
    for entry in flatdarklist:
        os.chdir(Raw)
        header = pyfits.open(entry)
        obsid = header[0].header['OBSID']
        for objDir in objDirList:
            for item in obsidDateList:
                if obsid in item:
                    date = item[0]
                    tempDir = objDir.split(os.sep)
                    if date in objDir:
                        shutil.copy('./'+entry, objDir+'/Calibrations/')
                        path = objDir+'/Calibrations/'
                        # create a flatdarklist in the relevant directory
                        writeList(entry, 'flatdarklist', path)

    # sort ronchi flats
    for entry in ronchilist:
        os.chdir(Raw)
        header = pyfits.open(entry)
        obsid = header[0].header['OBSID']
        for objDir in objDirList:
            for item in obsidDateList:
                if obsid in item:
                    date = item[0]
                    tempDir = objDir.split(os.sep)
                    if date in objDir:
                        shutil.copy('./'+entry, objDir+'/Calibrations/')
                        path = objDir+'/Calibrations/'
                        # create a ronchilist in the relevant directory
                        writeList(entry, 'ronchilist', path)

    # sort arc darks
    for entry in arclist:
        header = pyfits.open(entry)
        obsid = header[0].header['OBSID']
        date = header[0].header['DATE'].replace('-','')
        for objDir in objDirList:
            tempDir = objDir.split(os.sep)
            if date in tempDir:
                shutil.copy('./'+entry, objDir+'/Calibrations/')
                path = objDir+'/Calibrations/'
                # create an arclist in the relevant directory
                writeList(entry, 'arclist', path)

    # sort arc darks
    for entry in arcdarklist:
        header = pyfits.open(entry)
        obsid = header[0].header['OBSID']
        for objDir in objDirList:
            for item in obsidDateList:
                if obsid in item:
                    date = item[0]
                    tempDir = objDir.split(os.sep)
                    if date in objDir:
                        shutil.copy('./'+entry, objDir+'/Calibrations/')
                        path = objDir+'/Calibrations/'
                        # create an arcdarklist in the relevant directory
                        writeList(entry, 'arcdarklist', path)
    os.chdir(path1)

    return calDirList

#----------------------------------------------------------------------------------------#

def getPaths(allfilelist, objDateList, dir):

    ### creates a list of Calibrations directories, observation directories, and Tellurics directories

    obsDirList = []
    calDirList = []
    telDirList = []

    path = os.getcwd()
    if dir:
        Raw = dir
    else:
        Raw = path+'/Raw'

    for entry in allfilelist:
        header = pyfits.open(Raw+'/'+entry)

        obstype = header[0].header['OBSTYPE'].strip()
        obsid = header[0].header['OBSID']
        grat = header[0].header['GRATING'][0:1]
        date = header[0].header[ 'DATE'].replace('-','')
        obsclass = header[0].header['OBSCLASS']
        obj = header[0].header['OBJECT'].replace(' ','')
        # append obsDirList
        if obsclass=='science':
            objDir = path+'/'+obj
            path1 = (objDir+'/'+date+'/'+grat+'/obs'+obsid[-3:].replace('-',''))
            if not obsDirList or not obsDirList[-1]==path1:
                obsDirList.append(path1)

    for entry in allfilelist:
        header = pyfits.open(Raw+'/'+entry)
        obsid = header[0].header['OBSID'][-3:].replace('-','')
        date = header[0].header['DATE'].replace('-','')
        obsclass = header[0].header['OBSCLASS']

        if obsclass == 'partnerCal':
            for obsDir in obsDirList:
                tempObs = obsDir.split(os.sep)
                if date==tempObs[-3]:
                    tempDir = os.path.split(obsDir)
                    # append telDirList
                    if not telDirList or not telDirList[-1]==tempDir[0]+'/Tellurics/obs'+obsid:
                        telDirList.append(tempDir[0]+'/Tellurics/obs'+obsid)

    # append Calibrations directories to the calDirList (ie. YYYYMMDD/Calibrations)
    for item in objDateList:
            Calibrations = (path+'/'+item[0]+'/'+item[1]+'/Calibrations')
            calDirList.append(Calibrations)

    return obsDirList, calDirList, telDirList

#-----------------------------------------------------------------------------#


def telSort(telDirList, obsDirList):

    ### matches science images with the telluric images that are closest in time
    ### creates a file in each telluric observation directory called objtellist
    ### objtellist lists the obsid of the science images (ie. obs123) and then the science images with this obsid that match the telluric observation
    ### EXAMPLE:     obs28
    ###              N20130527S0264
    ###              N20130527S0266
    ###              obs30
    ###              N201305727S0299

    path = os.getcwd()

    dateList=[]


    for i in range(len(telDirList)):
        date = telDirList[i].split(os.sep)[-4]
        if i==0 or dateList[-1]!=date:
            dateList.append(date)

    for date in dateList:
        tellist = []
        for telDir in telDirList:
            if date in telDir:
                timeList=[]
                os.chdir(telDir)
                if os.path.exists('./objtellist'):
                    os.remove('./objtellist')
                templist = []
                imageList=glob.glob('N*.fits')
                templist.append(telDir)
                templist.append(imageList)
                tellist.append(templist)

            # create a list of the start and stop times for each observation called timeList
            # timeList is of the form [[obsid1, start1, stop1], [obsid2, start2, stop2],...]
        for a in range(len(tellist)):
            templist=[]
            os.chdir(tellist[a][0])
            telheader = pyfits.open(tellist[a][1][0])
            telobs = 'obs'+ telheader[0].header['OBSID'][-3:].replace('-','')
            start=timeCalc(tellist[a][1][0])
            stop=timeCalc(tellist[a][1][-1])
            templist.append(telobs)
            templist.append(start)
            templist.append(stop)
            timeList.append(templist)

        for obsDir in obsDirList:
            os.chdir(obsDir)
            if date in obsDir:
                sciImageList = open('objlist', "r").readlines()
                sciImageList = [image.strip() for image in sciImageList]
                for image in sciImageList:
                    diffList=[]
                    imageTime = timeCalc(image+'.fits')
                    for b in range(len(timeList)):
                        if abs(imageTime-timeList[b][1]) <= 5400 or abs(imageTime-timeList[b][2]) <=5400:
                            if abs(imageTime-timeList[b][1]) < abs(imageTime-timeList[b][2]):
                                diff = abs(imageTime-timeList[b][1])
                            else:
                                diff = abs(imageTime-timeList[b][2])
                            diffList.append(timeList[b][0])
                            diffList.append(diff)

                    # find and record the telluric observation that is closest in time to the science image
                    if diffList:
                        minDiff = min(diffList)
                        telobs = diffList[diffList.index(minDiff)-1]
                        sciheader = pyfits.open(image+'.fits')
                        sciObsid = 'obs'+ sciheader[0].header['OBSID'][-3:].replace('-','')
                        if not os.path.exists(os.path.split(tellist[0][0])[0]+'/'+telobs+'/objtellist'):
                            writeList(sciObsid, 'objtellist', os.path.split(tellist[0][0])[0]+'/'+telobs)
                        else:
                            objtellist = open(os.path.split(tellist[0][0])[0]+'/'+telobs+'/objtellist', 'r').readlines()
                            objtellist = [item.strip() for item in objtellist]
                            if sciObsid not in objtellist:
                                writeList(sciObsid, 'objtellist', os.path.split(tellist[0][0])[0]+'/'+telobs)
                        writeList(image, 'objtellist', os.path.split(tellist[0][0])[0]+'/'+telobs)
    os.chdir(path)

    return
