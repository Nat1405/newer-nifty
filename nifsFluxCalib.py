import os, logging
import sgmllib
import sys
import urllib, sgmllib
import re
import numpy
from pyraf import iraf
iraf.gemini()
iraf.nifs()
iraf.gnirs()
iraf.gemtools()
import numpy as np
import pylab as pl
from pyraf import iraffunctions
import pyfits
from pyfits import getdata, getheader
from nifsDefs import convertRAdec, datefmt, writeList

#--------------------------------------------------------------------#
#                                                                    #
#     FLUX CALIBRATION                                               #
#                                                                    #
#     This module contains all the functions needed to remove        #
#     H lines from the standard star and do the flux calibration.    #
#                                                                    #
#                                                                    #
#    COMMAND LINE OPTIONS                                            #
#    If you wish to skip this script enter -t in the command line    #
#    Specify a spectral type or temperature with -e                  #
#    Specify a magniture with -f                                     #
#    Specify an H line fitting method with -l (default is vega)      #
#    Specify interactive H line fitting with -i (default inter=no)   #
#    Specify interactive continuum fitting with -y (def inter=no)    #
#                                                                    #
#     INPUT:                                                         #
#     - reduced and combined standard star spectra                   #
#                                                                    #
#     OUTPUT:                                                        #
#     - reduced (H line and continuum fit) standard star spectra     #
#     - flux calibrated blackbody spectrum                           #
#                                                                    #
#--------------------------------------------------------------------#

iraf.gemini(_doprint=0, motd="no")
iraf.gnirs(_doprint=0)
iraf.imutil(_doprint=0)
iraf.onedspec(_doprint=0)
iraf.nsheaders('nifs',Stdout='/dev/null')

def start(telDirList, continuuminter, hlineinter, hline_method, spectemp, mag, over):
    """
#--------------------------------------------------------------------#
#                                                                    #
#     FLUX CALIBRATION                                               #
#                                                                    #
#     This module contains all the functions needed to remove        #
#     H lines from the standard star and do the flux calibration.    #
#                                                                    #
#                                                                    #
#    COMMAND LINE OPTIONS                                            #
#    If you wish to skip this script enter -t in the command line    #
#    Specify a spectral type or temperature with -e                  #
#    Specify a magniture with -f                                     #
#    Specify an H line fitting method with -l (default is vega)      #
#    Specify interactive H line fitting with -i (default inter=no)   #
#    Specify interactive continuum fitting with -y (def inter=no)    #
#                                                                    #
#     INPUT:                                                         #
#     - reduced and combined standard star spectra                   #
#                                                                    #
#     OUTPUT:                                                        #
#     - reduced (H line and continuum fit) standard star spectra     #
#     - flux calibrated blackbody spectrum                           #
#                                                                    #
#--------------------------------------------------------------------#
    """

    path = os.getcwd()
    # Set up the logging file
    FORMAT = '%(asctime)s %(message)s'
    DATEFMT = datefmt()
    logging.basicConfig(filename='main.log',format=FORMAT,datefmt=DATEFMT,level=logging.DEBUG)
    log = os.getcwd()+'/main.log'

    logging.info('##########################')
    logging.info('#                        #')
    logging.info('# Start Flux Calibration #')
    logging.info('#                        #')
    logging.info('##########################')

    print "telDirList= ", telDirList
    print " continuuminter=", continuuminter
    print "hlineinter= ", hlineinter
    print " hline_method=", hline_method
    print "spectemp= ", spectemp
    print " mag=", mag
    print " over=", over


    for telDir in telDirList:
        os.chdir(telDir)
        iraffunctions.chdir(telDir)

        # open and define standard star spectrum and its relevant header keywords
        try:
            standard = str(open('telluricfile', 'r').readlines()[0]).strip()
        except:
            print "No telluricfile found in ", telDir
            continue
        if not os.path.exists('objtellist'):
            print "No objtellist found in ", telDir
            continue

        telheader = pyfits.open(standard+'.fits')
        band = telheader[0].header['GRATING'][0]
        RA = telheader[0].header['RA']
        Dec = telheader[0].header['DEC']
        airmass_std = telheader[0].header['AIRMASS']
        temp1 = os.path.split(telDir)
        temp2 = os.path.split(temp1[0])
        # make directory PRODUCTS above the Telluric observation directory
        # telluric_hlines.txt is stored there
        if not os.path.exists(temp1[0]+'/PRODUCTS'):
            os.mkdir(temp1[0]+'/PRODUCTS')

        # defines 'name' that is passed to mag2mass
        if '-' in str(Dec):
            name = str(RA)+'d'+str(Dec)+'d'
        else:
            name = str(RA)+'d+'+str(Dec)+'d'

        # find standard star spectral type, temperature, and magnitude
        mag2mass(name, path, spectemp, mag, band)
        print " list", name, path, spectemp, mag, band

        # File for recording shift/scale from calls to "telluric"
        t1 = open('telluric_hlines.txt', 'w')

        # Remove H lines from standard star
        no_hline = False
        if os.path.exists("ftell_nolines"+band+'.fits'):
            if over:
                iraf.delete("ftell_nolines"+band+'.fits')
            else:
                no_hline = True
                print "Output file exists and -over- not set - skipping H line removal"

        if hline_method == "none":
            #need to copy files so have right names for later use
            iraf.imcopy(input=standard+'[sci,'+str(1)+']', output="ftell_nolines"+band, verbose='no')

        if hline_method == "none" and not no_hline:
            print ""
            print "***Removing intrinsic lines in standard star***"
            print ""

        if hline_method == "vega" and not no_hline:
            vega(standard, band, path, hlineinter, airmass_std, t1, log, over)

        if hline_method == "linefit_auto" and not no_hline:
            linefit_auto(standard, band)

        if hline_method == "linefit_manual" and not no_hline:
            linefit_manual(standard+'[sci,1]', band)

        if hline_method == "vega_tweak" and not no_hline:
            #run vega removal automatically first, then give user chance to interact with spectrum as well
            vega(standard,band, path, hlineinter, airmass_std, t1, log, over)
            linefit_manual("ftell_nolines"+band, band)

        if hline_method == "linefit_tweak" and not no_hline:
            #run Lorentz removal automatically first, then give user chance to interact with spectrum as well
            linefit_auto(standard,band)
            linefit_manual("ftell_nolines"+band, band)

        # make a list of exposure times from the science images that use this standard star spectrum for the telluric correction
        # used to make flux calibrated blackbody spectra
        objtellist = open('objtellist', 'r').readlines()
        objtellist = [image.strip() for image in objtellist]
        exptimelist = []
        for item in objtellist:
            if 'obs' in item:
                os.chdir(telDir)
                os.chdir('../../'+item)
            else:
                objheader = pyfits.open(item+'.fits')
                exptime = objheader[0].header['EXPTIME']
                if not exptimelist or exptime not in exptimelist:
                    exptimelist.append(int(exptime))

        os.chdir(telDir)
        for tgt_exp in exptimelist:

            # Make blackbody spectrum to be used in nifsScience.py
            file = open('std_star.txt','r')
            lines = file.readlines()
            #Extract stellar temperature from std_star.txt file , for use in making blackbody
            star_kelvin = float(lines[0].replace('\n','').split()[3])
            #Extract mag from std_star.txt file and convert to erg/cm2/s/A, for a rough flux scaling

            try:
                #find out if a matching band mag exists in std_star.txt
                if band == 'K':
                    star_mag = lines[0].replace('\n','').split()[2]
                    star_mag = float(star_mag)
                    flambda = 10**(-star_mag/2.5) * 4.28E-11
                if band == 'H':
                    star_mag = lines[1].replace('\n','').split()[2]
                    star_mag = float(star_mag)
                    flambda = 10**(-star_mag/2.5) * 1.133E-10
                if band == 'J':
                    star_mag = lines[2].replace('\n','').split()[2]
                    star_mag = float(star_mag)
                    flambda = 10**(-star_mag/2.5) * 3.129E-10
                print "flambda=", flambda

            except:
                #if not then just set to 1; no absolute flux cal. attempted
                flambda = 1
                print "No ", band, " magnitude found for this star. A relative flux calibration will be performed"
                print "star_kelvin=", star_kelvin
                print "star_mag=", star_mag

            effspec(telDir, standard, 'ftell_nolines'+band+'.fits', star_mag, star_kelvin, over)

            '''
            #account for standard star/science target exposure times
            std_exp = telheader[0].header['EXPTIME']
            flambda = flambda * (float(std_exp) / float(tgt_exp))

            #find the start and end wavelengths of the spectrum
            wstart = iraf.hselect(images=standard+'[SCI]', field='CRVAL1', expr='yes',  missing='INDEF', mode='al', Stdout=1)
            wstart = float(wstart[0].replace("'",""))
            wdelt = iraf.hselect(images=standard+'[SCI]', field='CD1_1', expr='yes',  missing='INDEF', mode='al', Stdout=1)
            wend = wstart + (2039 * float(wdelt[0].replace("'","")))

            #make a blackbody
            if over:
                if os.path.exists('blackbody'+str(tgt_exp)+'.fits'):
                    os.remove('blackbody'+str(tgt_exp)+'.fits')
                iraf.mk1dspec(input="blackbody"+str(tgt_exp),output="blackbody"+str(tgt_exp),ap=1,rv=0.0,z='no',title='',ncols=2040,naps=1,header='',wstart=wstart,wend=wend,continuum=1000,slope=0.0,temperature=star_kelvin,fnu='no',lines='',nlines=0,profile='gaussian',peak=-0.5,gfwhm=20.0,lfwhm=20.0,seed=1,comments='yes',mode='ql')
                    #scale it to the science target
                meana = iraf.imstat(images="blackbody"+str(tgt_exp), fields="mean", lower='INDEF', upper='INDEF', nclip=0, lsigma=3.0, usigma=3.0, binwidth=0.1, format='yes', cache='no', mode='al',Stdout=1)
                scalefac = flambda / float(meana[1].replace("'",""))
            elif not os.path.exists('blackbody'+str(tgt_exp)+'.fits'):
                iraf.mk1dspec(input="blackbody"+str(tgt_exp),output="blackbody"+str(tgt_exp),ap=1,rv=0.0,z='no',title='',ncols=2040,naps=1,header='',wstart=wstart,wend=wend,continuum=1000,slope=0.0,temperature=star_kelvin,fnu='no',lines='',nlines=0,profile='gaussian',peak=-0.5,gfwhm=20.0,lfwhm=20.0,seed=1,comments='yes',mode='ql')
                #scale it to the science target
                meana = iraf.imstat(images="blackbody"+str(tgt_exp), fields="mean", lower='INDEF', upper='INDEF', nclip=0, lsigma=3.0, usigma=3.0, binwidth=0.1, format='yes', cache='no', mode='al',Stdout=1)
                scalefac = flambda / float(meana[1].replace("'",""))
            else:
                print "Output file exists and -over- not set - skipping mk1dspec"

            if over:
                if os.path.exists("bbscale"+str(tgt_exp)+'.fits'):
                    os.remove("bbscale"+str(tgt_exp)+'.fits')
                iraf.imarith(operand1="blackbody"+str(tgt_exp), op="*", operand2=scalefac, result="bbscale"+str(tgt_exp),title='',divzero=0.0,hparams='',pixtype='',calctype='',verbose='no',noact='no',mode='al')
            elif not os.path.exists("bbscale"+str(tgt_exp)+'.fits'):
                iraf.imarith(operand1="blackbody"+str(tgt_exp), op="*", operand2=scalefac, result="bbscale"+str(tgt_exp),title='',divzero=0.0,hparams='',pixtype='',calctype='',verbose='no',noact='no',mode='al')
            else:
                print "Output file exists and -over- not set - skipping blackbody flux scaling"

            writeList("bbscale"+str(tgt_exp), "blackbodyfile", telDir)
            '''

    os.chdir(path)

#####################################################################################
#                                        FUNCTIONS                                  #
#####################################################################################

def mag2mass(name, path, spectemp, mag, band):
    """Find standard star spectral type, temperature, and magnitude
    """

    starfile = 'std_star.txt'
    kelvinfile = path+'/starstemp.txt'

    sf = open(starfile,'w')
    klf = open (kelvinfile)
    Kmag = ''
    Jmag = ''
    Hmag = ''

    # check to see if a spectral type or temperature has been given
    if spectemp:
        if not isinstance(spectemp[0], int):
            spectral_type = spectemp
            specfind = False
            tempfind = True
        else:
            kelvin = spectemp
            tempfind = False
            specfind = False
    else:
        specfind = True
        tempfind = True
    if mag:
        magfind = False
        if band=='K':
            Kmag=mag
        if band=='H':
            Hmag=mag
        if band=='J':
            Jmag=mag
    else:
        magfind = True

    if specfind or tempfind or magfind:
        #Construct URL based on standard star coords, execute SIMBAD query to find spectral type
        name = name.replace("+","%2b")
        name = name.replace("-", "%2D")
        start_name='http://simbad.u-strasbg.fr/simbad/sim-coo?Coord='
        end_name = '&submit=submit%20query&Radius.unit=arcsec&Radius=10'
        www_page = start_name+name+end_name
        f = urllib.urlopen(www_page)
        html2 = f.read()
        html2 = html2.replace(' ','')
        search_error = str(html2.split('\n'))


        #Exit if the lookup found nothing.
        if 'Noastronomicalobjectfound' in search_error:
            print "ERROR: no object was found at the coordinates you entered. You'll need to supply information in a file; see the manual for instructions."

        #If >1 object found, decrease search radius and try again
        if 'Numberofrows:' in search_error:
            start_name='http://simbad.u-strasbg.fr/simbad/sim-coo?Coord='
            end_name = '&submit=submit%20query&Radius.unit=arcsec&Radius=1'
            www_page = start_name+name+end_name
            f = urllib.urlopen(www_page)
            html2 = f.read()
            html2 = html2.replace(' ','')
            search_error = str(html2.split('\n'))

        #If that didn't return anything, exit and let the user sort it out
        if 'Noastronomicalobjectfound' in search_error:
            print "ERROR: didn't find a star at your coordinates within a search radius of 10 or 1 arcsec. You'll need to supply information in a file; see the manual for instructions."
            sys.exit()
        html2 = html2.split('\n')
        if specfind:
            count = 0
            aux = 0
            for line in html2:
                if (line[0:8] == 'Spectral') :
                    numi = aux + 5
                    count = 0
                    break
                else:
                    count += 1
                aux += 1
            spectral_type = str(html2[numi][0:3])
            if count > 0:
                print "ERROR: problem with SIMBAD output. You'll need to supply the spectral type or temperature in the command line prompt."
                sys.exit()


        if magfind:
            for line in html2:

                if 'Fluxes' in line:
                    i = html2.index(line)
                    break
            while 'IMGSRC' not in html2[i]:
                if all(s in html2[i] for s in ('K', 'C', '[', ']')):
                    index = html2[i].index('[')
                    Kmag = html2[i][1:index]
                if all(s in html2[i] for s in ('H', 'C', '[', ']')):
                    index = html2[i].index('[')
                    Hmag = html2[i][1:index]
                if all(s in html2[i] for s in ('J', 'C', '[', ']')):
                    index = html2[i].index('[')
                    Jmag = html2[i][1:index]
                i+=1
                if i>len(html2):
                    print "ERROR: problem with SIMBAD output. You'll need to supply the magniture in the command line prompt."
        if not Kmag:
            Kmag = 'nothing'
        if not Jmag:
            Jmag = 'nothing'
        if not Hmag:
            Hmag = 'nothing'
        if tempfind:
            #Find temperature for this spectral type in kelvinfile
            count = 0
            for line in klf:
                if '#' in line:
                    continue
                else:
                    if	spectral_type in line.split()[0]:
                        kelvin = line.split()[1]
                        count = 0
                        break
                    else:
                        count+=1

            if count > 0:
                print "ERROR: can't find a temperature for spectral type", spectral_type,". You'll need to supply information in a file; see the manual for instructions."
                sys.exit()

        if (Kmag or Jmag or Hmag) and Kmag!='x' and magfind:
            print "magnitudes retrieved OK"
            sf.write('k K '+Kmag+' '+kelvin+'\n')
            sf.write('h H '+Hmag+' '+kelvin+'\n')
            sf.write('j J '+Jmag+' '+kelvin+'\n')
            sf.write('j J '+Jmag+' '+kelvin+'\n')

        elif (Kmag or Jmag or Hmag) and Kmag!='x' and not magfind:
            sf.write('k K '+Kmag+' '+kelvin+'\n')
        elif Kmag=='x':
            print "WARNING: no magnitudes found for standard star. Doing relative flux calibration only."
            sf.write('k K N/A '+kelvin+' \n')
            sf.write('h H N/A '+kelvin+' \n')
            sf.write('j J N/A '+kelvin+' \n')
            sf.write('j J N/A '+kelvin+' \n')

    sf.close()
    klf.close()

#-------------------------------------------------------------------------------#

def write_line_positions(nextcur, var):
    """
    Write line x,y info to file containing Lorentz fitting commands for bplot
    """

    curfile = open(nextcur, 'w')
    i=-1
    for line in var:
        i+=1
        if i!=0:
            var[i]=var.split()
            var[i][2]=var[i][2].replace("',",'').replace("']", '')
        if not i%2 and i!=0:
            #even number, means RHS of H line
            #write x and y position to file, also "k" key
            curfile.write(var[i][0]+" "+var[i][2]+" 1 k \n")
            #LHS of line, write info + "l" key to file
            curfile.write(var[i-1][0]+" "+var[i-1][2]+" 1 l \n")
            #now repeat but writing the "-" key to subtract the fit
            curfile.write(var[i][0]+" "+var[i][2]+" 1 - \n")
            curfile.write(var[i-1][0]+" "+var[i-1][2]+" 1 - \n")
        curfile.write("0 0 1 i \n")
        curfile.write("0 0 q \n")
        curfile.close()

#-------------------------------------------------------------------------------#

def vega(spectrum, band, path, hlineinter, airmass, t1, log, over):
    """Use "telluric" to remove H lines from standard star, then remove normalization added by telluric
       specify the extension for vega_ext.fits from the band
    """
    if band=='K':
        ext = '1'
    if band=='H':
        ext = '2'
    if band=='J':
        ext = '3'
    if band=='Z':
        ext = '4'
    if os.path.exists("tell_nolines"+band+".fits"):
            if over:
                os.remove("tell_nolines"+band+".fits")
                tell_info = iraf.telluric(input=spectrum+"[1]", output='tell_nolines'+band, cal=path+'/vega_ext.fits['+ext+']', answer='yes', ignoreaps='yes', xcorr='yes', airmass = airmass, tweakrms='yes', inter=hlineinter, threshold=0.1, lag=3, shift=0., dshift=0.05, scale=.75, dscale=0.05, offset=0., smooth=1, cursor='', mode='al', Stdout=1)
            else:
                print "Output file exists and -over not set - skipping H line correction"
    else:
        tell_info = iraf.telluric(input=spectrum+"[1]", output='tell_nolines'+band, cal=path+'/vega_ext.fits['+ext+']', answer='yes', ignoreaps='yes', xcorr='yes', airmass = airmass, tweakrms='yes', inter=hlineinter, threshold=0.1, lag=3, shift=0., dshift=0.05, scale=1., dscale=0.05, offset=0, smooth=1, cursor='', mode='al', Stdout=1)

    # record shift and scale info for future reference
    t1.write(str(tell_info)+'\n')
    # need this loop to identify telluric output containing warning about pix outside calibration limits (different formatting)
    if "limits" in tell_info[-1].split()[-1]:
        norm=tell_info[-2].split()[-1]
    else:
        norm=tell_info[-1].split()[-1]

    if os.path.exists("ftell_nolines"+band+".fits"):
        if over:
            os.remove("ftell_nolines"+band+".fits")
            iraf.imarith(operand1='tell_nolines'+band, op='/', operand2=norm, result='ftell_nolines'+band, title='', divzero=0.0, hparams='', pixtype='', calctype='', verbose='yes', noact='no', mode='al')
        else:
            print "Output file exists and -over not set - skipping H line normalization"
    else:
        iraf.imarith(operand1='tell_nolines'+band, op='/', operand2=norm, result='ftell_nolines'+band, title='', divzero=0.0, hparams='', pixtype='', calctype='', verbose='yes', noact='no', mode='al')

#-------------------------------------------------------------------------------#

def linefit_auto(spectrum, band):
    """automatically fit Lorentz profiles to lines defined in existing cur* files
    Go to x position in cursor file and use space bar to find spectrum at each of those points
    """

    specpos = iraf.bplot(images=spectrum+'[SCI,1]', cursor='cur'+band, Stdout=1, StdoutG='/dev/null')
    specpose = str(specpos).split("'x,y,z(x):")
    nextcur = 'nextcur'+band+'.txt'
    # Write line x,y info to file containing Lorentz fitting commands for bplot
    write_line_positions(nextcur, specpos)
    iraf.delete('ftell_nolines'+band+'.fits,Lorentz'+band,ver="no",go_ahead='yes',Stderr='/dev/null')
    # Fit and subtract Lorentz profiles. Might as well write output to file.
    iraf.bplot(images=spectrum+'[sci,1]',cursor='nextcur'+band+'.txt', new_image='ftell_nolines'+band, overwrite="yes",StdoutG='/dev/null',Stdout='Lorentz'+band)

#-------------------------------------------------------------------------------#

def linefit_manual(spectrum, band):
    """ Enter splot so the user can fit and subtract lorents (or, actually, any) profiles
    """

    iraf.splot(images=spectrum, new_image='ftell_nolines'+band, save_file='../PRODUCTS/lorentz_hlines.txt', overwrite='yes')
    # it's easy to forget to use the 'i' key to actually write out the line-free spectrum, so check that it exists:
    # with the 'tweak' options, the line-free spectrum will already exists, so this lets the user simply 'q' and move on w/o editing (too bad if they edit and forget to hit 'i'...)
    while True:
        try:
            with open("ftell_nolines"+band+".fits") as f: pass
            break
        except IOError as e:
            print "It looks as if you didn't use the if key to write out the lineless spectrum. We'll have to try again. --> Re-entering splot"
            iraf.splot(images=spectrum, new_image='ftell_nolines'+band, save_file='../PRODUCTS/lorentz_hlines.txt', overwrite='yes')

#-------------------------------------------------------------------------------#

def effspec(telDir, standard, telnolines, mag, T, over):
    """
    This flux calibration method was adapted to NIFS
    """


    # define constants
    c=2.99792458e8
    h = 6.62618e-34
    k=1.3807e-23

    f0emp = lambda p, T: p[0]*np.log(T)**2+p[1]*np.log(T)+p[2]
    fnu = lambda x, T: (2.*h*(x**3)*(c**(-2)))/(np.exp((h*x)/(k*T))-1)
    flambda = lambda x, T: (2.*h*(c**2)*(x**(-5)))/((np.exp((h*c)/(x*k*T)))-1)

    print 'Input Standard spectrum for flux calibration is ', standard

    if os.path.exists('c'+standard+'.fits'):
        if not over:
            print 'Output already exists and -over- not set - calculation of efficiency spectrum'
            return
        if over:
            os.remove('c'+standard+'.fits')
            pass
    telluric = pyfits.open(telnolines)
    telheader = pyfits.open(standard+'.fits')
    band = telheader[0].header['GRATING'][0]
    exptime = float(telheader[0].header['EXPTIME'])
    telfilter = telheader[0].header['FILTER']

    # define wavelength array
    telwave = np.zeros(telheader[1].header['NAXIS1'])
    wstart = telheader[1].header['CRVAL1']
    wdelt = telheader[1].header['CD1_1']
    for i in range(len(telwave)):
        telwave[i] = wstart+(i*wdelt)

    if 'HK' in telfilter:
        coeff =[1.97547589e-02, -4.19035839e-01, -2.30083083e+01]
        lamc = 22000.
    if 'JH' in telfilter:
        coeff = [1.97547589e-02, -4.19035839e-01,  -2.30083083e+01]
        lamc = 15700.
    if 'ZJ' in telfilter:
        coeff = [0.14903624, -3.14636068, -9.32675924]
        lamc = 11100.

    lamc = telheader[0].header['WAVELENG']
    f0 = np.exp(f0emp(coeff, T))

    # create black body spectrum at a given temperature
    blackbody = (flambda(telwave*1e-10, T))*1e-7

    lamc_ind = np.where(telwave==min(telwave, key=lambda x:abs(x-lamc)))

    tel_bb = telluric[0].data/blackbody
    csb = tel_bb[lamc_ind[0]]
    cs =  telluric[0].data[lamc_ind[0]]

    effspec =  (tel_bb/exptime)*(cs/csb)*(10**(0.4*mag))*(f0)**-1
    print 'effspec =', effspec

    telheader[1].data = effspec
    telheader.writeto('c'+standard+'.fits',  output_verify='ignore')
    writeList('c'+standard, 'corrtellfile', telDir)

#telDirList = ['/Users/kklemmer/CGCG448-020_SourceC_TEL/20090826/K/Tellurics/obs47']

#start(telDirList, False, False, 'vega', False, False, True)
