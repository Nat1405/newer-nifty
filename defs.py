import time
import sys, calendar, pyfits, urllib, shutil, glob, os, fileinput
import numpy as np
from xml.dom.minidom import parseString
import logging
import smtplib
from pyraf import iraf

#--------------------------------------------------------------------#
#                                                                    #
#     DEFS                                                           #
#                                                                    #
#    Library of non reduction or sorting specific functions          #
#                                                                    #
#    The following functions were taken from the IPM scripts from    #
#    globaldefs.py:                                                  #
#    datefmt, getFitsHeader, FitsKeyEntry, stripString               #
#    stripNumber, getURLFiles                                        #
#                                                                    #
#--------------------------------------------------------------------#

def datefmt():
    datefmt = '%Y/%m/%d %H:%M:%S '
    return datefmt

#-----------------------------------------------------------------------------#

def getFitsHeader(fitsFile, fitsKeyWords):
    """ imported from /astro/sos/da/scisoft/das/daLog/MakeDaDataCheckLogDefs.py """
    selection2 ="fullheader/"+fitsFile
    url2 ="http://fits/" + selection2
    u2 = urllib.urlopen(url2)
    xml2 = u2.read()
    u2.close()
    fitsHeaderList = [fitsFile[:-5]]
    for entry in fitsKeyWords:
        myOut = FitsKeyEntry(entry, xml2)
        fitsHeaderList.append(myOut)
    #
    return fitsHeaderList

#-----------------------------------------------------------------------------#

def FitsKeyEntry(fitsKeyWd, fullheader):
    """ imported from /astro/sos/da/scisoft/das/daLog/MakeDaDataCheckLogDefs.py """
    selectEntry ="none found"
    fullList = fullheader.splitlines()
    checkKeyWd = fitsKeyWd.ljust(8,' ')
    for index in range(len(fullList)):
        if fullList[index][:8] == checkKeyWd:
            if fullList[index][10] == "'":
                selectEntry = stripString(fullList[index])
            else:
                selectEntry = stripNumber(fullList[index])
    return selectEntry

#-----------------------------------------------------------------------------#

def stripString(inputString):
    """ imported from /astro/sos/da/scisoft/das/daLog/MakeDaDataCheckLogDefs.py """

    delimString ="'"
    delimList = []
    for index in range(len(inputString)):
        if inputString[index] == delimString:
            delimList.append(index)
    outFull = inputString[delimList[0]+1:delimList[-1]]
    outPut = outFull.replace(" ","")
    #
    return outPut

#-----------------------------------------------------------------------------#

def stripNumber(inputString):
    """ imported from /astro/sos/da/scisoft/das/daLog/MakeDaDataCheckLogDefs.py
    """
    delim1 ="="
    delim2 ="/"
    delimList = []
    for index in range(len(inputString)):
        if inputString[index] == delim1:
            delimList.append(index)
        if inputString[index] == delim2:
            delimList.append(index)
    if len(delimList) == 1:
        delimList.append(index)
    outFull = inputString[delimList[0]+1:delimList[1]]
    outPut = float(outFull)
    #
    return outPut

#-----------------------------------------------------------------------------#

def getUrlFiles(url,tag):
    """ imported from IPM scripts globaldefs.py """
    u = urllib.urlopen(url)
    xml = u.read()
    u.close()
    dom = parseString(xml)

    # Get file list:
    fileList = []
    previousFilename =""
    for fe in dom.getElementsByTagName(tag):
        fitsFile = str(fe.getElementsByTagName('filename')[0].childNodes[0].data)
        # exclude consecutive duplicates:
        if fitsFile != previousFilename:
            fileList.append(fitsFile)
            previousFilename = fitsFile

    #Return file list:
    return fileList

#-----------------------------------------------------------------------------#

def checkOverCopy(filelist, path, over):
    """ checks if over is True or False and copies files from /net/mko-nfs/sci/dataflo
    based on this.
    """

    rawfiles = []
    missingRaw = []

    raw = '/net/mko-nfs/sci/dataflo'


    for entry in filelist:
        if glob.glob(path+'/'+entry):
            rawfiles.append(glob.glob(path+'/'+entry))
        else:
            missingRaw.append(entry)

    if rawfiles:
        if over:
            for entry in rawfiles:
                if os.path.exists(entry[0]):
                    os.remove(entry[0])
            # copy all science images from a given night into ./Raw/
            for entry in filelist:
                if os.path.exists(raw+'/'+entry):
                    shutil.copy(raw+'/'+entry, path)
                else:
                    print 'SKIPPED ', entry
        else:
            for entry in missingRaw:
                if os.path.exists(raw+'/'+entry):
                    shutil.copy(raw+'/'+entry, path)
                else:
                    print 'SKIPPED ', entry

    else:
        for entry in filelist:
            if os.path.exists(raw+'/'+entry):
                shutil.copy(raw+'/'+entry, path)
            else:
                print 'SKIPPED ', entry

    return

#-----------------------------------------------------------------------------#

def checkQAPIreq(alist):
    """ checks to make sure that the arcs meet the PI and QA requirements """

    blist = []
    for entry in alist:
        blist.append(entry)
    for i in range(len(alist)):
        fitsKeyWords = ['RAWPIREQ', 'RAWGEMQA']
        headerList = getFitsHeader(alist[i], fitsKeyWords)
        rawPIreq = headerList[1]
        rawGemQA = headerList[2]
        if rawPIreq in ["YES","UNKNOWN"] and rawGemQA in ["USABLE","UNKNOWN"]:
            logging.info(alist[i]+' added for processing')
        else:
            logging.info(alist[i]+' excluded, set to USABLE/FAIL')
            blist.remove(alist[i])

    return blist

#-----------------------------------------------------------------------------#

def listit(list, prefix):
    """ Returns a string where each element of list is prepended with prefix """

    l = []
    for x in list:
        l.append(prefix+(x.strip()).rstrip('.fits'))
    return ",".join(l)

#-----------------------------------------------------------------------------#

def checkDate(list):
    """ check the dates on all the telluric and acquisition files to make sure that
        there are science images on the same night
    """

    removelist = []
    datelist = []

    for entry in list:
        fitsKeyWords = ['DATE', 'OBSCLASS']
        header = getFitsHeader(entry, fitsKeyWords)
        date = header[1]
        obsclass = header[2]
        if obsclass=='science':
            if not datelist or not datelist[-1]==date:
                datelist.append(date)

    for entry in list:
        fitsKeyWords = ['DATE', 'OBSCLASS']
        header = getFitsHeader(entry, fitsKeyWords)
        date = header[1]
        obsclass = header[2]
        if not obsclass=='science' and date not in datelist:
            removelist.append(entry)

    return removelist

#-----------------------------------------------------------------------------#

def writeList(image, file, path):
    """ write image name into a file """
    homepath = os.getcwd()

    os.chdir(path)

    image = image.rstrip('.fits')

    if os.path.exists(file):
        filelist = open(file, 'r').readlines()
        if image+'\n' in filelist or not filelist:
            f = open(file, 'w')
            f.write(image+'\n')
        else:
            f = open(file, 'a')
            f.write(image+'\n')
    else:
        f = open(file, 'a')
        f.write(image+'\n')
    f.close()
    os.chdir(homepath)

    return
#-----------------------------------------------------------------------------#

def checkEntry(entry, entryType, filelist):
    """ checks to see the that program ID given matches the OBSID in the science headers
        checks to see that the date given matches the date in the science headers
    """

    if entryType == 'program':
        header = getFitsHeader(filelist[0], ['OBSID'])
        if entry in header[1]:
            pass
        else:
            print "\n Program number was entered incorrectly.\n"
            raise SystemExit

    if entryType == 'date':
        header = getFitsHeader(filelist[0], ['DATE'])
        if entry in header[1].replace('-',''):
            pass
        else:
            print "\n Date was entered incorrectly or there is no NIFS data for the date given. Please make sure the date has been entered as such: YYYYDDMM.\n"
            raise SystemExit

#-----------------------------------------------------------------------------#

def checkLists(original_list, path, prefix, suffix):
    """Check that all files made it through an iraf step. """

    new_list = []
    for image in original_list:
        image = image.strip()
        if os.path.exists(path+'/'+prefix+image+suffix):
            new_list.append(image)
        else:
            print '\n', image, '.fits not being processed due to error in image.\n'
            pass

    return new_list

#-----------------------------------------------------------------------------#

def writeCenters(objlist):
    """Write centers to a text file, load that textfile into list centers and
        return that list. """

    centers = []
    for image in objlist:
        header = pyfits.open(image+'.fits')
        poff = header[0].header['XOFFSET']
        qoff = header[0].header['YOFFSET']
        if objlist.index(image)==0:
            P0 = poff
            Q0 = qoff
            f=open('offsets', 'w')
            f.write(str(0)+'\t'+str(0)+'\n')
        else:
            f=open('offsets', 'a')
            f.write(str(P0-poff)+'\t'+str(Q0-qoff)+'\n')
    f.close()

    offlist = open('offsets', 'r').readlines()
    for line in offlist:
        centers.append([((float(line.split()[0])/5.0)/.1)+14.5, ((float(line.split()[1])/1.0)/.04)+34.5])

    return centers

#-----------------------------------------------------------------------------#

def makeSkyList(skylist, objlist, obsDir):
    """ check to see if the number of sky images matches the number of science
        images and if not duplicates sky images and rewrites the sky file and skylist
    """

    objtime = []
    skytime = []
    b = ['bbbbbbbbbbbb']
    for item in objlist:
        item = str(item).strip()
        otime = timeCalc(item+'.fits')
        objtime.append(otime)
    for sky in skylist:
        sky = str(sky).strip()
        stime = timeCalc(sky+'.fits')
        skytime.append(stime)
    print skytime
    print objtime

    templist = []
    for time in objtime:
        difflist = []
        for stime in skytime:
            difflist.append(abs(time-stime))
        ind = difflist.index(min(difflist))
        if templist and skylist[ind] in templist[-1]:
            n+=1
            templist.append(skylist[ind])
        else:
            n=0
            templist.append(skylist[ind])
        writeList(skylist[ind]+b[0][:n], 'skylist', obsDir)
        if n>0:
            shutil.copyfile(skylist[ind]+'.fits', skylist[ind]+b[0][:n]+'.fits')
    '''
    for i in range(len(skylist)-1):
        n=0
        for j in range(len(objtime)):
            if abs(skytime[i]-objtime[j])<abs(skytime[i+1]-objtime[j]):
                print skylist[i]+b[0][:n]
                writeList(skylist[i]+b[0][:n], 'skylist', obsDir)
                if n>0:
                    shutil.copyfile(skylist[i]+'.fits', skylist[i]+b[0][:n]+'.fits')
                n+=1
    '''
    skylist = open("skylist", "r").readlines()
    skylist = [image.strip() for image in skylist]
    return skylist

#-----------------------------------------------------------------------------#

def convertRAdec(ra, dec):
    """ converts RA from degrees to H:M:S and dec from degrees to degrees:arcmin:arcsec"""
    H = int(ra/15.)
    M = int((ra-(15*H))/.25)
    S = ((ra-(float(H)*15.))-(float(M)*.25))/(1./240.)

    ra = str(H)+'h'+str(M)+'m'+str(S)+'s'

    return ra

#-----------------------------------------------------------------------------#

def timeCalc(image):
    """Read time from .fits header. Convert to a float of seconds.
    """
    telheader = pyfits.open(image)
    UT = telheader[0].header['UT']
    secs = float(UT[6:10])
    mins = float(UT[3:5])
    hours = float(UT[0:2])
    time = secs+mins*60.+hours*(60.*60.)

    return time

#-----------------------------------------------------------------------------#

def MEFarithpy(MEF, image, op, result):

    if os.path.exists(result):
        os.remove(result)
    scimage = pyfits.open(MEF+'.fits')
    arithim = pyfits.open(image+'.fits')
    for i in range(88):
        if scimage[i].name=='SCI':
            if op=='multiply':
                scimage[i]=scimage[i]*arithim
            if op=='divide':
                scimage[i]=scimage[i]/arithim
    scimage.writeto(result, output_verify='ignore')
#-----------------------------------------------------------------------------#

def MEFarith(MEF, image, op, result):

    if os.path.exists(result):
        os.remove(result)
    iraf.fxcopy(input=MEF+'[0]', output=result)
    for i in range(1,88):
        iraf.fxinsert(input=MEF+'['+str(i)+']', output=result+'['+str(i)+']', groups='', verbose = 'no')
    for i in range(1,88):
        header = pyfits.open(result)
        extname = header[i].header['EXTNAME']
        if extname == 'SCI':
            iraf.imarith(operand1=result+'['+str(i)+']', op=op, operand2 = image, result = result+'['+str(i)+', overwrite]', divzero = 0.0)

#-----------------------------------------------------------------------------#

def MEFarithOLD(MEF, image, out, op, result):

    if os.path.exists(out+'.fits'):
        os.remove(out+'.fits')
    for i in range(1,88):
        header = pyfits.open(MEF+'.fits')
        extname = header[i].header['EXTNAME']
        if extname == 'DQ' or extname == 'VAR':
            iraf.imarith(operand1=MEF+'['+str(i)+']', op='*', operand2 = '1', result = out)
        if extname == 'SCI':
            iraf.imarith(operand1=MEF+'['+str(i)+']', op=op, operand2 = image, result = out, divzero = 0.0)

    iraf.fxcopy(input=MEF+'[0],'+out, output = result)
    iraf.hedit(result+'[1]', field = 'EXTNAME', value = 'SCI', add = 'yes', verify = 'no')
    iraf.hedit(result+'[1]', field='EXTVER', value='1', add='yes', verify='no')
