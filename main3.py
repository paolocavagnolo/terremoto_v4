from lib_modbus import *
from lib_terremoti import *
import time
import threading

import screeninfo
W = screeninfo.get_monitors()[0].width
H = screeninfo.get_monitors()[0].height
DEFAULT_IMAGE_SIZE = (W, H)

import pygame

DUMMY = False

# PYGAME STUFF

pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

BLUE = (45,45,250)
GREEN = (45,250,45)
RED = (250,45,45)

# GLOBAL VARIABLE

MAX_POS_X = 250000
MAX_POS_Y = 250000

# BUTTONS

sm_btn = pygame.image.load("imgs/sm_btn.jpg")
sm_btn = pygame.transform.scale(sm_btn, DEFAULT_IMAGE_SIZE)

norcia = pygame.image.load("imgs/norcia.jpg")
norcia = pygame.transform.scale(norcia, DEFAULT_IMAGE_SIZE)

norcia2 = pygame.image.load("imgs/norcia2.jpg")
norcia2 = pygame.transform.scale(norcia2, DEFAULT_IMAGE_SIZE)

mirandola = pygame.image.load("imgs/mirandola.png")
mirandola = pygame.transform.scale(mirandola, DEFAULT_IMAGE_SIZE)

NORCIA_BTN = pygame.Rect(W/5-97,H/2-85,213,202)
NORCIA2_BTN = pygame.Rect(W/5*2+24,H/2-90,208,197)
MIRANDOLA_BTN = pygame.Rect(W/5*3+144,H/2-87,218,207)

bg = sm_btn

# TEXT

font = pygame.font.Font('freesansbold.ttf', 50)
t_ready = font.render('CLICK TO START...', True, (0, 0, 0), (255, 255, 255))
t_go = font.render('SEQUENCE STARTED', True, (0, 0, 0), (255, 255, 255))

S = 0

tX = 0
tY = 0

# START MOTOR
X_driver = modbusDriver("10.0.0.205", 1, DUMMY)
Y_driver = modbusDriver("10.0.0.206", 1, DUMMY)
time.sleep(1)

X_driver.begin(MAX_POS_X+4000)
time.sleep(1)

Y_driver.begin(MAX_POS_Y+4000)
time.sleep(1)

run = True
hq_run = True
sequence = False

while run:

	if S == 0:
		hq_run = True
		sequence = False
		screen.blit(bg, (0, 0))
		pygame.draw.rect(screen, BLUE, NORCIA_BTN, 2)
		pygame.draw.rect(screen, BLUE, NORCIA2_BTN, 2)
		pygame.draw.rect(screen, BLUE, MIRANDOLA_BTN, 2)

	elif S == 1:
		screen.blit(bg, (0, 0))
		screen.blit(t_ready, (W/2-130, H/2))

	elif S == 2:
		screen.blit(bg, (0, 0))
		screen.blit(t_go, (W/2-130, H/2))

	elif S == 3:
		screen.blit(graph_X, (0, 0))

	elif S == 4:
		screen.blit(graph_Y, (0, 0))
		X_driver.idle()
		Y_driver.idle()


	for event in pygame.event.get():

		if event.type == pygame.MOUSEBUTTONDOWN:
			if event.button == 1:
				if S == 0:
					if NORCIA_BTN.collidepoint(event.pos):
						bg = norcia
						FILE_PATH = '../dati_terremoti/norcia'
						time_X, step_X, time_Y, step_Y = data_to_drive(FILE_PATH,True,MAX_POS_X,MAX_POS_Y)
						
						X_driver.moveTo(step_X[0],100,100)
						Y_driver.moveTo(step_Y[0],100,100)
						X_driver.run()
						Y_driver.run()

						S = 1

					elif NORCIA2_BTN.collidepoint(event.pos):
						bg = norcia2
						FILE_PATH = '../dati_terremoti/norcia_25km'
						time_X, step_X, time_Y, step_Y = data_to_drive(FILE_PATH,True,MAX_POS_X,MAX_POS_Y)
						
						X_driver.moveTo(step_X[0],100,100)
						Y_driver.moveTo(step_Y[0],100,100)
						X_driver.run()
						Y_driver.run()

						S = 1

					elif MIRANDOLA_BTN.collidepoint(event.pos):
						bg = mirandola
						FILE_PATH = '../dati_terremoti/mirandola'
						time_X, step_X, time_Y, step_Y = data_to_drive(FILE_PATH,True,MAX_POS_X,MAX_POS_Y)
						
						X_driver.moveTo(step_X[0],100,100)
						Y_driver.moveTo(step_Y[0],100,100)
						X_driver.run()
						Y_driver.run()

						S = 1

				elif S == 1:
					graph_X = pygame.image.load("imgs/graph_X.png")
					sequence = True
					screen.blit(bg, (0, 0))
					screen.blit(t_go, (W/2-130, H/2))
					S = 2

				elif S == 2:
					graph_X = pygame.image.load("imgs/graph_X.png")
					#graph_X = pygame.transform.scale(graph_X, DEFAULT_IMAGE_SIZE)
					S = 3

				elif S == 3:
					graph_Y = pygame.image.load("imgs/graph_Y.png")
					#graph_Y = pygame.transform.scale(graph_Y, DEFAULT_IMAGE_SIZE)
					S = 4

				elif S == 4:
					bg = sm_btn
					S = 0

		if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
			run = False

		if event.type == pygame.QUIT:
			run = False

	pygame.display.update()

	if sequence == True:

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
				sequence = False

pygame.quit()
