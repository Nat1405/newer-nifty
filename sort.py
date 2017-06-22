################################################################################
#                Import some useful Python utilities/modules                   #
################################################################################
from xml.dom.minidom import parseString
import urllib
from pyraf import iraf
import pyfits
import os, shutil, glob, math, logging
import numpy as np
# Import custom Nifty functions.
from defs import getUrlFiles, getFitsHeader, FitsKeyEntry, stripString, stripNumber, \
datefmt, checkOverCopy, checkQAPIreq, checkDate, writeList, checkEntry, timeCalc


def start(dir, tel, sort, over, copy, program, date):
    """
        nifs_sort

        This module contains all the functions needed to copy and sort
        NIFS RAW DATA.


        If nifs_sort is being run outside of the Gemini North internal network,
        a path to the raw files directory must be entered with -q.

        If nifs_sort is being run from the Gemini North internal network, data can
        be copied from /net/mko-nfs/sci/dataflow by entering a program id or date with
        -p or -d at command line.

        COMMAND LINE OPTIONS
        If you wish to process local raw files specify a path to the raw files
        directory with -q in command line
        If you wish to skip the copy procedure enter -c False in command line
        If you wish to skip the sort procedure enter -s False in command line
        If you already copied files from the Gemini North internal network and
        wish to skip the copy procedure enter -c False and -s False in command line.

        INPUT FILES:
        + Raw files
          - Science frames
          - Calibration frames
          - Telluric frames
          - Acquisition frames (optional)

        OUTPUT:
          - Sorted data
          - Lists of paths to the calibrations, science and telluric frames
          - Names of frames stored in text files for later use by the pipeline

    Args:
        dir (string):   Local path to raw files directory. Specified with -q at command line.
        tel (boolean):  If False no telluric corrections will be executed. Specified with
                        -t at command line. Default: True.
        over (boolean): If True old files will be overwritten during data reduction. Specified
                        with -o at command line. Default: False.
        sort (boolean): If False data will not be sorted. Specified with -s or --sort at
                        command line. Default: True.

            FOR INTERNAL GEMINI USE:
        copy (boolean):   Specified with -c or --copy at command line. If True data
                          will be copied from Gemini network. Default: False.
        program (string): OT observation id (used only within Gemini network). Specified with
                          -p at command line. "GN-2013B-Q-109".
        date (string):    program date (used only within Gemini network). Specified with -d at
                          command line. "YYYYMMDD".

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

    logging.info('####################################')
    logging.info('#                                  #')
    logging.info('#  Start NIFS sorting and copying  #')
    logging.info('#                                  #')
    logging.info('####################################\n')

    print '####################################'
    print '#                                  #'
    print '#  Start NIFS sorting and copying  #'
    print '#                                  #'
    print '####################################\n'


    # Check for invalid command line input. Cannot both copy from Gemini and sort local files.
    # Exit if -q <path to raw image files> and -c True are specified at command line (cannot copy from
    # Gemini North internal network AND use local raw data).
    if dir and copy:
        print "\n Error in sort. Cannot specify -q AND -c True (local raw files directory AND copy files from Gemini network).\n"
        raise SystemExit


    ############################################################################
    ############################################################################
    #                                                                          #
    #                     CASE 1: USE LOCAL RAW FILES                          #
    #                                                                          #
    #    These conditions are used when a local path to raw files              #
    #    is specified with -q at command line.                                 #
    #                                                                          #
    #                                                                          #
    ############################################################################
    ############################################################################


    # IF a local raw directory path is given with -q at command line, sort OR don't sort data.
    if dir:
        if sort:
            allfilelist, arclist, arcdarklist, flatlist, flatdarklist, ronchilist, objDateList, skylist, telskylist, obsidDateList, scienceImageList = makeSortFiles(dir)
            objDirList, obsDirList, telDirList = sortObs(allfilelist, skylist, telskylist, scienceImageList, dir)
            calDirList = sortCals(arcdarklist, arclist, flatlist, flatdarklist, ronchilist, objDateList, objDirList, obsidDateList, dir)
            # If a telluric correction will be performed sort the science and telluric images based on time between observations.
            # This will NOT be executed if -t False is specified at command line.
            if tel:
                telSort(telDirList, obsDirList)
        # IF NO sort, create lists of paths to data directories.
        # This will ONLY be executed IF -q <path to raw image files> AND -s False are specified at command line.
        elif not sort:
            allfilelist, arclist, arcdarklist, flatlist, flatdarklist, ronchilist, objDateList, skylist, telskylist, obsidDateList, scienceImageList = makeSortFiles(dir)
            obsDirList, calDirList, telDirList = getPaths(allfilelist, objDateList, dir)



    ############################################################################
    ############################################################################
    #                                                                          #
    #                       CASE 2: USE GEMINI NETWORK                         #
    #                                                                          #
    #     These conditions are used if a program, date or copy is specified    #
    #     with -p, -d or -c True at command line. Files can be copied from     #
    #     Gemini North internal network and sorted.                            #
    #                                                                          #
    #                                                                          #
    ############################################################################
    ############################################################################

    elif copy or program or date:
        try:
            import geminiSort
        except ImportError:
            print "\nImportError: I didn't find the geminiSort.py module. Be sure to install it\
                    to download from the Gemini Internal Network."
            raise SystemExit
        else:
            geminiSort.start(tel, sort, over, copy, program, date)





    # Exit if no or incorrectly formatted input is given.
    else:
        print "\nERROR in sort: Enter a program ID, observation date, or directory where the raw files are located.\n"
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

    allfilelist = [] # List of tellurics, science frames, aquisitions... But not calibrations!
    flatlist = [] # List of lamps on flat frames.
    flatdarklist = [] # List of lamps off flat frames.
    ronchilist = [] # List of ronchi flat frames.
    arclist = [] # List of arc frames.
    arcdarklist = [] # List of arc dark frames.

    objDateList = [] # 2D list of object (science or telluric) name, date pairs.

    skylist = [] # List of sky frames.
    telskylist = [] # List of telluric sky frames.

    obsidDateList = [] # 2D list of date, observation id pairs.
    sciDateList = [] # List of unique dates by science (including sky) frames.

    scienceImageList = [] # List of science observation directories.

    # Store current working directory for later use.
    path = os.getcwd()

    # If files were copied from Gemini Internal network raw files directory will
    # be path+"/Raw".
    if dir:
        Raw = dir
    else:
        Raw = path+'/Raw'

    # Change to raw files directory, copy and sort FILE NAMES into lists of each type (Eg: science frames, ronchi flat frames).
    # Sort by opening the .fits headers, reading header data into variables and sorting based on those variables.
    # DOES NOT COPY RAW .fits DATA IN THIS STEP
    os.chdir(Raw)
    print "Raw file directory is: ", Raw

    print "\nI am making lists of each type of file."

    # Make a list of all the files in the Raw directory.
    rawfiles = glob.glob('N*.fits')

    # Sort and copy each filename in the rawfiles directory into lists.
    for entry in rawfiles:

        # Open the .fits header.
        header = pyfits.open(entry)

        # Store information in variables.
        obstype = header[0].header['OBSTYPE'].strip()
        ID = header[0].header['OBSID']
        date = header[0].header[ 'DATE'].replace('-','')
        aper = header[0].header['APERTURE']
        obsclass = header[0].header['OBSCLASS']
        objname = header[0].header['OBJECT'].replace(' ', '')
        poff = header[0].header['POFFSET']
        qoff = header[0].header['QOFFSET']

        # Make a list of science, telluric and acquisition frames.
        # Use the copied variable (1 not copied, 0 copied) to check later that
        # the file was copied correctly. allfilelist is a 2D list of
        # [[filename1, copied, obsclass1], [filename2, copied, obsclass2]] pairs.
        if obstype == 'OBJECT' and (obsclass == 'science' or obsclass == 'acq' or obsclass == 'acqCal' or obsclass == 'partnerCal'):

            # Append a list of [filename, copied, obsclass] to the list. copied is
            # 1 if not copied, 0 if copied. obsclass is used later for checks.
            templist = [entry, 1, obsclass]
            allfilelist.append(templist)

            # Create a list of science sky frames.
            # Differentiating between on target and sky frames.
            rad = math.sqrt(poff**2 + qoff**2)

            # If the offsets are outside a circle of 5.0 units in radius, append to skylist.
            if obsclass == 'science':
                scienceImageList.append(entry)
                if rad > 3.0:
                    skylist.append(entry)

            # Create a list of telluric sky frames.
            if obsclass == 'partnerCal':
                if rad > 2.5:
                    telskylist.append(entry)

            # Create sciDateList: list of unique dates of science observations.
            if obsclass == 'science':
                # Append if list is empty or not a duplicate of last entry.
                if not sciDateList or not sciDateList[-1]==date:
                    sciDateList.append(date)

        # Add arc frame names to arclist.
        if obstype == 'ARC':
            arclist.append(entry)

        # Add arc dark frame names to arcdarklist.
        if obstype == 'DARK':
            arcdarklist.append(entry)

        # Add lamps on flat frames to flatlist,
        # add lamps off flat frames to flatdarklist,
        # add ronchi flat frames to ronchilist.
        # Lamps on and lamps off flats are seperated by mean number of counts per pixel.
        # Arbitrary threshold is if mean_counts < 2000 it is a lamps off flat.
        if obstype == 'FLAT':

            if aper == 'Ronchi_Screen_G5615':
                ronchilist.append(entry)

            else:
                # Open the image and store pixel values in an array and
                # take the mean of all pixel values.
                array = pyfits.getdata(entry)
                mean_counts = np.mean(array)

                # Once the mean is stored in mean_counts we can check whether the
                # frame is a sky or an object based on the counts. 2000.0 is an
                # arbitrary threshold that appears to work well.
                if mean_counts < 2000.0:
                    flatdarklist.append(entry)
                else:
                    flatlist.append(entry)

    # Based on science (including sky) frames, make a list of unique [object, date] list pairs to be used later.
    for i in range(len(rawfiles)):

        header = pyfits.open(rawfiles[i])
        date = header[0].header['DATE'].replace('-','')
        obsclass = header[0].header['OBSCLASS']
        obj = header[0].header['OBJECT'].replace(' ', '')
        obstype = header[0].header['OBSTYPE'].strip()
        obsid = header[0].header['OBSID']

        if obsclass == 'science':
            list1 = [obj, date]
            # Append if list is empty or not a duplicate of last entry.
            if not objDateList or not objDateList[-1]==list1:
                objDateList.append(list1)

    # Make list of unique [date, obsid] pairs from FLATS. If flat was taken on the same day as a science
    # frame, append that flat date. If not, append an arbitrary unique date from sciDateList.
    # This is so we can sort calibrations later by date and observation id.
    n = 0
    for flat in flatlist:
        header = pyfits.open(flat)
        obsid = header[0].header['OBSID']
        date = header[0].header['DATE'].replace('-','')
        # Make sure no duplicate dates are being entered.
        if flatlist.index(flat)==0 or not oldobsid==obsid:
            if date in sciDateList:
                list1 = [date, obsid]
            else:
                list1 = [sciDateList[n], obsid]
            obsidDateList.append(list1)
            n+=1
        oldobsid = obsid

    os.chdir(path)

    # Print information for user.
    print "\nTotal number of files found by type: "
    print "Length allfilelist (science and telluric frames): ", len(allfilelist)
    print "Length arclist (arc frames): ", len(arclist)
    print "Length arcdarklist (arc dark frames): ", len(arcdarklist)
    print "Length flatlist (lamps on flat frames): ", len(flatlist)
    print "Length flatdarklist (lamps off flat frames): ", len(flatdarklist)
    print "Length ronchilist (ronchi flat frames): ", len(ronchilist)
    print "Length skylist (science sky frames): ", len(skylist)
    print "Length telskylist (telluric sky frames): ", len(telskylist)

    # Store number of telluric, telluric, sky, telluric sky and acquisition frames in number_files_to_be_copied.
    number_files_to_be_copied = len(allfilelist)

    # Store number of arcs, arc darks, lamps on flats, lamps off flats and ronchi flats in number_calibration_files_to_be_copied.
    number_calibration_files_to_be_copied = len(arclist) + len(arcdarklist) +\
                         len(flatlist) + len(flatdarklist) + len(ronchilist)

    print "\nNumber of files to be processed: ", number_files_to_be_copied + number_calibration_files_to_be_copied

    return allfilelist, arclist, arcdarklist, flatlist, flatdarklist, ronchilist, objDateList, skylist, telskylist, obsidDateList, scienceImageList

#----------------------------------------------------------------------------------------#

def sortObs(allfilelist, skylist, telskylist, scienceImageList, dir):

    """Sorts the science images, tellurics and acquisitions into the appropriate directories based on date, grating, obsid, obsclass, when not using the Gemini network.
    """

    # Store number of science, telluric, sky, telluric sky and acquisition frames in number_files_to_be_copied
    number_files_to_be_copied = len(allfilelist)

    # Initialize a counter to track how many files were copied. If this is different than
    # number_files_to_be_copied print a warning for the user at the end of sortObs.
    number_files_that_were_copied = 0

    print "\n\nMaking new directories and copying files. In this step I will process " + str(number_files_to_be_copied) +\
            " files."

    # List of paths sorted by object and date. ['path/to/object1/date1', 'path/to/object1/date2'].
    objDirList = []
    # Create a 2D list obsDirList. Second part is a path to a science directory.
    # First part is a list of calculated times of each image in that science directory.
    # Eg: [[[5400,6500,7200], '/path/to/first/science'], [[3400,4300,5200], '/path/to/second/science']...]
    obsDirList = []
    # List of paths to telluric directories.
    telDirList = []

    path = os.getcwd()
    if dir:
        Raw = dir
    else:
        Raw = path+'/Raw'

    # Make new sorted directories to copy files in to.
    print "\nMaking new directories.\n"

    # All data is sorted by science frame data.
    # For each science frame, create a "science_object_name/date/" directory in
    # the current working directory.
    for entry in allfilelist:
        header = pyfits.open(Raw+'/'+entry[0])

        objname = header[0].header['OBJECT'].replace(' ', '')
        obsclass = header[0].header['OBSCLASS']
        date = header[0].header[ 'DATE'].replace('-','')         # 1st CAL sorting criterion

        if obsclass=='science':
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

    # For each science frame, create a "science_object_name/date/grating/observationid/"
    # directory in the current working directory.
    for entry in allfilelist:
        header = pyfits.open(Raw+'/'+entry[0])

        obstype = header[0].header['OBSTYPE'].strip()
        obsid = header[0].header['OBSID'][-3:].replace('-','')
        grat = header[0].header['GRATING'][0:1]
        date = header[0].header[ 'DATE'].replace('-','')
        obsclass = header[0].header['OBSCLASS']
        obj = header[0].header['OBJECT'].replace(' ','')

        if obsclass=='science':
            # Important- calculate the time of day in seconds that the science (and sky) frames
            # were taken. Used because one way to match telluric frames with science frames is
            # to pair the frames closest in time.
            time = timeCalc(Raw+'/'+entry[0])

            objDir = path+'/'+obj
            # Create a directory for each observation date (YYYYMMDD) in objDir/.
            if not os.path.exists(objDir+'/'+date):
                os.mkdir(objDir+'/'+date)
            # Create a directory for each grating used in objDir/YYYYMMDD/.
            if not os.path.exists(objDir+'/'+date+'/'+grat):
                os.mkdir(objDir+'/'+date+'/'+grat)
            # Create a directory for each obsid (eg. obs25) in objDir/YYYYMMDD/grating/.
            if not os.path.exists(objDir+'/'+date+'/'+grat+'/obs'+obsid):
                os.mkdir(objDir+'/'+date+'/'+grat+'/obs'+obsid)
                # If a new directory append time of science (or sky) frame and directory name to obsDirList.
                obsDirList.append([[time], objDir+'/'+date+'/'+grat+'/obs'+obsid])
            # Else if a new list or not a duplicate of the previous entry append time and directory name to obsDirList.
            elif not obsDirList or not obsDirList[-1][1]==objDir+'/'+date+'/'+grat+'/obs'+obsid:
                obsDirList.append([[time], objDir+'/'+date+'/'+grat+'/obs'+obsid])
            # IF A DUPLICATE:
            # Append the time to an existing time list.
            #
            # Eg, before appending: [[[5400,6500,7200], '/path/to/first/science'], [[5200], '/path/to/second/science']]
            # If we are processing the second image in /path/to/second/science/, obsDirList[-1][1] will equal /path/to/second/science.
            # 
            #

            elif obsDirList[-1][1] == objDir+'/'+date+'/'+grat+'/obs'+obsid:
                obsDirList[-1][0].append(time)


    # Copy science and acquisition images to the appropriate directory
    print "\nCopying Science and Acquisitions.\nNow copying: "

    for i in range(len(allfilelist)):
        header = pyfits.open(Raw+'/'+allfilelist[i][0])

        obstype = header[0].header['OBSTYPE'].strip()    # determines which files are ARCS
        obsid = header[0].header['OBSID'][-3:].replace('-','')
        grat = header[0].header['GRATING'][0:1]  # this is so we can trim the string using indexing
        date = header[0].header[ 'DATE'].replace('-','')         # 1st CAL sorting criterion
        obsclass = header[0].header['OBSCLASS']  # used to sort out the acqs and acqCals in the trap
        obj = header[0].header['OBJECT'].replace(' ', '')

        # Only grab the most recent aquisition image
        if i!=len(allfilelist)-1:
            header2 = pyfits.open(Raw+'/'+allfilelist[i+1][0])
            obsclass2 = header2[0].header['OBSCLASS']
            obj2 = header2[0].header['OBJECT'].replace(' ','')


        if obsclass=='science':
            print allfilelist[i][0]
            objDir = path+'/'+obj
            shutil.copy(Raw+'/'+allfilelist[i][0], objDir+'/'+date+'/'+grat+'/obs'+obsid+'/')
            number_files_that_were_copied += 1
            # Update status flag to show entry was copied
            allfilelist[i][1] = 0
            # create an objlist in the relevant directory
            if allfilelist[i][0] not in skylist:
                writeList(allfilelist[i][0], 'objlist', objDir+'/'+date+'/'+grat+'/obs'+obsid+'/')
            # create a skylist in the relevant directory
            if allfilelist[i][0] in skylist:
                writeList(allfilelist[i][0], 'skylist', objDir+'/'+date+'/'+grat+'/obs'+obsid+'/')


        if obsclass=='acq' and obsclass2=='science':
            print allfilelist[i][0]
            # create an Acquisitions directory in objDir/YYYYMMDD/grating
            if not os.path.exists(path+'/'+obj2+'/'+date+'/'+grat+'/Acquisitions/'):
                os.makedirs(path+'/'+obj2+'/'+date+'/'+grat+'/Acquisitions/')
            shutil.copy(Raw+'/'+allfilelist[i][0], path+'/'+obj2+'/'+date+'/'+grat+'/Acquisitions/')
            number_files_that_were_copied += 1
            allfilelist[i][1] = 0

    # Copy telluric images to the appropriate folder.
    # Note: Because the 'OBJECT' of a telluric file header is different then the
    # science target, we need to sort by date, grating AND most recent time.
    print "\n\nCopying tellurics data.\nNow copying: "
    for i in range(len(allfilelist)):
        header = pyfits.open(Raw+'/'+allfilelist[i][0])

        obstype = header[0].header['OBSTYPE'].strip()    # determines which files are ARCS
        obsid = header[0].header['OBSID'][-3:].replace('-','')
        grat = header[0].header['GRATING'][0:1]  # this is so we can trim the string using indexing
        date = header[0].header[ 'DATE'].replace('-','')         # 1st CAL sorting criterion
        obsclass = header[0].header['OBSCLASS']  # used to sort out the acqs and acqCals in the trap
        obj = header[0].header['OBJECT'].replace(' ', '')
        telluric_time = timeCalc(Raw+'/'+allfilelist[i][0])


        if obsclass=='partnerCal':
            print allfilelist[i][0]
            timeList = []
            for k in range(len(obsDirList)):
                # Make sure date and gratings match
                tempDir = obsDirList[k][1].split(os.sep)
                if date in tempDir and grat in tempDir:
                    # Open the times of all science images in science_directory
                    times = obsDirList[k][0]
                    # Find difference in each time from the telluric image we're trying to sort
                    diffList = []
                    for b in range(len(times)):
                        difference = abs(telluric_time-obsDirList[k][0][b])
                        templist = []
                        templist.append(difference)
                        templist.append(obsDirList[k][1])
                        diffList.append(templist)
                    # Find the science image with the smallest difference;
                    minDiff = min(diffList)
                    # Pass that time and path out of the for loop
                    timeList.append(minDiff)
            # Out of the for loop, compare min times from different directories.
            if timeList:
                closest_time = min(timeList)
                # Copy the telluric image to the path of that science image.
                path_to_science_dir = closest_time[1]
                path_to_tellurics = os.path.split(path_to_science_dir)[0]

                # create a Tellurics directory in objDir/YYYYMMDD/grating

                if not os.path.exists(path_to_tellurics + '/Tellurics'):
                    os.mkdir(path_to_tellurics + '/Tellurics')
                # create an obsid (eg. obs25) directory in the Tellurics directory
                if not os.path.exists(path_to_tellurics+'/Tellurics/obs'+obsid):
                    os.mkdir(path_to_tellurics+'/Tellurics/obs'+obsid)
                    telDirList.append(path_to_tellurics+'/Tellurics/obs'+obsid)
                elif not telDirList or not telDirList[-1]==path_to_tellurics+'/Tellurics/obs'+obsid:
                    telDirList.append(path_to_tellurics+'/Tellurics/obs'+obsid)
                shutil.copy(Raw+'/'+allfilelist[i][0], path_to_tellurics+'/Tellurics/obs'+obsid+'/')
                number_files_that_were_copied += 1
                allfilelist[i][1] = 0
                # create an objlist in the relevant directory
                if allfilelist[i][0] not in telskylist:
                    writeList(allfilelist[i][0], 'tellist', path_to_tellurics+'/Tellurics/obs'+obsid+'/')
                # create a skylist in the relevant directory
                if allfilelist[i][0] in telskylist:
                    writeList(allfilelist[i][0], 'skylist', path_to_tellurics+'/Tellurics/obs'+obsid+'/')

    # Modify obsDirList to a format telSort can use.
    tempList = []
    for i in range(len(obsDirList)):
        tempList.append(obsDirList[i][1])
    obsDirList = tempList

    #------------------------------ TESTS -------------------------------------#

    # Check to see which files were not copied
    print "\nChecking for non-copied science, tellurics and acquisitions.\n"
    for i in range(len(allfilelist)):
        # Check the copied flag. If not 0, print the entry.
        if allfilelist[i][1] != 0:
            print allfilelist[i][0], allfilelist[i][2],  " was not copied."
    print "\nEnd non-copied science, tellurics and acquisitions.\n"

    # Check that all science images were copied
    count_from_raw_files = len(scienceImageList)

    count = 0
    for science_directory in obsDirList:
        for file in os.listdir(science_directory):
            if file.endswith('.fits'):
                count += 1

    if count_from_raw_files != count:
        print "\nWARNING: ", count_from_raw_files - count, " science images (or sky frames) \
        were not copied.\n"
    else:
        print "\nExpected number of science and sky frames copied.\n"

    print "\n\nDone sorting and copying science and tellurics. Moving on to Calibrations.\n\n"

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

    count = 0
    expected_count = len(arcdarklist) + len(arclist) + len(flatlist)\
          + len(flatdarklist) + len(ronchilist)

    print "\nI am attempting to sort ", expected_count, " files.\n"

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
    print "\nSorting flats:"
    for entry in flatlist:
        header = pyfits.open(entry)
        obsid = header[0].header['OBSID']
        for objDir in objDirList:
            for item in obsidDateList:
                if obsid in item:
                    date = item[0]
                    if date in objDir:
                        shutil.copy('./'+entry, objDir+'/Calibrations/')
                        print entry
                        count += 1
                        path = objDir+'/Calibrations/'
                        # create a flatlist in the relevant directory
                        writeList(entry, 'flatlist', path)

    # sort lamps off flats
    print "\nSorting lamps off flats:"
    for entry in flatdarklist:
        os.chdir(Raw)
        header = pyfits.open(entry)
        obsid = header[0].header['OBSID']
        for objDir in objDirList:
            for item in obsidDateList:
                if obsid in item:
                    date = item[0]
                    if date in objDir:
                        shutil.copy('./'+entry, objDir+'/Calibrations/')
                        print entry
                        count += 1
                        path = objDir+'/Calibrations/'
                        # create a flatdarklist in the relevant directory
                        writeList(entry, 'flatdarklist', path)

    # sort ronchi flats
    print "\nSorting ronchi flats:"
    for entry in ronchilist:
        os.chdir(Raw)
        header = pyfits.open(entry)
        obsid = header[0].header['OBSID']
        for objDir in objDirList:
            for item in obsidDateList:
                if obsid in item:
                    date = item[0]
                    if date in objDir:
                        shutil.copy('./'+entry, objDir+'/Calibrations/')
                        print entry
                        count += 1
                        path = objDir+'/Calibrations/'
                        # create a ronchilist in the relevant directory
                        writeList(entry, 'ronchilist', path)

    # sort arc darks
    print "\nSorting arcs:"
    for entry in arclist:
        header = pyfits.open(entry)
        obsid = header[0].header['OBSID']
        date = header[0].header['DATE'].replace('-','')
        for objDir in objDirList:
            if date in objDir:
                shutil.copy('./'+entry, objDir+'/Calibrations/')
                print entry
                count += 1
                path = objDir+'/Calibrations/'
                # create an arclist in the relevant directory
                writeList(entry, 'arclist', path)

    # sort arc darks
    print "\nSorting arc darks:"
    for entry in arcdarklist:
        header = pyfits.open(entry)
        obsid = header[0].header['OBSID']
        for objDir in objDirList:
            for item in obsidDateList:
                if obsid in item:
                    date = item[0]
                    if date in objDir:
                        shutil.copy('./'+entry, objDir+'/Calibrations/')
                        print entry
                        count += 1
                        path = objDir+'/Calibrations/'
                        # create an arcdarklist in the relevant directory
                        writeList(entry, 'arcdarklist', path)
    os.chdir(path1)

    if expected_count - count == 0:
        print "\nI sorted the ", expected_count, " expected calibrations.\n"
    else:
        print "\nI did not copy ", expected_count - count, " calibration files.\n"

    return calDirList

#----------------------------------------------------------------------------------------#

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

    print "\nI am matching science images with tellurics closest in time.\n"
    for i in range(len(telDirList)):
        date = telDirList[i].split(os.sep)[-4]
        if i==0 or dateList[-1]!=date:
            dateList.append(date)

    for date in dateList:
        tellist = []
        for telDir in telDirList:
            if date in telDir:

                os.chdir(telDir)
                telImageList = open(telDir + '/' + 'tellist', "r").readlines()
                telImageList = [image.strip() for image in telImageList]
                telluric_image = telImageList[0]
                telluric_header = pyfits.open(telDir +'/'+ telluric_image + '.fits')
                telluric_grating = telluric_header[0].header['GRATING'][0:1]

                timeList=[]
                if os.path.exists('./objtellist'):
                    os.remove('./objtellist')
                templist = []
                imageList=glob.glob('N*.fits')
                templist.append(telDir)
                templist.append(imageList)
                templist.append(telluric_grating)
                tellist.append(templist)

            # Create a list of the start and stop times for each observation called timeList
            # timeList is of the form [[obsid1, start1, stop1], [obsid2, start2, stop2],...]
        for a in range(len(tellist)):
            templist=[]
            os.chdir(tellist[a][0])
            telheader = pyfits.open(tellist[a][1][0])
            start=timeCalc(tellist[a][1][0])
            stop=timeCalc(tellist[a][1][-1])
            templist.append(os.getcwd())
            templist.append(start)
            templist.append(stop)
            templist.append(tellist[a][2])
            timeList.append(templist)

        for obsDir in obsDirList:
            os.chdir(obsDir)
            if date in obsDir:
                try:
                    sciImageList = open('objlist', "r").readlines()
                except IOError:
                    sciImageList = open('skylist', "r").readlines()
                sciImageList = [image.strip() for image in sciImageList]

                # Open image and get science image grating from header

                science_image = sciImageList[0]
                science_header = pyfits.open('./'+ science_image + '.fits')
                science_grating = science_header[0].header['GRATING'][0:1]

                for image in sciImageList:
                    diffList=[]
                    imageTime = timeCalc(image+'.fits')
                    for b in range(len(timeList)):
                        # Check to make sure same grating is being used
                        if timeList[b][3] == science_grating:
                            if abs(imageTime-timeList[b][1]) <= 5400 or abs(imageTime-timeList[b][2]) <=5400:
                                if abs(imageTime-timeList[b][1]) < abs(imageTime-timeList[b][2]):
                                    diff = abs(imageTime-timeList[b][1])
                                else:
                                    diff = abs(imageTime-timeList[b][2])
                                diffList.append(timeList[b][0])
                                diffList.append(diff)

                    # find and record the science observation that is closest in time to the telluric image
                    if diffList:
                        minDiff = min(diffList)
                        telobs = diffList[diffList.index(minDiff)-1]
                        sciheader = pyfits.open(image+'.fits')
                        sciObsid = 'obs'+ sciheader[0].header['OBSID'][-3:].replace('-','')
                        if not os.path.exists(telobs+'/objtellist'):
                            writeList(sciObsid, 'objtellist', telobs)
                        else:
                            objtellist = open(telobs+'/objtellist', 'r').readlines()
                            objtellist = [item.strip() for item in objtellist]
                            if sciObsid not in objtellist:
                                writeList(sciObsid, 'objtellist', telobs)
                        writeList(image, 'objtellist', telobs)
    os.chdir(path)

    # ---------------------------- Tests ------------------------------------- #

    # Don't use tests if user doesn't want them
    tests = True
    if tests:
        # Check that each science observation has valid telluric data

        # For each science observation:
        for science_directory in obsDirList:
            os.chdir(science_directory)
            # Store science observation name in science_observation_name
            science_observation_name = science_directory.split(os.sep)[-1]
            # Optional: store time of a science frame in science_time
            try:
                sciImageList = open('objlist', "r").readlines()
            except IOError:
                print "\nWARNING in sort: science ", science_observation_name,\
                        " does not contain science images.\n"
                sciImageList = open('skylist', "r").readlines()
            sciImageList = [image.strip() for image in sciImageList]

            # Open image and get science image grating from header
            science_image = sciImageList[0]
            science_header = pyfits.open('./'+ science_image + '.fits')
            science_time = timeCalc(science_image+'.fits')
            science_date = science_header[0].header[ 'DATE'].replace('-','')

            # Check that directory obsname matches header obsname
            temp_obs_name = 'obs' + science_header[0].header['OBSID'][-3:].replace('-','')
            if science_observation_name != temp_obs_name:
                print "\nWARNING: Problem with science ", science_observation_name, \
                " observation name data in headers and directory do not match.\n"

            # Check that a tellurics directory exists
            if os.path.exists('../Tellurics/'):
                os.chdir('../Tellurics/')
            else:
                print "\nWARNING: Tellurics directory for science ", science_observation_name, \
                      " does not exist.\n"

            found_telluric_flag = False

            # Iterate through tellurics observation directories
            for directory in list(glob.glob('obs*')):
                os.chdir('./'+directory)
                # Check that a file, objtellist exists
                try:
                    objtellist = open('objtellist', "r").readlines()
                    # Check that the science observation name is in the file
                    # Check that immediately after is at least one telluric image name.
                    # Do this by checking for the science date in the telluric name.
                    for i in range(len(objtellist)):
                        telluric_observation_name = objtellist[i].strip()
                        if telluric_observation_name == science_observation_name:
                            if science_date in objtellist[i+1].strip():
                                found_telluric_flag = True
                                break
                except IOError:
                    pass

                if found_telluric_flag:
                    os.chdir('../')
                    break
                else:
                    os.chdir('../')

            if not found_telluric_flag:
                os.chdir('../')
                print "\nWARNING: no tellurics data found for science ", science_observation_name, \
                " .\n."
            else:
                print "\nFound telluric data for all science observations.\n"
            # Optional: open that telluric image and store time in telluric_time
            # Check that abs(telluric_time - science_time) < 1.5 hours

        # If failure at any point: catch appropriate exception and warn user that
        # valid telluric data for the science observation name is not present (and
        # can seriously impact results).


        # Check that each science directory has valid calibration data

    os.chdir(path)
    return

#-----------------------------------------------------------------------------#

def getPaths(allfilelist, objDateList, dir):

    """Creates a list of Calibrations directories, observation directories, and Tellurics directories.
    """

    obsDirList = []
    calDirList = []
    telDirList = []

    # Modify allfilelist to remove sorted/not sorted flag
    tempList = []
    for i in range(len(allfilelist)):
         tempList.append(allfilelist[i][0])
    allfilelist = tempList


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
        time = timeCalc(Raw+'/'+entry)
        # append obsDirList
        if obsclass=='science':
            objDir = path+'/'+obj
            path1 = (objDir+'/'+date+'/'+grat+'/obs'+obsid[-3:].replace('-',''))
            if not obsDirList or not obsDirList[-1][1]==path1:
                obsDirList.append([[time], path1])
            elif obsDirList[-1][1] == path1:
                print "Appending more times"
                obsDirList[-1][0].append(time)

    for i in range(len(allfilelist)):
        header = pyfits.open(Raw+'/'+allfilelist[i])

        obstype = header[0].header['OBSTYPE'].strip()    # determines which files are ARCS
        obsid = header[0].header['OBSID'][-3:].replace('-','')
        grat = header[0].header['GRATING'][0:1]  # this is so we can trim the string using indexing
        date = header[0].header[ 'DATE'].replace('-','')         # 1st CAL sorting criterion
        obsclass = header[0].header['OBSCLASS']  # used to sort out the acqs and acqCals in the trap
        obj = header[0].header['OBJECT'].replace(' ', '')
        telluric_time = timeCalc(Raw+'/'+allfilelist[i])


        if obsclass=='partnerCal':
            print 'sorting a telluric: '
            print allfilelist[i]
            timeList = []
            for k in range(len(obsDirList)):
                # Make sure date and gratings match
                tempDir = obsDirList[k][1].split(os.sep)
                if date in tempDir and grat in tempDir:
                    # Open the times of all science images in science_directory
                    times = obsDirList[k][0]
                    # Find difference in each time from the telluric image we're trying to sort
                    diffList = []
                    for b in range(len(times)):
                        difference = abs(telluric_time-obsDirList[k][0][b])
                        templist = []
                        templist.append(difference)
                        templist.append(obsDirList[k][1])
                        diffList.append(templist)
                    # Find the science image with the smallest difference;
                    minDiff = min(diffList)
                    # Pass that time and path out of the for loop
                    timeList.append(minDiff)
            # Out of the for loop, compare min times from different directories.
            if timeList:
                closest_time = min(timeList)
                # Copy the telluric image to the path of that science image.
                path_to_science_dir = closest_time[1]
                path_to_tellurics = os.path.split(path_to_science_dir)[0]
                if not telDirList or telDirList[-1] != path_to_tellurics:
                    telDirList.append(path_to_tellurics)

    # append Calibrations directories to the calDirList (ie. YYYYMMDD/Calibrations)
    for item in objDateList:
            Calibrations = (path+'/'+item[0]+'/'+item[1]+'/Calibrations')
            calDirList.append(Calibrations)

    # Modify obsDirList to remove extra time information
    tempList = []
    for i in range(len(obsDirList)):
        tempList.append(obsDirList[i][1])
    obsDirList = tempList

    return obsDirList, calDirList, telDirList

#-----------------------------------------------------------------------------#

if __name__ == '__main__':
    print "sort"
