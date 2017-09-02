Introduction
============

Documentation contents:

.. toctree::
   :maxdepth: 1

   preparingInput
   runningNifty
   availableRecipes
   hlineRemoval
   merging
   knownissues
   maintenance
   futurework
   api

   Table of Contents
   -----------------

   - nifsSort_

   - nifsBaselineCalibration_

   - nifsReduceTelluric_

   - nifsReduceScience_

Nifty Structure
---------------

Nifty.py is a "wrapper" script that can call nifsSort.py, nifsBaselineCalibration.py, and nifsReduce.py in order. Each of these scripts then calls various PyRAF tasks in the Gemini NIFS IRAF data reduction package. This makes it easy to run \emph{Nifty} in a linear semi or fully automatic fashion.

nifsSort.py sorts raw NIFS data. A user tells nifsSort.py to get raw NIFS data from one of three sources: (1) A local directory, (2) the public Gemini Data Archives, or (3) a private Gemini server. %NAT- should we advertise the private Gemini option here in the paper?

nifsBaselineCalibration.py reduces the raw NIFS baseline calibrations.

nifsReduce.py reduces both the raw NIFS telluric and science data.

nifsMerge.py merges all individual 3D data cubes to a single final merged cube. %NAT- not implemented yet; right now only merges cubes with the same grating.

nifsUtils.py contains general use functions used by the other five scripts.
