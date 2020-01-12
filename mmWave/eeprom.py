#!/usr/bin/python

try:
    import ederftdi
except ImportError, e:
    pass

try:
    import smbus
except ImportError, e:
    pass

import time

RFM_DATA_MAGIC_NUM_ADDR = 0x00
RFM_ID_BASE_ADDR        = 0x01
PB_ID_BASE_ADDR         = 0x05

class Eeprom(object):
    __instance = None

    def __new__(cls, board_type='MB1'):
        if cls.__instance is None:
            cls.__instance = super(Eeprom, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self, board_type='MB1'):
        if self.__initialized:
            return
        self.__initialized = True
        self.board_type = board_type
        if board_type=='MB1':
            self.eeprom_address = 0x53
            self.temp_sens_address = 0x1b
        else:
            self.i2cbus=smbus.SMBus(1)
            self.eeprom_address = 0x50
            self.temp_sens_address = 0x18


    def read_pcb_temp(self):
        if self.board_type == 'MB0':
            temp_reg = self.i2cbus.read_i2c_block_data(0x18, 5, 2)
            temperature = (temp_reg[0]<<8) + temp_reg[1]
            temperature=((1<<13)-1)& temperature
            if temperature & 0x1000:
                temperature = -temperature
            temperature = round(temperature /16.1, 2)
        else:
            try:
                temperature = round(ederftdi.gettemp(), 2)
            except:
                return 0

        return temperature
        
    def write_rfm_data(self, rfm_id, pb_id):
        if self.board_type == 'MB1':
            wait_time = 0.01
            if isinstance(rfm_id, int):
                pass
            else:
                if rfm_id[0:2].upper() == 'SN':
                    rfm_id = rfm_id[2:]
                try:
                    rfm_id = int(rfm_id)
                except:
                    rfm_id = -1

            if rfm_id > 0xFFFFFFFF:
                rfm_id = -1
            if rfm_id != -1:
                # Valid RFM ID
                ederftdi.writeeprom(RFM_ID_BASE_ADDR, (rfm_id & 0xff))
                time.sleep(wait_time)
                ederftdi.writeeprom(RFM_ID_BASE_ADDR + 1, ((rfm_id & 0xff00) >> 8))
                time.sleep(wait_time)
                ederftdi.writeeprom(RFM_ID_BASE_ADDR + 2, ((rfm_id & 0xff0000) >> 16))
                time.sleep(wait_time)
                ederftdi.writeeprom(RFM_ID_BASE_ADDR + 3, ((rfm_id & 0xff000000) >> 24))
                time.sleep(wait_time)
            else:
                print '    rfm_id not valid'
                return

            if isinstance(pb_id, int):
                pass
            else:
                if pb_id[0:2].upper() == 'PB':
                    pb_id = pb_id[2:]
                try:
                    pb_id = int(pb_id)
                except:
                    pb_id = -1

            if pb_id > 0xFFFFFFFF:
                pb_id = -1
            if pb_id != -1:
                # Valid RFM ID
                ederftdi.writeeprom(PB_ID_BASE_ADDR, (pb_id & 0xff))
                time.sleep(wait_time)
                ederftdi.writeeprom(PB_ID_BASE_ADDR + 1, ((pb_id & 0xff00) >> 8))
                time.sleep(wait_time)
                ederftdi.writeeprom(PB_ID_BASE_ADDR + 2, ((pb_id & 0xff0000) >> 16))
                time.sleep(wait_time)
                ederftdi.writeeprom(PB_ID_BASE_ADDR + 3, ((pb_id & 0xff000000) >> 24))
                time.sleep(wait_time)
            else:
                print '    pb_id not valid'
                return

            ederftdi.writeeprom(RFM_DATA_MAGIC_NUM_ADDR, 0xCD) # Mark section as valid
            time.sleep(wait_time)

    def read_rfm_data(self):
        if self.board_type == 'MB1':
            wait_time = 0.01
            valid_flag = ederftdi.readeprom(RFM_DATA_MAGIC_NUM_ADDR)
            if valid_flag == 0xCD: # Magic number for valid data
                rfm_id = ederftdi.readeprom(RFM_ID_BASE_ADDR) + (ederftdi.readeprom(RFM_ID_BASE_ADDR + 1) << 8) + \
                         (ederftdi.readeprom(RFM_ID_BASE_ADDR + 2) << 16) + (ederftdi.readeprom(RFM_ID_BASE_ADDR + 3) << 24)
                rfm_id = 'SN' + str(rfm_id).zfill(4)
                pb_id = ederftdi.readeprom(PB_ID_BASE_ADDR) + (ederftdi.readeprom(PB_ID_BASE_ADDR + 1) << 8) + \
                         (ederftdi.readeprom(PB_ID_BASE_ADDR + 2) << 16) + (ederftdi.readeprom(PB_ID_BASE_ADDR + 3) << 24)
                pb_id = 'PB' + str(pb_id).zfill(6)
            chip_data = {'rfm_id': rfm_id, 'pb_id': pb_id}
        else:
            chip_data = {'rfm_id': None, 'pb_id': None}

        return chip_data

