#!/usr/bin/env python3
#
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List
from pandas import DataFrame
  
#
class ABCImageBytesToText(ABC):
    def __init__(self, *, extractor_module:ABCModuleExtractor):
        super().__init__()
        self.extractor_module:ABCModuleExtractor = extractor_module
        self.lang:str = None ## APAGAR
        self.local_langs:List[str] = [] ## APAGAR
        
    @abstractmethod
    def to_table(self, img_bytes:bytes) -> DataFrame:
        """
            Converte um arquivo de imagem em DataFrame()
        """
        pass
    
    @abstractmethod
    def to_string(self, img_bytes:bytes) -> str:
        """
            Recebe um objeto de imagem e converte em string
        """
        pass
    
    @abstractmethod
    def to_text_data(self, img_bytes:bytes) -> str:
        """
            Recebe um objeto de imagem e converte em string no estilo DataFrame()
        """
        pass
    
    @abstractmethod
    def to_bytes_pdf(self, img_bytes:bytes) -> bytes:
        pass
    
    
class ABCImageFileToText(ABCImageBytesToText):
    def __init__(self, *, extractor_module):
        super().__init__(extractor_module=extractor_module)
        if not isinstance(extractor_module, ABCModuleExtractor):
            raise ValueError(f'{__class__.__name__}\n\nErro: Módulo inválido.\n{type(extractor_module)}\n')        
       
    @abstractmethod 
    def to_table(self, img_file:str):
        pass
    
    @abstractmethod
    def to_string(self, img_file:str):
        pass
    
    @abstractmethod
    def to_bytes_pdf(self, img_file:str):
        pass
    
    @abstractmethod
    def to_text_data(self, img_file:str) -> DataFrame:
        pass
    
#======================================================================#
# Abstração para o módulo que extrai o texto das imagens (OCR)
# pode ser implementado com pytesseract ou outros.
#======================================================================#
class ABCModuleExtractor(ABC):
    def __init__(self, *, cmd_executable:object, lang:str=None):
        self.cmd_executable:object = cmd_executable
        self.lang:str = lang
    
    @abstractmethod
    def image_to_string(self, img:object) -> str:
        pass
    
    @abstractmethod
    def image_to_bytes_pdf(self, img:object) -> bytes:
        pass