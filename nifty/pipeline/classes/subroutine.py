

class SubRoutine(object):
    """
    Abstract base class.

    A subroutine does the actual work of reducing data.
    """

    def __init__(self):
        """

        """
        pass

    pass

class NFPrepare(SubRoutine):
    """
    Wrapper around nfprepare
    """
    def __init__(self, calflat, log):
        """Return a new Car object."""
        self.calflat = calflat
        self.log = log
        self.runSubRoutine()

    def runSubRoutine(self, rawpath,outpref, shiftx, shifty,fl_vardq='no',fl_corr='no',fl_nonl='no', fl_int='no'):
        iraf.nfprepare(self.calflat,rawpath="",outpref="s", shiftx='INDEF', shifty='INDEF',fl_vardq='no',fl_corr='no',fl_nonl='no', fl_int='no', logfile=self.log)
