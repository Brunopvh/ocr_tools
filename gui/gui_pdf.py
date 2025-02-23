#!/usr/bin/env python3
#

from threading import (Thread, Event)
from typing import List
import os
import time

import tkinter as tk
from tkinter import (
        Tk,
        ttk,
)

from tkinter.ttk import (
    Frame, 
)

from gui.gui_utils import (
    show_warnnings,
    GetWidgets,
    AppPage,
    ContainerExportFiles,
    ContainerImportFiles,
)

from libconvert import (
    DocumentPdf,
    PageDocumentPdf,
    ConvertPdfToImages,
    export_dataframe,
    FilesTypes,
)
from PIL import Image
from pandas import DataFrame
import pandas

#========================================================#
# Image/PDF para planilha (OCR)
#========================================================#
class PageConvertPdfs(AppPage):
    def __init__(self, *, parent, controller):
        super().__init__(parent=parent, controller=controller)
        self.pageName = '/home/select_actions/convert_pdf'
        # Frame Principal desta Tela
        self.widgets = GetWidgets(self)
        self.frame_master:Frame = self.widgets.get_frame(self)
        self.frame_master.pack()
        self.running = False
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
        
        # 2 - Dividir PDFs
        self.btn_to_pdf = ttk.Button(
            self.frame_buttons_export,
            text='Dividir PDF(s)',
            command=self.convert_to_split_pdf,
        )
        self.btn_to_pdf.pack(expand=True, fill='both', padx=2, pady=1)
        
        # 3 - Para TXT
        self.btn_to_txt = ttk.Button(
            self.frame_buttons_export,
            text='Para Arquivos TXT',
            command=self.convert_to_txt_multi,
        )
        self.btn_to_txt.pack(expand=True, fill='both', padx=2, pady=1)
        
        # 4 - Para Imagens
        self.btn_to_images = ttk.Button(
            self.frame_buttons_export,
            text='Para Imagens',
            command=self.convert_to_images,
        )
        self.btn_to_images.pack(expand=True, fill='both', padx=2, pady=1)
        
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
        th = Thread(target=self._operation_convet_to_excel)
        th.start()
        
    def _operation_convet_to_excel(self):
        """
            Obter os textos de um arquivo PDF e gerar um arquivo Excel.
        """
        if not self._check_selected_files():
            return
        self.running = True
        self.container_pbar.start_pbar()
        data:List[DataFrame] = []
        for num_file, pdf in enumerate(self.controller.selectedUserFiles):
            base_text = f'Lendo documento: [{num_file+1} de {self.controller.numSelectedFiles}] {pdf.basename()}'
            self.container_pbar.set_text_pbar(base_text)
            self.container_pbar.set_text_progress(
                f'{((num_file/self.controller.numSelectedFiles)*100):.2f}'
            )
            # Obter o DataFrame() das páginas do arquivo.
            document:DocumentPdf = DocumentPdf(file=pdf)
            current_df:DataFrame = document.get_table()
            if current_df.empty:
                continue
            data.append(current_df)
        # Exportar para excel
        out_file = self.controller.saveDir.join_file(f'documentos-pdfs.xlsx')
        self.container_pbar.set_text_pbar(
            f'Exportando Excel: {out_file.basename()}'
        )
        export_dataframe(pandas.concat(data), out_file)
        #
        self.container_pbar.set_text_pbar(f'[OK] arquivos exportados em: {self.controller.saveDir.basename()}')
        self.container_pbar.set_text_progress('100')
        self.container_pbar.stop_pbar()
        self.running = False
        
    def convert_to_split_pdf(self):
        """
            Dividir PDF
        """
        if not self._check_selected_files():
            return
        t = Thread(target=self._operation_convert_to_split_pdf)
        t.start()
        
    def _operation_convert_to_split_pdf(self):
        self.running = True
        self.container_pbar.start_pbar()
        #
        for num, file_pdf in enumerate(self.controller.selectedUserFiles):
            base_text = f'Lendo: {num+1} de {self.controller.numSelectedFiles} | {file_pdf.basename()}'
            self.container_pbar.set_text_pbar(base_text)
            self.container_pbar.set_text_progress(f'{(num/self.controller.numSelectedFiles)*100:.1f}')
            document:DocumentPdf = DocumentPdf(file=file_pdf)
            document.pages_to_files(self.controller.saveDir)
        #
        self.container_pbar.set_text_pbar(f'Arquivos exportados em: {self.controller.saveDir.basename()}!')
        self.container_pbar.set_text_progress('100')        
        self.container_pbar.stop_pbar()
        self.running = False
        
    def convert_to_txt_multi(self):
        if not self._check_selected_files():
            return
        t = Thread(target=self._operation_contert_to_txt_multi)
        t.start()
    
    def _operation_contert_to_txt_multi(self):
        if not self._check_selected_files():
            return
        self.running = True
        self.container_pbar.start_pbar()
        #
        ####
        data:List[DataFrame] = []
        for num_file, pdf in enumerate(self.controller.selectedUserFiles):
            base_text = f'Lendo documento: [{num_file+1} de {self.controller.numSelectedFiles}] {pdf.basename()}'
            self.container_pbar.set_text_pbar(base_text)
            
            self.container_pbar.set_text_progress(
                f'{((num_file/self.controller.numSelectedFiles)*100):.2f}'
            )
            
            # Converter as páginas em imagens PIL.
            document_pages:List[PageDocumentPdf] = DocumentPdf(file=pdf).get_pages()
            max_num = len(document_pages)
            for num_page, page_pdf in enumerate(document_pages):
                base_text_page = f'[Página: {num_page+1} de {max_num}]'
                self.container_pbar.set_text_pbar(f'{base_text} | {base_text_page}')
                
                current_text_in_page = page_pdf.extract_text()
                if (current_text_in_page is None) and (current_text_in_page == ''):
                    continue
                text = current_text_in_page.upper()
                
                # Exportar para TXT
                out_file = self.controller.saveDir.join_file(f'{pdf.name()}.txt')
                out_file.path.write_text(text)
        #
        self.container_pbar.set_text_pbar(f'[OK] arquivos exportados em: {self.controller.saveDir.basename()}')
        self.container_pbar.set_text_progress('100')
        self.container_pbar.stop_pbar()
        self.running = False 

    def convert_to_images(self):
        if not self._check_selected_files():
            return
        th = Thread(target=self._operation_convet_to_images)
        th.start()
        
    def _operation_convet_to_images(self):
        """
            Converter PDFs em Imagem
        """
        self.container_pbar.start_pbar()
        conv:ConvertPdfToImages = ConvertPdfToImages()
        for num, pdf in enumerate(self.controller.selectedUserFiles):
            current_info = f'Dividindo documento: [{num+1} de {self.controller.numSelectedFiles}] {pdf.basename()}'
            self.container_pbar.set_text_pbar(current_info)
            try:
                images:List[Image.Image] = conv.from_file_pdf(pdf)
            except Exception as e:
                print(e)
                print(f'[PULANDO] {num+1}')
                continue
            #
            num_images = len(images)
            image:Image.Image
            for n, image in enumerate(images):
                self.container_pbar.set_text_progress(f'{((n/num_images)*100):.2f}')
                new_info = f'Página {n+1} de {num_images}'
                self.container_pbar.set_text_pbar(f'{current_info} | [{new_info}]')
                out_file = self.controller.saveDir.join_file(f'{pdf.name()}-pag-{n+1}.png')
                image.save(out_file.absolute(), 'png')

        self.container_pbar.set_text_pbar('OK')
        self.container_pbar.set_text_progress('100')
        self.container_pbar.stop_pbar()
        
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
        self.parent.title(f"Load Images - Dividir PDFs")

    def update_state(self):
        pass
