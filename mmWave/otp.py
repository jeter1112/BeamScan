import time
import sys
import keyboard

class Otp(object):
    import time

    __instance = None
    __src_1 = None
    __src_2 = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(Otp, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance
    
    def __init__(self):
        if self.__initialized:
            return
        self.__initialized = True
        import register
        import amux
        import adc
        import temp
        import eder_status
        import eder_logger
        self.regs   = register.Register()
        self.status = eder_status.EderStatus()
        self.logger = eder_logger.EderLogger()
        self.amux   = amux.Amux(self.regs)
        self.adc    = adc.Adc()
        self.temp   = temp.Temp()
        #self.lock = Lock()

    def reset(self):
        self.status.clr_init_bit(self.status.OTP_INIT)


    def init(self, threshold=0x05, tx_off=None, rx_off=None):
        self.status.set_init_bit(self.status.OTP_INIT)
        if tx_off == None:
			tx_off = self.regs.rd('trx_tx_off')
        if rx_off == None:
			rx_off = self.regs.rd('trx_rx_off')
        self.regs.wrrd('bist_ot_ctrl', 0x00)
        self.regs.wrrd('bist_ot_temp', 0x40|threshold)
        self.regs.wrrd('bist_ot_rx_off_mask', rx_off)
        self.regs.wrrd('bist_ot_tx_off_mask', tx_off)
        self.logger.log_info('Chip OTP init.',2)

    def enable(self, alarm=0x20):
        self.regs.set('bist_ot_ctrl', 0x10|alarm)
        self.logger.log_info('OTP Enabled.',2)

    def disable(self):
        self.regs.clr('bist_ot_ctrl', 0x30)
        self.logger.log_info('OTP Disabled.',2)

    def alarm_clr(self):
        self.regs.set('bist_ot_temp', 0x40)
        self.logger.log_info('OTP Alarm cleared.',2)



    def th_meas(self):
        bist_amux_ctrl = self.regs.rd('bist_amux_ctrl')
        bist_ot_ctrl   = self.regs.rd('bist_ot_ctrl')
        self.regs.wrrd('bist_ot_ctrl', (bist_ot_ctrl & 0x30) | 0x03)		# Workaround; enabling amux_otp with otp_th triggers temp_not_ok
        self.adc.start(0x80|self.adc.amux.amux_otp, bist_ot_ctrl & 0x30, 7)
        adc_ot_th = self.adc.mean()
        self.adc.stop()
        self.regs.wrrd('bist_amux_ctrl',bist_amux_ctrl)
        self.regs.wrrd('bist_ot_ctrl',bist_ot_ctrl)
        return adc_ot_th
        
    def th_inc(self):
        bist_ot_temp = self.regs.rd('bist_ot_temp')
        if (bist_ot_temp & 0x1F) < 0x1F:
        	self.regs.wr('bist_ot_temp',bist_ot_temp + 1)
        return self.regs.rd('bist_ot_temp')

    def th_dec(self):
        bist_ot_temp = self.regs.rd('bist_ot_temp')
        if (bist_ot_temp & 0x1F) > 0:
        	self.regs.wr('bist_ot_temp',bist_ot_temp - 1)
        return self.regs.rd('bist_ot_temp')

    def monitor(self):
        self.logger.log_info("Controls:",2)
        self.logger.log_info("e - Toggle enable/disable of OTP function",2)
        self.logger.log_info("a - Toggle enable/disable of Alarm function",2)
        self.logger.log_info("c - Clear Alarm indication",2)
        self.logger.log_info("u - Increase threshold level",2)
        self.logger.log_info("n - Decrease threshold level",2)
        self.logger.log_info("OTP En  Alarm En  OTP Ok  Alarm  Threshold         Temp        Diff",2)
        self.logger.log_info("======  ========  ======  =====  =========    ===============  ====",2)
        while 1:
            bist_ot_ctrl = self.regs.rd('bist_ot_ctrl')
            bist_ot_temp = self.regs.rd('bist_ot_temp')
            th_meas      = self.th_meas()
            temp_raw     = self.temp.run_raw()
            temp         = self.temp.run()-273
            sys.stdout.write("    %d       %d         %d       %d    %04d (%02d)    %04d (%03.2f C)  %3d  \r" % ((bist_ot_ctrl>>4)&1, (bist_ot_ctrl>>5)&1, (bist_ot_temp>>7), (bist_ot_temp>>6)&1, th_meas, (bist_ot_temp&0x1F), temp_raw, temp, temp_raw-th_meas))
            sys.stdout.flush()
            if keyboard.is_pressed('u'):
				if (bist_ot_temp & 0x1F) < 0x1F:
					self.regs.wr('bist_ot_temp',(bist_ot_temp & 0x1F) + 1)
            if keyboard.is_pressed('n'):
				if (bist_ot_temp & 0x1F) > 0:
					self.regs.wr('bist_ot_temp',(bist_ot_temp & 0x1F) - 1)
            if keyboard.is_pressed('c'):
				self.regs.wr('bist_ot_temp',bist_ot_temp|0x40)
            if keyboard.is_pressed('e'):
				self.regs.tgl('bist_ot_ctrl',0x10)
            if keyboard.is_pressed('a'):
				self.regs.tgl('bist_ot_ctrl',0x20)
            time.sleep(0.1)

        sys.stdout.write("\n")
        sys.stdout.flush()
