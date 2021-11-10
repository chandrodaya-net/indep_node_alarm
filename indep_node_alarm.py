import json
import time
import requests # sudo pip3 install requests
from pdpyras import APISession
import subprocess
import shutil
import config 
import sys
from utils import create_logger
import traceback
# import socket
# print(socket.gethostname())

logger = create_logger(config.log_file_path, __name__ , config.log_level, True)

def send_msg_to_telegram(msg):
    try:
        requestURL = "https://api.telegram.org/bot" + str(config.telegram_token) + "/sendMessage?chat_id=" + config.telegram_chat_id + "&text="
        requestURL = requestURL + str(msg)
        requests.get(requestURL, timeout=1)
    except Exception:
        error_msg = traceback.format_exc()
        logger.error(error_msg)
            
    

def loop():
    logger.info("start loop")
    try:
        status = json.loads(requests.get("http://localhost:26657/status").text)
        last_height = int(status["result"]["sync_info"]["latest_block_height"])
    except:
        last_height = 0
    
    logger.info("last_height={}".format(last_height))
    while True:
        logger.info(" ********************** sleep: {}s ****************************".format(config.height_increasing_time_period))
        sys.stdout.flush()
        time.sleep(config.height_increasing_time_period)
    
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
        logger.info("check disk space")
        if (free//(2**30)) < 10:
            alarm = True
            alarm_title = "disk free 9GB"
            alarm_content = config.node_name + ": " + alarm_title
        logger.info("check height stucked")
        if current_height == last_height:
            alarm = True
            alarm_title = "height stucked!"
            alarm_content = config.node_name + ": " + alarm_title
        else:
            height_start = last_height+1 
            height_end = current_height+1
            logger.info("check missing count in range({}, {})".format(height_start, height_end))
            
            missing_block_cnt = 0
            for height in range(height_start, height_end):
                precommit_match = False
                logger.debug("  Height={}: missing_block_cnt={} """.format(height, missing_block_cnt))
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
            if missing_block_cnt >= config.missing_block_trigger:
                alarm = True
                alarm_title = "missing blocks >= {}".format(config.missing_block_trigger)
                alarm_content =  """{node}: missing blocks={mb} >= {mbt}
                                 counting from height in range({height_start}, {height_end})""".format(node=config.node_name, 
                                                                                 mb=missing_block_cnt, 
                                                                                 mbt=config.missing_block_trigger,
                                                                                 height_start=height_start,
                                                                                 height_end=height_end)
        logger.info("alarm={}".format(alarm))
        if alarm:
            if config.pd_notification:
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
                
                logger.info("""send alert to pageyduty:
                               alarm_content: {}""".format(alarm_content))        
            
            logger.info("alarm msg to telegram")
            send_msg_to_telegram(alarm_content)
        else:
            logger.info("Ok msg to telegram")
            msg = "{}: status OK!".format(config.node_name)
            send_msg_to_telegram(msg) 
    
        last_height = current_height
        

if __name__ == "__main__":
    loop()
    
