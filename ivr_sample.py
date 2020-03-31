
# coding: utf-8

# In[ ]:


from flask import Flask,request, Response,session
import requests
import json
import nexmo
import datetime
from base64 import urlsafe_b64encode
import os
import calendar
# from jose import jwt
import jwt # https://github.com/jpadilla/pyjwt -- pip3 install PyJWT
import coloredlogs, logging
from uuid import uuid4

# test

# for heroku, please put all env parameters to 'Config Vars` in heroku dashboard
# from dotenv import load_dotenv
# dotenv_path = join(dirname(__file__), '.env')
# load_dotenv(dotenv_path)

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG', logger=logger)

api_key = os.environ.get("API_KEY") 
api_secret = os.environ.get("API_SECRET")
application_id = os.environ.get("APPLICATION_ID")

private_key = os.environ.get("PRIVATE_KEY")

# keyfile = "private.key"

url = "https://api.nexmo.com/v1/calls"

webhook_url = os.environ.get("WEBHOOK_URL")

web_port = os.environ.get("WEB_PORT")

virtual_number = os.environ.get("LVN")

sales_1 = os.environ.get("SALES_1")
sales_2 = os.environ.get("SALES_2")
engineer = os.environ.get("ENGINEER")

def get_recording(url,uuid):

    currentDT = datetime.datetime.now()
    date =currentDT.strftime("%H:%M:%S")
    
#    fname = uuid + "." + "mp3"
    fname = date + "." + "mp3"
    new_url=url+"?api_key="+api_key+"&"+"api_secret="+api_secret
    headers={ "content-type": "application/json"
                #"authorization": "Bearer {0}".format(jwt)
			}
    resp = requests.get(new_url, headers=headers)
    f= open('/var/www/html/'+fname ,'wb')
    f.write(resp.content)
    f.close()

    sms_text = "RecFile https://rec_url.xxxx.jp/"+fname
    response_SMS = client_sms.send_message({'from': 'NexmoJapan', 'to': engineer, 'text': sms_text})
    
    sms_text = "RecFile https://rec_url.xxxx.jp/"+fname
    response_SMS = client_sms.send_message({'from': 'NexmoJapan', 'to': sales_1, 'text': sms_text})
    
    sms_text = "RecFile https://rec_url.xxxx.jp/"+fname
    response_SMS = client_sms.send_message({'from': 'NexmoJapan', 'to': sales_2, 'text': sms_text})
    
    return "ok"


session={}
client_sms = nexmo.Client(key=api_key, secret=api_secret)


@app.route('/ivrstart',methods=['GET', 'POST'])
def japanivr():

    arg_to = request.args['to']
    arg_from = request.args['from']

    session['to'] = arg_to
    session['from'] = arg_from

    logger.debug('From: %s', arg_from)
    logger.debug('To: %s', arg_to)

    ncco=[{
	        "action": "talk",
	        "text": "　　こちらは、ヴォネージジャパンです。営業におつなぎするには１とシャープを、技術におつなぎするには２とシャープを、録音メッセージを残すには３とシャープを入力してください",
            "bargeIn": "true",
	        "voiceName": "Mizuki"

	      },
          {
            "action": "input",
            "timeOut": "30",
            "submitOnHash": "true",
            "eventUrl": [ webhook_url + "/dtmfresponse"]
            }]
    js=json.dumps(ncco)
    resp=Response(js, status=200, mimetype='application/json')
    print(resp.data)
    return resp


@app.route('/dtmfresponse',methods=['GET', 'POST'])
def dtmfresponse():

    currentDT = datetime.datetime.now()
    date =currentDT.strftime("%Y-%m-%d %H:%M:%S")

    webhookContent = request.json
    print(webhookContent)
    try:
        result = webhookContent['dtmf']
    except:
        pass

    logger.debug("The User enter: " + str(result) + "\n")
    logger.debug(date)

    if result == '1':

        sms_text = "Hi Ryusuke, you have call from " + session['from'] + " on " + date


        response_SMS = client_sms.send_message({'from': 'NexmoJapan', 'to': sales_1, 'text': sms_text})

        logger.debug(response_SMS)
        logger.debug(sms_text)

        ncco = [
                 {
                    "action": "connect",
                    "eventUrl": [webhook_url+"/usercallback"],
                    "eventType": "synchronous",
                    "timeout": "45",
                    "from": virtual_number,
                    "endpoint": [
                     {
                        "type": "phone",
                        "number": sales_1
                     }
                ]
            }
              ]
        js = json.dumps(ncco)
        resp = Response(js, status=200, mimetype='application/json')
        logger.debug('Response NCCO with Ryu number')
        print(resp)
        return resp
    elif result == '2':
        #sms_text = "Hi Miya, you have call from " + session['from'] + " on " + date

        #response_SMS = client_sms.send_message({'from': 'NexmoJapan', 'to': engineer, 'text': sms_text})
        #logger.debug(response_SMS)
        #logger.debug(sms_text)
#
#        ncco = [
#            {
#                "action": "connect",
#                "eventUrl": [webhook_url+"/usercallback"],
#                "eventType": "synchronous",
#                "timeout": "45",
#                "from": virtual_number,
#                "endpoint": [
#                    {
#                        "type": "phone",
#                        "number": engineer
#                    }
#                ]
#            }
#        ]
#
        ncco = [
            {
                "action": "connect",
                "eventUrl": [webhook_url+"/event"],
                "from": [session['from']],
                "endpoint": [
                    {
                        "type": "sip",
                        "uri": "sip:100@3.113.20.214",
                        "headers":{}
                    }
                ]
            }
        ]
        
        js = json.dumps(ncco)
        resp = Response(js, status=200, mimetype='application/json')
        logger.debug('Response NCCO with Miya number')
        print(resp)
        return resp
    else:
        ncco = [
            {
                "action": "talk",
                "text": "　発信音の後にメッセージを録音してください",
                "voiceName": "Mizuki"
            },
            {
                "action": "record",
                "eventUrl": [webhook_url+"/recordings"],
                "beepStart": "true",
                "endOnSilence": 3
            }
        ]
        js = json.dumps(ncco)
        resp = Response(js, status=200, mimetype='application/json')
        logger.debug('Response NCCO to record call')
        print(resp)
        return resp
    return "success"


@app.route('/usercallback', methods=['GET', 'POST'])
def usercallback():

    currentDT = datetime.datetime.now()
    date =currentDT.strftime("%Y-%m-%d %H:%M:%S")

    call_state=['timeout','failed','rejected','unanswered','busy']

    webhookContent = request.json
    print(webhookContent)
    try:
        callee = webhookContent['to']
        status = webhookContent['status']
    except:
        pass

    logger.debug('callee: %s', callee)
    logger.debug('status: %s', status)
    logger.debug(call_state)

    if callee == sales_1 and str(status) in call_state:

        logger.debug('*******  Ryu did not answer  **********')

        sms_text = "Hi Atsushi, you have call from " + session['from'] + " on " + date

        response_SMS = client_sms.send_message({'from': 'NexmoJapan', 'to': sales_2, 'text': sms_text})
        logger.debug(response_SMS)
        logger.debug(sms_text)

        ncco = [
                 {
                    "action": "connect",
                    "eventUrl": [webhook_url+"/usercallback"],
                    "eventType": "synchronous",
                    "timeout": "45",
                    "from": virtual_number,
                    "endpoint": [
                     {
                        "type": "phone",
                        "number": sales_2
                     }
                                ]
                 }
              ]
        js = json.dumps(ncco)
        resp = Response(js, status=200, mimetype='application/json')
        logger.debug(js)
        print(resp)
        return resp
    elif (callee == sales_1 or sales_2) and status in call_state:

        logger.debug('*******  Ryu  or Atsushi did not answer  **********')

        ncco= [
                {
                   "action": "talk",
                   "text": "ただいま電話に出ることができません。発信音の後にメッセージを残してください。",
                   "voiceName": "Mizuki"
                },
                {
                    "action": "record",
                    "eventUrl": [webhook_url+"/recordings"],
                    "beepStart":"true",
                    "endOnSilence": 3
                }
              ]
        js = json.dumps(ncco)
        resp = Response(js, status=200, mimetype='application/json')
        print(resp)
        return resp
    else:
        return "do nothing"

    return "success"

@app.route('/recordings', methods=['GET', 'POST'])
def retrieverecording():

    webhookContent = request.json

    try:
        record_url = webhookContent['recording_url']
        record_uuid = webhookContent['recording_uuid']
    except:
        pass

    logger.debug("recording url: " + str(record_url))
    logger.debug("recorindg uuild: " + str(record_uuid))

    get_recording(record_url, record_uuid)

    return "OK"

@app.route('/event', methods=['GET', 'POST', 'OPTIONS'])
def display():
    r = request.json
    print(r)
    return "OK"


if __name__ == '__main__':
    app.run(port=web_port)

