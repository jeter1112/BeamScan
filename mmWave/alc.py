import time
import sys

class Alc(object):
    # tx_bfrf_gain
    # tx_bf_pdet_mux
    # tx_alc_ctrl
    # tx_alc_loop_cnt
    # tx_alc_start_delay
    # tx_alc_meas_delay
    # tx_alc_bfrf_gain_max
    # tx_alc_bfrf_gain_min
    # tx_alc_step_max
    # tx_alc_pdet_lo_th
    # tx_alc_pdet_hi_offs_th
    # tx_alc_bfrf_gain (RO)
    # tx_alc_pdet (RO)

    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(Alc, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self):
        if self.__initialized:
            return
        import adc
        import amux
        import register
        import eder_logger
        self.regs   = register.Register()
        self.amux   = amux.Amux(self.regs);
        self.adc    = adc.Adc();
        self.logger = eder_logger.EderLogger()
        self.__initialized = True

    def _cycles(self, time_in_us):
        fast_clk_setting = self.regs.rd('fast_clk_ctrl')&0x30
        if fast_clk_setting == 0x10:
            fast_clk_freq = 225 # MHz
        elif fast_clk_setting == 0x20:
            fast_clk_freq = 160 # MHz
        elif fast_clk_setting == 0x30:
            fast_clk_freq = 200 # MHz
        else:
            fast_clk_freq = 180 # MHz
        return int(time_in_us*fast_clk_freq+0.5)-1


    def init(self):
        self.regs.wr('tx_alc_ctrl', 0xd0)
        self.regs.wr('tx_alc_loop_cnt', 0x00)
        self.regs.wr('tx_alc_start_delay', self._cycles(0.5))   # 1 us
        self.regs.wr('tx_alc_meas_delay',  self._cycles(0.3)) # 100 ns
        self.regs.wr('tx_alc_bfrf_gain_max', 0xff)
        self.regs.wr('tx_alc_bfrf_gain_min', 0x00)
        self.regs.wr('tx_alc_step_max', 0x01) # Only step RF-gain
        self.regs.wr('tx_alc_pdet_lo_th', 0x00)
        self.regs.wr('tx_alc_pdet_hi_offs_th', 0x00)
        self.regs.wr('tx_bf_pdet_mux', 0x00)

    
    def pdet_th(self, tx_alc_pdet_lo_th=None, tx_alc_pdet_hi_offs_th=None):
        if tx_alc_pdet_lo_th is None:
            self.logger.log_info('tx_alc_pdet_lo_th      : ' + hex(self.regs.rd('tx_alc_pdet_lo_th')),2)
        else:
            self.regs.wrrd('tx_alc_pdet_lo_th', tx_alc_pdet_lo_th)
        if tx_alc_pdet_hi_offs_th is None:
            self.logger.log_info('tx_alc_pdet_hi_offs_th : ' + hex(self.regs.rd('tx_alc_pdet_hi_offs_th')),2)
        else:
            self.regs.wrrd('tx_alc_pdet_hi_offs_th', tx_alc_pdet_hi_offs_th)


    def enable(self):
        self.regs.set('tx_alc_ctrl', 0x01)

    def disable(self):
        self.regs.clr('tx_alc_ctrl', 0x03)


    def start(self):
        if (self.regs.rd('tx_alc_ctrl') & 0x01) == 0x01:
            self.regs.tgl('tx_alc_ctrl', 0x02)
        else:
            self.regs.set('tx_alc_ctrl', 0x03)

    def stop(self):
        if (self.regs.rd('tx_alc_ctrl') & 0x01) == 0x01:
            self.regs.clr('tx_alc_ctrl', 0x03)
            self.regs.set('tx_alc_ctrl', 0x01)
        else:
            self.regs.clr('tx_alc_ctrl', 0x03)


    def status(self):
        self.logger.log_info('tx_alc_bfrf_gain : ' + hex(self.regs.rd('tx_alc_bfrf_gain')),2)
        self.logger.log_info('tx_alc_pdet      : ' + hex(self.regs.rd('tx_alc_pdet')),2)

    def dump_setup(self):
        self.logger.log_info('tx_alc_ctrl            : ' + hex(self.regs.rd('tx_alc_ctrl')),2)
        self.logger.log_info('tx_alc_loop_cnt        : ' + hex(self.regs.rd('tx_alc_loop_cnt')),2)
        self.logger.log_info('tx_alc_start_delay     : ' + hex(self.regs.rd('tx_alc_start_delay')),2)
        self.logger.log_info('tx_alc_meas_delay      : ' + hex(self.regs.rd('tx_alc_meas_delay')),2)
        self.logger.log_info('tx_alc_bfrf_gain_max   : ' + hex(self.regs.rd('tx_alc_bfrf_gain_max')),2)
        self.logger.log_info('tx_alc_bfrf_gain_min   : ' + hex(self.regs.rd('tx_alc_bfrf_gain_min')),2)
        self.logger.log_info('tx_alc_step_max        : ' + hex(self.regs.rd('tx_alc_step_max')),2)
        self.logger.log_info('tx_alc_pdet_lo_th      : ' + hex(self.regs.rd('tx_alc_pdet_lo_th')),2)
        self.logger.log_info('tx_alc_pdet_hi_offs_th : ' + hex(self.regs.rd('tx_alc_pdet_hi_offs_th')),2)
        self.logger.log_info('tx_alc_bfrf_gain (RO)  : ' + hex(self.regs.rd('tx_alc_bfrf_gain')),2)
        self.logger.log_info('tx_alc_pdet      (RO)  : ' + hex(self.regs.rd('tx_alc_pdet')),2)
        self.logger.log_info('tx_bf_pdet_mux         : ' + hex(self.regs.rd('tx_bf_pdet_mux')),2)


    def trim(self, bfrf_max, bfrf_min, ):
        self.logger.log_info('tx_alc_pdet_lo_th      : ' + hex(self.regs.rd('tx_alc_pdet_lo_th')),2)
        self.logger.log_info('tx_alc_pdet_hi_offs_th : ' + hex(self.regs.rd('tx_alc_pdet_hi_offs_th')),2)
        pdet_th = 0
        for i in xrange(7, -1, -1):
            lo_cnt = 0
            pdet_th += (1<<i)
            self.regs.wrrd('tx_alc_pdet_lo_th', pdet_th)
            rds = 1000
            for j in xrange(0, rds):
                if (self.regs.rd('tx_alc_pdet') & 0x01 == 0x01):
                    lo_cnt += 1
            self.logger.log_info('pdet_lo_th, lo_cnt: ' + hex(pdet_th) + ', ' + str(lo_cnt),4)
            if lo_cnt*2 > rds:
                pdet_th -= (1<<i)
        pdet_th = 0
        for i in xrange(4, -1, -1):
            hi_cnt = 0
            pdet_th += (1<<i)
            self.regs.wrrd('tx_alc_pdet_hi_offs_th', pdet_th)
            rds = 1000
            for j in xrange(0, rds):
                if (self.regs.rd('tx_alc_pdet') & 0x02 == 0x02):
                    hi_cnt += 1
            self.logger.log_info('pdet_hi_offs_th, hi_cnt: ' + hex(pdet_th) + ', ' + str(hi_cnt),4)
            if hi_cnt*2 < rds:
                pdet_th -= (1<<i)
        self.logger.log_info('tx_alc_pdet_lo_th      : ' + hex(self.regs.rd('tx_alc_pdet_lo_th')),2)
        self.logger.log_info('tx_alc_pdet_hi_offs_th : ' + hex(self.regs.rd('tx_alc_pdet_hi_offs_th')),2)

    def dump_pdet(self):
        bist_amux_ctrl = self.regs.rd('bist_amux_ctrl')
        tx_bf_pdet_mux = self.regs.rd('tx_bf_pdet_mux')
        self.logger.log_info("                                                    Tx Antenna                                                      ")
        self.logger.log_info("             0      1      2      3      4      5      6      7      8      9     10     11     12     13     14     15   ")
        row0_string = 'Pdet     :'
        row1_string = 'Pdet_peak:'
        row2_string = 'ALC Hi/Lo:'
        for pdet in xrange(0, 16):
            self.adc.start(self.amux.amux_tx_pdet, 0x80+pdet, 7)
            adc_pdet = self.adc.mean()
            self.adc.stop()
            self.adc.start(0x80+self.amux.amux_tx_env_pdet, 0x80+pdet, 7)
            adc_env_pdet = self.adc.mean()
            self.adc.stop()
            row0_string += ' {:0{}d}  '.format(adc_pdet,4)
            row1_string += ' {:0{}d}  '.format(adc_env_pdet,4)
            row2_string += '  {:0{}b}   '.format(self.regs.rd('tx_alc_pdet'),2)
        self.logger.log_info(row0_string)
        self.logger.log_info(row1_string)
        self.logger.log_info(row2_string)
        self.regs.wrrd('bist_amux_ctrl',bist_amux_ctrl)
        self.regs.wrrd('tx_bf_pdet_mux',tx_bf_pdet_mux)

    def meas_pdet(self,pdet):
        bist_amux_ctrl = self.regs.rd('bist_amux_ctrl')
        tx_bf_pdet_mux = self.regs.rd('tx_bf_pdet_mux')
        self.adc.start(self.amux.amux_tx_pdet, 0x80+pdet, 7)
        adc_pdet = self.adc.mean()
        self.adc.stop()
        self.regs.wrrd('bist_amux_ctrl',bist_amux_ctrl)
        self.regs.wrrd('tx_bf_pdet_mux',tx_bf_pdet_mux)
        return adc_pdet


    def monitor(self):
        while 1:
            sys.stdout.write("tx_alc_brf_gain: %d   pdet: %d \r" % (self.regs.rd('tx_alc_bfrf_gain'),self.regs.rd('tx_alc_pdet')))
            sys.stdout.flush()
            time.sleep(0.1)

        sys.stdout.write("\n")
        sys.stdout.flush()
