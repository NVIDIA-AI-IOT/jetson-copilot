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

# set -x

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

###
### Install Chromium if in Desktop/GUI environment (or forced)
### 

flag_install_chromium=false

echo "" | zenity --progress --text "Display test" --auto-close 2> /dev/null
if [ $? -eq 0 ]; then 
    log "Invoked in GUI/Desktop environmnet." -c "bright_blue"
	flag_install_chromium=true
else
	if [[ " $* " == *" --force-install-chromium "* ]]; then
		log "[WARN] Force install chromium specified" -c "yellow"
		flag_install_chromium=true
	fi
    log "[INFO] Not going to install Chromium as there is no display attached"
fi

if [ "$flag_install_chromium" = true ]; then
	if [ -x "$(command -v chromium)" ]; then
		log "[WARN] Chromium is already installed:   $(chromium --version)" -c "yellow"
	else
		log "Installing Chromium app from Snap Store ..."
		sudo snap install chromium
	fi
fi

###
### Docker install and setup
### 

flag_install_docker=false
DOCKER_DAEMON_CONFIG="/etc/docker/daemon.json"

if [ -x "$(command -v docker)" ]; then
	log "[WARN] Docker is already installed:   $(docker --version)"
	log "---- $DOCKER_DAEMON_CONFIG contents ----"
	cat $DOCKER_DAEMON_CONFIG
	log "\n------------------------------------------"
	if [[ " $* " == *" --force-install-docker "* ]]; then
		log "[WARN] Force (re)install docker specified"
		flag_install_docker=true
		### Uninstall Docker Engine 
		### https://docs.docker.com/engine/install/debian/#uninstall-docker-engine
		log "[INFO] Uninstalling Docker Engine and related packages ..."
		sudo apt-get -y purge docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin docker-ce-rootless-extras
	fi
else
	flag_install_docker=true
fi

if [ "$flag_install_docker" = true ]; then
	log "Installing Docker and setting up ..."

	sudo apt update
	log "Installing nvidia-container package ..."
	sudo apt install -y nvidia-container

	verions_numbers=(${L4T_VERSION//./ })
	L4T_VERSION_MAJOR=${verions_numbers[0]}

	if [ "$L4T_VERSION_MAJOR" == "35" ]; then
		log "JetPack 5.x :"
	elif [ "$L4T_VERSION_MAJOR" == "36" ]; then
		log "JetPack 6.x :"
		## Starting from JetPack 6.0 DP, the `nvidia-container`` package stop automatically installing Docker.
		## Following the official Docker installation flow.
		sudo apt install -y curl
		log "Installing Docker Engine ..."
		curl https://get.docker.com | sh && sudo systemctl --now enable docker
		sudo nvidia-ctk runtime configure --runtime=docker
	else
		log "[ERROR] unsupported architecture:  $ARCH"
		exit 1
	fi

	# Restart the Docker service and add your user to the docker group
	sudo systemctl restart docker
	sudo usermod -aG docker $USER
	#newgrp docker

	# Insert the `default-runtime` line
	if grep -q "\"default-runtime\": \"nvidia\"" "$DOCKER_DAEMON_CONFIG"; then
  		log "[INFO] Defulat-runtime nvidia is already added"
	else
		log "---- $DOCKER_DAEMON_CONFIG contents (before) ----"
		cat $DOCKER_DAEMON_CONFIG
		log "\n-------------------------------------------------"
		sudo sed 's|^{|{\n    "default-runtime": "nvidia",|' -i /etc/docker/daemon.json
		log "---- $DOCKER_DAEMON_CONFIG contents (after)  ----"
		cat $DOCKER_DAEMON_CONFIG
		log "\n-------------------------------------------------"
	fi

	# Restart Docker
	sudo systemctl daemon-reload && sudo systemctl restart docker

	# Execute newgrp command at last as it resets the bash session
	log "[WARN] newgrp command is executed, and your bash session is reset."
	newgrp docker
fi