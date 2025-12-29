from pyqtgraph.Qt import QtWidgets as qtw  # type: ignore


class Pressure_Time_View(qtw.QFrame):
    def __init__(self, fixture):
        super(Pressure_Time_View, self).__init__()

        self.fixture = fixture
        # Tab 1 Column 2 : Status & Controls
        label1 = qtw.QLabel()
        label1.setText("AcSense Data")

        self.label_date = qtw.QLabel()
        self.label_date.setText("INIT DATE")

        self.label_time = qtw.QLabel()
        self.label_time.setText("INIT TIME")

        self.label_pressure = qtw.QLabel()
        self.label_pressure.setText("INIT PRESS")

        self.label_temp = qtw.QLabel()
        self.label_temp.setText("INIT TEMP")

        self.label_logging = qtw.QLabel()
        self.label_logging.setText("LOGGING TBD")

        self.pause_button = qtw.QPushButton("Pause")
        self.resume_button = qtw.QPushButton("Resume")

        self.pause_button.pressed.connect(self.fixture.pause_sensors)
        self.resume_button.pressed.connect(self.fixture.resume_sensors)

        self.layout = qtw.QVBoxLayout()

        self.layout.addWidget(label1)
        self.layout.addWidget(self.label_date)
        self.layout.addWidget(self.label_time)
        self.layout.addWidget(self.label_pressure)
        self.layout.addWidget(self.label_temp)
        self.layout.addWidget(self.label_logging)
        self.layout.addItem(qtw.QSpacerItem(1, 30))
        self.layout.addWidget(self.pause_button)
        self.layout.addWidget(self.resume_button)
        self.layout.addStretch()
        self.setLayout(self.layout)

    def update(self):
        latest_pts = self.fixture.get_pts()
        if "pressure_mbar" in latest_pts.keys():
            self.label_pressure.setText(f"{latest_pts['pressure_mbar']:.2f} mbar")
            self.label_temp.setText(f"{latest_pts['temperature_c']:.2f} C")
        time_acsense = self.fixture.get_latest_timestamp()
        self.label_date.setText(time_acsense.strftime("%Y-%m-%d"))
        self.label_time.setText(time_acsense.strftime("%H:%M:%S") + " UTC")
        if self.fixture.is_logging_enabled():
            self.label_logging.setText("LOGGING ENABLED")
        else:
            self.label_logging.setText("LOGGING DISABLED")
