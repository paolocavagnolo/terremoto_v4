import matplotlib.pyplot as plt
import numpy as np

#FILE_PATH			= 'dati_terremoti/dato_N_NORCIA.txt'

MIN_SAMPLE_TIME 	= 0.1 	# s
MIN_SAMPLE_DISTANCE = 0.3  	# cm

TIME_WINDOW_BEFORE 	= 25 	# s
TIME_WINDOW_AFTER 	= 35 	# s


def data_to_drive(FILE_PATH, PLOT, MX, MY):

	path_N = FILE_PATH + "/dato_N.txt"
	path_E = FILE_PATH + "/dato_E.txt"

	with open(path_N,'r') as f:
		hq_data_N = f.readlines()

	with open(path_E,'r') as f:
		hq_data_E = f.readlines()

	t_raw_temp = []
	s_raw_temp_N = []
	s_raw_temp_E = []

	for line in hq_data_N:
		line_values = line.strip().split(' ')
		t_raw_temp.append(float(line_values[0]))
		s_raw_temp_N.append(float(line_values[1]))

	for line in hq_data_E:
		line_values = line.strip().split(' ')
		s_raw_temp_E.append(float(line_values[1]))

	max_raw = max(s_raw_temp_N)
	min_raw = min(s_raw_temp_N)

	if abs(max_raw) > abs(min_raw):
		t_center = t_raw_temp[s_raw_temp_N.index(max_raw)]
	else:
		t_center = t_raw_temp[s_raw_temp_N.index(min_raw)]

	if (t_center - t_raw_temp[0]) > TIME_WINDOW_BEFORE:
		START_TIME = t_center - TIME_WINDOW_BEFORE
	else:
		START_TIME = t_raw_temp[0]

	if t_raw_temp[-1] - t_center > TIME_WINDOW_AFTER:
		END_TIME = t_center + TIME_WINDOW_AFTER
	else:
		END_TIME = t_raw_temp[-1]

	t_raw = []
	s_raw_N = []
	s_raw_E = []

	for i in range(len(t_raw_temp)):
		if t_raw_temp[i] >= (START_TIME) and t_raw_temp[i] <= END_TIME:
			t_raw.append(t_raw_temp[i] - START_TIME )
			s_raw_N.append(s_raw_temp_N[i])

	for i in range(len(t_raw_temp)):
		if t_raw_temp[i] >= START_TIME and t_raw_temp[i] <= END_TIME:
			s_raw_E.append(s_raw_temp_E[i])

	step_X, time_X = raw_to_poi(t_raw, s_raw_N, MX, PLOT, "X")
	step_Y, time_Y = raw_to_poi(t_raw, s_raw_E, MY, PLOT, "Y")

	return time_X, step_X, time_Y, step_Y

def raw_to_poi(t_raw, s_raw, MAX_STEPS, PLOT, name):

	# FIND MIN-MAX ALL POINTS OF INTEREST

	dx 	= 0
	odx = 0
	mms = []
	mmt = []

	# add first point
	mms.append(s_raw[0])
	mmt.append(t_raw[0])

	for i in range(1,len(s_raw)-1):

		found = False

		dx = (s_raw[i+1] - s_raw[i])
		if (dx > 0):
			if (odx <= 0):
				found = True
		elif (dx < 0):
			if (odx >= 0):
				found = True

		if found:
			mms.append(s_raw[i])
			mmt.append(t_raw[i])

		odx = dx

	# FILTERED POINTS OF INTEREST

	mms_f = []
	mmt_f = []

	# add first point
	mms_f.append(mms[0])
	mmt_f.append(mmt[0])

	def square_dist(x1,y1,x2,y2):
		return np.sqrt((x2-x1)**2 + (y2-y1)**2) # VERSIONE 1

	def dist(y2,x2,y1,x1):
		# return np.sqrt((x2-x1)**2 + (y2-y1)**2) # VERSIONE 1
		dx = abs(x2 - x1)
		dy = abs(y2 - y1)
		vel = dy/dx

		if dx > 0.1:
			if dy > 0.5:
				if vel < 40:
					return 1

		return 0

	for i in range(1,len(mms)):

		dps = dist(mms[i],mmt[i],mms[i-1],mmt[i-1])

		if dps:
			mms_f.append(mms[i])
			mmt_f.append(mmt[i])


	## RE ALIGN ALL POINTS TO CHECK MAX-MIN

	mmt_f_new = [mmt_f[0]]
	mms_f_new = [mms_f[0]]

	for a in range(len(mmt_f)-2):

		b = a + 1
		c = a + 2

		start_time = mmt_f[a]
		end_time = mmt_f[c]

		start_idx = t_raw.index(start_time)
		end_idx = t_raw.index(end_time)

		s_min = min(s_raw[start_idx:end_idx+1])
		s_max = max(s_raw[start_idx:end_idx+1])

		t_min = t_raw[s_raw[start_idx:end_idx+1].index(s_min)+start_idx]
		t_max = t_raw[s_raw[start_idx:end_idx+1].index(s_max)+start_idx]

		tB = mmt_f[b]
		sB = mms_f[b]

		tC1 = t_min
		sC1 = s_min

		tC2 = t_max
		sC2 = s_max

		d1 = square_dist(tC1,sC1,tB,sB)
		d2 = square_dist(tC2,sC2,tB,sB)

		if d1 < d2:
			mmt_f[b] = tC1
			mms_f[b] = sC1
		else:
			mmt_f[b] = tC2
			mms_f[b] = sC2

	## add last points to return 0

	mms_f.append(0.0)
	mmt_f.append(mmt_f[-1]+2.0)

	# PRINT DEF VALUES

	MAX_S_STEP 	= MAX_STEPS
	MAX_S_CM	= 14.5
	STEP_CM 	= MAX_S_STEP / MAX_S_CM # [step/cm] 200000 steps for 20 cm

	max_s = max(mms_f)
	min_s = min(mms_f)

	space_range = abs(max_s - min_s)

	while space_range > MAX_S_CM:
		#print("INFO: space_range greater then " + str(MAX_S_CM) + " cm")

		if abs(min_s) > abs(max_s):
			idx = mms_f.index(min_s)
		else:
			idx = mms_f.index(max_s)
		
		mms_f[idx] = mms_f[idx]*0.8

		max_s = max(mms_f)
		min_s = min(mms_f)

		space_range = abs(max_s - min_s)

	# rescale

	MID = min_s + space_range / 2
	REF = MAX_S_CM / 2

	s_raw_r = []
	mms_f_r = []

	for i in range(len(s_raw)):
		s_raw_r.append(REF + (s_raw[i]-MID))

	for i in range(len(mms_f)):
		mms_f_r.append(REF + (mms_f[i]-MID))

	pos_step = [STEP_CM * e for e in mms_f_r]


	if PLOT:
		fig, ax1 = plt.subplots()
		plt.title(name + " movement")

		ax1.plot(t_raw,s_raw)
		ax1.plot(mmt_f,mms_f,'.y')

		plt.xlabel("time (s)")
		plt.ylabel("move (cm)")
		
		plt.savefig('imgs/graph_' + name + '.png', dpi=160)

	# CLEAN FROM DUPLICATE
	ot = -1

	clean_time = []
	clean_step = []

	for i in range(len(mmt_f)):

		if mmt_f[i] != ot:
			clean_time.append(mmt_f[i])
			clean_step.append(pos_step[i])

		ot = mmt_f[i]

	mmt_f = clean_time
	pos_step = clean_step

	return pos_step, mmt_f
