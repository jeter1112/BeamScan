class EderStatus(object):

    IDLE_MODE  = 0
    SX_MODE    = 1
    RX_MODE    = 2
    TX_MODE    = 3
    ADC_INIT   = (1 << 8)
    AGC_INIT   = (1 << 9)
    PLL_INIT   = (1 << 10)
    REF_INIT   = (1 << 11)
    TEMP_INIT  = (1 << 12)
    VCO_INIT   = (1 << 13)
    RXDCO_INIT = (1 << 14)
    RX_INIT    = (1 << 15)
    TX_INIT    = (1 << 16)
    OTP_INIT   = (1 << 17)

    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(EderStatus, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance
    
    def __init__(self):
        if self.__initialized:
            return
        import register
        self.__initialized = True
        self.regs = register.Register()
        self._read_status()

    def _read_status(self):
        self.regs.wr('chip_id_sw_en', 1)
        self.status = self.regs.rd('chip_id')
        self.regs.wr('chip_id_sw_en', 0)

    def _write_status(self):
        self.regs.wr('chip_id_sw_en', 1)
        self.regs.wr('chip_id', self.status)
        self.regs.wr('chip_id_sw_en', 0)

    def set_init_bit(self, init_bit):
        self.status |= init_bit
        self._write_status()

    def clr_init_bit(self, init_bit):
        self.status &= (~init_bit)
        self._write_status()

    def init_bit_is_set(self, init_bit):
        return ((self.status & init_bit) != 0)

    def set_mode(self, mode):
        self.status &= 0xffffff00
        self.status |=  mode
        self._write_status()

    def get_mode(self):
        txrx_hw_sw = self.regs.rd('trx_ctrl') & 0x10
        if txrx_hw_sw > 0:
            tx_rx_sw_gpio = self.regs.rd('gpio_tx_rx_sw_ctrl') & 0x10
            if tx_rx_sw_gpio == 0:
                set_mode(self.RX_MODE)
            else:
                set_mode(self.TX_MODE)
        return (self.status & 0xff)

    def get_status(self):
        return (self.status >> 8)
