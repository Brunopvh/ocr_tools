#!/usr/bin/env python3
#
import os
import clipboard
from typing import List
from PIL import Image
import cv2
import pandas
import re

from libconvert.utils import (FormatDate, FormatString, is_valid_date)
from libconvert.docpdf.load_pdf import (
    CreatePagesPdf,
    PageDocumentPdf,
    DocumentPdf,
    LibraryPDF,
    ConvertImagemToPagesPdf,
    ConvertPdfToImages,
)

from libconvert.ocr.extractors import (
    TextImageExtractor,
    GetImageTextExtractor,
    TextRecognizedBytes,
    TextRecognizedTable,
    TextRecognizedString,
    TextRecognizedToi,
)

from libconvert.sheets.load import (
    ParseDF,
    DataFrame
)

from libconvert.common import get_path_tesseract_system
from libconvert.utils.file import (
    File,
)
#
class RecognizeImage(object):
    """
        Reconher texto em imagem (arquivo/imagem PIL/bytes de imagem)
    """
    def __init__(self, path_tesseract:File, *, lang:str='por'):
        self.path_tesseract:File = path_tesseract
        self.lang = lang
        self._extractor:TextImageExtractor = GetImageTextExtractor(
                                                        path_tesseract=self.path_tesseract, 
                                                        lang=self.lang
                                                    ).get()
        # Progresso das operações
        self.__current_text:str = ''
        self.running = False
        
    def __show_progress(self):
        print(f'{__class__.__name__}() | {self.__current_text}')
    
    def get_current_text(self) -> str:
        return self.__current_text
    
    def image_file_to_table(self, file:File) -> TextRecognizedTable:
        """Reconhecer o texto apartir de um arquivo de imagem"""
        self.__current_text = f'Reconhecendo texto do arquivo: {file.basename()}'
        self.__show_progress()
        text:TextRecognizedTable = self._extractor.to_table(file.absolute())
        return TextRecognizedTable(text)
    
    def image_obj_to_table(self, image:object) -> TextRecognizedTable:
        """Reconhecer o texto apartir de uma imagem PIL ou bytes de imagem"""
        self.__current_text = 'Reconhecendo texto em imagem'
        self.__show_progress()
        text:str = self._extractor.to_string(image)
        if (text is None) or (text == ""):
            return TextRecognizedTable()
        return TextRecognizedTable(DataFrame({'TEXTO_LINHA': text.split('\n')}))
    
    def image_to_bytes_pdf(self, image:object) -> TextRecognizedBytes:
        """Reconhecer apartir de imagem PIL ou arquivo"""
        self.__current_text = f'Convertendo imagem em bytes PDF'
        self.__show_progress()
        text = self._extractor.to_bytes_pdf(image)
        return TextRecognizedBytes(text)
    
    def image_to_string(self, img:object) -> TextRecognizedString:
        self.__current_text = 'Convertertendo texto de imagem em string'
        self.__show_progress()
        return TextRecognizedString(self._extractor.to_string(img))
    
    def clip_board_to_string(self) -> str:
        """
            Copie o caminho completo de um arquivo para ser lido aqui.
        """
        img = clipboard.paste()
        return self.image_to_string(img).to_string()
        
    def clip_board_to_clipboard(self) -> None:
        pass
     
class RecognizePdf(object):
    """
        Reconhecer texto em documento PDF digitalizado usando o tesseract
    a entrada de dados pode ser: Arquivo pdf, página pdf ou bytes de uma página pdf.
    """
    def __init__(self, path_tesseract:File, *, lang:str='por'):
        if not path_tesseract.path.exists():
            print(f'{__class__.__name__}\n o arquivo não existe: {path_tesseract.absolute()}')
        
        self.path_tesseract:File = path_tesseract
        self.lang:str = lang
        # Obter dados do PDF para converter em imagem PIL
        self.convertPdfToImages:ConvertPdfToImages = ConvertPdfToImages()
        # Reconhecer texto em Imagens.
        self.recognizeImage:RecognizeImage = RecognizeImage(self.path_tesseract, lang=self.lang)
        # Extrair texto de imagens
        self.textExtractorImages:TextImageExtractor = GetImageTextExtractor(
                                                        path_tesseract=self.path_tesseract,
                                                        lang=self.lang
                                                    ).get()
        
        self.__current_prog:float = 0
        self.__current_text:str = '-'
        self.running = False
        
    def get_current_progress(self) -> float:
        return self.__current_prog
    
    def get_text_progress(self) -> str:
        return self.__current_text
    
    def is_running(self) -> bool:
        return self.running
    
    def __show_progress(self):
        print(f'{self.get_current_progress():.1f}% | {self.get_text_progress()}')
        
    def __from_images_obj(self, images:List[Image.Image]) -> List[PageDocumentPdf]:
        """
            Reconhecer os textos nas páginas convertidas em imagem e retornar uma lista
        de páginas PDF.
        """  
        self.running = True
        max_num = len(images)
        values = []
        for num, img in enumerate(images):
            self.__current_prog = (num/max_num) * 100
            self.__current_text = f'{__class__.__name__}() Convertendo: {num+1} de {max_num}'
            self.__show_progress()
            #output_bytes = self.textExtractorImages.to_bytes_pdf(img)
            output_bytes:TextRecognizedBytes = self.recognizeImage.image_to_bytes_pdf(img)
            if output_bytes.is_null():
                continue
            values.append(output_bytes.BYTES)
        self.running = False
        return CreatePagesPdf(LibraryPDF.PYPDF).from_bytes_pages(values)
        
    def from_file_pdf(self, file:File) -> List[PageDocumentPdf]:
        """
            Recebe um ARQUIVO pdf e retorna uma lista de páginas com o texto já reconhecido.
        """
        images:List[Image.Image] = self.convertPdfToImages.from_file_pdf(file)
        return self.__from_images_obj(images)
        
    def from_pages(self, pages:List[PageDocumentPdf]) -> List[PageDocumentPdf]:
        """
            Recebe uma lista de páginas pdf e retorna uma lista de páginas pdf com o texto reconhecido.
        """
        images:List[Image.Image] = [] 
        for page in pages:
            images.extend(
                self.convertPdfToImages.from_page_pdf(page)
            )
        return self.__from_images_obj(images)
    
    def to_table(self, file_pdf:File) -> TextRecognizedTable:
        """
            Reconhece os textos das páginas de um PDF e retorna um objeto
        TextRecognizedTable()
        """
        if not isinstance(file_pdf, File):
            raise ValueError(f'{__class__.__name__} image precisa ser do tipo File() não {type(file_pdf)}')
        # Converter as páginas em imagens PIL.
        images_pages:List[Image.Image] = self.convertPdfToImages.from_file_pdf(file_pdf)
        max_num = len(images_pages)
        data:List[DataFrame] = []
        # Reconhecer o texto de cada página.
        for num, img in enumerate(images_pages):
            print(f'{__class__.__name__}() Gerando Tabela: {num+1} de {max_num}')
            #current_bytes:bytes = self.textExtractorImages.to_bytes_pdf(img)
            current_bytes:TextRecognizedBytes = self.recognizeImage.image_to_bytes_pdf(img)
            if current_bytes.is_null():
                continue
            data_in_page:DataFrame = CreatePagesPdf().from_bytes_pages(
                    [current_bytes.BYTES]
                )[0].get_page_table()
            #
            len_data:int = len(data_in_page)
            if data_in_page.empty:
                continue
            data_in_page['ARQUIVO'] = [file_pdf.absolute()] * len_data
            data_in_page['PASTA'] = [file_pdf.dirname()] * len_data
            data_in_page['MD5'] = [file_pdf.md5()] * len_data
            data.append(data_in_page)
        #
        try:
            return TextRecognizedTable(pandas.concat(data))
        except Exception as e:
            print(e)
            return TextRecognizedTable()
        

# Clarear fundo de imagens e escurecer o texto:
class ImageInvertColorFromFile(object):
    """
        Escurecer texto em imagens.
    """
    def __init__(self, image_file:str):
        # Carrega a imagem em escala de cinza
        self.image_file = cv2.imread(image_file, cv2.IMREAD_GRAYSCALE)
        self.image_result = None

    def preprocess(self):
        # Aplica um filtro Gaussiano para reduzir o ruído
        self.blurred = cv2.GaussianBlur(self.image_file, (5, 5), 0)

    def binarize(self):
        # Aplica binarização adaptativa (texto branco, fundo preto)
        self.binary = cv2.adaptiveThreshold(
            self.blurred,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,  # Inverte o texto para ser branco inicialmente
            11,
            2
        )

    def invert_colors(self):
        # Inverte as cores para que o texto fique preto e o fundo branco
        self.image_result = cv2.bitwise_not(self.binary)

    def save_result(self, output_path):
        # Salva a imagem processada
        print(f'Salvando: {output_path}')
        cv2.imwrite(output_path, self.image_result)

    def show_result(self):
        # Mostra a imagem processada
        cv2.imshow('Texto Preto, Fundo Branco', self.image_result)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
    def to_file(self, output_image):
        self.preprocess()
        self.binarize()
        self.invert_colors()
        self.save_result(output_image)
        #self.show_result()    
        
    def to_pil(self) -> Image.Image:
        self.preprocess()
        self.binarize()
        self.invert_colors()
        return Image.fromarray(self.image_result)       
    

class ImageToi(object):
    def __init__(self, *, file:File, path_tesseract:File, lang='por'):
        self.file:File = file
        self.recognize:RecognizeImage = RecognizeImage(path_tesseract, lang=lang)
        
    def to_text(self) -> TextRecognizedToi:
        string = self.recognize.image_to_string(self.file.absolute())
        if string.is_null():
            return TextRecognizedToi()
        return TextRecognizedToi(string.TEXT.split('\n'))
    

class ToiConvert(object):
    """
        
    """
    def __init__(self, data:TextRecognizedToi) -> None:
        self.data:TextRecognizedToi = data
        
        self.date_dmy = r'\b\d{2}/\d{2}/\d{4}\b'
        self.date_ymd = r'\b\d{4}/\d{2}/\d{2}\b' 
        self.regex_toi = r'TO[^\d]*(\d+)'
        self.regex_uc = r'U[^\d]*(\d+)'
        self.regex_roteiro = r"\d{1,2}/\d{1,3}/\d{1,4}/\d+"
        
    def __replace_chars(self, text, char, new_char) -> str:
        return re.sub(r'{}'.format(char), new_char, text)
        
    def __get_match(self, pattern, text:str) -> object | None:
        i = re.search(pattern, text)
        if i is None:
            return None
        return i.group()

    def table(self) -> DataFrame:
        tb = {
            'UC': [self.uc()],
            'TOI': [self.toi()],
            'ROTEIRO': [self.roteiro()],
            'TEXTO_LINHA': [self.data.line_uc().to_upper().value]
        }

    def toi(self) -> str:
        line = self.data.line_toi()
        if line.is_null():
            return 'nan'
        text = self.__get_match(self.regex_toi, line.value)
        return text if (text is not None) else 'nan'
    
    def uc(self) -> str:
        line = self.data.line_uc()
        if line.is_null():
            return 'nan'
        text = self.__get_match(self.regex_uc, line.value)
        return text if (text is not None) else 'nan'
    
    def roteiro(self) -> str:
        line = self.data.line_roteiro()
        if line.is_null():
            return 'nan'
        text = self.__get_match(self.regex_roteiro, line.value)
        return text if (text is not None) else 'nan'
    
    def postagem(self) -> str:
        return 'nan'
