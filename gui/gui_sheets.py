#!/usr/bin/env python3
#

import os
import time
import pandas
from typing import (List)
import threading
from threading import Thread, Event

import tkinter as tk
from tkinter import (
        ttk,
        Tk,
)

from tkinter.ttk import ( 
    Button,
    Entry, 
    Frame, 
    Label,
)

from gui import (
    show_warnnings,
    AppPage,
    GetWidgets,
    ContainerExportFiles,
    ContainerImportFiles,
    ContainerProgressBar,
)

from libconvert import (
    SheetInputStream,
    SheetOutputStream,
    File,
    Directory,
    FormatString,
    FilesTypes,
    ToiConvert,
    TextRecognizedToi,
    ParseDF,
    export_dataframe,
)

import shutil
import pandas
from pandas import DataFrame

#========================================================#
# Filtrar TOI
#========================================================#
class PageDocsToi(AppPage):
    """
        Recebe uma planilha com texto bruto OCR de obtido de alguns documentos
    e filtra os dados UC e TOI.
    """
    
    def __init__(self, *, parent, controller):
        super().__init__(parent=parent, controller=controller)
        self.pageName = '/home/select_actions/page_toi'
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
            input_files_type=FilesTypes.EXCEL
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
        t = threading.Thread(target=self._execute_convert_to_excel)
        t.start()
    
    def _execute_convert_to_excel(self):
        """filtrar TOI"""
        self.container_pbar.start_pbar()
        file_sheet = self.controller.selectedUserFiles[0]
        parse = ParseDF(SheetInputStream(file_sheet).get_data())
        #
        column_filter:List[str] = parse.uniq_column('ARQUIVO').values.tolist()
        data:List[DataFrame] = []
        for item in column_filter:
            df = parse.find_elements(col='ARQUIVO', text=item).data
            if df.empty:
                continue
            num_lines = len(df)
            text_file = TextRecognizedToi(df['TEXTO_LINHA'].values.tolist())
            df['TEXTO_LINHA'] = [text_file.line_uc().value] * num_lines
            df['UC'] = [text_file.uc()] * num_lines
            df['TOI'] = [text_file.toi()] * num_lines
            df['ROTEIRO'] = [text_file.roteiro()] * num_lines
            df['POSTAGEM'] = [text_file.line_postagem()] * num_lines 
            df['NOVO_NOME'] = [
                    f'UC_{text_file.uc()}_{text_file.toi()}_{text_file.roteiro()}_{text_file.line_postagem()}'
                ] * num_lines
            data.append(df) 
        #
        export_dataframe(pandas.concat(data), self.controller.saveDir.join_file('toi.xlsx'))
        self.container_pbar.set_text_progress('100')
        self.container_pbar.stop_pbar()
        
    def set_size_screen(self):
        self.parent.geometry("625x260")
        self.parent.title(f"Load Images - Especial")


#========================================================#
# Filtrar Planilha
#========================================================#
class PageSoupSheets(AppPage):
    """Página para filtrar textos em planilha Excel."""
    def __init__(self, *, parent, controller):
        super().__init__(parent=parent, controller=controller)
        self.pageName = '/home/select_actions/soup_sheets'
        self.widgets = GetWidgets(self)
        self.frame_master = self.widgets.get_frame(self)
        self.frame_master.pack()
        self.__parse:ParseDF = None
        self.__fileSheetFilter:File = None
        
        self.initUI()
        
    def initUI(self) -> None:
        self.listColumnNames: List[str] = ['-']
        #=======================================================#
        # 0 - Frame Geral Local
        #=======================================================#
        self.containerPage = self.widgets.get_frame(self.frame_master)
        self.containerPage.pack()
        
        # 1 - Frame para widgets IO
        self.containerWidgesIo = self.widgets.get_frame(self.containerPage)
        self.containerWidgesIo.pack(side=tk.LEFT)
        
        # Frame para widgets da página
        self.containerSheetWidgets = self.widgets.get_frame(self.containerPage)
        self.containerSheetWidgets.config(style='Black.TFrame')
        self.containerSheetWidgets.pack()
        
        # Frame para barra de progresso.
        self.frameProgressBar = self.widgets.get_frame(self.frame_master)
        self.frameProgressBar.pack()
        
        # Container Input (selecionar arquivos ou pasta)
        self.miniFrameImport = self.widgets.get_frame(self.containerWidgesIo)
        self.miniFrameImport.pack()
        
        #
        self.container_import:ContainerImportFiles = ContainerImportFiles(
            frame=self.miniFrameImport,
            controller=self.controller,
            input_files_type=FilesTypes.SHEET,
        )
        
        # Container Output (Container pronto no módulo gui_utils.py)
        self.container_export:ContainerExportFiles = ContainerExportFiles(
            frame=self.containerWidgesIo,
            controller=self.controller,
            output_files_type=FilesTypes.SHEET,
        )
        
        # Container com Widgtes e barra de progresso.
        self.container_pbar:ContainerProgressBar = ContainerProgressBar(self.frameProgressBar)
        
        #=======================================================#
        # Frame para agrupar ações de Edição. Concatenar/Apagar etc.
        #=======================================================#
        self.containerEditActions:Frame = self.widgets.get_frame(self.containerSheetWidgets)
        self.containerEditActions.pack(expand=True, padx=3, pady=3, fill=tk.BOTH)
        
        # Label informativo no topo
        self.label_edit_info = self.widgets.get_label(self.containerEditActions)
        self.label_edit_info.config(text='Opções de Edição')
        self.label_edit_info.pack(expand=True, padx=1, pady=1)

        #=======================================================#
        # Frame widgets para apagar linhas
        #=======================================================#
        self.containerRemoveLines = self.widgets.get_frame(self.containerEditActions)
        self.containerRemoveLines.pack(expand=True, padx=3, pady=3, fill=tk.BOTH)
        
        # Combobox para apagar valores nulos de uma coluna qualquer da planilha.
        self.label_remove_null = self.widgets.get_label(self.containerRemoveLines)
        self.label_remove_null.config(text='Apagar linhas vazias')
        self.label_remove_null.pack(side=tk.LEFT, expand=True, fill='both', padx=1, pady=1)
        
        # Combobox ao lado do label APAGAR.
        self.combobox_delet_lines_in_col = self.widgets.get_combobox(
            self.containerRemoveLines, self.listColumnNames,
        )
        self.combobox_delet_lines_in_col.set('-')
        self.combobox_delet_lines_in_col.pack(side=tk.LEFT, expand=True, fill='both', padx=1, pady=1)
        
        # Botão para apagar valores vazios da coluna selecionda pelo usuário.
        self.btn_delet_null_lines = self.widgets.get_button(self.containerRemoveLines)
        self.btn_delet_null_lines.config(text='Apagar', command=self.action_remove_null_lines_in_col)
        self.btn_delet_null_lines.pack(side=tk.LEFT, expand=True, fill='both', padx=1, pady=1)

        #=======================================================#
        # Frame Para Widgets de remover coluna
        #=======================================================#
        self.containerRemoveColuns:ttk.Frame = self.widgets.get_frame(self.containerEditActions)
        self.containerRemoveColuns.pack(expand=True, padx=3, pady=3, fill=tk.BOTH)
        
        # Label informativo APAGAR colunas.
        self.label_rm_col = self.widgets.get_label(self.containerRemoveColuns)
        self.label_rm_col.config(text='Apagar coluna')
        self.label_rm_col.pack(side=tk.LEFT, expand=True, fill='both', padx=1, pady=1)
        # Botão/Combobox para apagar colunas (exibe uma lista de colunas quando clicado)
        self.combo_remove_colum = self.widgets.get_combobox(self.containerRemoveColuns, self.listColumnNames)
        self.combo_remove_colum.set('-')
        self.combo_remove_colum.pack(side=tk.LEFT, expand=True, fill='both', padx=1, pady=1)
        
        # Botão de ação para remover colunas da planilha
        self.btn_remove_columns:Button = self.widgets.get_button(self.containerRemoveColuns)
        self.btn_remove_columns.config(text='Apagar', command=self.action_delet_column)
        self.btn_remove_columns.pack(side=tk.LEFT, expand=True, fill='both', padx=1, pady=1)

        #=======================================================#
        # Frame para concatenar colunas
        #=======================================================#
        self.containerConcatColuns = self.widgets.get_frame(self.containerEditActions)
        #self.containerConcatColuns.config(style='LightPurple.TFrame')
        self.containerConcatColuns.pack(expand=True, padx=3, pady=3, fill=tk.BOTH)
        
        # Combobox para concatenar colunas
        self.label_concat = self.widgets.get_label(self.containerConcatColuns)
        self.label_concat.config(text='Concatenar')
        self.label_concat.pack(side=tk.LEFT, expand=True, fill='both', padx=1, pady=1)
        
        # Combo 1 de 3 - Concatenar
        self.combo_concat_1 = self.widgets.get_combobox(self.containerConcatColuns, self.listColumnNames,)
        self.combo_concat_1.set('-')
        self.combo_concat_1.config(width=7)
        self.combo_concat_1.pack(side=tk.LEFT, expand=True, fill='both', padx=1, pady=1)
        
        # Combo 2 de 3 - Concatenar
        self.combo_concat_2 = self.widgets.get_combobox(self.containerConcatColuns, self.listColumnNames,)
        self.combo_concat_2.set('-')
        self.combo_concat_2.config(width=7)
        self.combo_concat_2.pack(side=tk.LEFT, expand=True, fill='both', padx=1, pady=1)
        
        # Combo 3 de 3 - Concatenar
        self.combo_concat_3 = self.widgets.get_combobox(self.containerConcatColuns, self.listColumnNames,)
        self.combo_concat_3.set('-')
        self.combo_concat_3.config(width=7)
        self.combo_concat_3.pack(side=tk.LEFT, expand=True, fill='both', padx=1, pady=1)
        # botão concatenar
        self.btn_concat = self.widgets.get_button(self.containerConcatColuns)
        self.btn_concat.config(text='Concatenar', command=self.action_concat_columns,)
        self.btn_concat.pack(side=tk.LEFT, expand=True, fill='both', padx=1, pady=1)

        #=======================================================#
        # Frame para agrupar a coluna filtro, o texto a ser 
        # filtrado e a planilha de filtro.
        #=======================================================#
        # Frame para agrupar os widgets de filtro e exportação de dados.
        self.containerFilterAndExport = self.widgets.get_frame(self.containerSheetWidgets)
        #self.containerFilterAndExport.config(style='DarkPurple.TFrame')
        self.containerFilterAndExport.pack(expand=True, fill=tk.BOTH, padx=3, pady=3)

        #=======================================================#
        # Box dados para o filtro.
        #=======================================================#
        self.containerWidgetsFilter:Frame = self.widgets.get_frame(self.containerFilterAndExport)
        self.containerWidgetsFilter.config(style='DarkPurple.TFrame')
        self.containerWidgetsFilter.pack(side=tk.LEFT, expand=True, fill='both', padx=2, pady=2)
        
        # Label informativo para os tipos de filtro
        self.miniContainerLabelInfo = ttk.Frame(self.containerWidgetsFilter)
        self.miniContainerLabelInfo.pack(expand=True, fill='both', padx=3, pady=2)
        #
        self.label_info_filter = self.widgets.get_label(self.miniContainerLabelInfo)
        self.label_info_filter.config(text='Opções de filtro')
        self.label_info_filter.pack(padx=2, pady=2)
        
        # Frame para agrupar a coluna selecionada pelo usuário para filtrar os dados
        self.miniContainerColumnFilter:ttk.Frame = self.widgets.get_frame(self.containerWidgetsFilter)
        #self.miniContainerColumnFilter.config(style='DarkGray.TFrame')
        self.miniContainerColumnFilter.pack(expand=True, fill='both', padx=2, pady=2)
        
        # Frame para agrupar a caixa de texto de filtro.
        self.miniContainerInputTextFind:Frame = self.widgets.get_frame(self.containerWidgetsFilter)
        self.miniContainerInputTextFind.pack(expand=True, fill='both', padx=2, pady=2)
        
        # Combobox para o usuário informar a coluna da planilha onde os dados
        # devem ser filtrados.
        self.label_column:Label = self.widgets.get_label(self.miniContainerColumnFilter)
        self.label_column.config(text='Coluna (Filtro)')
        self.label_column.pack(side=tk.LEFT, expand=True, fill='both', padx=2, pady=2)
        # Combobox para o usuário informar a coluna da planilha onde os dados
        # devem ser filtrados.
        self.combobox_filter_column = self.widgets.get_combobox(
                                                self.miniContainerColumnFilter,
                                                self.listColumnNames,
                                            )
        self.combobox_filter_column.set('Selecione uma coluna')
        self.combobox_filter_column.pack(side=tk.LEFT, expand=True, fill='both', padx=2, pady=2)
        
        # Caixa de texto para o usuário informar o texto a ser filtrado.
        self.label_find_text:Label = self.widgets.get_label(self.miniContainerInputTextFind)
        self.label_find_text.config(text='Texto (Filtro)')
        self.label_find_text.pack(side=tk.LEFT, expand=True, fill='both', padx=2, pady=2)
        #
        self.box_find_text:Entry = self.widgets.get_input_box(self.miniContainerInputTextFind)
        self.box_find_text.pack(side=tk.LEFT, expand=True, fill='both', padx=2, pady=2)
        
        #=======================================================#
        # Frame Radio PLANILHA OU TEXTO
        #=======================================================#
        self.miniContainerRadiosFind: Frame = self.widgets.get_frame(self.containerWidgetsFilter)
        #self.miniContainerRadiosFind.config(style='DarkGray.TFrame')
        self.miniContainerRadiosFind.pack(expand=True, fill='both', padx=2, pady=2)
        
        # Radios para selecionar o tipo de filtro
        self.radio_text_or_sheet = tk.StringVar(value='from_text')
        #
        self.radio_opt_from_text = self.widgets.get_radio_button(self.miniContainerRadiosFind)
        self.radio_opt_from_text.config(
                        text='Filtrar com texto', 
                        variable=self.radio_text_or_sheet,
                        value='from_text',
                    )
        self.radio_opt_from_text.pack(side=tk.LEFT, expand=True, fill='both', padx=3, pady=2)
        #
        self.radio_opt_from_sheet = self.widgets.get_radio_button(self.miniContainerRadiosFind)
        self.radio_opt_from_sheet.config(
                            text='Filtrar de uma planilha',
                            variable=self.radio_text_or_sheet,
                            value='from_sheet',
                        )
        self.radio_opt_from_sheet.pack(side=tk.LEFT, expand=True, fill='both', padx=3, pady=2)

        #=======================================================#
        # Frame para o botão de selecionar planilha filtro
        #=======================================================#
        self.containerSelectSheet:Frame = self.widgets.get_frame(self.containerWidgetsFilter)
        self.containerSelectSheet.pack(expand=True)
        
        # Botão para o usuário filtrar textos apartir de uma planilha.
        self.btn_select_sheet:Button = self.widgets.get_button(self.containerSelectSheet)
        self.btn_select_sheet.config(text='Planilha de Filtro', command=self.select_sheet_filter)
        self.btn_select_sheet.pack(side=tk.LEFT, expand=True, fill='both', padx=2, pady=2)
        
        # Label para mostrar a planilha selecionada
        self.label_selected_sheet_filter: Label = self.widgets.get_label(self.containerSelectSheet)
        self.label_selected_sheet_filter.config(text='Arquivo filtro não selecionado')
        self.label_selected_sheet_filter.pack(side=tk.LEFT, expand=True, fill='both', padx=2, pady=2)
        
        #=======================================================#
        # Frame com botões radio - para selecionar o tipo de 
        # exportação.
        #=======================================================#
        self.containerOptionsExport: Frame = self.widgets.get_frame(self.containerFilterAndExport)
        self.containerOptionsExport.config(style='LightPurple.TFrame')
        self.containerOptionsExport.pack(expand=True, fill='both', padx=2, pady=2) 
        
        # Label informativo
        self.label_export_info = self.widgets.get_label(self.containerOptionsExport)
        self.label_export_info.config(text='Opções de exportação')
        self.label_export_info.pack(padx=3, pady=2)
        # exportar para único arquivo
        self.radio_value_uniq_or_multi = tk.StringVar(value="uniq_file")
        
        self.radio_uniq_file = self.widgets.get_radio_button(self.containerOptionsExport)
        self.radio_uniq_file.config(
                                text='Arquivo', 
                                variable=self.radio_value_uniq_or_multi, 
                                value='uniq_file'
                            )
        self.radio_uniq_file.pack(expand=True, fill='both', padx=3, pady=2)
        # exportar para vários arquivos
        self.radio_multi_files = self.widgets.get_radio_button(self.containerOptionsExport)
        self.radio_multi_files.config(
                                text='Arquivos', 
                                variable=self.radio_value_uniq_or_multi, 
                                value='multi_files'
                            )
        self.radio_multi_files.pack(expand=True, fill='both', padx=3, pady=2)
        # exportar valores únicos de uma coluna.
        self.radio_uniq_column = self.widgets.get_radio_button(self.containerOptionsExport)
        self.radio_uniq_column.config(
            text='Coluna', 
            variable=self.radio_value_uniq_or_multi, 
            value='uniq_column'
        )
        self.radio_uniq_column.pack(expand=True, fill='both', padx=3, pady=2)

        #=======================================================#
        # Frame OUTPUT
        #=======================================================#
        self.miniContainerButtons:Frame = self.widgets.get_frame(self.containerSheetWidgets)
        self.miniContainerButtons.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
        
        # Botão para carregar os dados.
        self.btn_load = ttk.Button(
            self.miniContainerButtons,
            text='Carregar Dados',
            command=self.operation_load_values,
        )
        self.btn_load.pack(side=tk.LEFT, expand=True, fill='both', padx=2, pady=2)
        
        # Botão para exportar a planilha filtrada.
        self.btn_export: Button = self.widgets.get_button(self.miniContainerButtons)
        self.btn_export.config(command=self.action_export_values, text='Exportar Excel')
        self.btn_export.pack(expand=True, fill='both', padx=2, pady=2)

    def setParse(self, p:ParseDF):
        if not isinstance(p, ParseDF):
            return
        self.__parse:ParseDF = p
        self.update_comboboxs()

    def getParse(self) -> ParseDF:
        return self.__parse   
         
    def check_values_column(self) -> bool:
        """
            Verificar se uma coluna válida foi selecionada pelo usuário, exibir mensagem de
        erro se necessário.
        """
        if self.getParse() is None:
            show_warnnings('Nenhuma planilha válida foi carregada, tente novamente!')
            return False
        if not self.getParse().exists_columns([self.combobox_filter_column.get()]):
            show_warnnings(f'Coluna inválida: {self.combobox_filter_column.get()}')
            return False
        return True
    
    def select_sheet_filter(self):
        """
            Caixa de diálogo para selecionar uma planilha para ser usada como filtro.
        """
        # uma planilha excel com uma coluna de textos que serão filtrados
        # na planilha principal.
        f = self.controller.openFiles.open_file_sheet()
        if not File(f).is_sheet():
            show_warnnings('Selecione uma planilha válida!')
            return
        self.__fileSheetFilter = File(f)

    def _check_sheet_filter(self) -> bool:
        """
            Checar o arquivo de filtro, exibir mensagens de erro se necessário.
        - obter o DataFrame().
        - verificar se possui a coluna de filtro informada pelo usuário na interface.
        """
        if self.__fileSheetFilter is None:
            show_warnnings('Selecione uma planilha para ser usada como filtro.')
            return False
        
        if not ParseDF(
                    SheetInputStream(self.__fileSheetFilter).get_data(),
                ).exists_column(self.combobox_filter_column.get()
            ):
            show_warnnings(f'Coluna não encontrada no arquivo FILTRO: {self.combobox_filter_column.get()}')
            return False
        return True
    
    def __get_data_filter(self) -> DataFrame:
        """
            Ler a planilha que o usuário selecionou para ser o filtro
        """
        if not self._check_sheet_filter():
            return DataFrame()
        return SheetInputStream(self.__fileSheetFilter).get_data()
    
    def action_concat_columns(self):
        """
            Ação conectada ao botão concatenar
        """
        t = Thread(target=self.__execute_concat_columns)
        t.start()

    def __execute_concat_columns(self):
        """
            Concatenar colunas
        essa ação deve ser executada em uma Thread para que seja exibido um loop ao usuário 
        enquanto a operação estiver em execução.
        """
        self.start_pbar()
        if not self.getParse().exists_columns(
                [self.combo_concat_1.get(), self.combo_concat_2.get(), self.combo_concat_3.get()]
            ):
            show_warnnings(f'Coluna(s) inválidas detectadas, tente novamente!')
            self.stop_pbar()
            return
        
        self.set_text_progress('Concatenando colunas')
        self.getParse().concat_columns(
            columns=[self.combo_concat_1.get(), self.combo_concat_2.get(), self.combo_concat_3.get()],
            new_col=f'{self.combo_concat_1.get()}-{self.combo_concat_2.get()}-{self.combo_concat_3.get()}',
            sep_cols='_',
        )
        self.stop_pbar()
    
    def action_delet_column(self):
        """
            Ação conectada ao botão para remover colunas
        Deleta uma coluna.
        """
        t = Thread(target=self.__execute_delet_column)
        t.start()

    def __execute_delet_column(self):
        self.start_pbar()
        self.set_text_progress(f'Apagando coluna: {self.combo_remove_colum.get()}')
        self.getParse().delet_columns([self.combo_remove_colum.get()]) 
        self.update_comboboxs()
        self.stop_pbar()
    
    def action_remove_null_lines_in_col(self):
        """
            Remove todas as linhas vazias da planilha com base na coluna selecionada.
        """
        if not self.check_running():
            return
        t = Thread(target=self.__execute_remove_null_lines_in_column)
        t.start()
        
    def __execute_remove_null_lines_in_column(self):
        """
            Remover linhas vazias da coluna selecionada.
        """
        self.start_pbar()
        if not self.getParse().exists_column(self.combobox_delet_lines_in_col.get()):
            show_warnnings(f'A coluna não exite:{self.combobox_delet_lines_in_col.get()}')
            self.stop_pbar()
            return
        self.getParse().remove_null(col=self.combobox_delet_lines_in_col.get())
        self.update_comboboxs()
        self.stop_pbar()
    
    def action_export_values(self):
        """
            Ação conectada ao botão de EXPORTAR.
        """
        if not self.check_running():
            return
        if not self.check_values_column():
            return
          
        if self.radio_value_uniq_or_multi.get() == 'uniq_column':
            exec_thread = threading.Thread(target=self.__export_uniq_column)
        elif self.radio_value_uniq_or_multi.get() == 'multi_files':
            exec_thread = threading.Thread(target=self.__export_multi_files)
        elif self.radio_value_uniq_or_multi.get() == 'uniq_file':
            exec_thread = threading.Thread(target=self.__export_uniq_file)
        else:
            return
        exec_thread.start()
    
    def __export_multi_files(self):
        """
            Filtrar o texto informado pelo usuário e exportar para um vários arquivos.
        - Para cada DADO filtrado será criado um novo arquivo Excel no disco.
        """
        self.start_pbar()
        if self.radio_text_or_sheet.get() == 'from_text':
            values_filter = [self.box_find_text.get()]
        elif self.radio_text_or_sheet.get() == 'from_sheet':
            df_filter = self.__get_data_filter().astype('str')
            if df_filter.empty:
                show_warnnings(f'A planilha de filtro está vazia!')
                self.stop_pbar()
                return
            values_filter:List[str] = ParseDF(df_filter).uniq_column(
                                                            self.combobox_filter_column.get()
                                                        ).values.tolist()
        #
        if len(values_filter) < 1:
            show_warnnings('Filtros vazios, tente novamente!')
            self.stop_pbar()
            return
        
        max_num = len(values_filter)
        for num, element in enumerate(values_filter):
            self.set_text_progress(f'{((num/max_num)*100):.1f}')
            self.set_text_label_output(f'[FILTRANDO]: {num+1} de {max_num} | {element}')
            #
            df = self.getParse().find_elements(
                col=self.combobox_filter_column.get(),
                text=element,
                iqual=True,
            ).data
            if (df is not None) and (not df.empty):
                # DataFrame e Arquivo.
                export_dataframe(
                    df,
                    self.controller.saveDir.join_file(
                            f'{self.combobox_filter_column.get()}-{element}.xlsx'
                        )
                )
            
        self.stop_pbar()

    def __export_uniq_file(self):
        """
            Filtrar o texto informado pelo usuário e exportar para um arquivo
        """
        self.start_pbar()
        # Obter os texto(s) a serem filtrado(s) / Arquivo ou texto digitado pelo usuário.
        if self.radio_text_or_sheet.get() == 'from_text':
            values_filter = [self.box_find_text.get()]
        elif self.radio_text_or_sheet.get() == 'from_sheet':
            df_filter = self.__get_data_filter().astype('str')
            if df_filter.empty:
                show_warnnings(f'A planilha de filtro está vazia!')
                self.stop_pbar()
                return
            values_filter:List[str] = ParseDF(df_filter).uniq_column(
                                                            self.combobox_filter_column.get()
                                                        ).values.tolist()
        # Verificar se a lista de textos a ser(em) filtrado(s) está vazia.
        if len(values_filter) < 1:
            show_warnnings('Filtros vazios, tente novamente!')
            self.stop_pbar()
            return
        
        # Arquivo para exportar
        output_file:str = self.controller.openFiles.save_file(FilesTypes.SHEET)
        if (output_file is None) or (len(output_file) < 1):
            show_warnnings('Nenhum arquivo foi selecionado!')
            self.stop_pbar()
            return
        
        max_num = len(values_filter)
        data:List[DataFrame] = []
        for num, element in enumerate(values_filter):
            self.set_text_progress(f'{((num/max_num)*100):.1f}')
            self.set_text_label_output(f'[FILTRANDO]: {num+1} de {max_num} | {element}')
            #
            df = self.getParse().find_elements(
                col=self.combobox_filter_column.get(),
                text=element,
                iqual=True,
            ).data
            if (df is not None) and (not df.empty):
               data.append(df)
        # Exportar
        export_dataframe(
            pandas.concat(data),
            File(output_file),
        )
        self.set_text_label_output('OK')
        self.set_text_progress('100')
        self.stop_pbar()

    def __export_uniq_column(self):
        """
            Exporta apenas uma coluna para um arquivo excel.
        """
        # Obter apenas valores não duplicados, da coluna que o usuário selecionou para exportar.
        self.start_pbar()
        if not self.getParse().exists_column(self.combobox_filter_column.get()):
            show_warnnings(f'Coluna inválida: {self.combobox_filter_column.get()}')
            self.stop_pbar()
            return
        
        output_file = self.controller.openFiles.save_file(FilesTypes.EXCEL)
        if output_file is None:
            show_warnnings(f'Arquivo inválido! {output_file}')
            self.stop_pbar()
            return
        #
        f = File(output_file)
        self.set_text_progress(f'Exportando coluna: {self.combobox_filter_column.get()} | {f.basename()}')
        export_dataframe(
            self.getParse().select_columns([self.combobox_filter_column.get()]).data.drop_duplicates(),
            f,
        )
        self.set_text_progress(f'[OK] Coluna exportada.')
        self.stop_pbar()
    
    def operation_load_values(self):
        if not self.check_running():
            return
        t = Thread(target=self._load_selected_sheets)
        t.start()
        
    def _load_selected_sheets(self) -> bool:
        """
            Ler a(s) planilha(s) selecionada(s) pelo usuário e obter o DataFrame()
        """
        if not self.check_running():
            return
        if self.controller.numSelectedFiles < 1:
            show_warnnings(f'Selecione uma ou mais planilhas para prosseguir!')
            return
        
        self.start_pbar()
        data:List[DataFrame] = []
        for num, file in enumerate(self.controller.selectedUserFiles):
            self.set_text_label_output(f'Lendo arquivo: {num+1} de {self.controller.numSelectedFiles}')
            if file.is_sheet():
                try:
                    _input_stream = SheetInputStream(file, load_now=True)
                    while True:
                        if not _input_stream.is_running():
                            break
                        self.set_text_progress(f'{_input_stream.get_progress():.2f}')
                        time.sleep(1)
                    df = _input_stream.get_data()
                except Exception as e:
                    print(e)
                    show_warnnings(f'{__class__.__name__}\n{e}')
                else:
                    if isinstance(df, DataFrame):  
                        data.append(df)
        #
        if len(data) < 1:
            self.set_text_label_output('FALHA!')
            self.stop_pbar()
            return
        self.set_text_label_output('Preparando dados, aguarde!')
        # Setar os dados obtidos da planilha.
        self.setParse(
            ParseDF(pandas.concat(data).astype('str'))
        )
        self.set_text_label_output('OK')
        self.set_text_progress('100')
        self.stop_pbar()
        
    def update_comboboxs(self) -> None:
        """
            Atualizar os valores dos combobox que usam o cabeçalho do DataFrame
        """
        self.combobox_filter_column['values'] = self.getParse().data.columns.tolist()
        self.combobox_delet_lines_in_col['values'] = self.getParse().data.columns.tolist()
        self.combo_remove_colum['values'] = self.getParse().data.columns.tolist()
        self.combo_concat_1['values'] = self.getParse().data.columns.tolist()
        self.combo_concat_2['values'] = self.getParse().data.columns.tolist()
        self.combo_concat_3['values'] = self.getParse().data.columns.tolist()
        
    def set_text_label_output(self, text:str) -> None:
        self.container_pbar.set_text_pbar(text)

    def set_text_progress(self, text):
        self.container_pbar.set_text_progress(text)

    def start_pbar(self):
        self.running = True
        self.container_pbar.start_pbar()

    def stop_pbar(self):
        self.running = False
        self.container_pbar.stop_pbar()
        
    def set_size_screen(self):
        """Redimensionar o tamanho da janela quando esta página for aberta."""
        self.parent.title("Filtra texto em planilhas")
        self.parent.geometry("800x420")

    def update_state(self):
        """
            Carregar algumas informações enquanto a janela é exibida.
        """
        pass

#========================================================#
# Planilhar Pasta
#========================================================#
class PageFilesToExcel(AppPage):
    """
        Página para planilhar pasta.
    """
    def __init__(self, *, parent, controller):
        super().__init__(parent=parent, controller=controller)
        self.pageName = '/home/select_actions/folder_to_excel'
        
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
        self.mainContainerIo = self.widgets.get_frame(self.frame_main_window)
        self.mainContainerIo.pack(side=tk.LEFT)
        
        #===============================================================#
        # 2 - Box para importar Arquivos
        #===============================================================#
        self.frame_import_files = self.widgets.get_frame(self.mainContainerIo)
        self.frame_import_files.pack(side=tk.LEFT, expand=True, fill='both', padx=1, pady=1)
        
        self.container_import_files = ContainerImportFiles(
            frame=self.frame_import_files, 
            controller=self.controller,
            input_files_type=FilesTypes.ALL_TYPES
        )
        
        #===============================================================#
        # 3 - Box para exportar arquivos
        #===============================================================#
        self.frame_export_files = self.widgets.get_frame(self.mainContainerIo)
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
        
        # 1 - 
        self.btn_to_excel = ttk.Button(
            self.frame_buttons_export,
            text='Para Excel',
            command=self.convert_folder_to_excel,
        )
        self.btn_to_excel.pack(expand=True, fill='both', padx=2, pady=1)
        
        # 2 - 
        self.btn_to_pdf = ttk.Button(
            self.frame_buttons_export,
            text='Para CSV',
            command=self.convert_folder_to_csv,
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
        
    def convert_folder_to_excel(self):
        """
            Planilhar os arquivos selecionados.
        """
        if not self._check_selected_files():
            return
        th = Thread(target=self._operation_convet_folder_to_excel)
        th.start()
        
    def _operation_convet_folder_to_excel(self):
        """
            -
        """
        self.start_pbar()
        self.set_text_pbar('Planilhando arquivos aguarde')
        df = self.__get_info_files()
        out_file = self.controller.saveDir.join_file('Arquivos-Planilhados.xlsx')
        export_dataframe(df, out_file, file_type=FilesTypes.EXCEL)
        
        self.set_text_progress('100')
        self.set_text_pbar('OK')
        self.stop_pbar()
        self.running = False
        
    def convert_folder_to_csv(self):
        """
            -
        """
        if not self._check_selected_files():
            return
        t = Thread(target=self._operation_convert_to_csv)
        t.start()
        
    def _operation_convert_to_csv(self):
        self.start_pbar()
        self.set_text_pbar('Planilhando arquivos aguarde')
        df = self.__get_info_files()
        out_file = self.controller.saveDir.join_file('Arquivos-Planilhados.csv')
        export_dataframe(df, out_file, file_type=FilesTypes.CSV)
        
        self.set_text_progress('100')
        self.set_text_pbar('OK')
        self.stop_pbar()
        self.running = False
        
    def __get_info_files(self) -> DataFrame:
        """
            Obter uma lista de com os nomes dos arquivos selecionados pelo usuário.
        """
        data:List[DataFrame] = []
        for num, file in enumerate(self.controller.selectedUserFiles):
            current = {} 
            current['NOME'] = [file.name()]
            current['ARQUIVO'] = [file.absolute()]
            current['TIPO'] = [file.extension()]
            current['PASTA'] = [file.dirname()]
            data.append(DataFrame(current))
        return pandas.concat(data)
        
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
        self.parent.title(f"Planilhar Pasta")

    def update_state(self):
        pass
    
#========================================================#
# Mover arquivos
#========================================================#
class PageMoveFiles(AppPage):
    """
        Página para mover arquivos..
    """
    def __init__(self, *, parent, controller):
        super().__init__(parent=parent, controller=controller)
        self.pageName = '/home/select_actions/move_files'
        
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
            input_files_type=FilesTypes.EXCEL
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
        
        # 1 - 
        self.btn_to_excel = ttk.Button(
            self.frame_buttons_export,
            text='Mover',
            command=self.action_move_files,
        )
        self.btn_to_excel.pack(expand=True, fill='both', padx=2, pady=1)
         
        # 6 - Barra de progresso
        self.frame_pbar = self.widgets.get_frame(self.frame_master)
        self.frame_pbar.pack(expand=True, fill='both', padx=1, pady=1)
        self.container_pbar = self.widgets.container_pbar(self.frame_pbar)
     
    def _check_selected_files(self) -> bool:
        if len(self.controller.selectedUserFiles) < 1:
            show_warnnings('Selecione arquivos para prosseguir!')
            return False
        return True
        
    def action_move_files(self):
        if not self._check_selected_files():
            return
        th = Thread(target=self._operation_move_files)
        th.start()
        
    def _operation_move_files(self):
        """
            -
        """
        self.start_pbar()
        self.set_text_pbar('Lendo base | Aguarde!')
        data:List[DataFrame] = []
        for f in self.controller.selectedUserFiles:
            df = SheetInputStream(f, load_now=True).get_data()
            if not 'ARQUIVO' in df.columns.tolist():
                continue
            if not 'NOVO_NOME' in df.columns.tolist():
                continue
            data.append(df)
        #
        final_df = pandas.concat(data)
        if not 'ARQUIVO' in final_df.columns.tolist():
            show_warnnings('Coluna [ARQUIVO] não encontrada!')
            self.stop_pbar()
            return
        if not 'NOVO_NOME' in final_df.columns.tolist():
            show_warnnings('Coluna [NOVO_NOME] não encontrada!')
            self.stop_pbar()
            return
        #
        final_df = ParseDF(final_df).select_columns(['ARQUIVO', 'NOVO_NOME']).data
        final_df.drop_duplicates()
        final_df.dropna(subset=['ARQUIVO', 'NOVO_NOME'])
        print(final_df)
        #
        self.set_text_pbar('Movendo arquivos')
        max_num = len(final_df)
        for idx, value in final_df.iterrows():
            self.set_text_progress(f'{(idx/max_num)*100:.1f}')
            self.set_text_pbar(f'Movendo: {value[1]}')
            src_file = File(value[0])
            output_name = FormatString(value[1]).replace_bad_chars(new_char='_').replace_all('/').value
            output_file = self.controller.saveDir.join_file(f'{output_name}{src_file.extension()}')
            
            if not src_file.path.exists(): # src
                continue
            if output_file.path.exists():
                continue
            
            print(output_file.absolute())
            try:
                shutil.move(
                    src_file.absolute(),
                    output_file.absolute()
                )
            except Exception as e:
                print(e)
            
        
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
        self.parent.title(f"Mover Arquivos")

    def update_state(self):
        pass

