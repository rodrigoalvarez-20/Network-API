#!/bin/bash
~/Documents/asr_network/api/venv/bin/python utils/topology_mapper.py &
~/Documents/asr_network/api/venv/bin/python monitor.py &
~/Documents/asr_network/api/venv/bin/python utils/notify.py &
echo "Services running...."