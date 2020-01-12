import sys, os, time

class Tx(object):

    __instance = None
    trx_tx_on_default = 0x1FFFFF
    trx_ctrl = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(Tx, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance


    def __init__(self):
        if self.__initialized:
            return
        self.__initialized = True
        import alc
        import bf
        import register
        import memory
        import gpio
        import tx_dco
        import eder_logger
        import eder_status
        self.regs   = register.Register()
        self.mems   = memory.Memory()
        self.gpio   = gpio.EderGpio(self.regs.board_type)
        self.alc    = alc.Alc()
        self.bf     = bf.Bf(bf.Bf.TX)
        self.dco    = tx_dco.TxDco()
        self.logger = eder_logger.EderLogger()
        self.status = eder_status.EderStatus()

    def __default(self):
        self.regs.wr('trx_tx_on',self.regs.value('trx_tx_on'))
        self.regs.wr('trx_tx_off',self.regs.value('trx_tx_off'))
        self.regs.wr('bias_ctrl',self.regs.value('bias_ctrl'))
        self.regs.wr('bias_tx',self.regs.value('bias_tx'))
        self.regs.clr('bias_lo',0x08)
        self.regs.wr('tx_ctrl',self.regs.value('tx_ctrl'))
        self.regs.wr('tx_bb_gain',self.regs.value('tx_bb_gain'))
        self.regs.wr('tx_bb_phase',self.regs.value('tx_bb_phase'))
        self.regs.wr('tx_bb_iq_gain',self.regs.value('tx_bb_iq_gain'))
        self.regs.wr('tx_bfrf_gain',self.regs.value('tx_bfrf_gain'))


    def set_beam(self, beam=None):
        restore_trx_ctrl = self.regs.rd('trx_ctrl')
        self.regs.wr('trx_ctrl', 0x02)
        if beam != None:
            self.bf.awv.set(beam)
        else:
            self.bf.awv.set(self.bf.awv.get()&0x3f)
        self.regs.wr('trx_ctrl',restore_trx_ctrl)
        
    def get_beam(self):
        return (self.bf.awv.get() & 0x3f)

    def reset(self):
        self.__default()
        self.status.clr_init_bit(self.status.TX_INIT)
        self.trx_tx_on_default = 0x1FFFFF
        self.trx_ctrl = None
        self.logger.log_info('TX Reset',2)


    def init(self, trx_tx_on=trx_tx_on_default):
        if self.status.init_bit_is_set(self.status.TX_INIT) == False:
            self.regs.wr('trx_tx_on',trx_tx_on)
            self.regs.wr('bias_tx', 0xAEAA)
            self.regs.wr('bias_ctrl', 0x7F)
            self.regs.set('bias_lo', 0x0A)
            self.regs.wr('tx_ctrl', 0x18)
            self.regs.wr('tx_bb_gain', 0x00)
            self.regs.wr('tx_bb_phase', 0x00)
            self.regs.wr('tx_bb_iq_gain', 0xFF)
            self.regs.wr('tx_bfrf_gain', 0x77)
            self.set_beam(31)
            self.status.set_init_bit(self.status.TX_INIT)
            self.logger.log_info('TX Initialised',2)


    def setup(self, freq, beam=None, trx_tx_on=trx_tx_on_default):
        self.freq = freq
        # Import beamforming table and write to memory
        # TODO: Here we should prepare for writing the beambook
        # freq 0.0 and temp 0.0 resets bf_tx_awv
        self.freq = freq
        self.bf.awv.setup('lut/beambook/bf_tx_awv', freq, 0.0)
        self.bf.idx.setup('lut/beambook/bf_tx_awv_idx', freq)

        self.init(trx_tx_on)
        self.set_beam(beam)
        self.logger.log_info('TX Setup completed',2)


    def enable(self, beam=None):
        if self.trx_ctrl == None:
            if (self.regs.rd('trx_ctrl') & 0x08):
                self.trx_ctrl = 'HW'
            else:
                self.trx_ctrl = 'SW'

        if self.trx_ctrl == 'HW':
            self.gpio.set_tx_mode();
        else:
            self.regs.set('trx_ctrl', 0x02)

        self.set_beam(beam)
        self.logger.log_info('TX enabled',2)
        
            
    def disable(self):
        if self.trx_ctrl == None:
            if (self.regs.rd('trx_ctrl') & 0x08):
                self.trx_ctrl = 'HW'
            else:
                self.trx_ctrl = 'SW'

        self.regs.clr('trx_ctrl', 0x02)
        self.logger.log_info('TX disabled',2)


    def hw_sw_enable(self):
        self.regs.set('trx_ctrl', 0x08)
        self.trx_sw_ctrl = 'HW'

    def hw_sw_disable(self):
        self.regs.clr('trx_ctrl',0x8)
        self.trx_sw_ctrl = 'SW'
    
    # add beamforming method by jeter

    def tx_beamforming(self):

        pathrx = "/tmp/rxpipe"
        pathradio = "/tmp/radiopipe"
        try:
            os.mkfifo(pathrx)
            os.mkfifo(pathradio)
        except:
            pass
        try:
            fiforx = open(pathrx, "w",0)
            fiforadio = open(pathradio, "w",0)
        except Exception as e:
            print (e)
            sys.exit()
        
        time.sleep(8)

        print('begin')
        for i in range(0,64):
            fiforx.write('b')
            fiforx.flush()
            fiforadio.write('b')
            fiforadio.flush()
            self.set_beam(i)
            print('tx beam:'+str(self.get_beam()))
            time.sleep(1.2)

	
        fiforx.write('c')
        fiforx.close()
        fiforadio.write('c')
        fiforadio.close()
        # try:
        #     os.unlink(fiforx)
        #     os.unlink(fiforadio)
        # except:
        #     pass
