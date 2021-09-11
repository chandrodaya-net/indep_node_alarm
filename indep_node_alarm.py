import json
import time
import requests # sudo pip3 install requests
from pdpyras import APISession
import subprocess
import shutil
import config_juno as config 
# import socket
# print(socket.gethostname())


height_increasing_time_period = 6 #600
missing_block_trigger = 10

def send_msg_to_telegram(msg):
    requestURL = "https://api.telegram.org/bot" + str(config.telegram_token) + "/sendMessage?chat_id=" + config.telegram_chat_id + "&text="
    requestURL = requestURL + str(msg)
    response = requests.get(requestURL, timeout=1)

def loop():
    try:
        status = json.loads(requests.get("http://localhost:26657/status").text)
        last_height = int(status["result"]["sync_info"]["latest_block_height"])
    except:
        last_height = 0
    
    while True:
        
        time.sleep(height_increasing_time_period)
    
        #cmd = "sudo <chain deamon> version --long > /home/ubuntu/ansible/<chain deamon>_version.out"
        #subprocess.check_output(cmd, shell=True)
        #cmd = "sudo <chaincli deamon> version --long > /home/ubuntu/ansible/<chaincli deamon>_version.out"
        #subprocess.check_output(cmd, shell=True)
        #cmd = "sudo python3 /home/ubuntu/ansible/indep_node_alarm_check.py"
        #subprocess.check_output(cmd, shell=True)
    
        alarm = False
        alarm_content = ""
        alarm_title = ""
        total, used, free = shutil.disk_usage("/")
        
        try:
            current_height = int(json.loads(requests.get("http://localhost:26657/status").text)["result"]["sync_info"]["latest_block_height"])
        except:
            current_height = last_height
        if (free//(2**30)) < 10:
            alarm = True
            alarm_title = "disk free 9GB"
            alarm_content = config.node_name + ": " + alarm_title
        # height doesn't change
        if current_height == last_height:
            alarm = True
            alarm_title = "height stucked!"
            alarm_content = config.node_name + ": " + alarm_title
        else:
            # missing count
            missing_block_cnt = 0
            for height in range(last_height+1,current_height+1):
                precommit_match = False
                try:
                    precommits = json.loads(requests.get("http://localhost:26657/commit?height=" + str(height)).text)["result"]["signed_header"]["commit"]["signatures"]
                    for precommit in precommits:
                        try:
                            validator_address = precommit["validator_address"]
                        except:
                            validator_address = ""
                        if validator_address == config.my_validator_address:
                            precommit_match = True
                            break
                    if precommit_match == False:
                        missing_block_cnt += 1
                except:
                    alarm = True
                    alarm_title = "chain daemon dead!"
                    alarm_content = config.node_name + ": " + alarm_title 
            if missing_block_cnt >= missing_block_trigger:
                alarm = True
                alarm_title = "missing blocks >= {}".format(missing_block_trigger)
                alarm_content =  """{node}: missing blocks={mb} >= {mbt}
                                 counting from height in range({lh}, {ch})""".format(node=config.node_name, 
                                                                                 mb=missing_block_cnt, 
                                                                                 mbt=missing_block_trigger,
                                                                                 lh=last_height+1,
                                                                                 ch=current_height+1)
    
        if alarm:
            session = APISession(config.pd_api_key, default_from=config.pd_default_email)
            payload = {
              "type": "incident",
              "title": alarm_title,
              "service": {"id": config.pd_service_id, "type": "service_reference"},
              "urgency": "high",
              "body": {
                  "type": "incident_body",
                  "details": alarm_content
                }
            }
            session.rpost("incidents", json=payload)
                    
            try:
                send_msg_to_telegram(alarm_content)
            except:
                pass
        else:
            msg = "{}: status OK!".format(config.node_name)
            send_msg_to_telegram(alarm_content) 
    
        last_height = current_height

if __name__ == "__main__":
    loop()
    
