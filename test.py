from libs import *
import time


# SOMOVE
## 17418 - 0 (manual)
## 


try:

	# CONFIG X DRIVER
	print("\n\n\nINITIALIZE X DRIVER\n")
	X_driver = modbusDriver("10.0.0.205", 1)

	X_driver.write(r_add["MBnode_guard"],[0,0]) # Test with 1000?	
	X_driver.write(r_add["AccessExcl"],[0,1])

	# TEST 1 - Leggi registro stato macchina

	X_DCOMstatus = X_driver.read(r_add["_DCOMstatus"],2)

	if (read_bit(X_DCOMstatus,15) == 0):
		print("\n\n\nPERFORM HOMING\n")
		X_driver.perform_homing(120)

	# TEST 3 - Numeri e posizioni

	maxPos = 200000
	minPos = 0

	loop = True

	motor = X_driver

	while loop:

		# disabilito motori
		motore.idle()

		c = input('>')

		if c == 'p':
			p = motor.read(r_add["_p_act"],2)

			print(p)

		if c == 'i':
			print("indietro")
			pos = motor.read(r_add["_p_act"],2)

			if (pos - STEP_REV) >= 0:
				motor.moveTo(pos - STEP_REV, 100, 100)

		if c == 'a':
			print("avanti")
			pos = motor.read(r_add["_p_act"],2)

			if (pos + STEP_REV) <= maxPos:
				motor.moveTo(pos + STEP_REV, 100, 100)

		if c == 'A':
			motor.moveTo(maxPos, 100, 100)

		if c == 'I':
			motor.moveTo(minPos, 100, 100)

		if c == 'h':
			motor.perform_homing(60)

		if c == 'L':
			for i in range(10):
				motor.moveRamp(maxPos,abs(maxPos-minPos),3)
				time.sleep(3)
				motor.moveRamp(minPos,abs(maxPos-minPos),3)
				time.sleep(3)

		if c == 'l':
			for i in range(5):
				motor.moveRamp(maxPos,abs(maxPos-minPos),1)
				time.sleep(1)
				motor.moveRamp(minPos,abs(maxPos-minPos),1)
				time.sleep(1)

		if c == 's':

			pp = [maxPos,minPos,maxPos,minPos,maxPos,minPos]
			tt = [1,1,1,1,1,1]

			motor.moveListRamp(pp,tt)

		if c == 'e':
			motor.print_errors()

		if c == 'q':
			loop = False
			print("ciao")


except KeyboardInterrupt:
	print("ciao")
	exit()