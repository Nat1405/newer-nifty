# Nifty
A Python Data Reduction Pipeline for Gemini-North Near-Infrared Integral Field Spectrometer (NIFS)

This is a new data reduction python pipeline that uses the GEMINI IRAF package to reduce NIFS data. It is offers that complete data reduction process from sorting the data to producing a final combined flux calibrated and wavelength calibrated cube with the full S/N for a science target.

This pipeline is open source, but is not supported by Gemini Observaory.

Any feedback and comments (mbusserolle@gemini.edu) are welcome !

________________________________________________________________________________________________________________________________________
----------------------------------------------------------------------------------------------------------------------------------------

COPYRIGHT

For more details, please read the LICENSE.

________________________________________________________________________________________________________________________________________
----------------------------------------------------------------------------------------------------------------------------------------

HOW TO SUBMIT BUGS AND REQUESTS

Very important: DO NOT SUBMIT A GEMINI HELPDESK TICKET.
If you want to report a problem, use the Gemini Data Reduction Forum thread  
(http://drforum.gemini.edu/topic/nifs-python-data-reduction-pipeline/) or create an issue in this repo.

________________________________________________________________________________________________________________________________________
----------------------------------------------------------------------------------------------------------------------------------------

INSTALLATION

1. Install the Gemini IRAF package (http://www.gemini.edu/sciops/data-and-results/processing-software). Requirements for the Gemini IRAF package can be found at  : http://www.gemini.edu/sciops/data-and-results/processing-software/requirements

2. Nifty is composed of these necessary scripts (all need to be located in the same directory) which are found in this repo:

Main.py
sort.py
calibration.py
nifsScience.py
nifsFluxCalib.py
nifsTelluric.py
nifsMerge.py
defs.py

The following files need to be located in the same directory as the scripts:

1.   vega_ext.fits
2.   starstemp.txt

MANDATORY COMMAND LINE OPTIONS

-d   or   --date		to specify the date when the data were observed; e.g. YYYYMMDD (used ONLY within the GEMINI network)

-p   or    --program	   	to specify the program number of the observed data; e.g. GN-2013B-Q-109 (used ONLY within the GEMINI network)
				program number can also be specified together with date to reduce data from a specific night of an observing program; e.g. -p GN-2013B-109 -d 20131010
-q   or    --path		to specify the path of the directory where the raw files are stored; e.g. users/name/reduction/Raw

OTHER COMMAND LINE OPTIONS

-o   or   --over		if over is specified then old files will be overwritten during the data reduction

-c   or   --copy		if specified then the data will be copied from /net/mko-nfs/sci/dataflow (used ONLY within the GEMINI network)

-s   or    --sort		if specified then the data will be sorted and file lists (i.e. objlist, skylist, flatlist)  will be created; data is sorted as follows:
				SCIENCE:	Object Name/Date/Grating/OBSID	e.g.  HD14004/20100401/K/obs107
				TELLURIC:   Sci Object Name/Date/Grating/Tellurics/OBSID        e.g.  HD14004/20100401/K/Tellurics/obs109
				CALIBRATIONS:   Sci Object Name/Date/Calibrations         e.g.  HD14004/20100401/Calibrations	  		   	
-r   or   --noreduce	   	if specified then the baseline calibrations will not be reduced; this option is useful when the calibration data has already been reduced
-a   or  --redstart                   to specify the starting step of the baseline calibration reductions; any integer value from 1 to 3 may be chosen; the default is 1; SEE BASELINE CALIBRATION REDUCTION STEPS BELOW
-z   or   --redstop		to specify the stopping step of the baseline calibration reductions; any integer value from 1 to 3 may be chosen; the default is 6; SEE BASELINE CALIBRATION REDUCTION STEPS BELOW
-k  or   --notelred		if specified then the telluric data will not be reduced according to the science and telluric reduction steps below
-g  or	 --nofluxcal          if specified then the final flux calibrated telluric (with hydrogen lines removed) will not be produced, which means that a telluric correction cannot be performed
-t   or   --telcorr	   	if specified then no H line removal, flux calibrations, or telluric corrections on science data will be executed
-e  or   --stdspectemp   	to specify the spectral type or temperature of the standard star; e.g. for a spectral type -e A0V; for a temperature -e 8000
-f   or   --stdmag	      	to specify the K band magnitude of the standard star; e.g. 5.4
				if you do not wish to do a flux calibration then enter -f -1
-l   or   --hline_method			to specify the method for removing the H lines from the telluric spectra; the default is vega
				the options are: none, vega, linefit_auto, linefit_manual, vega_tweak, and linefit_tweak
				none: does no H line removal
				vega: uses vega's spectrum to remove H lines with the iraf task "telluric"
				linefit_auto: automatically fit Lorentz profiles to lines
				linefit_manual: allows for interactive fitting of lines
				vega_tweak: uses the vega removal method and then allows for interactive tweaking
				linefit_tweak: uses the linefit_auto method and then allows for interactive tweaking
-i   or   --hinter                       if specified then the removal of H lines from the telluric spectra will be done interactively
-y  or   --continter		if specified then fitting a continuum to the telluric spectra will be done interactively
-w  or   --telinter   	      if specified then the telluric correction will be done interactively. The interactive correction is done in IRAF and the non-interactive correction is done in Python
-n  or   --sci  		if specified then the science data will not be reduced; this is useful when the science data has already been reduced and you want to add a telluric correction or produce a final merged cube
-b   or   --scistart	    	to specify the starting step of the science data reductions; any integer value from 1 to 9 may be chosen; the default is one; SEE SCIENCE AND TELLURIC DATA REDUCTION STEPS BELOW
-x   or  --scistop		to specify the stopping step of the science data reductions; any integer value from 1 to 9 may be chosen; the default is one; SEE SCIENCE AND TELLURIC DATA REDUCTION STEPS BELOW
-m  or  --merge		if specified then the data cubes produced in the science data reduction will not be merged


BASELINE CALIBRATION REDUCTION STEPS (these are the steps in calibration.py)

1      Determine the shift to the MDF file
2      Produce a normalized spectral flatfield and bad pixel mask
3      Prepare and combine the arc darks (if more than one)
4      Prepare, combine (if more than one), flat field, and cut the arc
5      Determine the wavelength solution
6      Determine the spatial curvature and distortion in the Ronchi flat

SCIENCE AND TELLURIC DATA REDUCTION STEPS (these are the steps in nifsScience.py)

1	Prepare raw data
2	Combine multiple sky frames for the telluric data and copy sky frames for the science data
3	Sky subtraction
4	Flat field
5	Correct bad pixels
6	Compute 2D dispersion and distortion maps
7	Rectify the 2D spectra
8	Create combined telluric spectrum (done interactively when telluric data is reduced) or apply telluric correction (interactively) and flux calibration (telluric correction and flux calibration are performed when science data is reduced)
9          Make  3D data cube
MERGING is found in a separate script called nifsMerge.py and is performed after the science data has been reduced

NOTES:

OBJECT AND SKY FRAMES

If the sorting script does not create a skylist in the object or telluric observation directories this means that the offsets between sky frames and object frames were smaller than expected. A skylist can be manually created and saved in the appropriate directory, or the limit placed on the offset can be changed. In sort.py the limit set on "rad" can be lowered in lines 194, 245, and 492 for object sky images and in lines 198, 249, and 495 for telluric sky images.

TELLURIC CORRECTION

The extraction of 1-D spectrum (used only in the telluric correction) must be done interactively. The diameter of the circular extraction aperture can be changed in nifsScience.py in line 383 by changing the value of "diam."

H-LINE REMOVAL

The H-line removal can be done non-interactively, but it is advised that this be performed interactively and using the "vega_tweak" method in order to accurately scale the vega spectrum.
In the interactive mode for the initial scaling and call to "telluric" these are the cursor keys and colon commands (from http://iraf.net/irafhelp.php?val=telluric&help=Help+Page):
? - print help
a - automatic RMS minimization within sample regions
c - toggle calibration spectrum display
d - toggle data spectrum display
e - expand (double) the step for the current selection
q - quit
r - redraw the graphs
s - add or reset sample regions
w - window commands (see :/help for additional information)
x - graph and select from corrected shifted candidates
y - graph and select from corrected scaled candidates

:help           - print help
:shift  [value] - print or reset the current shift
:scale  [value] - print or reset the current scale
:dshift [value] - print or reset the current shift step
:dscale [value] - print or reset the current scale step
:offset [value] - print or reset the current offset between spectra
:sample [value] - print or reset the sample regions
:smooth [value] - print or reset the smoothing box size

To decrease the scale or shift value, the cursor must be under the spectrum and to increase these values the cursor must be above the spectrum. Occasionally, this will not work in which case the value can be designated with a colon command.

If using the vega_tweak or other interactive line removal method, the lines can be removed in a splot environment (commands found here: http://stsdas.stsci.edu/cgi-bin/gethelp.cgi?splot.hlp). The most useful commands for this are:

k + (g, l or v)
Mark two continuum points and fit a single line profile. The second key selects the type of profile: g for gaussian, l for lorentzian, and v for voigt. Any other second key defaults to gaussian. The center, continuum at the center, core intensity, integrated flux, equivalent width, and FWHMs are printed and saved in the log file. See d for fitting multiple profiles and - to subtract the fit.

w
Window the graph. For further help type ? to the "window:" prompt or see help under gtools . To cancel the windowing use a.

It is necessary to press 'i' before 'q' once the h-lines have been removed in order to save the changes.


MERGING

Cubes can be shifted using QFits View (this is currently necessary for
very faint objects) and then combined using nifsMerge.py by prepending the name of each file with the prefix "shif" and saving them in the observation directory (where the reduced science data is stored).  

EXAMPLE COMMAND LINE PROMPTS

1. To perform sorting, calibration data reductions, and science reductions without the telluric correction and without producing a merged cube:
python Main.py -q users/name/reduction/Raw -t -k -m

2. To perform sorting, calibration data reductions, and science reductions without telluric correction and produce a merged cube:
python Main.py -q users/name/reduction/Raw -t -k

3. To perform sorting, calibration data reductions, and science reductions without the telluric correction, no flux calibration, and produce a merged cube:
python Main.py -q users/name/reduction/Raw -f -1

4. To perform sorting, calibration data reductions, and science reductions with the telluric correction (interactively), flux calibration, and produce a merged cube:
python Main.py -q users/name/reduction/Raw -w

5. To start the script by producing a merged cube (all the science data must already be reduced):
python Main.py -q users/name/reduction/Raw -s -r -n -t -k

6. To start the script by performing the telluric correction and produce a merged cube (assuming the telluric data and science data have already been reduced)
python Main.py -q users/name/reduction/Raw -s -r -k -b 8
