#!/bin/bash
#
# Intalar uma VENV loacal em sistemas Linux
#
# Em sistemas Windows você pode instalar os módulos com o seguinte comando:
# pip.exe install PyPDF2 pdf2image PyMuPDF reportlab openpyxl pandas Pillow pytesseract opencv-python clipboard tqdm pyinstaller

THIS_FILE=$(readlink -f "$0")
THIS_DIR=$(dirname "$THIS_FILE")
PREFIX='var/venv'
DIR_VENV="${HOME}/${PREFIX}"
FILE_REQ="${THIS_DIR}/requirements.txt"

function add_venv(){
	echo -e "[+] Criando venv em: ${DIR_VENV}"
	python3 -m venv "$DIR_VENV"
}

function config_venv(){
	source "$DIR_VENV/bin/activate"
	pip3 install --upgrade pip
	pip3 install -r "$FILE_REQ"
}

add_venv
config_venv