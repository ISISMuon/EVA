import pytest
from pytestqt.plugin import qtbot

from EVA.core.app import get_app


class TestPeakFitWindow:
    # TODO add tests
    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        pass
