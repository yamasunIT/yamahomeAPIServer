#!/usr/bin/python3
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import boto3
import json
from pydantic import BaseModel
from tinydb import TinyDB, Query
from typing import Union

class Device(BaseModel):
	name: str
	serialNo: str
	deviceType: str
	room: str

class Signup(BaseModel):
	account: str
	password: str
	name: str

class Signin(BaseModel):
	account: str
	password: str

app = FastAPI()

#aws source
client = boto3.client('iot-data', region_name='ap-northeast-1')

#Database
deviceDB = TinyDB('device.json')
userDB = TinyDB('user.json')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#測試用
@app.get("/api/test", tags=["測試"])
def test():
	return {'statusCode': 200, 'message': "hello world"}


#新增裝置 裝置名稱 裝置序號 裝置種類
@app.post("/api/devices", tags=["裝置"])
def createDevice(device: Device):
	data = deviceDB.insert(device.dict())
	if data > 0:
		return {'statusCode': 200, 'message': 'success'}
	else:
		return {'statusCode': 400, 'message': 'failed'}

#取得所有裝置
@app.get("/api/devices/all", tags=["裝置"])
def getDevices():
	data = deviceDB.all()
	return {'statusCode': 200, 'message': 'success', 'data': data}

#取得裝置
@app.get("/api/devices/{serialNo}", tags=["裝置"])
def getDevice(serialNo: str):
	device = Query()
	returnData = deviceDB.search(device.serialNo == serialNo)
	if len(returnData):
		return {'statusCode': 200, 'message': 'success', "data": returnData[0]}
	else:
		return {'statusCode': 400, 'message': 'failed'}
#刪除裝置
@app.delete("/api/devices/{serialNo}", tags=["裝置"])
def deleteDevice(serialNo: str):
	device = Query()
	data = deviceDB.remove(device.serialNo == serialNo)
	if len(data):
		return {"statusCode": 200, "message": "success"}
	else:
		return {"statusCode": 400, "message": "failed"}

#更新裝置
@app.put("/api/devices/{serialNo}", tags=["裝置"])
def updateDevice(serialNo: str, name: str, room: str):
	device = Query()
	data = deviceDB.update({'name': name, 'room': room}, device.serialNo == serialNo)
	if len(data):
		return {"statusCode": 200, "message": "success"}
	else:
		return {"statusCode": 400, "message": "failed"}



#-----------------------------------------------------------------------------------
#智慧插座控制
@app.get("/api/smartPlugs/{serialNo}/{cmd}", tags=["智慧插座"])
def smartPlugs(serialNo: str, cmd: str):
	response = client.publish(
		topic = "$aws/things/" + serialNo + "/shadow/name/" + serialNo + "-shadow/update",
		qos = 1,
		payload = json.dumps({"state":{"desired": {"plugState": (cmd == 'on')}}})
	)
	return {'statusCode': 200, 'message': 'success', 'data': json.dumps(response)}

#-----------------------------------------------------------------------------------
#註冊
@app.post("/api/users/register", tags=["使用者"])
def register(user: Signup):
	user_dict = user.dict()
	filtered_user = Query()
	filtered_data = userDB.search(filtered_user.account == user_dict['account'])
	if len(filtered_data) > 0:
		return {"statusCode": 400, "message": "account is exist."}
	else:
		data = userDB.insert(user_dict)
		if data > 0:
			return {"statusCode": 200, "message": "success"}
		else:
			return {"statusCode": 400, "message": "failed"}

#登入
@app.post("/api/users/login", tags=["使用者"])
def login(user: Signin):
	user_dict = user.dict()
	filtered_user = Query()
	filtered_data = userDB.search((filtered_user.account == user_dict['account']) & (filtered_user.password == user_dict['password']))
	if len(filtered_data) > 0:
		return {"statusCode": 200, "message": "success", "data": filtered_data[0]['name']}
	else:
		return {"statusCode": 400, "message": "user was not found"}

#變更密碼or名稱
@app.put("/api/users/{account}", tags=["使用者"])
def changeInfo(account: str, password: Union[str, None] = None,  userName: Union[str, None] = None):
	filtered_user = Query()
	if password:
		data = userDB.update({'password': password}, filtered_user.account == account)
		if len(data):
			return {"statusCode": 200, "message": "success"}
		else:
			return {"statusCode": 400, "message": "user was not found"}
	if userName:
		data = userDB.update({'name': userName}, filtered_user.account == account)
		if len(data):
			return {"statusCode": 200, "message": "success"}
		else:
			return {"statusCode": 400, "message": "user was not found"}


#刪除帳號
@app.delete("/api/users/{account}", tags=["使用者"])
def deleteAcount(account: str):
	filtered_user = Query()
	filtered_data = userDB.remove(filtered_user.account == account)
	if len(filtered_data):
		return {"statusCode": 200, "message": "success"}
	else:
		return {"statusCode": 400, "message": "failed"}



if __name__ == '__main__':
	uvicorn.run(app, host="0.0.0.0", port=8000)
