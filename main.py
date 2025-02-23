#!/usr/bin/env python3
#

"""
Configurações básicas para o reconhecimento de texto em imagens:

+ INSTALAR O TESSERACT (ou usar uma versão portável para Windows)
    1 - instalar o idioma pt-br para melhorar a detecção dos textos.
        Linux   -> sudo apt-get install tesseract-ocr-por
        Windows -> Baixe o arquivo por.traineddata (https://github.com/tesseract-ocr/tessdata)
                    salvar o arquivo no diretório tessdata (Na raiz da pasta tesseract)
                    
        - Defina o diretório onde os arquivos de linguagem estão localizados 
            os.environ['TESSDATA_PREFIX'] = r'C:\\caminho\\para\\o\\diretorio\\das\\linguagens'

    2 - Defina o Caminho para o Executável do Tesseract
        pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
        (Alterar o caminho se necessário)
        
    3 - Extraia o texto da imagem usando o idioma pt-BR 
            texto = pytesseract.image_to_string(imagem, lang='por')
            (já implementado no módulo OCR)    
        
    - Download do arquivo LANG em ptbr oficial.
        https://github.com/tesseract-ocr/tessdata/blob/main/por.traineddata

"""
import sys
import os

this_script = os.path.abspath(__file__) # Arquivo main.py
this_dir = os.path.dirname(this_script) # Diretório do raiz do projeto.

sys.path.insert(0, this_dir) # Para usar libs locais.
from gui.gui_master import runApp

def main():
    runApp()
    
if __name__ == '__main__':
    main()


