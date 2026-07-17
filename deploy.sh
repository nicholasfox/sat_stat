#!/bin/bash
cd /home/nicholas/workspace/agents/sat_stat
pkill -f "analysis.py" 2>/dev/null
nohup python3 analysis.py > /dev/null 2>&1 &
sleep 2
IP=$(ip addr show eth0 | grep -oP 'inet \K[\d.]+')
echo "Server: http://$IP:15001/"
