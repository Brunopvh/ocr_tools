#!/usr/bin/env python3
#
from __future__ import annotations
from typing import List, Callable
from typing import (Dict, List, Tuple)
from pathlib import Path
import os
import clipboard
import threading
import tkinter as tk
from tkinter import ( 
        filedialog, 
        messagebox,
        Tk,
        ttk,
)

from tkinter.ttk import (
        Frame,
)

from libconvert import (
    File,
    Directory,  
    InputFiles,
    FilesTypes,  
)

from libconvert.common import (
    UserFileSystem,
    UserAppDir,
    UserPrefs,
    get_path_tesseract_system,
)

from libconvert import (
    JsonConvert,
    JsonData,
)

def show_warnnings(text:str):
    messagebox.showwarning("Aviso", text)


class ContainerProgressBar(object):
    """
        Frame contendo uma barrade progresso indeterminada e dois labels personalizados.
    """
    def __init__(self, frame:ttk.Frame):
        self.frame = frame
        # Estilo para o FRAME
        self.styleFrame = ttk.Style()
        self.styleFrame.theme_use("default")
        self.styleFrame.configure(
            "DarkPurple.TFrame", 
            background="#4B0082"  # Roxo escuro
        )
        self.frame.config(relief='groove', style="DarkPurple.TFrame")
        self.frame.pack(expand=True, fill='both', padx=1, pady=1)
        
        # Frame/Container para Labels da barra de progresso
        self.container_labels_pbar = ttk.Frame(self.frame)
        self.container_labels_pbar.pack(expand=True, fill='both', padx=2, pady=1)
        
        # Label para exibir textos na barra de progresso.
        self.label_text_pbar = ttk.Label(
            self.container_labels_pbar,
            text='-'
        )
        self.label_text_pbar.pack(padx=2, pady=1)
        
        # Label para exibir o progresso
        self.label_text_progress = ttk.Label(
            self.container_labels_pbar,
            text='0%',
        )
        self.label_text_progress.pack(padx=2, pady=1)
    
        # Container exclusivo da barra de progresso.
        self.container_pbar = ttk.Frame(self.frame)
        self.container_pbar.pack(expand=True, fill='both', padx=2, pady=1)
        # Barra de progresso.
        self.pbar = ttk.Progressbar(
            self.container_pbar,
            mode='indeterminate',
        )
        self.pbar.pack(expand=True, fill='both', padx=3, pady=3)
        
    def set_text_pbar(self, text):
        """
            Atualizar o texto do label 1
        """
        if text is None:
            return
        if len(text) > 50:
            text = text[0:50]

        self.label_text_pbar.config(text=text)
        
    def set_text_progress(self, text):
        """Atualizar o texto do label 2"""
        if text is None:
            return
        self.label_text_progress.config(text=f'{text}%')
        
    def start_pbar(self):
        self.pbar.start(8)
        
    def stop_pbar(self):
        self.pbar.stop()
    
    
#===========================================================#
# Container importar arquivos
#===========================================================#
class ContainerImportFiles(object):
    """
        Container com label e botões para auxiliar a seleção de arquivos
    e pastas, contém um botão com ação de click já definida para selecionar arquivos/pasta
    """
    def __init__(
                self, 
                *, 
                frame:ttk.Frame, 
                controller:ControllerApp, 
                input_files_type:FilesTypes = FilesTypes.ALL_TYPES
            ):
        #
        self.controller:ControllerApp = controller
        self.controller.openFiles.typeSelectInput = True
        self.controller.openFiles.history_dirs.lastInputDir = self.controller.user_prefs.prefs['last_inputdir']
        
        # Frame principal
        self.frame_master_import = frame
        self.frame_master_import.pack(expand=True, fill='both', padx=2, pady=2)
        self.frame_master_import.config(style='Custom.TFrame')
        
        # Tipo de arquivos que serão aceitos na caixa de dialogo
        # o padrão é TODOS os tipos de arquivos, mas isso pode ser alterado
        # no construtor com o parâmetro input_files_type.
        self.inputFilesType:FilesTypes = input_files_type
        
        # Lista de arquivos selecionados pelo usuário, seja com diretório ou por meio da seleção direta de arquivos
        self.containerSelectedFiles:List[File] = []
        self.containerSelectedDir:Directory = None # Caso o usuário selecione um diretório.
        #
        self.initUI()

    def initUI(self):
        #----------------------------------------#
        # 0 - Segundo frame
        #----------------------------------------#
        self.containerImportFiles2:ttk.Frame = ttk.Frame(
            self.frame_master_import, 
            style="Black.TFrame", 
            relief='groove'
        )
        self.containerImportFiles2.pack(fill='both', expand=True, padx=2, pady=2, )
        
        #----------------------------------------#
        # 1 - Terceiro frame.
        #----------------------------------------#
        self.containerImportFiles3 = ttk.Frame(self.containerImportFiles2, style='LightPurple.TFrame')
        self.containerImportFiles3.pack(expand=True, fill='both', padx=3, pady=2)
        
        # Frame para texto importar arquivo
        self.containerTopText = ttk.Frame(self.containerImportFiles3)
        self.containerTopText.pack(expand=True, fill='both', padx=2, pady=2)
        
        # Label do topo Importar
        self.label_import_export:ttk.Label = ttk.Label(
            self.containerTopText,
            text='Importar Arquivos', 
            style="BoldLargeFont.TLabel",
        )
        self.label_import_export.pack(padx=1, pady=1)
        
        #================================================#
        # botão selecionar Arquivos
        #================================================#
        self.btn_select_files:ttk.Button = ttk.Button(self.containerImportFiles3)
        self.btn_select_files.config(text='Importar', command=self.select_input_files)
        self.btn_select_files.pack(padx=1, pady=2, expand=True, fill='both')
        
        #================================================#
        # Label para mostrar o total de arquivos selecionados.
        #================================================#
        self.label_selected_num_files = ttk.Label(
            self.containerImportFiles3,
            text=f'Arquivos selecionados: -'
        )
        self.label_selected_num_files.pack(padx=2, pady=1, expand=True, fill='both')
        
        #================================================#
        # Frame para Radios buttons
        #================================================#
        self.containerRadioSelectFiles = ttk.Frame(self.containerImportFiles2, style='DarkPurple.TFrame')
        self.containerRadioSelectFiles.pack(expand=True, fill='both', padx=3, pady=2)
        self.radio_file_or_dir:tk.StringVar = tk.StringVar(value='from_file')
        
        #================================================#
        # COMBO Para selecionar o tipo de documento a 
        # ser importado
        #================================================#
        #self.combo_type_docs = ttk.Combobox(
        #    self.frame_radio_select_files,
        #    values=['Imagens', 'PDFs', 'Planilhas']
        #)
        #self.combo_type_docs.pack()
        #self.combo_type_docs.set('Imagens')
        
        # De Arquivo
        self.radio_opt_from_file = ttk.Radiobutton(
            self.containerRadioSelectFiles,
            text='De Arquivos', 
            variable=self.radio_file_or_dir,
            value='from_file',
        )
        self.radio_opt_from_file.pack(padx=1, pady=1, expand=True, fill='both')
        
        # De pasta
        self.radio_opt_from_dir = ttk.Radiobutton(
            self.containerRadioSelectFiles,
            text='De Pasta', 
            variable=self.radio_file_or_dir,
            value='from_dir',
        )
        self.radio_opt_from_dir.pack(padx=1, pady=1, expand=True, fill='both')
        
        # Da área de transferência
        self.radio_opt_from_clipboard = ttk.Radiobutton(
            self.containerRadioSelectFiles,
            text='Da Área de Transferência', 
            variable=self.radio_file_or_dir,
            value='from_clipboard',
        )
        self.radio_opt_from_clipboard.pack(padx=1, pady=1, expand=True, fill='both')
        

    def select_input_files(self):
        """
            Selecionar Arquivos ou diretórios, de acordo com a
        preferência do usuário, Área de transferência, de pasta ou de arquivo.
        """
        self.controller.openFiles.typeSelectInput = True
        if self.radio_file_or_dir.get() == 'from_file':
            self.controller.selectedUserFiles = self._select_files()
        elif self.radio_file_or_dir.get() == 'from_clipboard':
            files = self._select_files_from_clipboard()
            if files == []:
                return
            self.controller.selectedUserFiles = files
        elif self.radio_file_or_dir.get() == 'from_dir':
            d = self._select_input_dir()
            if (d is None):
                return
            self.controller.selectedInputDir = d
            self.controller.selectedUserFiles = InputFiles(d).get_files(file_type=self.inputFilesType)
            
        self.controller.numSelectedFiles = len(self.controller.selectedUserFiles)
        self.label_selected_num_files.config(
            text=f'Arquivos selecionados: {self.controller.numSelectedFiles}'
        )
        
    def _select_files(self) -> List[File]:
        """Caixa de dialogo para selecionar arquivos"""
        files = []
        if self.inputFilesType == FilesTypes.ALL_TYPES:
            _selected_files = self.controller.openFiles.open_filesname()
            if _selected_files is not None:
                files = [f for f in _selected_files if f is not None]
        elif self.inputFilesType == FilesTypes.IMAGE:
            files = self.controller.openFiles.open_files_image()
        elif self.inputFilesType == FilesTypes.PDF:
            files = self.controller.openFiles.open_files_pdf()
        elif self.inputFilesType == FilesTypes.EXCEL:
            files = self.controller.openFiles.open_files_sheet()
        elif self.inputFilesType == FilesTypes.SHEET:
            files = self.controller.openFiles.open_files_sheet()
        else:
            show_warnnings('O tipo de documento a ser selecionado é inválido.')
        
        if (files == []):
            return []
        return [File(f) for f in files]
    
    def _select_files_from_clipboard(self) -> List[File]:
        try:
            f = clipboard.paste()
            print(f)
            print(type(f))
            if not os.path.exists(f):
                return []
        except Exception as e:
            print(e)
            return []
        else:
            file_path = File(f)
        #
        if self.inputFilesType == FilesTypes.ALL_TYPES:
            return [file_path]
        elif self.inputFilesType == FilesTypes.IMAGE:
            return [file_path] if file_path.is_image() else []
        elif self.inputFilesType == FilesTypes.PDF:
            return [file_path] if file_path.is_pdf() else []
        elif self.inputFilesType == FilesTypes.EXCEL:
            return [file_path] if file_path.is_sheet() else []
        elif self.inputFilesType == FilesTypes.SHEET:
            return [file_path] if file_path.is_sheet() else []
        else:
            show_warnnings('O tipo de documento a ser selecionado é inválido.')
        
            
    def _select_input_dir(self) -> Directory | None:
        """
            Caixa de dialogo para selecionar um diretório.
        """
        path = self.controller.openFiles.open_folder()
        if (not path) or (path is None):
            return None
        self.controller.user_prefs.prefs['initial_dir'] = path
        self.controller.user_prefs.prefs['last_inputdir'] = path
        return Directory(path)

#===========================================================#
# Container exportar arquivos
#===========================================================#
class ContainerExportFiles(object):
    def __init__(
        self, 
        *, 
        frame:ttk.Frame, 
        controller:ControllerApp, 
        output_files_type:FilesTypes = FilesTypes.ALL_TYPES
        ):
        #
        self.controller:ControllerApp = controller
        self.controller.openFiles.typeSelectInput = False
        self.controller.openFiles.history_dirs.lastOutputDir = self.controller.user_prefs.prefs['last_outputdir']
        #
        self.frame_master = frame
        self.frame_master.pack(padx=2, pady=2)
        self.frame_master.config(style='Custom.TFrame')
        #
        self.outputFilesType:FilesTypes = output_files_type
        # Arquivos
        self.containerSaveDir:Directory = None
        #
        self.initUI()

    def initUI(self):
        
        #----------------------------------------#
        # 0 - Frame Importar/Exportar
        #----------------------------------------#
        self.frame_export:ttk.Frame = ttk.Frame(
            self.frame_master, 
            style="Black.TFrame", 
            relief='groove'
        )
        self.frame_export.pack(padx=1, pady=1, fill='both', expand=True)
        
        #----------------------------------------#
        # 2 - Frame Exportar
        #----------------------------------------#
        self.frame_export = ttk.Frame(self.frame_export)
        self.frame_export.pack(padx=1, pady=1, expand=True, fill='both')
        
        # Frame para texto Exportar arquivo
        self.frame_top_text_export = ttk.Frame(self.frame_export)
        self.frame_top_text_export.pack(expand=True, fill='both', padx=2, pady=2)
        
        # Label do topo Exportar
        self.label_import_export:ttk.Label = ttk.Label(
            self.frame_top_text_export,
            text='Exportar Arquivos', 
            style="BoldLargeFont.TLabel"
        )
        self.label_import_export.pack(padx=1, pady=1, expand=True, fill='both')
        
        # Mostrar o diretório para exportar os dados
        self.label_export_dir = ttk.Label(self.frame_export)
        self.label_export_dir.config(
            text=f'Exportar em: {self.controller.saveDir.basename()}'
        )
        self.label_export_dir.pack(padx=1, pady=1)
        
        # Label para mostrar o total de arquivos no destino
        self.label_num_files_out_dir = ttk.Label(self.frame_export)
        self.label_num_files_out_dir.config(text='Arquivos no destino: -')
        self.label_num_files_out_dir.pack(expand=True, fill='both', padx=1, pady=1)
        
        # Botão para alterar a pasta de saída.
        self.btn_select_save_dir = ttk.Button(
            self.frame_export,
            text='Alterar Pasta', 
            command=self.select_outdir,
        )
        self.btn_select_save_dir.pack(padx=2, pady=2, expand=True, fill='both')
       
    def select_outdir(self):
        """Alterar a pasta para exportar os arquivo"""
        self.controller.openFiles.typeSelectInput = False
        path = self.controller.openFiles.open_folder()
        if path:
            self.controller.saveDir = Directory(path)
            self.controller.user_prefs.prefs['last_outputdir'] = path   
        #
        self.label_export_dir.config(text=f'Salvar em: {self.controller.saveDir.basename()}')
        self.label_num_files_out_dir.config(
            text=f'Total de arquivos no destino: {len(self.controller.saveDir.content_files())}'
        )


class GetWidgets(object):
    def __init__(self, root) -> None:
        self.root = root
        self.pady = 1
        self.padx = 1
        self.height = 2
        self.backGroundBlack = "#333333"
        self.backGround = self.backGroundBlack
        #===============================================#
        # Estilo para os Frames
        #===============================================#
        self.styleFrameBlack = ttk.Style()
        self.styleFrameBlack.theme_use("default")
        self.styleFrameBlack.configure(
                            "Black.TFrame", 
                            background="#2C2C2C"
                        )  # Cor de fundo preta

        # Fundo Roxo Claro
        self.styleFrameLightPurple = ttk.Style()
        self.styleFrameLightPurple.theme_use("default")
        self.styleFrameLightPurple.configure(
            "LightPurple.TFrame",  # Nome do estilo alterado
            background="#9370DB"   # Roxo claro (MediumPurple)
        )
        
        # Fundo Roxo Escuro
        self.styleFrameDarkPurple = ttk.Style()
        self.styleFrameDarkPurple.theme_use("default")
        self.styleFrameDarkPurple.configure(
            "DarkPurple.TFrame", 
            background="#4B0082"  # Roxo escuro
        )
        
        # Fundo Cinza escuro
        self.styleFrameDarkGray = ttk.Style()
        self.styleFrameDarkGray.theme_use("default")
        self.styleFrameDarkGray.configure(
            "DarkGray.TFrame",  # Nome do estilo alterado
            background="#2F4F4F"  # Cinza escuro (DarkSlateGray)
        )
        
        # Laranja escuro
        self.styleFrameDarkOrange = ttk.Style()
        self.styleFrameDarkOrange.theme_use("default")
        self.styleFrameDarkOrange.configure(
            "DarkOrange.TFrame",  # Nome do estilo alterado
            background="#FF8C00"  # Laranja escuro (DarkOrange)
        )

        #===============================================#
        # Estilo para os botões
        #===============================================#
        self.styleButtonGreen = ttk.Style()
        self.styleButtonGreen.theme_use("default")
        self.styleButtonGreen.configure(
                "TButton",
                foreground="white",
                background="#4CAF50",  # Verde padrão
                font=("Helvetica", 12)
            )
        
        self.styleButtonGreen.map(
            'TButton',             # Nome do estilo
            background=[('active', 'darkblue')],  # Cor de fundo ao passar o mouse
            foreground=[('disabled', 'gray')]    # Cor do texto quando desabilitado
        )
        
        self.style_btn_blue = ttk.Style()
        self.style_btn_blue.configure(
            "Custom.TButton",         # Nome do estilo
            font=("Helvetica", 14),   # Fonte personalizada
            foreground="white",       # Cor do texto
            background="blue"         # Cor de fundo
        )
        
        #===============================================#
        # Estilo para Labels
        #===============================================#
        self.stylePurple = ttk.Style()
        self.stylePurple.configure(
            "LargeFont.TLabel",  # Nome do estilo
            font=("Helvetica", 14),  # Fonte maior
            background="#9370DB",    # Cor de fundo roxo claro
            foreground="white"       # Cor do texto branco
        )
        
        # Default
        self.styleDefault = ttk.Style()
        self.styleDefault.configure(
            "BoldLargeFont.TLabel",  # Nome do estilo
            font=("Helvetica", 14, "bold")  # Fonte maior e negrito
        )
        
    def container_pbar(self, frame:ttk.Frame) -> ContainerProgressBar:
        return ContainerProgressBar(frame)

    def void_command(self) -> None:
        print(f'VOID')

    def get_progress_bar(self, parent:ttk.Frame=None, *, mode="indeterminate") -> ttk.Progressbar:
        if parent is None:
            parent = self.root
        return ttk.Progressbar(
                            parent, 
                            orient="horizontal", 
                            length=320, 
                            mode=mode,
                        )

    def get_frame(self, parent:ttk.Frame=None) -> ttk.Frame:
        if parent is None:
            parent = self.root
        return ttk.Frame(parent, relief="groove", style="Black.TFrame")
    
    def get_label(self, parent:ttk.Frame=None, text='-') -> ttk.Label:
        if parent is None:
            parent = self.root
        return ttk.Label(
                    parent, 
                    text=text
                )

    def get_button(self, parent:ttk.Frame=None, *, text='Botão', cmd=()) -> ttk.Button:
        if parent is None:
            parent = self.root

        return ttk.Button(
                    parent, 
                    text=text, 
                    command=cmd,
                    style='TButton',
                )  

    def get_input_box(self, parent:ttk.Frame=None) -> ttk.Entry:
        if parent is None:
            parent = self.root
        return ttk.Entry(parent)     

    def void_label(self, parent:ttk.Frame=None) -> ttk.Label:
        if parent is None:
            parent = self.root    
        lb = ttk.Label(parent)
        lb.config(padding=2)
        return lb

    def get_combobox(self, parent:ttk.Frame=None, values:List[str]=['-']) -> ttk.Combobox:
        if parent is None:
            parent = self.root
        return ttk.Combobox(parent, values=values)

    def get_radio_button(self, parent=None) -> ttk.Radiobutton:
        if parent is None:
            parent = self.root
        return ttk.Radiobutton(
                    parent, 
                    text="Opções", 
                )
  
class ContainerH(object):
    def __init__(self, frame:ttk.Frame):
        self.frame:ttk.Frame = frame
        
    def add_label(self, *, text='-') -> None:
        lb = ttk.Label(
            self.frame,
            text=text,
        )
        lb.pack(side=tk.LEFT, padx=1, pady=1, fill='both', expand=True)
        
    def add_button(self, *, text='Botão', cmd=()):
        btn = ttk.Button(
            self.frame,
            text=text,
            command=cmd,
        )
        btn.pack(side=tk.LEFT, padx=1, pady=1, fill='both', expand=True)
        

class HistoryDirs(object):
    def __init__(self) -> None:
        self.initialDir:str = None
        self.lastInputDir:str = os.path.abspath(Path().home())
        self.lastOutputDir:str = os.path.abspath(Path().home())
    
class OpenFiles(object):
    def __init__(self, ufs:UserFileSystem, *, history_dirs:HistoryDirs=HistoryDirs()) -> None:
        self.usf:UserFileSystem = ufs
        # Valores compartilhados entre as janelas
        self.history_dirs:HistoryDirs = history_dirs
        self.history_dirs.initialDir = self.usf.userDownloads.absolute()
        self.history_dirs.lastInputDir = self.usf.userDownloads.absolute()
        self.history_dirs.lastOutputDir = self.usf.userDownloads.absolute()
        self.typeSelectInput:bool = True
        
    def _get_initial_dir(self) -> str:
        if self.typeSelectInput == True:
            return self.history_dirs.lastInputDir
        else:
            return self.history_dirs.lastOutputDir
        
    def _set_initial_dir(self, d:str):
        if d is None:
            return
        self.history_dirs.initialDir = d
        if self.typeSelectInput == True:
            self.history_dirs.lastInputDir = d
        else:
            self.history_dirs.lastOutputDir = d
        
    def open_filename(self, input_type:FilesTypes=FilesTypes.ALL_TYPES) -> str | None:
        """
            Caixa de dialogo para selecionar um arquivo
        """
        
        _filesTypes = [("Todos os arquivos", "*"),]
        _title = 'Selecione um arquivo'
        if input_type == FilesTypes.SHEET:
            _filesTypes = [("Arquivos Excel", "*.xlsx"), ("Arquivos CSV", "*.csv *.txt")]
            _title = 'Selecione uma planilha'
        elif input_type == FilesTypes.EXCEL:
            _filesTypes = [("Arquivos Excel", "*.xlsx")]
            _title = 'Selecione uma planilha'
        elif input_type == FilesTypes.IMAGE:
            _filesTypes = [("Arquivos de Imagem", "*.png *.jpg *.jpeg *.svg")]
            _title = 'Selecione Imagens'
        elif input_type == FilesTypes.PDF:
            _filesTypes = [("Arquivos PDF", "*.pdf *.PDF"),]
            _title = 'Selecione arquivos PDF'
        #
        #
        filename = filedialog.askopenfilename(
            title=_title,
            initialdir=self._get_initial_dir(),
            filetypes=_filesTypes,
        )
        
        if not filename:
            return None
        self._set_initial_dir(os.path.abspath(os.path.dirname(filename)))
        return filename
    
    def open_filesname(self, input_type:FilesTypes=FilesTypes.ALL_TYPES) -> Tuple[str]:
        """
            Selecionar uma ou mais arquivos
        """
        
        _filesTypes = [("Todos os arquivos", "*"),]
        _title = 'Selecione um arquivo'
        if input_type == FilesTypes.SHEET:
            _filesTypes = [("Arquivos Excel", "*.xlsx"), ("Arquivos CSV", "*.csv *.txt")]
            _title = 'Selecione uma planilha'
        elif input_type == FilesTypes.EXCEL:
            _filesTypes = [("Arquivos Excel", "*.xlsx")]
            _title = 'Selecione uma planilha'
        elif input_type == FilesTypes.IMAGE:
            _filesTypes = [("Arquivos de Imagem", "*.png *.jpg *.jpeg *.svg")]
            _title = 'Selecione Imagens'
        elif input_type == FilesTypes.PDF:
            _filesTypes = [("Arquivos PDF", "*.pdf *.PDF"),]
            _title = 'Selecione arquivos PDF'
        #
        files = filedialog.askopenfilenames(
            title=_title,
            initialdir=self._get_initial_dir(),
            filetypes=_filesTypes,
        )
        if len(files) > 0:
            self._set_initial_dir(os.path.abspath(os.path.dirname(files[0])))
        return files
        
    def open_file_sheet(self) -> str | None:
        """
            Caixa de dialogo para selecionar um arquivo CSV/TXT/XLSX
        """
        return self.open_filename(FilesTypes.SHEET)

    def open_files_sheet(self) -> list:
        """
            Selecionar uma ou mais planilhas
        """
        return self.open_filesname(FilesTypes.SHEET)
    
    def open_files_image(self) -> List[str]:
        return self.open_filesname(FilesTypes.IMAGE)
    
    def open_files_pdf(self) -> List[str]:
        return self.open_filesname(FilesTypes.PDF)

    def open_folder(self) -> str | None:
        d = filedialog.askdirectory(
                    initialdir=self._get_initial_dir(),
            )
        if d is None:
            return None
        self._set_initial_dir(os.path.abspath(d))
        return d    
    
    def save_file(self, type_file:FilesTypes.ALL_TYPES) -> str:
        """Abre uma caixa de dialogo para salvar arquivos."""
        if type_file == FilesTypes.SHEET:
            _default = '.xlsx'
            _default_types = [("Arquivos Excel", "*.xlsx"), ("Arquivos CSV", "*.csv")]
        elif type_file == FilesTypes.EXCEL:
            _default = '.xlsx'
            _default_types = [("Arquivos Excel", "*.xlsx")]
        elif type_file == FilesTypes.CSV:
            _default = '.csv'
            _default_types = [("Arquivos CSV", "*.csv"), ("Arquivos de texto", "*.txt")]
        elif type_file == FilesTypes.PDF:
            _default = '.pdf'
            _default_types = [("Arquivos PDF", "*.pdf")]
        else:
            _default = '.*'
            _default_types = [("Salvar Como", "*.*")]
        
        # Abre a caixa de diálogo "Salvar Como"
        file_path = filedialog.asksaveasfilename(
            defaultextension=_default,  # Extensão padrão
            filetypes=_default_types,  # Tipos de arquivos suportados
            title="Salvar arquivo como"
        )

        # Exibe o caminho do arquivo selecionado
        if file_path:
            print("Arquivo será salvo em:", file_path)
        return file_path
    
    
class ControllerApp(Tk):
    """
        Este será um atributo comun entre as páginas, para compartilhamento de informações, e
    para controlar a navegação entra páginas.
    """
    def __init__(self, *, appDirs:UserAppDir):
        super().__init__()
        self.appDirs:UserAppDir = appDirs
        self.openFiles:OpenFiles = OpenFiles(self.appDirs.userFileSystem)
        self.saveDir:Directory = self.appDirs.workspaceDirApp
        self.saveDir.mkdir()
        self.selectedUserFiles:List[File] = []
        self.selectedInputDir:Directory = None
        self.numSelectedFiles:int = 0
        #
        self.appDirs.config_dir_app().mkdir()
        self.fileConfigJson:File = self.appDirs.config_dir_app().join_file('cfg.json')
        self.user_prefs:UserPrefs = UserPrefs(self.appDirs)
        self._load_local_user_prefs()
        self._runtimeTesseract:str = self.user_prefs.prefs['path_tesseract'] 
        #
        self.lastFrame:Frame = None
        self.pages:Dict[str, AppPage] = {}
        self.navigatorPages = Navigator(parent=self, controller=self)
        
    def select_file(self, input_type:FilesTypes=FilesTypes.ALL_TYPES):
        f = self.openFiles.open_filename(input_type)
        if (f is None) or (len(f) < 1):
            return
        self.numSelectedFiles = 1
        self.selectedUserFiles = [File(f)]
    
    def select_files(self, input_type:FilesTypes=FilesTypes.ALL_TYPES):
        files:Tuple[str] = self.openFiles.open_filesname(input_type)
        if (files is None) or (len(files) < 1):
            return
        self.selectedUserFiles = [File(f) for f in files if f is not None]
        self.numSelectedFiles = len(self.selectedUserFiles)
        
    def get_runtime_tesseract(self) -> str:
        print('-----------------------------------------------')
        print(f'[Run time tesseract]: {self._runtimeTesseract}')
        print('-----------------------------------------------') 
        return self._runtimeTesseract
    
    def set_runtime_tesseract(self, t:str):
        if not os.path.exists(t):
            print(f'{__class__.__name__} Erro: Tesseract inválido => {t}')
            return
        self._runtimeTesseract = t
        
    def _load_local_user_prefs(self):
        """Ler as configurações de um arquivo JSON local se existir"""
        if not self.fileConfigJson.path.exists():
            return
        print(f'Lendo configurações: [{self.fileConfigJson.absolute()}]')
        content_file:JsonData = JsonConvert().from_file(self.fileConfigJson)
        self.user_prefs.prefs = content_file.to_dict()
        print('-----------------------------------------------')
        for _k in content_file.to_dict().keys():
            print(f'{_k}: {content_file.to_dict()[_k]}')
        print('-----------------------------------------------')
        self.openFiles.history_dirs.initialDir = self.user_prefs.prefs['initial_dir']

    def to_page(self, page_name:str):
        """Navegar para uma página apartir do nome da página."""
        self.lastFrame.pack_forget()
        self.lastFrame = self.pages[page_name]
        frame = self.pages[page_name]
        frame.set_size_screen()
        frame.update_state()
        frame.pack()
           
class AppPage(ttk.Frame):
    def __init__(self, *, parent:Tk, controller:ControllerApp):
        super().__init__(parent)
        self.parent:Tk = parent
        self.controller:ControllerApp = controller
        self.widgets:GetWidgets = GetWidgets(self.parent)
        self.frameMaster = self.widgets.get_frame(self)
        self.frameMaster.config(style="Black.TFrame")
        self.frameMaster.pack(expand=True, fill=tk.BOTH)
        self.pageName:str = None
        self.runningMainThread:bool = False
        self.mainThreading: threading.Thread = None
        self.stopThreading: threading.Event = threading.Event()
        self.stopEventList:List[threading.Event] = []
        self.running:bool = False
        self.set_size_screen()
        
    def is_running(self):
        return self.running
    
    def check_running(self) -> bool:
        """
            Verifica se já existe outra operação em andamento.
        """
        if self.is_running():
            show_warnnings('Existe outra operação em andamento, aguarde!')
            return False
        return True
    
    def createMainThread(self, cmd:Callable, list_events:List[threading.Event]=[]):
        if self.runningMainThread == True:
            print(f'Já existe outra operação em andamento nesta tela, saindo...')
            return
        if self.mainThreading is not None:
            print(f'Thread principal já criada, saindo...')
            return
        if not isinstance(cmd, Callable):
            return
        self.runningMainThread = True
        self.stopThreading.clear()
        self.mainThreading = threading.Thread(target=cmd)
        self.mainThreading.start()
        self.stopEventList = list_events
        print(f'{__class__.__name__} Thread principal criada')

    def stopMainThread(self):
        if self.mainThreading is None:
            return
        for e in self.stopEventList:
            e.set()
        self.stopThreading.set()
        self.mainThreading.join()
        self.mainThreading = None
        self.runningMainThread = False
        self.running = False
        print(f'{__class__.__name__} Thread principal finalizada.')
        show_warnnings('Operação cancelada pelo usuário!')

    def commandStopButton(self):
        """
            Esse método pode ser conectado a um botão para parar a Thread principal.
        Podendo ser conectado diretamente ou indiretamente.
        """
        pass

    def add_button_back(self, container:Frame=None):
        if container is None:
            container = self.frameMaster
        # botão voltar
        self.btnBackPage = self.widgets.get_button(container)
        self.btnBackPage.config(text='Voltar', command=self.go_back_page)
        self.btnBackPage.pack()

    def go_back_page(self):
        self.stopMainThread()
        self.controller.navigatorPages.pop()
    
    def set_size_screen(self):
        pass

    def update_state(self):
        pass

class Navigator(object):
    def __init__(self, *, parent:Tk, controller:ControllerApp):
        self.parent:Tk = parent  # Janela principal ou root
        self.controller:ControllerApp = controller
        self.pages:Dict[str, AppPage] = {}  # Dicionário para armazenar as páginas
        self.current_page = None  # Página atualmente exibida
        self.history:List[str] = []  # Pilha para armazenar o histórico de navegação

    def add_page(self, page_class: AppPage):
        """
        Adiciona uma página ao navegador.

        :param page: Instância da página (AppPage).
        """
        p:AppPage = page_class(parent=self.parent, controller=self.controller)
        self.pages[p.pageName] = p
        print(f'Página adicionada: {p.pageName}')

    def push(self, page_name: str):
        """
        Exibe a página especificada.

        :param page_name: Nome da página a ser exibida.
        """    
        print(f'Navegando para {page_name}')
        if page_name not in self.pages:
            show_warnnings(f'Página não encontrada!\n{page_name}')
            return 
            
        # Esconde a página atual, se houver
        if self.current_page is not None:
            self.history.append(self.current_page.pageName)  # Salva no histórico
            self.current_page.pack_forget()

        # Mostra a nova página
        self.current_page: AppPage = self.pages[page_name]
        self.current_page.set_size_screen()
        self.current_page.update_state()
        #self.current_page.pack(fill="both", expand=True)
        self.current_page.pack()

    def pop(self):
        """
        Retorna à página anterior no histórico de navegação.
        """
        if not self.history:
            raise ValueError("Não há páginas anteriores no histórico para retornar.")

        # Esconde a página atual
        if self.current_page is not None:
            self.current_page.pack_forget()

        # Recupera a página anterior do histórico
        previous_page_name = self.history.pop()
        self.current_page: AppPage = self.pages[previous_page_name]
        self.current_page.set_size_screen()
        self.current_page.update_state()
        #self.current_page.pack(fill="both", expand=True)
        self.current_page.pack()
        print(f'Retornando para {previous_page_name}')


class AppPageIo(AppPage):
    def __init__(self, *, parent, controller):
        super().__init__(parent=parent, controller=controller)
        self.parent:Tk = parent
        self.controller:ControllerApp = controller
        self.inputFilesType = FilesTypes.ALL_TYPES
        self.outputFilesType = FilesTypes.ALL_TYPES
        self.initUI()
        
    def initUI(self):
        self.add_box_import()
        self.add_box_export()
    
    def add_box_import(self, f:ttk.Frame=None):
        if f is None:
            f = self.frameMaster
        #
        f.pack(side=tk.LEFT)
        self.containerInput:ContainerImportFiles = ContainerImportFiles(
            frame=f,
            controller=self.controller,
            input_files_type=self.inputFilesType,
        )
        
    def add_box_export(self, f:ttk.Frame=None):
        if f is None:
            f = self.frameMaster
        self.containerExport:ContainerExportFiles = ContainerExportFiles(
            frame=f,
            controller=self.controller,
            output_files_type=self.outputFilesType,
        )
    
    def add_box_io(self, f:ttk.Frame):
        self.add_box_import(f)
        self.add_box_export(f)