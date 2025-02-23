#!/usr/bin/env python3
#
from __future__ import annotations
from typing import List
from abc import ABC, abstractmethod
from enum import Enum
#
from pathlib import Path
#
from io import BytesIO
from pandas import DataFrame
import pandas
#
from PIL import Image
#
from reportlab.pdfgen import canvas
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
#
from PyPDF2 import PdfReader, PdfWriter, PageObject
from pdf2image import convert_from_bytes, convert_from_path
#
try:
    from fitz import Page, Pixmap, Document
except:
    from pymupdf import Page, Pixmap, Document
#
from libconvert.utils.file import (
    File,
    Directory,
)
#


class LibraryPDF(Enum):
    PYPDF = 'pypdf2'
    FITZ = 'fitz'
    CANVAS = 'canvas'
    PDF2IMAGE = 'pdf2image'
    

#======================================================================#
# Página PDF
#======================================================================#
class ABCPagePdf(ABC):
        
    @abstractmethod
    def extract_text(self) -> str:
        pass

    @abstractmethod
    def rotate(self, degrees: int):
        pass

    @abstractmethod
    def export_to_pdf(self, output_path: str):
        pass

    @abstractmethod
    def to_bytes(self) -> bytes:
        pass

    @abstractmethod
    def export_to_png(self, output_path: str):
        pass

    @abstractmethod
    def to_image(self) -> Image.Image:
        pass


class PyPdf2PagePdf(ABCPagePdf):
    """Implementação para manipular páginas PDF com PyPDF2"""
    def __init__(self, page:PageObject, page_number: int):
        self.page:PageObject = page
        self.page_number:object = page_number

    def extract_text(self) -> str:
        return self.page.extract_text()

    def rotate(self, degrees: int):
        self.page.rotate(degrees)

    def export_to_pdf(self, output_path: str):
        """Exportar a página atual para um arquivo."""
        writer = PdfWriter()
        writer.add_page(self.page)
        with open(output_path, 'wb') as f:
            writer.write(f)

    def export_to_png(self, output_path: str):
        raise NotImplementedError("PyPDF2 não suporta exportação direta para PNG")
    
    def to_image(self):
        raise NotImplementedError("PyPDF2 não suporta exportação direta para Imagem PIL")
    
    def to_bytes(self) -> bytes:
        # Criar um PdfWriter
        pdf_writer = PdfWriter()
        
        # Adicionar o PageObject (página atual) ao escritor
        pdf_writer.add_page(self.page)
        
        # Escrever para um objeto BytesIO
        output_bytes = BytesIO()
        pdf_writer.write(output_bytes)
        
        # Obter os bytes
        pdf_bytes = output_bytes.getvalue()
        
        # Fechar o objeto BytesIO
        output_bytes.close()
        return pdf_bytes


class FitzPagePdf(ABCPagePdf):
    """Implementação para manipular páginas PDF com fitz"""
    def __init__(self, page: Page, page_number:int):
        self.page_number:int = page_number
        self.page:Page = page

    def extract_text(self) -> str:
        return self.page.get_text()

    def rotate(self, degrees: int):
        # Ajuste para rotação anti-horária
        current_rotation = self.page.rotation  # Obter rotação atual da página
        new_rotation = (current_rotation + degrees) % 360  # Atualizar a rotação acumulativa
        self.page.set_rotation(new_rotation)  # Aplicar a nova rotação
        #
        #self.page.set_rotation(degrees)

    def export_to_pdf(self, output_path: str):
        """Exportar a página atual para um arquivo."""
        pdf_document:Document = Document()
        pdf_document.insert_pdf(self.page.parent, from_page=self.page.number, to_page=self.page.number)
        pdf_document.save(output_path)

    def export_to_png(self, output_path: str):
        pix:Pixmap = self.page.get_pixmap(dpi=300)
        pix.save(output_path)

    def to_image(self):
        pix:Pixmap = self.page.get_pixmap(dpi=300)
        return pix.pil_image()
        
    def to_bytes(self):
        return self.page.write()

#======================================================================#
# FACADE de Página PDF
#======================================================================#
class PageDocumentPdf(ABCPagePdf):
    def __init__(self, page:ABCPagePdf):
        super().__init__()
        self.page:ABCPagePdf = page
        self._page_number:int = self.page.page_number

    @property
    def page_number(self) -> int:
        return self._page_number
    
    @page_number.setter
    def page_number(self, value:int):
        self._page_number = value
        self.page.page_number = value

    def extract_text(self) -> str:
        return self.page.extract_text()

    def rotate(self, degrees: int):
        print(f'ROTACIOANDO A PÁGINA {self.page_number}')
        self.page.rotate(degrees)

    def export_to_pdf(self, output_path: str):
        print(f'[Exportando a página {self.page_number}]: {output_path}')
        self.page.export_to_pdf(output_path)

    def export_to_png(self, output_path: str):
        print(f'[Exportando a página {self.page_number} para imagem]: {output_path}')
        self.page.export_to_png(output_path)

    def get_page_lines(self) -> List[str]:
        lines = self.page.extract_text()
        if (lines is None) or (lines == ''):
            return []
        return lines.split('\n')
    
    def get_page_table(self) -> DataFrame:
        lines = self.get_page_lines()
        index_page = [self.page_number] * len(lines)
        return DataFrame(
            {
                'PÁGINA_PDF': index_page,
                'TEXTO_LINHA': lines
            }
        )

    def to_bytes(self) -> bytes:
        return self.page.to_bytes()
    
    def to_image(self):
        return self.page.to_image()

#======================================================================#
# Criar várias Página PDF apartir de um arquivo ou de uma lista de bytes.
#======================================================================#
class CreatePagesPdf(object):
    """
        Builder para obter páginas PDF apartir de um arquivo PDF
    ou de bytes de páginas PDF.
    """
    def __init__(self, library:LibraryPDF=LibraryPDF.PYPDF):
        self.library = library
        
    @staticmethod
    def __get_pages_file_from_pypdf2(file_path: str) -> List[PyPdf2PagePdf]:
        reader = PdfReader(file_path)
        pages = [PyPdf2PagePdf(page, idx) for idx, page in enumerate(reader.pages)]
        return pages

    @staticmethod
    def __get_pages_file_from_fitz(file_path: str) -> List[FitzPagePdf]:
        doc = Document(file_path)
        pages = [FitzPagePdf(page, idx) for idx, page in enumerate(doc)]
        return pages

    @staticmethod
    def __create_pages_bytes_from_pypdf2(file_bytes: List[bytes]) -> List[PyPdf2PagePdf]:
        """
            Criar páginas PDF (PyPDF2) apartir de bytes
        """
        # Cria um novo escritor de PDF
        pdf_writer = PdfWriter()

        # Itera sobre a lista de bytes e adicionar as páginas ao PDF combinado
        for current_bytes in file_bytes:
            pdf_reader = PdfReader(BytesIO(current_bytes))  # Carrega o PDF a partir dos bytes
            for page in pdf_reader.pages:
                pdf_writer.add_page(page)  # Adiciona cada página ao escritor
        return [PyPdf2PagePdf(page, idx) for idx, page in enumerate(pdf_writer.pages)]
    
    @staticmethod
    def __create_pages_bytes_from_fitz(file_bytes: List[bytes]) -> List[FitzPagePdf]:
        """
            Criar páginas PDF (fitz) apartir de bytes
        """
        # Criar um novo documento PDF vazio
        merged_document = Document()

        # Itera sobre os bytes e insere as páginas no documento combinado
        for pdf_bytes in file_bytes:
            # Abre o PDF em memória
            temp_doc:Document = Document(stream=pdf_bytes, filetype="pdf")  
            # Insere todas as páginas do PDF temporário
            merged_document.insert_pdf(temp_doc)  
        pages = [FitzPagePdf(page, idx) for idx, page in enumerate(merged_document)]
        return pages

    def from_bytes_pages(self, pages_bytes: List[bytes]) -> List[PageDocumentPdf]:
        """
            Criar páginas PDF apartir de bytes
        """
        if self.library == LibraryPDF.PYPDF:
            all_pages = self.__create_pages_bytes_from_pypdf2(pages_bytes)
        elif self.library == LibraryPDF.FITZ:
            all_pages = self.__create_pages_bytes_from_fitz(pages_bytes)
        else:
            raise ValueError("Biblioteca inválida: escolha 'fitz' ou 'pypdf2'.")
        #
        return [PageDocumentPdf(p) for p in all_pages]
    
    def from_file_pdf(self, file_path:str) -> List[PageDocumentPdf]:
        """
            Retornar uma lista de páginas PDF apartir de um arquivo PDF
        """
        if self.library == LibraryPDF.PYPDF:
            all_pages = self.__get_pages_file_from_pypdf2(file_path)
        elif self.library == LibraryPDF.FITZ:
            all_pages = self.__get_pages_file_from_fitz(file_path) 
        else:
            raise ValueError("Biblioteca inválida: escolha 'fitz' ou 'pypdf2'.")      
        #
        return [PageDocumentPdf(p) for p in all_pages]

#======================================================================#
# Documento PDF
#======================================================================#
class DocumentPdf(object):
    """
        Representação de um arquivo PDF no disco, esse objeto pode ser criado
    sem que o arquivo precise existir em disco (os dados/páginas podem ser adiconados
    posteriormente).
    """
    def __init__(self, *, file: File | str | Path, library:LibraryPDF = LibraryPDF.PYPDF):
        if isinstance(file, str):
            file = File(file)
        elif isinstance(file, Path):
            file = File(file.absolute())

        self.file:File = file
        self.library = library # fitz ou PyPDF2
        self.create_pages_pdf:CreatePagesPdf = CreatePagesPdf(self.library)
        self._pages:List[PageDocumentPdf] = []
        self._num_pages:int = 0
        self._lines = [] # Converter todas as linhas de todas as páginas em lista de String.
        self.__current_text:str = '-'
        self.__current_progress:float = 0
        self.__running = False
        
    def is_running(self) -> bool:
        return self.__running

    def get_current_text_progress(self) -> str:
        return self.__current_text
    
    def get_current_progress_num(self) -> float:
        if self.__current_progress > 100:
            return 100
        if self.__current_progress < 0:
            return 0
        return f'{self.__current_progress}'

    def get_pages(self) -> List[PageDocumentPdf]:
        """
            Retorna uma lista com todas as páginas do Documento.
        """
        if len(self._pages) == 0:
            if not self.file.path.exists():
                raise ValueError(f'{__class__.__name__} o arquivo não existe: {self.file.absolute()}')
            self._pages = self.create_pages_pdf.from_file_pdf(self.file.absolute())
        return self._pages
    
    def get_num_pages(self) -> int:
        """Total de páginas"""
        if self._num_pages == 0:
            self._num_pages = len(self.get_pages())
        return self._num_pages

    def rotate_page(self, page_number: int, degrees: int):
        self.get_pages()[page_number].rotate(degrees)

    def page_to_file(self, page_number: int, output_path: str):
        """Exporta uma página como PDF"""
        self.get_pages()[page_number].export_to_pdf(output_path)

    def pages_to_files(self, export_dir:str, prefix:str='pag') -> None:
        """
            Exporta cada página para um novo arquivo PDF
        """
        if isinstance(export_dir, str):
            d:Directory = Directory(export_dir)
        else:
            d = export_dir
        for n, page in enumerate(self.get_pages()):
            file_pdf:str = d.join_file(f'{self.file.name()}-{prefix}-{n+1}.pdf').absolute()
            page.export_to_pdf(file_pdf)
            
    def extract_text_from_page(self, page_number: int) -> str:
        return self._pages[page_number].extract_text()

    def get_table(self) -> DataFrame:
        """
            Retornar um DataFrame() apartir das informações e linhas do PDF.
        Estrutura da tabale gerada:
            - PÁGINA:          Número da página correspondente.
            - TEXTO_LINHA:     Texto da linha correspondente.
            - ARQUIVO:         Caminho absoluto do arquivo no disco.
            - TAMANHO_ARQUIVO: Tamnho do arquivo em bytes.
            - PASTA:           Diretório do arquivo no disco.
            - MD5:             Hash MD5 do arquivo.
        """
        data:List[DataFrame] = []
        _current_md5 = self.file.md5()
        for page in self.get_pages():
            df = page.get_page_table() # DataFrame da página atual.
            num:int = len(df.values.tolist()) # Ajustar o tamanho de cada coluna.
            df['ARQUIVO'] = [self.file.absolute()] * num
            df['TIPO'] = [self.file.extension()] * num
            df['TAMANHO_ARQUIVO'] = [self.file.size()] * num
            df['PASTA'] = [self.file.dirname()] * num
            df['MD5'] = [_current_md5] * num
            data.append(df)
        return pandas.concat(data)
    
    def add_page(self, page: PageDocumentPdf):
        """
            Adiciona uma nova página ao documento.
        """
        if isinstance(page, PageDocumentPdf):
            page.page_number = len(self._pages) + 1
            self._pages.append(page)
            print(f'Página adicionada ao documento: [{page.page_number}]')
        else:
            print(f'Erro página não adicionada: [{type(page)}]')

    def add_pages(self, pages:List[PageDocumentPdf]):
        for p in pages:
            self.add_page(p)

    def add_pages_from_bytes(self, pages_bytes: List[bytes]):
        """
            Adiciona páginas a partir de uma lista de bytes de páginas PDF.
        """
        new_pages = self.create_pages_pdf.from_bytes_pages(pages_bytes)
        self.add_pages(new_pages)

    def _save_with_fitz(self, fp: File):
        """
            Salva o documento no disco, incluíndo todas as páginas (atuais e adicionadas)
        com a lib fitz.
        """
        pdf_document = Document()  # Cria um novo documento PDF
        for page in self.get_pages():
            # Insere as páginas no novo documento
            pdf_document.insert_pdf(
                page.page.page.parent,
                from_page=page.page.page.number,
                to_page=page.page.page.number
            )
        
        # Salva o documento final no disco
        pdf_document.save(fp.absolute())
        pdf_document.close()

    def _save_with_pypdf2(self, fp: File):
        """
            Salva o documento no disco, incluindo todas as páginas (atuais e adicionadas),
        usando PyPDF2.
        """
        writer = PdfWriter()
        for page in self.get_pages():
            if isinstance(page.page, PyPdf2PagePdf):  # Verifica se a página é do tipo PyPdf2
                writer.add_page(page.page.page)  # Adiciona a página ao writer
            else:
                raise TypeError("Todas as páginas devem ser do tipo PyPdf2PagePdf para salvar com PyPDF2.")
        
        # Salva o documento no caminho especificado
        with open(fp.absolute(), "wb+") as f:
            writer.write(f)

    def save(self, fp: File=None):
        """
            Exporta as páginas do documento para um arquivo PDF no disco.
        Se não for informado um novo arquivo no parâmetro, as páginas serão salvas no 
        ARQUIVO ATUAL.
        """
        if fp is None:
            fp = self.file
        #
        if isinstance(fp, str):
            fp = File(fp)
        elif isinstance(fp, Path):
            fp = File(fp.absolute())
        #
        print(f'Salvando documento: [{fp.absolute()}]')
        if self.library == LibraryPDF.FITZ:
            self._save_with_fitz(fp)
        elif self.library == LibraryPDF.PYPDF:
            self._save_with_pypdf2(fp)


########################################################################
# Converter PDFs em Imagens
########################################################################
class ABCPdfToImages(ABC):
    """
        Converte um PDF/Página em imagem(s) do tipo PIL.
    """
    def __init__(self):
        super().__init__()
        
    @abstractmethod
    def from_page_bytes(self, page_bytes:bytes) -> List[Image.Image]:
        pass
    
    @abstractmethod
    def from_file_pdf(self, file:File) -> List[Image.Image]:
        pass
    
    @abstractmethod
    def from_page_pdf(self, page:PageDocumentPdf) -> List[Image.Image]:
        pass
    
    
# Implementar com pdf2image
class ImplementPdfToImagesPdf2Image(ABCPdfToImages):
    """
        Implementação para converter PDFs em Imagens PIL com o pdf2image
    """
    def __init__(self):
        super().__init__()
        
    def from_file_pdf(self, file:File) -> List[Image.Image]:
        """
            Recebe um arquivo PDF e retorna as páginas do pdf em forma de lista de Imagens PIL
        """
        try:
            return convert_from_path(file.absolute(), dpi=350)
        except:
            return convert_from_path(file.absolute())
    
    def from_page_bytes(self, page_bytes:bytes) -> List[Image.Image]:
        """
            Recebe uma página PDF e converte os bytes da página PDF em Lista de Imagens PIL
        """
        return convert_from_bytes(page_bytes, dpi=300)
    
    def from_page_pdf(self, page:PageDocumentPdf) -> List[Image.Image]:
        return self.from_page_bytes(page.to_bytes())
    
    
# Implementar com fitz
class ImplementPdfToImagesFitz(ABCPdfToImages):
    """
        Implementação para converter PDFs em Imagens PIL com o fitz.
    """
    def __init__(self):
        super().__init__()
        
    def from_file_pdf(self, file:File) -> List[Image.Image]:
        """
            Recebe um arquivo PDF e retorna as páginas do pdf em forma de lista de Imagens PIL
        """
        _doc:Document = Document(file.absolute())
        num_pages = _doc.page_count
        values:List[Image.Image] = []
        for n in range(0, num_pages):
            pixmap:Pixmap = _doc[n].get_pixmap(dpi=350)
            # Converter Pixmap para uma imagem PIL
            mode = "RGB" if pixmap.alpha == 0 else "RGBA"  # Verifica se a imagem tem canal alpha
            values.append(
                Image.frombytes(mode, [pixmap.width, pixmap.height], pixmap.samples)
            )
        #_doc.close()
        return values
    
    def from_page_bytes(self, page_bytes:bytes) -> List[Image.Image]:
        """
            Recebe uma página PDF e converte os bytes da página PDF em Lista de Imagens PIL
        """
        _doc:Document = Document(stream=page_bytes)
        page:Page = _doc[0]
        pixmap:Pixmap = page.get_pixmap(dpi=350)
        # Converter Pixmap para uma imagem PIL
        mode = "RGB" if pixmap.alpha == 0 else "RGBA"  # Verifica se a imagem tem canal alpha
        #_doc.close()
        return [Image.frombytes(mode, [pixmap.width, pixmap.height], pixmap.samples)]
        
    def from_page_pdf(self, page:PageDocumentPdf) -> List[Image.Image]:
        return self.from_page_bytes(page.to_bytes())
    
########################################################################
# Converter PDFs em Imagens (FACADE) - Usar a implementação anterior.
# [PDF(file/bytes/page) => Imagens(PIL)]
########################################################################
class ConvertPdfToImages(ABCPdfToImages):
    """
        Converter PDFs(arquivo/página/bytes) em imagens PIL
    """
    def __init__(self, library:LibraryPDF=LibraryPDF.FITZ):
        super().__init__()
        if library == LibraryPDF.FITZ:
            self.convert_pdf_to_images = ImplementPdfToImagesFitz()
        elif library == LibraryPDF.PDF2IMAGE:
            self.convert_pdf_to_images = ImplementPdfToImagesPdf2Image()
        else:
            raise ValueError(f'Library inválida, use: fitz ou pdf2image')
        
    def from_file_pdf(self, file:File) -> List[Image.Image]:
        print(f'Obtendo Imagens apartir do arquivo: [{file.absolute()}]')
        return self.convert_pdf_to_images.from_file_pdf(file)
    
    def from_page_bytes(self, page_bytes:bytes) -> List[Image.Image]:
        print(f'Obtendo Images apartir de bytes')
        return self.convert_pdf_to_images.from_page_bytes(page_bytes)
    
    def from_page_pdf(self, page:PageDocumentPdf) -> List[Image.Image]:
        print(f'Obtendo imagens apartir da página PDF')
        return self.convert_pdf_to_images.from_page_pdf(page)
       
       
########################################################################     
# Build para criar o objeto PdfToImages()
########################################################################
class CreatePdfToImages(object):
    def __init__(self, library:LibraryPDF = LibraryPDF.FITZ):
        self.library = library
        
    def create(self) -> ConvertPdfToImages:
        return ConvertPdfToImages(self.library)
     
########################################################################
# Converter IMAGEM para Arquivo ou página PDF.
# [Imagem(PIL/file) => PDF(page)]
########################################################################
class ABCImageToPdf(ABC):
    def __init__(self):
        super().__init__()
        
    @abstractmethod
    def from_image_file(self, img:str) -> List[PageDocumentPdf]:
        pass
    
    @abstractmethod
    def from_image(self, img:Image.Image) -> List[PageDocumentPdf]:
        pass
    
 
class ImplementImageToPdfCanvas(ABCImageToPdf):
    """
        Implementação para converter uma imagem em página PDF (canvas).
    """
    def __init__(self):
        super().__init__()
        
    def from_image(self, img) -> List[PageDocumentPdf]:
        """
            Converter uma imagem PIL em página PDF  
        """
        img_reader = ImageReader(img)
        # Cria um buffer de memória para o PDF
        buffer = BytesIO()

        # Cria o canvas associado ao buffer
        c:Canvas = canvas.Canvas(buffer, pagesize=letter)
        c.drawImage(
                img_reader, 
                0, 
                0, 
                width=letter[0], 
                height=letter[1], 
                preserveAspectRatio=True, 
                anchor='c'
            )
        c.showPage()
    
        # Finaliza o PDF
        c.save()

        # Move o ponteiro do buffer para o início
        buffer.seek(0)

        # Obtém os bytes do PDF
        pdf_bytes = buffer.getvalue()

        # Fecha o buffer (opcional, mas recomendado)
        buffer.close()
        
        # Gerar a página PDF
        return CreatePagesPdf().from_bytes_pages([pdf_bytes])
    
    def from_image_file(self, img) -> List[PageDocumentPdf]:
        """
            Converter um arquivo de imagem em páginas PDF
        """
        # Cria um buffer de memória para o PDF
        buffer = BytesIO()

        # Cria o canvas associado ao buffer
        c:Canvas = canvas.Canvas(buffer, pagesize=letter)
        c.drawImage(
                img, 
                0, 
                0, 
                width=letter[0], 
                height=letter[1], 
                preserveAspectRatio=True, 
                anchor='c'
            )
        c.showPage()
    
        # Finaliza o PDF
        c.save()

        # Move o ponteiro do buffer para o início
        buffer.seek(0)

        # Obtém os bytes do PDF
        pdf_bytes = buffer.getvalue()

        # Fecha o buffer (opcional, mas recomendado)
        buffer.close()
        
        # Gerar a página PDF
        return CreatePagesPdf().from_bytes_pages([pdf_bytes])
    
    
class ConvertImagemToPagesPdf(ABCImageToPdf):
    """
        Converter Imagem em páginas PDF.
    """
    def __init__(self, library:LibraryPDF = LibraryPDF.CANVAS):
        super().__init__()
        if library == LibraryPDF.CANVAS:
            self._image_to_pdf:ABCImageToPdf = ImplementImageToPdfCanvas()
        else:
            raise ValueError(f'{__class__.__name__} Library inválida, use: Canvas')
        
    def from_image(self, img) -> List[PageDocumentPdf]:
        return self._image_to_pdf.from_image(img)
    
    def from_image_file(self, img) -> List[PageDocumentPdf]:
        return self._image_to_pdf.from_image_file(img)
