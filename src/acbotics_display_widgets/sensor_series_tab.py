from pyqtgraph.Qt import QtWidgets as qtw  # type: ignore
import pyqtgraph as pg  # type: ignore
from .sensor_time_series_view import Sensor_Time_Series_View
from matplotlib import colors

from .pressure_time_view import Pressure_Time_View


class Sensor_Series_Tab(qtw.QFrame):
    @staticmethod
    def mpl2rgb(name: str):
        tup = colors.to_rgb(name)
        return tuple([int(x * 255) for x in tup])

    def __init__(self, fixture):
        super(Sensor_Series_Tab, self).__init__()
        self.fixture = fixture
        # Create spectrogram tab
        # ======================
        self.layout = qtw.QHBoxLayout()
        col1 = qtw.QWidget()
        col1.layout = qtw.QVBoxLayout()
        col2 = qtw.QWidget()
        col2.layout = qtw.QVBoxLayout()
        col3 = qtw.QWidget()
        col3.layout = qtw.QVBoxLayout()

        self.sensor_view = Sensor_Time_Series_View(self.fixture)
        self.sensor_view.create_widget()

        col1.layout.addWidget(self.sensor_view)
        col1.setLayout(col1.layout)
        self.date_labels = []
        self.time_labels = []
        self.pressure_labels = []
        self.temp_labels = []

        self.pressure_view = Pressure_Time_View(self.fixture)

        col3.layout.addWidget(self.pressure_view)

        col3.layout.addItem(qtw.QSpacerItem(1, 30))
        col3.layout.addStretch()
        col3.setLayout(col3.layout)

        # Tab 1 : Assemble Columns
        self.layout.addWidget(col1, stretch=6)
        # self.layout.addWidget(col2, stretch=1)
        self.layout.addWidget(col3)

        self.setLayout(self.layout)

    def gamepad_callbacks(self, event_info):
        return False

    def update(self):
        self.sensor_view.update()
        self.pressure_view.update()
