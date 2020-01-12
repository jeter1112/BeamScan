import spidev

eder = 0x00

class Spi(spidev.SpiDev):
    def __init__(self, unit):
        self.open(0, 0)        
        self.max_speed_hz  = 10000000
        if unit == eder:
            self.cshigh        = False
            self.loop          = False
            self.lsbfirst      = False
            self.no_cs         = False
            self.threewire     = False
            self.bits_per_word = 8
            self.mode          = 0
