import getopt
import os, glob, shutil, logging
import pexpect as p
import time
from pyraf import iraf
from pyraf import iraffunctions
import pyfits
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

    # Store the current working directory so we can find our way back later on.
    path = os.getcwd()

    logging.info('###############################')
    logging.info('#                             #')
    logging.info('#         Start Merge         #')
    logging.info('#                             #')
    logging.info('###############################')

    iraf.gemini()
    iraf.nifs()
    iraf.gnirs()
    iraf.gemtools()

    # Unlearn the used tasks.
    iraf.unlearn(iraf.gemini,iraf.gemtools,iraf.gnirs,iraf.nifs)

    # Prepare the package for NIFS
    iraf.nsheaders("nifs",logfile="Nifty.log")
    iraf.set(stdimage='imt2048')
    user_clobber=iraf.envget("clobber")
    iraf.reset(clobber='yes')

    # Set the default logfile for iraf tasks.
    # TODO: Set the logfile for all iraf tasks! Right now it is not logging their output because of im3dtran...
    # It seems im3dtran doesn't have a "log" parameter.
    log = "Nifty.log"

    # Change to the directory in iraf.
    iraffunctions.chdir(path)

    # Create some lists here.
    listsOfCubes = []        # List of lists of cubes (one list for each science observation directory).
    mergedCubes = []         # List of Merged cubes (one merged cube for each science observation directory).
    obsidlist = []           # List of science observation id s.
    # X pixel scale in arcseconds/pixel.
    xPixScale = 0.05
    # Y pixel scale in arcseconds/pixel.
    yPixScale = 0.043

    # TODO(ncomeau[*AT*]uvic.ca): implement a way to read and save cubelists to textfiles. It would be nice for users to
    # be able to edit the list of cubes to merge by hand.
    # If no Merged directory exists that contains a textfile list of cubes:
    # Go to each science directory and copy cubes from there to a new directory called Merged.
    for obsDir in obsDirList:
        # Get date, obsid and obsPath by splitting each science directory name.
        # Eg: directory name is ""/Users/ncomeau/research/newer-nifty/hd165459/20160705/H/obs13", then:
        # temp1 == ('/Users/ncomeau/research/newer-nifty/hd165459/20160705/H', 'obs13')
        # temp2 == ('/Users/ncomeau/research/newer-nifty/hd165459/20160705', 'H')
        # temp3 == ('/Users/ncomeau/research/newer-nifty/hd165459', '20160705')
        # temp4 == ('/Users/ncomeau/research/newer-nifty', 'hd165459')

        # TODO: make this clearer.

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
            logging.info('I am creating a directory called Merged')

        Merged = obsPath+'/Merged'

        if not os.path.exists(Merged+'/'+date+'_'+obsid):
            os.mkdir(Merged+'/'+date+'_'+obsid)
            logging.info('I am creating a directory with date and abs ID inside Merged ')

        # if a list called shiftedcubes already exists then just merge those shifted cubes and continue
        if glob.glob("./shif*.fits"):
            if over:
                if os.path.exists('./'+obsid+'_merged.fits'):
                    os.remove('./'+obsid+'_merged.fits')
                    iraf.gemcube(input="shif*.fits[SCI]", output=obsid+'_merged', logfile = log)
            elif not os.path.exists('./'+obsid+'_merged.fits'):
                iraf.gemcube(input="shif*.fits[SCI]", output=obsid+'_merged', logfile = log)
            else:
                logging.info("Output exists and -over- not set - shifted cubes are not being merged")
            shutil.copy('./'+obsid+'_merged.fits', Merged)
            if obsDir==obsDirList[-1]:
                return
            else:
                continue

        # Create a list called cubes, which stores all the cubes from a particular night.
        # Store all the cubes lists in a list of lists called listsOfCubes.
        # TODO: syntax is fairly ugly; there may be a better way to do this.
        cubes = glob.glob('catfbrsnN*.fits')          # Cubes order at this point is arbitrary so we need to sort.
        cubes.sort(key=lambda x: x[-8:-5])    # Sort cubes in increasing order by last three digits.

        if cubes:
            listsOfCubes.append(cubes)
        else:
            cubes = glob.glob('cptfbrsnN*.fits')
            if cubes:
                cubes.sort(key=lambda x: x[-8:-5])    # Sort cubes in increasing order by last three digits.
                listsOfCubes.append(cubes)
            else:
                cubes = glob.glob('ctfbrsnN*.fits')
                if cubes:
                    cubes.sort(key=lambda x: x[-8:-5])    # Sort cubes in increasing order by last three digits.
                    listsOfCubes.append(cubes)
                else:
                    logging.info("\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
                    logging.info("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
                    logging.info("")
                    logging.info("     ERROR in merge: no cubes found!")
                    logging.info("")
                    logging.info("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
                    logging.info("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n")
                    raise SystemExit
        # Copy cubes to their respective data_obsid directory within Merged.
        for cube in cubes:
            shutil.copy(cube, Merged+'/'+date+'_'+obsid)

    os.chdir(Merged)

    n=0
    for cubes in listsOfCubes:

        shiftlist = []
        os.chdir(Merged+'/'+obsidlist[n])
        iraffunctions.chdir(Merged+'/'+obsidlist[n])
        # Set the zero point p and q offsets to the p and q offsets of the first cube in each sequence.
        header = pyfits.open(cubes[0])
        p0 = header[0].header['POFFSET']
        q0 = header[0].header['QOFFSET']
        suffix = cubes[0][-8:-5]
        if os.path.exists('transcube'+suffix+'.fits'):
            if not over:
                logging.info('Output already exists and -over- not set - skipping im3dtran')
            if over:
                os.remove('transcube'+suffix+'.fits')
                iraf.im3dtran(input = cubes[0]+'[SCI][*,*,-*]', new_x=1, new_y=3, new_z=2, output = 'transcube'+suffix)
        else:
            iraf.im3dtran(input = cubes[0]+'[SCI][*,*,-*]', new_x=1, new_y=3, new_z=2, output = 'transcube'+suffix)
        shiftlist.append('cube'+suffix+'.fits')
        iraffunctions.chdir(os.getcwd())

        foff = open('offsets.txt', 'w')
        foff.write('%d %d %d\n' % (0, 0, 0))
        foff.close()

        for i in range(len(cubes)):
            # Skip the first cube!
            if i == 0:
                continue
            header2 = pyfits.open(cubes[i])
            suffix = cubes[i][-8:-5]
            # find the p and q offsets of the other cubes in the sequence
            poff = header2[0].header['POFFSET']
            qoff = header2[0].header['QOFFSET']
            # calculate the difference between the zero point offsets and the offsets of the other cubes and convert that to pixels
            pShift = round((poff - p0)/xPixScale)
            qShift = round((qoff - q0)/yPixScale)
            # write all offsets to a text file (keep in mind that the x and y offsets use different pixel scales)
            foff = open('offsets.txt', 'a')
            foff.write('%d %d %d\n' % (int(pShift), 0, int(qShift)))
            foff.close()
            if os.path.exists('transcube'+suffix+'.fits'):
                if not over:
                    logging.info('Output already exists and -over- not set - skipping im3dtran')
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
                logging.info('Output already exists and -over- not set - skipping imcombine')
        else:
            iraf.imcombine('transcube*.fits', output = 'cube_merged.fits',  combine = 'median', offsets = 'offsets.txt')
        if os.path.exists('out.fits'):
            if over:
                os.remove('out.fits')
                iraf.im3dtran(input='cube_merged[*,-*,*]', new_x=1, new_y=3, new_z=2, output = 'out.fits')
                iraf.fxcopy(input=cubes[0]+'[0], out.fits', output = obsidlist[n]+'_merged.fits')
            else:
                logging.info('Output already exists and -over- not set - skipping final im3dtran')
        else:
            iraf.im3dtran(input='cube_merged[*,-*,*]', new_x=1, new_y=3, new_z=2, output = 'out.fits')
            iraf.fxcopy(input=cubes[0]+'[0], out.fits', output = obsidlist[n]+'_merged.fits')
        mergedCubes.append(obsidlist[n]+'_merged.fits')
        n+=1
        os.chdir(Merged)

    # Copy the merged observation sequence data cubes to the Merged directory.
    for i in range(len(mergedCubes)):
        shutil.copy(Merged+'/'+obsidlist[i]+'/'+mergedCubes[i], './')

    # Merge all the individual merged observation sequence data cubes.
    # TODO: test. Still untested.
    if len(mergedCubes)>1:
        os.chdir(Merged)
        iraffunctions.chdir(Merged)
        gratlist = []
        for i in range(len(mergedCubes)):
            cubeheader = pyfits.open(mergedCubes[i])
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
                    logging.info('Output exists and -over- not set - skipping final cube merge')
            else:
                iraf.imcombine(inputstring, output = 'temp_merged'+gratlist[n][0]+'.fits', combine = 'median', offsets = 'waveoffsets'+grat[0]+'.txt')
                iraf.fxcopy(input=newcubelist[0]+'[0], temp_merged'+gratlist[n][0]+'.fits', output = 'TOTAL_merged'+gratlist[n][0]+'.fits')


#####################################################################################
#                                        FUNCTIONS                                  #
#####################################################################################


def waveshift(cubelist, grat):
    cubeheader0 = pyfits.open(cubelist[0])
    wstart0 = cubeheader0[1].header['CRVAL3']
    fwave = open('waveoffsets{0}.txt'.format(grat[0]), 'w')
    fwave.write('%d\t%d\t%d\n' % (0., 0., 0.,))
    for i in range(len(cubelist)):
        cubeheader = pyfits.open(cubelist[i])
        wstart = cubeheader[1].header['CRVAL3']
        wdelt = cubeheader[1].header['CD3_3']
        waveoff = int(round((wstart0-wstart)/wdelt))
        fwave.write('%d\t%d\t%d\n' % (0., 0., waveoff))
    fwave.close()

#---------------------------------------------------------------------------------------------------------------------------------------#

if __name__ == '__main__':
    pass
