import inspect
from unittest import mock

from pytest import raises

from data_vault.frames import FrameManager


def test_globals_from_frame():
    frame_manager = FrameManager()
    frames = inspect.stack()
    current_frame = frames[0]
    with mock.patch.object(FrameManager, 'ipython_frame_prefix', current_frame.filename):
        assert frame_manager.get_ipython_globals() == globals()

    with mock.patch.object(FrameManager, 'ipython_frame_prefix', 'not a frame'):
        with raises(Exception, match='Could not find ipython frame in stack'):
            frame_manager.get_ipython_globals()
