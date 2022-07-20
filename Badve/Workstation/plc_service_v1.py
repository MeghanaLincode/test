import plc_controller
# import config
import time
import datetime
import requests
import redis

import json
import numpy as np
import datetime
from bson import ObjectId
import os
import sys
import multiprocessing
# from datetime import datetime
import pickle
import requests
from common_utils import *

plc_ip = '192.168.1.20'


def singleton(cls):
    instances = {}
    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return getinstance

@singleton
class MongoHelper:
    client = None
    def __init__(self):
        if not self.client:
            self.client = MongoClient(host='localhost', port=27017)

        self.db = self.client[settings.MONGO_DB]
        # if settings.DEBUG:
            # self.db.set_profiling_level(2)
        # placeholder for filter
    """
    def getDatabase(self):
        return self.db
    """

    def getCollection(self, cname, create=False, codec_options=None):
        _DB = "LIVIS"
        DB = self.client[_DB]
        return DB[cname]

@singleton
class CacheHelper():
    def __init__(self):
        self.redis_cache = redis.StrictRedis(host="localhost", port="6379", db=0, socket_timeout=1)
        print("REDIS CACHE UP!")

    def get_redis_pipeline(self):
        return self.redis_cache.pipeline()
    
    #should be {'key'  : 'value'} always
    def set_json(self, k, v):
        try:
            #k, v = list(dict_obj.items())[0]
            v = pickle.dumps(v)
            return self.redis_cache.set(k, v)
        except redis.ConnectionError:
            return None

    def get_json(self, key):
        try:
            temp = self.redis_cache.get(key)
            #print(temp)\
            if temp:
                temp= pickle.loads(temp)
            return temp
        except redis.ConnectionError:
            return None
        return None

    def execute_pipe_commands(self, commands):
        #TBD to increase efficiency can chain commands for getting cache in one go
        return None

class air_gauge_calibration():
    def __init__(self):
        self.coll_name = "air_gauge_value_setting"
        self.get_value()

    def get_value(self):
        self.mp_air = MongoHelper().getCollection(self.coll_name)
        self.data = self.mp_air.find_one()
        self.air_id = self.data["_id"]
        self.raw_20_t_mm_min = int(self.data["raw_20_t_mm_min"])#7267
        self.raw_20_t_mm_max = int(self.data["raw_20_t_mm_max"])#4502

        self.raw_20_b_mm_min = int(self.data["raw_20_b_mm_min"])#6256
        self.raw_20_b_mm_max = int(self.data["raw_20_b_mm_max"])#4246 

        self.raw_18mm_min    = int(self.data["raw_18mm_min"])#7053
        self.raw_18mm_max    = int(self.data["raw_18mm_max"])#3460

        self.ref_20_t_mm_min = float(self.data["ref_20_t_mm_min"])#20.742
        self.ref_20_t_mm_max = float(self.data["ref_20_t_mm_max"])#20.811

        self.ref_20_b_mm_min = float(self.data["ref_20_b_mm_min"])#20.741
        self.ref_20_b_mm_max = float(self.data["ref_20_b_mm_max"])#20.806

        self.ref_18mm_min    = float(self.data["ref_18mm_min"])#18.352
        self.ref_18mm_max    = float(self.data["ref_18mm_max"])#18.424

        print(self.raw_20_t_mm_min, self.raw_20_t_mm_max)
        print(self.raw_20_b_mm_min, self.raw_20_b_mm_max)
        print(self.raw_18mm_min,    self.raw_18mm_max)
        print(self.ref_20_t_mm_min, self.ref_20_t_mm_max)
        print(self.ref_20_b_mm_min, self.ref_20_b_mm_max)
        print(self.ref_18mm_min,    self.ref_18mm_max)

        # data = [self.raw_20_t_mm_min, self.raw_20_t_mm_max,self.raw_20_b_mm_min, self.raw_20_b_mm_max,self.raw_18mm_min,    self.raw_18mm_max,
        #         self.ref_20_t_mm_min, self.ref_20_t_mm_max,self.ref_20_b_mm_min, self.ref_20_b_mm_max,self.ref_18mm_min,    self.ref_18mm_max]
        # return data

    def update_value(self,colle):
        self.coll_name = "air_gauge_value_setting"
        self.mp_air = MongoHelper().getCollection(self.coll_name)
        self.data = self.mp_air.find_one()
        self.air_id = data["_id"]
        self.mp_air.update({'_id' : ObjectId(self.air_id)}, {"$set" : colle})

def reset():
    CacheHelper().set_json('Modbus Status',False)
    CacheHelper().set_json('cam1_completed',False)
    CacheHelper().set_json('cam2_completed',False)
    CacheHelper().set_json('cam3_completed',False)
    CacheHelper().set_json('cam4_completed',False)
    CacheHelper().set_json('measurement_complete',False)
    CacheHelper().set_json('measure_length',False)
    CacheHelper().set_json('cam1_Start_Insp',False)
    CacheHelper().set_json('cam2_Start_Insp',False)
    CacheHelper().set_json('cam3_Start_Insp',False)
    CacheHelper().set_json('cam4_Start_Insp',False)
    CacheHelper().set_json('Trigger_cam1',False)
    CacheHelper().set_json('Trigger_cam2',False)
    CacheHelper().set_json('Trigger_cam3',False)
    CacheHelper().set_json('Trigger_cam4',False)

def get_current_inspection_id():
    while 1:
        mp = MongoHelper().getCollection("current_inspection")
        doc = mp.find_one()
        if doc.get("current_inspection_id"):
            current_inspection_id = doc["current_inspection_id"]
            return current_inspection_id
        else:
            time.sleep(0.1)
            print(datetime.datetime.now(),"process not started")
            continue

class plc():
    # ip = '192.168.1.20'
    def __init__(self,ip):
        self.wrong = 65152
        self.total_count = 6

        self.stage2_trigger_address  = 8394
        self.stage1_trigger_address  = 8192 + 100
        self.stage1_accepted         = 8192 + 255
        self.stage1_rejected         = 8192 + 256
        self.stage1_rework           = 8192 + 262
        self.stage2_accepted         = 8192 + 105
        self.stage2_rejected         = 8192 + 502
        self.stage2_rework           = 8192 + 503
        self.stage1_inspected        = 8192 + 252
        self.stage2_length_trigger   = 8192 + 600#rakshith to be modified

        print('PLC',ip)
        CacheHelper().set_json('Modbus Status',None)
        self.controller = plc_controller.ModbusController()
        status = self.controller.connect(ip,mode='TCP')

        if not status:
            CacheHelper().set_json('Modbus Status',False)
            sys.exit(0)
        CacheHelper().set_json('Modbus Status',True)
        self.air_gauge_calibration_data = air_gauge_calibration()
        self.old_trig_length = 0
        self.old_trig = 0
        self.old_trig1 = 0
        self.controller.write_coil(self.stage2_trigger_address,False)
        self.old_part_status = None
        self.previous_stage1_status = None
        self.stage1_status = None
        self.live_execution()

    def calibrate_air_gauge(self):
        air_gauge_position = CacheHelper().get_json('air_gauge_position')
        # print('Calibrating',air_gauge_position)
        if air_gauge_position=='Lower':
            colle = {
                'raw_20_t_mm_min':CacheHelper().get_json("internal_air_guage_a3"),
                'raw_20_b_mm_min':CacheHelper().get_json("internal_air_guage_a1"),
                'raw_18mm_min':CacheHelper().get_json("internal_air_guage_a2")
            }
            # mp_air.update({'_id' : ObjectId(air_id)}, {"$set" : colle})
            self.air_gauge_calibration_data.update_value(colle)
        elif air_gauge_position=='Higher':
            colle = {
                'raw_20_t_mm_max':CacheHelper().get_json("internal_air_guage_a3"),
                'raw_20_b_mm_max':CacheHelper().get_json("internal_air_guage_a1"),
                'raw_18mm_max':CacheHelper().get_json("internal_air_guage_a2")
            }
            # mp_air.update({'_id' : ObjectId(air_id)}, {"$set" : colle})
            self.air_gauge_calibration_data.update_value(colle)
        self.air_gauge_calibration_data.get_value()
        CacheHelper().set_json("is_edited",False)
        CacheHelper().set_json("air_gauge_position",None)

    def verify_air_gauge(self,analog1_data,analog2_data,analog3_data):
        print(len(analog1_data),len(analog2_data),len(analog3_data))
        if len(analog1_data)==0 or len(analog2_data)==0 or len(analog3_data)==0:
            print('------------------Air guage inspection not done')
            return None,"No_Inspection"
        a1_final = analog1_data[int(len(analog1_data)/2)]
        a2_final = analog2_data[int(len(analog2_data)/2)]
        a3_final = analog3_data[int(len(analog3_data)/2)]
        CacheHelper().set_json("internal_air_guage_a1",a1_final)
        CacheHelper().set_json("internal_air_guage_a2",a2_final)
        CacheHelper().set_json("internal_air_guage_a3",a3_final)
        # print('analog1 final',a1_final)
        # print('analog2 final',a2_final)
        # print('analog3 final',a3_final)
        print('a1 calculation')
        print(a1_final,self.air_gauge_calibration_data.raw_20_b_mm_min,self.air_gauge_calibration_data.ref_20_b_mm_max,self.air_gauge_calibration_data.ref_20_b_mm_min,self.air_gauge_calibration_data.raw_20_b_mm_max,self.air_gauge_calibration_data.raw_20_b_mm_min,self.air_gauge_calibration_data.ref_20_b_mm_min)
        print((a1_final-self.air_gauge_calibration_data.raw_20_b_mm_min),(self.air_gauge_calibration_data.ref_20_b_mm_max-self.air_gauge_calibration_data.ref_20_b_mm_min),(self.air_gauge_calibration_data.raw_20_b_mm_max-self.air_gauge_calibration_data.raw_20_b_mm_min),self.air_gauge_calibration_data.ref_20_b_mm_min)
        print('a2_calculation')
        print(a2_final,self.air_gauge_calibration_data.raw_18mm_min,self.air_gauge_calibration_data.ref_18mm_max,self.air_gauge_calibration_data.ref_18mm_min,self.air_gauge_calibration_data.raw_18mm_max,self.air_gauge_calibration_data.raw_18mm_min,self.air_gauge_calibration_data.ref_18mm_min)
        print((a2_final-self.air_gauge_calibration_data.raw_18mm_min),(self.air_gauge_calibration_data.ref_18mm_max-self.air_gauge_calibration_data.ref_18mm_min),(self.air_gauge_calibration_data.raw_18mm_max-self.air_gauge_calibration_data.raw_18mm_min),self.air_gauge_calibration_data.ref_18mm_min)
        print('a3_calculation')
        print(a3_final,self.air_gauge_calibration_data.raw_20_t_mm_min,self.air_gauge_calibration_data.ref_20_t_mm_max,self.air_gauge_calibration_data.ref_20_t_mm_min,self.air_gauge_calibration_data.raw_20_t_mm_max,self.air_gauge_calibration_data.raw_20_t_mm_min,self.air_gauge_calibration_data.ref_20_t_mm_min)
        print((a3_final-self.air_gauge_calibration_data.raw_20_t_mm_min),(self.air_gauge_calibration_data.ref_20_t_mm_max-self.air_gauge_calibration_data.ref_20_t_mm_min),(self.air_gauge_calibration_data.raw_20_t_mm_max-self.air_gauge_calibration_data.raw_20_t_mm_min),self.air_gauge_calibration_data.ref_20_t_mm_min)
        a1_calculated = round(((a1_final-self.air_gauge_calibration_data.raw_20_b_mm_min)*(self.air_gauge_calibration_data.ref_20_b_mm_max-self.air_gauge_calibration_data.ref_20_b_mm_min)/(self.air_gauge_calibration_data.raw_20_b_mm_max-self.air_gauge_calibration_data.raw_20_b_mm_min))+self.air_gauge_calibration_data.ref_20_b_mm_min,3)
        a2_calculated = round(((a2_final-self.air_gauge_calibration_data.raw_18mm_min)*(self.air_gauge_calibration_data.ref_18mm_max-self.air_gauge_calibration_data.ref_18mm_min)/(self.air_gauge_calibration_data.raw_18mm_max-self.air_gauge_calibration_data.raw_18mm_min))+self.air_gauge_calibration_data.ref_18mm_min,3)
        a3_calculated = round(((a3_final-self.air_gauge_calibration_data.raw_20_t_mm_min)*(self.air_gauge_calibration_data.ref_20_t_mm_max-self.air_gauge_calibration_data.ref_20_t_mm_min)/(self.air_gauge_calibration_data.raw_20_t_mm_max-self.air_gauge_calibration_data.raw_20_t_mm_min))+self.air_gauge_calibration_data.ref_20_t_mm_min,3)
        print('20mm B cal',a1_calculated)
        print('18mm   cal',a2_calculated)
        print('20mm T cal',a3_calculated)
        CacheHelper().set_json('20mm_B',a1_calculated)
        CacheHelper().set_json('18mm',a2_calculated)
        CacheHelper().set_json('20mm_T',a3_calculated)
        reject_reasons = ""
        #rakshith:modifications : fetch air gauge master min and max from DB
        print((a1_calculated >= 20.745 ),( a1_calculated <= 20.807) , (a3_calculated >= 20.745 ), (a3_calculated <= 20.807) , (a2_calculated >= 18.359 ),(a2_calculated <= 18.421),(a1_calculated >= 20.745 and a1_calculated <= 20.807),(a3_calculated >= 20.745 and a3_calculated <= 20.807),(a2_calculated >= 18.359 and a2_calculated <= 18.421))
        if (a1_calculated >= 20.745 and a1_calculated <= 20.807) and (a3_calculated >= 20.745 and a3_calculated <= 20.807) and (a2_calculated >= 18.359 and a2_calculated <= 18.421) :
        
            CacheHelper().set_json('Stage1_Status','Accepted')
            stage1_status = "Accepted"
            time.sleep(1)
            self.controller.write_coil(self.stage1_accepted,True)
            self.previous_stage1_status = 'Accepted'
            print('Stage1  air gauge Accepted')
        else:
            time.sleep(1)
            
            if a1_calculated < 20.745 or a3_calculated < 20.745:
                reject_reasons += ",20_Undersize"
                print('20.8 Undersize')
            if a1_calculated > 20.807 or a3_calculated > 20.807:
                reject_reasons += ",20_Oversize"
                print('20.8 Oversize')
            if a2_calculated < 18.359:
                reject_reasons += ",18_Undersize"
                print('18 Undersize')
            if a2_calculated > 18.421:
                reject_reasons += ",18_Oversize"
                print('18 Oversize')
            
            self.previous_stage1_status = None
            if 'Oversize' in reject_reasons:
                self.controller.write_coil(stage1_rejected,True)
                self.previous_stage1_status = 'Rejected'
                print('Stage1 air gauge Rejected')
                CacheHelper().set_json('Stage1_Status','Rejected')
                stage1_status = "Rejected"
                
            else :
                self.controller.write_coil(self.stage1_rework,True)
                self.previous_stage1_status = 'Rework'
                print('Stage1 air gauge Rework')
                CacheHelper().set_json('Stage1_Status','Rework')
                stage1_status = "Rework"

        return stage1_status,reject_reasons

    def live_execution(self):
        while 1:
            # while 1:
            current_inspection_id = get_current_inspection_id()
            calibration_save = CacheHelper().get_json("is_edited")
            if calibration_save:
                self.calibrate_air_gauge()
            
            # is_calibrate = CacheHelper().get_json('is_calibrate')
            # if is_calibrate:
            #     self.controller.write_coil(self.stage1_inspected,0)

            trig_length = self.controller.read_coil(self.stage2_length_trigger)
            if trig_length == 1 and self.old_trig_length == 0:
                print('Trigger Length High')
                # time.sleep(5)
                CacheHelper().set_json('measure_length',True)
                self.old_trig_length = 1
            elif trig_length == 0 and self.old_trig_length == 1:
                print('Trigger Length Low')
                self.old_trig_length = 0

            if CacheHelper().get_json('measurement_complete'):
                self.controller.write_coil(self.stage2_length_trigger,0)
                CacheHelper().set_json('measurement_complete',False)

            trig = self.controller.read_coil(self.stage2_trigger_address)
            if trig == 1 and self.old_trig == 0:
                print('Trig High')
                CacheHelper().set_json("current_inspection_status", "started")
                CacheHelper().set_json('cam1_Start_Insp',True)
                CacheHelper().set_json('cam2_Start_Insp',True)
                CacheHelper().set_json('cam3_Start_Insp',True)
                CacheHelper().set_json('cam4_Start_Insp',True)
                self.old_trig = 1
            elif trig == 0 and self.old_trig == 1:
                self.old_trig = 0
                print('Trig Low')
                # trigger = 1

            trig1 = self.controller.read_coil(self.stage1_trigger_address)
            if trig1 == 1 and self.old_trig1 == 0:
                print('****************************************Trig1 High')
                if self.stage1_status != None and self.stage1_status != "Accepted":
                    #rakshith : to be verified 
                    # if self.controller.read_coil(self.stage2_rejected)==True or self.controller.read_coil(self.stage2_rework) == True:
                        print('*******************************************************************************')
                        print('Vision not running due to Stage1 Reject/Rework')
                        print('*******************************************************************************')
                        self.stage1_status = None
                        r = requests.post(url="http://127.0.0.1:8000/livis/v1/inspection/save_results/", data={"inspection_id": str(current_inspection_id)})
                CacheHelper().set_json("current_inspection_status", "started")
                analog1_data = []
                analog2_data = []
                analog3_data = []
                CacheHelper().set_json('Stage1_Status',None)
                # if previous_stage1_status=='Accepted':
                #     controller.write_coil(stage1_accepted,True)
                # elif previous_stage1_status == 'Rejected':
                #     controller.write_coil(stage1_rejected,True)
                # previous_stage1_status = None
                self.old_trig1 = 1
            elif trig1 == 0 and self.old_trig1 == 1:
                self.old_trig1 = 0
                print('****************************************Trig1 Low')
                stage1_status,reject_reasons = self.verify_air_gauge(analog1_data,analog2_data,analog3_data)
                print("*******sending stage1 api***********")
                #rakshith:parijath: if air guage gets stuck, should it be manually reset, or automatically come back
                #should we show any status to front end regarding status of air guage error
                # should the roller setup run to perform inspection,
                # or should we start simultaniously and consider it as last part, as inspection of air guage part could not be done
                r = requests.post(url="http://127.0.0.1:8000/livis/v1/inspection/save_results_stage1/",\
                        data={"inspection_id" : str(current_inspection_id),\
                        "reject_reasons":reject_reasons, "stage1_status":stage1_status})
                        
            
            # if stage1_status != None and stage1_status != "Accepted":
            #     if controller.read_coil(stage2_rejected)==True or controller.read_coil(stage2_rework) == True:
            #         print('*******************************************************************************')
            #         print('Vision not running due to Stage1 Reject/Rework')
            #         print('*******************************************************************************')
            #         stage1_status = None
            #         r = requests.post(url="http://127.0.0.1:8000/livis/v1/inspection/save_results/", data={"inspection_id": str(current_inspection_id)})
                # trigger = 1
            if trig1 == 1:
                analog1 = self.controller.read_holding_register(20480+6300)
                analog2 = self.controller.read_holding_register(20480+6340)
                analog3 = self.controller.read_holding_register(20480+6380)
                if (analog1 < self.wrong) and (analog2 < self.wrong) and (analog3 < self.wrong):
                    analog1_data.append(analog1)
                    analog2_data.append(analog2)
                    analog3_data.append(analog3)
                    print(analog1,analog2,analog3)
                    # started = 1
                # elif started == 1:

            if self.previous_stage1_status!=None and self.controller.read_coil(self.stage1_inspected) == False :#rakshith to be verified
                CacheHelper().set_json('Stage1_Status',None)
                self.previous_stage1_status=None
                if self.stage1_status != None and self.stage1_status != "Accepted":
                    # if controller.read_coil(stage2_rejected)==True or controller.read_coil(stage2_rework) == True:
                        print('*******************************************************************************')
                        print('Vision not running due to Stage1 Reject/Rework')
                        print('*******************************************************************************')
                        stage1_status = None
                        r = requests.post(url="http://127.0.0.1:8000/livis/v1/inspection/save_results/", data={"inspection_id": str(current_inspection_id)})

            trig_cam1 = CacheHelper().get_json('Trigger_cam1')
            trig_cam2 = CacheHelper().get_json('Trigger_cam2')
            trig_cam3 = CacheHelper().get_json('Trigger_cam3')
            trig_cam4 = CacheHelper().get_json('Trigger_cam4')
            # print(trig_cam1,trig_cam2,trig_cam3,trig_cam4,(trig_cam1 and trig_cam2 and trig_cam3 and trig_cam4))
            if (trig_cam1 and trig_cam2 and trig_cam3 and trig_cam4):
                # time.sleep(1)
                self.controller.write_coil(self.stage2_trigger_address,False)
                old_trig = 0
                # time.sleep(0.1)
                print('Trig Low...')
                # time.sleep(1)
                CacheHelper().set_json('Trigger_cam1',False)
                CacheHelper().set_json('Trigger_cam2',False)
                CacheHelper().set_json('Trigger_cam3',False)
                CacheHelper().set_json('Trigger_cam4',False)

            cam1_complete = CacheHelper().get_json('cam1_completed')
            cam2_complete = CacheHelper().get_json('cam2_completed')
            cam3_complete = CacheHelper().get_json('cam3_completed')
            cam4_complete = CacheHelper().get_json('cam4_completed')
            #rakshith : to be verified
            # if  (cam1_complete and cam2_complete and cam3_complete and cam4_complete):
            #     controller.write_coil(self.stage2_trigger_address,False)
            
            part_status=CacheHelper().get_json('backend_part_status')
            # print(part_status,old_part_status,part_status != old_part_status)
            if part_status != self.old_part_status:
                print('\nPart Status',part_status,'\n')
                self.old_part_status = part_status
            if part_status == 'Accepted':
                self.controller.write_coil(self.stage2_accepted,1)
                CacheHelper().set_json('backend_part_status',None)
            elif part_status == 'Rejected':
                self.controller.write_coil(self.stage2_rejected,1)
                CacheHelper().set_json('backend_part_status',None)
            elif part_status == 'Rework':
                self.controller.write_coil(self.stage2_rework,1)
                CacheHelper().set_json('backend_part_status',None)
            #rakshith : to check when '--' is being shared 
            elif part_status == '--':
                # controller.write_coil(stage2_rework,1)
                CacheHelper().set_json('backend_part_status',None)
            elif part_status != None:
                self.controller.write_coil(self.stage2_rework,1)
                CacheHelper().set_json('backend_part_status',None)
                print('Forced To Rework')

def __main__():
    reset()
    
    plc(plc_ip)

if __name__ == "__main__":
    __main__() 