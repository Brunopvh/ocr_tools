#!/bin/bash

THIS_FILE=$(readlink -f "$0")
THIS_DIR=$(dirname "$THIS_FILE")
FILE_MAIN="${THIS_DIR}/build.py"
DIR_VENV="${HOME}/local-venv"
FILE_ACTIVATE="${DIR_VENV}/bin/activate"

function main(){
    clear
    if [[ ! -d "$DIR_VENV" ]]; then
        echo "VENV não econtrada em: $DIR_VENV"
        return 1
    fi

    echo -e "Ativando VEVN em: $FILE_ACTIVATE\n"
    source "$FILE_ACTIVATE"
    echo -e "Executando: ${FILE_MAIN}"
    python3 "${FILE_MAIN}"
}

main $@
