from lib_modbus import *
from lib_terremoti import *
import time
import threading

MAX_POS_X = 250000
MAX_POS_Y = 250000

try:

	FILE_PATH = '../dati_terremoti/norcia'
	time_X, step_X, time_Y, step_Y = data_to_drive(FILE_PATH,True,MAX_POS_X,MAX_POS_Y)

	X_driver = modbusDriver("10.0.0.205", 1)
	Y_driver = modbusDriver("10.0.0.206", 1)

	X_thread = threading.Thread(target=X_driver.moveList(), args=(step_X,time_X,), daemon=False)
	Y_thread = threading.Thread(target=Y_driver.moveList(), args=(step_Y,time_Y,), daemon=False)

	input('Begin:')
	X_driver.begin(MAX_POS_X+4000)
	Y_driver.begin(MAX_POS_Y+4000)

	input('Max distance:')
	X_driver.moveTo(MAX_POS_X,5000,1000)
	Y_driver.moveTo(MAX_POS_Y,5000,1000)
	X_driver.run()
	Y_driver.run()

	input('Begin Sequence Position:')
	X_driver.moveTo(step_X[0],5000,1000)
	Y_driver.moveTo(step_Y[0],5000,1000)
	X_driver.run()
	Y_driver.run()

	input('Move List:')
	X_thread.start()
	Y_thread.start()

	input('End:')
	X_driver.idle()
	Y_driver.idle()
	X_driver.client.close()
	Y_driver.client.close()


except KeyboardInterrupt:
	print("ciao")
	exit()