#!/bin/bash

ROOT="$(dirname "$(readlink -f "$0")")"

# run the container
ARCH=$(uname -i)

set -ex

# check for jtop
JTOP_SOCKET=""
JTOP_SOCKET_FILE="/run/jtop.sock"

if [ -S "$JTOP_SOCKET_FILE" ]; then
	JTOP_SOCKET="-v /run/jtop.sock:/run/jtop.sock"
fi

if [ $ARCH = "aarch64" ]; then

	# this file shows what Jetson board is running
	# /proc or /sys files aren't mountable into docker
	cat /proc/device-tree/model > /tmp/nv_jetson_model

    docker run --runtime nvidia -it --rm --network host \
            --volume /tmp/argus_socket:/tmp/argus_socket \
            --volume /etc/enctune.conf:/etc/enctune.conf \
            --volume /etc/nv_tegra_release:/etc/nv_tegra_release \
            --volume /tmp/nv_jetson_model:/tmp/nv_jetson_model \
            --volume /var/run/dbus:/var/run/dbus \
            --volume /var/run/avahi-daemon/socket:/var/run/avahi-daemon/socket \
            --volume /var/run/docker.sock:/var/run/docker.sock \
            --volume $ROOT/Documents:/opt/jetson_copilot/Documents \
            --volume $ROOT/Indexes:/opt/jetson_copilot/Indexes \
            --volume $ROOT/logs:/data/logs \
            --volume $ROOT/ollama_models://data/models/ollama/models \
            --volume $ROOT/streamlit_app:/opt/jetson_copilot/app \
            --device /dev/snd \
            --device /dev/bus/usb \
            $DATA_VOLUME $DISPLAY_DEVICE $V4L2_DEVICES $I2C_DEVICES $JTOP_SOCKET $EXTRA_FLAGS \
            dustynv/jetrag:r36.3.0 \
            bash -c '/start_ollama && cd /opt/jetson_copilot/app/ && streamlit run ./app.py' \
            | tee  -a ./logs/container.log & pid=$!
    PID_LIST+=" $pid"
fi

echo "############################# $PID_LIST added to PID_LIST"

echo "" | zenity --progress --text "Display test" --auto-close 2> /dev/null
if [ $? -eq 0 ]
then 
    chromium --profile-directory="Default" --app="data:text/html,<html><body><script>window.resizeTo(560,1080);window.moveTo(1300,120);window.location='http://localhost:8501';</script></body></html>" & pid=$!
    PID_LIST+=" $pid"
else
    echo "no display"
fi

# tail -f ./logs/container.log

trap "kill $PID_LIST" SIGINT

echo "Parallel processes have started";

wait $PID_LIST

echo
echo "All processes have completed";

# echo "" | zenity --progress --text "Display test" --auto-close 2> /dev/null
# if [ $? -eq 0 ]
# then 
#     chromium
# else
#     echo "no display"
# fi

# tail -n10 ./logs/container.log

# sleep 100