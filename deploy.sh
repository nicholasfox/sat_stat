#!/bin/bash
cd /home/nicholas/workspace/agents/sat_stat
pkill -f "python3.*analysis.py" 2>/dev/null
python3 analysis.py &
sleep 2
IP=$(ip addr show eth0 | grep -oP 'inet \K[\d.]+')
echo "Server: http://$IP:15001/"
