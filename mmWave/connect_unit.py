    #
def connect_unit(self, device_role):
    if device_role != 'tester' and device_role != 'dut':
        print 'device should be ''dut'' or ''tester'' '
        return
    self.regs.o_spi.close()
    if device_role == 'tester':
        self.regs.o_spi.open(0,1)
    elif device_role == 'dut':
        self.regs.o_spi.open(0,0)
    self.regs.o_spi.max_speed_hz  = 10000000
    self.regs.o_spi.cshigh        = False
    self.regs.o_spi.loop          = False
    self.regs.o_spi.lsbfirst      = False
    self.regs.o_spi.no_cs         = False
    self.regs.o_spi.threewire     = False
    self.regs.o_spi.bits_per_word = 8
    self.regs.o_spi.mode          = 0 