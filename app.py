from flask import *
import mysql.connector
import os
from dotenv import load_dotenv
from mysql.connector import pooling

app=Flask(__name__)
app.config["JSON_AS_ASCII"]=False
app.config["TEMPLATES_AUTO_RELOAD"]=True

load_dotenv()
local_password=os.getenv("password")
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

if __name__=="__main__":
    app.run(host='0.0.0.0',port=3000)