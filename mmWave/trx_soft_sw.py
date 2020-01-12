class TrxSoftSw(object):
    
    import common

    trx_soft_rx_on_enables = [0,0,0,0,0,0,0,0]
    trx_soft_tx_on_enables = [0,0,0,0,0,0,0,0]

    def __init__(self):
        import register
        self.regs = register.Register()
        
    def init(self, max_state, delay):
        self.regs.wr('trx_soft_delay', delay)
        self.regs.wr('trx_soft_max_state', max_state)
        self.regs.wr('trx_soft_tx_on_enables', self.common.intlist2int(trx_soft_tx_on_enables))
        self.regs.wr('trx_soft_rx_on_enables', self.common.intlist2int(trx_soft_rx_on_enables))
        self.regs.wr('trx_soft_bf_on_grp_sel', 0x00000000)
        
    def enable(self, txrx_soft_sw):
        if txrx_soft_sw == 'rx':
            self.regs.set('trx_soft_ctrl', 1)
        elif txrx_soft_sw == 'tx':
            self.regs.set('trx_soft_ctrl', 2)
        elif txrx_soft_sw == 'txrx':
            self.regs.set('trx_soft_ctrl', 3)
        
    def disable(self, txrx_soft_sw):
        if txrx_soft_sw == 'rx':
            self.regs.clr('trx_soft_ctrl', 1)
        elif txrx_soft_sw == 'tx':
            self.regs.clr('trx_soft_ctrl', 2)
        elif txrx_soft_sw == 'txrx':
            self.regs.clr('trx_soft_ctrl', 3)
