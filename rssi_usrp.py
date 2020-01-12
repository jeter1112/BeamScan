#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Top Block
# Generated: Mon Dec 30 09:55:17 2019
##################################################

from distutils.version import StrictVersion

if __name__ == '__main__':
    import ctypes
    import sys
    if sys.platform.startswith('linux'):
        try:
            x11 = ctypes.cdll.LoadLibrary('libX11.so')
            x11.XInitThreads()
        except:
            print "Warning: failed to XInitThreads()"

from PyQt5 import Qt, QtCore
from gnuradio import analog
from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import uhd
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from optparse import OptionParser
import sys
import threading
import time
from gnuradio import qtgui
import os

class top_block(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "Top Block")
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Top Block")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except:
            pass
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("GNU Radio", "top_block")

        if StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
            self.restoreGeometry(self.settings.value("geometry").toByteArray())
        else:
            self.restoreGeometry(self.settings.value("geometry", type=QtCore.QByteArray))

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 200000
        self.rss = rss = 0

        ##################################################
        # Blocks
        ##################################################
        self.pb = blocks.probe_signal_f()
        self.uhd_usrp_source_0 = uhd.usrp_source(
        	",".join(("", "")),
        	uhd.stream_args(
        		cpu_format="fc32",
        		channels=range(1),
        	),
        )
        self.uhd_usrp_source_0.set_samp_rate(samp_rate)
        self.uhd_usrp_source_0.set_center_freq(0, 0)
        self.uhd_usrp_source_0.set_gain(0, 0)
        self.uhd_usrp_source_0.set_antenna('RX2', 0)
        self.uhd_usrp_sink_0 = uhd.usrp_sink(
        	",".join(("", "")),
        	uhd.stream_args(
        		cpu_format="fc32",
        		channels=range(1),
        	),
        )
        self.uhd_usrp_sink_0.set_samp_rate(samp_rate)
        self.uhd_usrp_sink_0.set_center_freq(0, 0)
        self.uhd_usrp_sink_0.set_gain(0, 0)
        self.uhd_usrp_sink_0.set_antenna('TX/RX', 0)

        def _rss_probe():
            while True:
                val = self.pb.level()
                try:
                    self.set_rss(val)
                except AttributeError:
                    pass
                time.sleep(0.008)

        def attact_rssi():
            pathradio = "/tmp/radiopipe"
            pathrxradio = "/tmp/radiorxpipe"
            pathrssi  ="rssi.txt"
            try:
                fiforx = open(pathradio, "r")
                fiforadio=open(pathrxradio, "r")
                frssi  = open(pathrssi,"w")
            except Exception as e:
                print (e)
                sys.exit()
                
            while True:
                
                r = fiforx.read(1)
                
                if r == 'b':
                    for i in range (0,64):
                        dio=fiforadio.read(1)
                        if dio =='b' or len(dio) ==0:
                            if dio=='b':
                                print(i)
                            else:
                                print('?')
                            time.sleep(0.014)
                            if i<63:
                                frssi.write(str(self.get_rss())+',')
                            else:
                                frssi.write(str(self.get_rss())+'\n') 
                        
                        else:
                            break
                       
                        
                elif r=='c':
                    print r
                    break
            fiforx.close()
            fiforadio.close()  
            frssi.close()
            os.unlink(pathradio)
            os.unlink(pathrxradio)

        _rss_thread = threading.Thread(target=_rss_probe)
        _rss_thread.daemon = True
        _rss_thread.start()

        rssi_thread = threading.Thread(target=attact_rssi)
        rssi_thread.daemon = True
        rssi_thread.start()



        self.blocks_nlog10_ff_0 = blocks.nlog10_ff(10.0, 1, 0)
        self.blocks_moving_average_xx_0 = blocks.moving_average_ff(samp_rate/2000, 40000.0/samp_rate, samp_rate/1000)
        self.blocks_complex_to_mag_squared_0 = blocks.complex_to_mag_squared(1)
        self.analog_sig_source_x_0 = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, 20000, 0.1, 0)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_sig_source_x_0, 0), (self.uhd_usrp_sink_0, 0))
        self.connect((self.blocks_complex_to_mag_squared_0, 0), (self.blocks_moving_average_xx_0, 0))
        self.connect((self.blocks_moving_average_xx_0, 0), (self.blocks_nlog10_ff_0, 0))
        self.connect((self.blocks_nlog10_ff_0, 0), (self.pb, 0))
        self.connect((self.uhd_usrp_source_0, 0), (self.blocks_complex_to_mag_squared_0, 0))

    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "top_block")
        self.settings.setValue("geometry", self.saveGeometry())
        event.accept()

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.uhd_usrp_source_0.set_samp_rate(self.samp_rate)
        self.uhd_usrp_sink_0.set_samp_rate(self.samp_rate)
        self.blocks_moving_average_xx_0.set_length_and_scale(self.samp_rate/2000, 40000.0/self.samp_rate)
        self.analog_sig_source_x_0.set_sampling_freq(self.samp_rate)

    def get_rss(self):
        return self.rss

    def set_rss(self, rss):
        self.rss = rss


def main(top_block_cls=top_block, options=None):

    if StrictVersion("4.5.0") <= StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
        style = gr.prefs().get_string('qtgui', 'style', 'raster')
        Qt.QApplication.setGraphicsSystem(style)
    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()
    tb.start()
    tb.show()

    def quitting():
        tb.stop()
        tb.wait()
    qapp.aboutToQuit.connect(quitting)
    qapp.exec_()


if __name__ == '__main__':
    main()
