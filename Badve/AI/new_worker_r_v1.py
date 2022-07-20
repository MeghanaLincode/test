import requests
import glob
from inference_module import *
from config_module import *
import shutil
import json
from common_utils import *
import cv2
import time
import parameters
import os
import threading
# import cv2
from PIL import Image
import copy
import numpy as np

rch = CacheHelper()
opt = opt_config()
defects = opt.defects
def get_defect_list(detector_predictions):
	defect_list = []
	for i in detector_predictions:
		if i in defects:
			defect_list.append(i)
	return defect_list

length_result_px = []
length_result_mm = []
def measurement(path):
	#!/usr/bin/env python
	# coding: utf-8

	# In[25]:


	
	# path
	# path = r'D:/a/images/OD_Burr_day2123.jpg'
	# path = r'OD_Burr_day2137.jpg'

	# img_main = cv2.imread("/home/maini/main/cameraEngine/savedimages/measurement.jpg")
	# img_main = rch.get_json('measurement')
	img_main=CacheHelper().get_json('measurement')
	print('*******************measurement img',img_main.shape)
	gray_image = cv2.cvtColor(img_main, cv2.COLOR_BGR2GRAY)

	# c1_x1 = 0
	# c1_x2 = 100
	# c1_y1 = 200
	# c1_y2 = 350
	# c2_x1 = 550
	# c2_x2 = 630
	# c2_y1 = 200
	# c2_y2 = 350

	# c1_x1 = 43
	# c1_x2 = 71
	# c1_y1 = 260
	# c1_y2 = 320
	# c2_x1 = 563
	# c2_x2 = 598
	# c2_y1 = 249
	# c2_y2 = 303
	# c1_x1 = 16
	# c1_x2 = 50
	# c1_y1 = 259
	# c1_y2 = 310
	# c2_x1 = 549
	# c2_x2 = 590
	# c2_y1 = 271
	# c2_y2 = 325

	# c1_x1 = 22
	# c1_x2 = 53
	# c1_y1 = 261
	# c1_y2 = 310
	# c2_x1 = 544
	# c2_x2 = 603
	# c2_y1 = 255
	# c2_y2 = 339

	# cropped_image_left_main = img_main[c1_y1:c1_y2,c1_x1:c1_x2]
	
	# cropped_image_right_main = img_main[c2_y1:c2_y2,c2_x1:c2_x2]

	# # cv2.imshow('crop1', cropped_image_left_main)
	# # cv2.imshow('crop2', cropped_image_right_main)
	# # cv2.waitKey(0)

	# cropped_image_left = gray_image[c1_y1:c1_y2,c1_x1:c1_x2]
	# cropped_image_right = gray_image[c2_y1:c2_y2,c2_x1:c2_x2]
	# c1_x1 = 30
	# c1_x2 = 90
	# c1_y1 = 225
	# c1_y2 = 324
	# c2_x1 = 563
	# c2_x2 = 622
	# c2_y1 = 258
	# c2_y2 = 330


	c1_x1 = 14
	c1_x2 = 125
	c1_y1 = 257
	c1_y2 = 322
	c2_x1 = 520
	c2_x2 = 627
	c2_y1 = 271
	c2_y2 = 327


	cropped_image_left_main = img_main[c1_y1:c1_y2,c1_x1:c1_x2]
	cropped_image_right_main = img_main[c2_y1:c2_y2,c2_x1:c2_x2]


	cropped_image_left = gray_image[c1_y1:c1_y2,c1_x1:c1_x2]
	cropped_image_right = gray_image[c2_y1:c2_y2,c2_x1:c2_x2]
	
	calibration_mm = 46.3
	calibration_px = 530

	calibration_mm_per_px = calibration_mm / calibration_px

	
	x = 0
	y = 0
	w = 0
	h = 0
	ret,thresh1 = cv2.threshold(cropped_image_left,240,255,cv2.THRESH_BINARY)
	ret,thresh2 = cv2.threshold(cropped_image_right,210,255,cv2.THRESH_BINARY)

	edges1 = cv2.Canny(thresh1, 900,900)
	edges2 = cv2.Canny(thresh2, 900,900)


	# cv2.imshow('edge1', edges1)
	# cv2.imshow('edge2', edges2)
	# cv2.waitKey(0)

	vertical1 = np.copy(edges1)
	vertical2 = np.copy(edges2)
	# print(vertical1)

	rows1 = vertical1.shape[0]
	rows2 = vertical2.shape[0]

	verticalsize1 = rows1 // 8
	verticalsize2 = rows2 // 8

	verticalStructure1 = cv2.getStructuringElement(cv2.MORPH_RECT, (1, verticalsize1))
	verticalStructure2 = cv2.getStructuringElement(cv2.MORPH_RECT, (1, verticalsize2))

	vertical1 = cv2.erode(vertical1, verticalStructure1)
	vertical2 = cv2.erode(vertical2, verticalStructure2)

	vertical11 = cv2.dilate(vertical1, verticalStructure1)
	vertical12 = cv2.dilate(vertical2, verticalStructure2)
	# cv2.imshow('image1', vertical11)
	# cv2.imshow('image2', vertical12)

	# cv2.imshow('image11', thresh1)
	# cv2.imshow('image21', thresh2)

	# cv2.imshow('c1', cropped_image_left)
	# cv2.imshow('c2', cropped_image_right)

	# cv2.imshow('vertiical1', vertical11)
	# cv2.imshow('vertiical2', vertical12)
	# cv2.waitKey(0)

	contours,_= cv2.findContours(vertical11,cv2.RETR_TREE,cv2.CHAIN_APPROX_NONE)
	cv2.drawContours(cropped_image_left_main, contours, -1, (0,255,0), 2)
	contour_length = 0
	# print(len(contours))
	for contour in contours:
		# Find bounding rectangles
		
		# print(cv2.contourArea(contour),len(contour))
		if len(contour) > contour_length:
			contour_length = len(contour)
			x,y,w,h = cv2.boundingRect(contour)
			
		# Draw the rectangle
			cv2.rectangle(cropped_image_left_main,(x,y),(x+w,y+h),(255,255,0),1)
		
	# print()
	contours1,_= cv2.findContours(vertical12,cv2.RETR_TREE,cv2.CHAIN_APPROX_NONE)
	cv2.drawContours(cropped_image_right_main, contours1, 0, (0,255,0), 2)
	# cv2.imshow("img",vertical12)
	contour_length = 0

	x1 = 0
	y1 = 0
	w1 = 0
	h1 = 0
	# print(len(contours1))
	for contour1 in contours1:
		# Find bounding rectangles
		
		# Draw the rectangle
		# print(cv2.contourArea(contour1),len(contour1))
		if len(contour1) > contour_length:
			contour_length = len(contour1)
			x1,y1,w1,h1 = cv2.boundingRect(contour1)
			cv2.rectangle(cropped_image_right_main,(x1,y1),(x1+w1,y1+h1),(255,255,0),1)

	# print()

	center1 = ((x+(x+w))/2, (y+(y+h))/2)
	aa1 = int(center1[0])
	bb1 = int(center1[1])
	aaa1 = aa1+c1_x1
	bbb1 = bb1+c1_y1
	print(aaa1,bbb1)
	cv2.circle(img_main, (aaa1, bbb1), 5, (255,0,5), -1)

	center2 = ((x1+(x1+w1))/2, (y1+(y1+h1))/2)
	aa2 = int(center2[0])
	bb2 = int(center2[1])
	aaa2 = aa2+c2_x1
	bbb2 = bb2+c2_y1
	print(aaa2,bbb2)
	cv2.circle(img_main, (aaa2, bbb2), 5, (255,0,0), -1)



	cv2.line(img_main, (aaa1 ,bbb1), (aaa2 ,bbb2), (0,0,0), 3)
	result= ((((aaa2 - aaa1 )**2) + ((bbb2-bbb1)**2) )**0.5)
	length_result_px.append(result)
	length_result_mm.append(result*calibration_mm_per_px)
	print(length_result_px)
	print(length_result_mm)
	print(result)
	print(result*calibration_mm_per_px)
	cv2.imwrite("/home/maini/main/aiEngine/aiworker/results/measurement.jpg",img_main)
	cv2.imwrite(path+"/measurement.jpg",img_main)
	CacheHelper().set_json({'measurement_result':img_main})
	CacheHelper().set_json({'measurement_result_val':result*calibration_mm_per_px})
	# Show extracted vertical lines
	# cv2.imshow("vertical", cropped_image_left)
	# Show extracted vertical lines
	# cv2.imshow("vertical2", cropped_image_right)

	# cv2.imshow('left',edges1)
	# cv2.imshow('right',edges2)
	# cropped_image_right = img[535,223,599,327]
	#cv2.imwrite("l.jpg", cropped_image_left)
	# cv2.imwrite("r.jpg", cropped_image_right)
	#15, 223, 58, 125
	#544, 224, 47, 113

	# print(left_rect)
	# sketcher_rect = rect_img
	# cv2.imshow('image', img_main)
	# cv2.waitKey(0)  
	# cv2.destroyAllWindows()


## Getting inference frame
def predict_frame(input_image):
	
	with torch.no_grad():
		predictor = Inference()
		predictor.input_frame  = input_image
		predicted_frame, detector_predictions,cord  = predictor.dummy()
		print(detector_predictions)

		defect_list =  get_defect_list(detector_predictions)
	return predicted_frame,detector_predictions,cord

def save_inspection_per_view(current_inspection_id, counter, cam_id, part_name):
	r = requests.post(url="http://127.0.0.1:8000/livis/v1/inspection/save_results_per_view/",
					  data={"inspection_id" : str(current_inspection_id),
		"camera_view" : str(counter), "camera_index": cam_id, "part_name": part_name})
	return 0



######################################################################################################
mp  = MongoHelper().getCollection("workstations")
doc = mp.find_one({"workstation_name":"maini1"})
camera_list = doc["cameras"]
predictions_list = []
time_stamp_list = []
defect_list = ['burr','crack','scratch','dent']
while True:
	mp = MongoHelper().getCollection("current_inspection")
	doc = mp.find_one()
	#print(doc)
	if doc.get("current_inspection_id"):
		current_inspection_id = doc["current_inspection_id"]
		# CacheHelper.set_json{'current_inspection_id_backend':'current_inspection_id'}
		#print("process started")
	else:
		print("process not statrted")
		continue

	cam1_complete = rch.get_json('cam1_completed')
	cam2_complete = rch.get_json('cam2_completed')
	cam3_complete = rch.get_json('cam3_completed')
	cam4_complete = rch.get_json('cam4_completed')
	
	if not (cam1_complete and cam2_complete and cam3_complete and cam4_complete):
		continue

	start = datetime.datetime.now()
	rch.set_json({'backend_part_status':None})
	#folder creation logic
	main_path = '/home/maini/main/aiEngine/aiworker/results/'
	date_folder = datetime.datetime.now().strftime('%y_%m_%d')
	date_path = main_path + date_folder
	part_folder = datetime.datetime.now().strftime('%H_%M_%S')
	part_path = date_path+'/'+part_folder
	if not(os.path.exists(date_path)):
		os.mkdir(date_path)
	if not(os.path.exists(part_path)):
		os.mkdir(part_path)
	
	
	part_status = 'Accepted'
	part_status_list = []
	predictions_list = []
	defect_width = []
	CacheHelper().set_json({'Stage2_Status':"started"})
	for item in camera_list:
		for i in range(6):
			# time.sleep(1)
			part_name = "Housing_Component"
			input_frame_key = "cam"+item["camera_name"] + '_' + str(i)
			print(input_frame_key,'topic from worker')
			input_image = rch.get_json(input_frame_key)
			input_image1 = input_image.copy()
			#print(input_image.shape)
			# print(input_image.keys())
			predicted_frame,detector_predictions,cord = predict_frame(input_image)
			for j in detector_predictions:
				predictions_list.append(j)
			# predictions_list.append(detector_predictions)
			counter = int(item["camera_name"]) + i + (5*(int(item["camera_name"])-1))
			output_frame_key = "cam"+str(counter)+"_predicted_frame"
			output_frame_list = "cam"+str(counter)+"_predicted_list"
			output_frame_defect_widths = "cam"+str(counter)+"_predicted_widths"
			print("########\n\n")
			print(output_frame_key)
			# cv2.imwrite("/home/maini/main/aiEngine/aiworker/results/"+output_frame_key+'.jpg',predicted_frame)
			cv2.imwrite(part_path+'/'+input_frame_key+'.jpg',predicted_frame)
			out_folder_path = '/home/maini/main/aiEngine/aiworker/results/defects'
			print(cord)
			defect_width = {}
			for j in cord:
				print(j)
				for k,v in j.items():
					if k in defect_list:
						print('***************************Defect',k,v)
						# print("cam"+item["camera_name"]+'/'+  input_frame_key+'_'+datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')+'.jpg')
						# print(out_folder_path+'/'+k+'/'+ "cam"+item["camera_name"]+'/'+ input_frame_key+'_'+datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')+'.jpg')
						# print("cam"+item["camera_name"])
						# print(input_frame_key+'_')
						# print(datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')+'.jpg')
						cv2.imwrite(out_folder_path+'/'+k+'/'+ "cam"+item["camera_name"]+'/'+ input_frame_key+'_'+datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')+'.jpg',input_image1)
						cv2.imwrite(out_folder_path+'/'+k+'/'+ "cam"+item["camera_name"]+'/'+ input_frame_key+'_crop_'+datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')+'.jpg',input_image1[v[1]:v[3],v[0]:v[2]])
						if item['camera_name'] == 3:
							width_in_px = v[2]-v[0]
							print('width_in_px',width_in_px)
							#defect_width[k] = width_in_px
						else:
							width_in_px = v[3]-v[1]
							print('width_in_px',width_in_px)
						defect_width[k] = width_in_px
						# cropped_image_defect = input_image1[v[1]:v[3],v[0]:v[2]]
						# ret,thresh1 = cv2.threshold(cropped_image_defect,130,255,cv2.THRESH_BINARY)
						# # edges1 = cv2.Canny(thresh1, 600,600)
						# contours,_= cv2.findContours(thresh1,cv2.RETR_TREE,cv2.CHAIN_APPROX_NONE)
						# cv2.drawContours(cropped_image_defect, contours, -1, (0,255,0), 2)
						# for contour in contours:
						# 	# Find bounding rectangles
							
						# 	# Draw the rectangle
						# 	print(cv2.contourArea(contour),len(contour))
						# 	if len(contour) > contour_length:
						# 		contour_length = len(contour)
						# 		x,y,w,h = cv2.boundingRect(contour)
						# 		cv2.rectangle(cropped_image_defect,(x,y),(x+w,y+h),(255,255,0),1)
						# print('Width',w)
			CacheHelper().set_json({output_frame_key:predicted_frame})
			print("#########", defect_width)
			#CacheHelper().set_json({output_frame_defect_widths:defect_width})
			if "NA" in detector_predictions:
				part_name = ""
			CacheHelper().set_json({output_frame_list:detector_predictions})
			t1 = threading.Thread(target=save_inspection_per_view, args=(current_inspection_id, counter,item['camera_index'], part_name))
			t1.start()
			# r = requests.post(url="http://127.0.0.1:8000/livis/v1/inspection/save_results_per_view/",
			#data={"inspection_id" : str(current_inspection_id),
			#	 "camera_view" : str(counter), "camera_index": item['camera_index'], "part_name": part_name})

	measurement(part_path)
	CacheHelper().set_json({"Stage2_Status": ""})

	r = requests.post(url="http://127.0.0.1:8000/livis/v1/inspection/save_results/", data={"inspection_id": str(current_inspection_id)})
	CacheHelper().set_json({'Stage2_Status':""})
	data = r.json()
	is_accepted = data['data']
	print('Status', is_accepted)
	unique_list=[]
	print(defect_width)
	CacheHelper().set_json({'defect_width_list':defect_width})
	for x in predictions_list:
		# check if exists in unique_list or not
		if x not in unique_list:
			unique_list.append(x)
	print(predictions_list)
	print(unique_list)
	for i in unique_list:
		if i in parameters.rejected:
			part_status = 'Rejected'
			break
		elif i in parameters.rework:
			part_status = 'Rework'
		elif i in parameters.accepted:
			pass

	print('Backend Status',part_status)
	#CacheHelper().set_json({'Stage2_Status':part_status})
	#measurement(part_path)
	rch.set_json({'backend_part_status': is_accepted})
	rch.set_json({'cam1_completed': False})
	rch.set_json({'cam2_completed': False})
	rch.set_json({'cam3_completed': False})
	rch.set_json({'cam4_completed': False})
	
	d = datetime.datetime.now() - start
	time_stamp_list.append(str(d))
	print('\n\n\n\nend',d)
	print(time_stamp_list)

cv2.destroyAllWindows()