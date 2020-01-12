import time
import numpy as np
import sys
import csv
import fileHandler as fh


class tx_dco(object):
    __instance = None
    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(tx_dco, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self):
        if self.__initialized:
            return
        self.__initialized = True

        import register
        import adc
        import pll
        import eder_status
        import eder_logger
        import rx
        import tx

        self.regs   = register.Register()
        self.adc    = adc.Adc()
        self.pll    = pll.Pll()
        self.status = eder_status.EderStatus()
        self.logger = eder_logger.EderLogger()
        self.rx     = rx.Rx()
        self.tx     = tx.Tx()

    def getRXoffset(self):
        self.adc.start(0x89)
        valI = self.adc.mean(self.adc.dump(16))
        self.adc.start(0x8a)
        valQ = self.adc.mean(self.adc.dump(16))
        return valI, valQ

    def setTXoffset(self,valI, valQ):
        self.regs.wr('tx_bb_i_dco', valI)
        self.regs.wr('tx_bb_q_dco', valQ)

    # rewrite to change only the necessary registers
    # 60.48GHz -> "TXcalibration_20170726.json"
    def setChipLoopBack(self, fileName):
        #fh=fileHandler.FH(fileName)
        #a=fh.read()
        #self.regs.dump(a)
        self.regs.dump(fh.read(fileName))

    def run(self):

        # STEP 1: create parameters for calibration
        errorTXmax = 90        # maximum allowed error
        currentI   = 16        # start value for DCo I
        currentQ   = 16        # start value for DCo Q
        currentE   = 100       # place holder for error value
        minVI      = 0         # goal value for I
        minVQ      = 0         # goal value for Q
        stepI      = 1         # optimization step for I
        stepQ      = 1         # optimization step for Q
        iteration  = 1         # current optimizer iteration
        optFreq    = 60.48e9   # RF frequency
        self.logger.log_info('TX DCO starting',2)

        #STEP 2: perform RX-calibration and read RX DC-offset value
        #self.tx_setup(optFreq)
        self.logger.log_info('TX DCO TX setup starting',4)
        self.pll.init()
        self.pll.set(optFreq)
        self.tx.setup(optFreq)
        self.logger.log_info('TX DCO TX setup complete',4)
        #self.rx_setup(optFreq)
        self.logger.log_info('TX DCO RX setup starting',4)
        self.rx.setup(optFreq)
        self.logger.log_info('TX DCO Rx setup complete',4)

        self.logger.log_info('TX DCO json file read',4)
        self.setChipLoopBack("json/TXcalibration_20170726.json")
        #self.tx_disable()
        self.tx.disable()
        self.logger.log_info('TX DCO TX disabled',4)
        #self.rx_enable()
        self.rx.enable()
        self.logger.log_info('TX DCO RX enabled',4)
        self.logger.log_info('TX DCO RX DCO running',4)
        self.rx.dco.run()
        minVI, minVQ = self.getRXoffset()

        #STEP 3: enable TX and read current offset Error
        #self.tx_enable()
        self.tx.enable()
        self.logger.log_info('TX DCO TX enabled',4)
        self.setTXoffset(currentI,currentQ)
        valI, valQ = self.getRXoffset()
        currentE = abs((valI-minVI) + 1j*(valQ-minVQ))

        #STEP 4: run the search using modified 2D Newton-Rhapson method
        self.logger.log_info('TX DCO TX DCO searching ...',4)
        while currentE >= errorTXmax:
            # get rxDCoI & rxDCoQ @ I+step,Q and calculate the ERROR
            self.setTXoffset(currentI+stepI,currentQ)
            valI, valQ = self.getRXoffset()
            errorIP = abs((valI-minVI) + 1j*(valQ-minVQ))
            # get rxDCoI & rxDCoQ @ I-step,Q and calculate the ERROR
            self.setTXoffset(currentI-stepI,currentQ)
            valI, valQ = self.getRXoffset()
            errorIN = abs((valI-minVI) + 1j*(valQ-minVQ))
            # get rxDCoI & rxDCoQ @ I,Q+step and calculate the ERROR
            self.setTXoffset(currentI,currentQ+stepQ)
            valI, valQ = self.getRXoffset()
            errorQP = abs((valI-minVI) + 1j*(valQ-minVQ))
            # get rxDCoI & rxDCoQ @ I,Q-step and calculate the ERROR
            self.setTXoffset(currentI,currentQ-stepQ)
            valI, valQ = self.getRXoffset()
            errorQN = abs((valI-minVI) + 1j*(valQ-minVQ))

            # calculate the gradients for N-R iteration
            slopeIQ = 0.5/((errorIP-errorIN) + 1j*(errorQP-errorQN))
            slopeI  =  1/np.real(slopeIQ)
            slopeQ  = -1/np.imag(slopeIQ)

            # calculate next I values for N-R iteration
            currentI = currentI + round(-1*currentE/slopeI)
            if currentI   > 31: currentI = 31
            elif currentI <  0: currentI =  0

            # calculate next Q values for N-R iteration
            currentQ = currentQ + round(-1*currentE/slopeQ)
            if currentQ   > 31: currentQ = 31
            elif currentQ <  0: currentQ =  0

            # measure new ERROR
            self.setTXoffset(currentI,currentQ)
            valI, valQ = self.getRXoffset()
            currentE = abs((valI-minVI) + 1j*(valQ-minVQ))

            # update iteration counter
            iteration = iteration+1

        #STEP5: print final I & Q values, final ERROR and number of iterations
        print 'RXdcoI= {0:2}, RXdcoQ = {1:2}, error = {2:3}, iteration = {3:2}'.format(currentI,currentQ,currentE,iteration)


if __name__ == "__main__":
    pass
