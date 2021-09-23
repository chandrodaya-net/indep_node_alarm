cd /home/alert/indep_node_alarm;echo "[Unit]
Description=indep_node_alarm
After=network-online.target
[Service]
User=alert
WorkingDirectory=/home/alert/indep_node_alarm
ExecStart=/home/alert/venv/bin/python /home/alert/indep_node_alarm/indep_node_alarm.py
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=indep_node_alarm
Restart=on-failure
RestartSec=200
LimitNOFILE=4096
[Install]
WantedBy=multi-user.target" > indep_node_alarm.service;sudo mv indep_node_alarm.service /etc/systemd/system/;sudo systemctl enable indep_node_alarm.service
