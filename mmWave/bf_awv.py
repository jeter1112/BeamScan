class Awv():
    import common
    
    RX = 0
    TX = 1
    
    def __init__(self, txrx):
        import memory
        import eder_logger
        self._txrx = txrx
        self.memory = memory.Memory()
        self.logger = eder_logger.EderLogger()

    def set(self, index):
        if index > 63:
            self.logger.log_info('Error: index should be between 0 and 63')
            return
        ptr = 0x80 | index
        if self._txrx == self.RX:
            self.memory.awv.wr('bf_rx_awv_ptr', ptr)
        elif self._txrx == self.TX:
            self.memory.awv.wr('bf_tx_awv_ptr', ptr)

    def get(self):
        if self._txrx == self.RX:
            return self.memory.awv.rd('bf_rx_awv_ptr')
        elif self._txrx == self.TX:
            return self.memory.awv.rd('bf_tx_awv_ptr')

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

    def pack_bytes_2_bf_awv(self, i, q):
        pack = lambda i , q : ( ((i & 0x3f) << 6) + (q & 0x3f) )
        return pack(i,q)

    def unpack_bf_awv_2_bytes(self, data):
        return (data >> 6)&0x3f, (data & 0x3f)

    def unpack_bf_awv_2_word(self, data):
        (i,q) = self.unpack_bf_awv_2_bytes(data)
        return (i<<8) + q

    def setup(self, fname, freq, temp):
        """ Write the beamforming table values for RX or TX.
        The tables are imported from specified CSV file.
        freq is frequency in Hz. temp is temperature in Celcius.
        Example: eder.tx.bf.awv.setup('lut/beambook/bf_rx_awv', 60000000000, 25.0)
        """
        freq = float(freq)
        freq = freq / 1000000000
        temp = float(temp)
        if self._txrx != self.RX and self._txrx != self.TX:
            # Wrong parameter value
            self.logger.log_error("First parameter should be RX or TX")
            return
        bf_awv = []
        table_tag = 'START_TABLE FREQ:' + '{:.2f}'.format(freq) + ' TEMP:' + str(temp)
        content = self._find_table(fname, table_tag)
        if content is None:
            self.logger.log_error('Error: File not found.')
            return
        content = content.replace('\r', '').replace('\n', ',').split(',')
        for element in content:
            if element != '' and element != 'X':
                bf_awv.append(int(element,16))

        if len(bf_awv) < 64*16:
            self.logger.log_error('wrong matrix dimensions')
            return

        packed_bf_awv = []
        #pack_bf_awv = lambda x , y : (x << 6) + y
        for index in xrange(0,len(bf_awv)/2):
            packed_bf_awv.append(self.pack_bytes_2_bf_awv(bf_awv[index*2], bf_awv[index*2+1]))
        intbfdata = self.common.intlist2int(packed_bf_awv,0x10000)
        if self._txrx == self.RX:
            self.memory.awv.wr('bf_rx_awv', intbfdata)
        elif self._txrx == self.TX:
            self.memory.awv.wr('bf_tx_awv', intbfdata)

    def _get_element_addr(self, index, ant):
        if index > 63 or ant > 15:
            self.logger.log_error('Error: index or ant out of range')
            return -1
        if self._txrx == self.RX:
            addr = self.memory.awv.addr('bf_rx_awv')
        elif self._txrx == self.TX:
            addr = self.memory.awv.addr('bf_tx_awv')
        addr += (index*32 + ant*2)
        return addr

    def rd(self, index, ant):
        """Prints and returns value at location [index,ant] in the AWV table
           Example: The following reads index 2 antenna 4 value in AWV table,
                    eder.rx.bf.read_awv_value(2, 4)
        """
        value = self.unpack_bf_awv_2_word(self.memory.awv.rd(self._get_element_addr(index, ant), 2))
        return value

    def wr(self, index, ant, value):
        """Writes the specified value to AWV table at coordinates [index,ant]
           Example: The following write value 0xabab to index 2 antenna 4 in
                    the AWV table,
                    eder.rx.bf.write_awv_value(2, 4, 0xabab) 
        """
        self.memory.awv.wr(self._get_element_addr(index, ant), self.pack_bytes_2_bf_awv((value&0x3F00)>>8, value&0x003F), 2)

    def dump(self, do_print=True):
        """
        """
        if self._txrx == self.RX:
            values = self.memory.awv.rd('bf_rx_awv')
        elif self._txrx == self.TX:
            values = self.memory.awv.rd('bf_tx_awv')
        else:
            values = None
        if do_print:
            self.logger.log_info("             -------------------------------------------------------------------------------------------------------------------")
            self.logger.log_info("             |                                                    AWV_Table                                                    |")
            self.logger.log_info("     AWV_Ptr |   0      1      2      3      4      5      6      7      8      9      10     11     12     13     14     15   |")
            self.logger.log_info("--------------------------------------------------------------------------------------------------------------------------------")
            for row in xrange(0,64):
                row_string = '       {:{}}    |'.format(row,2)
                row_val = (values>>((63-row)*16*16))&(2**(16*16)-1)
                for col in xrange(0,16):
                    col_val = self.unpack_bf_awv_2_word((row_val>>((15-col)*16))&0xffff)
                    row_string += ' 0x{:0{}X}'.format(int(col_val),4)
                row_string += ' |'
                self.logger.log_info(row_string)
            self.logger.log_info("--------------------------------------------------------------------------------------------------------------------------------")
            self.logger.log_info("Direct AWV_Ptr : " + str(self.get()&0x3f))
        else:
            return values


    def rd_raw(self, index, ant):
        """Prints and returns value at location [index,ant] in the AWV table
           Example: The following reads index 2 antenna 4 value in AWV table,
                    eder.rx.bf.read_awv_value(2, 4)
        """
        value = self.memory.awv.rd(self._get_element_addr(index, ant), 2)
        return value

    def wr_raw(self, index, ant, value):
        """Writes the specified value to AWV table at coordinates [index,ant]
           Example: The following write value 0xabab to index 2 antenna 4 in
                    the AWV table,
                    eder.rx.bf.write_awv_value(2, 4, 0xabab) 
        """
        self.memory.awv.wr(self._get_element_addr(index, ant), value, 2)

    def dump_raw(self, do_print=True):
        """
        """
        if self._txrx == self.RX:
            values = self.memory.awv.rd('bf_rx_awv')
        elif self._txrx == self.TX:
            values = self.memory.awv.rd('bf_tx_awv')
        else:
            values = None
        if do_print:
            self.logger.log_info("             -------------------------------------------------------------------------------------------------------------------")
            self.logger.log_info("             |                                                    AWV_Table                                                    |")
            self.logger.log_info("     AWV_Ptr |   0      1      2      3      4      5      6      7      8      9      10     11     12     13     14     15   |")
            self.logger.log_info("--------------------------------------------------------------------------------------------------------------------------------")
            for row in xrange(0,64):
                row_string = '       {:{}}    |'.format(row,2)
                row_val = (values>>((63-row)*16*16))&(2**(16*16)-1)
                for col in xrange(0,16):
                    col_val = (row_val>>((15-col)*16))&0xffff
                    row_string += ' 0x{:0{}X}'.format(int(col_val),4)
                row_string += ' |'
                self.logger.log_info(row_string)
            self.logger.log_info("--------------------------------------------------------------------------------------------------------------------------------")
            self.logger.log_info("Direct AWV_Ptr : " + str(self.get()))
        else:
            return values
