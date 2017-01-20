import pyfits
import numpy as np
from scipy.interpolate import interp1d
from scipy import arange, array, exp
import os, glob
import pylab as pl

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
        #bblist = [image.strip() for image in bblist]
        

        tempDir = obsDir.split(os.sep)
        if tempDir[-1] in objlist:
            os.chdir(obsDir)
            scilist = glob.glob('c*.fits')
            for image in scilist:
                if image.replace('ctfbrgn','').replace('.fits', '') in objlist:
                    if os.path.exists(image[0]+'p'+image[1:]):
                        if not over:
                            print 'Output already exists and -over- not set - skipping telluric correction and flux calibration'
                            continue
                        if over:
                            os.remove(image[0]+'p'+image[1:])
                            pass
                    np.set_printoptions(threshold=np.nan)


                    # read in cube data
                    cube, cubewave = readCube(image)
                    
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
                        print "No airmass found in header. No airmass correction being performed on "+image
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
                        print "No airmass found in header. No airmass correction being performed on "+image
                        airmcor= False
    
                    if airmcor:
                        amcor = sciairmass/telairmass
                                
                    for i in range(len(effspec)):
                        if effspec[i]>0. and effspec[i]<1.:
                            effspec[i] = np.log(effspec[i])
                            effspec[i] *=amcor
                            effspec[i] = np.exp(effspec[i])

                    # divide each spectrum in the cubedata array by the efficiency spectrum
                    print image
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
                    cube.writeto(image[0]+'p'+image[1:], output_verify='ignore')
