class RxDco(object):

    try:
        import ederftdi
        if ederftdi.extdcodac() == 1:
            External_DCO_DAC_present = True
            print '  External DCO DAC found.'
        else:
            External_DCO_DAC_present = False
    except:
        External_DCO_DAC_present = False


    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(RxDco, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self):
        if self.__initialized:
            return
        import register
        import rx_iq_meas
        import rx
        import eder_status
        import eder_logger
        self.__initialized = True
        self.regs    = register.Register()
        self.iq_meas = rx_iq_meas.RxIQMeas()
        self.rx = rx.Rx()
        self._decToVolt = self.iq_meas._decToVolt
        self.status  = eder_status.EderStatus()
        self.logger  = eder_logger.EderLogger()

    def init(self):
        if self.status.init_bit_is_set(self.status.RXDCO_INIT) == False:
            self.iq_meas.init()
            self.status.set_init_bit(self.status.RXDCO_INIT)

    def default(self):
        self.regs.wr('rx_bb_q_dco',self.regs.value('rx_bb_q_dco'))
        self.regs.wr('rx_bb_i_dco',self.regs.value('rx_bb_i_dco'))

    def reset(self):
        self.default()
        self.iq_meas.reset()
        self.status.clr_init_bit(self.status.RXDCO_INIT)


    def dco_split(self,dco_reg):
        return {'mult':(dco_reg>>12)&0x3, 'shift':(dco_reg>>8)&0x3, 'val':dco_reg&0x7f}
    
    def dco(self, mult, shift, val):
            return (mult<<12) + (shift<<8) + val

    def print_report(self, meas):
        dco_i = self.regs.rd('rx_bb_i_dco')
        dco_q = self.regs.rd('rx_bb_q_dco')
        self.logger.log_info('rx_bb_i_dco : ' + hex(dco_i) + ' (' + hex(self.dco_split(dco_i)['mult']) + ',' + hex(self.dco_split(dco_i)['shift']) + ',' + hex(self.dco_split(dco_i)['val']) + ')',2)
        self.logger.log_info('rx_bb_q_dco : ' + hex(dco_q) + ' (' + hex(self.dco_split(dco_q)['mult']) + ',' + hex(self.dco_split(dco_q)['shift']) + ',' + hex(self.dco_split(dco_q)['val']) + ')',2)
        self.logger.log_info('V_i_diff    : ' + str(self._decToVolt(meas['idiff'])/(-2.845)) + ' V',2)
        self.logger.log_info('V_q_diff    : ' + str(self._decToVolt(meas['qdiff'])/(-2.845)) + ' V',2)
        self.logger.log_info('V_i_com     : ' + str(self._decToVolt(meas['icm'])) + ' V',2)
        self.logger.log_info('V_q_com     : ' + str(self._decToVolt(meas['qcm'])) + ' V',2)
        
        
    def report(self, meas_type='sys'):
        self.print_report(self.iq_meas.meas(32,meas_type))


        
    def sweep(self, meas_type='sys', search_scope='full', iq='iq', do_print=False):

        if self.status.init_bit_is_set(self.status.RXDCO_INIT) == False:
            self.init()

        i       = {'min':100000000, 'dco':0, 'cal':0, 'msb':0}
        q       = {'min':100000000, 'dco':0, 'cal':0, 'msb':0}
        restore = {}

        restore['dco_i'] = self.regs.rd('rx_bb_i_dco')
        restore['dco_q'] = self.regs.rd('rx_bb_q_dco')
        
        self.report(meas_type)

        if search_scope == 'full':
		msb_scope = {0:(0,0), 1:(1,1), 2:(2,2), 3:(3,3)}
        else:
        	msb_scope = {0:search_scope}

        for k,(msb_i,msb_q) in msb_scope.iteritems():
            for y in xrange(0, 128):

                if (iq == 'iq') or (iq == 'q'):
                    self.regs.wr('rx_bb_q_dco',self.dco(msb_q,y))
                else:
                    self.regs.wr('rx_bb_q_dco',0)

                if (iq == 'iq') or (iq == 'i'):
                    self.regs.wr('rx_bb_i_dco',self.dco(msb_i,y))
                else:
                    self.regs.wr('rx_bb_i_dco',0)

                meas = self.iq_meas.meas_vdiff(16,meas_type,'No')

                if (abs(meas['idiff']) < i['min']):
                    i['min'] = abs(meas['idiff'])
                    i['dco'] = self.dco(msb_i,y)
                    i['msb'] = msb_i
                    i['cal'] = y
                if (abs(meas['qdiff']) < q['min']):
                    q['min'] = abs(meas['qdiff'])
                    q['dco'] = self.dco(msb_q,y)
                    q['msb'] = msb_q
                    q['cal'] = y
                if do_print:
                    self.report(meas_type)

        self.regs.wr('rx_bb_i_dco',restore['dco_i'])
        self.regs.wr('rx_bb_q_dco',restore['dco_q'])
        return {'q':q['dco'], 'i':i['dco'], 'imeas':i, 'qmeas':q}


    def run_dco_cal(self, iq, mtype='sys'):

        if iq == 'i':
            register = 'rx_bb_i_dco'
            diff = 'idiff'
        elif iq == 'q':
            register = 'rx_bb_q_dco'
            diff = 'qdiff'
        else:
            print 'Invalid argument.'
            return

        sign = lambda x: x and (1, -1)[x < 0]

        selected_mult = -1
        selected_shift = -1
        for mult in range(0,4):
            if selected_mult != -1:
                break
            for shift in range(0,3):
                self.regs.wr(register, (mult<<12) + (shift<<8))
                measured_values_0 = self.iq_meas.meas(meas_type=mtype)
                self.regs.wr(register, (mult<<12)+(shift<<8)+0x7F)
                measured_values_1 = self.iq_meas.meas(meas_type=mtype)
                if sign(measured_values_0[diff]) != sign(measured_values_1[diff]):
                    selected_mult = mult
                    selected_shift = shift
                    break

        if selected_mult == -1:
            print 'RX DCO calibration failed!'
            return 0

        START = 0
        MID = 1
        END = 2

        rx_bb_dco = [0,0,0]
        dco_diff = [0,0,0]

        rx_bb_dco[START] = 0
        rx_bb_dco[END] = 0x7F

        average = (rx_bb_dco[START] + rx_bb_dco[END]) / 2
        rx_bb_dco[MID] = int(round(average, 0))

        self.regs.wr(register, (selected_mult<<12)|(selected_shift<<8)|rx_bb_dco[START])
        measured_values = self.iq_meas.meas(meas_type=mtype)
        dco_diff[START] = measured_values[diff]

        self.regs.wr(register, (selected_mult<<12)|(selected_shift<<8)|rx_bb_dco[MID])
        measured_values = self.iq_meas.meas(meas_type=mtype)
        dco_diff[MID] = measured_values[diff]

        self.regs.wr(register, (selected_mult<<12)|(selected_shift<<8)|rx_bb_dco[END])
        measured_values = self.iq_meas.meas(meas_type=mtype)
        dco_diff[END] = measured_values[diff]

        while (abs(rx_bb_dco[START]-rx_bb_dco[MID]) > 1) or (abs(rx_bb_dco[MID]-rx_bb_dco[END]) > 1):
            if sign(dco_diff[START]) == sign(dco_diff[MID]):
                rx_bb_dco[START] = rx_bb_dco[MID]
                average = (rx_bb_dco[START] + rx_bb_dco[END]) / 2
                rx_bb_dco[MID] = int(round(average, 0))
                dco_diff[START] = dco_diff[MID]
                self.regs.wr(register, (selected_mult<<12)|(selected_shift<<8)|rx_bb_dco[MID])
                measured_values = self.iq_meas.meas(meas_type=mtype)
                dco_diff[MID] = measured_values[diff]
            elif sign(dco_diff[END]) == sign(dco_diff[MID]):
                rx_bb_dco[END] = rx_bb_dco[MID]
                average = (rx_bb_dco[START] + rx_bb_dco[END]) / 2
                rx_bb_dco[MID] = int(round(average, 0))
                dco_diff[END] = dco_diff[MID]
                self.regs.wr(register, (selected_mult<<12)|(selected_shift<<8)|rx_bb_dco[MID])
                measured_values = self.iq_meas.meas(meas_type=mtype)
                dco_diff[MID] = measured_values[diff]
            else:
                # mid_dco diff is 0'
                # Doubble check
                if dco_diff[MID] == 0:
                    self.regs.wr(register, (selected_mult<<12)|(selected_shift<<8)|rx_bb_dco[MID])
                    break
                else:
                    print 'Something went wrong!!!'
            #print rx_bb_dco
            #print dco_diff
            
        dco_diff = map(abs, dco_diff)
        i = dco_diff.index(min(dco_diff))
            
        self.regs.wr(register, (selected_mult<<12)|(selected_shift<<8)|rx_bb_dco[i])
        return (selected_mult<<12)|(selected_shift<<8)|rx_bb_dco[i]

    def ext_run_dco_cal(self, iq, mtype='sys'):

        if iq == 'i':
            rdac = 2
            diff = 'idiff'
        elif iq == 'q':
            rdac = 1
            diff = 'qdiff'
        else:
            print 'Invalid argument.'
            return

        sign = lambda x: x and (1, -1)[x < 0]

        START = 0
        MID = 1
        END = 2

        ext_rx_bb_dco = [0,0,0]
        dco_diff = [0,0,0]

        ext_rx_bb_dco[START] = 0
        ext_rx_bb_dco[END] = 0xFF

        average = (ext_rx_bb_dco[START] + ext_rx_bb_dco[END]) / 2
        ext_rx_bb_dco[MID] = int(round(average, 0))

        self.ederftdi.setdcodac(rdac, ext_rx_bb_dco[START])
        measured_values = self.iq_meas.meas(meas_type=mtype)
        dco_diff[START] = measured_values[diff]

        self.ederftdi.setdcodac(rdac, ext_rx_bb_dco[MID])
        measured_values = self.iq_meas.meas(meas_type=mtype)
        dco_diff[MID] = measured_values[diff]

        self.ederftdi.setdcodac(rdac, ext_rx_bb_dco[END])
        measured_values = self.iq_meas.meas(meas_type=mtype)
        dco_diff[END] = measured_values[diff]

        while (abs(ext_rx_bb_dco[START]-ext_rx_bb_dco[MID]) > 1) or (abs(ext_rx_bb_dco[MID]-ext_rx_bb_dco[END]) > 1):
            if sign(dco_diff[START]) == sign(dco_diff[MID]):
                if abs(dco_diff[START]) >= abs(dco_diff[MID]):
                    ext_rx_bb_dco[START] = ext_rx_bb_dco[MID]
                    average = (ext_rx_bb_dco[START] + ext_rx_bb_dco[END]) / 2
                    ext_rx_bb_dco[MID] = int(round(average, 0))
                    dco_diff[START] = dco_diff[MID]
                    self.ederftdi.setdcodac(rdac, ext_rx_bb_dco[MID])
                    measured_values = self.iq_meas.meas(meas_type=mtype)
                    dco_diff[MID] = measured_values[diff]
                    continue

            if sign(dco_diff[END]) == sign(dco_diff[MID]):
                if abs(dco_diff[END]) >= abs(dco_diff[MID]):
                    ext_rx_bb_dco[END] = ext_rx_bb_dco[MID]
                    average = (ext_rx_bb_dco[START] + ext_rx_bb_dco[END]) / 2
                    ext_rx_bb_dco[MID] = int(round(average, 0))
                    dco_diff[END] = dco_diff[MID]
                    self.ederftdi.setdcodac(rdac, ext_rx_bb_dco[MID])
                    measured_values = self.iq_meas.meas(meas_type=mtype)
                    dco_diff[MID] = measured_values[diff]
                    continue

            if abs(dco_diff[START]) >= abs(dco_diff[MID]):
                ext_rx_bb_dco[START] = ext_rx_bb_dco[MID]
                average = (ext_rx_bb_dco[START] + ext_rx_bb_dco[END]) / 2
                ext_rx_bb_dco[MID] = int(round(average, 0))
                dco_diff[START] = dco_diff[MID]
                self.ederftdi.setdcodac(rdac, ext_rx_bb_dco[MID])
                measured_values = self.iq_meas.meas(meas_type=mtype)
                dco_diff[MID] = measured_values[diff]

            if abs(dco_diff[END]) >= abs(dco_diff[MID]):
                ext_rx_bb_dco[END] = ext_rx_bb_dco[MID]
                average = (ext_rx_bb_dco[START] + ext_rx_bb_dco[END]) / 2
                ext_rx_bb_dco[MID] = int(round(average, 0))
                dco_diff[END] = dco_diff[MID]
                self.ederftdi.setdcodac(rdac, ext_rx_bb_dco[MID])
                measured_values = self.iq_meas.meas(meas_type=mtype)
                dco_diff[MID] = measured_values[diff]

        dco_diff = map(abs, dco_diff)
        i = dco_diff.index(min(dco_diff))

        self.ederftdi.setdcodac(rdac, ext_rx_bb_dco[i])
        return ext_rx_bb_dco[i]

    def int_run(self, meas_type='sys'):
        self.regs.wr('rx_dco_en',0x01)
        self.report(meas_type)
        rx_gain_ctrl_bfrf = self.regs.rd('rx_gain_ctrl_bfrf')
        beam = self.rx.get_beam()
        self.regs.wr('rx_gain_ctrl_bfrf', rx_gain_ctrl_bfrf&0x0F)
        self.rx.set_beam(63)
        rx_bb_i_dco = self.run_dco_cal('i', meas_type)
        rx_bb_q_dco = self.run_dco_cal('q', meas_type)
        self.regs.wr('rx_gain_ctrl_bfrf', rx_gain_ctrl_bfrf)
        self.rx.set_beam(beam)
        self.report(meas_type)
        return rx_bb_i_dco, rx_bb_q_dco

    def ext_run(self, meas_type='sys'):
        self.regs.wr('rx_dco_en',0x00)
        self.report(meas_type)
        rx_bb_i_dco_ext = self.ext_run_dco_cal('i', meas_type)
        rx_bb_q_dco_ext = self.ext_run_dco_cal('q', meas_type)
        print '  rx_bb_i_dco_ext : ' + hex(rx_bb_i_dco_ext)
        print '  rx_bb_q_dco_ext : ' + hex(rx_bb_q_dco_ext)
        self.report(meas_type)
        return rx_bb_i_dco_ext, rx_bb_q_dco_ext

    def run(self):
        trx_ctrl = self.regs.rd('trx_ctrl')
        self.regs.wr('trx_ctrl', 0x01)

        if self.External_DCO_DAC_present == True:
            self.run_1()
        else:
            self.int_run()

        self.regs.wr('trx_ctrl', trx_ctrl)


    def run_1(self):
        rx_gain_ctrl_bfrf = self.regs.rd('rx_gain_ctrl_bfrf')
        rx_gain_ctrl_bb1 = self.regs.rd('rx_gain_ctrl_bb1')
        rx_gain_ctrl_bb2 = self.regs.rd('rx_gain_ctrl_bb2')
        rx_gain_ctrl_bb3 = self.regs.rd('rx_gain_ctrl_bb3')

        self.regs.wr('rx_gain_ctrl_bfrf', 0)
        self.regs.wr('rx_gain_ctrl_bb1', 0)
        self.regs.wr('rx_gain_ctrl_bb2', 0)
        self.regs.wr('rx_gain_ctrl_bb3', 0)

        self.ext_run()

        self.regs.wr('rx_gain_ctrl_bfrf', 0xff)
        self.regs.wr('rx_gain_ctrl_bb1', 0xff)
        self.regs.wr('rx_gain_ctrl_bb2', 0xff)
        self.regs.wr('rx_gain_ctrl_bb3', 0xff)

        self.int_run()

        self.regs.wr('rx_gain_ctrl_bfrf', rx_gain_ctrl_bfrf)
        self.regs.wr('rx_gain_ctrl_bb1', rx_gain_ctrl_bb1)
        self.regs.wr('rx_gain_ctrl_bb2', rx_gain_ctrl_bb2)
        self.regs.wr('rx_gain_ctrl_bb3', rx_gain_ctrl_bb3)


    def run_2(self):
        self.regs.wr('trx_rx_on', 0x140000)
        self.ext_run()
        self.regs.wr('trx_rx_on', 0x1FFFFF)
        self.int_run()
