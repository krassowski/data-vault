import inspect


class FrameManager:
    """Just to make unit testing easier"""

    def find_ipython_frame(self, frames):
        for frame in frames:
            if frame.filename.startswith('<ipython-input-'):
                return frame
        return None

    def ensure_frame(self, frame):
        if not frame:
            raise Exception('Could not find ipython frame in stack')

    def get_frames(self):
        return inspect.stack()

    def get_ipython_globals(self):
        frame = self.find_ipython_frame(self.get_frames())
        self.ensure_frame(frame)
        return frame.frame.f_globals


frame_manager = FrameManager()