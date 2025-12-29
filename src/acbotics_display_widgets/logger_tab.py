from pyqtgraph.Qt import QtWidgets as qtw  # type: ignore
import sys
import logging
from functools import partial
import datetime
import os
from .pressure_time_view import Pressure_Time_View


if sys.version_info.major == 3 and sys.version_info.minor >= 12:
    utcfromtimestamp = partial(datetime.datetime.fromtimestamp, tz=datetime.UTC)  # type: ignore
else:
    utcfromtimestamp = datetime.datetime.utcfromtimestamp  # type: ignore

logger = logging.getLogger(__name__)


class Logger_Tab(qtw.QFrame):
    def __init__(self, fixture):
        self.fixture = fixture
        super(Logger_Tab, self).__init__()
        # Create logger tab
        # =================
        self.layout = qtw.QHBoxLayout()
        self.date_labels = []
        self.time_labels = []
        self.pressure_labels = []
        self.temp_labels = []

        col1 = qtw.QWidget()
        col1.layout = qtw.QVBoxLayout()
        col2 = qtw.QWidget()
        col2.layout = qtw.QVBoxLayout()

        # Currently just stating default outdir;
        # plan to add directory chooser in hte future
        line1 = qtw.QWidget()
        line1.layout = qtw.QHBoxLayout()
        label1 = qtw.QLabel()
        label1.setText("Output directory:\r\n Newline")
        lineedit1 = qtw.QLineEdit()
        lineedit1.setReadOnly(True)
        lineedit1.setText(f"{self.fixture.outdir}")
        line1.layout.addWidget(label1)
        line1.layout.addWidget(lineedit1)
        self.enable_button = qtw.QPushButton("Enable All")
        self.disable_button = qtw.QPushButton("Disable All")

        self.enable_button.pressed.connect(self.enable_logging)
        self.disable_button.pressed.connect(self.disable_logging)
        line1.layout.addWidget(self.enable_button)
        line1.layout.addWidget(self.disable_button)

        line1.layout.addStretch()

        line1.setLayout(line1.layout)
        col1.layout.addWidget(line1)

        line_all_loggers = qtw.QWidget()
        line_all_loggers.layout = qtw.QHBoxLayout()
        self.all_loggers_label = qtw.QLabel("All  Loggers:")
        self.all_loggers_disply = qtw.QLabel("Disabled")
        line_all_loggers.layout.addWidget(self.all_loggers_label)
        line_all_loggers.layout.addWidget(self.all_loggers_disply)
        line_all_loggers.setLayout(line_all_loggers.layout)

        col1.layout.addWidget(line_all_loggers)

        self.status_box = qtw.QLabel("Logger status")
        col1.layout.addWidget(self.status_box)

        col1.layout.addStretch()
        col1.setLayout(col1.layout)

        self.pressure_view = Pressure_Time_View(self.fixture)

        # Tab 1 : Assemble Columns
        self.layout.addWidget(col1)
        self.layout.addWidget(self.pressure_view)

        self.setLayout(self.layout)

    def enable_logging(self):
        self.switch_logging_all(1)

    def disable_logging(self):
        self.switch_logging_all(0)

    def gamepad_callbacks(self, event_info):
        if (
            event_info["ev_type"] == "Key"
            and event_info["code"] == "BTN_NORTH"
            and event_info["state"] == 1
        ):
            self.switch_logging_all(1)
            return True
        if (
            event_info["ev_type"] == "Key"
            and event_info["code"] == "BTN_EAST"
            and event_info["state"] == 1
        ):
            self.switch_logging_all(0)
            # disable logging
            return True

    def switch_logging_all(self, val):
        if val:
            self.all_loggers_disply.setText("Enabled")
        else:
            self.all_loggers_disply.setText("Disabled")
        self.fixture.switch_logging_all(val)

    def update(self):
        self.pressure_view.update()

        logger_paths = self.fixture.get_logger_paths()
        status_string = "Logger status: \r\n"
        for pth in sorted(logger_paths):
            if len(pth) == 0:
                continue
            sz = 0
            try:
                sz = os.path.getsize(pth)
            except:
                pass

            status_string += repr(sz) + "\t\t" + pth + "\r\n"
        self.status_box.setText(status_string)
