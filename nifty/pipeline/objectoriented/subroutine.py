

class Prepare(SubRoutine):
    """
    Wrapper around nfprepare
    """
    def __init__(self):
        """
        Run a task; can be IRAF or Python.

        """
        pass

    def run(self, inputFile, **kwargs):
        iraf.nfprepare(inputFile, **kwargs)
