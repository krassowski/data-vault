class FrameManager:
    """Just to make unit testing easier"""

    def __init__(self, ipython_globals=None):
        self.ipython_globals = ipython_globals

    def get_ipython_globals(self):
        assert self.ipython_globals
        return self.ipython_globals


frame_manager = FrameManager()
