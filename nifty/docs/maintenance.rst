Maintaining Nifty
=================

Documentation
=============

Right now there exists five forms of documentation.

Paper
-----
.. Insert a paper!

README.rst
----------

Manual
------

Nifty's manual gives a broad overview of how the code functions. It is included as
a pdf.

.rst Files in the docs/ directory
---------------------------------

This file, others like it in the docs/ directory and the README are written in
reStructuredText. This markup language integrates well with Python's automatic
documentation builder (read Sphinx) and Github as well as being human readable. You can
read more about reStructuredText `here.<http://www.sphinx-doc.org/en/stable/rest.html>`_

Comments and DocStrings in Source Code
--------------------------------------

Nifty uses the Google docstring style. Examples of docstrings can be found
`here.<http://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html>`_

Other Python comments use the following convention:

- A # is followed by a space and a capital letter.
- All comments end in a period where possible.

Updates
=======

Version Numbers
---------------

Nifty uses semantic versioning(see http://semver.org/). This means version numbers come in

.. code-block:: text

  MAJOR.MINOR.PATCH

In brief, when releasing a version of Nifty that is not backward-compatible with old test recipes,
or changes break the public API, it is time to increment the MAJOR version number.

..TODO(nat): maybe make this a little clearer.

Code Conventions
================

Nifty was partly written using `atom.<https://atom.io/>`_ Error messages,
warnings and updates were written using templates in the included snippets.cson file.

Where possible, nat used 2D (and higher) dimensional lists to implement error
checking flags. These are particularly prominent in sort.

Variables and functions were named using conventions in the
`Python Style Guide.<https://www.python.org/dev/peps/pep-0008/#descriptive-naming-styles>`_
Specifically a mix of camelCase and lower_case_with_underscores was used.

Known Issues
============

Nifty.py
--------

nifsSort.py
-----------

nifsBaselineCalibration.py
--------------------------

nifsReduce.py
-------------
- z-band data is not capable of a flux calibration (yet!).
- Seems to be missing the first peak of the ronchi slit when iraf.nfsdist() is run interactively.
  This does not seem to be a problem.
- We noticed that iraf.nfsdist() produced different results when run interactively and
  non-interactively. To test check the log for iraf.nfsdist() output and make sure it is
  identifying 8/8 or 9/9 peaks every time.
- iraf.nftelluric() was not built to be run automatically. A lightly tested modified
  version that allows an automatic telluric correction is included in the extras directory
  but more testing is needed. For now applyTelluricPython() is recommended.

nifsMerge.py
------------

nifsDefs.py
-----------

General Issues
--------------
- A longstanding bug (see `astropy<https://github.com/astropy/astropy/pull/960>`_ ) in astropy has made it
  difficult to build Nifty as a binary executable.
- The conversion of print statements to logging.info() statements was messy. Some of these
  may still not be properly converted and will throw nasty tracebacks. However these seem to
  have no effect on the functionioning of the code.
- Logging is still not perfect. One or two iraf tasks are sending their log files to
  "nifs.log" instead of "Nifty.log".

Future Work
===========

- Update config to use .cfg and a config parser instead of .json files, a la space-telescope










.. placeholder comment
