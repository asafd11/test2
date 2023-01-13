from flask import Flask, request, redirect
from twilio.twiml.messaging_response import MessagingResponse
from flask_mysqldb import MySQL
import os
import openai
import json
from twilio.rest import Client
import duffel
import mysql.connector
import config


openai.api_key= config.openai_api_key
twiliophone=config.twilio_phone
accountsid=config.account_sid
authtoken=config.twilio_token


app = Flask(__name__)
"""
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'booking'
app.config['MYSQL_PASSWORD'] = 'david'
app.config['MYSQL_DB'] = 'booking'

mysql = MySQL(app)
"""
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
    
#model="code-davinci-002",
def openai_get_json3(sms_body):
    print(sms_body)
    response = openai.Completion.create(
    model="text-davinci-003",
    prompt=sms_body,
    temperature=0,
    max_tokens=256,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0
    )
    openai_respons=response.choices[0]
    print(openai_respons.text)
    arrsplit=openai_respons.text.split("\n")
    arr_list=[]
    for obj in arrsplit:
        if len(obj)>2:
            objvalue=obj.split(":")[1].strip()
            arr_list.append(objvalue)
    buildstr="fly_from:{} fly_to:{} departure:{} returning:{}".format(arr_list[0],arr_list[1],arr_list[2],arr_list[3])
    print(buildstr)
    return arr_list
def openai_get_json2(sms_body):
    print(sms_body)
    response = openai.Completion.create(
    model="code-davinci-002",
    prompt=sms_body,
    temperature=0,
    max_tokens=256,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0
    )
    openai_respons=response.choices[0]
    print(openai_respons.text)
    strsplit=openai_respons.text.split("*")[0].split(":",1)[1].replace("\n","").strip()
    test=strsplit.split("from: '")
    fly_from=strsplit.split("from: '")[1].split("'")[0]
    fly_to=strsplit.split("to: '")[1].split("'")[0]
    departure=strsplit.split("departure: '")[1].split("'")[0]
    returning=strsplit.split("return: '")[1].split("'")[0]
    buildstr="fly_from:{} fly_to:{} departure:{} returning:{}".format(fly_from,fly_to,departure,returning)
    print(buildstr)
    return buildstr

def openai_get_json(sms_body):
    print(sms_body)
    response = openai.Completion.create(
    model="code-davinci-002",
    prompt=sms_body,
    temperature=0,
    max_tokens=256,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0
    )
    openai_respons=response.choices[0]
    print(openai_respons)
    jsontest=json.loads(openai_respons.text.replace("<code>","").replace("</code>",""))
    return jsontest
    """
    print(test)
    print(test.text.split("{")[1].split("}")[0].replace("\n","").split(","))
    respons_array=test.text.split("{")[1].split("}")[0].replace("\n","").split(",")
    origin=respons_array[0].split(":")[1].strip().replace('"',"")
    destination=respons_array[1].split(":")[1].strip().replace('"',"")
    departuredate=respons_array[2].split(":")[1].strip().replace('"',"")
    returndate=respons_array[3].split(":")[1].strip().replace('"',"")
    bstr="origin: {} destination: {} departuredate:{} returndate:{}".format(origin,destination,departuredate,returndate)
    return bstr
    """
def getrespons(msg_from,msg_body):
    cur = mysql.connection.cursor()
    print("select * from booking_sessions where from_phone='{}' and create_at=CURDATE()".format(msg_from))
    cur.execute("select * from booking_sessions where from_phone='{}' and create_at=CURDATE() ORDER BY `booking_sessions`.`create_at` DESC".format(msg_from))
    result=cur.fetchall()
    if len(result)==0:
        cur.execute("INSERT INTO `booking_sessions` (`from_phone`, `create_at`, `where_to`, `from_where`, `on_date`, `status`) VALUES ('{}', 'CURDATE()', '', '', NULL, '0');")
        mysql.connection.commit()
        return "where do you want to go?"
    obj=result[0]
    if obj[2]=='':
        str_date="{}-{}-{}".format(obj[1].year,obj[1].month,obj[1].day)
        cur.execute("UPDATE `booking_sessions` SET `where_to` = '{}' WHERE `booking_sessions`.`from_phone` = '{}' AND `booking_sessions`.`create_at` = '{}';".format(msg_body,msg_from,str_date))
        mysql.connection.commit()
        return "from where?"
    if obj[3]=='':
        str_date="{}-{}-{}".format(obj[1].year,obj[1].month,obj[1].day)
        cur.execute("UPDATE `booking_sessions` SET `from_where` = '{}' WHERE `booking_sessions`.`from_phone` = '{}' AND `booking_sessions`.`create_at` = '{}';".format(msg_body,msg_from,str_date))
        mysql.connection.commit()
        return "on what date? (yyyy-mm-dd)"
    if obj[4]=='':
        str_date="{}-{}-{}".format(obj[1].year,obj[1].month,obj[1].day)
        cur.execute("UPDATE `booking_sessions` SET `on_date` = '{}' WHERE `booking_sessions`.`from_phone` = '{}' AND `booking_sessions`.`create_at` = '{}';".format(msg_body,msg_from,str_date))
        mysql.connection.commit()

        # all fields are done get list from duffel
        return "return the duffel result for phone:{} session_date:{} fly_from:{} fly_to:{} at_date:{}".format(msg_from,str_date,obj[1],obj[2],obj[3])

    #print(result)

def send_sms(smsbody,smsfrom):
    account_sid =config.account_sid
    auth_token = config.twilio_token
    client = Client(account_sid, auth_token)

    message = client.messages.create(
    body=smsbody,
    from_=config.twilio_phone,
    to=smsfrom
    )
def checkforuser(msgg_from,mydb,mycursor):
    phone=msgg_from.replace("+","")
    #Creating a connection cursor
    mydb,mycursor=getconnection()
    
    #Executing SQL Statements
    mycursor.execute(''' SELECT * FROM `users` WHERE `phone` = '{}';  '''.format(phone))
    #cursor.execute(''' INSERT INTO table_name VALUES(v1,v2...) ''')
    #cursor.execute(''' DELETE FROM table_name WHERE condition ''')
    result=mycursor.fetchall()
    if len(result)==0:
        msg="We need some more info to get started, {}/duffel/regpage.php?phone={}".format(config.base_url,phone)
        send_sms(msg,msgg_from)
        return True
    
    #Saving the Actions performed on the DB
    #mysql.connection.commit()
    
    #Closing the cursor
    #mycursor.close()
    #mydb.close()
    return result[0]


@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():
    """Respond to incoming calls with a simple text message."""
    # Start our TwiML response
    mydb,mycursor=getconnection()
    msgg_body = request.values.get('Body', None)
    msgg_from = request.values.get('From', None)
    #check if got user info
    passenger_info=checkforuser(msgg_from,mydb,mycursor)
    if passenger_info==True:
        return #msg was send with url for reg
    if msgg_body == '!help':
        msg="""
        example for request:
        i need a flight from london to Helisinki on 22 april 2023 and returning on 01.07.2023
        commands type:
            1.for user info
            2.url to update info/reg
        """
        send_sms(msg,msgg_from)
        return 'ok'
    #resp = MessagingResponse()

    if msgg_body=="1":    
        msg="first name:{} last name:{} phone:{} email:{} id:{} title:{} gender:{} birthday:{} ".format(passenger_info[2],passenger_info[3],passenger_info[0],passenger_info[4],passenger_info[1],passenger_info[5],passenger_info[6],passenger_info[7])
        send_sms(msg,msgg_from)
        return 'ok'

    if msgg_body=="2":
        phone=msgg_from.replace("+","")
        msg="We need some more info to get started, {}/duffel/regpage.php?phone={}".format(config.base_url,phone)
        send_sms(msg,msgg_from)
        return 'ok'


    if len(msgg_body)<10:
        msg=""" type !help for commands
         example for request:
        i need a flight from london to Helisinki on 22 april 2023 and returning on 01.07.2023     
        """
        send_sms(msg,msgg_from)
        return 
    #str_template="""create a javascript object with the given information from to deparure return and parse date.
    #input:'{}.'""".format(msgg_body)
    str_template2="""i will give you a text message from out user. you will respond in the following format after convert flight_From and flight_to to closets airport code and parse date to YYYY-MM-DD:
    flight_from:
    flight_to:
    depart_date:
    return_date:
    No description or anythig else.
    lets start.
    '{}'
    """.format(msgg_body)
    openai_res=openai_get_json3(str_template2)

    url,insertquery =duffel.booking(msgg_from,openai_res,passenger_info)
    
    mycursor.execute(insertquery)
    mydb.commit()
    lastid=mycursor.lastrowid
    url="{}&oid={}".format(url,lastid)
    msg_back="""link for payment:
    {}
    """.format(url)
    #data = json.dumps(openai_res)
    #resp.message(data)
    send_sms(msg_back,msgg_from)
    mycursor.close()
    mydb.close()
    return "ok"

    #resp = MessagingResponse()

    # Add a message
    #resp.message("The Robots are coming! Head for the hills!")

   # return str(resp)
   

if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=True)