#!/bin/bash

### Color logger function

singal='\033[0;93m'
clear='\033[0m'

function log () {
  # check if message
  test -n "$1" || {
    echo;
    return;
  }
  printf "${singal}$1${clear}\n"
}

#############################################################
### L4T_VERSION retrieve logic
### Copied from https://github.com/dusty-nv/jetson-containers/blob/master/jetson_containers/l4t_version.sh
###vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv###

ARCH=$(uname -i)
log "ARCH:  $ARCH"

if [ $ARCH = "aarch64" ]; then
	L4T_VERSION_STRING=$(head -n 1 /etc/nv_tegra_release)

	if [ -z "$L4T_VERSION_STRING" ]; then
		#echo "reading L4T version from \"dpkg-query --show nvidia-l4t-core\""

		L4T_VERSION_STRING=$(dpkg-query --showformat='${Version}' --show nvidia-l4t-core)
		L4T_VERSION_ARRAY=(${L4T_VERSION_STRING//./ })	

		#echo ${L4T_VERSION_ARRAY[@]}
		#echo ${#L4T_VERSION_ARRAY[@]}

		L4T_RELEASE=${L4T_VERSION_ARRAY[0]}
		L4T_REVISION=${L4T_VERSION_ARRAY[1]}
	else
		#echo "reading L4T version from /etc/nv_tegra_release"

		L4T_RELEASE=$(echo $L4T_VERSION_STRING | cut -f 2 -d ' ' | grep -Po '(?<=R)[^;]+')
		L4T_REVISION=$(echo $L4T_VERSION_STRING | cut -f 2 -d ',' | grep -Po '(?<=REVISION: )[^;]+')
	fi

	L4T_REVISION_MAJOR=${L4T_REVISION:0:1}
	L4T_REVISION_MINOR=${L4T_REVISION:2:1}

	L4T_VERSION="$L4T_RELEASE.$L4T_REVISION"

	log "L4T_VERSION:  $L4T_VERSION"
	
elif [ $ARCH != "x86_64" ]; then
	log "unsupported architecture:  $ARCH"
	exit 1
fi

###^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^###
###  L4T_VERSION retrieve logic done
#############################################################

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
	
    verions_numbers=(${L4T_VERSION//./ })
	L4T_VERSION_MAJOR=${verions_numbers[0]}

    # https://hub.docker.com/r/dustynv/jetson-copilot/tags
	if [ "$L4T_VERSION_MAJOR" == "35" ]; then
		log "JetPack 5.x :"
        CONTAINER_TAG="r35.4.1"
	elif [ "$L4T_VERSION_MAJOR" == "36" ]; then
		log "JetPack 6.x :"
        CONTAINER_TAG="r36.3.0"
    fi

    if [ -z "$1" ]; then
        # No argument supplied, use the default container image hosted on Docker Hub
        CONTIANER_IMAGE="dustynv/jetson-copilot:$CONTAINER_TAG"
    else
        # Argument supplied, use the specified (potentially local) Docker container image
        CONTIANER_IMAGE=$1
    fi

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
            $CONTIANER_IMAGE \
            bash -c '/start_ollama && \
                cd /opt/jetson_copilot/app && \
                /bin/bash'
fi
