class Bf():
    import common
    
    RX = 0
    TX = 1
    
    def __init__(self, txrx):
        import memory
        import bf_awv
        import bf_idx
        import eder_logger
        self._txrx = txrx
        self.awv = bf_awv.Awv(txrx)
        self.idx = bf_idx.Idx(txrx)
        self.logger = eder_logger.EderLogger()

    def dump(self, do_print=True):
        """
        """
        awv_tbl = self.awv.dump(do_print=False)
        idx_tbl = self.idx.dump(do_print=False)
        if do_print:
            self.logger.log_info("--------------------------------------------------------------------------------------------------------------------------------")
            self.logger.log_info("  Idx Table  |                                                    AWV_Table                                                    |")
            self.logger.log_info("Idx  AWV_Ptr |   0      1      2      3      4      5      6      7      8      9      10     11     12     13     14     15   |")
            self.logger.log_info("--------------------------------------------------------------------------------------------------------------------------------")
            for row in xrange(0,64):
                idx_val = (idx_tbl>>((63-row)*8))&0xff
                row_string = str('{:{}}'.format(row,2)+'    {:{}}     |'.format(int(idx_val),2))
                awv_row_val = (awv_tbl>>((63-idx_val)*16*16))&(2**(16*16)-1)
                for col in xrange(0,16):
                    awv_col_val = (awv_row_val>>((15-col)*16))&0xffff
                    row_string += ' 0x{:0{}X}'.format(int(awv_col_val),4)
                row_string += ' |'
                self.logger.log_info(row_string)
            self.logger.log_info("--------------------------------------------------------------------------------------------------------------------------------")
            self.logger.log_info("Direct AWV_Ptr   : " + str(self.awv.get()&0x3f))
            self.logger.log_info("Idx RTN/RST Value: " + str(self.idx.get()))
        else:
            return {'awv':awv_tbl, 'idx':idx_tbl}
