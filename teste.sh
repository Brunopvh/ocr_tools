#!/bin/bash

THIS_FILE=$(readlink -f "$0")
THIS_DIR=$(dirname "$THIS_FILE")
FILE_MAIN="${THIS_DIR}/local-teste.py"

# venv
_PREFIX='var/venv'
DIR_VENV="${HOME}/${_PREFIX}"
FILE_ACTIVATE="${DIR_VENV}/bin/activate"
echo -e "[VENV LOCAL]: ${DIR_VENV}"

function main(){
    clear
    if [[ ! -d "$DIR_VENV" ]]; then
        echo "[!] VENV não econtrada em: $DIR_VENV"
        return 1
    fi

    source "$FILE_ACTIVATE"
    python3 "${FILE_MAIN}"
}

main $@