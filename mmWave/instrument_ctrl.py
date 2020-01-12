import visa
import logging
import time
import eder
import csv

v8486A_cal_table = {'50GZ':'118.6%', '51GZ':'115.1%', '52GZ':'113.4%',
                    '53GZ':'117.9%', '54GZ':'120.4%', '55GZ':'119.8%',
                    '56GZ':'118.8%', '57GZ':'118.7%', '58GZ':'122.2%',
                    '59GZ':'124.9%', '60GZ':'125.2%', '61GZ':'123.9%',
                    '62GZ':'121.0%', '63GZ':'123.6%', '64GZ':'122.2%',
                    '65GZ':'123.7%', '66GZ':'120.7%', '67GZ':'120.0%',
                    '68GZ':'119.7%', '69GZ':'117.3%', '70GZ':'116.1%',
                    '71GZ':'113.8%', '72GZ':'111.1%', '73GZ':'108.0%',
                    '74GZ':'105.0%', '75GZ':'104.8%'
}


def hp_437b_cal_fac(rm):
    logger.info("Starting programming Agilent V8486A calibration factors ...")
    hp = rm.open_resource('GPIB0::13::INSTR')
    logger.debug(hp.write('SN8V8486A_'))
    logger.debug(hp.write('CT8'))
    logger.debug(hp.write('RF8100%'))
    logger.debug(hp.write('ET8'))
    for freq,cal_fac in sorted(v8486A_cal_table.iteritems()):
        logger.info(freq+' '+cal_fac)
        logger.debug(hp.write(freq+cal_fac+'EN'))
        time.sleep(1)
    logger.debug(hp.write('EX'))
    logger.info("Done programming Agilent V8486A calibration factors.")

def test((rm,dut,tx_all)):
    hi = rm.open_resource('ASRL/dev/ttyACM0::INSTR')
    hp = rm.open_resource('GPIB0::13::INSTR')

    dut.reset()
    dut.run_tx()
    dut.regs.wrrd('trx_tx_on',0x1F0000)
    dut.tx.dco.run()
    freq = 60.48

    with open("eder_b_pdet_meas.csv", 'ab') as csv_log:
        writer = csv.writer(csv_log)

        element = int(raw_input("Set Element and start measurement by inputting here which element is set:"))
        while element < 16:
            logger.info("Measurement for Element "+str(element)+" started ...")

            logger.debug(hi.write("POWER:LEVEL -30"))
            logger.debug(hi.write("OUTPUT OFF"))
            logger.debug(hi.write("FREQ:CW 50E6"))
            logger.debug(hp.write("SE8EN"))
            logger.debug(hp.write("FR"+str(freq)+"GZ"))
            writer.writerow(["Element:", element, "Frequency:", freq])
            writer.writerow(["Pin", "Pout", "Pdet"])

            if tx_all == 'all':
                logger.info(dut.regs.wrrd('trx_tx_on',0x1FFFFF))
            else:
                logger.info(dut.regs.wrrd('trx_tx_on',0x1F0000|(1<<element)))

            for pin in xrange(-30,5):
                logger.debug(hi.write("POWER:LEVEL "+str(pin)))
                logger.debug(hi.write("OUTPUT ON"))
                time.sleep(2)
                logger.debug(hp.write("GT1"))
                pout=float(hp.read())
                pdet=dut.tx.alc.meas_pdet(element);
                writer.writerow([pin, pout, pdet])

            logger.info("Measurement for Element "+str(element)+" done!")
            element = int(raw_input("Set Element and start measurement by inputting here which element is set:"))
    csv_log.close()
    logger.debug(hi.write("POWER:LEVEL -30"))
    logger.debug(hi.write("OUTPUT OFF"))

    dut.reset()


if __name__ == '__main__':
    rm = visa.ResourceManager('@py')
    dut = eder.Eder(unit_name='SN0310',board_type='MB1')

    logger = logging.getLogger('instrument_ctrl')
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    logger.addHandler(ch)

    # Set up measurement types
    options = {0: ("HP 437B calibration factor programming",hp_437b_cal_fac,rm),
               1: ("Test with all TX elements enabled",test,(rm,dut,'all')),
               2: ("Test with individual elements enabled",test,(rm,dut,'individual'))
              }
    # Get user input on what test to run
    print "#####################################################"
    print "###Sivers Tx Power detector measurement #############"
    print "#####################################################"
    print "Choose an option by entering the corresponding number"
    for num,choice in sorted(options.iteritems()):
        print str(num)+': '+options[int(num)][0] 
    num = raw_input("To proceed choose measurement type: ")

    # Call the corresponding function
    try:
        options[int(num)][1](options[int(num)][2])
    except KeyError:
        print "Not valid input"

    print "The script has finished!"
