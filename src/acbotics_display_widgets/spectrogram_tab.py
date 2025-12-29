from pyqtgraph.Qt import QtWidgets as qtw  # type: ignore
import pyqtgraph as pg  # type: ignore
from .spectrogram_view import Spectrogram_View
from matplotlib import colors

from .pressure_time_view import Pressure_Time_View


class Spectrogram_Tab(qtw.QFrame):
    @staticmethod
    def mpl2rgb(name: str):
        tup = colors.to_rgb(name)
        return tuple([int(x * 255) for x in tup])

    def __init__(self, fixture):
        super(Spectrogram_Tab, self).__init__()
        self.fixture = fixture
        self.current_ch = self.fixture.current_ch
        # Create spectrogram tab
        # ======================
        self.layout = qtw.QHBoxLayout()
        self.num_channels = self.fixture.num_channels
        col1 = qtw.QWidget()
        col1.layout = qtw.QVBoxLayout()
        col2 = qtw.QWidget()
        col2.layout = qtw.QVBoxLayout()
        col3 = qtw.QWidget()
        col3.layout = qtw.QVBoxLayout()

        self.spectrogram_view = Spectrogram_View(self.fixture)
        self.spectrogram_view.create_widget()

        col1.layout.addWidget(self.spectrogram_view)
        col1.setLayout(col1.layout)
        self.date_labels = []
        self.time_labels = []
        self.pressure_labels = []
        self.temp_labels = []

        col2.setLayout(col2.layout)

        self.pressure_view = Pressure_Time_View(self.fixture)

        label2 = qtw.QLabel()
        label2.setText("Controls")
        self.ch_controls = []

        line1 = qtw.QWidget()
        line1.layout = qtw.QHBoxLayout()
        label3 = qtw.QLabel()
        label3.setText("Ch:")
        ctrl1 = qtw.QComboBox()
        ctrl1.addItems([f"{x}" for x in range(self.num_channels)])
        ctrl1.setMinimumContentsLength(2)
        ctrl1.setMinimumHeight(30)
        line1.layout.addWidget(label3)
        line1.layout.addWidget(ctrl1)
        line1.setLayout(line1.layout)

        ctrl1.activated.connect(self.set_curr_ch)
        self.ctrl1 = ctrl1
        self.ch_controls.append(ctrl1)

        col3.layout.addWidget(self.pressure_view)

        col3.layout.addItem(qtw.QSpacerItem(1, 30))
        col3.layout.addWidget(label2)
        col3.layout.addWidget(line1)
        # col3.layout.addWidget(ctrl2)
        # col3.layout.addWidget(line2)
        # col3.layout.addWidget(line3)
        col3.layout.addStretch()
        col3.setLayout(col3.layout)

        # Tab 1 : Assemble Columns
        self.layout.addWidget(col1, stretch=6)
        self.layout.addWidget(col2, stretch=1)
        self.layout.addWidget(col3)

        self.setLayout(self.layout)

    def update_current_channel_widget(self):
        for it in self.ch_controls:
            it.activated.disconnect(self.set_curr_ch)
            it.setCurrentIndex(self.current_ch)
            it.activated.connect(self.set_curr_ch)

    def set_curr_ch(self, index):
        change = self.fixture.set_current_channel(index)

    def gamepad_callbacks(self, event_info):
        if (
            event_info["ev_type"] == "Key"
            and event_info["code"] == "BTN_THUMBR"
            and event_info["state"] == 1
        ):
            self.spectrogram_view.spectrogram_reset_callback()
            return True
        if event_info["ev_type"] == "Absolute" and event_info["code"] == "ABS_RY":
            self.spectrogram_view.spectrogram_level_callback(event_info["state"])
            return True
        if event_info["ev_type"] == "Absolute" and event_info["code"] == "ABS_Y":
            self.spectrogram_view.spectrogram_width_callback(event_info["state"])
            return True

    def update(self):
        self.spectrogram_view.update()

        if not self.current_ch == self.fixture.current_ch:
            self.current_ch = self.fixture.current_ch
            self.ctrl1.setCurrentIndex(self.current_ch)
            self.spectrogram_view.plot_gram.setLabel(
                "bottom", f"Ch {self.current_ch} - Frequency", units="Hz"
            )
            for it in self.ch_controls:
                it.activated.disconnect(self.set_curr_ch)
                it.setCurrentIndex(self.current_ch)
                it.activated.connect(self.set_curr_ch)

        self.pressure_view.update()
