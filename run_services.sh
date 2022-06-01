#!/bin/bash
~/Documents/asr_network/api/venv/bin/python ~/Documents/asr_network/api/utils/topology_mapper.py &
~/Documents/asr_network/api/venv/bin/python ~/Documents/asr_network/api/monitor.py &
~/Documents/asr_network/api/venv/bin/python ~/Documents/asr_network/api/utils/notify.py &
echo "Services running...."