class Ref(object):

    __instance = None 

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(Ref, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self):
        if self.__initialized:
            return
        self.__initialized = True
        import register
        import eder_status
        import eder_logger
        self.regs = register.Register()
        self.status = eder_status.EderStatus()
        self.logger = eder_logger.EderLogger()

    def reset(self):
        self.status.clr_init_bit(self.status.REF_INIT)

    def init(self):
        if self.status.init_bit_is_set(self.status.REF_INIT) == False:
            self.regs.set('bias_ctrl',0x1c)
            self.regs.set('bias_pll',0x37)
            self.regs.set('pll_en',0x08)
            
            self.regs.wr('pll_ref_in_lvds_en',0x01)
            self.status.set_init_bit(self.status.REF_INIT)
            self.logger.log_info('Chip REF init.',2)
        else:
            self.logger.log_info('Chip REF already initialized.',2)

    def monitor(self):
        self.regs.wr('pll_ld_mux_ctrl',0x02)
