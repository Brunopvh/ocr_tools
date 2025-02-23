#!/usr/bin/env python3
#
from typing import List,Tuple,Dict
from tkinter import ttk, filedialog, messagebox
import tkinter as tk
from pandas import DataFrame
from pathlib import Path
import shutil
import threading
import sys, os
import time
from libconvert import (
    Directory,
    File,
    SheetInputStream,
    SheetOutputStream,
    ParseDF,
    FilesTypes,
    export_dataframe,
    FormatString,
)

from gui import (
    GetWidgets,
    AppPage,
    show_warnnings
)

#========================================================#
# Mover arquivos
#========================================================#
class PageMoveFiles(AppPage):
    def __init__(self, *, parent, controller):
        super().__init__(parent=parent, controller=controller)
        self.pageName = '/home/select_actions/page_mv_files'
        self.widgets_recognize:GetWidgets = GetWidgets(self)
        # Frame Principal desta Tela
        self.frame_master:ttk.Frame = self.widgets_recognize.get_frame(self)
        self.frame_master.pack()
        self.running = False
        self._outputDir:Directory = self.controller.saveDir.concat('Renomeados')
        self.sheetMoveFiles:File = None
        self._mainDataFrame:DataFrame = None
        self._outputDir.mkdir()
        self.__padx = 2
        self.__pady = 3
        
        self.initUI()

    def initUI(self):
        #===============================================================#
        # 0 - Box Principal da janela (filho do master)
        #===============================================================#
        self.containerMainWindow = ttk.Frame(self.frame_master)
        self.containerMainWindow.pack()
        
        #===============================================================#
        # Box para selecionar a planilha de dados.
        #===============================================================#
        self.containerInputSheet:ttk.Frame = ttk.Frame(self.containerMainWindow, style='LightPurple.TFrame')
        self.containerInputSheet.pack(side=tk.LEFT, expand=True, padx=self.__padx, pady=self.__pady)
        # Label de topo
        self._containerLabelTop1 = ttk.Frame(self.containerInputSheet)
        self._containerLabelTop1.pack(expand=True, fill='both', padx=self.__padx, pady=self.__pady)
        #
        self.labelImportText:ttk.Label = ttk.Label(
            self._containerLabelTop1, 
            text='Importar planilha de dados'
        )
        self.labelImportText.pack()
        # Botão importar
        self.btnImportSheet:ttk.Button = ttk.Button(
            self.containerInputSheet,
            text='Importar',
            command=self._select_input_sheet,
        )
        self.btnImportSheet.pack(side=tk.LEFT, expand=True, fill='both', padx=self.__padx, pady=self.__pady)
        # Informações sobre a planilha selecionda.
        self.labelInfoSheet:ttk.Label = ttk.Label(
            self.containerInputSheet,
            text=f'Nenhuma planilha selecionada',
        )
        self.labelInfoSheet.pack(expand=True, fill='both', padx=self.__padx, pady=self.__pady)
        
        #===============================================================#
        # Box para Opções de exportação.
        #===============================================================#
        self.containerExportFiles:ttk.Frame = ttk.Frame(
            self.containerMainWindow,
            style='LightPurple.TFrame',
        )
        self.containerExportFiles.pack(expand=True, padx=self.__padx, pady=self.__pady)
        
        # Container para selecionar a pasta de saída.
        self._containerOutputDir:ttk.Frame = ttk.Frame(
            self.containerExportFiles,
        )
        self._containerOutputDir.pack(expand=True, padx=self.__padx, pady=self.__pady)
        # Botão para selecionar/alterar pasta de saída.
        self.btnOutputDir = ttk.Button(
            self._containerOutputDir,
            text='Alterar',
            command=self._update_output_dir,
        )
        self.btnOutputDir.pack(side=tk.LEFT)
        # Label
        self._labelTopOutDir = ttk.Label(
            self._containerOutputDir,
            text=f'Mover arquivos para: {self._outputDir.basename()}',
        )
        self._labelTopOutDir.pack()
        
        #===============================================================#
        # Box para Informar o tipo de padrão a ser reconhecido nos documentos
        # para renomear.
        #===============================================================#
        self.containerInputBox = ttk.Frame(
            self.containerExportFiles,   
        )
        self.containerInputBox.pack(expand=True, fill='both', padx=self.__padx, pady=self.__pady)
        
        # Container com o primeiro padrão de texto
        self._containerInput1 = ttk.Frame(
            self.containerInputBox,
        )
        self._containerInput1.pack(expand=True, fill='both', padx=self.__padx, pady=self.__pady)
        
        # label 1
        self._labelInputText1 = ttk.Label(
            self._containerInput1,
            text='Texto padrão do arquivo',
        )
        self._labelInputText1.pack(side=tk.LEFT, expand=True, fill='both', padx=self.__padx, pady=self.__pady)
        # Caixa de texto 1
        self._entry1 = ttk.Entry(
            self._containerInput1,
        )
        self._entry1.pack(expand=True, fill='both', padx=self.__padx, pady=self.__pady)
        
        # Container com o segundo padrão de texto
        self._containerInput2 = ttk.Frame(
            self.containerInputBox,
        )
        self._containerInput2.pack(expand=True, fill='both', padx=self.__padx, pady=self.__pady)
        # Label 2
        self._labelInputText2 = ttk.Label(
            self._containerInput2,
            text='Adicionar texto padrão'
        )
        self._labelInputText2.pack(side=tk.LEFT, expand=True, fill='both', padx=self.__padx, pady=self.__pady)
        # Caixa de texto 2
        self._entry2 = ttk.Entry(self._containerInput2,)
        self._entry2.pack(expand=True, fill='both', padx=self.__padx, pady=self.__pady)
        
        #===============================================================#
        # Box com botões para processar as ações.
        #===============================================================#
        self._containerButtons = ttk.Frame(
            self.frame_master,
        )
        self._containerButtons.pack(padx=self.__padx, pady=self.__pady)
        
        # botão gerar planilha
        self._containerExportSheet = ttk.Frame(self._containerButtons, style='LightPurple.TFrame')
        self._containerExportSheet.pack(expand=True, fill='both', padx=self.__padx, pady=self.__pady)
        # Botão exportar planilha
        self._btnExportSheet = ttk.Button(
            self._containerExportSheet,
            text='Exportar Planilha',
            command=self.action_export_sheet,
        )
        self._btnExportSheet.pack(side=tk.LEFT, expand=True, fill='both', padx=self.__padx, pady=self.__pady)
        #
        self._labelExportSheet = ttk.Label(
            self._containerExportSheet,
            text='Exporta uma planilha com a relação dos arquivos a serem modificados'
        )
        self._labelExportSheet.pack(expand=True, fill='both', padx=self.__padx, pady=self.__pady)
        
        #===============================================================#
        # Container Gerar planilha e mover arquivos
        #===============================================================#
        self._containerButtonMoveFiles = ttk.Frame(
            self._containerButtons,
            style='LightPurple.TFrame'
        )
        self._containerButtonMoveFiles.pack(expand=True, fill='both', padx=self.__padx, pady=self.__pady)
        # Botão Gerar planilha e mover arquivos
        self._btnMoveFile = ttk.Button(
            self._containerButtonMoveFiles,
            text='Mover arquvos',
            command=self.action_move_files,
        )
        self._btnMoveFile.pack(side=tk.LEFT, expand=True, fill='both', padx=self.__padx, pady=self.__pady)
        #
        self._labelMoveFiles = ttk.Label(
            self._containerButtonMoveFiles,
            text='Renomar documentos no disco com base em uma planilha de dados'
        )
        self._labelMoveFiles.pack(expand=True, fill='both', padx=self.__padx, pady=self.__pady)

        # 6 - Barra de progresso
        self.containerLocalPbar = ttk.Frame(self.frame_master)
        self.containerLocalPbar.pack(expand=True, fill='both', padx=1, pady=1)
        self.container_pbar = self.widgets.container_pbar(self.containerLocalPbar)
        
    def action_move_files(self):
        th = threading.Thread(target=self.__execute_move_files)
        th.start()
        
    def __execute_move_files(self):
        self.start_pbar()
        df = self.get_data_move_files()
        if (df is None) or (df.empty):
            self.stop_pbar()
            return
        parse = ParseDF(df).find_elements(col='MOVER', text='SIM', iqual=True)
        _index:List[str] = parse.data.index.tolist()
        max_num:int = len(_index)
        
        for num, i in enumerate(_index):
            src_file = parse.data['ARQUIVO'][i]
            out_filename = parse.data['NOVO_ARQUIVO'][i]
            dest_file = os.path.join(self._outputDir.absolute(), out_filename)
            if not os.path.isfile(src_file):
                continue
            if os.path.isfile(dest_file):
                continue # O arquivo já existe no destino
            self.set_text_pbar(f'Movendo: {dest_file}')
            self.set_text_progress(f'{((num+1)/max_num)*100:.2f}')
            try:
                shutil.move(src_file, dest_file)
            except Exception as e:
                print(e)
       
        self.set_text_progress(f'-')
        self.set_text_pbar('OK')
        messagebox.showinfo(
            'Arquivos Movidos',
            f'Arquivos movidos em:\n{self._outputDir.absolute()}'
        )
        self.stop_pbar()
        
    def get_data_move_files(self) -> DataFrame | None:
        """
            Usar o DataFrame da planilha de dados para gerar uma coluna com o nome dos 
        arquivos a serem movidos/renomeados
        """
        if not self.check_files():
            return None
        if self.get_dataframe().empty:
            return None
        if (self._entry1.get() == '') or (self._entry1.get() is None):
            show_warnnings('Preencha a caixa de texto padrão para prosseguir!')
            return None
        self.start_pbar()
        _list_new_names:List[str] = []
        _list_status:List[str] = []
        df = ParseDF(self.get_dataframe()).select_columns(['TEXTO_LINHA', 'ARQUIVO']).data
        _index:List[int] = df.index.tolist()
        for i in _index:
            new_name = None
            current_line:str = df['TEXTO_LINHA'][i]
            if self._entry1.get() in current_line:
                idx = current_line.find(self._entry1.get())
                new_name = current_line[idx:-1]
            
                if (not self._entry2.get() == '') and (self._entry2.get() is not None):
                    if not self._entry2.get() in new_name:
                        new_name = None
            #
            if new_name is None:
                _list_new_names.append('-')
                _list_status.append('N')
            else:
                _list_new_names.append(
                    FormatString(new_name)
                    .replace_bad_chars()
                    .replace_all('/').replace_all(' ', '_')
                    .to_upper().value[0:55]
                )
                _list_status.append('SIM')
        df['NOVO_ARQUIVO'] = _list_new_names
        df['MOVER'] = _list_status
        self.stop_pbar()
        return df
                
    def action_export_sheet(self):
        th = threading.Thread(target=self.__execute_export_sheet)
        th.start()
        
    def __execute_export_sheet(self):
        self.start_pbar()
        df = self.get_data_move_files()
        if (df is None) or (df.empty):
            self.stop_pbar()
            return
        
        export_dataframe(df, self._outputDir.join_file('mover.xlsx'))
        messagebox.showinfo(
            'Planilha Exportada',
            f'Planilha exportada em:\n{self._outputDir.join_file("mover.xlsx").absolute()}'
        )
        self.stop_pbar()
        
    def _update_page(self):
        if not self.check_files():
            return
        if not self.check_running():
            return
        th = threading.Thread(target=self.__execute_update_page)
        th.start()
        
    def __execute_update_page(self):
        if self.sheetMoveFiles is not None:
            try:
                self.start_pbar()
                load = SheetInputStream(self.sheetMoveFiles, load_now=True)
                while True:
                    if not load.is_running():
                        break
                    self.set_text_pbar(f'Lendo: {self.sheetMoveFiles.basename()}')
                    self.set_text_progress(f'{load.get_progress():.2f}')
            except:
                self.set_text_pbar(f'Falha ao tentar ler o arquivo: {self.sheetMoveFiles.basename()}')
            else:
                self.set_dataframe(load.get_data())
            finally:
                self.set_text_pbar('OK')
                self.set_text_progress('100')
                self.stop_pbar()
            
    def set_dataframe(self, d:DataFrame):
        if not isinstance(d, DataFrame):
            return 
        # Verificar se a planiha informada contém as colunas corretas.
        if not ParseDF(d).exists_columns(['TEXTO_LINHA', 'ARQUIVO']):
            show_warnnings('Planilha inválida!\nSelecione uma planilha válida e tente novamente.')
            return
        self._mainDataFrame = d.astype('str')

    def get_dataframe(self) -> DataFrame:
        if self._mainDataFrame is None:
            return DataFrame()
        return self._mainDataFrame
        
    def _select_input_sheet(self):
        filename = filedialog.askopenfilename(
            title='Selecione uma planilha',
            initialdir=self.controller.user_prefs.prefs['last_inputdir'],
            filetypes=[("Arquivos Excel", "*.xlsx")],
        )
        
        if not filename:
            return
        self.sheetMoveFiles = File(filename)
        self.controller.user_prefs.prefs['last_inputdir'] = self.sheetMoveFiles.dirname()
        self.labelInfoSheet.config(text=self.sheetMoveFiles.basename())
        self._update_page()
        
    def _update_output_dir(self):
        print(self.controller.user_prefs.prefs['last_inputdir'])
        out = filedialog.askdirectory(
                    initialdir=self.controller.user_prefs.prefs['last_inputdir'],
            )
        if out is None:
            return None
           
        try:
            if os.path.isdir(out):
                self._outputDir = Directory(out)
        except:
            pass
        else:
            self._labelTopOutDir.config(text=f'Mover em: {self._outputDir.basename()}')
            self.controller.user_prefs.prefs['last_inputdir'] = out
            self._outputDir.mkdir()
            
    def check_files(self) -> bool:
        if self.sheetMoveFiles is None:
            show_warnnings('Selecione uma planilha de dados para mover arquivos!')
            return False
        return True
            
    def set_text_progress(self, text:str):
        self.container_pbar.set_text_progress(text)
            
    def set_text_pbar(self, text:str):
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
        self.parent.geometry("645x300")
        self.parent.title(f"OCR Tool - Mover arquivos")

    def update_state(self):
        pass


