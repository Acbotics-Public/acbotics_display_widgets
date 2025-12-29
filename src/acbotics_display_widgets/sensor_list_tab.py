from pyqtgraph.Qt import QtWidgets as qtw  # type: ignore
import pyqtgraph as pg  # type: ignore
import numpy as np
from scipy.spatial.transform import Rotation  # type: ignore
import sys
import logging
from functools import partial
import datetime
import copy
from netifaces import interfaces, ifaddresses, AF_INET

from .pressure_time_view import Pressure_Time_View

if sys.version_info.major == 3 and sys.version_info.minor >= 12:
    utcfromtimestamp = partial(datetime.datetime.fromtimestamp, tz=datetime.UTC)  # type: ignore
else:
    utcfromtimestamp = datetime.datetime.utcfromtimestamp  # type: ignore

logger = logging.getLogger(__name__)


class Sensor_List_Tab(qtw.QFrame):
    def __init__(self, fixture):
        super(Sensor_List_Tab, self).__init__()
        self.fixture = fixture

        self.layout = qtw.QHBoxLayout()
        self.date_labels = []
        self.time_labels = []
        self.pressure_labels = []
        self.temp_labels = []

        scroll1 = qtw.QScrollArea()
        # scroll1.setVerticalScrollBarPolicy(pg.QtCore.Qt.ScrollBarAlwaysOn)
        scroll1.setHorizontalScrollBarPolicy(pg.QtCore.Qt.ScrollBarAlwaysOff)

        col1 = qtw.QWidget()
        col1.layout = qtw.QVBoxLayout()

        # Tab 1 Column 1 : Plots

        # Tab 1 Column 2 : Status & Controls
        label1 = qtw.QLabel()
        label1.setText("RTC Data")

        rtc_label_date = qtw.QLabel()
        rtc_label_date.setText("INIT RTC DATE")

        rtc_label_time = qtw.QLabel()
        rtc_label_time.setText("INIT RTC TIME")

        label2 = qtw.QLabel()
        label2.setText("EPT Data")

        ept_label_pressure = qtw.QLabel()
        ept_label_pressure.setText("INIT EPT PRESS")

        ept_label_temp = qtw.QLabel()
        ept_label_temp.setText("INIT EPT TEMP")

        label3 = qtw.QLabel()
        label3.setText("IMU Data")

        imu_label_accel_x = qtw.QLabel()
        imu_label_accel_x.setText("INIT IMU ACCEL X")
        imu_label_accel_y = qtw.QLabel()
        imu_label_accel_y.setText("INIT IMU ACCEL Y")
        imu_label_accel_z = qtw.QLabel()
        imu_label_accel_z.setText("INIT IMU ACCEL Z")

        imu_label_gyro_x = qtw.QLabel()
        imu_label_gyro_x.setText("INIT IMU GYRO X")
        imu_label_gyro_y = qtw.QLabel()
        imu_label_gyro_y.setText("INIT IMU GYRO Y")
        imu_label_gyro_z = qtw.QLabel()
        imu_label_gyro_z.setText("INIT IMU GYRO Z")

        # imu_label_pitch = qtw.QLabel()
        # imu_label_pitch.setText("INIT IMU PITCH")
        # imu_label_roll = qtw.QLabel()
        # imu_label_roll.setText("INIT IMU ROLL")

        labelBNO = qtw.QLabel()
        labelBNO.setText("BNO Data")

        bno_label_accel_x = qtw.QLabel()
        bno_label_accel_x.setText("INIT BNO ACCEL X")
        bno_label_accel_y = qtw.QLabel()
        bno_label_accel_y.setText("INIT BNO ACCEL Y")
        bno_label_accel_z = qtw.QLabel()
        bno_label_accel_z.setText("INIT BNO ACCEL Z")

        bno_label_gyro_x = qtw.QLabel()
        bno_label_gyro_x.setText("INIT BNO GYRO X")
        bno_label_gyro_y = qtw.QLabel()
        bno_label_gyro_y.setText("INIT BNO GYRO Y")
        bno_label_gyro_z = qtw.QLabel()
        bno_label_gyro_z.setText("INIT BNO GYRO Z")

        bno_label_mag_x = qtw.QLabel()
        bno_label_mag_x.setText("INIT BNO MAG X")
        bno_label_mag_y = qtw.QLabel()
        bno_label_mag_y.setText("INIT BNO MAG Y")
        bno_label_mag_z = qtw.QLabel()
        bno_label_mag_z.setText("INIT BNO MAG Z")

        # bno_label_quat_i = qtw.QLabel()
        # bno_label_quat_i.setText("INIT BNO QUAT i")
        # bno_label_quat_j = qtw.QLabel()
        # bno_label_quat_j.setText("INIT BNO QUAT j")
        # bno_label_quat_k = qtw.QLabel()
        # bno_label_quat_k.setText("INIT BNO QUAT k")
        # bno_label_quat_r = qtw.QLabel()
        # bno_label_quat_r.setText("INIT BNO QUAT r")

        bno_label_yaw = qtw.QLabel()
        bno_label_yaw.setText("INIT BNO YAW")
        bno_label_pitch = qtw.QLabel()
        bno_label_pitch.setText("INIT BNO PITCH")
        bno_label_roll = qtw.QLabel()
        bno_label_roll.setText("INIT BNO ROLL")

        self.ip_address_label = qtw.QLabel("IP ADDRESSES")

        col1.layout.addWidget(label1)
        col1.layout.addWidget(rtc_label_date)
        col1.layout.addWidget(rtc_label_time)
        col1.layout.addItem(qtw.QSpacerItem(1, 30))
        col1.layout.addWidget(label2)
        col1.layout.addWidget(ept_label_pressure)
        col1.layout.addWidget(ept_label_temp)
        col1.layout.addItem(qtw.QSpacerItem(1, 30))
        col1.layout.addWidget(label3)
        col1.layout.addWidget(imu_label_accel_x)
        col1.layout.addWidget(imu_label_accel_y)
        col1.layout.addWidget(imu_label_accel_z)
        col1.layout.addItem(qtw.QSpacerItem(1, 10))
        col1.layout.addWidget(imu_label_gyro_x)
        col1.layout.addWidget(imu_label_gyro_y)
        col1.layout.addWidget(imu_label_gyro_z)

        col1.layout.addItem(qtw.QSpacerItem(1, 30))
        col1.layout.addWidget(labelBNO)
        col1.layout.addWidget(bno_label_accel_x)
        col1.layout.addWidget(bno_label_accel_y)
        col1.layout.addWidget(bno_label_accel_z)
        col1.layout.addItem(qtw.QSpacerItem(1, 10))
        col1.layout.addWidget(bno_label_gyro_x)
        col1.layout.addWidget(bno_label_gyro_y)
        col1.layout.addWidget(bno_label_gyro_z)
        col1.layout.addItem(qtw.QSpacerItem(1, 10))
        col1.layout.addWidget(bno_label_mag_x)
        col1.layout.addWidget(bno_label_mag_y)
        col1.layout.addWidget(bno_label_mag_z)
        col1.layout.addItem(qtw.QSpacerItem(1, 10))
        col1.layout.addWidget(bno_label_yaw)
        col1.layout.addWidget(bno_label_pitch)
        col1.layout.addWidget(bno_label_roll)
        col1.layout.addWidget(self.ip_address_label)

        # col1.layout.addItem(qtw.QSpacerItem(1, 10))
        # col1.layout.addWidget(imu_label_pitch)
        # col1.layout.addWidget(imu_label_roll)
        col1.layout.addItem(qtw.QSpacerItem(1, 30))
        col1.layout.addStretch()

        col1.setLayout(col1.layout)

        self.labels_other = {
            "rtc_date": rtc_label_date,
            "rtc_time": rtc_label_time,
            "ept_pressure": ept_label_pressure,
            "ept_temp": ept_label_temp,
            "imu_accel_x": imu_label_accel_x,
            "imu_accel_y": imu_label_accel_y,
            "imu_accel_z": imu_label_accel_z,
            "imu_gyro_x": imu_label_gyro_x,
            "imu_gyro_y": imu_label_gyro_y,
            "imu_gyro_z": imu_label_gyro_z,
            "bno_accel_x": bno_label_accel_x,
            "bno_accel_y": bno_label_accel_y,
            "bno_accel_z": bno_label_accel_z,
            "bno_gyro_x": bno_label_gyro_x,
            "bno_gyro_y": bno_label_gyro_y,
            "bno_gyro_z": bno_label_gyro_z,
            "bno_mag_x": bno_label_mag_x,
            "bno_mag_y": bno_label_mag_y,
            "bno_mag_z": bno_label_mag_z,
            "bno_yaw": bno_label_yaw,
            "bno_pitch": bno_label_pitch,
            "bno_roll": bno_label_roll,
            # "imu_pitch": imu_label_pitch,
            # "imu_roll": imu_label_roll,
        }

        scroll1.setWidget(col1)

        col1.setFixedWidth(scroll1.width() - scroll1.verticalScrollBar().width() - 2)

        self.pressure_view = Pressure_Time_View(self.fixture)
        # Tab 1 : Assemble Columns
        self.layout.addWidget(scroll1)
        self.layout.addWidget(self.pressure_view)

        self.setLayout(self.layout)

    def update(self):
        latest_imu = self.fixture.get_imu()
        if "accel_x" in latest_imu:
            self.labels_other["imu_accel_x"].setText(
                f"ACCEL X = {latest_imu['accel_x'] * 16 / 2**15:.3f} g"
            )
            self.labels_other["imu_accel_y"].setText(
                f"ACCEL Y = {latest_imu['accel_y'] * 16 / 2**15:.3f} g"
            )
            self.labels_other["imu_accel_z"].setText(
                f"ACCEL Z = {latest_imu['accel_z'] * 16 / 2**15:.3f} g"
            )

            self.labels_other["imu_gyro_x"].setText(
                f"GYRO X = {latest_imu['gyro_x'] * 2000 / 2**15:.3f} deg/s"
            )
            self.labels_other["imu_gyro_y"].setText(
                f"GYRO Y = {latest_imu['gyro_y'] * 2000 / 2**15:.3f} deg/s"
            )
            self.labels_other["imu_gyro_z"].setText(
                f"GYRO Z = {latest_imu['gyro_z'] * 2000 / 2**15:.3f} deg/s"
            )

            # self.labels_other["imu_pitch"].setText(
            #     f"PITCH = {imu.pitch_ned_deg:.2f} deg"
            # )
            # self.labels_other["imu_roll"].setText(
            #     f"ROLL = {imu.roll_ned_deg:.2f} deg"
            # )
        latest_bno_acc = self.fixture.get_bno_accel()

        if "sense_x" in latest_bno_acc:
            self.labels_other["bno_accel_x"].setText(
                f"ACCEL X = {latest_bno_acc['sense_x'] / 9.8:.3f} g"
            )
            self.labels_other["bno_accel_y"].setText(
                f"ACCEL Y = {latest_bno_acc['sense_y']/ 9.8:.3f} g"
            )
            self.labels_other["bno_accel_z"].setText(
                f"ACCEL Z = {latest_bno_acc['sense_z'] / 9.8:.3f} g"
            )

        latest_bno_gyro = self.fixture.get_bno_gyro()
        if "sense_x" in latest_bno_gyro:

            self.labels_other["bno_gyro_x"].setText(
                f"GYRO X = {latest_bno_gyro['sense_x']:.3f} deg/s"
            )
            self.labels_other["bno_gyro_y"].setText(
                f"GYRO Y = {latest_bno_gyro['sense_y']:.3f} deg/s"
            )
            self.labels_other["bno_gyro_z"].setText(
                f"GYRO Z = {latest_bno_gyro['sense_z']:.3f} deg/s"
            )

        latest_bno_mag = self.fixture.get_bno_mag()
        if "sense_x" in latest_bno_mag:

            self.labels_other["bno_mag_x"].setText(
                f"MAG X = {latest_bno_mag['sense_x']:.3f} T"
            )
            self.labels_other["bno_mag_y"].setText(
                f"MAG Y = {latest_bno_mag['sense_y']:.3f} T"
            )
            self.labels_other["bno_mag_z"].setText(
                f"MAG Z = {latest_bno_mag['sense_z']:.3f} T"
            )
        latest_bnr = self.fixture.get_bnr()
        if "quat_i" in latest_bnr:

            quat = [
                latest_bnr["quat_i"],
                latest_bnr["quat_j"],
                latest_bnr["quat_k"],
                latest_bnr["quat_r"],
            ]
            norm = np.sqrt(quat[0] ** 2 + quat[1] ** 2 + quat[2] ** 2 + quat[3] ** 2)

            if norm > 0.9 and norm < 1.1 and not all([x == 0 for x in quat]):
                try:
                    rot = Rotation.from_quat(quat)
                    pitch, roll, yaw = rot.as_euler("xyz", degrees=True)

                    self.labels_other["bno_roll"].setText(
                        f"ROLL (X)  = {roll:8.3f} deg"
                    )
                    self.labels_other["bno_pitch"].setText(
                        f"PITCH (Y) = {pitch:8.3f} deg"
                    )
                    self.labels_other["bno_yaw"].setText(f"YAW (Z)   = {-yaw:8.3f} deg")
                except ValueError as e:
                    logger.error(e)
        latest_ept = self.fixture.get_ept()
        if "pressure_mbar" in latest_ept.keys():
            self.labels_other["ept_pressure"].setText(
                f"{latest_ept['pressure_mbar']:.2f} mbar"
            )
            self.labels_other["ept_temp"].setText(
                f"{latest_ept['temperature_c']:.2f} C"
            )

        latest_rtc = self.fixture.get_rtc()
        if "rtc_time" in latest_bnr:
            time_rtc = utcfromtimestamp(latest_rtc["rtc_time"])
            self.labels_other["rtc_date"].setText(time_rtc.strftime("%Y-%m-%d"))
            self.labels_other["rtc_time"].setText(time_rtc.strftime("%H:%M:%S"))

        ips = self.ip4_addresses()
        ip_str = "IP ADDRESSES: "
        for ip in ips:
            ip_str += repr(ip) + "  "

        self.ip_address_label.setText(ip_str)

        self.pressure_view.update()

    def ip4_addresses(self):
        ip_list = []
        for interface in interfaces():
            for link in ifaddresses(interface).get(AF_INET, ()):
                ip_list.append(link["addr"])
        return ip_list
