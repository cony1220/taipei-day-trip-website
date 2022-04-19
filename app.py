from flask import *
import mysql.connector
import os
from dotenv import load_dotenv
from mysql.connector import pooling
import re
import bcrypt
import datetime
import requests as req

app=Flask(__name__)
app.config["JSON_AS_ASCII"]=False
app.config["TEMPLATES_AUTO_RELOAD"]=True

app.secret_key=os.urandom(24)
load_dotenv()
local_password=os.getenv("password")
partner_key=os.getenv("partner_key")
connectionpool=pooling.MySQLConnectionPool(pool_name="poolname",
                                            pool_size=3,
                                            pool_reset_session=True,
                                            host="localhost",
                                            port="3306",
                                            user="root",
                                            password=local_password,
                                            database="Attractions")

def get_data(cursor,n):
	data=cursor.fetchall()
	# 取得欄位名稱
	key=cursor.description
	key_list=[]
	for item in key:
		key_list.append(item[0])
	response={}
	if n==None:
		response["nextPage"]=n
	else:
		response["nextPage"]=n+1
	response["data"]=[]
	# 寫入{data:[{,},...]}
	for item in data:
		content={}
		for idx, row in enumerate(key_list):
			if row=="images":
				content[row]=item[idx].split(",")
			else:
				content[row]=item[idx]
		response["data"].append(content)
	return jsonify(response)
# Pages
@app.route("/")
def index():
	return render_template("index.html")
@app.route("/attraction/<id>")
def attraction(id):
	return render_template("attraction.html")
@app.route("/booking")
def booking():
	return render_template("booking.html")
@app.route("/thankyou")
def thankyou():
	return render_template("thankyou.html")
@app.route("/history")
def history():
	return render_template("history.html")
@app.route("/member")
def member():
	return render_template("member.html")

@app.route("/api/attractions", methods=["GET"])
def attraction_qurey():
	try:
		connection=connectionpool.get_connection()
		cursor=connection.cursor()
		page=request.args.get("page", "")
		keyword=request.args.get("keyword", "")
		if keyword=="":
			cursor.execute("SELECT COUNT(*) FROM `location`")
			count=cursor.fetchone()
			count=count[0]
			total_page=count//12
			left=count%12
			if page=="" or page=="0":
				n=0
				cursor.execute("SELECT * FROM `location` LIMIT 0,12")
				response=get_data(cursor,n)
				response=make_response(response,200)
				return response
			else:
				if int(page)<total_page:
					n=int(page)
					cursor.execute("SELECT * FROM `location` LIMIT %s,12",[n*12])
					response=get_data(cursor,n)
					response=make_response(response,200)
					return response
				elif int(page)==total_page:
					n=int(page)
					cursor.execute("SELECT * FROM `location` LIMIT %s,%s",[n*12,left])
					response=get_data(cursor,None)
					response=make_response(response,200)
					return response
				else:
					response={
						"error":True,
						"message":"out of range"
					}
					response=make_response(jsonify(response),500)
					return response
		else:
			cursor.execute("SELECT COUNT(*) FROM `location` WHERE `name` like %s",["%"+keyword+"%"])
			count=cursor.fetchone()
			count=count[0]
			total_page=count//12
			left=count%12
			print(count)
			if count>12:
				if page=="" or page=="0":
					n=0
					cursor.execute("SELECT * FROM `location`WHERE `name` like %s LIMIT 0,12",["%"+keyword+"%"])
					response=get_data(cursor,n)
					response=make_response(response,200)
					return response
				elif 0<int(page)<total_page:
					n=int(page)
					cursor.execute("SELECT * FROM `location`WHERE `name` like %s LIMIT %s,12",["%"+keyword+"%",n*12])
					response=get_data(cursor,n)
					response=make_response(response,200)
					return response
				elif int(page)==total_page:
					n=int(page)
					cursor.execute("SELECT * FROM `location` WHERE `name` like %s LIMIT %s,%s",["%"+keyword+"%",n*12,left])
					response=get_data(cursor,None)
					response=make_response(response,200)
					return response
				else:
					response={
						"error":True,
						"message":"out of range"
					}
					response=make_response(jsonify(response),500)
					return response
			elif 0<count<=12:
				if page=="" or page=="0":
					n=None
					cursor.execute("SELECT * FROM `location`WHERE `name` like %s LIMIT 0,%s",["%"+keyword+"%",left])
					response=get_data(cursor,n)
					response=make_response(response,200)
					return response
				else:
					response={
						"error":True,
						"message":"out of range"
					}
					response=make_response(jsonify(response),500)
					return response
			else:
				response={
						"error":True,
						"message":"out of range"
					}
				response=make_response(jsonify(response),500)
				return response
	except:
		connection.rollback()
		response={
				"error":True,
				"message":"error"
			}
		response=make_response(jsonify(response),500)
		return response
	finally:
		if connection.is_connected():
			cursor.close()
			connection.close()
			print("connection is closed")
@app.route("/api/attraction/<attractionId>")
def id_query(attractionId):
	try:
		id=attractionId
		connection=connectionpool.get_connection()
		cursor=connection.cursor()
		cursor.execute("SELECT * FROM `location` WHERE `id`=%s",[id])
		data=cursor.fetchone()
		if data:
			# 取得欄位名稱
			key=cursor.description
			key_list=[]
			for item in key:
				key_list.append(item[0])
			response={}
			# 寫入{data:[{,},...]}
			content={}
			for idx, row in enumerate(key_list):
				if row=="images":
					content[row]=data[idx].split(",")
				else:
					content[row]=data[idx]
			response["data"]=content
			response=make_response(jsonify(response),200)
			return response
		else:
			response={
					"error":True,
					"message":"out of range"
				}
			response=make_response(jsonify(response),400)
			return response
	except:
		connection.rollback()
		response={
				"error":True,
				"message":"error"
			}
		response=make_response(jsonify(response),500)
		return response
	finally:
		if connection.is_connected():
			cursor.close()
			connection.close()
			print("connection is closed")
@app.route("/api/user", methods=["GET","PATCH","POST","DELETE"])
def api_user():
	try:
		connection=connectionpool.get_connection()
		cursor=connection.cursor()
		if request.method=="PATCH":
			data=request.get_json()
			email=data["email"]
			password=data["password"]
			cursor.execute("SELECT * FROM `member` WHERE `email`=%s",(email,))
			user=cursor.fetchone()
			if user:
				hashed_password=user[3]
				if bcrypt.checkpw(password.encode('utf-8'),hashed_password.encode('utf-8')):
					session["id"]=user[0]
					session["name"]=user[1]
					session["email"]=user[2]
					session["login"]=True
					response={
						"ok":True
					}
					response=make_response(jsonify(response),200)
					return response
				else:
					response={
						"error":True,
						"message":"email or password is incorrect"
					}
					response=make_response(jsonify(response),400)
					return response
			else:
				response={
					"error":True,
					"message":"email or password is incorrect"
				}
				response=make_response(jsonify(response),400)
				return response
		elif request.method=="GET":
			status=session.get("login")
			if status==True:
				response={
					"data":{
						"id":session["id"],
						"name":session["name"],
						"email":session["email"]
					}
				}
				response=make_response(jsonify(response),200)
				return response
			else:
				response={
					"data":None
				}
				response=make_response(jsonify(response),200)
				return response
		elif request.method=="POST":
			data=request.get_json()
			name=data["name"]
			email=data["email"]
			password=data["password"]
			name_pattern=re.compile('[\w]{1,19}$')
			email_pattern=re.compile('^[a-zA-Z0-9]{3,19}@[a-zA-Z0-9-.]{2,19}$')
			pattern=re.compile('[a-zA-Z0-9]{3,19}$')
			if re.match(name_pattern,name) and re.match(email_pattern,email) and re.match(pattern,password):
				cursor.execute("SELECT * FROM `member` WHERE `email`=%s",[email])
				examine_user=cursor.fetchone()
				if examine_user:
					response={
						"error":True,
						"message":"email already exists"
					}
					response=make_response(jsonify(response),400)
					return response
				else:
					password=password.encode('utf-8')
					hashed_password=bcrypt.hashpw(password,bcrypt.gensalt())
					cursor.execute("INSERT INTO `member` (`name`,`email`,`password`)VALUES(%s,%s,%s)",(name,email,hashed_password))
					connection.commit()
					response={
						"ok":True,
					}
					response=make_response(jsonify(response),200)
					return response
			else:
				response={
					"error":True,
					"message":"invalid format"
				}
				response=make_response(jsonify(response),400)
				return response
		elif request.method=="DELETE":
			session["login"]=False
			response={
				"ok":True
			}
			response=make_response(jsonify(response),200)
			return response
	except:
		connection.rollback()
		response={
			"error":True,
			"message":"server error"
		}
		response=make_response(jsonify(response),500)
		return response
	finally:
		if connection.is_connected():
			cursor.close()
			connection.close()
			print("connection is closed")

@app.route("/api/booking", methods=["GET","POST","DELETE"])
def api_booking():
	try:
		connection=connectionpool.get_connection()
		cursor=connection.cursor()
		if request.method=="GET":
			status=session.get("login")
			if status==True:
				user_id=session.get("id")
				cursor.execute("SELECT * FROM `booking` WHERE `user_id`=%s",[user_id])
				information=cursor.fetchone()
				if information:
					attraction_id=information[2]
					cursor.execute("SELECT * FROM `location` WHERE `id`=%s",[attraction_id])
					data=cursor.fetchone()
					images=data[9].split(",")
					response={
						"data":{
							"attraction":{
								"id":data[0],
								"name":data[1],
								"address":data[4],
								"image":images[0]
							},
							"date":information[3],
							"time":information[4],
							"price":information[5]
						}
					}
					response=make_response(jsonify(response),200)
					return response
				else:
					response={
						"data":None
					}
					response=make_response(jsonify(response),200)
					return response
			else:
				response={
					"error":True,
					"message":"Not loging"
				}
				response=make_response(jsonify(response),403)
				return response
		elif request.method=="POST":
			status=session.get("login")
			if status==True:
				data=request.get_json()
				attraction_id=data["attractionId"]
				cursor.execute("SELECT * FROM `location` WHERE `id`=%s",[attraction_id])
				information=cursor.fetchone()
				if information:
					user_id=session.get("id")
					date=data["date"]
					time=data["time"]
					price=data["price"]
					cursor.execute("SELECT * FROM `booking` WHERE `user_id`=%s",[user_id])
					booking_data=cursor.fetchone()
					if booking_data:
						cursor.execute("DELETE FROM `booking` WHERE `user_id` =%s",[user_id])
					cursor.execute("INSERT INTO `booking` (`user_id`,`attraction_id`,`date`,`time`,`price`)VALUES(%s,%s,%s,%s,%s)",(user_id,attraction_id,date,time,price))
					connection.commit()
					response={
						"ok":True,
					}
					response=make_response(jsonify(response),200)
					return response
				else:
					response={
						"error":True,
						"message":"Data doesen't exist"
					}
					response=make_response(jsonify(response),400)
					return response
			else:
				response={
					"error":True,
					"message":"Not Loging"
				}
				response=make_response(jsonify(response),403)
				return response
		elif request.method=="DELETE":
			status=session.get("login")
			if status==True:
				user_id=session.get("id")
				cursor.execute("DELETE FROM `booking` WHERE `user_id` = %s",[user_id])
				connection.commit()
				response={
					"ok":True,
				}
				response=make_response(jsonify(response),200)
				return response
			else:
				response={
					"error":True,
					"message":"Not loging"
				}
				response=make_response(jsonify(response),403)
				return response
	except:
		connection.rollback()
		response={
			"error":True,
			"message":"Server error"
		}
		response=make_response(jsonify(response),500)
		return response
	finally:
		if connection.is_connected():
			cursor.close()
			connection.close()
			print("connection is closed")

@app.route("/api/orders", methods=["POST"])
def api_orders():
	try:
		connection=connectionpool.get_connection()
		cursor=connection.cursor()
		status=session.get("login")
		user_id=session.get("id")
		if status==True:
			data=request.get_json()
			attraction_id=data["orders"]["trip"]["attraction"]["id"]
			cursor.execute("SELECT * FROM `booking` WHERE `user_id`=%s and `attraction_id`=%s",[user_id,attraction_id])
			information=cursor.fetchone()
			if information:
				attraction_name=data["orders"]["trip"]["attraction"]["name"]
				attraction_address=data["orders"]["trip"]["attraction"]["address"]
				image=data["orders"]["trip"]["attraction"]["image"]
				date=data["orders"]["trip"]["date"]
				time=data["orders"]["trip"]["time"]
				price=data["orders"]["price"]
				name=data["orders"]["contact"]["name"]
				email=data["orders"]["contact"]["email"]
				phone=data["orders"]["contact"]["phone"]
				pay_status=1
				pay_message="付款失敗"
				tonow=datetime.datetime.today()
				cursor.execute("select count(*) from `orders`")
				order_number=cursor.fetchone()
				order_number=order_number[0]+1
				number=str(tonow.year)+str(tonow.month)+str(tonow.day)+str(tonow.hour)+str(tonow.minute)+str(tonow.second)+str(user_id)+str(attraction_id)+str(order_number)
				url='https://sandbox.tappaysdk.com/tpc/payment/pay-by-prime'
				headers={
					'Content-Type': 'application/json',
	 				'x-api-key': partner_key
				}
				pay_data={
					"prime": data["prime"],
					"partner_key": partner_key,
					"merchant_id": "DKC_CTBC",
					"details":"TapPay Test",
					"amount": price,
					"cardholder": {
						"phone_number": phone,
						"name": name,
						"email": email,
					},
					"remember": True
				}
				r=req.post(url,json=pay_data,headers=headers)
				r_json=r.json()
				if (r_json["status"]==0):
					pay_status=0
					pay_message="付款成功"
					cursor.execute("DELETE FROM `booking` WHERE `user_id`=%s and `attraction_id`=%s",[user_id,attraction_id])
				cursor.execute("INSERT INTO `orders` VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(number,user_id,price,attraction_id,attraction_name,attraction_address,image,date,time,name,email,phone,pay_status))
				connection.commit()
				response={
					"data":{
						"number":number,
						"payment":{
							"status":pay_status,
							"message":pay_message
						}
					}
				}
				response=make_response(jsonify(response),200)
				return response
			else:
				response={
					"error":True,
					"message":"Data doesen't exist"
				}
				response=make_response(jsonify(response),400)
				return response
		else:
			response={
				"error":True,
				"message":"Not Loging"
			}
			response=make_response(jsonify(response),403)
			return response
	except:
		connection.rollback()
		response={
			"error":True,
			"message":"Server error"
		}
		response=make_response(jsonify(response),500)
		return response
	finally:
		if connection.is_connected():
			cursor.close()
			connection.close()
			print("connection is closed")

@app.route("/api/order/<orderNumber>", methods=["GET"])
def api_order(orderNumber):
	try:
		connection=connectionpool.get_connection()
		cursor=connection.cursor()
		status=session.get("login")
		user_id=session.get("id")
		if status==True:
			cursor.execute("SELECT * FROM `orders` WHERE `number`=%s and `user_id`=%s",(orderNumber,user_id))
			data=cursor.fetchone()
			if data:
				response={
					"data":{
						"number":data[0],
						"price":data[2],
						"trip":{
							"attraction":{
								"id":data[3],
								"name":data[4],
								"address":data[5],
								"image":data[6]
							},
							"date":data[7],
							"time":data[8]
						},
						"contact":{
							"name":data[9],
							"email":data[10],
							"phone":data[11]
						},
						"status":data[12]
					}
				}
				response=make_response(jsonify(response),200)
				return response
			else:
				response={
					"data":None
				}
				response=make_response(jsonify(response),200)
				return response
		else:
			response={
				"error":True,
				"message":"Not Loging"
			}
			response=make_response(jsonify(response),403)
			return response
	except:
		connection.rollback()
		response={
			"error":True,
			"message":"Server error"
		}
		response=make_response(jsonify(response),500)
		return response
	finally:
		if connection.is_connected():
			cursor.close()
			connection.close()
			print("connection is closed")

@app.route("/api/history", methods=["GET"])
def api_history():
	try:
		connection=connectionpool.get_connection()
		cursor=connection.cursor()
		status=session.get("login")
		user_id=session.get("id")
		if status==True:
			cursor.execute("SELECT * FROM `orders` WHERE `user_id`=%s and `status`=0",(user_id,))
			history_data=cursor.fetchall()
			if history_data:
				response={}
				response["data"]=[]
				for data in history_data:
					content={
						"number":data[0],
						"price":data[2],
						"trip":{
							"attraction":{
								"id":data[3],
								"name":data[4],
								"address":data[5],
								"image":data[6]
							},
							"date":data[7],
							"time":data[8]
						},
						"contact":{
							"name":data[9],
							"email":data[10],
							"phone":data[11]
						}
					}
					response["data"].append(content)
				response=make_response(jsonify(response),200)
				return response
			else:
				response={
					"data":None
				}
				response=make_response(jsonify(response),200)
				return response
		else:
			response={
				"error":True,
				"message":"Not Loging"
			}
			response=make_response(jsonify(response),403)
			return response		
	except:
		connection.rollback()
		response={
			"error":True,
			"message":"Server error"
		}
		response=make_response(jsonify(response),500)
		return response
	finally:
		if connection.is_connected():
			cursor.close()
			connection.close()
			print("connection is closed")

if __name__=="__main__":
    app.run(host='0.0.0.0',port=3000)