Nifty
=====
A Python Data Reduction Pipeline for the Gemini-North Near-Infrared Integral
Field Spectrometer (NIFS).

This is a new data reduction python pipeline that uses Astroconda and the Gemini
Iraf Package to reduce NIFS data. It offers a complete data reduction process from
sorting the data to producing a final flux calibrated and wavelength calibrated
combined cube with the full S/N for a science target.

This pipeline is open source but is not supported by Gemini Observatory.

Any feedback and comments (mbusserolle@gemini.edu) are welcome!

Copyright
---------

For more details, please read the LICENSE.


HOW TO SUBMIT BUGS AND REQUESTS
-------------------------------

Very important: DO NOT SUBMIT A GEMINI HELPDESK TICKET.
If you want to report a problem, use the Gemini Data Reduction Forum thread
(http://drforum.gemini.edu/topic/nifs-python-data-reduction-pipeline/) or create an issue in this repo.

Installation
============

1. Install Astroconda. Instructions can be found on Gemini's website `here. <http://www.gemini.edu/node/12665>`
2. Download the latest release of Nifty from `here.<https://github.com/Nat1405/newer-nifty/releases>`
3. Unpack the .zip or .tar file.
4. In a terminal change into the unpacked Nifty directory. When you type "ls" you should see
   several files like "Nifty.py, nifsSort.py, etc.".
5. TODO(nat): add a way to verify the download with an md5.
5. You're ready to go! Launch Nifty by typing "python Nifty.py" or making it executable and typing "./Nifty.py".

You should see the following directory structure:

|_ Nifty.py
|_ nifsSort.py
|_ nifsBaselineCalibration.py
|_ nifsReduce.py
|_ nifsMerge.py
|_ nifsDefs.py
|____ runtimeData/
|  |____ h_wave.data
|  |____ j_wave.data
|  |____ k_wave.data
|____ docs/
|  |____ nifs_pipeline_june_2015.pdf
|____ extras/
|  |____ geminiSort.py
|____ tests/
   |____ generate_response_curve.py
   |____ hk.txt
   |____ nftelluric_modified.cl


Quick Start
-----------

To launch Nifty with interactive input, type:

.. code-block:: text

   python Nifty.py

Nifty will let you select parameters for the data reduction. Press enter to accept
the default options.

To do a full reduction accepting all the defaults, you can either type:

.. code-block:: text

   python Nifty.py -f

or type "yes" at the first interactive prompt that asks if you would like to do a
full default reduction.

Overview of Major Reduction Steps
---------------------------------



Note:
=====

OBJECT AND SKY FRAMES

If the sorting script does not create a skylist in the object or telluric observation
directories this means that the offsets between sky frames and object frames were smaller
than expected. A skylist can be manually created and saved in the appropriate directory, or
the limit placed on the offset can be changed. In sort.py the limit set on "rad" can be lowered in
lines 194, 245, and 492 for object sky images and in lines 198, 249, and 495 for telluric sky images.

H-Line Removal
--------------

The H-line removal can be done non-interactively, but it is advised that this be performed
interactively and using the "vega_tweak" method in order to accurately scale the vega spectrum.
In the interactive mode for the initial scaling and call to "telluric" these are the cursor keys
and colon commands (from http://iraf.net/irafhelp.php?val=telluric&help=Help+Page):

- ? - print help
- a - automatic RMS minimization within sample regions
- c - toggle calibration spectrum display
- d - toggle data spectrum display
- e - expand (double) the step for the current selection
- q - quit
- r - redraw the graphs
- s - add or reset sample regions
- w - window commands (see :/help for additional information)
- x - graph and select from corrected shifted candidates
- y - graph and select from corrected scaled candidates

- :help           - print help
- :shift  [value] - print or reset the current shift
- :scale  [value] - print or reset the current scale
- :dshift [value] - print or reset the current shift step
- :dscale [value] - print or reset the current scale step
- :offset [value] - print or reset the current offset between spectra
- :sample [value] - print or reset the sample regions
- :smooth [value] - print or reset the smoothing box size

To decrease the scale or shift value, the cursor must be under the spectrum and to increase
these values the cursor must be above the spectrum. Occasionally, this will not work in which
case the value can be designated with a colon command.

If using the vega_tweak or other interactive line removal method, the lines can be removed
in a splot environment (commands found here: http://stsdas.stsci.edu/cgi-bin/gethelp.cgi?splot.hlp).
The most useful commands for this are:

- k + (g, l or v)
Mark two continuum points and fit a single line profile. The second key selects the
type of profile: g for gaussian, l for lorentzian, and v for voigt. Any other second key
defaults to gaussian. The center, continuum at the center, core intensity, integrated flux,
equivalent width, and FWHMs are printed and saved in the log file. See d for fitting multiple profiles and - to subtract the fit.

- w
Window the graph. For further help type ? to the "window:" prompt or see help under gtools.
To cancel the windowing use a.

It is necessary to press 'i' before 'q' once the h-lines have been removed in order to save the changes.


Interactive Merging
-------------------

Cubes can be shifted using QFits View (this is currently necessary for
very faint objects) and then combined using nifsMerge.py by prepending the name of each
file with the prefix "shif" and saving them in the observation directory (where the reduced science data is stored).

Some Recipes
------------

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
