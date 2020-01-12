class Rxbbdc(object):

    __instance = None
    __init = False

    import time
    import operator

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(Rxbbdc, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self):
        if self.__initialized:
            return
        self.__initialized = True
        import register
        import eder_status
        import eder_logger
        import adc
        import amux
        self.regs  = register.Register()
        self.adc   = adc.Adc()
        self.amux  = amux.Amux(self.regs)
        self.logger = eder_logger.EderLogger()

        self.dcip = []
        self.dcin = []
        self.dcqp = []
        self.dcqn = []

        
    def _listToVolt(self, myList):
        adc_factor = (1.1905*3)/4096
        return [round(x*adc_factor,4) for x in myList]

    # Read out
    def rd_vals(self,pos):
        import math
        vals = []
        for i in pos:
            #self.time.sleep(0.001)
            self.adc.start(self.amux.amux_rx_bb, i, math.log(128, 2))
            vals.append(self.adc.mean())
            self.adc.stop()
        return vals

    # read all positive I-channel DC values
    def rd_dc_i_p(self):
        return self.rd_vals((9, 25, 41, 57, 73, 89))
    
    # read all positive Q-channel DC values
    def rd_dc_q_p(self):
        return self.rd_vals((10, 26, 42, 58, 74, 90))
    
    # read all negative I-channel DC values
    def rd_dc_i_n(self):
        return self.rd_vals((13, 29, 45, 61, 77, 93))
    
    # read all negative Q-channel DC values
    def rd_dc_q_n(self):
        return self.rd_vals((14, 30, 46, 58, 78, 94))
    
    # Get DC values for all groups
    def rd_dc_i(self):
        self.dcip = self.rd_dc_i_p()
        self.dcin = self.rd_dc_i_n()

    def rd_dc_q(self):
        self.dcqp = self.rd_dc_q_p()
        self.dcqn = self.rd_dc_q_n()

    def dc_diff_i(self):
        return map(lambda x,y: x-y, self.dcip, self.dcin)

    def dc_diff_q(self):
        return map(lambda x,y: x-y, self.dcqp, self.dcqn)

    def dc_cm_i(self): 
        return map(lambda x,y: (x+y)/2, self.dcip, self.dcin)
    
    def dc_cm_q(self): 
        return map(lambda x,y: (x+y)/2, self.dcqp, self.dcqn)

    def report(self,iq='iq'):
        if (iq == 'iq') or (iq == 'qi') or (iq == 'i'): self.rd_dc_i()
        if (iq == 'iq') or (iq == 'qi') or (iq == 'q'): self.rd_dc_q()
        if (iq == 'iq') or (iq == 'qi') or (iq == 'i'):
            self.logger.log_info('I, Measure point: ' + '    0   ' + '   1    ' + '    2     ' + '  3    ' + '   4    ' + '  5   ')
            self.logger.log_info('v_i_p           : ' + str(self._listToVolt(self.dcip)))
            self.logger.log_info('v_i_n           : ' + str(self._listToVolt(self.dcin)))
            self.logger.log_info('v_diff_i        : ' + str(self._listToVolt(self.dc_diff_i())))
            self.logger.log_info('v_cm_i          : ' + str(self._listToVolt(self.dc_cm_i())))
            self.logger.log_info('')
        if (iq == 'iq') or (iq == 'qi') or (iq == 'q'):
            self.logger.log_info('Q, Measure point: ' + '    0   ' + '   1    ' + '    2     ' + '  3    ' + '   4    ' + '  5   ' )
            self.logger.log_info('v_q_p           : ' + str(self._listToVolt(self.dcqp)))
            self.logger.log_info('v_q_n           : ' + str(self._listToVolt(self.dcqn)))
            self.logger.log_info('v_diff_q        : ' + str(self._listToVolt(self.dc_diff_q())))
            self.logger.log_info('v_cm_q          : ' + str(self._listToVolt(self.dc_cm_q())))
            self.logger.log_info('')

