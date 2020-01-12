class Vco(object):
    
    __instance = None


    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(Vco, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self):
        if self.__initialized:
            return
        self.__initialized = True
        import register
        import eder_status
        import eder_logger
        self.regs = register.Register()
        self.status = eder_status.EderStatus()
        self.logger = eder_logger.EderLogger()
        self.alc_hi_th_tbl = dict()

    def reset(self):
        self.status.clr_init_bit(self.status.VCO_INIT)
        self.alc_hi_th_tbl = dict()

    def init(self):
        if self.status.init_bit_is_set(self.status.VCO_INIT) == False:
            self.regs.set('bias_ctrl',0x1f)
            self.regs.wr('bias_vco_x3',0x00)
            self.regs.wr('vco_en',0x1c)
            self.regs.wr('vco_override_ctrl',0x1f)
            self._import_file('lut/vco/alc_hi_th', self.alc_hi_th_tbl)
            self.status.set_init_bit(self.status.VCO_INIT)
            self.logger.log_info('Chip VCO init.',2)
        else:
            self.logger.log_info('Chip VCO already initialized.',2)


    def set(self,dig_tune=0,ibias=0x0f):
        self.regs.set('vco_override_ctrl',0x180)
        self.regs.wr('vco_ibias',ibias)
        self.regs.wr('vco_dig_tune',dig_tune)

    def monitor(self,divn=214):
        self.regs.set('bias_ctrl',0x1c)
        self.regs.set('bias_pll',0x37)
        self.regs.set('vco_en',0x04)
        self.regs.set('vco_override_ctrl',0x004)
        self.regs.wr('pll_divn',divn)
        self.regs.set('pll_en',0x0B)
        self.regs.wr('pll_ld_mux_ctrl',0x03)

    def _import_file(self, fname, table):
        try:
            f = open(fname)
        except IOError:
            print fname + ' not found!'
            return
        line = '#'
        while line[0]=='#':
            # Ignore the header.
            # Header should always start with '#'
            line = f.readline()

        while True:
            if line == '':
                break
            line = line.replace('\n', '')
            line = line.replace('\r', '')
            line = line.split(',')
            table[line[0]] = line[1:len(line)]
            line = f.readline()
        f.close()

    def _test_import_file(self, fname, table):
        try:
            f = open(fname)
        except IOError:
            self.logger.log_error(fname + ' not found!')
            return
        line = '#'
        while line[0]=='#':
            # Ignore the header.
            # Header should always start with '#'
            line = f.readline()

        while True:
            if line == '':
                break
            line = line.replace('\n', '')
            line = line.replace('\r', '')
            line = line.split(',')
            temp_dict = dict()
            for i in xrange(1, len(line)-1, 2):
                temp_dict[str(float(line[i]))] = line[i+1]
            table[line[0]] = temp_dict
            line = f.readline()
        f.close()

    def test_set_alc_hi_th(self, freq, temp):
        table = dict()
        freq = float(freq)
        temp = float(temp)
        self._test_import_file('lut/vco/test_alc_hi_th', table)
        if table.has_key(str(freq)) == False:
            table_sorted_keys = table.keys()
            table_sorted_keys.sort()
            print table_sorted_keys
            for freq_index in xrange(len(table)):
                if freq < float(table_sorted_keys[freq_index]):
                    print '*'
        return
        print table[str(freq)][str(temp)]


