# office ocr

Este projeto é contém uma interface gráfica em Python Tk para minipular e editar documentos (imagens e PDFs).

- Combinar arquivos PDFs (Unir e dividir)
- Converter imagem em PDF(s)
- Extrair textos de imagens e PDFs

# Dependência externa - Tesseract para extrair texto das imagens 
    https://github.com/tesseract-ocr/tesseract

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