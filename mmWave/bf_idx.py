class Idx():
    import common
    
    RX = 0
    TX = 1
    
    def __init__(self, txrx):
        import memory
        import gpio
        import eder_logger
        self._txrx = txrx
        self.memory = memory.Memory()
        self.rpi = gpio.EderGpio()
        self.logger = eder_logger.EderLogger()

    def set(self, index):
        if index > 63:
            self.logger.log_error('Error: index should be between 0 and 63')
            return
        if self._txrx == self.RX:
            self.memory.idx.wr('bf_rx_awv_idx', index)
        elif self._txrx == self.TX:
            self.memory.idx.wr('bf_tx_awv_idx', index)

    def get(self):
        if self._txrx == self.RX:
            return self.memory.idx.rd('bf_rx_awv_idx')
        elif self._txrx == self.TX:
            return self.memory.idx.rd('bf_tx_awv_idx')

    def inc(self):
        self.rpi.gpio_o('BF_INC',1)
        self.rpi.gpio_o('BF_INC',0)

    def rtn(self):
        self.rpi.gpio_o('BF_RTN',1)
        self.rpi.gpio_o('BF_RTN',0)

    def rst(self):
        self.rpi.gpio_o('BF_RST',1)
        self.rpi.gpio_o('BF_RST',0)

    def _find_table(self, fname, tag):
        try:
            f = open(fname)
        except IOError:
            try:
                f = open('../'+fname)
            except IOError:
                self.logger.log_error(fname + ' not found!')
                return
        line = ''
        while line[0:len(tag)] != tag:
            line = f.readline()
            if line == '':
                break
        line = f.readline()
        table = ''
        while line[0:len('END_TABLE')] != 'END_TABLE':
            if line == '':
                break
            table += line
            line = f.readline()
        f.close()
        return table

    def setup(self, fname, freq):
        """ Write the beamforming index table for RX or TX.
        The tables are imported from specified CSV file.
        freq is the frequency in GHz.
        Example: write_bf_awv_idx('lut/beambook/bf_rx_awv_idx', 60.0)
        """
        freq = float(freq)
        freq = freq /1000000000
        table_tag = 'START_TABLE FREQ:' + '{:.2f}'.format(freq)
        table = self._find_table(fname, table_tag).replace('\r', '').replace('\n', ',').split(',')
        bf_awv_idx = []
        for element in table:
            if element != '':
                bf_awv_idx.append(int(element,16))

        if len(bf_awv_idx) < 64:
            self.logger.log_error('Too small BF IDX table: ' + str(len(bf_awv_idx)),2)
            return
        if len(bf_awv_idx) > 64:
            self.logger.log_error('Too large BF IDX table: ' + str(len(bf_awv_idx)),2)
            return
        
        intbfidxdata = self.common.intlist2int(bf_awv_idx)
        if self._txrx == self.RX:
            self.memory.idx.wr('bf_rx_awv_idx_table', intbfidxdata)
        elif self._txrx == self.TX:
            self.memory.idx.wr('bf_tx_awv_idx_table', intbfidxdata)

    def _get_element_addr(self, index):
        if index > 63:
            self.logger.log_error('Error: index or ant out of range')
            return -1
        if self._txrx == self.RX:
            addr = self.memory.idx.addr('bf_rx_awv_idx_table')
        elif self._txrx == self.TX:
            addr = self.memory.idx.addr('bf_tx_awv_idx_table')
        addr += index
        return addr

    def rd(self, index):
        """Prints and returns value at location [index,ant] in the AWV table
           Example: The following reads index 2 antenna 4 value in AWV table,
                    eder.rx.bf.read_awv_value(2, 4)
        """
        value = self.memory.idx.rd(self._get_element_addr(index),1)
        return value

    def wr(self, index, value):
        """Writes the specified value to AWV table at coordinates [index,ant]
           Example: The following write value 0xabab to index 2 antenna 4 in
                    the AWV table,
                    eder.rx.bf.write_awv_value(2, 4, 0xabab) 
        """
        self.memory.idx.wr(self._get_element_addr(index), value,1)

    def dump(self, do_print=True):
        """
        """
        if self._txrx == self.RX:
            values = self.memory.idx.rd('bf_rx_awv_idx_table')
        elif self._txrx == self.TX:
            values = self.memory.idx.rd('bf_tx_awv_idx_table')
        else:
            values = None
        if do_print:
            self.logger.log_info("Idx  AWV_Ptr")
            self.logger.log_info("------------")
            for row in xrange(0,64):
                row_val = (values>>((63-row)*8))&0xff
                self.logger.log_info('{:{}}'.format(row,2) + '    {:{}}'.format(int(row_val),2))
                #print '{:{}}'.format(row,2),'    {:{}}'.format(int(row_val),2)
            self.logger.log_info("------------")
            self.logger.log_info("Idx RTN/RST Value: " + str(self.get()))
        else:
            return values
