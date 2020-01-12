from threading import Lock
class Adc(object):
    import time

    __instance = None
    __src_1 = None
    __src_2 = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(Adc, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance
    
    def __init__(self):
        if self.__initialized:
            return
        self.__initialized = True
        import register
        import ref
        import amux
        import eder_status
        import eder_logger
        self.regs   = register.Register()
        self.status = eder_status.EderStatus()
        self.logger = eder_logger.EderLogger()
        self.ref    = ref.Ref()
        self.amux   = amux.Amux(self.regs)
        #self.lock = Lock()

    def reset(self):
        self.status.clr_init_bit(self.status.ADC_INIT)
        self.ref.reset()
        self.regs.tgl('adc_ctrl',0x20)
        self.amux.set(self.__src_1,self.__src_2)
        #self.lock.release()

    def init(self,div=3,cycle=10,set_edge=0):
        self.ref.init()
        self.regs.set('bias_ctrl',0x60)
        self.regs.wr('adc_clk_div',div)
        self.regs.wr('adc_sample_cycle',cycle)
        self.edge(set_edge)
        self.status.set_init_bit(self.status.ADC_INIT)
        self.logger.log_info('Chip ADC init.',2)

    def edge(self,set_edge):
        if (set_edge == 1):
            self.regs.set('adc_ctrl',2)
        else:
            self.regs.clr('adc_ctrl',2)

    def start(self,src1, src2=None, log2_nsamples=4):
        #self.lock.acquire()
        if (self.regs.rd('adc_ctrl') & 0x80) == 0x80:
            self.logger.log_info('ADC has been started and is ready, but has not been stopped/reseted.',2)
            return
        self.__src_1, self.__src_2 = self.amux.get()
        self.amux.set(src1,src2)
        self.regs.wr('adc_num_samples', log2_nsamples)
        self.regs.tgl('adc_ctrl',0x10)
        while (self.regs.rd('adc_ctrl') & 0x80) == 0:
            pass
        

    def stop(self):
        self.regs.tgl('adc_ctrl',0x20)
        self.amux.set(self.__src_1,self.__src_2)
        #self.lock.release()

    def mean(self):
        return self.regs.rd('adc_mean') & 0x0fff

    def max(self):
        return self.regs.rd('adc_max') & 0x0fff

    def min(self):
        return self.regs.rd('adc_min') & 0x0fff
    
    def diff(self):
        return self.regs.rd('adc_diff') & 0x0fff
