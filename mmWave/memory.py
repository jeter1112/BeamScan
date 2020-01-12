import ederspi

class Memory(object):

    __instance = None

    idx_awv = {
        'bf_tx_awv_idx_table':   {'group':'bf_tx', 'addr':0x0100, 'size':64, 'value':0x00},
        'bf_tx_awv_idx':         {'group':'bf_tx', 'addr':0x0140, 'size':1,  'value':0x00},
        'bf_tx_awv_ce':          {'group':'bf_tx', 'addr':0x0141, 'size':1,  'value':0x00},
        'bf_tx_cfg':             {'group':'bf_tx', 'addr':0x0143, 'size':1,  'value':0x01},
        #
        'bf_rx_awv_idx_table':   {'group':'bf_rx', 'addr':0x0160, 'size':64, 'value':0x00},
        'bf_rx_awv_idx':         {'group':'bf_rx', 'addr':0x01A0, 'size':1,  'value':0x00},
        'bf_rx_awv_ce':          {'group':'bf_rx', 'addr':0x01A1, 'size':1,  'value':0x00},
        'bf_rx_cfg':             {'group':'bf_rx', 'addr':0x01A3, 'size':1,  'value':0x01},
    }
    mbist_awv = {
        'bf_tx_mbist_0_pat':     {'group':'bf_tx', 'addr':0x0144, 'size':2, 'value':0x5555},
        'bf_tx_mbist_1_pat':     {'group':'bf_tx', 'addr':0x0146, 'size':2, 'value':0xaaaa},
        'bf_tx_mbist_2p_sel':    {'group':'bf_tx', 'addr':0x0149, 'size':1, 'value':0x00},
        'bf_tx_mbist_en':        {'group':'bf_tx', 'addr':0x014a, 'size':2, 'value':0x0000},
        'bf_tx_mbist_result':    {'group':'bf_tx', 'addr':0x014c, 'size':2, 'value':0x0000},
        'bf_tx_mbist_done':      {'group':'bf_tx', 'addr':0x014e, 'size':2, 'value':0x0000},
        #
        'bf_rx_mbist_0_pat':     {'group':'bf_rx', 'addr':0x01A4, 'size':2, 'value':0x5555},
        'bf_rx_mbist_1_pat':     {'group':'bf_rx', 'addr':0x01A6, 'size':2, 'value':0xaaaa},
        'bf_rx_mbist_2p_sel':    {'group':'bf_rx', 'addr':0x01A9, 'size':1, 'value':0x00},
        'bf_rx_mbist_en':        {'group':'bf_rx', 'addr':0x01Aa, 'size':2, 'value':0x0000},
        'bf_rx_mbist_result':    {'group':'bf_rx', 'addr':0x01Ac, 'size':2, 'value':0x0000},
        'bf_rx_mbist_done':      {'group':'bf_rx', 'addr':0x01Ae, 'size':2, 'value':0x0000},
    }

    tbls_awv = {
        'bf_tx_awv_ptr':         {'group':'bf_tx', 'addr':0x0142, 'size':1,  'value':0x00},
        'bf_rx_awv_ptr':         {'group':'bf_rx', 'addr':0x01A2, 'size':1,  'value':0x00},
        'bf_tx_awv':             {'group':'bf_tx', 'addr':0x0800, 'size':64*32, 'value':0x0000},
        'bf_rx_awv':             {'group':'bf_rx', 'addr':0x1000, 'size':64*32, 'value':0x0000},
    }

    def __new__(cls, board_type='MB1'):
        if cls.__instance is None:
            cls.__instance = super(Memory, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self, board_type='MB1'):
        if self.__initialized:
            return
        self.__initialized = True
        self.idx   = ederspi.EderSpi(self.idx_awv, board_type)
        self.awv   = ederspi.EderSpi(self.tbls_awv, board_type)
        self.mbist = ederspi.EderSpi(self.mbist_awv, board_type)

    def clear(self,mem_name):
        self.awv.wr(mem_name,0)

