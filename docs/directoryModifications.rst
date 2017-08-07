Example of Directory Modifications Through Nifty
================================================

This is an example of how the Nifty directory tree appears after each step of the
date reduction. These directory trees were created using a custom **niftree** bash command:

.. code-block:: text

  find . -name .git -prune -o -print | sed -e 's;[^/]*/;|____;g;s;____|; |;g'

Add the following line to your ~/.bash_profile to create the **niftree** alias:

.. code-block:: text

  alias niftree="find . -name .git -prune -o -print | sed -e 's;[^/]*/;|____;g;s;____|; |;g'"

Table of Contents
-----------------

- nifsSort_

- nifsBaselineCalibration_

- `nifsReduce(Tellurics)<nifsReduceTelluric>`_

- `nifsReduce(Science)<nifsReduceScience>`_

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

.. _nifsSort:

nifsSort
========

Before nifsSort
---------------

.. code-block:: text

    |____.DS_Store
    |____.gitignore
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
    | |____calibrationDirectoryList.txt
    | |____default_input.json
    | |____h_test_one_argon.dat
    | |____j_test_one_argon.dat
    | |____k_test_two_argon.dat
    | |____new_starstemp.txt
    | |____scienceDirectoryList.txt
    | |____telluricDirectoryList.txt
    | |____user_options.json
    | |____vega_ext.fits
    |____unitTests
    | |____generate_response_curve.py
    | |____hk.txt
    | |____nftelluric_modified.cl

After makePythonLists()
-----------------------

makePythonLists() only creates python lists of files; it does not write any new files.

.. code-block:: text

    .
    |____.DS_Store
    |____.gitignore
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
    | |____calibrationDirectoryList.txt
    | |____default_input.json
    | |____h_test_one_argon.dat
    | |____j_test_one_argon.dat
    | |____k_test_two_argon.dat
    | |____new_starstemp.txt
    | |____scienceDirectoryList.txt
    | |____telluricDirectoryList.txt
    | |____user_options.json
    | |____vega_ext.fits
    |____unitTests
    | |____generate_response_curve.py
    | |____hk.txt
    | |____nftelluric_modified.cl

After sortScienceAndTelluric()
------------------------------

sortScienceAndTelluric() creates a directory structure and copies science, telluric, sky frames and
acquisitions to the appropriate directories.

.. code-block:: text

    .
    |____.DS_Store
    |____.gitignore
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
    |____HD141004
    | |____20100401
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
    | |____calibrationDirectoryList.txt
    | |____default_input.json
    | |____h_test_one_argon.dat
    | |____j_test_one_argon.dat
    | |____k_test_two_argon.dat
    | |____new_starstemp.txt
    | |____scienceDirectoryList.txt
    | |____telluricDirectoryList.txt
    | |____user_options.json
    | |____vega_ext.fits
    |____unitTests
    | |____generate_response_curve.py
    | |____hk.txt
    | |____nftelluric_modified.cl

After sortCalibrations()
------------------------

.. code-block:: text

    .
    |____.DS_Store
    |____.gitignore
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
    | |____calibrationDirectoryList.txt
    | |____default_input.json
    | |____h_test_one_argon.dat
    | |____j_test_one_argon.dat
    | |____k_test_two_argon.dat
    | |____new_starstemp.txt
    | |____scienceDirectoryList.txt
    | |____telluricDirectoryList.txt
    | |____user_options.json
    | |____vega_ext.fits
    |____unitTests
    | |____generate_response_curve.py
    | |____hk.txt
    | |____nftelluric_modified.cl

After matchTels()
-----------------

.. code-block:: text

    .
    |____.DS_Store
    |____.gitignore
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
    | |____calibrationDirectoryList.txt
    | |____default_input.json
    | |____h_test_one_argon.dat
    | |____j_test_one_argon.dat
    | |____k_test_two_argon.dat
    | |____new_starstemp.txt
    | |____scienceDirectoryList.txt
    | |____telluricDirectoryList.txt
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

    .
    |____.DS_Store
    |____.gitignore
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
    | |____calibrationDirectoryList.txt
    | |____default_input.json
    | |____h_test_one_argon.dat
    | |____j_test_one_argon.dat
    | |____k_test_two_argon.dat
    | |____new_starstemp.txt
    | |____scienceDirectoryList.txt
    | |____telluricDirectoryList.txt
    | |____user_options.json
    | |____vega_ext.fits
    |____unitTests
    | |____generate_response_curve.py
    | |____hk.txt
    | |____nftelluric_modified.cl

.. _nifsBaselineCalibration:

nifsBaselineCalibration
=======================

Before running nifsBaselineCalibration()
----------------------------------------

.. code-block:: text

    .
    |____.DS_Store
    |____.gitignore
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
    | |____calibrationDirectoryList.txt
    | |____default_input.json
    | |____h_test_one_argon.dat
    | |____j_test_one_argon.dat
    | |____k_test_two_argon.dat
    | |____new_starstemp.txt
    | |____scienceDirectoryList.txt
    | |____telluricDirectoryList.txt
    | |____user_options.json
    | |____vega_ext.fits
    |____unitTests
    | |____generate_response_curve.py
    | |____hk.txt
    | |____nftelluric_modified.cl

After Step 1: Locate the Spectrum
---------------------------------

This step writes two new files; a .fits shiftfile and a textfile storing the name of the shiftfile.

.. code-block:: text

    .
    |____.DS_Store
    |____.gitignore
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
    | | | |____shiftfile
    | | | |____sN20100410S0362.fits
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
    | |____calibrationDirectoryList.txt
    | |____default_input.json
    | |____h_test_one_argon.dat
    | |____j_test_one_argon.dat
    | |____k_test_two_argon.dat
    | |____new_starstemp.txt
    | |____scienceDirectoryList.txt
    | |____telluricDirectoryList.txt
    | |____user_options.json
    | |____vega_ext.fits
    |____unitTests
    | |____generate_response_curve.py
    | |____hk.txt
    | |____nftelluric_modified.cl

After Step 2: Flat Field
------------------------

.. code-block:: text

    .
    |____.DS_Store
    |____.gitignore
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
    |____HD141004
    | |____20100401
    | | |____Calibrations_K
    | | | |____arcdarklist
    | | | |____arclist
    | | | |____flatdarklist
    | | | |____flatfile
    | | | |____flatlist
    | | | |____gnN20100410S0362.fits
    | | | |____gnN20100410S0368.fits
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
    | | | |____nN20100410S0362.fits
    | | | |____nN20100410S0363.fits
    | | | |____nN20100410S0364.fits
    | | | |____nN20100410S0365.fits
    | | | |____nN20100410S0366.fits
    | | | |____nN20100410S0367.fits
    | | | |____nN20100410S0368.fits
    | | | |____nN20100410S0369.fits
    | | | |____nN20100410S0370.fits
    | | | |____nN20100410S0371.fits
    | | | |____nN20100410S0372.fits
    | | | |____rgnN20100410S0362.fits
    | | | |____rgnN20100410S0362_flat.fits
    | | | |____rgnN20100410S0362_sflat.fits
    | | | |____rgnN20100410S0362_sflat_bpm.pl
    | | | |____rgnN20100410S0368.fits
    | | | |____rgnN20100410S0368_dark.fits
    | | | |____ronchilist
    | | | |____sflat_bpmfile
    | | | |____sflatfile
    | | | |____shiftfile
    | | | |____sN20100410S0362.fits
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
    | |____calibrationDirectoryList.txt
    | |____default_input.json
    | |____h_test_one_argon.dat
    | |____j_test_one_argon.dat
    | |____k_test_two_argon.dat
    | |____new_starstemp.txt
    | |____scienceDirectoryList.txt
    | |____telluricDirectoryList.txt
    | |____user_options.json
    | |____vega_ext.fits
    |____unitTests
    | |____generate_response_curve.py
    | |____hk.txt
    | |____nftelluric_modified.cl

After Step 3: Wavelength Solution
---------------------------------

.. code-block:: text

    .
    |____.DS_Store
    |____.gitignore
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
    |____HD141004
    | |____20100401
    | | |____Calibrations_K
    | | | |____arcdarkfile
    | | | |____arcdarklist
    | | | |____arclist
    | | | |____database
    | | | | |____idwrgnN20100401S0137_SCI_10_
    | | | | |____idwrgnN20100401S0137_SCI_11_
    | | | | |____idwrgnN20100401S0137_SCI_12_
    | | | | |____idwrgnN20100401S0137_SCI_13_
    | | | | |____idwrgnN20100401S0137_SCI_14_
    | | | | |____idwrgnN20100401S0137_SCI_15_
    | | | | |____idwrgnN20100401S0137_SCI_16_
    | | | | |____idwrgnN20100401S0137_SCI_17_
    | | | | |____idwrgnN20100401S0137_SCI_18_
    | | | | |____idwrgnN20100401S0137_SCI_19_
    | | | | |____idwrgnN20100401S0137_SCI_1_
    | | | | |____idwrgnN20100401S0137_SCI_20_
    | | | | |____idwrgnN20100401S0137_SCI_21_
    | | | | |____idwrgnN20100401S0137_SCI_22_
    | | | | |____idwrgnN20100401S0137_SCI_23_
    | | | | |____idwrgnN20100401S0137_SCI_24_
    | | | | |____idwrgnN20100401S0137_SCI_25_
    | | | | |____idwrgnN20100401S0137_SCI_26_
    | | | | |____idwrgnN20100401S0137_SCI_27_
    | | | | |____idwrgnN20100401S0137_SCI_28_
    | | | | |____idwrgnN20100401S0137_SCI_29_
    | | | | |____idwrgnN20100401S0137_SCI_2_
    | | | | |____idwrgnN20100401S0137_SCI_3_
    | | | | |____idwrgnN20100401S0137_SCI_4_
    | | | | |____idwrgnN20100401S0137_SCI_5_
    | | | | |____idwrgnN20100401S0137_SCI_6_
    | | | | |____idwrgnN20100401S0137_SCI_7_
    | | | | |____idwrgnN20100401S0137_SCI_8_
    | | | | |____idwrgnN20100401S0137_SCI_9_
    | | | |____flatdarklist
    | | | |____flatfile
    | | | |____flatlist
    | | | |____gnN20100401S0137.fits
    | | | |____gnN20100410S0362.fits
    | | | |____gnN20100410S0368.fits
    | | | |____gnN20100410S0373.fits
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
    | | | |____nN20100401S0137.fits
    | | | |____nN20100401S0181.fits
    | | | |____nN20100410S0362.fits
    | | | |____nN20100410S0363.fits
    | | | |____nN20100410S0364.fits
    | | | |____nN20100410S0365.fits
    | | | |____nN20100410S0366.fits
    | | | |____nN20100410S0367.fits
    | | | |____nN20100410S0368.fits
    | | | |____nN20100410S0369.fits
    | | | |____nN20100410S0370.fits
    | | | |____nN20100410S0371.fits
    | | | |____nN20100410S0372.fits
    | | | |____nN20100410S0373.fits
    | | | |____nN20100410S0374.fits
    | | | |____rgnN20100401S0137.fits
    | | | |____rgnN20100410S0362.fits
    | | | |____rgnN20100410S0362_flat.fits
    | | | |____rgnN20100410S0362_sflat.fits
    | | | |____rgnN20100410S0362_sflat_bpm.pl
    | | | |____rgnN20100410S0368.fits
    | | | |____rgnN20100410S0368_dark.fits
    | | | |____ronchilist
    | | | |____sflat_bpmfile
    | | | |____sflatfile
    | | | |____shiftfile
    | | | |____sN20100410S0362.fits
    | | | |____wrgnN20100401S0137.fits
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
    | |____calibrationDirectoryList.txt
    | |____default_input.json
    | |____h_test_one_argon.dat
    | |____j_test_one_argon.dat
    | |____k_test_two_argon.dat
    | |____new_starstemp.txt
    | |____scienceDirectoryList.txt
    | |____telluricDirectoryList.txt
    | |____user_options.json
    | |____vega_ext.fits
    |____unitTests
    | |____generate_response_curve.py
    | |____hk.txt
    | |____nftelluric_modified.cl

.. _nifsReduceTelluric:

nifsReduce(tellurics)
=====================



.. _nifsReduceScience:

nifsReduce(science)
===================




















.. Just a placeholder
