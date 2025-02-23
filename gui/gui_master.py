#!/usr/bin/env python3
#
from __future__ import annotations
import os
from typing import (List, Callable)
from threading import Thread

from tkinter import ttk
import tkinter as tk
from tkinter import (
        Tk,
        Menu,  
        filedialog, 
        messagebox,
)

from gui.gui_version import (
    __author__,
    __version__,
    __url__,
    __update__,
    __version_lib__,
)

from gui import (
    show_warnnings,
    GetWidgets,
    AppPage,
    ControllerApp,
    Navigator,
    PageRecognizeImages,
    PageRecognizePDF,
    PageConvertPdfs,
    PageImagesToPdf,
    PageMoveFiles,
)

from libconvert.common import (
    UserAppDir,
    get_path_tesseract_system,
)

from libconvert import (
    JsonConvert,
    JsonData,
    File,
)

#========================================================#
# Página com botões para seleção de ações.
#========================================================#
class PageSelectActions(AppPage):
    def __init__(self, *, parent, controller):
        super().__init__(parent=parent, controller=controller)
        self.pageName = '/home'
        self.widgets = GetWidgets(self)
        self.frame_master = self.widgets.get_frame(self)
        self.frame_master.pack(padx=20, pady=20)
        self.frame_master.config(style='Custom.TFrame')
        self.padding=(8, 9)
        self.initUI()
        
    def initUI(self):
        self._start_widgets()
        # Botão voltar
        self.btn_back = self.widgets.get_button(self.frame_master)
        self.btn_back.config(text='Voltar', command=lambda: self.controller.navigatorPages.pop())
        self.btn_back.pack()
      
    def _start_widgets(self):
        #=========================================================#
        # Frame para botões de reconhecimento de texto OCR
        #=========================================================#
        self.containerButtonsOcr = self.widgets.get_frame(self.frame_master)
        self.containerButtonsOcr.config(style="LightPurple.TFrame")
        self.containerButtonsOcr.pack(expand=True, fill='both', padx=1, pady=1)
        
        # Texto de topo
        self._container_label_top = ttk.Frame(self.containerButtonsOcr)
        self._container_label_top.pack(expand=True, fill='both', padx=3, pady=1)
        self.labelTextOcrDocs = self.widgets.get_label(self._container_label_top, text='OCR')
        self.labelTextOcrDocs.pack(padx=1, pady=1)
        
        # Container OCR 1
        self.containerOcr1 = self.widgets.get_frame(self.containerButtonsOcr)
        self.containerOcr1.pack(expand=True, fill='both', padx=3, pady=1)
        
        # Botão Reconhecer Imagens
        self.btn_images_to_pdf = self.widgets.get_button(
            self.containerOcr1, 
            text='Reconhecer Imagens (OCR)',
            cmd=lambda: self.to_page('/home/select_actions/page_ocr_imgs')
            #cmd=lambda: self.controller.navigatorPages.push('/home/select_actions/page_ocr_imgs')
        )
        self.btn_images_to_pdf.pack(side=tk.LEFT, expand=True, fill='both', padx=1, pady=1)
        
        # Botão Reconhecer PDF
        self.btn_recognize_pdfs = self.widgets.get_button(
            self.containerOcr1,
            text='Reconhecer PDFs (OCR)',
            cmd=lambda: self.to_page('/home/select_actions/page_ocr_pdf'),
        )
        self.btn_recognize_pdfs.pack(side=tk.LEFT, expand=True, fill='both', padx=1, pady=1)

        #=========================================================#
        # Frame para botões de conversão PDF e Imagens
        #=========================================================#
        self.containerButtonsDocuments = self.widgets.get_frame(self.frame_master)
        self.containerButtonsDocuments.pack(expand=True, fill='both', padx=2, pady=2)
        # Texto de topo do Frame
        self.label_info_pdf = self.widgets.get_label(self.containerButtonsDocuments)
        self.label_info_pdf.config(text='Editar documentos PDF/Imagens')
        self.label_info_pdf.pack()

        # Primeiro container PDF
        self.containerConvertDocs = self.widgets.get_frame(self.containerButtonsDocuments)
        self.containerConvertDocs.config()
        self.containerConvertDocs.pack(expand=True, fill='both', padx=2, pady=2)

        # Botão Converter PDF
        self.btn_uniq_pdf = self.widgets.get_button(self.containerConvertDocs)
        self.btn_uniq_pdf.config(
            text='Converter PDF',
            command=lambda: self.to_page('/home/select_actions/convert_pdf'),
        )
        self.btn_uniq_pdf.pack(side=tk.LEFT, expand=True, fill='both')
        
        # Converter imagens.
        self.btn_imgs_to_pdf = self.widgets.get_button(self.containerConvertDocs)
        self.btn_imgs_to_pdf.config(
            text='Imagens para PDF', 
            command=lambda: self.to_page('/home/select_actions/imgs_to_pdf'),
        )
        self.btn_imgs_to_pdf.pack(side=tk.LEFT, expand=True, fill='both')

        #=========================================================#
        # Frame para Outros botões.
        #=========================================================#
        self.containerMoveDocs = self.widgets.get_frame(self.frame_master)
        self.containerMoveDocs.pack(expand=True, fill='both', padx=2, pady=2)
        
        # Label
        self.labelInfoMoveFiles = self.widgets.get_label(self.containerMoveDocs)
        self.labelInfoMoveFiles.config(text='Mover documentos.')
        self.labelInfoMoveFiles.pack()
    
        # Mover Documentos.
        self.btn_imgs_to_pdf = self.widgets.get_button(self.containerMoveDocs)
        self.btn_imgs_to_pdf.config(
            text='Mover documentos', 
            command=lambda: self.to_page('/home/select_actions/page_mv_files'),
        )
        self.btn_imgs_to_pdf.pack(side=tk.LEFT, expand=True, fill='both')
        
    def to_page(self, page:str):
        if page is None:
            return
        if not os.path.isfile(self.controller.user_prefs.prefs['path_tesseract']):
            if get_path_tesseract_system().path.exists():
               self.controller.user_prefs.prefs['path_tesseract'] = get_path_tesseract_system().absolute() 
            else:
                show_warnnings(
                    f'''
                    Tesseract não encontrado em PATH. 
                    Instale o tesseract para proseguir!\n
                    URL: https://github.com/tesseract-ocr/tesseract/releases
                '''
                )
            return
        self.controller.navigatorPages.push(page)

    def set_size_screen(self):
        self.parent.geometry("460x240")
        self.parent.title(f"OCR Tool")


class HomePage(PageSelectActions):
    def __init__(self, *, parent, controller):
        super().__init__(parent=parent, controller=controller)
        #self.pageName = '/home'
        
    def initUI(self):
        pass

    def go_page_select_actions(self):
        pass        

#========================================================#
# Janela inicial.
#========================================================#
class MyApplication(ControllerApp):
    def __init__(self, *, appDirs:UserAppDir):
        super().__init__(appDirs=appDirs)
        self.root:Tk = self
        self.widgets:GetWidgets = GetWidgets(self)
        self.initUI()

        # Gerenciar a navegação de páginas e a seleção de arquivos e configurações
        self.controller:ControllerApp = self
        self.navigatorPages: Navigator = Navigator(parent=self, controller=self.controller)
        # Páginas
        _pages = (
            HomePage,
            PageSelectActions,
            PageRecognizeImages,
            PageRecognizePDF,
            PageImagesToPdf,
            PageConvertPdfs,
            PageMoveFiles,
        )
        for page in _pages:
            self.navigatorPages.add_page(page)

        self.pages = self.navigatorPages.pages
        self.last_frame = self.pages['/home']
        self.navigatorPages.push('/home')
    
    def initUI(self):
        self.title("OCR Tool")
        self.geometry("460x460")
        self.initMenuBar()

    def initMenuBar(self) -> None:
        # Variáveis para armazenar os caminhos dos arquivos
        # Criar o menu principal
        self.menu_bar = Menu(self.root)
        self.root.config(menu=self.menu_bar)
        self.create_menu_file()
        self.create_menu_config()
        self.create_menu_about()

    def create_menu_file(self):
        # Criar o menu Arquivo
        self.menu_file = Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Arquivo", menu=self.menu_file)

        if os.path.exists(self.user_prefs.prefs['path_tesseract']):
            file_tesseract = self.user_prefs.prefs['path_tesseract']
        else:
            #file_tesseract = get_path_tesseract_system().absolute()
            file_tesseract = '-'

        # Adicionar itens ao menu Arquivo
        self.tesseract_index = self.add_item_menu_file(
            label="Tesseract",
            tooltip=file_tesseract,
            command=lambda: self.select_bin_file_tesseract("tesseract"),
        )
        
        #
        self.cmd_go_back_page = self.add_item_menu_file(
            label='Voltar',
            tooltip='Voltar para a página anterior',
            command=lambda: self.navigatorPages.pop(),
        )

        self.exit_cmd = self.add_item_menu_file(
            label='Sair', 
            tooltip='Sair do programa', 
            command=self.exit_app
        )

    def add_item_menu_file(self, label: str, tooltip: str, command: Callable[[], None]) -> int:
        """
        Adiciona um item ao menu 'Arquivo' com um tooltip.

        :param label: Nome do item no menu.
        :param tooltip: Texto do tooltip exibido no menu.
        :param command: Função a ser chamada ao clicar no item.
        :return: Indice do item adicionado no menu.
        """
        self.menu_file.add_command(
            label=f"{label} ({tooltip})",
            command=command,
        )
        return self.menu_file.index(tk.END)
    
    def create_menu_config(self):
        self.menu_config = Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Configurações", menu=self.menu_config)
        
        # Incluir itens no menu configurações
        self.menu_config.add_command(
            label=f"Arquivo de configuração: -",
            command=self.change_file_config,
        )
        self.menu_config.index(tk.END)

    def select_bin_file_tesseract(self, label: str) -> None:
        """
        Abre um diálogo para selecionar um arquivo e armazenar o caminho em uma variável.

        :param label: Rótulo do item no menu.
        """
        path_file: str = filedialog.askopenfilename(
            title=f"Selecione um arquivo para {label}",
            initialdir=self.openFiles.history_dirs.initialDir,
        )
        if path_file:
            # Armazena o caminho do arquivo selecionado na variável correspondente
            if label == "tesseract":
                self.user_prefs.prefs['path_tesseract'] = path_file
                self.menu_file.entryconfig(self.tesseract_index, label=f"Tesseract: {path_file}")
                self.user_prefs.prefs['path_tesseract'] = path_file
            elif label == "ocrmypdf":
                pass
            messagebox.showinfo(label, f"Caminho selecionado:\n{path_file}")
        else:
            messagebox.showinfo(label, "Nenhum arquivo foi selecionado.")

    def create_menu_about(self) -> None:
        """Exibe informações sobre o programa.""" 
        self.autor = f'Autor: {__author__}'
        self.versao = f'Versão: {__version__} | Atualização {__update__}' 
        self.version_lib = f'Lib Convert: {__version_lib__}'
        self.url = f'URL: {__url__}'

        self.menu_sobre = Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Sobre", menu=self.menu_sobre)

        self.add_items_menu_about()
        self.root.config(menu=self.menu_bar)
    
    def add_items_menu_about(self):
        self.menu_sobre.add_command(label=self.autor,)
        self.menu_sobre.add_command(label=self.versao,)
        self.menu_sobre.add_command(label=self.version_lib)
        self.menu_sobre.add_command(label=self.url,)

    def change_file_config(self) -> None:
        """
            Alterar o arquivo de configuração
        """
        filename:str = filedialog.askopenfilename(
            title=f"Selecione um arquivo para JSON",
            initialdir=self.controller.openFiles.history_dirs.initialDir,
            filetypes=[("Arquivos JSON", "*.json")]
        )
        if not filename:
            return
        if not os.path.isfile(filename):
            return
        
        self.controller.fileConfigJson = File(filename)
        self.update_state()

    def update_menu_bar(self):
        self.menu_config.entryconfig(
            0,
            label=f'Arquivo: {self.controller.fileConfigJson.absolute()}'
        )
        self.controller.user_prefs.prefs['last_inputdir'] = self.controller.fileConfigJson.dirname()
        self.controller.user_prefs.prefs['file_json'] = self.controller.fileConfigJson.absolute()
        self.controller.user_prefs.prefs = JsonConvert().from_file(self.controller.fileConfigJson).to_dict()
        print(self.controller.user_prefs.prefs)

    def update_state(self):
        self.update_menu_bar()

    def exit_app(self):
        # Salvar as configurações alteradas, antes de sair
        print(f'Salvando configurações em: [{self.controller.fileConfigJson.absolute()}]')
        # Gerar um dado JSON apartir de um dicionário.
        data:JsonData = JsonConvert().from_dict(self.controller.user_prefs.prefs)
        # Exportar o JSON para um arquivo local.
        data.to_file(self.controller.fileConfigJson)
        print('OK')
        self.root.quit()

def runApp():
    # Criação da janela principal e execução da interface do aplicativo
    app = MyApplication(
        appDirs=UserAppDir('Document-Convert')
    )
    app.mainloop()

if __name__ == "__main__":
    runApp()

