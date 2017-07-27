import getopt
import os, glob, shutil, logging
import pexpect as p
import time
from pyraf import iraf
from pyraf import iraffunctions
import astropy.io.fits
from nifs_defs import datefmt, writeList, listit


def start(obsDirList, over=""):
    """MERGE

    This module contains all the functions needed to merge
    the final data cubes.

    NOTE: If you wish to shift the cubes manually in QFits View
    you can combine them in this script by making sure that you
    attach the prefix "shif" to each shifted image and save them
    in the observation directory (ie. obs108). This is necessary
    for very faint objects.

    COMMAND LINE OPTIONS
    If you wish to skip this script enter -m in the command line

    INPUT:
        - Reference data cubes
        - A list of paths where final data cubes are located
        - Transformed integral field spectra

    OUTPUT:
        - Merged cubes for each observation (ie. DATE_obs##(#).fits)
        - One final merged cube from entire observation program
    """

    path = os.getcwd()
    cubelist = []
    mergedCubes = []
    obsidlist = []
    pixScale = 0.043

    # Set up logfile
    FORMAT = '%(asctime)s %(message)s'
    DATEFMT = datefmt()
    logging.basicConfig(filename='Nifty.log',format=FORMAT,datefmt=DATEFMT,level=logging.DEBUG)
    log = os.getcwd()+'/Nifty.log'

    logging.info('###############################')
    logging.info('#                             #')
    logging.info('#         Start Merge         #')
    logging.info('#                             #')
    logging.info('###############################')

    print '###############################'
    print '#                             #'
    print '#         Start Merge         #'
    print '#                             #'
    print '###############################'

    # Unlearn the used tasks
    iraf.unlearn(iraf.gemini,iraf.gemtools,iraf.gnirs,iraf.nifs)
    iraf.gemini()
    iraf.nifs()
    iraf.gnirs()
    iraf.gemtools()

    # Prepare the package for NIFS
    #iraf.nsheaders("nifs",logfile=log)
    iraf.set(stdimage='imt2048')
    user_clobber=iraf.envget("clobber")
    iraf.reset(clobber='yes')

    # change to the directory in iraf
    iraffunctions.chdir(path)
    cubelist = []

    for obsDir in obsDirList:
        # Get date, obsid and obsPath by splitting each science directory name.
        # Eg: directory name is ""/Users/ncomeau/research/newer-nifty/hd165459/20160705/H/obs13", then:
        # temp1 == ('/Users/ncomeau/research/newer-nifty/hd165459/20160705/H', 'obs13')
        # temp2 == ('/Users/ncomeau/research/newer-nifty/hd165459/20160705', 'H')
        # temp3 == ('/Users/ncomeau/research/newer-nifty/hd165459', '20160705')
        # temp4 == ('/Users/ncomeau/research/newer-nifty', 'hd165459')

        # CHANGE

        temp1 = os.path.split(obsDir)
        temp2 = os.path.split(temp1[0])
        temp3 = os.path.split(temp2[0])
        temp4 = os.path.split(temp3[0])
        objname = temp4[1]
        date = temp3[1]
        obsid = temp1[1]
        obsPath = temp3[0]
        os.chdir(obsDir)
        obsidlist.append(date+'_'+obsid)

        # create a directory called Merged and copy all the data cubes to this directory
        if not os.path.exists(obsPath+'/Merged/'):
            os.mkdir(obsPath+'/Merged/')
            print 'I am creating a directory called Merged'

        Merged = obsPath+'/Merged'

        if not os.path.exists(Merged+'/'+date+'_'+obsid):
            os.mkdir(Merged+'/'+date+'_'+obsid)
            print 'I am creating a directory with date and abs ID inside Merged '

        # if a list called shiftedcubes already exists then just merge those shifted cubes and continue
        if glob.glob("./shif*.fits"):
            if over:
                if os.path.exists('./'+obsid+'_merged.fits'):
                    os.remove('./'+obsid+'_merged.fits')
                    iraf.gemcube(input="shif*.fits[SCI]", output=obsid+'_merged', logfile = log)
            elif not os.path.exists('./'+obsid+'_merged.fits'):
                iraf.gemcube(input="shif*.fits[SCI]", output=obsid+'_merged', logfile = log)
            else:
                print "Output exists and -over- not set - shifted cubes are not being merged"
            shutil.copy('./'+obsid+'_merged.fits', Merged)
            if obsDir==obsDirList[-1]:
                return
            else:
                continue

        # create a list called cubes, which stores all the cubes from a particular night
        # store all the cubes lists in a list of lists called cubelist
        cubes = glob.glob('catfbrgnN*.fits')
        if cubes:
            cubelist.append(cubes)
        else:
            cubes = glob.glob('ctfbrgn*.fits')
            if cubes:
                cubelist.append(cubes)
        '''
        if cubes:
            cubelist.append(cubes)
            pre = 'atfbrgn'
        else:
            cubes = glob.glob('tfbrgn*.fits')
            cubelist.append(cubes)
            pre = 'tfbrgn'
        '''
        # copy cubes to their date directory within Merged
        for cube in cubes:
            shutil.copy(cube, Merged+'/'+date+'_'+obsid)

    os.chdir(Merged)

    n=0
    for cubes in cubelist:

        if cubes:
            shiftlist = []
            os.chdir(Merged+'/'+obsidlist[n])
            iraffunctions.chdir(Merged+'/'+obsidlist[n])
            # set the zero point p and q offsets to the p and q offsets of the first cube in each sequence (assumed to have a p and q of 0)
            header = astropy.io.fits.open(cubes[0])
            p0 = header[0].header['POFFSET']
            q0 = header[0].header['QOFFSET']
            suffix = cubes[0][-8:-5]
            if os.path.exists('transcube'+suffix+'.fits'):
                if not over:
                    print 'Output already exists and -over- not set - skipping im3dtran'
                if over:
                    os.remove('transcube'+suffix+'.fits')
                    iraf.im3dtran(input = cubes[0]+'[SCI][*,*,-*]', new_x=1, new_y=3, new_z=2, output = 'transcube'+suffix)
            else:
                iraf.im3dtran(input = cubes[0]+'[SCI][*,*,-*]', new_x=1, new_y=3, new_z=2, output = 'transcube'+suffix)
            shiftlist.append('cube'+suffix+'.fits')
            iraffunctions.chdir(os.getcwd())
            foff = open('offsets.txt', 'w')
            foff.write('%d\t%d\t%d\n' % (0, 0, 0))

        for i in range(len(cubes)-1):
            i+=1
            header2 = astropy.io.fits.open(cubes[i])
            # find the p and q offsets of the other cubes in the sequence
            poff = header2[0].header['POFFSET']
            qoff = header2[0].header['QOFFSET']
            # calculate the difference between the zero point offsets and the offsets of the other cubes and convert that to pixels
            pShift = round((poff - p0)/pixScale)
            qShift = round((qoff - q0)/pixScale)
            # write all offsets to a text file (keep in mind that the x and y offsets use different pixel scales)
            foff = open('offsets.txt', 'a')
            foff.write('%d\t%d\t%d\n' % (pShift, qShift, 0.))
            foff.close()
            suffix = cubes[i][-8:-5]
            if os.path.exists('transcube'+suffix+'.fits'):
                if not over:
                    print 'Output already exists and -over- not set - skipping im3dtran'
                if over:
                    os.remove('transcube'+suffix+'.fits')
                    iraf.im3dtran(input = cubes[i]+'[SCI][*,*,-*]', new_x=1, new_y=3, new_z=2, output = 'transcube'+suffix)
            else:
                iraf.im3dtran(input = cubes[i]+'[SCI][*,*,-*]', new_x=1, new_y=3, new_z=2, output = 'transcube'+suffix)
            shiftlist.append('cube'+suffix+'.fits')
        if os.path.exists('cube_merged.fits'):
            if over:
                os.remove('cube_merged.fits')
                iraf.imcombine('transcube*.fits', output = 'cube_merged.fits',  combine = 'median', offsets = 'offsets.txt')
            else:
                print 'Output already exists and -over- not set - skipping imcombine'
        else:
            iraf.imcombine('transcube*.fits', output = 'cube_merged.fits',  combine = 'median', offsets = 'offsets.txt')
        if os.path.exists('out.fits'):
            if over:
                os.remove('out.fits')
                iraf.im3dtran(input='cube_merged[*,-*,*]', new_x=1, new_y=3, new_z=2, output = 'out.fits')
                iraf.fxcopy(input=cubes[0]+'[0], out.fits', output = obsidlist[n]+'_merged.fits')
            else:
                print 'Output already exists and -over- not set - skipping final im3dtran'
        else:
            iraf.im3dtran(input='cube_merged[*,-*,*]', new_x=1, new_y=3, new_z=2, output = 'out.fits')
            iraf.fxcopy(input=cubes[0]+'[0], out.fits', output = obsidlist[n]+'_merged.fits')
        mergedCubes.append(obsidlist[n]+'_merged.fits')
        n+=1
        os.chdir(Merged)

    # copy the merged observation sequence data cubes to the Merged directory
    for i in range(len(mergedCubes)):
        shutil.copy(Merged+'/'+obsidlist[i]+'/'+mergedCubes[i], './')

    # merge all the individual merged observation sequence data cubes
    if len(mergedCubes)>1:
        os.chdir(Merged)
        iraffunctions.chdir(Merged)
        gratlist = []
        for i in range(len(mergedCubes)):
            cubeheader = astropy.io.fits.open(mergedCubes[i])
            grat = cubeheader[0].header['GRATING']
            gratlist.append(grat)
        for n in range(len(gratlist)):
            indices = [k for k, x in enumerate(gratlist) if x==gratlist[n]]
            newcubelist = []
            for ind in indices:
                newcubelist.append(mergedCubes[ind])
            waveshift(newcubelist, grat)
            for i in range(len(newcubelist)):
                if i==0:
                    inputstring = newcubelist[i]+'[1]'
                else:
                    inputstring += ','+newcubelist[i]+'[1]'
            if os.path.exists('temp_merged'+gratlist[n][0]+'.fits'):
                if over:
                    iraf.delete('temp_merged'+gratlist[n][0]+'.fits')
                    iraf.imcombine(inputstring, output = 'temp_merged'+gratlist[n][0]+'.fits', combine = 'median', offsets = 'waveoffsets'+grat[0]+'.txt')
                    iraf.fxcopy(input=newcubelist[0]+'[0], temp_merged'+gratlist[n][0]+'.fits', output = 'TOTAL_merged'+gratlist[0][0]+'.fits')
                else:
                    print 'Output exists and -over- not set - skipping final cube merge'
            else:
                iraf.imcombine(inputstring, output = 'temp_merged'+gratlist[n][0]+'.fits', combine = 'median', offsets = 'waveoffsets'+grat[0]+'.txt')
                iraf.fxcopy(input=newcubelist[0]+'[0], temp_merged'+gratlist[n][0]+'.fits', output = 'TOTAL_merged'+gratlist[n][0]+'.fits')


#####################################################################################
#                                        FUNCTIONS                                  #
#####################################################################################


def waveshift(cubelist, grat):
    cubeheader0 = astropy.io.fits.open(cubelist[0])
    wstart0 = cubeheader0[1].header['CRVAL3']
    fwave = open('waveoffsets{0}.txt'.format(grat[0]), 'w')
    fwave.write('%d\t%d\t%d\n' % (0., 0., 0.,))
    for i in range(len(cubelist)):
        cubeheader = astropy.io.fits.open(cubelist[i])
        wstart = cubeheader[1].header['CRVAL3']
        wdelt = cubeheader[1].header['CD3_3']
        waveoff = int(round((wstart0-wstart)/wdelt))
        fwave.write('%d\t%d\t%d\n' % (0., 0., waveoff))
    fwave.close()

#---------------------------------------------------------------------------------------------------------------------------------------#

def mergeOld(obsDirList, over=""):
    path = os.getcwd()
    cubelist = []
    mergedCubes = []
    obsidlist = []
    pixScaleX = 0.05
    pixScaleY = 0.043
    # Set up the logging file
    FORMAT = '%(asctime)s %(message)s'
    DATEFMT = datefmt()
    logging.basicConfig(filename='Nifty.log',format=FORMAT,datefmt=DATEFMT,level=logging.DEBUG)
    log = os.getcwd()+'/Nifty.log'
    logging.info('###############################')
    logging.info('#                             #')
    logging.info('#         Start Merge         #')
    logging.info('#                             #')
    logging.info('###############################')
    print '###############################'
    print '#                             #'
    print '#         Start Merge         #'
    print '#                             #'
    print '###############################'
    # Unlearn the used tasks
    iraf.unlearn(iraf.gemini,iraf.gemtools,iraf.gnirs,iraf.nifs)
    # Prepare the package for NIFS
    iraf.nsheaders("nifs",logfile=log)
    iraf.set(stdimage='imt2048')
    user_clobber=iraf.envget("clobber")
    iraf.reset(clobber='yes')
    # change to the directory in iraf
    iraffunctions.chdir(path)
    for obsDir in obsDirList:
        temp1 = os.path.split(obsDir)
        temp2 = os.path.split(temp1[0])
        temp3 = os.path.split(temp2[0])
        temp4 = os.path.split(temp3[0])
        objname = temp4[1]
        date = temp3[1]
        obsid = temp1[1]
        obsPath = temp3[0]
        os.chdir(obsDir)
        obsidlist.append(date+'_'+obsid)
        # create a directory called Merged and copy all the data cubes to this directory
        if not os.path.exists(obsPath+'/Merged/'):
            os.mkdir(obsPath+'/Merged/')
        Merged = obsPath+'/Merged'
        if not os.path.exists(Merged+'/'+date+'_'+obsid):
            os.mkdir(Merged+'/'+date+'_'+obsid)
        # if a list called shiftedcubes already exists then just merge those shifted cubes and continue
        if glob.glob("./shif*.fits"):
            if over:
                if os.path.exists('./'+obsid+'_merged.fits'):
                    os.remove('./'+obsid+'_merged.fits')
                    iraf.gemcube(input="shif*.fits[SCI]", output=obsid+'_merged', logfile = log)
            elif not os.path.exists('./'+obsid+'_merged.fits'):
                iraf.gemcube(input="shif*.fits[SCI]", output=obsid+'_merged', logfile = log)
            else:
                print "Output exists and -over- not set - shifted cubes are not being merged"
            shutil.copy('./'+obsid+'_merged.fits', Merged)
            if obsDir==obsDirList[-1]:
                return
            else:
                continue
        # create a list called cubes, which stores all the cubes from a particular night
        # store all the cubes lists in a list of lists called cubelist
        cubes = glob.glob('bbatfbrgnN*.fits')
        if cubes:
            cubelist.append(cubes)
            pre = 'atfbrgn'
        else:
            cubes = glob.glob('tfbrgn*.fits')
            cubelist.append(cubes)
            pre = 'tfbrgn'
        # copy cubes to their date directory within Merged
        for cube in cubes:
            if cubes.index(cube)==0:
                shutil.copy('c'+pre+cube[-19:], Merged+'/'+date+'_'+obsid)
            shutil.copy(cube, Merged+'/'+date+'_'+obsid)
    os.chdir(Merged)
    n=0
    for cubes in cubelist:
        if cubes:
            os.chdir(Merged+'/'+obsidlist[n])
            # set the zero point p and q offsets to the p and q offsets of the first cube in each sequence (assumed to have a p and q of 0)
            print cubes
            print cubelist
            header = astropy.io.fits.open(cubes[0])
            p0 = header[0].header['POFFSET']
            q0 = header[0].header['QOFFSET']
            refCube = "cube"+cubes[0][-8:-5]
            iraffunctions.chdir(os.getcwd())
            if over:
                if os.path.exists('./'+refCube+'.fits'):
                    os.remove('./'+refCube+'.fits')
                iraf.imcopy('c'+pre+cubes[0][-19:-5]+"[sci,1][*,0:62,*]", output=refCube)
            elif not os.path.exists('./'+refCube+'.fits'):
                iraf.imcopy('c'+pre+cubes[0][-19:-5]+"[sci,1][*,0:62,*]", output=refCube)
            else:
                "Output file exists and -over not set - skipping imcopy reference cube"
            fx = open('offsetsX.txt', 'w')
            fx.write('%d\t%d\t%d\n' % (0, 0, 0))
            foff = open('offsets.txt', 'w')
            foff.write('%d\t%d\t%d\n' % (0, 0, 0))
        for i in range(len(cubes)-1):
            i+=1
            header2 = astropy.io.fits.open(cubes[i])
            # find the p and q offsets of the other cubes in the sequence
            poff = header2[0].header['POFFSET']
            qoff = header2[0].header['QOFFSET']
            # find the reference pixel values of the other cubes in the sequence
            refX = header2[0].header['CRPIX1']
            refY = header2[0].header['CRPIX2']
            # calculate the difference between the zero point offsets and the offsets of the other cubes and convert that to pixels
            pShift = round((poff - p0)/pixScaleX)
            qShift = round((qoff - q0)/pixScaleY)
            # write the y offsets to a text file (used in gemcombine step)
            fy = open('offsetsY.txt', 'w')
            fy.write('%d\t%d\t%d\t\n%d\t%d\t%d\n' % (0.,0.,0.,0., qShift, 0.))
            fy.close()
            # write the x offsets to a text file (used in imcombine step)
            fx = open('offsetsX.txt', 'a')
            fx.write('%d\t%d\t%d\n' % (pShift, 0., 0.))
            fx.close()
            # write all offsets to a text file (keep in mind that the x and y offsets use different pixel scales)
            foff = open('offsets.txt', 'a')
            foff.write('%d\t%d\t%d\n' % (pShift, qShift, 0.))
            foff.close()
            suffix = cubes[i][-8:-5]
            f = open('atlist', 'w')
            f.write(cubes[0].lstrip('c')+'\n'+cubes[i].lstrip('c'))
            f.close()
            atlist = open('atlist', 'r').readlines()
            # gemcombine the 2D spectra of the zero point offset and a cube that needs to be shifted
            # executes the shift in the y direction
            if over:
                if os.path.exists('./at'+suffix+'.fits'):
                    os.remove('./at'+suffix+'.fits')
                iraf.gemcombine(listit(atlist, ""), output = "at"+suffix, combine = 'average', offsets = 'offsetsY.txt', logfile = log)
            elif not os.path.exists('./at'+suffix+'.fits'):
                iraf.gemcombine(listit(atlist, ""), output = "at"+suffix, combine = 'average', offsets = 'offsetsY.txt', logfile = log)
            else:
                print "Output file exists and -over not set - skipping gemcombine (y-shift)"
            # nifcube sometimes runs into an unpredictable error
            # the pexpect sequence below anticipates this error to avoid a crash
            if over:
                if os.path.exists('./cat'+suffix+'.fits'):
                    os.remove('./cat'+suffix+'.fits')
                child = p.spawn('pyraf')
                child.expect("")
                child.sendline('gemini')
                child.expect("")
                child.sendline('nifs')
                child.expect("")
                child.sendline("nifcube at"+suffix+" logfile="+log)
                index = child.expect(["Using input files:", "Name of science extension:"])
                if index==0:
                    pass
                elif index==1:
                    child.sendline('SCI')
                child.expect("NIFCUBE  Exit status good", timeout=100)
                child.sendline('.exit')
                print child.before
                child.interact()
            elif not os.path.exists('./cat'+suffix+'.fits'):
                child = p.spawn('pyraf')
                child.expect("")
                child.sendline('gemini')
                child.expect("")
                child.sendline('nifs')
                child.expect("")
                child.sendline("nifcube at"+suffix+" logfile="+log)
                index = child.expect(["Using input files:","Name of science extension:"])
                if index==0:
                    pass
                elif index==1:
                    child.sendline('SCI')
                child.expect("NIFCUBE  Exit status good", timeout=100)
                child.sendline('.exit')
                print child.before
                child.interact()
            else:
                print "Output file exists and -over not set - skipping nifcube"
            # need to trim the image to use in imarith
            # trim to the same dimensions and position as the zero point offset image
            # this is the part of this script that does not work for faint objects
            if over:
                if os.path.exists('./ccat'+suffix+'.fits'):
                    os.remove('./ccat'+suffix+'.fits')
                if qShift < 0.:
                    iraf.imcopy("cat"+suffix+".fits[sci,1][*,"+str(int((qShift*(-1))-1))+":"+(str(int(62+(qShift*(-1))-1)))+",*]",  output = "ccat"+suffix)
                else:
                    iraf.imcopy("cat"+suffix+".fits[sci,1][*,0:62,*]", output = "ccat"+suffix)
            elif not os.path.exists('./ccat'+suffix+'.fits'):
                if qShift < 0.:
                    iraf.imcopy("cat"+suffix+".fits[sci,1][*,"+str(int((qShift*(-1))-1))+":"+(str(int(62+(qShift*(-1))-1)))+",*]",  output = "ccat"+suffix)
                else:
                    iraf.imcopy("cat"+suffix+".fits[sci,1][*,0:62,*]", output = "ccat"+suffix)
            else:
                print "Output file exists and -over not set - skipping imcopy y-shifted cube"
            # remove the zero point offset image from the average combined data cube
            if over:
                if os.path.exists('./temp'+suffix+'.fits'):
                    os.remove('./temp'+suffix+'.fits')
                iraf.imarith(operand1 = "ccat"+suffix, operand2 = 2, op = "*", result = "temp"+suffix)
            elif not os.path.exists('./temp'+suffix+'.fits'):
                iraf.imarith(operand1 = "ccat"+suffix, operand2 = 2, op = "*", result = "temp"+suffix)
            else:
                 print "Output file exists and -over not set - skipping imarith multiplication"
            if over:
                if os.path.exists('./cube'+suffix+'.fits'):
                    os.remove('./cube'+suffix+'.fits')
                iraf.imarith(operand1 = "temp"+suffix, operand2 = refCube, op = "-", result = "cube"+suffix)
            elif not os.path.exists('./cube'+suffix+'.fits'):
                iraf.imarith(operand1 = "temp"+suffix, operand2 = refCube, op = "-", result = "cube"+suffix)
            else:
                print "Output file exists and -over not set - skipping imarith subtraction"
        # sum all the y shifted data cubes and zero point offset cube
        # x shift is done in this step
        if over:
            if os.path.exists('./'+obsidlist[n]+'_merged.fits'):
                os.remove('./'+obsidlist[n]+'_merged.fits')
            iraf.imcombine("cube*.fits", output = obsidlist[n]+'_merged',  combine = 'sum', offsets = 'offsetsX.txt', logfile = log)
        elif not os.path.exists('./'+obsidlist[n]+'_merged.fits'):
            iraf.imcombine("cube*.fits", output = obsidlist[n]+'_merged',  combine = 'sum', offsets = 'offsetsX.txt', logfile = log)
        else:
            print "Output file exists and -over not set - skipping imcombine (x-shift)"
        mergedCubes.append(obsidlist[n]+'_merged')
        n+=1
    os.chdir(Merged)
    # copy the merged observation sequence data cubes to the Merged directory
    for i in range(len(mergedCubes)):
        shutil.copy(Merged+'/'+obsidlist[i]+'/'+mergedCubes[i]+'.fits', './')
    # merge all the individual merged observation sequence data cubes
    if len(mergedCubes)>1:
        iraf.imcombine("*_obs*_merged.fits", output = objname+'_merged.fits', combine = 'sum')

#---------------------------------------------------------------------------------------------------------------------------------------#

if __name__ == '__main__':
    print "nifsMerge"
