#!/usr/bin/env python3
#
import os
import time
import clipboard
from typing import List
from threading import Thread
from gui.gui_utils import (
    GetWidgets,
    AppPage,
    ControllerApp,
    ContainerImportFiles,
    ContainerExportFiles,
    show_warnnings,
)

from tkinter import (
    Tk,
    Frame,
    ttk,
)

import tkinter as tk

from gui.models import (
    Directory,
    File,
)

from libconvert import (
    RecognizeImage,
    RecognizePdf,
    TextRecognizedBytes,
    TextRecognizedTable,
    TextRecognizedString,
    DocumentPdf,
    PageDocumentPdf,
    CreatePagesPdf,
    ConvertPdfToImages,
    LibraryPDF,
    FilesTypes,
    export_dataframe,
    
    ImageInvertColorFromFile,
)

import pandas
from pandas import DataFrame
from PIL import Image

#========================================================#
# Reconhecer Texto em PDF
#========================================================#
class PageRecognizePDF(AppPage):
    def __init__(self, *, parent, controller):
        super().__init__(parent=parent, controller=controller)
        self.pageName = '/home/select_actions/page_ocr_pdf'
        self.widgets_recognize:GetWidgets = GetWidgets(self)
        # Frame Principal desta Tela
        self.frame_master:Frame = self.widgets_recognize.get_frame(self)
        self.frame_master.pack()
        self.running = False
        self.recognizePdf:RecognizePdf = RecognizePdf(File(self.controller.user_prefs.prefs['path_tesseract']))
        self.reconizeImage = RecognizeImage(File(self.controller.user_prefs.prefs['path_tesseract'])) 
        self.convertPdfToImages:ConvertPdfToImages = ConvertPdfToImages()
        self.initUI()

    def initUI(self):
        #===============================================================#
        # 0 - Box Principal da janela (filho do master)
        #===============================================================#
        self.frame_main_window = self.widgets.get_frame(self.frame_master)
        self.frame_main_window.pack()
        
        #===============================================================#
        # 1 - Box Principal para os containers de importar e exportar.
        #===============================================================#
        self.main_frame_io = self.widgets.get_frame(self.frame_main_window)
        self.main_frame_io.pack(side=tk.LEFT)
        
        #===============================================================#
        # 2 - Box para importar Arquivos
        #===============================================================#
        self.frame_import_files = self.widgets.get_frame(self.main_frame_io)
        self.frame_import_files.pack(side=tk.LEFT, expand=True, fill='both', padx=1, pady=1)
        
        self.container_import_files = ContainerImportFiles(
            frame=self.frame_import_files, 
            controller=self.controller,
            input_files_type=FilesTypes.PDF
        )
        
        #===============================================================#
        # 3 - Box para exportar arquivos
        #===============================================================#
        self.frame_export_files = self.widgets.get_frame(self.main_frame_io)
        self.frame_export_files.pack(expand=True, fill='both', padx=1, pady=1)
        
        self.container_export = ContainerExportFiles(
            frame=self.frame_export_files,
            controller=self.controller,
            output_files_type=FilesTypes.ALL_TYPES,
        )
        
        #===============================================================#
        # 4 - Box Com botões para exportar
        #===============================================================#
        self.frame_buttons_export = ttk.Frame(self.frame_main_window, style="DarkPurple.TFrame")
        self.frame_buttons_export.pack(expand=True, fill='both', padx=4, pady=3)
        
        # 1 - Para Excel
        self.btn_to_excel = ttk.Button(
            self.frame_buttons_export,
            text='Exportar para Excel',
            command=self.convert_to_excel,
        )
        self.btn_to_excel.pack(expand=True, fill='both', padx=2, pady=1)
        
        # 2 - Para PDF(s)
        self.btn_to_pdf = ttk.Button(
            self.frame_buttons_export,
            text='Para Arquivos PDF(s)',
            command=self.convert_to_pdf_multi,
        )
        self.btn_to_pdf.pack(expand=True, fill='both', padx=2, pady=1)
        
        # 3 - Para TXT
        self.btn_to_txt = ttk.Button(
            self.frame_buttons_export,
            text='Para Arquivos TXT',
            command=self.convert_to_txt_multi,
        )
        self.btn_to_txt.pack(expand=True, fill='both', padx=2, pady=1)
        
        # 4 - Para Área de transferência
        self.btn_to_clipboard = ttk.Button(
            self.frame_buttons_export,
            text='Para Área de transferência',
            command=self.convert_to_clipboard,
        )
        self.btn_to_clipboard.pack(expand=True, fill='both', padx=2, pady=1)
        
        # 6 - Barra de progresso
        self.frame_pbar = self.widgets.get_frame(self.frame_master)
        self.frame_pbar.pack(expand=True, fill='both', padx=1, pady=1)
        self.container_pbar = self.widgets.container_pbar(self.frame_pbar)
     
    def _check_selected_files(self) -> bool:
        if len(self.controller.selectedUserFiles) < 1:
            show_warnnings('Selecione arquivos para prosseguir!')
            return False
        if not os.path.exists(self.controller.user_prefs.prefs['path_tesseract']):
            show_warnnings(f'Tesseract inválido:\n{self.controller.user_prefs.prefs["path_tesseract"]}')
            return False
        return True
        
    def convert_to_excel(self):
        if not self._check_selected_files():
            return
        if not self.check_running():
            return
        th = Thread(target=self._operation_convet_to_excel)
        th.start()
        
    def _operation_convet_to_excel(self):
        """
            Reconhecer textos de imagens e exportar os dados para excel.
        """
        if not self._check_selected_files():
            return
        self.running = True
        self.container_pbar.start_pbar()
        data:List[DataFrame] = []
        for num_file, pdf in enumerate(self.controller.selectedUserFiles):
            base_text = f'Reconhecendo texto: [{num_file+1} de {self.controller.numSelectedFiles}] {pdf.basename()}'
            self.container_pbar.set_text_pbar(base_text)
            self.container_pbar.set_text_progress(
                f'{((num_file/self.controller.numSelectedFiles)*100):.2f}'
            )
            #
            _table:TextRecognizedTable = self.recognizePdf.to_table(pdf)
            if _table.is_null():
                continue
            data.append(_table.to_data())
        # Exportar para excel
        out_file = self.controller.saveDir.join_file(f'recognized-pdfs.xlsx')
        self.container_pbar.set_text_pbar(f'Exportando Excel: {out_file.basename()}')
        export_dataframe(pandas.concat(data), out_file)
        #
        self.container_pbar.set_text_pbar(f'[OK] arquivos exportados em: {self.controller.saveDir.basename()}')
        self.container_pbar.set_text_progress('100')
        self.container_pbar.stop_pbar()
        self.running = False
        
    def convert_to_pdf_multi(self):
        """
            Converter em um novo arquivo PDF com o texto reconhecido.
        """
        if not self._check_selected_files():
            return
        if not self.check_running():
            return
        t = Thread(target=self._operation_convert_to_pdf_multi)
        t.start()
        
    def _operation_convert_to_pdf_multi(self):
        self.running = True
        self.container_pbar.start_pbar()
        
        for num_file, pdf in enumerate(self.controller.selectedUserFiles):
            base_text_file = f'Lendo arquivo: [{num_file+1} de {self.controller.numSelectedFiles}] | {pdf.basename()}'
            self.container_pbar.set_text_pbar(base_text_file)
            self.container_pbar.set_text_progress(f'{(num_file/self.controller.numSelectedFiles)*100:.1f}')
            print(base_text_file)
            try:
                images_pil:List[Image.Image] = self.convertPdfToImages.from_file_pdf(pdf)
            except Exception as e:
                print(e)
                continue
                
            max_num_images = len(images_pil)
            for num_pag, img in enumerate(images_pil):
                # Exportar página para um novo arquivo.
                out_file = self.controller.saveDir.join_file(f'ocr-{pdf.name()}-pag-{num_pag+1}.pdf')
                if out_file.path.exists():
                    base_text_pag = f'[PULANDO]: o arquivo já existe: {out_file.basename()}'
                    print(base_text_file)
                    self.container_pbar.set_text_pbar(base_text_pag)
                    continue
                base_text_pag = f'OCR página {num_pag+1} de {max_num_images}'
                self.container_pbar.set_text_pbar(f'{base_text_file} | [{base_text_pag}]')
                output_bytes = self.reconizeImage.image_to_bytes_pdf(img)
                if output_bytes.is_null():
                    continue
                # Converter em páginas PDF reconhecidas
                pages:List[PageDocumentPdf] = CreatePagesPdf().from_bytes_pages([output_bytes.BYTES])
                doc = DocumentPdf(file=out_file)
                doc.add_pages(pages)
                doc.save()
                #
        self.container_pbar.set_text_pbar(f'Arquivos exportados em: {self.controller.saveDir.basename()}!')
        self.container_pbar.set_text_progress('100')        
        self.container_pbar.stop_pbar()
        self.running = False
        
    def convert_to_txt_multi(self):
        if not self._check_selected_files():
            return
        if not self.check_running():
            return
        t = Thread(target=self._operation_contert_to_txt_multi)
        t.start()
    
    def _operation_contert_to_txt_multi(self):
        self.start_pbar()
        for num_file, pdf in enumerate(self.controller.selectedUserFiles):
            base_text_file = f'Lendo PDF: [{num_file+1} de {self.controller.numSelectedFiles}] | {pdf.basename()}'
            self.container_pbar.set_text_pbar(base_text_file)
            self.container_pbar.set_text_progress(f'{(num_file/self.controller.numSelectedFiles)*100:.1f}')
            # Converter as páginas em imagens
            try:
                images_pil:List[Image.Image] = self.convertPdfToImages.from_file_pdf(pdf)
            except Exception as e:
                print(e)
                continue
            
            max_num_images = len(images_pil)
            for num_pag, img in enumerate(images_pil):
                output_file = self.controller.saveDir.join_file(f'ocr-{pdf.name()}-pag-{num_pag+1}.txt')
                if output_file.path.exists():
                    self.container_pbar.set_text_pbar(f'[PULANDO] O arquivo já exite: {output_file.basename()}')
                    continue
                base_text_pag = f'OCR página {num_pag+1} de {max_num_images}'
                self.container_pbar.set_text_pbar(f'{base_text_file} | [{base_text_pag}]')
                output_text:TextRecognizedString = self.reconizeImage.image_to_string(img)
                if output_text.is_null():
                    continue
                print(f'Salvando: {output_file.absolute()}')
                output_file.path.write_text(output_text.to_string())
                #
        #
        self.container_pbar.set_text_pbar(f'Arquivos exportados em: {self.controller.saveDir.basename()}!')
        self.container_pbar.set_text_progress('100')        
        self.stop_pbar()
        self.running = False  

    def convert_to_clipboard(self):
        if not self._check_selected_files():
            return
        if not self.check_running():
            return
        th = Thread(target=self._operation_convet_to_clipboard)
        th.start()
        
    def _operation_convet_to_clipboard(self):
        """
            Reconhecer textos de PDF e exportar os dados para excel.
        """
        pass
        
    def start_pbar(self):
        self.running = True
        self.container_pbar.start_pbar()

    def stop_pbar(self):
        self.container_pbar.stop_pbar()
        self.running = False

    def go_home_page(self):
        """Voltar para Tela Principal"""
        self.controller.to_page('/home')

    def set_size_screen(self):
        self.parent.geometry("625x260")
        self.parent.title(f"OCR Tool - Reconhecer Texto em PDFs")

    def update_state(self):
        pass


#========================================================#
# Reconhecer Texto em Imagem
#========================================================#
class PageRecognizeImages(AppPage):
    def __init__(self, *, parent, controller):
        super().__init__(parent=parent, controller=controller)
        self.pageName = '/home/select_actions/page_ocr_imgs'
        self.parent:Tk = parent
        self.controller:ControllerApp = controller
        self.widgets_recognize:GetWidgets = GetWidgets(self)
        # Frame Principal desta Tela
        self.frame_master:Frame = self.widgets_recognize.get_frame(self)
        self.frame_master.pack()
        self.running = False
        self.recognizeImage:RecognizeImage = RecognizeImage(
            File(self.controller.user_prefs.prefs['path_tesseract'])
        )
        self._noRecognizedFiles:List[str] = []
        self.initUI()

    def initUI(self):
        #===============================================================#
        # 0 - Box Principal da janela (filho do master)
        #===============================================================#
        self.frame_main_window = self.widgets.get_frame(self.frame_master)
        self.frame_main_window.pack()
        
        #===============================================================#
        # 1 - Box Principal para os containers de importar e exportar.
        #===============================================================#
        self.main_frame_io = self.widgets.get_frame(self.frame_main_window)
        self.main_frame_io.pack(side=tk.LEFT)
        
        #===============================================================#
        # 2 - Box para importar Arquivos
        #===============================================================#
        self.frame_import_files = self.widgets.get_frame(self.main_frame_io)
        self.frame_import_files.pack(side=tk.LEFT, expand=True, fill='both', padx=1, pady=1)
        
        self.container_import_files = ContainerImportFiles(
            frame=self.frame_import_files, 
            controller=self.controller,
            input_files_type=FilesTypes.IMAGE
        )
        
        #===============================================================#
        # 3 - Box para exportar arquivos
        #===============================================================#
        self.frame_export_files = self.widgets.get_frame(self.main_frame_io)
        self.frame_export_files.pack(expand=True, fill='both', padx=1, pady=1)
        
        self.container_export = ContainerExportFiles(
            frame=self.frame_export_files,
            controller=self.controller,
            output_files_type=FilesTypes.ALL_TYPES,
        )
        
        #===============================================================#
        # 4 - Box Com botões para exportar
        #===============================================================#
        self.frame_buttons_export = ttk.Frame(self.frame_main_window, style="LightPurple.TFrame")
        self.frame_buttons_export.pack(expand=True, fill='both', padx=4, pady=3)
        
        # 1 - Para Excel
        self.btn_to_excel = ttk.Button(
            self.frame_buttons_export,
            text='Exportar para Excel',
            command=self.convert_to_excel,
        )
        self.btn_to_excel.pack(expand=True, fill='both', padx=2, pady=1)
        
        # 2 - Para PDF(s)
        self.btn_to_pdf = ttk.Button(
            self.frame_buttons_export,
            text='Para Arquivos PDF(s)',
            command=self.convert_to_pdf_multi,
        )
        self.btn_to_pdf.pack(expand=True, fill='both', padx=2, pady=1)
        
        # 3 - Para TXT
        self.btn_to_txt = ttk.Button(
            self.frame_buttons_export,
            text='Para Arquivos TXT',
            command=self.convert_to_txt_multi,
        )
        self.btn_to_txt.pack(expand=True, fill='both', padx=2, pady=1)
        
        # 4 - Para Área de transferência
        self.btn_to_clipboard = ttk.Button(
            self.frame_buttons_export,
            text='Para Área de transferência',
            command=self.convert_to_clipboard,
        )
        self.btn_to_clipboard.pack(expand=True, fill='both', padx=2, pady=1)
        
        # 5 - Escurecer imagens.
        self.btn_to_black_images = ttk.Button(
            self.frame_buttons_export,
            text='Escurecer imagens',
            command=self.convet_to_darktext,
        )
        self.btn_to_black_images.pack(expand=True, fill='both', padx=2, pady=1)
        
        # 6 - Barra de progresso
        self.frame_pbar = self.widgets.get_frame(self.frame_master)
        self.frame_pbar.pack(expand=True, fill='both', padx=1, pady=1)
        self.container_pbar = self.widgets.container_pbar(self.frame_pbar)
     
    def _check_selected_files(self) -> bool:
        if len(self.controller.selectedUserFiles) < 1:
            show_warnnings('Selecione arquivos para prosseguir!')
            return False
        return True
    
    def export_log(self):
        log_dir = self.controller.saveDir.concat('log')
        log_dir.mkdir()
        df = DataFrame({'NÃO APLICADO OCR': self._noRecognizedFiles})
        export_dataframe(df, log_dir.join_file('log-no-ocr.xlsx'))
        
    def convet_to_darktext(self):
        if not self._check_selected_files():
            return
        if not self.check_running():
            return
        th = Thread(target=self._operation_to_darktext)
        th.start()
    
    def _operation_to_darktext(self):
        self.start_pbar()
        self.controller.saveDir.mkdir()
        for num, image in enumerate(self.controller.selectedUserFiles):
            prog = (num/self.controller.numSelectedFiles) * 100
            self.container_pbar.set_text_progress(f'{prog:.1f}')
            self.container_pbar.set_text_pbar(
                f'Escurecendo texto: {num+1} de {self.controller.numSelectedFiles} | {image.basename()}'
            )
            outfile_image = self.controller.saveDir.join_file(image.basename())
            ImageInvertColorFromFile(image.absolute()).to_file(outfile_image.absolute())
        #
        self.container_pbar.set_text_pbar(
            f'[OK] Imagens exportadas em: {self.controller.saveDir.basename()}'
        )
        self.container_pbar.set_text_progress('100')
        self.stop_pbar()
        
    def convert_to_excel(self):
        if not self._check_selected_files():
            return
        if not self.check_running():
            return
        th = Thread(target=self._operation_convet_to_excel)
        th.start()
        
    def _operation_convet_to_excel(self):
        """
            Reconhecer textos de imagens e exportar os dados para excel.
        """
        self.start_pbar()
        data = []
       
        for num, image in enumerate(self.controller.selectedUserFiles):
            prog = (num/self.controller.numSelectedFiles) * 100
            self.container_pbar.set_text_progress(f'{prog:.1f}')
            self.container_pbar.set_text_pbar(
                f'Reconhecendo texto: {num+1} de {self.controller.numSelectedFiles} | {image.basename()}'
            )
            text = self.recognizeImage.image_file_to_table(image)
            if not text.is_null():
                text.remove_bad_chars()
                data.append(text.to_data())
        #
        out_file = self.controller.saveDir.join_file('imagens_para_planilha.xlsx')
        self.container_pbar.set_text_pbar(
            f'Exportando Excel: {self.controller.saveDir.basename()} | {out_file.basename()}'
        )
        try:
            df = pandas.concat(data)
            export_dataframe(df, out_file)
        except Exception as e:
            print(e)
            self.container_pbar.set_text_pbar('Erro na operação')
            self.container_pbar.set_text_progress('0')
            show_warnnings(f'Erro ao tentar exportar planilha!\n{e}')
        
        self.container_pbar.set_text_pbar(
            f'[OK] Arquivo exportado: {out_file.basename()}'
        )
        self.container_pbar.set_text_progress('100')
        self.stop_pbar()
        
    def convert_to_pdf_multi(self):
        if not self._check_selected_files():
            return
        if not self.check_running():
            return
        t = Thread(target=self._operation_convert_to_pdf_multi)
        t.start()
        
    def _operation_convert_to_pdf_multi(self):
        self.start_pbar()
        self.container_pbar.set_text_pbar('Iniciando operação!')
        self.container_pbar.set_text_progress('40')
        
        for num, image in enumerate(self.controller.selectedUserFiles):
            out_file = self.controller.saveDir.join_file(f'{image.name()}.pdf')
            if out_file.path.exists():
                print(f'[PULANDO] O arquivo já existe: {out_file.basename()}')
                self.container_pbar.set_text_pbar(f'[PULANDO] O arquivo já existe: {out_file.basename()}')
                self._noRecognizedFiles.append(image.absolute())
                continue
            
            self.container_pbar.set_text_progress(f'{(num/self.controller.numSelectedFiles) * 100:.1f}')
            self.container_pbar.set_text_pbar(
                f'Reconhecendo texto: {num+1} de {self.controller.numSelectedFiles} | {image.basename()}'
            )
            text_image = self.recognizeImage.image_to_bytes_pdf(image.absolute())
            #
            self.container_pbar.set_text_pbar(f'Exportando PDF: {out_file.basename()}')
            doc_pdf = DocumentPdf(file=out_file)
            doc_pdf.add_pages(CreatePagesPdf().from_bytes_pages([text_image.BYTES]))
            doc_pdf.save()
        #
        self.export_log()
        self.container_pbar.set_text_pbar(
            f'[OK] Arquivos exportados em: {self.controller.saveDir.basename()}'
        )
        self.container_pbar.set_text_progress('100')
        self.stop_pbar()  
        
    def convert_to_txt_multi(self):
        if not self._check_selected_files():
            return
        if not self.check_running():
            return
        t = Thread(target=self._operation_contert_to_txt_multi)
        t.start()
    
    def _operation_contert_to_txt_multi(self):
        self.start_pbar()
        self.container_pbar.set_text_pbar('Iniciando operação!')
        self.container_pbar.set_text_progress('40')
        
        for num, image in enumerate(self.controller.selectedUserFiles):
            prog = (num/self.controller.numSelectedFiles) * 100
            self.container_pbar.set_text_progress(f'{prog:.1f}')
            self.container_pbar.set_text_pbar(
                f'Reconhecendo texto: {num+1} de {self.controller.numSelectedFiles} | {image.basename()}'
            )
            out_file = self.controller.saveDir.join_file(f'{image.name()}.txt')
            text = self.recognizeImage.image_to_string(image.absolute())
            #
            if not text.is_null():
                self.container_pbar.set_text_pbar(f'Exportando TXT: {out_file.basename()}')
                out_file.path.write_text(text.to_string())
        #
        self.container_pbar.set_text_pbar(
            f'[OK] Arquivos exportados em: {self.controller.saveDir.basename()}'
        )
        self.container_pbar.set_text_progress('100')
        self.stop_pbar()   

    def convert_to_clipboard(self):
        if not self._check_selected_files():
            return
        if not self.check_running():
            return
        th = Thread(target=self._operation_convet_to_clipboard)
        th.start()
        
    def _operation_convet_to_clipboard(self):
        """
            Reconhecer textos de imagens e exportar os dados para excel.
        """
        self.start_pbar()
        data:List[str] = []
       
        for num, image in enumerate(self.controller.selectedUserFiles):
            prog = (num/self.controller.numSelectedFiles) * 100
            self.container_pbar.set_text_progress(f'{prog:.1f}')
            self.container_pbar.set_text_pbar(
                f'Reconhecendo texto: {num+1} de {self.controller.numSelectedFiles} | {image.basename()}'
            )
            img_pil = ImageInvertColorFromFile(image.absolute()).to_pil()
            #text:TextRecognizedTable = self.recognizeImage.image_file_to_table(image)
            text = self.recognizeImage.image_to_string(img_pil)
            if not text.is_null():
                data.append(text.to_string())
        #
        if len(data) < 1:
            show_warnnings('Falha o texto está vazio.')
            self.container_pbar.set_text_pbar(f'Falha')
        else:
            all_text = ""
            for text in data:
                all_text = f'{all_text}\n{text}'
            clipboard.copy(all_text)
            self.container_pbar.set_text_pbar(
                f'[OK] Texto copiado para área de transferência'
            )
        self.container_pbar.set_text_progress('100')
        self.stop_pbar()
        
    def start_pbar(self):
        self.running = True
        self.container_pbar.start_pbar()

    def stop_pbar(self):
        self.container_pbar.stop_pbar()
        self.running = False

    def go_home_page(self):
        """Voltar para Tela Principal"""
        self.controller.to_page('/home')

    def set_size_screen(self):
        self.parent.geometry("625x260")
        self.parent.title(f"OCR Tool - Reconhecer Texto em Imagens")

    def update_state(self):
        pass
