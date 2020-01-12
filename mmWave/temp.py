class Temp(object):

    __instance = None

    #ADC reference measured at Tamb = 45 degrees (10 unit average), Estimate Tchip = 50 degrees (5 degree overtemp idle)
    adc_ref_volt = 1.228  # [V]
    adc_max      = 4095   #
    adc_scale    = 3      #
    temp_k       = 4e-3   # [V/K]
    temp_offs    = 41e-3  # [K/V]
    temp_scale   = adc_scale*adc_ref_volt/adc_max/temp_k # [K]
    temp_comp    = temp_offs/temp_k                      # [K]


    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(Temp, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self):
        if self.__initialized:
            return
        self.__initialized = True
        import adc
        import eder_status
        import eder_logger
        self.adc = adc.Adc();
        self.status = eder_status.EderStatus()
        self.logger = eder_logger.EderLogger()

    def reset(self):
        self.status.clr_init_bit(self.status.TEMP_INIT)

    def init(self):
        self.adc.init()
        if self.status.init_bit_is_set(self.status.TEMP_INIT) == False:
            self.status.set_init_bit(self.status.TEMP_INIT)
            self.logger.log_info('Chip TEMP init.',2)
        else:
            self.logger.log_info('Chip TEMP already initialized.',2)

    def run_raw(self):
        if self.status.init_bit_is_set(self.status.TEMP_INIT) == False:
            self.init()
        self.adc.start(0x83,None,4)
        temp = self.adc.mean()
        self.adc.stop()
        return temp

    def run(self):
        return self.run_raw()*self.temp_scale - self.temp_comp

