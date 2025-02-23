#!/bin/bash

THIS_FILE=$(readlink -f "$0")
THIS_DIR=$(dirname "$THIS_FILE")
FILE_MAIN="${THIS_DIR}/local-teste.py"
DIR_VENV="${HOME}/local-venv"
FILE_ACTIVATE="${DIR_VENV}/bin/activate"

function add_venv(){
    echo -e "Criando VEVN em: $DIR_VENV\n"
    python3 -m venv "$DIR_VENV"
}

function config_venv(){
    local file_req="${THIS_DIR}/requirements.txt"
    source "$FILE_ACTIVATE"
    pip3 install --upgrade pip
    pip3 install -r "$file_req"

}

function main(){
    clear
    if [[ ! -d "$DIR_VENV" ]]; then
        echo "VENV não econtrada em: $DIR_VENV"
        add_venv
        config_venv
        return 1
    fi

    #config_venv; return
    echo -e "Ativando VEVN em: $FILE_ACTIVATE\n"
    source "$FILE_ACTIVATE"

    python3 "${FILE_MAIN}"
}

main $@
