#!/usr/bin/env python3
from __future__ import annotations
from typing import List, Dict
from abc import (ABC, abstractmethod)
from pathlib import Path
from pandas import DataFrame
from pytesseract import Output
from PIL import (Image, ImageFile)
import pandas
import pytesseract
import os
import io
import re
import clipboard
import subprocess
import platform
from pathlib import Path

from libconvert.utils import (
    File,
    Directory,
    FilesTypes,
    FormatDate,
    FormatString,
    ABCModuleExtractor,
    ABCImageFileToText,
)

def get_temp_dir(prefix=Path().home()) -> str:
    prefix = Path().home()
    sys_temp_dir = os.environ.get('TMP', os.path.join(prefix, 'var', 'temp'))
    if not sys_temp_dir:
        sys_temp_dir = os.path.join(prefix, 'var', 'temp')
    if not os.path.exists(sys_temp_dir):
        try:
            os.makedirs(sys_temp_dir)
        except Exception as e:
            print(e)
    os.environ["TEMP"] = sys_temp_dir
    print('-' * 30)
    print(f'Diretório temporário: {sys_temp_dir}')
    print('-' * 30)
    return sys_temp_dir

#======================================================================#
# Recognize Images
#======================================================================#
# Tipo de dado para guardar uma lista de DataFrame
class TextRecognizedTable(object):
    def __init__(self, data:DataFrame=None):
        self.TABLE:DataFrame = data
        if self.TABLE is not None:
            self.TABLE = self.TABLE.astype('str')
        #
        if not self.is_null():
            if 'TEXTO_LINHA' in self.TABLE.columns.tolist():
                self.__column_text = 'TEXTO_LINHA'
            elif 'text' in self.TABLE.columns.tolist():
                self.__column_text = 'text'

        #
        self.list_bad_char = [
                            ':', ',', ';', '$', '=', 
                            '!', '}', '{', '(', ')', 
                            '|', '\\', '‘', '*'
                            '¢', '“', '\'', '¢', '"', 
                            '#', '.', '<', '?', '>', 
                            '»', '@', '+', '[', ']',
                            '%', '~', '¥', '♀',
        ]


    def remove_bad_chars(self):
        # Substituindo os caracteres pela "_"
        for char in self.list_bad_char:
            self.TABLE = self.TABLE.replace(char, ' ')
        
    def to_upper(self) -> None:
        if 'text' in self.TABLE.columns.tolist():
            self.TABLE['text'] = self.TABLE['text'].str.upper()
        elif self.__column_text in self.TABLE.columns.tolist():
            self.TABLE[self.__column_text] = self.TABLE[self.__column_text].str.upper()
        
    def to_string(self) -> str | None:
        if self.is_null():
            return None
        return ", ".join(self.to_list())
    
    def to_list(self) -> List[str] | None:
        if self.is_null():
            return None
        if 'text' in self.TABLE.columns.tolist():
            return self.to_data()['text'].values.tolist()
        elif self.__column_text in self.TABLE.columns.tolist():
            return self.to_data()[self.__column_text].values.tolist()
    
    def to_data(self) -> DataFrame | None:
        if self.is_null():
            return None
        return self.TABLE
        
    def is_null(self) -> bool:
        if (self.TABLE is None) or (len(self.TABLE) < 1):
            return True
        return False

# Lista de bytes obtidos de uma imagem e processados com tesseract para representação de um 
# PDF, ou seja, cada byte dessa lista é uma página de PDF com o texto já reconhecido.
class TextRecognizedBytes(object):
    def __init__(self, item:bytes=None):
        self.BYTES:bytes = item
    
    def is_bytes(self) -> bool:
        if self.is_null():
            return False
        return True    
    
    def is_null(self) -> bool:
        if (self.BYTES is None):
            return True
        return False
    
class TextRecognizedString(object):
    def __init__(self, text:str=None):
        self.TEXT = text
        
    def is_null(self) -> bool:
        if (self.TEXT is None) or (self.TEXT == ''):
            return True
        return False
    
    def to_string(self) -> str | None:
        return self.TEXT
    
    def to_list(self) -> List[str] | None:
        if self.is_null():
            return None
        return self.TEXT.split('\n')
    
    def to_upper(self) -> None:
        self.TEXT = self.TEXT.upper()
  
class TextRecognizedToi(object):
    def __init__(self, list_text:List[str]):
        # Todas as linhas que foram reconhecidas em uma imagem.
        self.listText:List[str] = list_text
        if (len(list_text) > 0):
            values = []
            for i in list_text:
                if i == "":
                    continue
                values.append(i)
            self.listText = values
        # Expressões regulares
        self.regex_line_uc = r'.*U.*[^\d]*\d{3,}.*$.*'
        #self.regex_line_toi = r'.*TO.*[^\d]*\d{3,}.*$.*'
        self.regex_line_toi = r".*\bTO.{0,4}\d{3,}.*$"
        
        self.date_dmy = r'\b\d{2}/\d{2}/\d{4}\b'
        self.date_ymd = r'\b\d{4}/\d{2}/\d{2}\b' 
        self.regex_toi = r'TO[^\d]*(\d+)'
        self.regex_uc = r'U[^\d]*(\d+)'
        self.regex_roteiro = r"\d{1,2}/\d{1,3}/\d{1,4}/\d+"
        # re.search(r"TO\s*(.*)", texto)  # Captura tudo após "TO"
        #
        # apenas_numeros = re.sub(r"\D", "", texto)  # Remove tudo que não é número (\D)
        #
        # match = re.search(r"\d+", texto)  # Procura a primeira sequência de números
        # primeiro_numero = match.group()
        
    def __replace_chars(self, text, char, new_char) -> str:
        return re.sub(r'{}'.format(char), new_char, text)
        
    def __get_match_group(self, pattern, text:str) -> object | None:
        i = re.search(pattern, text)
        if i is None:
            return None
        return i.group()
    
    def __get_match_groups(self, pattern, text:str) -> object | None:
        i = re.search(pattern, text)
        if i is None:
            return None
        return i.groups()
    
    def is_null(self) -> bool:
        if len(self.listText) < 1:
            return True
        if self.listText is None:
            return True
        return False
        
    def to_string(self) -> str:
        return ', '.join(self.listText)
    
    def to_data(self) -> DataFrame:
        return DataFrame({'TEXTO_LINHA': self.to_list()})
    
    def to_list(self) -> List[str]:
        return self.listText
    
    def to_upper(self) -> TextRecognizedToi:
        new_list = []
        for item in self.listText:
            if item == "":
                continue
            new_list.append(item.upper())
        self.listText = new_list
        return self
    
    def remove_bad_chars(self) -> TextRecognizedToi:
        values = []
        for item in self.to_list():
            values.append(
                FormatString(item).replace_bad_chars(new_char='_').value
            )
        self.listText = values
        return self
    
    def uc(self) -> str:
        """
            Extrair o número da UC em forma de string, se a operação falhar, será retornado (nan)
        """
        if self.line_uc().is_null():
            return 'nan'
        t:str = self.__get_match_group(self.regex_uc, self.line_uc().value)
        if t is None:
            return 'nan'
        # Encontrar a primeira sequência de números.
        t = re.search(r"\d+", t)
        if t.group() is None:
            return 'nan'
        return re.sub(r"\D", "", t.group())
    
    def toi(self) -> str:
        if self.line_uc().is_null():
            return 'nan'
        t:str = self.__get_match_group(
            self.regex_toi, 
            self.line_uc().value,
        )
        if t is None:
            return 'nan'
        # Encontrar a seguna sequência de números.
        t = re.findall(r"\d+", t)
        if len(t) < 1:
            return 'nan'
        if len(t) >= 1:
            text_toi = t[0]
        return re.sub(r"\D", "", text_toi)
    
    def roteiro(self) -> str:
        self.remove_bad_chars()
        values:str = 'nan'
        for item in self.to_list():
            out = self.__get_match_group(self.regex_roteiro, item)
            if out is not None:
                values = out
                break
        if '/' in values:
            values = FormatString(values).replace_all('/', '-').value
        return values
    
    def line_postagem(self) -> str:
        self.remove_bad_chars()
        values:str = 'nan'
        for item in self.to_list():
            out = self.__get_match_group(self.date_dmy, item)
            if out is not None:
                values = out
                break
        return values
        
    def line_uc(self) -> FormatString:
        values = self.to_upper().to_list()
        line = None
        for item in values:
            content = self.__get_match_group(self.regex_line_uc, item)
            if content is not None:
                line = content
                break
        if line is None:
            return FormatString(None)
        s = FormatString(line).replace_all('/', '_').replace_all(':', '')
        return s if (len(s.value) < 70) else FormatString(s.value[0:70]) 
    
    def line_toi(self) -> FormatString:
        values = self.to_upper().to_list()
        values_toi = []
        for item in values:
            content = self.__get_match_group(self.regex_toi, item)
            if content is not None:
                values_toi.append(content)
        if values_toi == []:
            return FormatString(None)
        s = FormatString(', '.join(values_toi)).replace_all('/', '_').replace_all(':', '')
        return s #if (len(s.value) < 100) else FormatString(s.value[0:100])
    
    def line_roteiro(self) -> FormatString:
        return FormatString(None) 


#======================================================================#
# Implementar a extração/conversão de texto com pytesseract
#======================================================================#
class ImplementModuleExtractorPytesseract(ABCModuleExtractor):
    def __init__(self, *, cmd_executable:File, lang = None):
        super().__init__(cmd_executable=cmd_executable, lang=lang)
        self._extractor:pytesseract = pytesseract
        self._extractor.pytesseract.tesseract_cmd = cmd_executable.absolute()
        print(f'[TESSERACT CMD]: {cmd_executable.absolute()}')
        
    def image_to_bytes_pdf(self, img):
        if self.lang is None:
            return self._extractor.image_to_pdf_or_hocr(img)
        return self._extractor.image_to_pdf_or_hocr(img, lang=self.lang)
    
    def image_to_string(self, img):
        if self.lang is None:
            return self._extractor.image_to_string(img)
        return self._extractor.image_to_string(img, lang=self.lang)
    
    
#======================================================================#
# IMPLEMENTAR a extração de texto com um módulo que extraia texto
# atualmente está em uso o módulo implementado com pytesseract.
#======================================================================#     
class ImplementImageFileToText(ABCImageFileToText):
    """
        Extrair textos de objetos de imagem, podendo ser arquivos, PIL, ou bytes.
    """
    def __init__(self, *, extractor_module:ImplementModuleExtractorPytesseract):
        """
            extractor_module: 
                        é a implementação de um módulo que extraia texto de imagens
                        seguindo o contrato da classe ABCModuleExtractor()
                            
        """
        super().__init__(extractor_module=extractor_module)
        self.extractor_module:ImplementModuleExtractorPytesseract = extractor_module
            
    def __bytes_image_to_table(self, img_obj:bytes) -> object:
        """
            Recebe os bytes de uma imagem e retorna um DataFrame() com as informações 
        da imagem.
        """
        return self.to_text_data(img_obj)
        
    def __file_image_to_table(self, img_file:str) -> DataFrame:
        if not isinstance(img_file, str):
            raise ValueError(f'{__class__.__name__} image precisa ser do tipo File() não {type(img_file)}')
        
        text:List[str] = self.to_string(img_file).split('\n')
        num_lines = len(text)
        list_name_file = [os.path.basename(img_file)] * num_lines
        list_path_file = [img_file] * num_lines
        list_dir = [os.path.dirname(img_file)] * num_lines
        #
        tb = {}
        tb['TEXTO_LINHA'] = text
        tb['NOME'] = list_name_file
        tb['ARQUIVO'] = list_path_file
        tb['PASTA'] = list_dir
        return DataFrame(tb)
    
    def to_table(self, img) -> DataFrame:
        if isinstance(img, str):
            return self.__file_image_to_table(img)
        else:
            return self.__bytes_image_to_table(img)
    
    def to_bytes_pdf(self, file_image:str) -> bytes:
        """
            Recebe os bytes de uma imagem e retorna os bytes reconhecidos
        em forma de bytes PDF.
        """
        return self.extractor_module.image_to_bytes_pdf(file_image)
    
    def to_text_data(self, file_image:str) -> DataFrame:
        """
            Recebe uma imagem/objeto e retorna os textos no formato DataFrame().
        """
        text = self.to_string(file_image)
        if (text is None) or (text == ""):
            return None
        return DataFrame({'TEXTO_LINHA': text.split('\n')})
    
    def to_string(self, file_image:str) -> str:
        return self.extractor_module.image_to_string(file_image)
        
#======================================================================#
# FACADE que usa uma implementação qualquer de ABCImageFileToText()
#======================================================================#
class TextImageExtractor(object):
    """Usa um extrator de imagens para obter os textos."""
    def __init__(self, *, image_file_extractor:ABCImageFileToText):
        if not isinstance(image_file_extractor, ABCImageFileToText):
            raise ValueError(f'{__class__.__name__}\n\nErro: conversor inválido.\n{type(image_file_extractor)}\n')
        self.imageFileExtractor:ABCImageFileToText = image_file_extractor
        
    def _get_obj_image(self, img:object) -> object | None:
        try:
            if isinstance(img, bytes):
                image_object:Image.ImageFile = Image.open(io.BytesIO(img))
            elif isinstance(img, File):
                image_object = img.absolute()
            elif isinstance(img, str):
                image_object = img
            elif isinstance(img, Image.Image):
                image_object = img
        except Exception as e:
            raise ValueError(f'{__class__.__name__} Objeto/Imagem inválida {img}')
        else:
            return image_object
        
    def to_bytes_pdf(self, img:str | bytes) -> bytes:
        return self.imageFileExtractor.to_bytes_pdf(self._get_obj_image(img))
    
    def to_text_data(self, img:str | bytes) -> DataFrame:
        return self.imageFileExtractor.to_text_data(self._get_obj_image(img))
    
    def to_string(self, img:str | bytes) -> str:
        return self.imageFileExtractor.to_string(self._get_obj_image(img))
    
    def to_table(self, img:str)-> DataFrame:
        """Retorna um DataFrame com o texto da imagem"""
        return self.imageFileExtractor.to_table(self._get_obj_image(img))
    
#======================================================================#
# BUILD TextExtractor
#======================================================================#
class GetImageTextExtractor(object):
    """
        Builder para criar: TextImageExtractor()
    """
    def __init__(self, *, path_tesseract:File, lang='por'):
        if not isinstance(path_tesseract, File):
            raise ValueError(f'{__class__.__name__}\npath_tesseract precisa ser File() não {type(path_tesseract)}')
        
        self.path_tesseract:File = path_tesseract
        self.lang:str = lang
        
    def get(self) -> TextImageExtractor:
        _module = ImplementModuleExtractorPytesseract(cmd_executable=self.path_tesseract, lang=self.lang)
        _image_to_text = ImplementImageFileToText(extractor_module=_module)
        return TextImageExtractor(image_file_extractor=_image_to_text)

            
        
        
        
        
        

