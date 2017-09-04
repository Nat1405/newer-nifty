


class Routine(object):
    """
    """

    def __init__(self, name, subroutines):
        """

        """
        self.name = name
        # class, arguments tuple
        self.subroutines = subroutines
        checkOverwrite()
        run()

    def doSingle(self, subroutine):
        """
        Do a subroutine once on a single input
        """
        checkInput()
        checkOverwrite()
        subroutine.run()
        checkOutput()
        pass

    def doLoop(self):
        """
        Do a subroutine, looping over multiple input.

        """
        for subroutine in subroutines:
            subroutine.run()

    def checkOutput():
        pass

class MakeFlat(Routine):
    """
    """

    def run(self):
        doLoop(flatlist,
            iraf.nfprepare(image+'.fits',rawpath='.',shiftim="s"+calflat, fl_vardq='yes', fl_corr='no',fl_nonl='no', logfile=log)
        )
        doLoop(flatdarklist,
            iraf.nfprepare(image+'.fits',rawpath='.',shiftim="s"+calflat, fl_vardq='yes',fl_corr='no',fl_nonl='no', logfile=log)
        )
        doSingle(GemCombine(calflat))
        doSingle(GemCombine(flatdark))
        doSingle(NSReduce("gn"+calflat))
        soSingle(NSReduce("gn"+flatdark))
        doSingle(NSFlat())
        soSingle(NSSlitFunction)










#
