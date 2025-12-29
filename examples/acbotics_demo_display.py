import datetime
import json
import logging
import logging.handlers
import os
import signal as sig
import socket
import sys
import time
from functools import partial

# from .gamepad_input import GamepadInputs
from acbotics_demo_fixture import AcboticsDemoFixture
from acbotics_display_widgets.spectrogram_tab import Spectrogram_Tab

from acbotics_display_widgets.time_series_tab import Time_Series_Tab

# from .acsense_time_series_multi_tab import Acsense_Time_Series_Multi_Tab
from acbotics_display_widgets.sensor_list_tab import Sensor_List_Tab

from acbotics_display_widgets.logger_tab import Logger_Tab
from acbotics_display_widgets.sensor_series_tab import Sensor_Series_Tab
import numpy as np
from osgeo import gdal  # type: ignore

if hasattr(gdal, "DontUseExceptions"):
    gdal.DontUseExceptions()


import pyqtgraph as pg  # type: ignore
from matplotlib import colors
from pyqtgraph.Qt import QtWidgets as qtw  # type: ignore

sig.signal(sig.SIGINT, sig.SIG_DFL)


logging.basicConfig(
    # format="[%(asctime)s] %(name)s.%(funcName)s() : \n\t%(message)s",
    format="[%(asctime)s] %(levelname)s: %(filename)s:L%(lineno)d : %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    # level=logging.DEBUG,
    level=logging.INFO,
    force=True,
)

logging.getLogger("matplotlib").propagate = False
logger = logging.getLogger(__name__)

LOWERCASE_MU = "\u03bc"


if sys.version_info.major == 3 and sys.version_info.minor >= 12:
    utcfromtimestamp = partial(datetime.datetime.fromtimestamp, tz=datetime.UTC)  # type: ignore
else:
    utcfromtimestamp = datetime.datetime.utcfromtimestamp  # type: ignore


class MainWindow(qtw.QMainWindow):
    def __init__(self, scr_width, scr_height, args):
        logger.debug("Setting up MainWindow")

        self.fixture = AcboticsDemoFixture(args)
        self.fixture.run_as_thread()
        self.current_ch = self.fixture.current_ch
        self.zoom_coeff = 1.5
        self.use_filter = False
        self.num_channels = 16
        self.Fs = self.fixture.Fs

        self.increment_channel_flag = 0
        self.decrement_channel_flag = 0
        # self.gpad = GamepadInputs()
        # self.gpad.add_callback(self.gamepad_callback, "Key")
        # self.gpad.add_callback(self.gamepad_callback, "Absolute")

        # self.gpad.run_as_thread()

        super().__init__()
        self.run_basic_setup(scr_width, scr_height)

        self.date_labels = []
        self.time_labels = []
        self.pressure_labels = []
        self.temp_labels = []

        self.ch_controls = []

        self.tab_widget = qtw.QWidget()
        self.tab_widget.layout = qtw.QVBoxLayout()

        # Initialize tab screen
        self.tabs = qtw.QTabWidget()
        self.tabs.resize(self.width, self.height)

        self.create_tab_specgram()
        # self.create_tab_beamform()
        # self.create_tab_tracker()
        self.create_tab_time_series()
        # self.create_tab_time_series_multi()
        self.create_tab_loggers()
        self.create_tab_sensor_list()
        self.create_tab_sensors()

        # self.tabs.setCurrentIndex(1)

        # Add tabs to widget
        # ==================

        self.tab_widget.layout.addWidget(self.tabs)
        self.tab_widget.setLayout(self.tab_widget.layout)

        mw_w = qtw.QWidget()
        mw_w.layout = qtw.QGridLayout()

        # label1 = qtw.QLabel()
        # label1.setText("System Time")

        self.label_date = qtw.QLabel()
        self.label_date.setText("INIT DATE")
        # self.date_labels.append(label_date)

        self.label_time = qtw.QLabel()
        self.label_time.setText("INIT TIME")
        # self.time_labels.append(label_time)

        time_w = qtw.QWidget()
        time_w.layout = qtw.QHBoxLayout()
        time_w.layout.addStretch()
        # time_w.layout.addWidget(label1)
        time_w.layout.addWidget(self.label_date)
        time_w.layout.addWidget(self.label_time)
        # time_w.layout.addStretch()
        time_w.setLayout(time_w.layout)

        mw_w.layout.addWidget(time_w, 0, 0, pg.QtCore.Qt.AlignTop)
        mw_w.layout.addWidget(self.tab_widget, 0, 0)
        mw_w.setLayout(mw_w.layout)

        # self.setCentralWidget(self.tab_widget)
        self.setCentralWidget(mw_w)

        if self.use_fullscreen:
            self.showFullScreen()

        self.show()
        # self.reset_filter()

    def run_basic_setup(self, scr_width, scr_height):
        self.title = "AcSense Display"
        self.left = 0
        self.top = 0

        self.width = scr_width
        self.height = scr_height
        self.use_fullscreen = True
        logger.info(f"Detected screen size (WxH) : {(self.width, self.height)}")
        if self.height > 1000:
            self.width = scr_width // 2
            self.height = scr_height // 2
            self.use_fullscreen = False
            logger.info("Large screen detected; skipping fullscreen")

        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

    #         self.setStyleSheet(
    #             (
    #                 """

    # QMainWindow {
    #     background-color: black;
    #     color: white;
    # }

    # QTabBar::tab:selected {
    #     background-color: #333333;
    # }

    # QTabBar::tab {
    #     border: 2px solid #333333;
    #     padding: 4px 16px 4px 16px;

    #     border-top-left-radius: 12px;
    #     border-top-right-radius: 12px;
    # }

    # QTabBar {
    #     background-color: black;
    #     color: white;
    # }

    # QTabWidget::pane { /* The tab widget frame */
    #     border: 2px solid #333333;
    # }

    # QScrollArea > QWidget > QWidget {
    #     background: transparent;
    # }

    # QScrollArea {
    #     background: black;
    #     border: 1px solid black;
    # }

    # QScrollBar::handle {
    #     background: gray;
    # }

    # QScrollBar {
    #     background: palette(base);
    # }

    # QWidget {
    #     color: white;
    # }

    # QLabel {
    #     background-color: black;
    #     color: white;
    # }

    # QComboBox {
    #     color: white;
    #     background-color: dimgray;
    # }

    # QComboBox::item {
    #     color: white;
    #     background-color: dimgray;
    #     selection-background-color: gray;
    # }

    # QCheckBox {
    #     color: white;
    # }

    # QCheckBox::indicator {
    #     border: 2px solid white;
    #     background-color: white;
    #     width: 20px;
    #     height: 20px;
    # }

    # QCheckBox::indicator:checked {
    #     border: 2px solid white;
    #     background-color: blue;
    # }

    # QDoubleSpinBox::down-button{
    #     width: 20px;
    # }

    # QDoubleSpinBox::up-button{
    #     width: 20px;
    # }
    #                 """
    #             )
    #         )

    def create_tab_specgram(self):
        self.spectrogram_tab = Spectrogram_Tab(self.fixture)
        self.tabs.addTab(self.spectrogram_tab, "Spectrogram")

    # def create_tab_beamform(self):
    #     self.tab_beamform = Acsense_Beamform_Tab(self.fixture)
    #     self.tabs.addTab(self.tab_beamform, "Beamforming")

    # def create_tab_tracker(self):
    #     self.tab_tracker = Acsense_Tracker_Tab(self.fixture)
    #     self.tabs.addTab(self.tab_tracker, "Tracker")

    def create_tab_time_series(self):
        self.tab_timeseries = Time_Series_Tab(self.fixture)
        self.tabs.addTab(self.tab_timeseries, "Time-Series")

    # def create_tab_time_series_multi(self):
    #     self.tab_timeseries_multi = Acsense_Time_Series_Multi_Tab(self.fixture)
    #     self.tabs.addTab(self.tab_timeseries_multi, "Multi")

    def create_tab_loggers(self):
        self.tab_loggers = Logger_Tab(self.fixture)
        self.tabs.addTab(self.tab_loggers, "Loggers")

    def create_tab_sensor_list(self):
        self.tab_other = Sensor_List_Tab(self.fixture)
        self.tabs.addTab(self.tab_other, "Sensor List")

    def create_tab_sensors(self):
        self.tab_sensors = Sensor_Series_Tab(self.fixture)
        self.tabs.addTab(self.tab_sensors, "Sensors")

    # def gamepad_callbacks_time_series(self, event_info):
    #     if (
    #         event_info["ev_type"] == "Key"
    #         and event_info["code"] == "BTN_WEST"
    #         and event_info["state"] == 1
    #     ):
    #         self.increment_current_channel_callback()
    #         return True
    #     if (
    #         event_info["ev_type"] == "Key"
    #         and event_info["code"] == "BTN_SOUTH"
    #         and event_info["state"] == 1
    #     ):
    #         self.decrement_current_channel_callback()
    #         return True
    #     return False

    # def gamepad_callbacks_spectrogram(self, event_info):
    #     if (
    #         event_info["ev_type"] == "Key"
    #         and event_info["code"] == "BTN_WEST"
    #         and event_info["state"] == 1
    #     ):
    #         self.increment_current_channel_callback()
    #         return True
    #     if (
    #         event_info["ev_type"] == "Key"
    #         and event_info["code"] == "BTN_SOUTH"
    #         and event_info["state"] == 1
    #     ):
    #         self.decrement_current_channel_callback()
    #         return True
    #     return self.spectrogram_tab.gamepad_callbacks(event_info)

    # def gamepad_callback(self, event_info):
    #     if (
    #         event_info["ev_type"] == "Key"
    #         and event_info["code"] == "BTN_TR"
    #         and event_info["state"] == 1
    #     ):
    #         self.cycle_panels_fwd()
    #         return
    #     if (
    #         event_info["ev_type"] == "Key"
    #         and event_info["code"] == "BTN_TL"
    #         and event_info["state"] == 1
    #     ):
    #         self.cycle_panels_rev()
    #         return
    #     processed = False
    #     if self.tabs.tabText(self.tabs.currentIndex()) == "Time-Series":
    #         processed = self.gamepad_callbacks_time_series(event_info)
    #     elif self.tabs.tabText(self.tabs.currentIndex()) == "Spectrogram":
    #         processed = self.gamepad_callbacks_spectrogram(event_info)
    #     elif self.tabs.tabText(self.tabs.currentIndex()) == "Loggers":
    #         processed = self.tab_loggers.gamepad_callbacks(event_info)
    #     elif self.tabs.tabText(self.tabs.currentIndex()) == "Other":
    #         pass
    #     elif self.tabs.tabText(self.tabs.currentIndex()) == "Tracker":
    #         pass
    #     elif self.tabs.tabText(self.tabs.currentIndex()) == "Beamforming":
    #         pass

    def cycle_panels_fwd(self, state=None):
        cur = self.tabs.currentIndex()
        next = (cur + 1) % self.tabs.count()
        self.tabs.setCurrentIndex(next)

    def cycle_panels_rev(self, state=None):
        cur = self.tabs.currentIndex()
        next = (cur - 1) % self.tabs.count()
        self.tabs.setCurrentIndex(next)

    def increment_current_channel_callback(self, state=None):
        self.increment_channel_flag += 1

    def decrement_current_channel_callback(self, state=None):
        self.decrement_channel_flag += 1

    def increment_current_channel(self):
        if self.current_ch < self.num_channels - 1:
            self.set_curr_ch(self.current_ch + 1)

    def decrement_current_channel(self):
        if self.current_ch > 0:
            self.set_curr_ch(self.current_ch - 1)

    def set_curr_ch(self, index):
        change = self.fixture.set_current_channel(index)
        self.current_ch = self.fixture.current_ch

    def update(self):
        while self.increment_channel_flag > 0:
            self.increment_channel_flag -= 1
            self.increment_current_channel()

        while self.decrement_channel_flag > 0:
            self.decrement_channel_flag -= 1
            self.decrement_current_channel()

        if not self.fixture.get_num_channels() == self.num_channels:
            logger.debug("Mismatched number of channels; updating controls")
            self.num_channels = self.fixture.get_num_channels()
            for it in self.ch_controls:
                it.clear()
                it.addItems([f"{x}" for x in range(self.num_channels)])

        if not self.Fs == self.fixture.Fs:
            self.spectrogram_tab.spectrogram_view.update_sample_rate()
            self.Fs = self.fixture.Fs

        # if self.fixture.pts is not None:
        #     for ii in range(len(self.date_labels)):
        #         self.pressure_labels[ii].setText(
        #             f"{self.fixture.pts.pressure_mbar:.2f} mbar"
        #         )
        #         self.temp_labels[ii].setText(f"{self.fixture.pts.temperature_c:.2f} C")

        self.tabs.currentWidget().update()
        time_now = datetime.datetime.now()
        self.label_date.setText(time_now.strftime("%Y-%m-%d"))
        self.label_time.setText(time_now.strftime("%H:%M:%S"))

        # Get latest data timestamp
        time_acsense = self.fixture.get_latest_timestamp()
        for ii in range(len(self.date_labels)):
            self.date_labels[ii].setText(time_acsense.strftime("%Y-%m-%d"))
            self.time_labels[ii].setText(time_acsense.strftime("%H:%M:%S") + " UTC")


def acbotics_demo_display():
    import argparse

    parser = argparse.ArgumentParser(
        prog="Acbotics Demo Display",
        description="Launch a graphical display to visualize AcSense data streams",
        epilog="Written by Acbotics Research",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--iface_ip",
        type=str,
        default="127.0.0.1",
        help="IP of interface to bind, on host",
    )
    parser.add_argument("--use_mcast", action="store_true")
    parser.add_argument(
        "--mcast_group",
        type=str,
        default="224.1.1.1",
        help="Multicast group to collect data from (if using multicast)",
    )
    parser.add_argument(
        "--aco_port",
        type=int,
        default=9760,
        help="Port to collect acoustic data from",
    )
    parser.add_argument(
        "--sen_port",
        type=int,
        default=9770,
        help="Port to collect internal sensor data from",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        type=int,
        default=0,
        help="Set log verbosity level",
    )
    parser.add_argument(
        "--debug_python",
        "-d",
        action="store_true",
        help="Enable expanded debug of the Python code for this app",
    )
    parser.add_argument(
        "--debug_socket_in",
        action="store_true",
        help="Enable expanded debug for UdpSocketIn",
    )
    parser.add_argument(
        "--debug_udp_data",
        action="store_true",
        help="Enable expanded debug for UdpData",
    )
    parser.add_argument(
        "--debug_fft", action="store_true", help="Enable expanded debug for FFT"
    )

    args, unk = parser.parse_known_args()
    logger.info(f"Using arguments : \n{args.__dict__}")
    if len(unk) > 0:
        logger.warning(f"Unknown args ignored : {unk}")

    AcboticsDemoFixture.process_args(args)

    logger.debug("Setting up Qt App...")
    app = qtw.QApplication(sys.argv)

    scr_size = app.screens()[0].size()
    scr_width = scr_size.width()
    scr_height = scr_size.height()

    mw = MainWindow(scr_width, scr_height, args)

    logger.info("Starting up Qt Timer...")
    timer = pg.QtCore.QTimer()
    timer.timeout.connect(mw.update)
    timer.start(int(1 / 20 * 1e3))

    logger.info("Launching App...")

    if sys.version_info.major == 3 and sys.version_info.minor >= 12:
        sys.exit(app.exec())
    else:
        sys.exit(app.exec_())


if __name__ == "__main__":
    acbotics_demo_display()
