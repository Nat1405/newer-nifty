Nifty
=====

.. image:: https://zenodo.org/badge/93109208.svg
   :alt: DOI of the latest release. See releases.
   :target: https://zenodo.org/record/852696#.WaWmr5PyhMA
.. image:: https://readthedocs.org/projects/newer-nifty/badge/?version=latest
   :alt: Nifty's documentation, hosted on ReadtheDocs.
   :target: http://newer-nifty.readthedocs.io/en/latest/
.. image:: http://img.shields.io/badge/powered%20by-AstroPy-orange.svg?style=flat
   :alt: Nifty uses Astropy! Here is a link to the project webpage:
   :target: http://www.astropy.org/

A Python Data Reduction Pipeline for the Gemini-North Near-Infrared Integral
Field Spectrometer (NIFS).

Full documentation: `ReadTheDocs <http://newer-nifty.readthedocs.io/en/latest/>`_.

This is a new data reduction Python pipeline that uses Astroconda and the Gemini
IRAF Package to reduce NIFS data. It offers a complete data reduction process from
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

If you want to report a problem, use the `Gemini Data Reduction Forum thread <http://drforum.gemini.edu/topic/nifs-python-data-reduction-pipeline/>`_
or create an issue in this repo.

Installation
============

Pre-Requisites
--------------
Make sure you have the latest version of Gemini Astroconda installed, have activated an Astroconda environment and have set up PYRAF.
You can find instructions for installing Astroconda `here <https://astroconda.readthedocs.io/en/latest/>`_.

Installing
----------
From PyPi.org:

.. code-block:: text

    pip install Nifty4NIFS

.. TODO(nat): implement these instructions.
*Coming Soon: Instructions for installing in Developer mode.*

.. code-block:: text

    Not implemented yet.

Quick Start
===========

To run Nifty, getting data reduction parameters from an interactive input session:

.. code-block:: text

   runNifty -i

To run Nifty in full-automatic mode with default input parameters, provide the -f flag
and a full local path to the raw data or a Gemini Program ID string (Eg: GN-2013A-Q-62).

.. code-block:: text

   runNifty -f <data_location>


Running Nifty
=============

The runNifty command should now be active. You can now run Nifty from any directory to do either a
full or partial data reduction. Nifty is launched by typing the runNifty command with the name of a
configuration file and optional command line options. Typing runNifty without any arguments lists the
syntax and available options.

To get available options:

.. code-block:: text

   runNifty

To show help:

.. code-block:: text

   runNifty -h

To run Nifty, populating a configuration file interactively:

.. code-block:: text

   runNifty -i

To run Nifty by supplying your own configuration file:

.. code-block:: text

   runNifty <configurationfile.cfg>

To do a full automatic data reduction with default options:

.. code-block:: text

   runNifty -f <pathOrProgramID>

To redo the last data reduction, reading the config file saved at the beginning of the most recent reduction:

.. code-block:: text

  runNifty -f


Input
=====

You can provide input to Nifty in three ways:

- Interactive input
- A runtimeData/user_options.json file
- Command line arguments

To provide interactive input run Nifty with no command line options by typing:

.. code-block:: text

   python Nifty.py

Note that the data reduction parameters are saved to a new runtimeData/user_options.json file
at the end of an interactive input session.

To have Nifty load its parameters from a runtimeData/user_options.json use the -r or -l command line arguments. These arguments are equivalent.

.. code-block:: text

   python Nifty.py -r

or:

.. code-block:: text

   python Nifty.py -l

Practical Examples
==================

Observations of Titan
---------------------

Recipe used: defaultConfig.cfg

Observations of a Moderate Redshift Galaxy
------------------------------------------

Recipe used: defaultConfig.cfg

Let's reduce NIFS data of a moderate redshift galaxy, located at z ~ 1.284. This is a faint target, so after making
individual cubes we use the reported telescope P and Q offsets to blindly merge our final cubes.

As this program is out of its proprietary period and available on the Gemini Public Archive, we can use the defaultConfig.cfg configuration
file and specify its program ID to reduce it.

.. code-block:: text

   runNifty -f GN-2013A-Q-62

We could also launch the reduction from a provided configuration file.


Contents of the configuration file:

.. code-block:: text

   TODO(nat): When finalized fill this out!

To launch the reduction:

.. code-block:: text

   runNifty <configurationFile>






Editable Control Files
======================

At several points Nifty reads and writes data from textfiles. These files are found in the runtimeData/
directory. They are:

Modifed line lists; we used calibration line lists from `GNIRS<http://www.gemini.edu/sciops/instruments/gnirs/calibration/arc-lamp-ids>`_
- h_test_one_argon.dat
A modified list of wavelength calibration lines in the H band that we found worked well.
- j_test_one_argon.dat
A modified list of wavelength calibration lines in the J band that we found worked well.
- k_test_two_argon.dat
A modified list of wavelength calibration lines in the K band that we found worked well.
- new_starstemp.txt
Effective temperatures for each spectral type are stored in this.
- vega_ext.fits
Spectra of Vega in the z, J, H and K bands are included in the 4 extensions of this.
-runtimeData/user_options.json saves the parameters of the latest data reduction. **It is updated after each data reduction.**



Notes
=====

Object and Sky frame differentiation
------------------------------------

If the sorting script does not create a skylist in the object or telluric observation
directories this means that the offsets between sky frames and object frames were smaller
than expected. A skyframelist can be manually created and saved in the appropriate directory, or
the limit placed on the offset can be changed. To lower the limit manually do a search in nifsSort.py
for "skyframelist.append(entry)" and change the <= <value_in_arcseconds> to something new.

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
**These are pretty much all depreciated.** TODO(nat): update these.

We have built several data reduction recipes that you may find useful. These consist of
runtimeData/user_options.json files that are loaded with the -l flag.

1. To perform sorting, calibration data reductions, and science reductions without the telluric correction and without producing a merged cube:

.. code-block:: text

    python Nifty.py -q users/name/reduction/Raw -t -k -m

2. To perform sorting, calibration data reductions, and science reductions without telluric correction and produce a merged cube:

.. code-block:: text

    python Nifty.py -q users/name/reduction/Raw -t -k

3. To perform sorting, calibration data reductions, and science reductions without the telluric correction, no flux calibration, and produce a merged cube:

.. code-block:: text

    python Nifty.py -q users/name/reduction/Raw -f -1

4. To perform sorting, calibration data reductions, and science reductions with the telluric correction (interactively), flux calibration, and produce a merged cube:

.. code-block:: text

    python Nifty.py -q users/name/reduction/Raw -w

5. To start the script by producing a merged cube (all the science data must already be reduced):

.. code-block:: text

    python Nifty.py -q users/name/reduction/Raw -s -r -n -t -k

6. To start the script by performing the telluric correction and produce a merged cube (assuming the telluric data and science data have already been reduced)

.. code-block:: text

    python Nifty.py -q users/name/reduction/Raw -s -r -k -b 8
