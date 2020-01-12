class Test(object):

    import math

    def __init__(self, eder):
	    self.eder = eder

    def run_all(self):
        self.check_spi()
        self.check_i2c()
        self.check_45mhz()
        self.mbist()
		
    def check_spi(self):
        if self.eder.check():
            print 'SPI check         [OK]'
            return True
        print 'SPI check         [FAIL]'
        return False
		
    def check_i2c(self):
        temp = self.eder.eeprom.read_pcb_temp()
        if temp > 0.0:
            print 'I2C check         [OK]'
            return True
        print 'I2C check         [FAIL]'
        return False
		
    def check_45mhz(self):
        temp = self.eder.temp.run()
        if temp > 0.0:
            print '45MHz clock check [OK]'
            return True
        print '45MHz clock check [FAIL]'
        return False
		
    def mbist(self, port):
        if (port != 0) and (port != 0):
            print 'Port must be 0 or 1'
            return NULL
        self.eder.reset()   
        self.eder.init()
        bf_rx_mbist_done = self.eder.mems.mbist.rd('bf_rx_mbist_done')  # Check that this is all zeroes
        print bf_rx_mbist_done
        bf_tx_mbist_done = self.eder.mems.mbist.rd('bf_tx_mbist_done')  # Check that this is all zeroes
        print bf_tx_mbist_done
        result = (bf_rx_mbist_done == 0) and (bf_tx_mbist_done == 0)

        bf_rx_mbist_result = self.eder.mems.mbist.rd('bf_rx_mbist_result')  # Check that this is all zeroes
        print bf_rx_mbist_result
        bf_tx_mbist_result = self.eder.mems.mbist.rd('bf_tx_mbist_result')  # Check that this is all zeroes
        print bf_tx_mbist_result
        result = result and (bf_rx_mbist_result == 0) and (bf_tx_mbist_result == 0)

        self.eder.mems.mbist.wr('bf_rx_mbist_2p_sel', port)
        self.eder.mems.mbist.wr('bf_tx_mbist_2p_sel', port)
        self.eder.mems.mbist.wr('bf_rx_mbist_en',0xFFFF)
        self.eder.mems.mbist.wr('bf_tx_mbist_en',0xFFFF)
        bf_rx_mbist_done = self.eder.mems.mbist.rd('bf_rx_mbist_done')  # Check that this is all ones
        print bf_rx_mbist_done
        bf_tx_mbist_done = self.eder.mems.mbist.rd('bf_tx_mbist_done')  # Check that this is all ones
        print bf_tx_mbist_done
        result = result and (bf_rx_mbist_done == 0xFFFF) and (bf_tx_mbist_done == 0xFFFF)
      
        bf_rx_mbist_result = self.eder.mems.mbist.rd('bf_rx_mbist_result')  # Check that this is all zeroes
        print bf_rx_mbist_result
        bf_tx_mbist_result = self.eder.mems.mbist.rd('bf_tx_mbist_result')  # Check that this is all zeroes
        print bf_tx_mbist_result
        result = result and (bf_rx_mbist_result == 0) and (bf_tx_mbist_result == 0)

        self.eder.reset()
        if result == True:
            print 'MBIST             [OK]'
            return True
        print 'MBIST RX:0x{0:04X} TX:0x{1:04X} [FAIL]'.format(bf_rx_mbist_result, bf_tx_mbist_result)
        return False



    # Internal AGC test

    def agc_test(self):
        import time

        self.eder.fpga_clk(1)

        self.eder.regs.wr('agc_en', 0x15)
        self.eder.regs.wr('agc_timeout', 200)
        self.eder.regs.wr('agc_use_agc_ctrls', 0x3F)
        self.eder.regs.wr('agc_detector_mask', 0x1F1F)
        self.eder.regs.wr('agc_bf_rf_gain_lvl', 0x55443322)
        self.eder.regs.wr('agc_bb_gain_1db_lvl', 0x654321)

        #self.eder.regs.wr('gpio_agc_done_ctrl', 0x02)

        self.eder.ederftdi.setagcrst(1)
        time.sleep(0.01)
        self.eder.ederftdi.setagcrst(0)

        self.eder.ederftdi.setagcstart(1)
        time.sleep(0.01)
        self.eder.ederftdi.setagcstart(0)

        agc_status = self.eder.ederftdi.getagcstate()
        while (agc_status & 0x80) == 0:
            agc_status = self.eder.ederftdi.getagcstate()
        
        print hex(self.eder.ederftdi.getagcstate())




    # ADC Measurement tests

    def dco_beam_sweep(self, file_name='test_log.csv', num_samples=16, meas_type='bb'):
        import time
        with open(file_name, 'ab') as dco_log:
            writer = self.eder.csv.writer(dco_log)
            #writer.writerow([meas_type, "", "", "", ""])
            writer.writerow([meas_type])
            writer.writerow(["Beam", " Temp."," V_i_diff[ADC]"," V_i_diff[V]", " V_q_diff[ADC]", " V_q_diff[V]", " V_i_com[ADC]", " V_i_com[V]", " V_q_com[ADC]", " V_q_com[V]"])
            dco_log.close()
        
        rx_bb_i_vga_1_2 = self.eder.regs.rd('rx_bb_i_vga_1_2')
        rx_bb_q_vga_1_2 = self.eder.regs.rd('rx_bb_q_vga_1_2')

        self.eder.regs.wr('rx_bb_i_vga_1_2', 0xf1)
        self.eder.regs.wr('rx_bb_q_vga_1_2', 0xf1)
        self.eder.rx.dco.run()

        #self.eder.regs.wr('rx_bb_i_vga_1_2', rx_bb_i_vga_1_2)
        #self.eder.regs.wr('rx_bb_q_vga_1_2', rx_bb_q_vga_1_2)

        self.eder.regs.wr('rx_bb_i_vga_1_2', 0xf3)
        self.eder.regs.wr('rx_bb_q_vga_1_2', 0xf3)

        for beam in range(0,64):
            self.eder.rx.set_beam(beam)
            time.sleep(0.1)
            self.dco_log(file_name, beam, num_samples, meas_type)



    def dco_beam_gain_sweep(self, file_name='test_log.csv', numsamples=16):
        import time
        with open(file_name, 'ab') as dco_log:
            writer = self.eder.csv.writer(dco_log)
            writer.writerow(["BB1", "BB2", "i_diff[ADC]", " q_diff[ADC]", "i_diff[V]", " q_diff[V]"])
            dco_log.close()

            bb1_gain_vector = [0xFF, 0xFF, 0xFF, 0xFF, 0x77, 0x33, 0x11]
            bb2_gain_vector = [0xFF, 0x77, 0x33, 0x11, 0x11, 0x11, 0x11]
            beam_vector = [0, 14, 28, 32, 36, 50, 63]

            for beam_index in range(0,7):
                self.eder.rx.set_beam(beam_vector[beam_index])
                with open(file_name, 'ab') as dco_log:
                    writer = self.eder.csv.writer(dco_log)
                    writer.writerow(['beam', beam_vector[beam_index]])
                    for bb_gain_index in range(0,7):  
                        self.eder.regs.wr('rx_gain_ctrl_bb1', bb1_gain_vector[bb_gain_index])
                        self.eder.regs.wr('rx_gain_ctrl_bb2', bb2_gain_vector[bb_gain_index])
                        time.sleep(0.1)
                        trx_rx_on = self.eder.regs.rd('trx_rx_on')
                        self.eder.regs.wr('trx_rx_on', 0x1F0000)
                        diff = self.eder.rx.dco.iq_meas.meas_vdiff(num_samples=numsamples)
                        self.eder.regs.wr('trx_rx_on', trx_rx_on)
                        writer.writerow([bb1_gain_vector[bb_gain_index], bb2_gain_vector[bb_gain_index], diff['idiff'], diff['qdiff'], self._AdcToVolt(diff['idiff']), self._AdcToVolt(diff['qdiff'])])

            dco_log.close()
            self.eder.reset()



    def dco_gain_sweep(self, file_name='test_log.csv', numsamples=16):
        import time
        with open(file_name, 'ab') as dco_log:
            writer = self.eder.csv.writer(dco_log)
            writer.writerow(["BB1", "BB2", "i_diff[ADC]", " q_diff[ADC]", "i_diff[V]", " q_diff[V]"])
            dco_log.close()

            bb1_gain_vector = [0xFF, 0xFF, 0xFF, 0xFF, 0x77, 0x33, 0x11]
            bb2_gain_vector = [0xFF, 0x77, 0x33, 0x11, 0x11, 0x11, 0x11]

            with open(file_name, 'ab') as dco_log:
                writer = self.eder.csv.writer(dco_log)
                for bb_gain_index in range(0,7):  
                    self.eder.regs.wr('rx_gain_ctrl_bb1', bb1_gain_vector[bb_gain_index])
                    self.eder.regs.wr('rx_gain_ctrl_bb2', bb2_gain_vector[bb_gain_index])
                    time.sleep(0.1)
                    diff = self.eder.rx.dco.iq_meas.meas_vdiff(num_samples=numsamples)
                    writer.writerow([bb1_gain_vector[bb_gain_index], bb2_gain_vector[bb_gain_index], diff['idiff'], diff['qdiff'], self._AdcToVolt(diff['idiff']), self._AdcToVolt(diff['qdiff'])])

            dco_log.close()
            self.eder.reset()

    def dco_gain_sweep_calib(self, file_name='test_log.csv', numsamples=16):
        import time
        with open(file_name, 'ab') as dco_log:
            writer = self.eder.csv.writer(dco_log)
            writer.writerow(["BB1", "BB2", "i_diff[ADC]", " q_diff[ADC]", "i_diff[V]", " q_diff[V]", "rx_bb_i_dco", "rx_bb_q_dco"])
            dco_log.close()

            bb1_gain_vector = [0xFF, 0xFF, 0xFF, 0xFF, 0x77, 0x33, 0x11]
            bb2_gain_vector = [0xFF, 0x77, 0x33, 0x11, 0x11, 0x11, 0x11]

            with open(file_name, 'ab') as dco_log:
                writer = self.eder.csv.writer(dco_log)
                for bb_gain_index in range(0,7):  
                    self.eder.regs.wr('rx_gain_ctrl_bb1', bb1_gain_vector[bb_gain_index])
                    self.eder.regs.wr('rx_gain_ctrl_bb2', bb2_gain_vector[bb_gain_index])
                    rx_bb_i_dco, rx_bb_q_dco = self.eder.rx.dco.run()
                    time.sleep(0.5)
                    diff = self.eder.rx.dco.iq_meas.meas_vdiff(num_samples=numsamples)
                    writer.writerow([bb1_gain_vector[bb_gain_index], bb2_gain_vector[bb_gain_index], diff['idiff'], diff['qdiff'], self._AdcToVolt(diff['idiff']), self._AdcToVolt(diff['qdiff']), rx_bb_i_dco, rx_bb_q_dco])

            dco_log.close()
            self.eder.reset()

   
    def _AdcToVolt(self, number):
        return round(0.000886948*number,6)


    def dco_log(self, file_name, beam, num_samples, meas_type):
        measured_values = self.eder.rx.dco.iq_meas.meas(num_samples, meas_type)
        measured_values_v = dict()
        with open(file_name, 'ab') as dco_log:
            writer = self.eder.csv.writer(dco_log)
            temperature = round(self.eder.temp.run()-273, 1)
            measured_values_v['idiff'] = self.eder.rx.dco._decToVolt(measured_values['idiff'])
            measured_values_v['qdiff'] = self.eder.rx.dco._decToVolt(measured_values['qdiff'])
            measured_values_v['icm'] = self.eder.rx.dco._decToVolt(measured_values['icm'])
            measured_values_v['qcm'] = self.eder.rx.dco._decToVolt(measured_values['qcm'])
            writer.writerow([beam, temperature, measured_values['idiff'], measured_values_v['idiff'], measured_values['qdiff'], 
                             measured_values_v['qdiff'], measured_values['icm'], measured_values_v['icm'], measured_values['qcm'], measured_values_v['qcm']])
            dco_log.close()


    def dco_sweep(self, file_name='dco_sweep.csv', num_samples=16):
        with open(file_name, 'ab') as dco_log:
            writer = self.eder.csv.writer(dco_log)
            writer.writerow(['Shift', 'Mult. factor', 'Offset', 'i_diff', 'q_diff'])
            
            for shift in range(0,3):
                if shift == 0:
                    log_shift = 'no'
                elif shift == 1:
                    log_shift = 'neg.'
                else:
                    log_shift = 'pos.'
                for mult_fact in range(0,4):
                    if mult_fact == 0:
                        log_mult_fact = 'x1'
                    elif mult_fact == 1:
                        log_mult_fact = 'x2'
                    elif mult_fact == 2:
                        log_mult_fact = 'x3'
                    else:
                        log_mult_fact = 'x4'
                    for dco_reg_value in range(0,0x80):
                        rx_bb_iq_dco = dco_reg_value + (shift << 8) + (mult_fact << 12)
                        #print hex(rx_bb_iq_dco)
                        self.eder.regs.wr('rx_bb_i_dco', rx_bb_iq_dco)
                        self.eder.regs.wr('rx_bb_q_dco', rx_bb_iq_dco)
                        diff = self.eder.rx.dco.iq_meas.meas_vdiff(meas_cm='Yes')
                        writer.writerow([log_shift, log_mult_fact, dco_reg_value, diff['idiff'], diff['qdiff']])
        dco_log.close()
        
    def dco_beam_sweep_0001(self, file_name='dco_beam_sweep_0001.csv'):
        with open(file_name, 'ab') as log_file:
            writer = self.eder.csv.writer(log_file)
            writer.writerow(['Beam', 'i_diff(V)_ffff', 'q_diff(V)_ffff', 'i_diff(V)_0000', 'q_diff(V)_0000'])
            for beam in range(0,64):
                self.eder.rx.set_beam(beam)
                self.eder.regs.wr('trx_rx_on', 0x1fffff)
                measured_values = self.eder.rx.dco.iq_meas.meas()
                measured_values_v_1_idiff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845)
                measured_values_v_1_qdiff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845)
                self.eder.regs.wr('trx_rx_on', 0x1f0000)
                measured_values = self.eder.rx.dco.iq_meas.meas()
                measured_values_v_0_idiff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845)
                measured_values_v_0_qdiff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845)
                writer.writerow([beam, measured_values_v_1_idiff, measured_values_v_1_qdiff, measured_values_v_0_idiff, measured_values_v_0_qdiff])
        log_file.close()

    def dco_beam_sweep_0002(self, file_name='dco_beam_sweep_0002.csv'):
        import time
        with open(file_name, 'ab') as log_file:
            writer = self.eder.csv.writer(log_file)
            writer.writerow(['Beam', 'i_diff(V)', 'q_diff(V)'])
            for beam in range(0,64):
                self.eder.rx.set_beam(beam)
                time.sleep(0.1)
                measured_values = self.eder.rx.dco.iq_meas.meas()
                measured_values_v_1_idiff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845)
                measured_values_v_1_qdiff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845)
                writer.writerow([beam, measured_values_v_1_idiff, measured_values_v_1_qdiff])
        log_file.close()

    def dco_beam_sweep_0003(self, file_name='dco_beam_sweep_0003.csv'):
        import time
        self.eder.regs.wr('rx_gain_ctrl_bb1', 0x77)
        self.eder.regs.wr('rx_gain_ctrl_bb2', 0x33)
        self.eder.regs.wr('rx_gain_ctrl_bb3', 0xEE)
        self.eder.regs.wr('rx_gain_ctrl_bfrf', 0xEE)
        self.eder.rx.dco.run()
        with open(file_name, 'ab') as log_file:
            writer = self.eder.csv.writer(log_file)
            writer.writerow(['Beam', 'i_diff(V)', 'q_diff(V)'])
            for beam in range(0,64):
                self.eder.rx.set_beam(beam)
                time.sleep(0.1)
                measured_values = self.eder.rx.dco.iq_meas.meas()
                measured_values_v_1_idiff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845)
                measured_values_v_1_qdiff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845)
                writer.writerow([beam, measured_values_v_1_idiff, measured_values_v_1_qdiff])
        log_file.close()

    def dco_phase_sweep_0001(self, file_name='dco_phase_sweep_0001.csv'):
        import time
        with open(file_name, 'ab') as log_file:
            writer = self.eder.csv.writer(log_file)
            writer.writerow(['Phase', 'i_diff(V)', 'q_diff(V)'])
            for phase in range(0,0x41):
                for ant in range(0,16):
                    self.eder.rx.bf.awv.wr(31, ant, (phase << 8) | phase)
                self.eder.rx.set_beam(31)
                time.sleep(1)
                #self.eder.regs.wr('trx_rx_on', 0x1fffff)
                measured_values = self.eder.rx.dco.iq_meas.meas()
                measured_values_v_1_idiff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845)
                measured_values_v_1_qdiff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845)
                writer.writerow([phase, measured_values_v_1_idiff, measured_values_v_1_qdiff])
        log_file.close()

    def dco_single_phase_sweep_0001(self, ant, file_name='dco_single_phase_sweep_0001.csv'):
        with open(file_name, 'ab') as log_file:
            writer = self.eder.csv.writer(log_file)
            writer.writerow(['Phase', 'i_diff(V)', 'q_diff(V)'])
            for phase in range(0,0x41):
                self.eder.rx.bf.awv.wr(31, ant, (phase << 8) | phase)
                self.eder.rx.set_beam(31)
                self.eder.regs.wr('trx_rx_on', 0x1fffff)
                measured_values = self.eder.rx.dco.iq_meas.meas()
                measured_values_v_1_idiff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845)
                measured_values_v_1_qdiff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845)
                writer.writerow([phase, measured_values_v_1_idiff, measured_values_v_1_qdiff])
        log_file.close()

    def dco_single_ant_phase_sweep_0001(self, ant, file_name='dco_single_ant_phase_sweep_0001.csv'):
        with open(file_name, 'ab') as log_file:
            writer = self.eder.csv.writer(log_file)
            writer.writerow(['Phase', 'i_diff(V)', 'q_diff(V)'])
            self.eder.regs.wr('trx_rx_on', 0x1f0000|(1<<ant))
            for phase in range(0,0x41):
                self.eder.rx.bf.awv.wr(31, ant, (phase << 8) | phase)
                self.eder.rx.set_beam(31)
                measured_values = self.eder.rx.dco.iq_meas.meas()
                measured_values_v_1_idiff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845)
                measured_values_v_1_qdiff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845)
                writer.writerow([phase, measured_values_v_1_idiff, measured_values_v_1_qdiff])
        log_file.close()

    def dco_single_ant_phase_sweep_0002(self, ant, file_name='dco_single_ant_phase_sweep_0002.csv'):
        with open(file_name, 'ab') as log_file:
            writer = self.eder.csv.writer(log_file)
            writer.writerow(['I phase', 'Q phase', 'i_diff(V)', 'q_diff(V)'])
            self.eder.regs.wr('trx_rx_on', 0x1f0000|(1<<ant))
            self.eder.rx.bf.awv.wr(31, ant, 0x1f1f)
            self.eder.rx.dco.run()
            for i_phase in range(0,0x40):
                for q_phase in range(0,0x40):
                    self.eder.rx.bf.awv.wr(31, ant, (i_phase << 8) | q_phase)
                    self.eder.rx.set_beam(31)
                    measured_values = self.eder.rx.dco.iq_meas.meas()
                    measured_values_v_1_idiff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845)
                    measured_values_v_1_qdiff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845)
                    writer.writerow([i_phase, q_phase, measured_values_v_1_idiff, measured_values_v_1_qdiff])
        log_file.close()

    def dco_single_ant_phase_sweep_0003(self, ant, file_name='dco_single_ant_phase_sweep_0003'):
        with open(file_name+'_ant_'+str(ant)+'.csv', 'ab') as log_file:
            writer = self.eder.csv.writer(log_file)
            self.eder.regs.wr('trx_rx_on', 0x1f0000|(1<<ant))
            self.eder.rx.bf.awv.wr(31, ant, 0x1f1f)
            self.eder.rx.dco.run()
            row_data_idiff = []
            row_data_qdiff = []
            col_header = ['', 'q_phase', '']
            for i in range(0, 0x40):
                col_header = col_header + [i]
            writer.writerow(col_header)
            for i_phase in range(0,0x40):
                row_data_idiff = ['i_phase'] + [i_phase] + ['Vidiff']
                row_data_qdiff = ['i_phase'] + [i_phase] + ['Vqdiff']
                for q_phase in range(0,0x40):
                    self.eder.rx.bf.awv.wr(31, ant, (i_phase << 8) | q_phase)
                    self.eder.rx.set_beam(31)
                    measured_values = self.eder.rx.dco.iq_meas.meas()
                    measured_values_v_1_idiff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845)
                    measured_values_v_1_qdiff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845)
                    row_data_idiff = row_data_idiff + [measured_values_v_1_idiff]
                    row_data_qdiff = row_data_qdiff + [measured_values_v_1_qdiff]

                writer.writerow(row_data_idiff)
                writer.writerow(row_data_qdiff)
        log_file.close()

    def dco_single_ant_phase_sweep_0004(self, ant, file_name='dco_single_ant_phase_sweep_0004'):
        with open(file_name+'_ant_'+str(ant)+'_I'+'.csv', 'ab') as log_file_i:
            with open(file_name+'_ant_'+str(ant)+'_Q'+'.csv', 'ab') as log_file_q:
                writer_i = self.eder.csv.writer(log_file_i)
                writer_q = self.eder.csv.writer(log_file_q)
                self.eder.regs.wr('trx_rx_on', 0x1f0000|(1<<ant))
                self.eder.rx.bf.awv.wr(31, ant, 0x3f3f)
                import time
                time.sleep(30)
                self.eder.rx.dco.run()
                row_data_idiff = []
                row_data_qdiff = []
                col_header = ['', 'q_phase', '']
                for i in range(0, 0x40):
                    col_header = col_header + [i]
                writer_i.writerow(col_header)
                writer_q.writerow(col_header)
                for i_phase in range(0,0x40):
                    row_data_idiff = ['i_phase'] + [i_phase] + ['Vidiff']
                    row_data_qdiff = ['i_phase'] + [i_phase] + ['Vqdiff']
                    for q_phase in range(0,0x40):
                        self.eder.rx.bf.awv.wr(31, ant, (i_phase << 8) | q_phase)
                        self.eder.rx.set_beam(31)
                        measured_values = self.eder.rx.dco.iq_meas.meas()
                        measured_values_v_1_idiff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845)
                        measured_values_v_1_qdiff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845)
                        row_data_idiff = row_data_idiff + [measured_values_v_1_idiff]
                        row_data_qdiff = row_data_qdiff + [measured_values_v_1_qdiff]

                    writer_i.writerow(row_data_idiff)
                    writer_q.writerow(row_data_qdiff)
        log_file_i.close()
        log_file_q.close()

    def i_q_circle(self, ampl=1, start_angle=0):
        import math
        i=[]
        q=[]
        for angle_deg in range(start_angle, start_angle+360,4):
            angle = angle_deg * math.pi / 180
            i = i + [ampl*math.cos(angle)]
            q = q + [ampl*math.sin(angle)]
        return i,q


    def dco_single_ant_phase_sweep_0005(self, ant, file_name='dco_single_ant_phase_sweep_0005'):
        with open(file_name+'_ant_'+str(ant)+'.csv', 'ab') as log_file:
                writer = self.eder.csv.writer(log_file)
                #self.eder.regs.wr('trx_rx_on', 0x1f0000|(1<<ant))
                #self.eder.rx.bf.awv.wr(31, ant, 0x3f3f)
                import time
                time.sleep(30)
                self.eder.rx.dco.run()
                row_data_idiff = []
                row_data_qdiff = []
                header_0 = []
                header_1 = []
                i_coord, q_coord = self.i_q_circle(0.5)
                for index in range(0, len(q_coord)):
                    header_0 = header_0 + [int(i_coord[index]*31+31)]
                    header_1 = header_1 + [int(q_coord[index]*31+31)]
                writer.writerow(header_0)
                writer.writerow(header_1)
                writer.writerow([''])
                row_data_idiff = []
                row_data_qdiff = []
                for phase_index in range(0, len(i_coord)):
                    self.eder.rx.bf.awv.wr(31, ant, ( int((i_coord[phase_index]*31+31)) << 8) | int((q_coord[phase_index]*31+31)))
                    self.eder.rx.set_beam(31)
                    measured_values = self.eder.rx.dco.iq_meas.meas(num_samples=128)
                    measured_values_v_1_idiff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845)
                    measured_values_v_1_qdiff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845)
                    row_data_idiff = row_data_idiff + [measured_values_v_1_idiff]
                    row_data_qdiff = row_data_qdiff + [measured_values_v_1_qdiff]
                writer.writerow(row_data_idiff)
                writer.writerow(row_data_qdiff)
        log_file.close()

    def dco_all_ant_phase_sweep_0006(self, start_angle=0, file_name='dco_all_ant_phase_sweep_0006'):
        with open(file_name+'.csv', 'ab') as log_file:
                writer = self.eder.csv.writer(log_file)
                import time
                time.sleep(30)
                self.eder.rx.dco.run()
                row_data_idiff = []
                row_data_qdiff = []
                header_0 = []
                header_1 = []
                i_coord, q_coord = self.i_q_circle(1, start_angle)
                for index in range(0, len(q_coord)):
                    header_0 = header_0 + [int(i_coord[index]*31+31)]
                    header_1 = header_1 + [int(q_coord[index]*31+31)]
                writer.writerow(header_0)
                writer.writerow(header_1)
                writer.writerow([''])
                row_data_idiff = []
                row_data_qdiff = []
                for phase_index in range(0, len(i_coord)):
                    for ant in range(0,16):
                        self.eder.rx.bf.awv.wr(31, ant, ( int((i_coord[phase_index]*31+31)) << 8) | int((q_coord[phase_index]*31+31)))
                    self.eder.rx.set_beam(31)
                    measured_values = self.eder.rx.dco.iq_meas.meas(num_samples=128)
                    measured_values_v_1_idiff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845)
                    measured_values_v_1_qdiff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845)
                    row_data_idiff = row_data_idiff + [measured_values_v_1_idiff]
                    row_data_qdiff = row_data_qdiff + [measured_values_v_1_qdiff]
                writer.writerow(row_data_idiff)
                writer.writerow(row_data_qdiff)
        log_file.close()

    def dco_all_ant_phase_sweep_0007(self, ant, start_angle=0, file_name='dco_all_ant_phase_sweep_0007'):
        with open(file_name+'.csv', 'ab') as log_file:
                writer = self.eder.csv.writer(log_file)
                writer.writerow([''])
                writer.writerow([''])
                writer.writerow(['Element', ant])
                import time
                #self.set_phase(31, 0x1f, 0x1f)
                time.sleep(30)
                self.eder.rx.dco.run()
                row_data_idiff = []
                row_data_qdiff = []
                header_0 = []
                header_1 = []
                i_coord, q_coord = self.i_q_circle(1, start_angle)
                for index in range(0, len(q_coord)):
                    header_0 = header_0 + [int(i_coord[index]*31+31)]
                    header_1 = header_1 + [int(q_coord[index]*31+31)]
                writer.writerow(header_0)
                writer.writerow(header_1)
                writer.writerow([''])
                row_data_idiff = []
                row_data_qdiff = []
                for phase_index in range(0, len(i_coord)):
                    self.eder.rx.bf.awv.wr(31, ant, ( int((i_coord[phase_index]*31+31)) << 8) | int((q_coord[phase_index]*31+31)))
                    self.eder.rx.set_beam(31)
                    measured_values = self.eder.rx.dco.iq_meas.meas(num_samples=128)
                    measured_values_v_1_idiff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845)
                    measured_values_v_1_qdiff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845)
                    row_data_idiff = row_data_idiff + [measured_values_v_1_idiff]
                    row_data_qdiff = row_data_qdiff + [measured_values_v_1_qdiff]
                writer.writerow(row_data_idiff)
                writer.writerow(row_data_qdiff)
        log_file.close()

    def dco_one_ant_phase_sweep_0008(self, ant, start_angle=0, file_name='dco_one_ant_phase_sweep_0008'):
        with open(file_name+'.csv', 'ab') as log_file:
                writer = self.eder.csv.writer(log_file)
                writer.writerow([''])
                writer.writerow([''])
                writer.writerow(['Element', ant])
                import time
                self.set_phase(31, 0x1f, 0x1f)
                time.sleep(30)
                self.eder.rx.dco.run()
                measured_values = self.eder.rx.dco.iq_meas.meas(num_samples=128)
                initial_i_diff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845)
                #initial_i_diff = measured_values['idiff']
                initial_q_diff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845)
                #initial_q_diff = measured_values['qdiff']
                writer.writerow(['V i_diff', initial_i_diff])
                writer.writerow(['V q_diff', initial_q_diff])
                #writer.writerow(['ADC i_diff', initial_i_diff])
                #writer.writerow(['ADC q_diff', initial_q_diff])
                #self.eder.regs.wr('trx_rx_on', 0x1f0000|(1<<ant))
                row_data_idiff = []
                row_data_qdiff = []
                header_0 = []
                header_1 = []
                i_coord, q_coord = self.i_q_circle(1, start_angle)
                for index in range(0, len(q_coord)):
                    header_0 = header_0 + [int(i_coord[index]*31+31)]
                    header_1 = header_1 + [int(q_coord[index]*31+31)]
                writer.writerow(header_0)
                writer.writerow(header_1)
                writer.writerow([''])
                row_data_idiff = []
                row_data_qdiff = []
                for phase_index in range(0, len(i_coord)):
                #for phase_index in range(0, 100):
                    self.eder.rx.bf.awv.wr(31, ant, ( int((i_coord[phase_index]*31+31)) << 8) | int((q_coord[phase_index]*31+31)))
                    self.eder.rx.set_beam(31)
                    measured_values = self.eder.rx.dco.iq_meas.meas(num_samples=128)
                    measured_values_v_1_idiff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845) - initial_i_diff
                    #measured_values_v_1_idiff = measured_values['idiff']
                    measured_values_v_1_qdiff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845) - initial_q_diff
                    #measured_values_v_1_qdiff = measured_values['qdiff']
                    row_data_idiff = row_data_idiff + [measured_values_v_1_idiff]
                    row_data_qdiff = row_data_qdiff + [measured_values_v_1_qdiff]
                writer.writerow(row_data_idiff)
                writer.writerow(row_data_qdiff)
        log_file.close()

    def dco_one_ant_phase_sweep_0009(self, ant, start_angle=0, file_name='dco_one_ant_phase_sweep_0009'):
        with open(file_name+'.csv', 'ab') as log_file:
                writer = self.eder.csv.writer(log_file)
                writer.writerow([''])
                writer.writerow([''])
                writer.writerow(['Element', ant])
                import time
                self.set_phase(31, 0x1f, 0x1f)
                time.sleep(30)
                self.eder.rx.dco.run()
                measured_values = self.eder.rx.dco.iq_meas.meas(num_samples=128)
                initial_i_diff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845)
                initial_q_diff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845)
                writer.writerow(['V i_diff', initial_i_diff])
                writer.writerow(['V q_diff', initial_q_diff])
                #self.eder.regs.wr('trx_rx_on', 0x1f0000|(1<<ant))
                row_data_idiff = []
                row_data_qdiff = []
                header_0 = []
                header_1 = []
                i_coord, q_coord = self.i_q_circle(1, start_angle)
                for index in range(0, len(q_coord)):
                    header_0 = header_0 + [int(i_coord[index]*31+31)]
                    header_1 = header_1 + [int(q_coord[index]*31+31)]
                writer.writerow(header_0)
                writer.writerow(header_1)
                writer.writerow([''])
                row_data_idiff = []
                row_data_qdiff = []
                for phase_index in range(0, len(i_coord)):
                    self.eder.rx.bf.awv.wr(31, ant, ( int((i_coord[phase_index]*31+31)) << 8) | int((q_coord[phase_index]*31+31)))
                    self.eder.rx.set_beam(31)
                    measured_values = self.eder.rx.dco.iq_meas.meas(num_samples=128)
                    measured_values_v_1_idiff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845) - initial_i_diff
                    measured_values_v_1_qdiff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845) - initial_q_diff
                    row_data_idiff = row_data_idiff + [measured_values_v_1_idiff]
                    row_data_qdiff = row_data_qdiff + [measured_values_v_1_qdiff]
                writer.writerow(row_data_idiff)
                writer.writerow(row_data_qdiff)
        log_file.close()

    def dco_one_ant_phase_sweep_0010(self, ant, start_angle=0, file_name='dco_one_ant_phase_sweep_0010'):
        with open(file_name+'.csv', 'ab') as log_file:
                writer = self.eder.csv.writer(log_file)
                writer.writerow([''])
                writer.writerow([''])
                writer.writerow(['Element', ant])
                import time
                self.set_phase(31, 0x1f, 0x1f)
                time.sleep(30)
                self.eder.rx.dco.run()
                for count in range(0,6):
                    measured_values = self.eder.rx.dco.iq_meas.meas(num_samples=128)
                    #initial_i_diff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845)
                    initial_i_diff = measured_values['idiff']
                    #initial_q_diff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845)
                    initial_q_diff = measured_values['qdiff']
                    #writer.writerow(['V i_diff', initial_i_diff])
                    #writer.writerow(['V q_diff', initial_q_diff])
                    writer.writerow(['ADC i_diff', initial_i_diff])
                    writer.writerow(['ADC q_diff', initial_q_diff])
                #self.eder.regs.wr('trx_rx_on', 0x1f0000|(1<<ant))
                row_data_idiff = []
                row_data_qdiff = []
                header_0 = []
                header_1 = []
                i_coord, q_coord = self.i_q_circle(1, start_angle)
                for index in range(0, len(q_coord)):
                    header_0 = header_0 + [int(i_coord[index]*31+31)]
                    header_1 = header_1 + [int(q_coord[index]*31+31)]
                writer.writerow(header_0)
                writer.writerow(header_1)
                writer.writerow([''])
                row_data_idiff = []
                row_data_qdiff = []
                #for phase_index in range(0, len(i_coord)):
                for phase_index in range(0, 100):
                    #self.eder.rx.bf.awv.wr(31, ant, ( int((i_coord[phase_index]*31+31)) << 8) | int((q_coord[phase_index]*31+31)))
                    #self.eder.rx.set_beam(31)
                    measured_values = self.eder.rx.dco.iq_meas.meas(num_samples=128)
                    #measured_values_v_1_idiff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845) - initial_i_diff
                    measured_values_v_1_idiff = measured_values['idiff']
                    #measured_values_v_1_qdiff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845) - initial_q_diff
                    measured_values_v_1_qdiff = measured_values['qdiff']
                    row_data_idiff = row_data_idiff + [measured_values_v_1_idiff]
                    row_data_qdiff = row_data_qdiff + [measured_values_v_1_qdiff]
                writer.writerow(row_data_idiff)
                writer.writerow(row_data_qdiff)
        log_file.close()

    def dco_double_phase_sweep_0001(self, ant, file_name='dco_single_phase_sweep_0001.csv'):
        with open(file_name, 'ab') as log_file:
            writer = self.eder.csv.writer(log_file)
            writer.writerow(['Phase', 'i_diff(V)', 'q_diff(V)'])
            for phase in range(0,0x41):
                self.eder.rx.bf.awv.wr(31, ant, (phase << 8) | phase)
                self.eder.rx.set_beam(31)
                self.eder.regs.wr('trx_rx_on', 0x1fffff)
                measured_values = self.eder.rx.dco.iq_meas.meas()
                measured_values_v_1_idiff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845)
                measured_values_v_1_qdiff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845)
                writer.writerow([phase, measured_values_v_1_idiff, measured_values_v_1_qdiff])
        log_file.close()

    def set_phase(self, index, i_phase, q_phase):
        for ant in range(0,16):
            self.eder.rx.bf.awv.wr(index, ant, (i_phase << 8) | q_phase)
            self.eder.rx.set_beam(index)

    def read_adc_volt(self, src, num_samples=16):
        self.eder.adc.start(0x80|src, None, self.math.log(num_samples, 2))
        adc_val = self.eder.adc.mean()
        self.eder.adc.stop()
        return self.eder.rx.dco._decToVolt(adc_val)

    def set_ext_dco_dac(self, RDAC, data):
        if RDAC == 1 or RDAC == 2:
            import smbus
            bus = smbus.SMBus(1)
            SLAVE_ADDRESS = 0x20
            #SLAVE_ADDRESS = 0x22
            #SLAVE_ADDRESS = 0x23
            #SLAVE_ADDRESS = 0x28
            #SLAVE_ADDRESS = 0x2a
            #SLAVE_ADDRESS = 0x2b
            #SLAVE_ADDRESS = 0x2c
            #SLAVE_ADDRESS = 0x2e
            #SLAVE_ADDRESS = 0x2f

            DEVICE_CONTROL = 0x10
            command = DEVICE_CONTROL | RDAC

            bus.write_byte_data(slave_addr, command, data)
        else:
            print 'Incorrect RDAC. Should be 1 or 2'


    def ext_rdac_sweep(self, channel='iq', file_name='ext_rdac_sweep.csv'):
        try:
            import ederftdi
            if ederftdi.extdcodac() == 1:
                External_DCO_DAC_present = True
                print '  External DCO DAC found.'
            else:
                External_DCO_DAC_present = False
                print '  NO external DCO DAC found.'
        except:
            External_DCO_DAC_present = False
            print 'ederftdi import failed'

        if External_DCO_DAC_present == True:
            print '  RDAC sweep started'
            self.eder.regs.wr('rx_dco_en', 0)
            rx_gain_ctrl_bfrf = self.eder.regs.rd('rx_gain_ctrl_bfrf')
            rx_gain_ctrl_bb1 = self.eder.regs.rd('rx_gain_ctrl_bb1')
            rx_gain_ctrl_bb2 = self.eder.regs.rd('rx_gain_ctrl_bb2')
            rx_gain_ctrl_bb3 = self.eder.regs.rd('rx_gain_ctrl_bb3')

            self.eder.regs.wr('rx_gain_ctrl_bfrf', 0)
            self.eder.regs.wr('rx_gain_ctrl_bb1', 0)
            self.eder.regs.wr('rx_gain_ctrl_bb2', 0)
            self.eder.regs.wr('rx_gain_ctrl_bb3', 0)
            with open(file_name, 'ab') as log_file:
                writer = self.eder.csv.writer(log_file)
                writer.writerow(['RDAC', 'i_diff(V)', 'q_diff(V)'])
                import time
                rdac_i = 2
                rdac_q = 1
                for rdac_val in range(0, 0x100):
                    if channel == 'iq' or channel == 'i':
                        ederftdi.setdcodac(rdac_i, rdac_val)
                    if channel == 'iq' or channel == 'q':
                        ederftdi.setdcodac(rdac_q, rdac_val)
                    time.sleep(0.01)
                    measured_values = self.eder.rx.dco.iq_meas.meas()
                    measured_values_v_1_idiff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845)
                    measured_values_v_1_qdiff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845)
                    writer.writerow([rdac_val, measured_values_v_1_idiff, measured_values_v_1_qdiff])
            log_file.close()
            self.eder.regs.wr('rx_dco_en', 1)
            self.eder.regs.wr('rx_gain_ctrl_bfrf', rx_gain_ctrl_bfrf)
            self.eder.regs.wr('rx_gain_ctrl_bb1', rx_gain_ctrl_bb1)
            self.eder.regs.wr('rx_gain_ctrl_bb2', rx_gain_ctrl_bb2)
            self.eder.regs.wr('rx_gain_ctrl_bb3', rx_gain_ctrl_bb3)
            print '  RDAC sweep ended'


    def dco_step_meas(self, file_name='dco_step_meas.csv'):
        with open(file_name, 'ab') as log_file:
            writer = self.eder.csv.writer(log_file)
            writer.writerow(['mult', 'shift', 'rx_bb_dco_i/q', 'i_diff(V)', 'q_diff(V)'])
            import time
            for mult in range(0,4):
                for shift in range(0,3):
                    for rx_bb_dco in range(0, 0x80):
                        self.eder.regs.wr('rx_bb_i_dco', (mult<<12)|(shift<<8)|rx_bb_dco)
                        self.eder.regs.wr('rx_bb_q_dco', (mult<<12)|(shift<<8)|rx_bb_dco)
                        time.sleep(0.001)
                        measured_values = self.eder.rx.dco.iq_meas.meas()
                        measured_values_v_1_idiff = self.eder.rx.dco._decToVolt(measured_values['idiff'])/(-2.845)
                        measured_values_v_1_qdiff = self.eder.rx.dco._decToVolt(measured_values['qdiff'])/(-2.845)
                        writer.writerow([mult, shift, rx_bb_dco, measured_values_v_1_idiff, measured_values_v_1_qdiff])


