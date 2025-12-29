from pyqtgraph.Qt import QtWidgets as qtw  # type: ignore
import numpy as np
import pyqtgraph as pg  # type: ignore
from matplotlib import colors


class Sensor_Time_Series_View(qtw.QFrame):
    @staticmethod
    def mpl2rgb(name: str):
        tup = colors.to_rgb(name)
        return tuple([int(x * 255) for x in tup])

    def __init__(self, fixture):
        super(Sensor_Time_Series_View, self).__init__()
        self.fixture = fixture
        self.layout = qtw.QHBoxLayout()
        plot_lines = pg.PlotWidget()
        # plot_lines.plotItem.plot([1, 2, 3, 4], [3, 2, 3, 1])
        col1 = qtw.QWidget()
        col1.layout = qtw.QVBoxLayout()

        # plot_lines.plotItem.setLabel("bottom", "Samples", units="S")
        plot_lines.plotItem.setLabel("bottom", "Time", units="s")
        # plot_lines.plotItem.enableAutoRange("xy", False)
        # plot_lines.plotItem.enableAutoRange("x", False)
        # plot_lines.plotItem.setXRange(0 - 10, self.history_raw + 10, padding=0)
        # plot_lines.plotItem.setYRange(-1.1, 1.1, padding=0)
        plot_lines.plotItem.setYRange(-0.005, 0.005, padding=0)
        plot_lines.plotItem.enableAutoRange("y", True)
        plot_lines.plotItem.setMouseEnabled(x=False, y=False)
        self.raw_data_curve = plot_lines.plotItem.plot(
            pen=self.mpl2rgb(f"C{self.fixture.current_ch}")
        )
        col1.layout.addWidget(plot_lines)
        col1.setLayout(col1.layout)
        col2 = qtw.QWidget()
        col2.layout = qtw.QVBoxLayout()

        label2 = qtw.QLabel()
        label2.setText("Controls")

        line1 = qtw.QWidget()
        line1.layout = qtw.QHBoxLayout()
        label3 = qtw.QLabel()
        label3.setText("Ch:")
        self.ctrl_sensor = qtw.QComboBox()

        self.active_sensor = ""

        self.ctrl_sensor.addItems(
            [sensor for sensor in sorted(self.fixture.get_sensor_names())]
        )
        self.ctrl_sensor.setMinimumContentsLength(2)
        self.ctrl_sensor.setMinimumHeight(30)

        self.ctrl_signals = qtw.QComboBox()

        self.active_signal = ""

        self.ctrl_signals.setMinimumContentsLength(2)
        self.ctrl_signals.setMinimumHeight(30)

        line1.layout.addWidget(label3)
        line1.layout.addWidget(self.ctrl_sensor)
        line1.layout.addWidget(self.ctrl_signals)
        line1.setLayout(line1.layout)

        self.ctrl_sensor.activated.connect(self.set_active_sensor)
        self.ctrl_signals.activated.connect(self.set_active_signal)

        col2.layout.addWidget(label2)
        col2.layout.addWidget(line1)
        col2.layout.addStretch()
        col2.setLayout(col2.layout)

        # Tab 1 : Assemble Columns
        self.layout.addWidget(col1)
        self.layout.addWidget(col2)

        self.setLayout(self.layout)

    def create_widget(self):
        pass

    def set_active_sensor(self, sensor_index):
        sensor = self.ctrl_sensor.currentText()
        if not sensor == self.active_sensor:
            self.active_sensor = sensor
            self.available_signals = self.fixture.get_sensor_signals(self.active_sensor)
            self.available_signals.extend(
                [""]
            )  # add null for blanking and to gurantee at least one option
            self.active_signal = self.available_signals[0]
            self.update_signal_controls(self.available_signals)

    def update_signal_controls(self, signals):
        self.ctrl_signals.clear()
        self.ctrl_signals.addItems([signal for signal in sorted(signals)])

    def set_active_signal(self, signal_index):
        signal = self.ctrl_signals.currentText()
        self.active_signal = signal

    def update(self):

        if (
            self.active_sensor in self.fixture.get_sensor_names()
            and self.active_signal
            in self.fixture.get_sensor_signals(self.active_sensor)
        ):
            data_raw = self.fixture.get_signal_buffer(
                self.active_sensor, self.active_signal
            )
            times = data_raw[0]
            trace = data_raw[1]
            if times is not None:
                self.raw_data_curve.setData(
                    times,
                    trace,
                )
        else:
            pass  # clear the plot?
