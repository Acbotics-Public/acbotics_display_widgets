from pyqtgraph.Qt import QtWidgets as qtw  # type: ignore
import numpy as np
import pyqtgraph as pg  # type: ignore

LOWERCASE_MU = "\u03bc"


class Spectrogram_View(qtw.QFrame):
    def __init__(self, fixture):
        super(Spectrogram_View, self).__init__()

        self.fixture = fixture
        self.spectrogram_level_adjust = 0
        self.spectrogram_width_adjust = 0
        self.spectrogram_view_reset = False

        self.plot_gram = pg.PlotWidget()
        self.img_gram = pg.ImageItem()
        self.cm_gram = pg.colormap.get("viridis")  # prepare a linear color map
        self.cbar_gram = self.plot_gram.plotItem.addColorBar(
            self.img_gram,
            colorMap=self.cm_gram,
            values=(90, 140),
            label=f"dB re 1 {LOWERCASE_MU}Pa**2 / Hz",
        )
        self.sample_rate = None

    def set_curr_ch(self, ch):
        pass

    def update_sample_rate(self):
        xform = pg.QtGui.QTransform()
        fft_freq = np.fft.rfftfreq(self.fixture.NFFT) * self.sample_rate

        xform.scale(
            fft_freq[-1] / len(fft_freq),
            (self.fixture.NFFT - self.fixture.noverlap) / self.sample_rate,
        )  # scale horizontal and vertical axes
        self.setTransform(xform)  # assign transform

        self.img_gram.setImage(
            np.array(self.fixture.data_fft).T,
            # np.array(Sxx),
            autoLevels=False,
        )  # disable autolevels so colorbar retains control
        self.img_gram.setPos(
            0,
            -len(self.fixture.data_fft)
            * (self.fixture.NFFT - self.fixture.noverlap)
            / self.sample_rate,
        )

    def setTransform(self, xform):
        self.img_gram.setTransform(xform)  # assign transform

    def spectrogram_level_callback(self, val):
        self.spectrogram_level_adjust = val

    def spectrogram_width_callback(self, val):
        self.spectrogram_width_adjust = val

    def spectrogram_reset_callback(self, val):
        self.spectrogram_view_reset = True

    def reset_spectrogram_view(self):
        self.cbar_gram.setLevels(self.default_spectrogram_values)

    def increase_spectrogram_level(self, val):
        current_levels = self.cbar_gram.levels()
        offset = val / 25000.0
        new_levels = (current_levels[0] + offset, current_levels[1] + offset)
        self.cbar_gram.setLevels(values=new_levels)

    def increase_spectrogram_width(self, val):
        current_levels = self.cbar_gram.levels()
        scale_pct = val / 500000.0
        center = (current_levels[0] + current_levels[1]) / 2.0
        old_span = current_levels[1] - current_levels[0]
        span = old_span * (1 + scale_pct)
        new_levels = (center - span / 2.0, center + span / 2.0)
        self.cbar_gram.setLevels(values=new_levels)

    def create_widget(self):
        self.plot_gram.setLabel("left", "Time", units="s")
        self.plot_gram.setLabel(
            "bottom", f"Ch {self.fixture.current_ch} - Frequency", units="Hz"
        )

        self.plot_gram.setMouseEnabled(x=False, y=False)

        Sxx = np.array(
            [[90, 100, 120], [100, 120, 130], [120, 130, 140], [100, 120, 130]]
        )

        self.plot_gram.plotItem.addItem(self.img_gram)

        self.cbar_gram.axis.setWidth(50)

        # Sxx contains the amplitude for each pixel
        self.img_gram.setImage(Sxx)
        self.layout = qtw.QVBoxLayout()

        self.layout.addWidget(self.plot_gram)
        self.setLayout(self.layout)

    def update(self):
        # if not self.sample_rate == self.fixture.sample_rate:
        #     self.sample_rate = self.fixture.sample_rate
        #     self.update_sample_rate()
        if not self.spectrogram_level_adjust == 0:
            self.increase_spectrogram_level(self.spectrogram_level_adjust)
        if not self.spectrogram_width_adjust == 0:
            self.increase_spectrogram_width(self.spectrogram_width_adjust)

        if self.spectrogram_view_reset:
            self.reset_spectrogram_view()
            self.spectrogram_view_reset = False

        data_fft = self.fixture.get_fft_data()
        if len(data_fft) == 0:
            return
        if not self.fixture.get_fft_sample_rate() == self.sample_rate:
            self.sample_rate = self.fixture.get_fft_sample_rate()
            self.update_sample_rate()
        self.img_gram.setImage(
            data_fft[self.fixture.current_ch],
            # np.array(Sxx),
            autoLevels=False,
        )  # disable autolevels so colorbar retains control
        self.img_gram.setPos(
            0,
            -len(data_fft[self.fixture.current_ch])
            * (self.fixture.NFFT - self.fixture.noverlap)
            / self.sample_rate,
        )
