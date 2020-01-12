class TxDco(object):
    import time

    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(TxDco, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self):
        if self.__initialized:
            return
        import register
        import rx_iq_meas
        import temp
        import eder_status
        import eder_logger
        self.__initialized = True
        self.regs = register.Register()
        self.rx_iq_meas = rx_iq_meas.RxIQMeas()
        self.temp = temp.Temp()
        self.status = eder_status.EderStatus()
        self.logger = eder_logger.EderLogger()
        
    def run(self, do_print=False):
        wait_time = 0.001
        import rx
        import tx
        tx = tx.Tx()
        rx = rx.Rx()

        # Store current gain settings
        trx_tx_on_stored = self.regs.rd('trx_tx_on')
        tx_bb_iq_gain_stored = self.regs.rd('tx_bb_iq_gain')
        tx_bb_gain_stored = self.regs.rd('tx_bb_gain')
        tx_bfrf_gain_stored = self.regs.rd('tx_bfrf_gain')
        trx_rx_on_stored = self.regs.rd('trx_rx_on')
        bias_lo_stored = self.regs.rd('bias_lo')
        tx_beam_store = tx.bf.awv.get()&0x3f
   
        rx_gain_ctrl_bb1_stored = self.regs.rd('rx_gain_ctrl_bb1')
        rx_gain_ctrl_bb2_stored = self.regs.rd('rx_gain_ctrl_bb2')
        rx_gain_ctrl_bb3_stored = self.regs.rd('rx_gain_ctrl_bb3')
        rx_gain_ctrl_bfrf_stored = self.regs.rd('rx_gain_ctrl_bfrf')
        rx_bb_test_ctrl_stored = self.regs.rd('rx_bb_test_ctrl')
        trx_ctrl_stored = self.regs.rd('trx_ctrl')
        bias_rx_stored = self.regs.rd('bias_rx')

        freq = tx.freq
        print 'freq: ' + str(tx.freq)
        
        tx.disable()
        rx.disable()
        rx.init(0x1F0000)
        self.regs.wr('trx_ctrl', 0x01)
        import time

        import numpy as np

        self.regs.wr('rx_gain_ctrl_bb1', 0xFF)
        self.regs.wr('rx_gain_ctrl_bb2', 0xFF)
        self.regs.wr('rx_gain_ctrl_bb3', 0x77)
        self.regs.wr('rx_gain_ctrl_bfrf', 0x0F)

        self.regs.wr('tx_bfrf_gain', tx_bfrf_gain_stored|0x0F)

        rx.enable()
        rx.dco.report('sys')
        rx.dco.run()
        
        self.regs.wr('trx_tx_on', 0x1F0000)
        self.regs.wr('bias_lo', 0x2A)
        self.regs.set('trx_ctrl', 0x03)


        #STEP 1: create parameters for calibration
        errorTXmax = 0         # maximum allowed error
        lower_limit= 4.0
        currentE   = 100       # place holder for error value
        stepI      = 6         # optimization step for I
        stepQ      = 6         # optimization step for Q


        # Find max error
        self.regs.wr('tx_bb_i_dco', 0)
        self.regs.wr('tx_bb_q_dco', 0)
        time.sleep(wait_time)

        self.regs.set('tx_ctrl', 0x40)

        TRASH = tx.dco.rx_iq_meas.meas_vdiff()
        valI_lb  = TRASH['idiff']
        valQ_lb  = TRASH['qdiff']

        self.regs.clr('tx_ctrl', 0x40)

        TRASH = tx.dco.rx_iq_meas.meas_vdiff()
        valI  = TRASH['idiff']
        valQ  = TRASH['qdiff']

        self.regs.set('tx_ctrl', 0x40)

        currentE = abs((valI-valI_lb) + 1j*(valQ-valQ_lb))

        print 'tx_bb_i_dco: 0x{0:02X}  tx_bb_q_dco: 0x{1:02X}  error: {2}'.format(0, 0, currentE)
        if currentE > 300:
            errorTXmax = currentE / 35
        else:
            errorTXmax = currentE / 7

        

        if self.regs.rd('tx_ctrl')&0x04:
            #currentI   = 0x5A - stepI
            #currentQ   = 0x5A - stepQ
            currentI   = 0x26 - stepI
            currentQ   = 0x26 - stepQ
        else:
            currentI   = 0x30 - stepI
            currentQ   = 0x30 - stepQ
            #currentI   = 0x26 - stepI
            #currentQ   = 0x26 - stepQ

        self.regs.wr('tx_bb_i_dco',currentI)
        self.regs.wr('tx_bb_q_dco',currentQ)
        time.sleep(wait_time)

        TRASH = tx.dco.rx_iq_meas.meas_vdiff()
        valI_lb  = TRASH['idiff']
        valQ_lb  = TRASH['qdiff']

        self.regs.clr('tx_ctrl', 0x40)

        TRASH = tx.dco.rx_iq_meas.meas_vdiff()
        valI  = TRASH['idiff']
        valQ  = TRASH['qdiff']

        self.regs.set('tx_ctrl', 0x40)

        currentE = abs((valI-valI_lb) + 1j*(valQ-valQ_lb))

        print 'tx_bb_i_dco: 0x{0:02X}  tx_bb_q_dco: 0x{1:02X}  error: {2}'.format(int(currentI), int(currentQ), currentE)

        #STEP 4: run the search using modified 2D Newton-Rhapson method
        while (currentE >= errorTXmax) and (currentE > lower_limit) :
            if currentE < 300:
                stepI = 1
                stepQ = 1
            else:
                stepI = 6
                stepQ = 6

            # get rxDCoI & rxDCoQ @ I+step,Q and calculate the ERROR
            self.regs.wrrd('tx_bb_i_dco',currentI+stepI)
            self.regs.wrrd('tx_bb_q_dco',currentQ)
            time.sleep(wait_time)
            TRASH = tx.dco.rx_iq_meas.meas_vdiff()
            valI_lb  = TRASH['idiff']
            valQ_lb  = TRASH['qdiff']

            self.regs.clr('tx_ctrl', 0x40)
            TRASH = tx.dco.rx_iq_meas.meas_vdiff()
            valI  = TRASH['idiff']
            valQ  = TRASH['qdiff']
            self.regs.set('tx_ctrl', 0x40)


            errorIP = abs((valI-valI_lb) + 1j*(valQ-valQ_lb))

            # get rxDCoI & rxDCoQ @ I-step,Q and calculate the ERROR
            self.regs.wrrd('tx_bb_i_dco',currentI-stepI)
            self.regs.wrrd('tx_bb_q_dco',currentQ)
            time.sleep(wait_time)
            
            TRASH = tx.dco.rx_iq_meas.meas_vdiff()
            valI_lb  = TRASH['idiff']
            valQ_lb  = TRASH['qdiff']

            self.regs.clr('tx_ctrl', 0x40)
            TRASH = tx.dco.rx_iq_meas.meas_vdiff()
            valI  = TRASH['idiff']
            valQ  = TRASH['qdiff']
            self.regs.set('tx_ctrl', 0x40)

            errorIN = abs((valI-valI_lb) + 1j*(valQ-valQ_lb))

            # get rxDCoI & rxDCoQ @ I,Q+step and calculate the ERROR
            self.regs.wrrd('tx_bb_i_dco',currentI)
            self.regs.wrrd('tx_bb_q_dco',currentQ+stepQ)
            time.sleep(wait_time)
            
            TRASH = tx.dco.rx_iq_meas.meas_vdiff()
            valI_lb  = TRASH['idiff']
            valQ_lb  = TRASH['qdiff']

            self.regs.clr('tx_ctrl', 0x40)
            TRASH = tx.dco.rx_iq_meas.meas_vdiff()
            valI  = TRASH['idiff']
            valQ  = TRASH['qdiff']
            self.regs.set('tx_ctrl', 0x40)

            errorQP = abs((valI-valI_lb) + 1j*(valQ-valQ_lb))

            # get rxDCoI & rxDCoQ @ I,Q-step and calculate the ERROR
            self.regs.wrrd('tx_bb_i_dco',currentI)
            self.regs.wrrd('tx_bb_q_dco',currentQ-stepQ)
            time.sleep(wait_time)
            
            TRASH = tx.dco.rx_iq_meas.meas_vdiff()
            valI_lb  = TRASH['idiff']
            valQ_lb  = TRASH['qdiff']

            self.regs.clr('tx_ctrl', 0x40)
            TRASH = tx.dco.rx_iq_meas.meas_vdiff()
            valI  = TRASH['idiff']
            valQ  = TRASH['qdiff']
            self.regs.set('tx_ctrl', 0x40)

            errorQN = abs((valI-valI_lb) + 1j*(valQ-valQ_lb))

            # calculate the gradients for N-R iteration
            if (errorIP == errorIN) or (errorQP == errorQN):
            	continue
            slopeIQ = 1.5/((errorIP-errorIN) + 1j*(errorQP-errorQN))
            if (np.real(slopeIQ) == 0) or (np.imag(slopeIQ) == 0):
            	continue
            slopeI  =  1/np.real(slopeIQ)
            slopeQ  = -1/np.imag(slopeIQ)

            # calculate next I values for N-R iteration
            #currentI = currentI + round(-2*currentE/slopeI)
            currentI = currentI + round(-1*currentE/slopeI)
            #print '****'
            #print currentI
            if currentI   > 127:
                currentI = 0x28
            elif currentI <  0:
                currentI = 0x64
            #print currentI

            # calculate next Q values for N-R iteration
            #currentQ = currentQ + round(-2*currentE/slopeQ)
            currentQ = currentQ + round(-1*currentE/slopeQ)
            #print '****'
            #print currentQ
            if currentQ   > 127:
                currentQ = 0x28
            elif currentQ <  0:
                currentQ = 0x64

            #print currentQ

            # measure new ERROR
            self.regs.wr('tx_bb_i_dco',currentI)
            self.regs.wr('tx_bb_q_dco',currentQ)
            time.sleep(wait_time)
            
            TRASH = tx.dco.rx_iq_meas.meas_vdiff()
            valI_lb  = TRASH['idiff']
            valQ_lb  = TRASH['qdiff']

            self.regs.clr('tx_ctrl', 0x40)
            TRASH = tx.dco.rx_iq_meas.meas_vdiff()
            valI  = TRASH['idiff']
            valQ  = TRASH['qdiff']
            self.regs.set('tx_ctrl', 0x40)

            currentE = abs((valI-valI_lb) + 1j*(valQ-valQ_lb))

            print 'tx_bb_i_dco: 0x{0:02X}  tx_bb_q_dco: 0x{1:02X}  error: {2}'.format(int(currentI), int(currentQ), currentE)


        if ((int(currentI) == 0) or (int(currentQ) == 0)):
            print 'TX LO leakage calibration failed'
        else:
            print 'TX LO leakage calibration complete.'
            print 'tx_bb_i_dco: ' + hex(self.regs.rd('tx_bb_i_dco'))
            print 'tx_bb_q_dco: ' + hex(self.regs.rd('tx_bb_q_dco'))

        self.regs.clr('tx_ctrl', 0x40)

        #STEP 5: print final I & Q values, final ERROR and number of iterations
        rx.disable()

        # Write back stored gain settings
        rx.status.clr_init_bit(rx.status.RX_INIT)
        self.regs.wr('trx_tx_on', trx_tx_on_stored)
        self.regs.wr('tx_bb_iq_gain', tx_bb_iq_gain_stored)
        self.regs.wr('tx_bb_gain', tx_bb_gain_stored)
        self.regs.wr('tx_bfrf_gain', tx_bfrf_gain_stored)
        self.regs.wr('trx_rx_on', trx_rx_on_stored)
        self.regs.wr('bias_lo', bias_lo_stored)
        self.regs.wr('rx_gain_ctrl_bb1', rx_gain_ctrl_bb1_stored)
        self.regs.wr('rx_gain_ctrl_bb2', rx_gain_ctrl_bb2_stored)
        self.regs.wr('rx_gain_ctrl_bb3', rx_gain_ctrl_bb3_stored)
        self.regs.wr('rx_gain_ctrl_bfrf', rx_gain_ctrl_bfrf_stored)
        self.regs.wr('rx_bb_test_ctrl',rx_bb_test_ctrl_stored)
        self.regs.wr('trx_ctrl', trx_ctrl_stored)
        self.regs.wr('bias_rx',bias_rx_stored)
        tx.set_beam(tx_beam_store)


    def run_sweep(self, do_print=False):
        wait_time = 0.005

        import rx
        import tx
        tx = tx.Tx()
        rx = rx.Rx()

        # Store current gain settings
        trx_tx_on_stored = self.regs.rd('trx_tx_on')
        tx_bb_iq_gain_stored = self.regs.rd('tx_bb_iq_gain')
        tx_bb_gain_stored = self.regs.rd('tx_bb_gain')
        tx_bfrf_gain_stored = self.regs.rd('tx_bfrf_gain')
        trx_rx_on_stored = self.regs.rd('trx_rx_on')
        bias_lo_stored = self.regs.rd('bias_lo')
        tx_beam_store = tx.bf.awv.get()
   
        rx_gain_ctrl_bb1_stored = self.regs.rd('rx_gain_ctrl_bb1')
        rx_gain_ctrl_bb2_stored = self.regs.rd('rx_gain_ctrl_bb2')
        rx_gain_ctrl_bb3_stored = self.regs.rd('rx_gain_ctrl_bb3')
        rx_gain_ctrl_bfrf_stored = self.regs.rd('rx_gain_ctrl_bfrf')
        rx_bb_test_ctrl_stored = self.regs.rd('rx_bb_test_ctrl')
        trx_ctrl_stored = self.regs.rd('trx_ctrl')
        bias_rx_stored = self.regs.rd('bias_rx')

        freq = tx.freq
        print 'freq: ' + str(tx.freq)
        import time
        time.sleep(10)
        current_temp = self.temp.run()
        previous_temp = 0
        while (current_temp - previous_temp) > 0.1:
                previous_temp = current_temp
                time.sleep(3)
                current_temp = self.temp.run()
                print 'temp: {0} C'.format(round(current_temp-273.15,2))

        target_temp = (current_temp - 273.15) * 1.05
        
        tx.disable()
        rx.disable()
        tx.bf.awv.setup('lut/beambook/bf_tx_awv', 0.0, 0.0)
        tx.bf.idx.setup('lut/beambook/bf_tx_awv_idx', 0.0)
        tx.set_beam(0)
        rx.init(0x1F0000)
        rx.setup_no_dco_cal(0.0, 0, 0x1F0000)
        self.regs.wr('trx_ctrl', 0x01)
        import time
        print 'Wait for temperature stabilization'
        previous_temp = 0
        current_temp = self.temp.run()

        while (current_temp - previous_temp) > 0.1:
                previous_temp = current_temp
                time.sleep(1)
                current_temp = self.temp.run()
                print 'temp: {0} C'.format(round(current_temp-273.15,2))
                if current_temp-273.15 > target_temp:
                    break
        if current_temp-273.15 > target_temp:
            print 'Target temperature reached'
        else:
            print 'Temperature stabilized'

        self.regs.wr('trx_tx_on', 0x1F0000)

        # Calibration starts here
        self.regs.wr('tx_bfrf_gain', 0xEE)

        import numpy as np
        
        # OK
        self.regs.wr('rx_gain_ctrl_bb1', 0xFF)
        self.regs.wr('rx_gain_ctrl_bb2', 0x77)
        self.regs.wr('rx_gain_ctrl_bb3', 0x33)
        self.regs.wr('rx_gain_ctrl_bfrf', 0xEE)

        rx.enable()

        rx.dco.report('sys')
        rx.dco.run()
        TRASH = tx.dco.rx_iq_meas.meas_vdiff()
        print '******************************'
        print TRASH
        print '******************************'
        minVI = TRASH['idiff']
        minVQ = TRASH['qdiff']


        self.regs.set('trx_ctrl', 0x02)
        self.regs.set('tx_ctrl', 0x40)

        #STEP 1: create parameters for calibration
        currentE   = 100       # place holder for error value
        
        #STEP 2: perform RX-calibration and read RX DC-offset value
        #rx.dco.report()
        current_temp = self.temp.run()
        print 'temp: ' + str(current_temp-273.15)
        print "RX DCO Ready"
        time.sleep(0.05)
        min_error = 2000
        for currentI in range(0,0x7f):
            for currentQ in range(0,0x7f):
                # measure new ERROR
                self.regs.wr('tx_bb_i_dco',currentI)
                self.regs.wr('tx_bb_q_dco',currentQ)
                time.sleep(wait_time)
                TRASH = tx.dco.rx_iq_meas.meas_vdiff()
                valI  = TRASH['idiff']
                valQ  = TRASH['qdiff']
                print 'idiff: ', str(TRASH['idiff'])
                print 'qdiff: ', str(TRASH['qdiff'])
                currentE = abs((valI-minVI) + 1j*(valQ-minVQ))
                print 'tx_bb_i_dco: 0x{0:02X}  tx_bb_q_dco: 0x{1:02X}  error: {2}'.format(int(currentI), int(currentQ), currentE)
                if currentE < min_error:
                    min_error = currentE
                    best_tx_bb_i_dco = currentI
                    best_tx_bb_q_dco = currentQ

        print 'min_error: ', str(min_error)
        print 'best_tx_bb_i_dco: ' + hex(best_tx_bb_i_dco)
        print 'best_tx_bb_q_dco: ' + hex(best_tx_bb_q_dco)

        #STEP 5: print final I & Q values, final ERROR and number of iterations
        rx.disable()
        tx.bf.awv.setup('lut/beambook/bf_tx_awv', freq, 0.0)
        tx.bf.idx.setup('lut/beambook/bf_tx_awv_idx', freq)

        self.regs.clr('tx_ctrl', 0x40)

        # Write back stored gain settings
        rx.status.clr_init_bit(rx.status.RX_INIT)
        self.regs.wr('trx_tx_on', trx_tx_on_stored)
        self.regs.wr('tx_bb_iq_gain', tx_bb_iq_gain_stored)
        self.regs.wr('tx_bb_gain', tx_bb_gain_stored)
        self.regs.wr('tx_bfrf_gain', tx_bfrf_gain_stored)
        self.regs.wr('trx_rx_on', trx_rx_on_stored)
        self.regs.wr('bias_lo', bias_lo_stored)
        self.regs.wr('rx_gain_ctrl_bb1', rx_gain_ctrl_bb1_stored)
        self.regs.wr('rx_gain_ctrl_bb2', rx_gain_ctrl_bb2_stored)
        self.regs.wr('rx_gain_ctrl_bb3', rx_gain_ctrl_bb3_stored)
        self.regs.wr('rx_gain_ctrl_bfrf', rx_gain_ctrl_bfrf_stored)
        self.regs.wr('rx_bb_test_ctrl',rx_bb_test_ctrl_stored)
        self.regs.wr('trx_ctrl', trx_ctrl_stored)
        self.regs.wr('bias_rx',bias_rx_stored)
        tx.set_beam(tx_beam_store)
