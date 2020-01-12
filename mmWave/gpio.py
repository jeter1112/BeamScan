#!/usr/bin/python

import sys, time

class EderGpio(object):

    __instance = None

    try:
        import ederftdi
    except ImportError, e:
        pass

    EVALD0 = {
        'I2C_SDA'    : 3,
        'I2C_SCL'    : 5,
        #
        'AGC_CLK'    : 7,
        'AGC_IRQ'    : 8,
        'AGC_CMD0'   : 10,
        'AGC_CMD1'   : 12,
        'AGC_CMD2'   : 16,
        'AGC_GAIN_6' : 37,
        'AGC_GAIN_5' : 35,
        'AGC_GAIN_4' : 33,
        'AGC_GAIN_3' : 31,
        'AGC_GAIN_2' : 29,
        'AGC_GAIN_1' : 27,
        'AGC_GAIN_0' : 25,
        #
        'RST_N'      : 11,
        'TX_RX_SW'   : 13,
        'TST_EN'     : 15,
        #
        'SPI_MOSI'   : 19,
        'SPI_MISO'   : 21,
        'SPI_CLK'    : 23,
        'SPI_CS_N'   : 24,
        #
        'BF_INC'     : 18,
        'BF_RTN'     : 22,
        'BF_RST'     : 36
        }

    EVALDX = {
        'I2C_SDA'    : 3,
        'I2C_SCL'    : 5,
        #
        'AGC_IRQ'    : 8,
        'AGC_START'  : 12,
        'AGC_RST'    : 16,
        'AGC_GAIN_6' : 37,
        'AGC_GAIN_5' : 35,
        'AGC_GAIN_4' : 33,
        'AGC_GAIN_3' : 31,
        'AGC_GAIN_2' : 29,
        'AGC_GAIN_1' : 27,
        'AGC_GAIN_0' : 25,
        #
        'RST_N'      : 18,
        'TX_RX_SW'   : 36,
        'TST_EN'     : 15,
        #
        'SPI_MOSI'   : 19,
        'SPI_MISO'   : 21,
        'SPI_CLK'    : 23,
        'SPI_CS_N'   : 24,
        #
        'BF_INC'     : 13,
        'BF_RTN'     : 15,
        'BF_RST'     : 36
        }

    MB1 = {
        'I2C_SDA'    : 100,
        'I2C_SCL'    : 101,
        #
        'AGC_IRQ'    : 7,
        'AGC_START'  : 102,
        'AGC_RST'    : 109,
        'AGC_GAIN_6' : 6,
        'AGC_GAIN_5' : 5,
        'AGC_GAIN_4' : 4,
        'AGC_GAIN_3' : 3,
        'AGC_GAIN_2' : 2,
        'AGC_GAIN_1' : 1,
        'AGC_GAIN_0' : 0,
        #
        'RST_N'      : 103,
        'TX_RX_SW'   : 12,
        'TST_EN'     : 104,
        #
        'SPI_MOSI'   : 105,
        'SPI_MISO'   : 106,
        'SPI_CLK'    : 107,
        'SPI_CS_N'   : 108,
        #
        'BF_INC'     : 14,
        'BF_RTN'     : 13,
        'BF_RST'     : 15
        }

    ALL = 255

    def __new__(cls, board_type='Unspecified'):
        if cls.__instance is None:
            cls.__instance = super(EderGpio, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self, board_type='Unspecified'):
        if self.__initialized:
            return
        self.__initialized = True
        self.board_type = board_type
        if self.board_type == 'MB0':
            import RPi.GPIO as GPIO
            self.GPIO = GPIO
            self.hi_lo = {
                    1 : self.GPIO.HIGH,
                    0 : self.GPIO.LOW,
                    self.GPIO.HIGH : self.GPIO.HIGH,
                    self.GPIO.LOW : self.GPIO.LOW,
                    'high' : self.GPIO.HIGH,
                    'low' : self.GPIO.LOW        
                    }
            self.GPIO.setwarnings(False)
            self.GPIO.setmode(self.GPIO.BOARD)
            self.evald=self.EVALD0
        elif self.board_type == 'MB1':
            self.evald=self.MB1


    def gpio_o(self, gpio_name, oval):
        if self.board_type == 'MB0':
            self.GPIO.setup(self.evald[gpio_name], self.GPIO.OUT)
            self.GPIO.output(self.evald[gpio_name], self.hi_lo[oval])
            return self.GPIO.input(self.evald[gpio_name])
        elif self.board_type == 'MB1':
            if self.evald[gpio_name] > 7:
                gpio_value = self.ederftdi.getgpio2()
                if oval == 1:
                    mask = (1 << self.evald[gpio_name]-8)
                    gpio_value = gpio_value | mask
                elif oval == 0:
                    mask = ~(1 << self.evald[gpio_name]-8)
                    gpio_value = gpio_value & mask
                self.ederftdi.setgpio2(gpio_value)
            else:
                gpio_value = self.ederftdi.getgpio1()
                if oval == 1:
                    mask = (1 << self.evald[gpio_name])
                    gpio_value = gpio_value | mask
                elif oval == 0:
                    mask = ~(1 << self.evald[gpio_name])
                    gpio_value = gpio_value & mask
                self.ederftdi.setgpio1(gpio_value)

    def gpio_i(self, gpio_name):
        if self.board_type == 'MB0':
            self.GPIO.setup(self.evald[gpio_name], self.GPIO.IN)
            return self.GPIO.input(self.evald[gpio_name])
        #***** TODO: Implement for MB1 ******
        return 0

    def set_tx_mode(self):
        if self.board_type == 'MB0':
            self.gpio_o('TX_RX_SW', 1)
        elif self.board_type == 'MB1':
            self.ederftdi.settxrxsw(1)

    def set_rx_mode(self):
        if self.board_type == 'MB0':
            self.gpio_o('TX_RX_SW', 0)
        elif self.board_type == 'MB1':
            self.ederftdi.settxrxsw(0)

    def trx_mode_disable(self):
        if self.board_type == 'MB0':
            self.gpio_i('TX_RX_SW')


    def reset(self, rst_time_in_ms=1):
        if self.board_type == 'MB0':
            self.gpio_o('RST_N', 0)
            time.sleep(0.001*rst_time_in_ms)
            self.gpio_o('RST_N', 1)
            self.gpio_i('RST_N')
        elif self.board_type == 'MB1':
            self.ederftdi.setrstn(0)
            time.sleep(0.001*rst_time_in_ms)
            self.ederftdi.setrstn(1)

    def agc_gain(self, index):
	index = index & 0x3F
	self.gpio_o('AGC_CLK', 0)
        self.gpio_o('AGC_CMD2', (index >> 5) & 1)
        self.gpio_o('AGC_CMD1', (index >> 4) & 1)
        self.gpio_o('AGC_CMD0', (index >> 3) & 1)
        self.gpio_o('AGC_CLK', 1)
        self.gpio_o('AGC_CMD2', (index >> 2) & 1)
        self.gpio_o('AGC_CMD1', (index >> 1) & 1)
        self.gpio_o('AGC_CMD0', (index >> 0) & 1)
        self.gpio_o('AGC_CLK', 0)

