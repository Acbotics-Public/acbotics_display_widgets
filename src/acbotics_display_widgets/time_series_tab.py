from pyqtgraph.Qt import QtWidgets as qtw  # type: ignore
import pyqtgraph as pg  # type: ignore
from matplotlib import colors
import numpy as np

from .pressure_time_view import Pressure_Time_View


class Time_Series_Tab(qtw.QFrame):
    @staticmethod
    def mpl2rgb(name: str):
        tup = colors.to_rgb(name)
        return tuple([int(x * 255) for x in tup])

    def __init__(self, fixture, update_div=8):
        super(Time_Series_Tab, self).__init__()
        self.fixture = fixture
        self.processing = False
        self.update_div = update_div
        self.last_update_count = 0
        self.current_ch = self.fixture.current_ch
        # Create time-series tab
        # ======================
        self.layout = qtw.QHBoxLayout()
        self.num_channels = self.fixture.num_channels

        col1 = qtw.QWidget()
        col1.layout = qtw.QVBoxLayout()
        col2 = qtw.QWidget()
        col2.layout = qtw.QVBoxLayout()

        self.ch_controls = []

        # Tab 1 Column 1 : Plots

        plot_lines = pg.PlotWidget()
        # plot_lines.plotItem.plot([1, 2, 3, 4], [3, 2, 3, 1])

        # plot_lines.plotItem.setLabel("bottom", "Samples", units="S")
        plot_lines.plotItem.setLabel("bottom", "Time", units="s")
        # plot_lines.plotItem.enableAutoRange("xy", False)
        # plot_lines.plotItem.enableAutoRange("x", False)
        # plot_lines.plotItem.setXRange(0 - 10, self.history_raw + 10, padding=0)
        # plot_lines.plotItem.setYRange(-1.1, 1.1, padding=0)
        plot_lines.plotItem.setYRange(-0.005, 0.005, padding=0)
        plot_lines.plotItem.enableAutoRange("y", True)
        plot_lines.plotItem.setMouseEnabled(x=False, y=False)
        # plot_lines.setMaximumHeight(self.height // 3)

        # self.curves = []
        # for ch in range(self.num_channels):
        #     self.curves.append(
        #         plot_lines.plotItem.plot(pen=self.mpl2rgb(f"C{ch}"))
        #     )

        self.raw_data_curve = plot_lines.plotItem.plot(
            pen=self.mpl2rgb(f"C{self.fixture.current_ch}")
        )

        # col1.layout.addWidget(self.label1_1)
        col1.layout.addWidget(plot_lines)
        # col1.layout.addWidget(self.plot_gram)
        col1.setLayout(col1.layout)

        self.pressure_view = Pressure_Time_View(self.fixture)

        label2 = qtw.QLabel()
        label2.setText("Controls")

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
        self.ch_controls.append(ctrl1)

        col2.layout.addWidget(self.pressure_view)
        col2.layout.addItem(qtw.QSpacerItem(1, 30))
        col2.layout.addWidget(label2)
        col2.layout.addWidget(line1)
        col2.layout.addStretch()
        col2.setLayout(col2.layout)

        # Tab 1 : Assemble Columns
        self.layout.addWidget(col1)
        self.layout.addWidget(col2)

        self.setLayout(self.layout)

    def set_curr_ch(self, index):
        change = self.fixture.set_current_channel(index)
        # self.current_ch = self.fixture.current_ch
        # if change:
        #     self.ctrl1.setCurrentIndex(index)
        #     self.plot_gram.setLabel(
        #         "bottom", f"Ch {self.current_ch} - Frequency", units="Hz"
        #     )
        #     for it in self.ch_controls:
        #         it.activated.disconnect(self.set_curr_ch)
        #         it.setCurrentIndex(index)
        #         it.activated.connect(self.set_curr_ch)
        # else:
        #     print("Failed to change channe to %d" % (index))

    def update(self):
        self.pressure_view.update()

        if self.processing:
            return
        if not self.last_update_count == 0:
            self.last_update_count -= 1
            return
        self.last_update_count = self.update_div
        self.processing = True

        data_raw = self.fixture.get_raw_aco_data()
        times = data_raw[0]
        traces = data_raw[1]
        # self.raw_data_curve.setData(
        #     -np.arange(len(data_raw))[::-1] / self.fixture.Fs,
        #     np.array(data_raw),
        # )
        if times is not None:
            self.raw_data_curve.setData(
                times / self.fixture.Fs,
                traces[self.fixture.current_ch],
            )
        if not self.current_ch == self.fixture.current_ch:
            self.current_ch = self.fixture.current_ch
            # self.ctrl1.setCurrentIndex(self.current_ch)
            for it in self.ch_controls:
                it.activated.disconnect(self.set_curr_ch)
                it.setCurrentIndex(self.current_ch)
                it.activated.connect(self.set_curr_ch)
        self.processing = False
