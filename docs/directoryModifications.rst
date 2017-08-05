Example of Directory Modifications Through Nifty
================================================

This is an example of how the Nifty directory tree appears after each step of the
date reduction.

Contents of user_options.json:

.. code-block:: text

    "sci": "yes",
    "mag": null,
    "over": false,
    "telred": "yes",
    "tel": "yes",
    "efficiencySpectrumCorrection": "yes",
    "telinter": false,
    "telluric_correction_method": "python",
    "telStop": 6,
    "continuuminter": false,
    "telStart": 1,
    "program": null,
    "spectemp": null,
    "__version__": "v0.1.1",
    "red": "yes",
    "sort": "yes",
    "sciStop": 6,
    "rawPath": "/Users/ncomeau/data/TUTORIAL_HD141004",
    "rstop": 4,
    "hlineinter": false,
    "rstart": 1,
    "hline_method": "vega",
    "date": null,
    "copy": null,
    "sciStart": 1,
    "use_pq_offsets": true,
    "merge": "yes"

Before nifsSort
---------------

.. code-block:: text

    |____docs
    | |____directoryModifications.rst
    | |____example_calibrationDirectoryList.txt
    | |____example_scienceDirectoryList.txt
    | |____example_telluricDirectoryList.txt
    | |____faq.rst
    | |____hline_removal.rst
    | |____maintenance.rst
    | |____nifs_pipeline_june_2015.pdf
    |____extras
    | |____gemini_sort.py
    | |____MANIFEST.in
    | |____old_merge.py
    | |____setup.py
    | |____spec-file-osx-64.txt
    |____LICENSE
    |____nifsBaselineCalibration.py
    |____nifsDefs.py
    |____nifsMerge.py
    |____nifsReduce.py
    |____nifsSort.py
    |____Nifty.py
    |____README.rst
    |____recipes
    |____runtimeData
    | |____default_input.json
    | |____h_test_one_argon.dat
    | |____j_test_one_argon.dat
    | |____k_test_two_argon.dat
    | |____new_starstemp.txt
    | |____user_options.json
    | |____vega_ext.fits
    |____unitTests
    | |____generate_response_curve.py
    | |____hk.txt
    | |____nftelluric_modified.cl

After nifsSort
--------------

nifsSort.py adds a scienceObjectName directory and some data files in the runtimeData directory.

.. code-block:: text

    |____docs
    |____extras
    |____HD141004
    | |____20100401
    | | |____Calibrations_K
    | | | |____arcdarklist
    | | | |____arclist
    | | | |____flatdarklist
    | | | |____flatlist
    | | | |____N20100401S0137.fits
    | | | |____N20100401S0181.fits
    | | | |____N20100410S0362.fits
    | | | |____N20100410S0363.fits
    | | | |____N20100410S0364.fits
    | | | |____N20100410S0365.fits
    | | | |____N20100410S0366.fits
    | | | |____N20100410S0367.fits
    | | | |____N20100410S0368.fits
    | | | |____N20100410S0369.fits
    | | | |____N20100410S0370.fits
    | | | |____N20100410S0371.fits
    | | | |____N20100410S0372.fits
    | | | |____N20100410S0373.fits
    | | | |____N20100410S0374.fits
    | | | |____N20100410S0375.fits
    | | | |____N20100410S0376.fits
    | | | |____ronchilist
    | | |____K
    | | | |____obs107
    | | | | |____N20100401S0182.fits
    | | | | |____N20100401S0183.fits
    | | | | |____N20100401S0184.fits
    | | | | |____N20100401S0185.fits
    | | | | |____N20100401S0186.fits
    | | | | |____N20100401S0187.fits
    | | | | |____N20100401S0188.fits
    | | | | |____N20100401S0189.fits
    | | | | |____N20100401S0190.fits
    | | | | |____scienceFrameList
    | | | | |____skyframelist
    | | | |____Tellurics
    | | | | |____obs109
    | | | | | |____N20100401S0138.fits
    | | | | | |____N20100401S0139.fits
    | | | | | |____N20100401S0140.fits
    | | | | | |____N20100401S0141.fits
    | | | | | |____N20100401S0142.fits
    | | | | | |____N20100401S0143.fits
    | | | | | |____N20100401S0144.fits
    | | | | | |____N20100401S0145.fits
    | | | | | |____N20100401S0146.fits
    | | | | | |____scienceMatchedTellsList
    | | | | | |____skyframelist
    | | | | | |____tellist
    |____LICENSE
    |____nifsBaselineCalibration.py
    |____nifsBaselineCalibration.pyc
    |____nifsDefs.py
    |____nifsDefs.pyc
    |____nifsMerge.py
    |____nifsMerge.pyc
    |____nifsReduce.py
    |____nifsReduce.pyc
    |____nifsSort.py
    |____nifsSort.pyc
    |____Nifty.log
    |____Nifty.py
    |____README.rst
    |____recipes
    |____runtimeData
    | |____**calibrationDirectoryList.txt**
    | |____default_input.json
    | |____h_test_one_argon.dat
    | |____j_test_one_argon.dat
    | |____k_test_two_argon.dat
    | |____new_starstemp.txt
    | |____**scienceDirectoryList.txt**
    | |____**telluricDirectoryList.txt**
    | |____user_options.json
    | |____vega_ext.fits
    |____unitTests


After nifsReduce(tellurics)
---------------------------

After nifsReduce(science)
-------------------------
