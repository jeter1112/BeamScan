class Pll(object):
    import time
    import math

    __instance = None

    ref_freq=45e6               # XO reference frequency
    alc_th_v=1.30               # VCO amplitude threshold = 1.30V
    atc_hi_th_v=2.4             # High tune voltage threshold = 2.4V
    atc_lo_th_v=0.4             # Low tune voltage threshold = 0.4V
    alc_th=102
    #atc_hi_th=191
    atc_lo_th=34
    dac_ref=3.0
    a_freq=0
    vtune=0
    vtune_th=0
    t=-273
    adc_ref_volt = 1.1
    adc_max      = 4095
    adc_scale    = 3
    adc_num_samp = 256
    temp_k       = 4e-3

    pll_en_divn = (1 << 0)
    pll_en_div2 = (1 << 1)
    pll_en_leak = (1 << 2)
    pll_en_ld   = (1 << 3)
    pll_en_chp  = (1 << 4)
    pll_en_pfd  = (1 << 5)

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(Pll, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self):
        if self.__initialized:
            return
        self.__initialized = True
        import ref
        import vco
        import register
        import eder_status
        import eder_logger
        import temp
        import adc

        self.adc = adc.Adc()
        self.temp  = temp.Temp()
        self.regs = register.Register()
        self.ref  = ref.Ref()
        self.vco  = vco.Vco()
        self._status = eder_status.EderStatus()
        self.logger = eder_logger.EderLogger()

    def freq_to_divn(self, freq):
        return int(freq/6/self.ref_freq-36)

    def divn_to_freq(self, divn):
        return (divn+36)*6*self.ref_freq

    def reset(self):
        self._status.clr_init_bit(self._status.PLL_INIT)
        self.alc_hi_th_tbl = dict()
        self.ref.reset()
        self.vco.reset()
	self.regs.set('vco_tune_ctrl',0xFF)
	self.regs.clr('vco_tune_ctrl',0xFF)

    def init(self, restart=True):
        self.vco.init()
        self.temp.init()

        self.alc_hi_th_tbl = dict()
        self._import_file('lut/vco/alc_hi_th', self.alc_hi_th_tbl)
        self.regs.set('bias_ctrl',0x7f)                                          # Enable BG and LDO:s
        self.regs.wr('bias_pll',0x17)                                            # Set PLL bias till nominal current
        self.regs.wr('bias_lo',0x2a)                                             # Set nominal bias for X3
        #
        self.regs.wr('pll_ref_in_lvds_en',0x01)                                  # Set REF input to LVDS
        self.regs.wr('pll_en',0x7b)                                              # Enable the PLL, Changed to 7B in Eder B.
        self.regs.wr('pll_chp',0x01)                                             # Set charge pump current to 600 uA
        #
        self.regs.wr('vco_alc_del',0x0e)                                         # 311 nanoseconds
        self.regs.wr('vco_tune_loop_del',0x000384)                               # 20 microseconds
        self.regs.wr('vco_atc_vtune_set_del',0x001194)                           # 100 microseconds
        self.regs.wr('vco_atc_vtune_unset_del',0x000384)                         # 20 microseconds
        self.regs.wr('vco_override_ctrl',0x3f)                                   # Internal VCO tune state machine
        #									 # should only control:
	#									 # 1. Vtune set
        #									 # 2. dig tune
        #									 # 3. ibias	
        #
        self.regs.wr('vco_vtune_ctrl',0x20)					 # ATC Low threshold mux function enabled
        self.alc_th=int(self.alc_th_v/self.dac_ref*255)                          # VCO amplitude threshold
        self.regs.wr('vco_alc_hi_th', self.alc_th)
        self.atc_hi_th=int(self.atc_hi_th_v/self.dac_ref*255)
        self.regs.wr('vco_atc_hi_th', self.atc_hi_th)
        self.atc_lo_th=int(self.atc_lo_th_v/self.dac_ref*255)
        self.regs.wr('vco_atc_lo_th',self.atc_lo_th)
        self.regs.wr('pll_pfd',0x00)
        self.regs.wr('vco_en',0x3c)
	if restart == True:
		self.regs.set('vco_tune_ctrl',(1<<2))
	else:
		self.regs.clr('vco_tune_ctrl',(1<<2))

        self.time.sleep(0.5)
        self._status.set_init_bit(self._status.PLL_INIT)
        self.logger.log_info('Chip PLL init',2)


    def set(self, frequency):
        start_time = self.time.time()
        if self._status.init_bit_is_set(self._status.PLL_INIT) == False:
            self.init()
        self.t=self.temp.run()-273;
        self.vtune_th=int((self.t*67e-4+1.066)*255/self.dac_ref);
        self.logger.log_info('Temperature: ' + "%1.3f" % (self.t) + ' C')
        self.logger.log_info('vco_vtune_atc_lo_th: ' + hex(self.vtune_th) + ' (' + "%1.3f" % (self.vtune_th*self.dac_ref/255) + ' V)')
        self.logger.log_info('vco_tune_ctrl: ' + hex(self.regs.rd('vco_tune_ctrl')))
        self.regs.wr('vco_vtune_atc_lo_th',self.vtune_th)
        self.regs.wr('pll_divn',self.freq_to_divn(frequency))
        self.regs.tgl('vco_tune_ctrl', 0x02)
        self.regs.tgl('vco_tune_ctrl', 0x01)
        self.time.sleep(0.002) 									# Increased to 2 ms from 0.5 ms
        vco_tune_status = self.regs.rd('vco_tune_status')
        vco_tune_det_status = self.regs.rd('vco_tune_det_status')
        vco_tune_freq_cnt = self.regs.rd('vco_tune_freq_cnt')
        self.logger.log_info('vco_tune_status [0x7e]: ' + hex(vco_tune_status))
        self.logger.log_info('vco_tune_det_status[0] [1]: ' + hex(vco_tune_det_status))
        self.logger.log_info('vco_tune_freq_cnt [0x7ff +/-11]: ' + hex(vco_tune_freq_cnt))

        # Check if tuning has succeeded
        if (vco_tune_status != 0x7e) or \
           (vco_tune_det_status & 0x01 != 0x01) or \
           (vco_tune_freq_cnt > 0x80a) or \
           (vco_tune_freq_cnt < 0x7f4):
            self.logger.log_info('VCO tune FAILED')
        else:
            self.logger.log_info('VCO tune OK.')
            self.regs.set('vco_tune_ctrl', 0x04)

        self.monitor('Vtune')
        self.logger.log_info('PLL Set time = {} seconds.'.format(self.time.time()-start_time))

    def status(self, cnt):
        self.time.sleep(0.015)
        for i in xrange(0,cnt):
            self.logger.log_info(hex(self.regs.rd('vco_tune_status')))

    def monitor(self, sel_mon):
        if sel_mon == 'ld':                                                           # Monitor LD
            self.regs.wr('pll_ld_mux_ctrl',0x0)
            self.logger.log_info('Monitor LD')
        if sel_mon == 'ref':                                                          # Monitor reference frequency
            self.regs.wr('pll_ld_mux_ctrl',0x2)
            self.logger.log_info('Monitor REF freq dvided by 2')
        if sel_mon == 'vco':                                                          # Monitor VCO frequency
            self.regs.wr('pll_ld_mux_ctrl',0x3)
            m_div = self.regs.rd('pll_divn')
            self.logger.log_info('Monitor VCO freq divided by ' + str((m_div+36)*4))
        if sel_mon == 'test':                                                         # Monitor test output
            self.regs.wr('pll_ld_mux_ctrl',0x5)
        if sel_mon == 'Vtune':                                                        # Monitor tune voltage
            dac = 128
            for x in range(0,8,1):                                                    # AD convert the tune voltage
                self.regs.wr('vco_atc_hi_th',dac)                                     # Set DAC value
                if self.regs.rd('vco_tune_det_status') >= 8:                          # Check if vco_atc_hi_th=1
                    dac = int(dac + 2**(6-x))                                         # Set next DAC vale for the SA
                else:
                    dac = int(dac - 2**(6-x))
            self.regs.wr('vco_atc_hi_th', int(self.atc_hi_th_v/self.dac_ref*255))     # Set correct tune threshold
            self.logger.log_info('Vtune = ' + str(dac*self.dac_ref/255) + ' V')  
            return dac*self.dac_ref/255						      # Write the tune voltage
        if sel_mon == 'VCOamp':                                                       # Monitor VCO amplitude
            dac = 128
            for x in range(0,8,1):                                                    # AD convert the VCO amplitude
                self.regs.wr('vco_alc_hi_th',dac)                                     # Set DAC value
                alc=self.regs.rd('vco_tune_det_status')                               # Read detecor status
                if alc&2 >0:                                                          # Check if vco_alc_hi_th=1                                    
                    dac = int(dac + 2**(6-x))                                         # Set next DAC vale for the SA
                else:
                    dac = int(dac - 2**(6-x))
            self.regs.wr('vco_alc_hi_th',self.alc_th)                                 # Set correct VCO ampltude th
            self.logger.log_info('VCO amplitude = '+str(dac*self.dac_ref/255) + ' V') # Write the VCO amplitude
            return dac*self.dac_ref/255


    def _import_file(self, fname, table):
        try:
            f = open(fname)
        except IOError:
            try:
                f = open('../'+fname)
            except IOError:
                print fname + ' not found!'
                return
        line = '#'
        while line[0]=='#':
            # Ignore the header.
            # Header should always start with '#'
            line = f.readline()

        while True:
            if line == '':
                break
            line = line.replace('\n', '')
            line = line.replace('\r', '')
            line = line.split(',')
            table[line[0]] = line[1:len(line)]
            line = f.readline()
        f.close()
