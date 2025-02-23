# OCR Tool

Este projeto é contém uma interface gráfica em Python Tk para minipular e editar documentos (imagens e PDFs).

- Combinar arquivos PDFs (Unir e dividir)
- Converter imagem em PDF(s)
- Extrair textos de imagens e PDFs

# Módulos python externos
    PyPDF2      - (para manipulação de arquivos/bytes em PDF)
    pdf2image   - (para manipulação de arquivos/bytes em PDF)
    PyMuPDF     - (para manipulação de arquivos/bytes em PDF)
    reportlab   - (para manipulação de arquivos/bytes em PDF)
    openpyxl    - (para manipulação de planilhas Excel)
    pandas      - (para manipulação de dados)
    Pillow      - (para manipulação de imagens)
    pytesseract - (para manipulação reconhecimento de texto em imagem com o tesseract)
    opencv-python - (para manipulação de imagens)
    clipboard     - (para copiar e exportar textos para área de transferência)
    tqdm          - (para exibir uma barra de progresso durante a execução das operações)
    pyinstaller   - OPCIONAL (para exportar um binário executável do projeto Linux/Windows/Mac)

# Instalação do módulos
    pip install PyPDF2 pdf2image PyMuPDF reportlab openpyxl pandas Pillow pytesseract opencv-python clipboard tqdm pyinstaller

# Insalação do Tesseract Windows - baixe o instalador na página do projeto.
    https://github.com/tesseract-ocr/tesseract/releases

# Instalação do Tesseract Linux
    Debian/Ubuntu sudo apt install tesseract-ocr

# Execução do APP 
    Linux:
        - instaler os pacotes: Tk, VirtualEnv e Python3 
        sudo apt install python3 python3-venv python3-tk

        - Abra a pasta raiz deste projeto e crie uma venv local
        chmod +x add_venv.sh && ./add_venv.sh

        - Execute o APP
        ./app.sh

    Windows:
        - Instale o python3.11 ou superior
        
        - Instale as dependências
        pip.exe install -r requirements.txt

        - Execute o APP
        python.exe main.py

