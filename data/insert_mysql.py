import json
import mysql.connector
import os
from dotenv import load_dotenv
try:
    load_dotenv()
    local_password=os.getenv("password")
    connection=mysql.connector.connect(host="localhost",
                                        port="3306",
                                        user="root",
                                        password=local_password,
                                        database="Attractions")
    cursor = connection.cursor()
    with open("taipei-day-trip-website/data/taipei-attractions.json","r",encoding="utf-8") as file:
        data=json.load(file)
    attractions=data["result"]["results"]
    for idx, location in enumerate(attractions):
        name=location["stitle"]
        category=location["CAT2"]
        description=location["xbody"]
        address=location["address"]
        transport=location["info"]
        mrt=location["MRT"]
        latitude=location["latitude"]
        longitude=location["longitude"]
        images=','.join(['https'+content for idx, content in enumerate(location["file"].split('https'))\
         if idx!=0 and ('jpg'in content.lower() or 'png'in content.lower())])
        cursor.execute("INSERT INTO `location` (`name`,`category`,`description`,`address`,`transport`,`mrt`,`latitude`,`longitude`,`images`)\
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)",(name,category,description,address,transport,mrt,latitude,longitude,images))
    connection.commit()
except mysql.connector.Error as error:
    print("Failed to update record to database rollback: {}".format(error))
    connection.rollback()
except:
    print("other error")
finally:
    cursor.close()
    connection.close()
    

