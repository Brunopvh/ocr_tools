#!/usr/bin/env python3
#

import os
import time
from typing import (List)
from threading import Thread, Event

from gui.models import (
    File,
)

import tkinter as tk
from tkinter import ttk

from gui.gui_utils import (
    show_warnnings,
    GetWidgets,
    AppPage,
    ContainerExportFiles,
    ContainerImportFiles,
    ContainerProgressBar,
    ControllerApp,
)

from libconvert import (
    File,
    Directory,
    FilesTypes,    
    ConvertImagemToPagesPdf,
    PageDocumentPdf,
    DocumentPdf,
)

#========================================================#
# Converter IMAGENS em PDF
#========================================================#
class PageImagesToPdf(AppPage):
    """
        Esta página serve para manipulação de imagem, não será usado OCR aqui, apenas
    conversões.
    """
    def __init__(self, *, parent, controller):
        super().__init__(parent=parent, controller=controller)
        self.pageName = '/home/select_actions/imgs_to_pdf'

        # Frame Principal desta Tela
        self.widgets = GetWidgets(self)
        self.frame_master:ttk.Frame = self.widgets.get_frame(self)
        self.frame_master.pack()
        self.running = False
         
        #self.convert_pdf_to_images = ConvertPdfToFilesImage(self.controller.saveDir)
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
        self.frame_buttons_export = ttk.Frame(self.frame_main_window, style="DarkPurple.TFrame")
        self.frame_buttons_export.pack(expand=True, fill='both', padx=4, pady=3)
        
        # 1 - Imagens para PDF(s)
        self.btn_to_excel = ttk.Button(
            self.frame_buttons_export,
            text='Imagens para PDF(s)',
            command=self.convert_images_to_pdfs,
        )
        self.btn_to_excel.pack(expand=True, fill='both', padx=2, pady=1)
        
        # 2 - Imagens para PDF
        self.btn_to_pdf = ttk.Button(
            self.frame_buttons_export,
            text='Imagens para PDF',
            command=self.convert_images_to_uniq_pdf,
        )
        self.btn_to_pdf.pack(expand=True, fill='both', padx=2, pady=1)
        
        # 6 - Barra de progresso
        self.frame_pbar = self.widgets.get_frame(self.frame_master)
        self.frame_pbar.pack(expand=True, fill='both', padx=1, pady=1)
        self.container_pbar = self.widgets.container_pbar(self.frame_pbar)
     
    def _check_selected_files(self) -> bool:
        if len(self.controller.selectedUserFiles) < 1:
            show_warnnings('Selecione arquivos para prosseguir!')
            return False
        return True
        
    def convert_images_to_pdfs(self):
        if not self._check_selected_files():
            return
        th = Thread(target=self._operation_convet_images_to_pdfs)
        th.start()
        
    def _operation_convet_images_to_pdfs(self):
        """
            Converter imagens em PDF, cada imagem será um novo arquivo PDF.
        """
        self.running = True
        self.start_pbar()
        for num, image in enumerate(self.controller.selectedUserFiles):
            out_file = self.controller.saveDir.join_file(f'{image.name()}.pdf')
            self.set_text_progress(f'{((num/self.controller.numSelectedFiles)*100):.1f}')
            self.set_text_pbar(
                f'Convertendo: {num+1} de {self.controller.numSelectedFiles} | {out_file.basename()}'
            )
            #
            pages = ConvertImagemToPagesPdf().from_image_file(image.absolute())
            doc = DocumentPdf(file=out_file)
            doc.add_pages(pages)
            doc.save()
        
        self.set_text_progress('100')
        self.set_text_pbar('OK')
        self.stop_pbar()
        self.running = False
        
    def convert_images_to_uniq_pdf(self):
        """
            Converter várias imagens e um PDF.
        """
        if not self._check_selected_files():
            return
        t = Thread(target=self._operation_convert_to_uniq_pdf)
        t.start()
        
    def _operation_convert_to_uniq_pdf(self):
        self.running = True
        self.start_pbar()
        pages:List[PageDocumentPdf] = []
        for num, image in enumerate(self.controller.selectedUserFiles):
            self.set_text_progress(f'{((num/self.controller.numSelectedFiles)*100):.1f}')
            self.set_text_pbar(
                f'Convertendo: {num+1} de {self.controller.numSelectedFiles} | {image.basename()}'
            )
            #
            pages.extend(ConvertImagemToPagesPdf().from_image_file(image.absolute()))
        #
        out_file = self.controller.saveDir.join_file(f'{image.name()}.pdf')
        self.set_text_pbar(f'Exportando PDF: {out_file.basename()}')
        doc = DocumentPdf(file=out_file)
        doc.add_pages(pages)
        doc.save()
        self.set_text_progress('100')
        self.set_text_pbar('OK')
        self.stop_pbar()
        self.running = False
        
    def set_text_progress(self, text):
        self.container_pbar.set_text_progress(text)
        
    def set_text_pbar(self, text):
        self.container_pbar.set_text_pbar(text)
        
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
