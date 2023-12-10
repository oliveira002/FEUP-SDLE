BASE_PATH="$(pwd)"

gnome-terminal -- /usr/bin/python3.10 "$BASE_PATH/src/loadbalancer/LoadBalancer.py" p

gnome-terminal -- /usr/bin/python3.10 "$BASE_PATH/src/loadbalancer/LoadBalancer.py" b


sleep 2


gnome-terminal -- /usr/bin/python3.10 "$BASE_PATH/src/server/Server.py" 1225
sleep 1

gnome-terminal -- /usr/bin/python3.10 "$BASE_PATH/src/server/Server.py" 1226
sleep 1
gnome-terminal -- /usr/bin/python3.10 "$BASE_PATH/src/server/Server.py" 1227
sleep 1
gnome-terminal -- /usr/bin/python3.10 "$BASE_PATH/src/server/Server.py" 1228
sleep 1
gnome-terminal -- /usr/bin/python3.10 "$BASE_PATH/src/server/Server.py" 1229

# Introduce a 5-second delay
sleep 5
