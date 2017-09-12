Example of Nifty File I/O
=========================

This is an example of how the Nifty directory tree appears after each step of the
date reduction. These directory trees were created using a custom **niftree** bash command:

.. code-block:: text

  find . -name .git -prune -o -print | sed -e 's;[^/]*/;|____;g;s;____|; |;g'

Add the following line to your ~/.bash_profile to create the **niftree** alias:

.. code-block:: text

  alias niftree="find . -name .git -prune -o -print | sed -e 's;[^/]*/;|____;g;s;____|; |;g'"

linearPipeline Data Reduction
-----------------------------

Config file used:

.. code-block:: text

  # Nifty configuration file.
  #
  # Each section lists parameters required by a pipeline step.

  manualMode = True
  over = False
  merge = True
  scienceDirectoryList = []
  telluricDirectoryList = []
  calibrationDirectoryList = []

  [linearPipelineConfig]
  sort = True
  calibrationReduction = True
  telluricReduction = True
  scienceReduction = True

  [sortConfig]
  rawPath = '/Users/ncomeau/data/TUTORIAL_HD141004'
  program = ''
  skyThreshold = 2.0
  sortTellurics = True
  date = ''
  copy = ''

  [calibrationReductionConfig]
  baselineCalibrationStart = 1
  baselineCalibrationStop = 4

  [telluricReductionConfig]
  telStart = 1
  telStop = 6
  telluricSkySubtraction = True
  spectemp = ''
  mag = ''
  hline_method = 'vega'
  hlineinter = False
  continuuminter = False

  [scienceReductionConfig]
  sciStart = 1
  sciStop = 6
  scienceSkySubtraction = True
  telluricCorrectionMethod = 'gnirs'
  telinter = False
  fluxCalibrationMethod = 'gnirs'
  use_pq_offsets = True
  im3dtran = True

  # Good luck with your Science!

Starting directory structure:

.. code-block:: text

  .
  |____config.cfg


Command used to launch Nifty:

.. code-block:: text

  runNifty linearPipeline config.cfg

Directory structure after sorting:

.. code-block:: text

  .
  |____config.cfg
  |____HD141004/                         # Object name, from science header
  | |____20100401/                       # UT date, from science header
  | | |____Calibrations_K/               # Calibrations for a given science observation
  | | | |____arcdarklist                 # Textfile list of lamps-off arc frames
  | | | |____arclist                     # Textfile list of lamps-on arc frames
  | | | |____flatdarklist                # Textfile list of lamps-off flats; same length as flatlist
  | | | |____flatlist                    # Textfile list of lamps-on flats; same length as flatdarklist
  | | | |____N201004*.fits               # Raw Calibration Frames
  | | | |____original_flatdarklist       # Unmodified textfile list of lamps-off flats
  | | | |____original_flatlist           # Unmodified textfile list of lamps-on flats
  | | | |____ronchilist                  # Textfile list of lamps-on ronchi flats
  | | |____K/                            # Grating of science and telluric frames
  | | | |____obs107/                     # Science observation, from science headers
  | | | | |____N201004*.fits             # Raw science frames
  | | | | |____scienceFrameList          # Textfile list of science frames
  | | | | |____skyFrameList              # Textfile list of science sky frames
  | | | |____Tellurics/
  | | | | |____obs109/                   # A single standard star observation directory
  | | | | | |____N201004*.fits           # Raw standard star frames
  | | | | | |____scienceMatchedTellsList # Textfile matching telluric observations with science frames
  | | | | | |____skyFrameList            # Textfile list of standard star sky frames
  | | | | | |____tellist                 # Textfile list of standard star frames
  |____Nifty.log                         # Master log file

Now in nifsBaselineCalibration:

After Step 1: Get Shift, two new files appear.

.. code-block:: text

  .
  |____config.cfg
  |____HD141004/
  | |____20100401/
  | | |____Calibrations_K/
  | | | |____arcdarklist
  | | | |____arclist
  | | | |____flatdarklist
  | | | |____flatlist
  | | | |____N201004*.fits
  | | | |____original_flatdarklist
  | | | |____original_flatlist
  | | | |____ronchilist
  | | | |____shiftfile               # Textfile storing name of the reference shift file
  | | | |____sN20100410S0362.fits    # Reference shift file; a single lamps-on flat run through nfprepare
  |____Nifty.log

After Step 2: Make Flat and bad pixel mask, several new files and intermediate results appear.

.. code-block:: text

  .
  |____config.cfg
  |____HD141004/
  | |____20100401/
  | | |____Calibrations_K/
  | | | |____arcdarklist
  | | | |____arclist
  | | | |____flatdarklist
  | | | |____flatfile                         # Textfile storing name of final flat
  | | | |____flatlist
  | | | |____gnN20100410S0362.fits            # Median-combined with gemcombine() and prepared lamps-on flat
  | | | |____gnN20100410S0368.fits            # Median-combined with gemcombine() and prepared lamps-off flat
  | | | |____N201004*.fits
  | | | |____nN201004*.fits                   # Result of running raw frames through nfprepare()
  | | | |____original_flatdarklist
  | | | |____original_flatlist
  | | | |____rgnN20100410S0362.fits           # Result of running gemcombine() lamps-on flats through nsreduce()
  | | | |____rgnN20100410S0362_flat.fits      # Final rectified flat; result of nsslitfunction()
  | | | |____rgnN20100410S0362_sflat.fits     # Preliminary flat; result of nsflat()
  | | | |____rgnN20100410S0362_sflat_bpm.pl   # Final bad pixel mask; later used in nffixbad()
  | | | |____rgnN20100410S0368.fits           # Result of running gemcombine() lamps-off flats through nsreduce()
  | | | |____rgnN20100410S0368_dark.fits      # Final flat dark frame
  | | | |____ronchilist
  | | | |____sflat_bpmfile                    # Textfile storing name of final bad pixel mask
  | | | |____sflatfile
  | | | |____shiftfile
  | | | |____sN20100410S0362.fits
  |____Nifty.log
