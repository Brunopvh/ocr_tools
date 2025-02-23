#!/usr/bin/env bash
#
#--------------------------------------------------#
# Installer Load Images - V 202-01-31
#--------------------------------------------------#

[[ -z "$HOME" ]] && HOME=~/

THIS_FILE=$(readlink -f $0)
THIS_DIR=$(dirname $THIS_FILE)
DIR_ROOT=$(dirname $THIS_DIR)

INSTALL_DIR="${HOME}/var/opt/load-images"
FILE_MAIN="${INSTALL_DIR}/app.sh"
FILE_BIN="${HOME}/bin/load-images"
FILE_DESKTOP="${HOME}/.local/share/applications/load-images.desktop"

function create_dirs(){
	mkdir -p "$INSTALL_DIR"
	mkdir -p $(dirname "$FILE_DESKTOP")
	mkdir -p $(dirname "$FILE_BIN")
	mkdir -p $(dirname "$FILE_MAIN")
}

function add_file_desktop(){

	echo '[Desktop Entry]' > "$FILE_DESKTOP"
	{
		echo -e "Name=Load Images"
		echo -e "Exec=${FILE_MAIN}";
		echo 'Terminal=false';
		echo 'Type=Application';
		echo -e "Categories=Utility;";
	} >> "$FILE_DESKTOP"
	chmod 777 "$FILE_DESKTOP"
	gtk-update-icon-cache
	return 0
}

function install_files(){
	cd "$DIR_ROOT"
	echo -e "Copiando arquivos..."
	cp -r -u * "${INSTALL_DIR}/"
	chmod +x "$FILE_MAIN"
	ln -sf "${FILE_MAIN}" "$FILE_BIN"
	return 0
}

function main(){
	create_dirs
	echo -e $DIR_ROOT
	install_files
	add_file_desktop
	echo 'OK'
}


main $@