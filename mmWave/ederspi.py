from common import *

class EderSpi:
    import math

    SPI_WR_RAW  = 0
    SPI_WR_CLR  = 1
    SPI_WR_NAND = 1
    SPI_WR_SET  = 2
    SPI_WR_OR   = 2
    SPI_WR_TGL  = 3
    SPI_WR_XOR  = 3
    SPI_RD      = 4

    RX_MODE   = 0
    TX_MODE   = 1
    TXRX_MODE = 2

    def __init__(self, regs, board_type='MB1'):
        self.board_type = board_type
        if self.board_type == 'MB0':
            try:
                import spi
                self.spi = spi
                self.o_spi  = self.spi.Spi(self.spi.eder)
            except ImportError, e:
                print 'spi module NOT installed.'
                print 'spi module MUST be installed for MB0.'
        elif self.board_type == 'MB1':
            try:
                import ederftdi
                self.ederftdi = ederftdi
            except ImportError, e:
                print 'ederftdi module NOT installed.'
                print 'ederftdi module MUST be installed for MB1.'
        self.regs = regs
        self.reg_groups = {}
        for reg_name in sorted(regs):
            if self.group(reg_name) in self.reg_groups:
                self.reg_groups[self.group(reg_name)].append(reg_name)
            else:
                self.reg_groups[self.group(reg_name)]=[reg_name]

    def groups(self):
        """Return all available groups"""
        return sorted(self.reg_groups)

    def group(self, reg_name):
        """Return group for symbolic address"""
        return self.regs[reg_name]['group']

    def addr(self, reg_name):
        """Return decimal address for symbolic address"""
        return self.regs[reg_name]['addr']

    def size(self, reg_name):
        """Return size of symbolic address"""
        return self.regs[reg_name]['size']

    def value(self, reg_name):
        """Return default value for symbolic address"""
        return self.regs[reg_name]['value']

    def mask(self, reg_name):
        """Return mask for symbolic address"""
        return self.regs[reg_name]['mask']

    def name(self, addr):
        reg_name  = None
        for key,reg in self.regs.iteritems():
            if (reg['addr'] <= addr) and (reg['addr']+reg['size'] > addr):
                reg_name  = key
        return reg_name

    def addr_and_size(self, reg_name_or_addr, bsize=None):
        if isinstance(reg_name_or_addr,int):
            address = reg_name_or_addr
            if bsize is None:
                bsize = self.size(self.name(address))
        else:
            address = self.addr(reg_name_or_addr)
            if bsize is None:
                bsize = self.size(reg_name_or_addr)
        return address,bsize

    def rd(self, reg_name_or_addr, bsize=None, lst=0, debug=0):
        """Read contents of register 'reg_name_or_addr' and return as integer.
           Example: rd('chip_id')
        """
        address,bsize = self.addr_and_size(reg_name_or_addr,bsize)
        command       = int2intlist((address << 3) + self.SPI_RD,256,2)
        
        data    = bsize * [0x00]
        if (debug == 1):
            print command + data
        if (lst != 0):
            num_ints = int(ceil(bsize/lst))
            if self.board_type == 'MB1':
                try:
                    answer   = intlist2intlist(self.ederftdi.xfer(command + data),256**lst,num_ints,256)
                except:
                    print '  SPI read error.'
                    answer = 0
            elif self.board_type == 'MB0':
                answer   = intlist2intlist(self.o_spi.xfer(command + data)[2:],256**lst,num_ints,256)
        else:
            if self.board_type == 'MB1':
                try:
                    answer  = intlist2int(self.ederftdi.xfer(command + data))
                except:
                    print '  SPI read error.'
                    answer = 0
            elif self.board_type == 'MB0':
                answer  = intlist2int(self.o_spi.xfer(command + data)[2:])

        return answer

    def rd_str(self, reg_name_or_addr):
        if isinstance(reg_name_or_addr,int):
            reg_name_or_addr = self.name(reg_name_or_addr)
        width = 2 * self.size(reg_name_or_addr)
        data  = self.rd(reg_name_or_addr)
        return '0x{:0{}X}'.format(data, width)
    
    def wr(self, reg_name_or_addr, data, bsize=None, wr_mode = SPI_WR_RAW, lst=0, debug=0):
        """Write new contents to register 'addr' and return old contents
           as integer. Register name or address can be given as memory destination.
           Example: wr('chip_id',0x01020304)
                    wr(0x0160, 0x01020304)
        """

        address,bsize = self.addr_and_size(reg_name_or_addr,bsize)
        command       = int2intlist((address << 3) + wr_mode,256,2)
        if self.board_type == 'MB1':
            answer = self.rd(address, bsize)
        
        if (debug == 1):
            print command + int2intlist(data,256,bsize) + int2intlist(0x00,256,1)
        if (lst != 0):
            num_ints = int(ceil(bsize/lst))
            if self.board_type == 'MB1':
                intlist2intlist(self.ederftdi.xfer(command + int2intlist(data,256,bsize) + int2intlist(0x00,256,1))[2:2+bsize],256**lst,num_ints,256)
            elif self.board_type == 'MB0':
                answer   = intlist2intlist(self.o_spi.xfer(command + int2intlist(data,256,bsize) + int2intlist(0x00,256,1))[2:2+bsize],256**lst,num_ints,256)
        else:
            if self.board_type == 'MB1':
                self.ederftdi.xfer(command + int2intlist(data,256,bsize) + int2intlist(0x00,256,1))
            elif self.board_type == 'MB0':
                answer = intlist2int(self.o_spi.xfer(command + int2intlist(data,256,bsize) + int2intlist(0x00,256,1))[2:2+bsize])
            
        return answer

    def wrrd(self, reg_name_or_addr, data, bsize=None, wr_mode = SPI_WR_RAW):
        """Write new contents to register at 'addr' and then read the same register.
           Returns a string looking like: '<old contents> -> <new contents>'.
           Example: wrrd('chip_id',0x01020304)
        """
        address,bsize = self.addr_and_size(reg_name_or_addr,bsize)

        return fhex(self.wr(reg_name_or_addr, data, bsize, wr_mode), 2 * bsize) + " -> " + fhex(self.rd(reg_name_or_addr,bsize), 2 * bsize)

    def tgl(self, reg_name_or_addr, data, bsize=None):
        """Toggle value of indicated bits of register 'reg_name_or_addr'.
           Example: tgl('chip_id',0x01)
        """
        return self.wr(reg_name_or_addr, data, bsize, self.SPI_WR_TGL)

    def clr(self, reg_name_or_addr, data, bsize=None):
        """Clear indicated bits of register 'reg_name_or_addr'.
           Example: clr('chip_id',0x01)
        """
        return self.wr(reg_name_or_addr, data, bsize, self.SPI_WR_CLR)

    def set(self, reg_name_or_addr, data, bsize=None):
        """Set indicated bits of register 'reg_name_or_addr'.
           Example: set('chip_id',0x01)
        """
        return self.wr(reg_name_or_addr, data, bsize, self.SPI_WR_SET)

    def dump(self, group=None, do_print=True):
        """List all available registers and their contents"""
        res = {}
        groups = self.reg_groups
        if isinstance(group,str):
            if group in groups:
                groups={}
                groups[group] = self.reg_groups[group]
            else:
                print "Group does not exist!"
                return
        for group_name in sorted(groups):
            if do_print:
                print group_name
            regs = groups[group_name]
            for reg_name in sorted(regs):
                data = self.rd(reg_name)
                width = 2 * self.size(reg_name)
                if do_print:
                    print '  {:<25}: {:>18}'.format(reg_name,'0x{:0{}X}'.format(data, width))
                res[reg_name] = {'value': data}

        if not do_print:
            return res

    def dump_wr(self, group=None, do_print=True):
        """List all available registers and their contents"""
        res = {}
        do_write = False
        regs = self.regs
        if isinstance(group,dict):
            regs = group
            do_print = True
            do_write = True
        if isinstance(group,str):
            groups = self.reg_groups[group]
        for reg_name in sorted(regs):
            if do_write:
                self.wr(reg_name, regs[reg_name]['value'])
            data = self.rd(reg_name)
            width = 2 * self.size(reg_name)
            if do_print:
                print '{:<25}: {:>18}'.format(reg_name,'0x{:0{}X}'.format(data, width))
            res[reg_name] = {'value': data}
        if not do_print:
            return res

    def verify(self, ref = None, do_print = False):
        """Verify that registers contain specified values"""
        res   = True
        if (ref == None) or (ref == 'default'):
            ref = self.regs
        for reg_name in sorted(self.regs):
            width = 2 * self.size(reg_name)
            data  = self.rd(reg_name)
            ref_val = ref[reg_name]['value']
            mask = self.regs[reg_name]['mask']
            if (data & mask) == (ref_val & mask):
                result = 'Ok!'
            else:
                result = '!= 0x{:0{}X}'.format(ref_val, width)
                res    = False
            if do_print:
                print '{:<22}: {:>18} {:<10}'.format(reg_name,'0x{:0{}X}'.format(data, width), result)
        return res
