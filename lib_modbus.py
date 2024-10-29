import logging
import time

import struct

from pyModbusTCP import utils
from pyModbusTCP.client import ModbusClient

STEP_REV = 16384

# DEBUG LEVELS
# set debug level for pyModbusTCP.client to see frame exchanges

logging.basicConfig()
logging.getLogger('pyModbusTCP.client').setLevel(logging.DEBUG)

# REGISTER ADDRESSES

r_add = {

	"MBnode_guard": 5644,	# UINT16 	R/W 	Monitoring time in ms 0 - 10000
	"AccessExcl": 	282,	# UINT16 	R/W 	Get exclusive access to access channel (0, no - 1, exclusive)
	"DEVcmdinterf": 1282,	# UINT16 	R/W 	Control Mode: 1 Local 2 Fieldbus 3 RS485
	"_DCOMstatus": 	6916,	# UINT16 	R/- 	DriveCom status word: 15th bit - reference ok
	"DCOMopmode": 	6918,	# INT16 	R/W 	Operating Mode: 1 Profile Position 6 Homing
	"HMmethod": 	6936,	# INT16 	R/W 	17 LIMN
	"HMv": 			10248,	# UINT32	R/W 	Target velocity for searching the switch
	"HMv_out": 		10250,	# UINT32	R/W 	Target velocity for moving away from the switch
	"DCOMcontrol": 	6914,	# UINT16	R/W		DriveCom control word: [0,15] READY - [0,31] GO
	"PPp_target": 	6940, 	# INT32		R/W 	Target position for operating mode Profile Position
	"PPv_target": 	6942,	# UINT32	R/W 	Target velocity for operating mode Profile Position
	"RAMP_v_acc": 	1556,	# UINT32	R/W 	Acceleration of the motion profile for velocity
	"RAMP_v_dec": 	1558,	# UINT32	R/W 	Deceleration of the motion profile for velocity
	"_p_act": 		7706,	# INT32 	R/- 	Actual position
	"ScalePOSnum":	1552,	# INT32 	R/W 	Position scaling: Numerator
	"ScalePOSdenom":1550,	# INT32 	R/W 	Position scaling: Denominator
	"ERR_clear":	15112,	# UINT16 	R/W 	Clear error memory
	"driveStat":	6986,	# UINT16 	R/- 	Drive Profile Lexium driveStat
	"PositiveLimit":1544
}

def read_bit(value,bit):
	if value is not None:
		r = utils.get_bits_from_int(value, val_size=16)
		return r[bit]
	else:
		return None

def print_bits(value, size):
	if value is not None:
		r = utils.get_bits_from_int(value, val_size=size)

		print()
		print("\
	Bit 0: {} - Operating state Ready To Switch On\n\
	Bit 1: {} - Operating state Switched On\n\
	Bit 2: {} - Operating state Operation Enabled\n\
	Bit 3: {} - Operating state Fault\n\
	Bit 4: {} - Voltage Enabled\n\
	Bit 5: {} - Operating state Quick Stop\n\
	Bit 6: {} - Operating state Switch On Disabled\n\
	Bit 7: {} - Error of error class 0\n\
	Bit 8: {} - HALT request active\n\
	Bit 9: {} - Remote\n\
	Bit 10: {} - Target Reached\n\
	Bit 11: {} - Internal Limit Active\n\
	Bit 12: {} - Operating mode-specific\n\
	Bit 13: {} - x_err\n\
	Bit 14: {} - x_end\n\
	Bit 15: {} - ref_ok\n\
			".format(*r))


def dConv(p):

	p = int(p)
	return utils.long_list_to_word([p])



class modbusDriver:

	def __init__(self, host, unit_id, dummy = False):

		self.client = ModbusClient(
			host 		= host, 
			port 		= 502, 
			unit_id		= 1, 
			auto_open	= True, 
			auto_close	= False,
			timeout		= 10
			)
		self.dummy = dummy

	def read(self, address, length):

		if not self.dummy:
			int_list = self.client.read_holding_registers(address,length)
			return utils.word_list_to_long(int_list)[0]
		else:
			print("read",address,length)
			return 0

	def write(self, address, values):

		if not self.dummy:
			a = []

			for e in values:
				a.append(int(e))

			print(a)

			return self.client.write_multiple_registers(int(address),a)
		else:
			print("write",address,values)
			return 0

	def run(self):

		self.write(r_add["DCOMcontrol"],[0,15])		# motore in Run
		time.sleep(0.1)
		self.write(r_add["DCOMcontrol"],[0,31])		# go!

	def homing(self, vel):

		self.write(r_add["DCOMopmode"],[0,6])		# passa in modalita' HOMING
		self.write(r_add["HMmethod"],[0,17])		# selezione la modalita' di Homing LIMN
		self.write(r_add["HMv"],[0,vel,0,vel/2])	# selezione la velocita' di Homing


	def move(self, pos, vel, acc):

		act_pos = self.read(r_add["_p_act"],2)
		target_pos = act_pos + pos

		self.write(r_add["DCOMopmode"],[0,1])		# passa in modalita' PROFILE POSITION

		self.write(r_add["PPp_target"],dConv(target_pos))
		self.write(r_add["PPv_target"],dConv(vel))
		self.write(r_add["RAMP_v_acc"],dConv(acc))
		self.write(r_add["RAMP_v_dec"],dConv(acc))

	def moveTo(self, pos, vel, acc):

		self.write(r_add["DCOMopmode"],[0,1])		# passa in modalita' PROFILE POSITION

		self.write(r_add["PPp_target"],dConv(pos))
		self.write(r_add["PPv_target"],dConv(vel))
		self.write(r_add["RAMP_v_acc"],dConv(acc))
		self.write(r_add["RAMP_v_dec"],dConv(acc))

	def moveList(self, pos_, time_):

		self.write(r_add["DCOMopmode"],[0,1])		# passa in modalita' PROFILE POSITION

		for i in range(1,len(time_)):

			pos_[i] = int(pos_[i])
			time_[i] = float(time_[i])

			dist = abs(pos_[i] - pos_[i-1])
			durata = time_[i] - time_[i-1]
			pos_to_rev = dist / STEP_REV 			# [rev]
			vel = int(pos_to_rev / (durata / 60)) * 2 	# [rpm]
			acc = int(vel / (durata / 2))				# [rpm/s]

			self.write(r_add["PPp_target"],dConv(pos_[i]))
			self.write(r_add["PPv_target"],dConv(vel))
			self.write(r_add["RAMP_v_acc"],dConv(acc))
			self.write(r_add["RAMP_v_dec"],dConv(acc))
			self.run()
			time.sleep(durata)

	def idle(self):

		self.write(r_add["DCOMcontrol"],[0,0])		# motore idle

	def begin(self,pos_lim, dummy = False):

		self.write(r_add["MBnode_guard"],[0,0])
		self.write(r_add["AccessExcl"],[0,1])
		self.write(r_add["PositiveLimit"],dConv(pos_lim))

		self.homing(120)
		self.run();
		
		#while read_bit(self.read(r_add['_DCOMstatus'],2),15) != 0:
		#	time.sleep(0.5)

		# self.idle()

	def print_errors(self):

		value = self.read(7184,2)
		if value is not None:
			r = utils.get_bits_from_int(value, val_size=32)

			print()
			print("\
		Bit 0: {} General error\n\
		Bit 1: {} Hardware limit switches (LIMP/LIMN/REF)\n\
		Bit 2: {} Out of range (software limit switches, tuning)\n\
		Bit 3: {} Quick Stop via fieldbus\n\
		Bit 4: {} Error in active operating mode\n\
		Bit 5: {} Commissioning interface (RS485)\n\
		Bit 6: {} Integrated fieldbus\n\
		Bit 7: {} Reserved\n\
		Bit 8: {} Following error\n\
		Bit 9: {} Reserved\n\
		Bit 10: {} Inputs STO are 0\n\
		Bit 11: {} Inputs STO different\n\
		Bit 12: {} Reserved\n\
		Bit 13: {} DC bus voltage low\n\
		Bit 14: {} DC bus voltage high\n\
		Bit 15: {} Mains phase missing\n\
		Bit 16: {} Integrated encoder interface\n\
		Bit 17: {} Overtemperature motor\n\
		Bit 18: {} Overtemperature power stage\n\
		Bit 19: {} Reserved\n\
		Bit 20: {} Memory card\n\
		Bit 21: {} Fieldbus module\n\
		Bit 22: {} Encoder module\n\
		Bit 23: {} Safety module eSM or module IOM1\n\
		Bit 24: {} Reserved\n\
		Bit 25: {} Reserved\n\
		Bit 26: {} Motor connection\n\
		Bit 27: {} Motor overcurrent/short circuit\n\
		Bit 28: {} Frequency of reference signal too high\n\
		Bit 29: {} EEPROM error detected\n\
		Bit 30: {} System start-up (hardware or parameter)\n\
		Bit 31: {} System error detected (for example, watchdog, internal hardware interface)\n\
			".format(*r))

