#!/bin/bash

name=$(basename "$PWD")
touch /etc/systemd/system/$name.service

cat > /etc/systemd/system/$name.service <<EOF 
[Unit]
Description="Best bot 4ever!"


[Service]
User=ubuntu
WorkingDirectory=$(pwd)
VIRTUAL_ENV=$(pwd)/venv
Environment=PATH=$VIRTUAL_ENV/bin:$PATH
ExecStart=$(pwd)/venv/bin/python main.py

[Install]
WantedBy=multi-user.target
EOF

python3 -m venv venv
./venv/bin/python -m pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

systemctl daemon-reload
systemctl start $name.service
systemctl enable $name.service
systemctl status $name.service