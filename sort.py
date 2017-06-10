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
#    copied from /net/mko-nfs/sci/dataflow by entering a program id, #
#    date, or both. If data does not need to be copied or the        #
#    script is being run outside of the network, a path to the raw   #
#    files must be entered.                                          #
#                                                                    #
#    COMMAND LINE OPTIONS                                            #
#    If you wish to skip the copy procedure enter -c in the command  #
#    line and if you wish to skip the sort procedure enter -s.       #
#                                                                    #
#                                                                    #
#     INPUT FILES:                                                   #
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
    """Copy and sort data based on command line input.

    If -c (or --copy) True is specified data will be copied from Internal Gemini
    network (used ONLY within Gemini).

    Args:
        dir:            Local path to raw files directory. Specified with -q at command line.
        tel (boolean):  Specified with -t at command line. If False no
                        telluric corrections will be executed. Default: True.
        over (boolean): Specified with -o at command line. If True
                        old files will be overwritten during data reduction. Default: False.
        sort (boolean): Specified with -s or --sort at command line. If False data will not be
                        sorted. Default: True.

            FOR INTERNAL GEMINI USE:
        copy (boolean): Specified with -c or --copy at command line. If True data
                        will be copied from Gemini network. Default: False.
        program: Specified with -p at command line. Eg GN-2013B-Q-109. Used only within Gemini network.
        date: Specified with -d at command line. YYYYMMDD. Used only within Gemini network.

    """

    # Set up the logging file
    FORMAT = '%(asctime)s %(message)s'
    DATEFMT = datefmt()
    logging.basicConfig(filename='main.log',format=FORMAT,datefmt=DATEFMT,level=logging.DEBUG)
    log = os.getcwd()+'/main.log'

    path = os.getcwd()

    # Exit if -q and -c True are specified at command line (cannot copy from Gemini AND use local raw data).
    if dir and copy:
        print "\n Error in sort.py. Cannot specify -q AND -c True (local raw files directory AND copy files from Gemini network).\n"
        raise SystemExit


    ############################################################################
    ############################################################################
    #                                                                          #
    #                     CASE 1: USE LOCAL RAW FILES                          #
    #                                                                          #
    #    These conditionals are used when a local path to raw files            #
    #    is specified with -q at command line.                                 #
    #                                                                          #
    #                                                                          #
    ############################################################################
    ############################################################################


    # IF a local raw directory path is given with -q at command line, sort OR don't sort data.
    if dir:
        if sort:
            allfilelist, arclist, arcdarklist, flatlist, flatdarklist, ronchilist, objDateList, skylist, telskylist, obsidDateList = makeSortFiles(dir)
            objDirList, obsDirList, telDirList = sortObs(allfilelist, skylist, telskylist, dir)
            calDirList = sortCals(arcdarklist, arclist, flatlist, flatdarklist, ronchilist, objDateList, objDirList, obsidDateList, dir)
            # If a telluric correction will be performed sort the science and telluric images based on time between observations.
            # This will ONLY NOT be executed if -t False is specified at command line.
            if tel:
                telSort(telDirList, obsDirList)
        # When not sorting, create a list of data directory paths.
        # This will ONLY be executed IF -q <path to raw image files> AND -s False are specified at command line.
        elif not sort:
            allfilelist, arclist, arcdarklist, flatlist, flatdarklist, ronchilist, objDateList, skylist, telskylist, obsidDateList = makeSortFiles(dir)
            obsDirList, calDirList, telDirList = getPaths(allfilelist, objDateList, dir)



    ############################################################################
    ############################################################################
    #                                                                          #
    #                       CASE 2: USE GEMINI NETWORK                         #
    #                                                                          #
    #     These conditionals are used if -c True is specified at command       #
    #     line (OR files were previously copied from Internal Gemini Network   #
    #     and a date or program is specifed with -d or -p). Files will be      #
    #     copied from Gemini internal network.                                 #
    #                                                                          #
    #                                                                          #
    ############################################################################
    ############################################################################

    elif copy or date or program:
        try:
            import geminiSort
        except ImportError:
            print "\nImportError: I didn't find the geminiSort.py module. Be sure to install it\
                    to download from the Gemini Internal Network."
        else:
            geminiSort.start(tel, sort, over, copy, program, date)





    # Exit if no or incorrectly formatted input is given
    else:
        print "\n Enter a program ID, observation date, or directory where the raw files are located.\n"
        raise SystemExit

    os.chdir(path)

    return obsDirList, calDirList, telDirList



##################################################################################################################
#                                                                                                                #
#                                                   FUNCTIONS                                                    #
#                                                                                                                #
##################################################################################################################


def makeSortFiles(dir):

    """Creates lists of file names necessary for sorting the files into the proper directories."""

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

def sortObs(allfilelist, skylist, telskylist, dir):

    """Sorts the science images, tellurics and acquisitions into the appropriate directories based on date, grating, obsid, obsclass, when not using the Gemini network.
    """

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
                        print os.getcwd()
                        print allfilelist[i]
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
                os.makedirs(path+'/'+obj2+'/'+date+'/'+grat+'/Acquisitions/')
            shutil.copy(Raw+'/'+allfilelist[i], path+'/'+obj2+'/'+date+'/'+grat+'/Acquisitions/')

    os.chdir(path)

    return objDirList, obsDirList, telDirList

#----------------------------------------------------------------------------------------#

def sortCals(arcdarklist, arclist, flatlist, flatdarklist, ronchilist, objDateList, objDirList, obsidDateList, dir):

    """Sort calibrations into the appropriate directory based on date.
    """
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

    """Creates a list of Calibrations directories, observation directories, and Tellurics directories.
    """

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

    """Matches science images with the telluric images that are closest in time.
    Creates a file in each telluric observation directory called objtellist.
    objtellist lists the obsid of the science images (ie. obs123) and then the
    science images with this obsid that match the telluric observation.

    EXAMPLE:    obs28
                N20130527S0264
                N20130527S0266
                obs30
                N201305727S0299

    """

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

#-----------------------------------------------------------------------------#

if __name__ == '__main__':
    print "sort"
