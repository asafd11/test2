import mysql.connector
import time
from duffel_api import Duffel
from duffel_api.models import PaymentIntent
from twilio.rest import Client
import config
import json
def send_sms(smsbody,smsfrom):
    account_sid = config.account_sid
    auth_token = config.twilio_token
    client = Client(account_sid, auth_token)

    message = client.messages.create(
    body=smsbody,
    from_=config.twilio_phone,
    to="+{}".format(smsfrom)
    )
def checkforuser(msgg_from,mycursor):
    mycursor.execute(''' SELECT * FROM `users` WHERE `phone` = '{}';  '''.format(msgg_from))
    result=mycursor.fetchall()
    return result[0]
def getconnection():
    try:
        mydb = mysql.connector.connect(
                host=config.mysql_server,
                user="booking",
                password="david",
                database="booking"
            )
        mycursor = mydb.cursor()
        return mydb,mycursor
    except:
        print("fail to get mysql connection")
        return 0,0

duffel = Duffel(access_token=config.duffel_us_token)
mydb=0
mycursor=0
while True:   
    try:
        mydb,mycursor=getconnection()
        if mydb==0:
            print("fail to create connection plz check")
            time.sleep(5)
            continue
        mycursor.execute("select * from orders where payment_status=0")
        result=mycursor.fetchall()
        for obj in result:
            try:
                payment_check=duffel.payment_intents.confirm(obj[1])
            except:
                continue
            if payment_check.status!='succeeded':
                continue
            passenger_info=checkforuser(obj[2],mycursor)
            passengerss_info = [
                {
                "phone_number": "+{}".format(passenger_info[0]),
                "email": "{}".format(passenger_info[4]),
                "born_on": "{}".format(passenger_info[-1]),
                "title": "{}".format(passenger_info[5]),
                "gender": "{}".format(passenger_info[6]),
                "family_name": "{}".format(passenger_info[3]),
                "given_name": "{}".format(passenger_info[2]),
                "id": "{}".format(obj[7])
                }
            ]
            payamount=obj[3]
            currecies=obj[4]
            payments = [
                {
                    "type": "balance",
                    "currency": "{}".format(currecies),
                    "amount": "{}".format(payamount)
                }
            ]
            if True:
                try:
                  res=duffel.orders.create().selected_offers([obj[6]]).payments(payments).passengers(passengerss_info).execute()
                  strobj=str(res)
                  try:
                    airline=strobj.split("owner=Airline")
                    airlinename=airline[1].split("name='")[1].split("'")[0]
                  except:
                    airlinename="fail to get airline name"
                  try:
                    bookref=strobj.split("booking_reference='")[1].split("'")[0]
                  except:
                    bookref="fail to get booking ref"
                  
                  strbuild="airline name:{} booking reference:{}".format(airlinename,bookref)
                  msgbuild="""booking Confirmed: 
                  {}
                  """.format(strbuild)
                  send_sms(msgbuild,passenger_info[0])
                  print(res)
                  #update status from 0 to 1
                  mycursor.execute("UPDATE `orders` SET `payment_status`='1',`order_info`='{}' WHERE `client_token`='{}' and `id`='{}'".format(strbuild,obj[0],obj[1]))
                  mydb.commit()
                except Exception as error:
                    send_sms("error at booking contact us at {} the error:{}".format(config.support_email,error.message),passenger_info[0])
                    mycursor.execute("UPDATE `orders` SET `payment_status`='99' WHERE `client_token`='{}' and `id`='{}'".format(obj[0],obj[1]))
                    mydb.commit()
                    print(error.message)

        mycursor.close()
        mydb.close()
        time.sleep(10)
        print("loop")

    except:
        print("error check")
        time.sleep(5)
        duffel = Duffel(access_token=config.duffel_us_token)
        mydb,mycursor=getconnection()
