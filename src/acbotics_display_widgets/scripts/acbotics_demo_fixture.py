from collections import deque
import numpy as np
import os
import acbotics_interface as ac
import logging
import yaml
import sys
from functools import partial
import datetime
import threading


from acbotics_pipeline.fixtures.fixture import Fixture
from acbotics_pipeline.blocks.cpp_interface import (
    Aco_To_Data_Container,
    FFT_To_Data_Container,
    Pts_To_Data_Container,
    Ept_To_Data_Container,
    Rtc_To_Data_Container,
    Imu_To_Data_Container,
    Bno_To_Data_Container,
    Bnr_To_Data_Container,
)


from acbotics_pipeline.blocks.output.buffer import (
    Out_Buffer_Constant_Rate,
    Out_Buffer_FFT,
    Out_Buffer_Sensor,
)


ac.init_logger()
logger = logging.getLogger(__name__)
LOWERCASE_MU = "\u03bc"
if sys.version_info.major == 3 and sys.version_info.minor >= 12:
    utcfromtimestamp = partial(datetime.datetime.fromtimestamp, tz=datetime.UTC)  # type: ignore
else:
    utcfromtimestamp = datetime.datetime.utcfromtimestamp  # type: ignore


class AcboticsDemoFixture(Fixture):
    def configure_logger_outdir(self):
        outdir = os.path.expanduser("~/acsense_data/")
        if not os.path.isdir(outdir):
            os.mkdir(outdir)
        self.outdir = outdir

        self.cpp_blocks["ACO_LOG"].set_outdir(outdir)
        self.cpp_blocks["SENSE_LOG"].set_outdir(outdir)
        self.gps_logger.set_outdir(outdir)

    def get_logger_paths(self):
        paths = []
        paths.extend(self.cpp_blocks["ACO_LOG"].get_current_paths())
        paths.extend(self.cpp_blocks["SENSE_LOG"].get_current_paths())
        paths.extend(self.gps_logger.get_current_paths())
        return paths

    def switch_logging_all(self, val):
        if val:
            self.logging_enabled = True
            self.gps_logger.start_logging()
            self.cpp_blocks["ACO_LOG"].start_logging()
            self.cpp_blocks["SENSE_LOG"].start_logging()
        else:
            self.logging_enabled = False
            self.gps_logger.stop_logging()
            self.cpp_blocks["ACO_LOG"].stop_logging()
            self.cpp_blocks["SENSE_LOG"].stop_logging()

    def get_raw_aco_data(self, chans=None):
        return self.aco_buffer.get_buffer(chans)

    def get_fft_data(self, chans=None):
        return self.fft_buffer.get_buffer(chans)

    def get_fft_sample_rate(self):
        return self.fft_buffer.get_sample_rate()

    def get_pts(self):
        return self.pts_buffer.get_latest()

    def get_ept(self):
        return self.ept_buffer.get_latest()

    def get_rtc(self):
        return self.rtc_buffer.get_latest()

    def get_imu(self):
        return self.imu_buffer.get_latest()

    def get_bnr(self):
        return self.bnr_buffer.get_latest()

    def get_bno_accel(self):
        return self.bno_buffer_accel.get_latest()

    def get_bno_gyro(self):
        return self.bno_buffer_gyro.get_latest()

    def get_bno_mag(self):
        return self.bno_buffer_mag.get_latest()

    def __init__(self, args):
        self.args = args
        self.current_ch = 1
        self.Fs = 50000
        self.num_channels = 8
        self.NFFT = 512
        self.noverlap = self.NFFT // 2
        self.window = np.hanning(self.NFFT)
        self.outdir = ""
        self.sensors = {}
        self.logging_enabled = False

        self.data_fft = [[1, 2], [3, 4]]

        super().__init__()

    def build(self):
        args = self.args

        self.gps_logger = ac.Logger_GPS_Host_Block()
        self.gps_logger.run()

        self.add_cpp_block(
            "ACO_IN",
            ac.UdpSocketIn(
                args.use_mcast, args.iface_ip, args.aco_port, args.mcast_group
            ),
        )
        self.translate_block = Aco_To_Data_Container()
        self.cpp_blocks["ACO_IN"].register_client_aco(
            self.translate_block.cpp_queue_aco
        )
        self.add_block(self.translate_block, output_signal="ACO")

        # Buffer block for GUI display
        self.aco_buffer = Out_Buffer_Constant_Rate(samples_to_keep=52734)
        self.add_block(
            self.aco_buffer,
            input_signal="ACO",
        )

        self.add_cpp_block(
            "SENSE_IN",
            ac.UdpSocketIn(
                args.use_mcast, args.iface_ip, args.sen_port, args.mcast_group
            ),
        )
        self.add_cpp_block("FFT", ac.FFT.create())
        self.cpp_blocks["ACO_IN"].register_client_aco(
            self.cpp_blocks["FFT"].get_input_queue()
        )

        self.translate_block_fft = FFT_To_Data_Container()
        self.cpp_blocks["FFT"].register_client(self.translate_block_fft.cpp_queue_fft)
        self.add_block(self.translate_block_fft, output_signal="FFT")
        # Buffer block for GUI display
        self.fft_buffer = Out_Buffer_FFT(samples_to_keep=512)
        self.add_block(
            self.fft_buffer,
            input_signal="FFT",
        )

        self.add_cpp_block("ACO_LOG", ac.LoggerBlock())
        self.cpp_blocks["ACO_IN"].register_client_aco(
            self.cpp_blocks["ACO_LOG"].get_input_queue()
        )

        self.add_cpp_block("SENSE_LOG", ac.Logger_Sensor_Block())
        self.cpp_blocks["SENSE_IN"].register_client(self.cpp_blocks["SENSE_LOG"])

        _config = {}
        # if args.config and os.path.isfile(args.config):
        #     with open(args.config) as ff:
        #         try:
        #             _config = yaml.safe_load(ff)["config"]
        #         except Exception as e:
        #             logger.error(f"Could not load requested configuration file!\n{e}")

        _config = {k.lower(): v for k, v in _config.items()}

        if "nfft" in _config:
            self.NFFT = _config["nfft"]
            self.noverlap = self.NFFT // 2

        if "noverlap" in _config and _config["noverlap"] < self.NFFT:
            self.noverlap = _config["noverlap"]

        self.cpp_blocks["FFT"].set_NFFT(self.NFFT)
        self.cpp_blocks["FFT"].set_noverlap(self.noverlap)

        if "f_start" in _config and "f_end" in _config:
            self.cpp_blocks["FFT"].add_frequency_band_min_max(
                _config["f_start"], _config["f_end"]
            )
        else:
            self.cpp_blocks["FFT"].add_frequency_band_min_max(500, 8000)

        if len(_config.keys()) > 0:
            ss_len = np.max([len(x) for x in _config.keys()])
            ss_config = "Configuration:\n"
            for key, val in _config.items():
                ss_config += f"{key:>{ss_len}s} : {val}\n"
            logger.info(ss_config)

        # configure sensors
        pts_queue = ac.Q_PTS.create()
        self.translate_block_pts = Pts_To_Data_Container(pts_queue)
        self.cpp_blocks["SENSE_IN"].register_client_pts(pts_queue)
        self.add_block(self.translate_block_pts, output_signal="PTS")
        self.pts_buffer = Out_Buffer_Sensor(samples_to_keep=100)
        self.add_block(self.pts_buffer, input_signal="PTS")

        ept_queue = ac.Q_EPT.create()
        self.translate_block_ept = Ept_To_Data_Container(ept_queue)
        self.cpp_blocks["SENSE_IN"].register_client_ept(ept_queue)
        self.add_block(self.translate_block_ept, output_signal="EPT")
        self.ept_buffer = Out_Buffer_Sensor(samples_to_keep=100)
        self.add_block(self.ept_buffer, input_signal="EPT")

        rtc_queue = ac.Q_RTC.create()
        self.translate_block_rtc = Rtc_To_Data_Container(rtc_queue)
        self.cpp_blocks["SENSE_IN"].register_client_rtc(rtc_queue)
        self.add_block(self.translate_block_rtc, output_signal="RTC")
        self.rtc_buffer = Out_Buffer_Sensor(samples_to_keep=100)
        self.add_block(self.rtc_buffer, input_signal="RTC")

        imu_queue = ac.Q_IMU.create()
        self.translate_block_imu = Imu_To_Data_Container(imu_queue)
        self.cpp_blocks["SENSE_IN"].register_client_imu(imu_queue)
        self.add_block(self.translate_block_imu, output_signal="IMU")
        self.imu_buffer = Out_Buffer_Sensor(samples_to_keep=100)
        self.add_block(self.imu_buffer, input_signal="IMU")

        bnr_queue = ac.Q_BNR.create()
        self.translate_block_bnr = Bnr_To_Data_Container(bnr_queue)
        self.cpp_blocks["SENSE_IN"].register_client_bnr(bnr_queue)
        self.add_block(self.translate_block_bnr, output_signal="BNR")
        self.bnr_buffer = Out_Buffer_Sensor(samples_to_keep=100)
        self.add_block(self.bnr_buffer, input_signal="BNR")

        # bno has 3 separate streams that need to be split
        bno_queue = ac.Q_BNO.create()
        self.translate_block_bno = Bno_To_Data_Container(bno_queue)
        self.cpp_blocks["SENSE_IN"].register_client_bno(bno_queue)
        self.add_block(self.translate_block_bno, output_signal="BNO")
        self.bno_buffer_accel = Out_Buffer_Sensor(samples_to_keep=100)
        self.bno_buffer_mag = Out_Buffer_Sensor(samples_to_keep=100)
        self.bno_buffer_gyro = Out_Buffer_Sensor(samples_to_keep=100)
        self.add_block(self.bno_buffer_accel)
        self.add_block(self.bno_buffer_mag)
        self.add_block(self.bno_buffer_gyro)
        self.translate_block_bno.add_acceleration_callback(
            self.bno_buffer_accel.input_data
        )
        self.translate_block_bno.add_gyro_callback(self.bno_buffer_gyro.input_data)
        self.translate_block_bno.add_magnetic_callback(self.bno_buffer_mag.input_data)

        self.sensors["EPT"] = self.ept_buffer
        self.sensors["RTC"] = self.rtc_buffer
        self.sensors["BNO_ACC"] = self.bno_buffer_accel
        self.sensors["BNO_GYR"] = self.bno_buffer_gyro
        self.sensors["BNO_MAG"] = self.bno_buffer_mag
        self.sensors["PTS"] = self.pts_buffer
        self.sensors["BNR"] = self.bnr_buffer
        self.sensors["IMU"] = self.imu_buffer

        self.configure_logger_outdir()

    def is_logging_enabled(self):
        return self.logging_enabled

    def pause_sensors(self):
        for k, sensor in self.sensors.items():
            sensor.pause()
        self.aco_buffer.pause()
        self.fft_buffer.pause()

    def resume_sensors(self):
        for k, sensor in self.sensors.items():
            sensor.resume()
        self.aco_buffer.resume()
        self.fft_buffer.resume()

    def get_sensor_names(self):
        return list(self.sensors.keys())

    def get_sensor_signals(self, sensor):
        res = []
        if sensor in self.sensors.keys():
            sens_buff = self.sensors[sensor]
            res = sens_buff.get_signal_names()
        return res

    def get_signal_buffer(self, sensor, signal):
        if sensor in self.sensors.keys():
            sense_buf = self.sensors[sensor]
            res = sense_buf.get_buffer(signals=[signal])
            return (res[0], res[1][signal])
        return (None, [])

    def set_current_channel(self, chan):
        self.current_ch = chan

    def get_num_channels(self):
        return self.num_channels

    def get_latest_timestamp(self):
        return (
            datetime.datetime.now()
        )  # TODO, this should probably be last valid data time

    @classmethod
    def process_args(cls, args):
        if args.debug_socket_in:
            ac.debug_socket_in()
        if args.debug_fft:
            ac.debug_fft()
        if args.debug_udp_data:
            ac.debug_udp_data()

        if args.verbose > 0:
            ac.set_verbose(args.verbose)
        if args.debug_python:
            logger.setLevel(logging.DEBUG)

    def run_as_thread(self):
        self.thread = threading.Thread(target=self.run)
        self.thread.start()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        prog="Acbotics Demo Fixture",
        description="Create a fixture capable of collecting Acsense Data",
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

    f = AcboticsDemoFixture(args)
    f.run()
