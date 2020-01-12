### Eder Server
### Provides a simple network interface to an Eder chip.
###
### Run with flag -h to display help and information.
### For information about the interface, read the user manual.
### Press Ctrl+C to close the server.
###
### Author: Kjartan Kristjansson
### Company: Sivers IMA AB
### Revision 1.0  2017/08/28  19:16
### Initial revision.
### Revision 1.1  2017/10/25  10:52
### Added functionality for reading chip temperature and resetting.
### the chip
### Revision 1.2  2017/12/11  09:53
### Added functionality for Eder charge pump measurements.
### Revision 2.0  2018/06/21  14:14
### Modified to work with Eder B. Not backwards-compatible at the moment.
### Revision 2.1  2018/06/26  15:35
### Added functionality to initializing Eder in SX mode.

import BaseHTTPServer
import argparse
import eder
import sys
import time
from collections import OrderedDict
from datetime import datetime
from threading import Thread, Event

def CreateEderHandler(eder_obj, event):
	"""
	# This function is a class factory for the EderHandler.
	# By defining the class this way, the Eder object and event can 
	# be passed to the request handler without making them global.
	"""

	class EderHandler(BaseHTTPServer.BaseHTTPRequestHandler, object):
		"""
		# The EderHandler class handles the HTTP requests that
		# are sent to the server, i.e. interprets them and passes
		# the commands on to the Eder object.
		# Responds with responses from Eder, if appropriate.
		"""

		def __init__(self, *args, **kwargs):
			"""
			# Constructor, set instance variables and then proceed with
			# request handling.
			"""
			self.eder_obj = eder_obj
			self.event = event
			try:
				super(EderHandler, self).__init__(*args, **kwargs)
			except Exception as e:
				print 'Something went wrong, signalling main thread to exit.'
				print 'Error message: {}'.format(e)
				self.event.set()
				
		def log_message(self, format, *args):
			"""Suppress the default BasicHTTPRequestHandler log."""
			pass

		def do_GET(self):
			"""
			# This method determines how the server handles requests.
			# If you are going to add functionality to the server,
			# add a condition to the if-clause in this method.
			"""
			self.send_response(200)
			self.send_header('Content-type', 'text/html')
			self.end_headers()
			
			print datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
			
			print 'Received a request on {}'.format(self.path)
			split_path = self.path.split('/')
			
			request = split_path[1]
			
			# Server received a root request.
			# Respond with a message.
			if not split_path[1]:
				self.wfile.write('<html><body><h1>EderServer</h1><p>Server is up and running.</p></body></html>')
				return

			# The code below determines how the server deals with different types
			# of requests. Edit this to alter behaviour or add functionality.
			if request == 'txenable':
				self.eder_obj.tx_enable()
				print 'Enabling Eder TX'
			elif request == 'txdisable':
				self.eder_obj.tx_disable()
				print 'Disabling Eder TX'
			elif request == 'txsetup':
				freq = int(split_path[2], 10)
				self.eder_obj.tx_setup(freq)
				res_freq = self.get_rf_freq()
				self.wfile.write('{}'.format(res_freq))
				print 'Ran Eder TX setup'
			elif request == 'txchannels':
				channels = split_path[2:]
				self.set_channels('TX', channels)
			elif request == 'txchannelandfirst':
				channels = split_path[2:]
				channels.append('1')
				self.set_channels('TX', channels)
			elif request == 'txallchannels':
				channels = map(str, xrange(1, 17))
				self.set_channels('TX', channels)
			elif request == 'rxenable':
				self.eder_obj.rx_enable()
				print 'Enabling Eder RX'
			elif request == 'rxdisable':
				self.eder_obj.rx_disable()
				print 'Disabling Eder RX'
			elif request == 'rxsetup':
				value = int(split_path[2], 10)
				self.eder_obj.rx_setup(value)
				res_freq = self.get_rf_freq()
				self.wfile.write('{}'.format(res_freq))
			elif request == 'rxchannels':
				channels = split_path[2:]
				self.set_channels('RX', channels)
			elif request == 'rxallchannels':
				channels = map(str, xrange(1, 17))
				self.set_channels('RX', channels)
			elif request == 'rxdcorun':
				self.eder_obj.rx.dco.run()
				print 'Ran DC-offset calibration'
			elif request == 'freqset':
				value = int(split_path[2], 10)
				self.eder_obj.pll.set(value)
				res_freq = self.get_rf_freq()
				self.wfile.write('{}'.format(res_freq))
			elif request == 'regread':
				register = split_path[2]
				reg_value = self.eder_obj.regs.rd(register)
				self.wfile.write('{}'.format(reg_value))
				print 'Register {} value read: 0x{:02X}'.format(register, reg_value)
			elif request == 'regwrite':
				register = split_path[2]
				value = int(split_path[3], 16)
				print 'Reg {} : {}'.format(register, self.eder_obj.regs.wrrd(register, value))
			elif request == 'regdump':
				registers = self.eder_obj.regs.regs
				reg_arr = []
				for reg in sorted(registers):
					value = self.eder_obj.regs.rd(reg)
					width = 2 * self.eder_obj.regs.size(reg)
					reg_arr.append(r'{}:0x{:0{}X}'.format(reg, value, width))
				self.wfile.write(' '.join(reg_arr))
				print 'Register dump written'
			elif request == 'txphaseshifterinit':
				value = int(split_path[2], 10)
				self.eder_obj.tx.set_beam(value)
				print 'Phase shifter init, value:', value
			elif request == 'txphaseshifterset':
				row = int(split_path[2], 10)
				col = int(split_path[3], 10)
				value = int(split_path[4], 10)
				self.eder_obj.tx.bf.awv.wr_raw(row, col, value)
				print 'Phase shifter set with values: ({}, {}, {})'.format(row, col, value)
			elif request == 'txawvsetup':
				freq = int(split_path[2], 10)
				self.eder_obj.tx.bf.awv.setup('lut/beambook/bf_tx_awv_3', freq, 0.0)
				self.eder_obj.tx.bf.idx.setup('lut/beambook/bf_tx_awv_idx', freq)
				self.eder_obj.tx.bf.awv.dump()
			elif request == 'txawvsetupzeros':
				self.eder_obj.tx.bf.awv.setup('lut/beambook/bf_tx_awv', 0.0, 0.0)
				self.eder_obj.tx.bf.idx.setup('lut/beambook/bf_tx_awv_idx', 0.0)
				self.eder_obj.tx.bf.awv.wr(63, 6, 0x0)
				self.eder_obj.tx.bf.awv.dump()
			elif request == 'rxawvsetupzeros':
				self.eder_obj.rx.bf.awv.setup('lut/beambook/bf_rx_awv', 0.0, 0.0)
				self.eder_obj.rx.bf.idx.setup('lut/beambook/bf_rx_awv_idx', 0.0)
				self.eder_obj.rx.bf.awv.wr(63, 6, 0x0)
				self.eder_obj.rx.bf.awv.dump()
			elif request == 'rxphaseshifterinit':
				value = int(split_path[2], 10)
				self.eder_obj.rx.set_beam(value)
				print 'RX Phase shifter init, value:', value
			elif request == 'rxphaseshifterset':
				row = int(split_path[2], 10)
				col = int(split_path[3], 10)
				value = int(split_path[4], 10)
				self.eder_obj.rx.bf.awv.wr(row, col, value)
				print 'Phase shifter set with values: ({}, {}, {})'.format(row, col, value)
			elif request == 'rxawvsetup':
				freq = int(split_path[2], 10)
				self.eder_obj.rx.bf.awv.setup('lut/beambook/bf_rx_awv_3', freq, 0.0)
				self.eder_obj.rx.bf.idx.setup('lut/beambook/bf_rx_awv_idx', freq)
				self.eder_obj.rx.bf.awv.dump()
			elif request == 'reset':
				self.eder_obj.reset()
			elif request == 'chipinit':
				self.eder_obj.init()
			elif request == 'chiptemp':
				temp = self.eder_obj.temp.run() - 273.15
				self.wfile.write('{0:.1f}'.format(temp))
				print 'Chip temperature read, value: {0:.1f} degrees C'.format(temp)
			elif request == 'adcinit':
				self.eder_obj.adc.init()
			elif request == 'tempinit':
				self.eder_obj.temp.init()
				self.eder_obj.adc.init()				
			elif request == 'adcread':
				mux_ch = int(split_path[2], 10);
				val = self.adc_read(mux_ch)
				self.wfile.write('{}'.format(val))
				print 'ADC value read, value: {}'.format(val)
			elif request == 'adcamuxset':
				src1 = split_path[2]
				srcattr1 = getattr(self.eder_obj.adc.amux, src1)
				srcattr2 = None
				if len(split_path) > 3:
					src2 = split_path[3]
					srcattr2 = getattr(self.eder_obj.adc.amux, src2)
				self.eder_obj.adc.amux.set(srcattr1, srcattr2)
			elif request == 'pllinit':
				self.eder_obj.pll.init()
			elif request == 'vcoampread':
				self.eder_obj.regs.wr('vco_amux_ctrl', 0x11)
				self.eder_obj.adc.init()
				amp = self.adc_read(5)
				amp = round(0.000886948*amp,6)
				self.wfile.write('{}'.format(amp))
				print 'VCO Amplitude read, value: {}'.format(amp)
			elif request == 'vcoamppllmon':
				vcoamp = self.eder_obj.pll.monitor('VCOamp')
				self.wfile.write('{}'.format(vcoamp))				
				#print 'PLL Monitor VCOamp read, value: {} V'.format(vcoamp)				
			elif request == 'setvcm':
				voltage = int(split_path[2], 10)
				self.eder_obj.ederftdi.setvcm(voltage)
				print 'Set Vcm to {}'.format(voltage)
			elif request == 'setvchp':
				vchp = int(split_path[2])
				self.eder_obj.ederftdi.setvchp(vchp)
			elif request == 'readVtune':
				vtune = self.eder_obj.pll.monitor('Vtune')
				self.wfile.write('{}'.format(vtune))				
				#print 'Vtune read, value: {} V'.format(vtune)
			elif request == 'getchpc':
				current = self.eder_obj.ederftdi.getchpc()
				self.wfile.write('{}'.format(current))
			elif request == 'eepromtemp':
				temp = self.eder_obj.ederftdi.gettemp()
				self.wfile.write('{}'.format(temp))
			elif request == 'voltagecheck':
				self.wfile.write('Measuring voltages... ')

				checks = OrderedDict()
				checks['bg_pll'] = {'str1': 'amux_bg_pll', 'str2': None, 'label': 'BG PLL', 'addr': 0, 'multiplier': 1}
				checks['bg_tx'] = {'str1': 'amux_bg_tx', 'str2': None, 'label': 'BG TX', 'addr': 1, 'multiplier': 1}
				checks['bg_rx'] = {'str1': 'amux_bg_rx', 'str2': None, 'label': 'BG RX', 'addr': 2, 'multiplier': 1}
				checks['vcc_pll'] = {'str1': 'amux_vcc_pll', 'str2': None, 'label': 'VCC PLL', 'addr': 6, 'multiplier': 4/3.0}
				checks['vcc_pa'] = {'str1': 'amux_vcc_pll', 'str2': None, 'label': 'VCC PA', 'addr': 14, 'multiplier': 4/3.0}
				checks['vcc_tx'] = {'str1': 'amux_vcc_tx', 'str2': None, 'label': 'VCC TX', 'addr': 15, 'multiplier': 4/3.0}
				checks['vcc_vco'] = {'str1': 'amux_vco', 'str2': 'vco_vcc_vco', 'label': 'VCC VCO', 'addr': 5, 'multiplier': 1}
				checks['vcc_vco_chp'] = {'str1': 'amux_vco', 'str2': 'vco_vcc_chp', 'label': 'VCC VCO CHP', 'addr': 5, 'multiplier': 1}
				checks['vcc_vco_synth'] = {'str1': 'amux_vco', 'str2': 'vco_vcc_synth', 'label': 'VCC VCO Synth', 'addr': 5, 'multiplier': 4/3.0}
				checks['vcc_vco_bb_tx'] = {'str1': 'amux_vco', 'str2': 'vco_vcc_bb_tx', 'label': 'VCC VCO BB TX', 'addr': 5, 'multiplier': 4/3.0}
				checks['vcc_vco_bb_rx'] = {'str1': 'amux_vco', 'str2': 'vco_vcc_bb_rx', 'label': 'VCC VCO BB RX', 'addr': 5, 'multiplier': 4/3.0}
				checks['vdd_otp_1v2'] = {'str1': 'amux_otp', 'str2': 'otp_vdd_1v2', 'label': 'VDD OTP 1V2', 'addr': 12, 'multiplier': 1}
				checks['vdd_otp_1v8'] = {'str1': 'amux_otp', 'str2': 'otp_vdd_1v8', 'label': 'VDD OTP 1V8', 'addr': 12, 'multiplier': 1}
				checks['vcc_otp_rx'] = {'str1': 'amux_otp', 'str2': 'otp_vcc_rx', 'label': 'VCC OTP RX', 'addr': 12, 'multiplier': 4/3.0}

				results = []

				for v in checks:
					check = checks[v]
					str1 = getattr(self.eder_obj.adc.amux, check['str1'])
					str2 = getattr(self.eder_obj.adc.amux, check['str2']) if check['str2'] else None
					self.eder_obj.adc.amux.set(str1, str2)
					voltage = 3.3*self.adc_read(check['addr'], 128)/2**12*check['multiplier']
					results.append('{}: {:0.3f} V'.format(check['label'], voltage))

				self.wfile.write('Done!<br><br>')
				self.wfile.write('<br>'.join(results))
			elif request == 'rxdcocheck':
				idiff, qdiff, icm, qcm = self.eder_obj.rx.dco.iq_meas.meas_volt(16, 'sys')
				dcostr = '{:07.5f}, {:07.5f}, {:07.5f}, {:07.5f}'.format(idiff, qdiff, icm, qcm)
				self.wfile.write('{}'.format(dcostr))				
				print 'Rx DCO read: '
				print 'Idiff: {:07.5f} V'.format(idiff)
				print 'Qdiff: {:07.5f} V'.format(qdiff)
				print 'Icm: {:07.5f} V'.format(icm)
				print 'Qcm: {:07.5f} V'.format(qcm)
			elif request == 'shutdown':
				self.event.set()
			else:
				print 'Illegal request "{}" received. It was ignored.'.format(request)
				
			# Add empty line for log readability.
			print
				
		def get_rf_freq(self):
			"""Get the RF frequency of Eder."""
			divn = self.eder_obj.regs.rd('pll_divn')
			ref_freq = 45e6
			return (divn + 36)*6*ref_freq
				
		def set_channels(self, side, channels):
			"""
			# Set the channels for the chosen side (TX or RX) to
			# the ones given in the array channels.
			"""
			try:
				regVal = (0x1F << 16) + sum(map(lambda ch: 2**(int(ch, 10)-1), channels))
				print 'Setting {} channels to {}:'.format(side, channels)
				print self.eder_obj.regs.wrrd('trx_{}_on'.format(side.lower()), regVal)
			except ValueError:
				# Invalid request, do nothing but report.
				print 'Error: Could not set {} channels, invalid format.'.format(side)
				
		def is_int_list(self, lst):
			"""
			# Returns True if and only if all the items in the list
			# 'lst' are of type int.
			"""
			return all(map(lambda x: type(x) == int, lst))
			
		def adc_read(self, channel):
			self.eder_obj.adc.start(channel)
			time.sleep(0.1)
			val = self.eder_obj.adc.mean()
			self.eder_obj.adc.stop()
			return val
				
				
	return EderHandler
	
class EderServer():
	def __init__(self, port, unit_name):
		"""Constructor, set instance variables."""
		self.port = port
		self.unit_name = unit_name
		self.event_monitor_drop = Event()
		self.event_monitor_term = Event()
		self.event_running = Event()
		self.eder_obj = None
		
	def monitor(self, eder_obj, event_drop, event_term):
		"""
		# A function that is intended to be run in a separate daemon thread.
		# Detects if the connection to Eder is dropped and signals the server
		# to reconnect in that case.
		# Continues until the server signals that it is shutting down by setting
		# the event_term event.
		"""
		while not event_term.isSet():
			time.sleep(5)
			try:
				eder_obj.chip_is_present()
			except:
				event_drop.set()
			
	def run(self):
		"""
		# Create the Eder object and run the Eder server.
		# Monitors input from the user and exits if a Ctrl+C
		# is received.
		# Also exits if any errors occur.
		"""
		try:
			# Create an Eder object with the parameters supplied by the user.
			self.eder_obj = eder.Eder(unit_name=self.unit_name, board_type='MB1')
		except:
			print 'A connection to Eder could not be established. Please restart the server.'
			sys.exit(1)

		# Create an Eder handler that uses the newly created Eder object.
		handler = CreateEderHandler(self.eder_obj, self.event_running)
		httpd = BaseHTTPServer.HTTPServer(('localhost', self.port), handler)

		# Create the thread that monitors the connection to Eder.
		thread_monitor = Thread(target = self.monitor, kwargs={'eder_obj':self.eder_obj, 'event_drop':self.event_monitor_drop, 'event_term': self.event_monitor_term})
		thread_monitor.daemon = True
		thread_monitor.start()
		
		# Create the thread that handles the server requests.
		thread_server = Thread(target = httpd.serve_forever)
		thread_server.daemon = True
		
		try:
			thread_server.start()
			print 'EderServer is serving at port {}.'.format(self.port)
			while True:
				while not (self.event_monitor_drop.isSet() or self.event_running.isSet()):
					# Main thread does nothing but poll monitor drop and server error signals.
					time.sleep(1)
				if self.event_monitor_drop.isSet():
					# Eder connection dropped. Attempt to reconnect until successful or
					# the user requests server shutdown.
					print 'Lost connection with Eder, trying to reconnect...'
					time.sleep(5)
					self.eder_reconnect()
				if self.event_running.isSet():
					break
					
		except KeyboardInterrupt:
			print 'Received termination signal from user. Shutting down...'
			
		self.event_monitor_term.set()
		thread_monitor.join()
		httpd.shutdown()
		httpd.socket.close()
		print 'EderServer exited successfully.'
		
	def eder_reconnect(self):
		"""
		# Attempt to reconnect to Eder.
		# Clear the event monitor 'dropped' event if successful.
		"""
		status = self.eder_obj.ederftdi.reinit(self.unit_name)
		if not status:
			# Init returned 0 (Success).
			print 'Successfully reconnected to Eder!'
			print 'EderServer is still serving at port {}.'.format(self.port)
			print 'Attention: The chip might have been reset.'
			self.event_monitor_drop.clear()

def main():
	"""Parse input arguments and start server."""
	parser = argparse.ArgumentParser(description='Sivers IMA - Eder Server')

	parser.add_argument('-p', '--port', dest='port', default=8000, type=int, help='The port on which to serve the Eder interface. Default: 8000.')
	parser.add_argument('-u', dest='unit_name', metavar='UNIT', default=None, help='The serial number of the MB1 unit.')
	args = parser.parse_args()
	
	if not args.unit_name:
		print 'A MB1 unit name was not given, searching for available devices...'
		device = find_device()
		if not device:
			print 'No device was found! Make sure that an MB1 board is connected and try again.'
			sys.exit(1)
		else:
			print 'Found device {}'.format(device)
			args.unit_name = device
			
	server = EderServer(args.port, args.unit_name)
	server.run()

def find_device():
	"""
	# This function checks the output from the ederftdi module to find out
	# if there are any Eder chips present.
	# If so, returns the unit name of the first device found.
	# The current implementation is higly sensitive to the way ederftdi
	# module lists the connected devices.
	"""
	from os import linesep
	import subprocess
	try:
		dev_str = subprocess.check_output('python -c "import ederftdi;ederftdi.listdevs()"')
	except:
		print 'Could not search for devices. Make sure that the ederftdi module is installed'
	if not dev_str.startswith('0'):
		# At least one device was found, return the device name.
		device = dev_str.split(linesep)[2].strip().split('=')[1]
		return device
	else:
		# No device was found
		return None

if __name__ == '__main__':
	main()
