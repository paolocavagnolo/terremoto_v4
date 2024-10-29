from lib_modbus import *
from lib_terremoti import *
import time
import threading

import pygame

DUMMY = True

# PYGAME STUFF

pygame.init()
W = 1366
H = 768
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

BLUE = (45,45,250)
GREEN = (45,250,45)
RED = (250,45,45)

# GLOBAL VARIABLE

MAX_POS_X = 250000
MAX_POS_Y = 250000

# BUTTONS

NORCIA_BTN = pygame.Rect(W/6*2-50,H/3,200,100)
NORCIA_25KM_BTN = pygame.Rect(W/6*3-50,H/3,200,100)
MIRANDOLA_BTN = pygame.Rect(W/6*4-50,H/3,200,100)

screen.fill((120,120,120))

pygame.draw.rect(screen, BLUE, NORCIA_BTN, 1)
pygame.draw.rect(screen, BLUE, NORCIA_25KM_BTN, 1)
pygame.draw.rect(screen, BLUE, MIRANDOLA_BTN, 1)

font = pygame.font.Font('freesansbold.ttf', 26)

textX1 = font.render('NORCIA', True, (0,0,0))
textX2 = font.render('NORCIA_25km', True, (0,0,0))
textX3 = font.render('MIRANDOLA', True, (0,0,0))

screen.blit(textX1, (W/6*2-50+10,H/2-25+13))
screen.blit(textX2, (W/6*3-50+5,H/2-25+13))
screen.blit(textX3, (W/6*4-50+5,H/2-25+13))

pygame.display.update()

FILE_PATH = '../dati_terremoti/norcia'
time_X, step_X, time_Y, step_Y = data_to_drive(FILE_PATH,False,MAX_POS_X,MAX_POS_Y)

# CLEAN FROM DUPLICATE
otX = -1
otY = -1

clean_time_X = []
clean_step_X = []

for i in range(len(time_X)):

	if time_X[i] != otX:
		clean_time_X.append(time_X[i])
		clean_step_X.append(step_X[i])

	otX = time_X[i]

clean_time_Y = []
clean_step_Y = []

for i in range(len(time_Y)):

	if time_Y[i] == otY:
		clean_time_Y.append(time_Y[i])
		clean_step_Y.append(step_Y[i])

	otY =  time_Y[i]


time_X = clean_time_X
time_Y = clean_time_Y
step_X = clean_step_X
step_Y = clean_step_Y

X_driver = modbusDriver("10.0.0.205", 1, False)
Y_driver = modbusDriver("10.0.0.206", 1, False)

tX = 0
tY = 0

run = True
hq_run = True
while run:
	for event in pygame.event.get():
		if event.type == pygame.MOUSEBUTTONDOWN:
			if event.button == 1:
				if HOME_BTN.collidepoint(event.pos):

					X_driver.begin(MAX_POS_X+4000)
					Y_driver.begin(MAX_POS_Y+4000)
					X_driver.moveTo(0,5000,1000)
					Y_driver.moveTo(0,5000,1000)
					X_driver.run()
					Y_driver.run()

				elif MAXD_BTN.collidepoint(event.pos):

					X_driver.moveTo(MAX_POS_X,5000,1000)
					Y_driver.moveTo(MAX_POS_Y,5000,1000)
					X_driver.run()
					Y_driver.run()

				elif INIT_BTN.collidepoint(event.pos):

					X_driver.moveTo(step_X[0],5000,1000)
					Y_driver.moveTo(step_Y[0],5000,1000)
					X_driver.run()
					Y_driver.run()

				elif GOOO_BTN.collidepoint(event.pos):

					X_driver.write(r_add["DCOMopmode"],[0,1])
					Y_driver.write(r_add["DCOMopmode"],[0,1])

					iX = 0
					iY = 0

					endX = False
					endY = False

					durata_X = 0
					durata_Y = 0

					while hq_run:

						# X COORDINATE
						if iX < len(time_X):
							if ((time.time() - tX) > durata_X):

								step_X[iX] = int(step_X[iX])
								time_X[iX] = float(time_X[iX])

								dist = abs(step_X[iX] - step_X[iX-1])
								durata_X = float(time_X[iX] - time_X[iX-1])
								pos_to_rev = dist / STEP_REV 			# [rev]
								vel = int(pos_to_rev / (durata_X / 60)) * 2 	# [rpm]
								acc = int(vel / (durata_X / 2))				# [rpm/s]

								X_driver.write(r_add["PPp_target"],dConv(step_X[iX]))
								X_driver.write(r_add["PPv_target"],dConv(vel))
								X_driver.write(r_add["RAMP_v_acc"],dConv(acc))
								X_driver.write(r_add["RAMP_v_dec"],dConv(acc))

								tX = time.time()

								X_driver.run()

								iX += 1
						else:
							endX = True


						# Y COORDINATE
						if iY < len(time_Y):
							if ((time.time() - tY) > durata_Y):
								step_Y[iY] = int(step_Y[iY])
								time_Y[iY] = float(time_Y[iY])

								dist = abs(step_Y[iY] - step_Y[iY-1])
								durata_Y = float(time_Y[iY] - time_Y[iY-1])
								pos_to_rev = dist / STEP_REV 			# [rev]
								vel = int(pos_to_rev / (durata_Y / 60)) * 2 	# [rpm]
								acc = int(vel / (durata_Y / 2))				# [rpm/s]

								Y_driver.write(r_add["PPp_target"],dConv(step_Y[iY]))
								Y_driver.write(r_add["PPv_target"],dConv(vel))
								Y_driver.write(r_add["RAMP_v_acc"],dConv(acc))
								Y_driver.write(r_add["RAMP_v_dec"],dConv(acc))

								tY = time.time()

								Y_driver.run()

								iY += 1
						else:
							endY = True

						if endY and endX:
							hq_run = False
						

		if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
			run = False

		if event.type == pygame.QUIT:
			run = False

pygame.quit()
X_driver.idle()
Y_driver.idle()
X_driver.client.close()
Y_driver.client.close()
