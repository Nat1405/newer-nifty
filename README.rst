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


How to Submit Bugs and Requests
-------------------------------

Very important: **do not submit a Gemini help desk ticket!**.

If you want to report a problem, use the `Gemini Data Reduction Forum thread <http://drforum.gemini.edu/topic/nifs-python-data-reduction-pipeline/>`
or create an issue in this repo.

Installation
============

.. 1. Install Astroconda. Instructions can be found on Gemini's website `here. <http://www.gemini.edu/node/12665>`
.. This will work but doesn't guarantee an identical pipeline every time.
1. Make sure you have Anaconda installed. We tested Nifty with Anaconda 4.4.0.
   You can grab the latest version `here<https://www.continuum.io/downloads>`
   **Important: do not activate an environment yet. We will create a new one in step 5.**
2. Make sure your terminal is using a bash shell. This should print something similar to /bin/bash.

.. code-block:: text

    echo $SHELL

2. Download the latest release of Nifty from `github.<https://github.com/Nat1405/newer-nifty/releases>`
3. Unpack the .zip or .tar file.
4. Within a terminal change into the unpacked Nifty directory. When you type "ls" you should see
   several files like "Nifty.py, nifsSort.py and environment-file.txt.".
5. From the spec-file-osx-64.txt create a new conda environment. This helps ensure you are
   using identical python modules to those used during testing. For more info on creating
   identical environments see `here.<https://conda.io/docs/using/envs.html#build-identical-conda-environments>`
.. code-block:: text

    conda create --name niftyconda --file spec-file-osx-64.txt

6. Activate the new "niftyconda" environment.

..code-block:: text

    source activate niftyconda

.. Insert photo of the new prompt.

You should see (niftyconda) appear before your shell prompt.

You're ready to begin reducing data!

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
|  |____ generate_response_curve.py
|  |____ hk.txt
|  |____ nftelluric_modified.cl
|_ .gitignore
|_ LICENSE
|_ README.rst
|_ spec-file-osx-64.txt

*Nifty.py is the main control script of the pipeline.*

Quick Start
===========

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

Input
=====

You can provide input to Nifty in three ways:

- Interactive input
- A user_options.json file
- Command line arguments

To provide interactive input run Nifty with no command line options by typing:

.. code-block:: text

   python Nifty.py

Note that the data reduction parameters are saved to a new user_options.json file
at the end of an interactive input session.

To have Nifty load its parameters from a user_options.json use the -r or -l command line arguments. These arguments are equivalent.

.. code-block:: text

   python Nifty.py -r

or:

.. code-block:: text

   python Nifty.py -l

Command Line Arguments
----------------------

Nifty supports several command line arguments. Using these with a user_options.json input file
makes Nifty integrate well with shell scripts.

Nifty may be invoked with the following command line arguments:

**-l**
  Load. Load data reduction parameters from a user_options.json file.
**-r**
  Repeat. Repeat the last data reduction, loading parameters from a user_options.json file.
  Equivalent to -l, Load.
**-f**
  Full automatic run. Do a full automatic data reduction copying parameters from the included default_input.json.

Notes
=====

Object and Sky frame differentiation
------------------------------------

If the sorting script does not create a skylist in the object or telluric observation
directories this means that the offsets between sky frames and object frames were smaller
than expected. A skylist can be manually created and saved in the appropriate directory, or
the limit placed on the offset can be changed. In sort.py the limit set on "rad" can be lowered in
lines 194, 245, and 492 for object sky images and in lines 198, 249, and 495 for telluric sky images.

H-Line Removal
--------------

See hline_removal.rst for more info.

Interactive Merging
-------------------

Cubes can be shifted using QFits View (this is currently necessary for
very faint objects) and then combined using nifsMerge.py by prepending the name of each
file with the prefix "shif" and saving them in the observation directory (where the reduced science data is stored).

Merging
-------

.. TODO(nat): improve this.

One can use custom offsets for each cube to merge by specifying use_pq_offsets==False.
The pipeline will pause and wait for you to create an appropriate offsets.txt in the appropriate
directory.

Recipes
=======

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
