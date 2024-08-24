#!/bin/bash

# Define the master connection (adjust as needed)
DRONE_IP="127.0.0.1"
MASTER_PORT="5760"

# Define the output connections
OUT_1="udp:127.0.0.1:14550"
OUT_2="udp:127.0.0.1:14551"

# Start MAVProxy with the defined parameters
mavproxy.py --master=tcp:${DRONE_IP}:${MASTER_PORT} --out=${OUT_1} --out=${OUT_2}

# design patterns
# clean arch
# clean code
# clean arch
# Domain driven design
# hexagonal arch
# design patterns enteprises
# SAGA
