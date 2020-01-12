class Amux:

    # DC sense calibration
    amux_dc_sense_calib = 0x40

    # bist_amux_ctrl
    # ==============
    amux_bg_pll       = 0
    amux_bg_tx        = 1
    amux_bg_rx        = 2
    amux_temp         = 3
    amux_rx_bb        = 4
    amux_vco          = 5
    amux_vcc_pll      = 6
    amux_tx_pdet      = 7
    amux_adc_ref      = 8
    amux_dco_i        = 9
    amux_dco_q        = 10
    amux_dco_cm       = 11
    amux_otp          = 12
    amux_tx_env_pdet  = 13
    amux_vcc_pa       = 14
    amux_vcc_tx       = 15

    # amux_rx_bb (rx_bb_test_ctrl)
    # ============================
    rx_bb_mix_pd_i    = 1
    rx_bb_mix_pd_q    = 2
    rx_bb_mix_pd_th_i = 5
    rx_bb_mix_pd_th_q = 6
    rx_bb_mix_dc_p_i  = 9
    rx_bb_mix_dc_p_q  = 10
    rx_bb_mix_dc_n_i  = 13
    rx_bb_mix_dc_n_q  = 14
    rx_bb_inb_pd_i    = 17
    rx_bb_inb_pd_q    = 18
    rx_bb_inb_pd_th_i = 21
    rx_bb_inb_pd_th_q = 22
    rx_bb_inb_dc_p_i  = 25
    rx_bb_inb_dc_p_q  = 26
    rx_bb_inb_dc_n_i  = 29
    rx_bb_inb_dc_n_q  = 30
    rx_bb_vga1_pd_i    = 33
    rx_bb_vga1_pd_q    = 34
    rx_bb_vga1_pd_th_i = 37
    rx_bb_vga1_pd_th_q = 38
    rx_bb_vga1_dc_p_i  = 41
    rx_bb_vga1_dc_p_q  = 42
    rx_bb_vga1_dc_n_i  = 45
    rx_bb_vga1_dc_n_q  = 46
    rx_bb_vga2_pd_i    = 49
    rx_bb_vga2_pd_q    = 50
    rx_bb_vga2_pd_th_i = 53
    rx_bb_vga2_pd_th_q = 54
    rx_bb_vga2_dc_p_i  = 57
    rx_bb_vga2_dc_p_q  = 58
    rx_bb_vga2_dc_n_i  = 61
    rx_bb_vga2_dc_n_q  = 62
    rx_bb_vga1db_pd_i    = 65
    rx_bb_vga1db_pd_q    = 66
    rx_bb_vga1db_pd_th_i = 69
    rx_bb_vga1db_pd_th_q = 70
    rx_bb_vga1db_dc_p_i  = 73
    rx_bb_vga1db_dc_p_q  = 74
    rx_bb_vga1db_dc_n_i  = 77
    rx_bb_vga1db_dc_n_q  = 78
    rx_bb_outb_pd_i    = 81
    rx_bb_outb_pd_q    = 82
    rx_bb_outb_pd_th_i = 85
    rx_bb_outb_pd_th_q = 86
    rx_bb_outb_dc_p_i  = 89
    rx_bb_outb_dc_p_q  = 90
    rx_bb_outb_dc_n_i  = 93
    rx_bb_outb_dc_n_q  = 94


    # vco_amux_ctrl
    # =============
    vco_alc_th    = 0
    vco_vco_amp   = 1
    vco_atc_lo_th = 2
    vco_atc_hi_th = 3
    vco_vcc_vco   = 4
    vco_vcc_chp   = 5
    vco_vcc_synth = 6
    vco_vcc_bb_tx = 7
    vco_vcc_bb_rx = 8

    # bist_otp_ctrl
    # =============
    otp_temp_th   = 0
    otp_vdd_1v2   = 1
    otp_vdd_1v8   = 2
    otp_vcc_rx    = 3

    # pll_ld_mux_ctrl
    # ===============
    pll_ld_ld     = 0
    pll_ld_xor    = 1
    pll_ld_ref    = 2
    pll_ld_vco    = 3
    pll_ld_ld_raw = 4
    pll_ld_tst_0  = 5
    pll_ld_tst_1  = 6

    def __init__(self, regs):
        self.regs = regs


    def set(self, src=None, src_2=None):
        """Enables output of source "src" on AMUX-pin.
           src : source for AMUX output
           Example:
           amux.set(dbg.amux_vco)
        """
        if src != None:
            self.regs.wr('bist_amux_ctrl',src)

        if src_2 != None:
            if   (self.regs.rd('bist_amux_ctrl') & 0x7F) == self.amux_rx_bb:
                self.regs.wr('rx_bb_test_ctrl', src_2)
            elif (self.regs.rd('bist_amux_ctrl') & 0x7F) == self.amux_vco:
                self.regs.wr('vco_amux_ctrl', src_2)
            elif (self.regs.rd('bist_amux_ctrl') & 0x7F) == self.amux_otp:
                self.regs.wr('bist_ot_ctrl', src_2)
            elif (self.regs.rd('bist_amux_ctrl') & 0x7F) == self.amux_tx_pdet:
                self.regs.wr('tx_bf_pdet_mux', src_2)
            elif (self.regs.rd('bist_amux_ctrl') & 0x7F) == self.amux_tx_env_pdet:
                self.regs.wr('tx_bf_pdet_mux', src_2)

    def get(self):
        src = self.regs.rd('bist_amux_ctrl')
        src_2 = None
        if (0x7F & src) == (0x7F & self.amux_rx_bb):
            src_2 = self.regs.rd('rx_bb_test_ctrl')
        elif (0x7F & src) == (0x7F & self.amux_vco):
            src_2 = self.regs.rd('vco_amux_ctrl')
        elif (0x7F & src) == (0x7F & self.amux_otp):
            src_2 = self.regs.rd('bist_ot_ctrl')
        elif (0x7F & src) == (0x7F & self.amux_tx_pdet):
            src_2 = self.regs.rd('tx_bf_pdet_mux')
        return src, src_2

    def enable(self):
        """Enable output on AMUX-pin.
        """
        self.regs.set('bist_amux_ctrl',0x80)

    def disable(self):
        """Disable output on AMUX-pin.
        """
        self.regs.clr('bist_amux_ctrl',0x80)


    def clr(self):
        """Disable output on AMUX-pin.
        """
        self.regs.clr('bist_amux_ctrl',0x80)
