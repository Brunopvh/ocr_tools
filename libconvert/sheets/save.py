#!/usr/bin/env python3
#
from __future__ import annotations
from typing import List
from abc import ABC, abstractmethod
from pandas import DataFrame
import pandas
from libconvert.utils.file import (
    File, 
    Directory, 
    FilesTypes,
)

from libconvert.sheets.load import (
    ParseData,
)

def export_dataframe(df:DataFrame, file:File, *, file_type:FilesTypes=FilesTypes.EXCEL, index:bool=False):
    print(f'[EXPORTANDO]: {file.absolute()}', end=' ')
    if '.xlsx' in file_type.value:
        df.to_excel(file.absolute(), index=index)
    elif '.csv' in file_type.value:
        df.to_csv(file.absolute(), index=index, sep='\t')
    elif '.json' in file_type.value:
        df.to_json(file.absolute())
    else:
        df.to_excel(file.absolute(), index=index)
    print('OK')

class ABCSaveSheets(ABC):
    def __init__(
            self, 
            outdir:Directory, 
            *, 
            col_toname:str,
            separator:str='\t', 
            index:bool=False,
            files_types:FilesTypes=FilesTypes.EXCEL,
        ):
        """
            outdir: Directory = pasta para salvar os dataframes
            inname:List[str]  = usar o texto da linha/linhas nas colunas informadas.
            separator:str = usado em CSV para separar os textos
            index:bool = salvar o índice na planilha exportada. 
        """
        #
        self.separator:str=separator
        self.index:bool=index
        self.outdir:Directory=outdir
        self.col_toname:str = col_toname
        self.file_types:FilesTypes = files_types
        self.erros:int = 0
    
    @abstractmethod
    def get_num_erros(self) -> int:
        return self.erros

    @abstractmethod
    def save(self, list_data:List[DataFrame], multi_files:bool=True) -> bool:
        pass

    @abstractmethod
    def get_progress(self) -> float:
        pass

    @abstractmethod
    def get_text(self) -> float:
        pass

    @abstractmethod
    def is_running(self) -> bool:
        pass

#
class SaveSheets(ABCSaveSheets):
    def __init__(
                self, 
                outdir:Directory, 
                *, 
                col_toname:str, 
                separator:str='\t', 
                index:bool=False, 
                files_types=FilesTypes.EXCEL,
            ):
        super().__init__(outdir, col_toname=col_toname, separator=separator, index=index, files_types=files_types)
        self._current_prog:float = 0
        self._current_text:str = ''
        self._running:bool = False
        self.extension = self.file_types.value[0]

    def is_running(self):
        return self._running

    def get_progress(self):
        return self._current_prog
    
    def get_text(self):
        return self._current_text
    
    def get_num_erros(self):
        return self.erros
    
    def _save_multifiles(self, data:List[DataFrame]):
        self._running = True
        max_num:int = len(data)
        if max_num < 1:
            self._current_text = 'Dados vazios'
            print(f'{__class__.__name__} {self.get_text()}')
            self._running = False
            return
        #
        for num, df in enumerate(data):
            self._current_prog = (num/max_num) * 100
            if df.empty:
                self.erros += 1
                continue
            #
            df = df.astype('str')
            if not self.col_toname in df.columns.tolist():
                self.erros += 1
                continue
            current_name = f'{num+1}_{self.col_toname}_{df[self.col_toname].values.tolist()[0]}{self.extension}'
            self._current_text = f'[EXPORTANDO] {num+1} de {max_num} | Arquivo: {current_name}'
            try:
                export_dataframe(
                    df,
                    self.outdir.join_file(current_name),
                    file_type=self.file_types,
                    index=self.index,
                )
            except Exception as e:
                self.erros += 1
                print(f'{__class__.__name__}\n{e}')
            #
        self._current_prog = 100
        self._running = False

    def _save_uniq_file(self, data:List[DataFrame]):
        self._running = True
        if len(data) < 1:
            self._current_text = 'Dados vazios'
            print(f'{__class__.__name__} {self.get_text()}')
            self._running = False
            return
        #
        self._current_text = 'Unindo Dados aguarde...'
        print(self.get_text())
        df = pandas.concat(data).astype('str')
        if not self.col_toname in df.columns.tolist():
            self.erros += 1
            self._current_text = f'{__class__.__name__} a coluna não existe: {self.col_toname}'
            print(self.get_text())
            return
        current_name = f'{self.col_toname}_{df[self.col_toname].values.tolist()[0]}{self.extension}'
        self._current_text = f'[EXPORTANDO] {current_name}'
        export_dataframe(
            df,
            self.outdir.join_file(f'{current_name}'),
            file_type=self.file_types,
            index=self.index,
        )
        #
        self._current_prog = 100
        self._running = False

    def save(self, data:List[DataFrame], multi_files:bool=True):
        if multi_files == True:
            self._save_multifiles(data)
        else:
            self._save_uniq_file(data)
        
class SheetOutputStream(ABCSaveSheets):
    """FACADE"""
    def __init__(
                self, 
                outdir:Directory, 
                *, 
                col_toname:str, 
                separator:str='\t', 
                index:bool=False, 
                files_types:FilesTypes=FilesTypes.EXCEL
            ):
        super().__init__(outdir, col_toname=col_toname, separator=separator, index=index, files_types=files_types)
        self._save_sheets:ABCSaveSheets = SaveSheets(
            self.outdir,
            col_toname=self.col_toname,
            separator=self.separator,
            index=self.index,
            files_types=self.file_types,
        )

    def get_num_erros(self):
        return self._save_sheets.get_num_erros()
    
    def get_progress(self):
        return self._save_sheets.get_progress()

    def get_text(self):
        return self._save_sheets.get_text()
    
    def save(self, data:List[DataFrame], multi_files:bool = True):
        if not isinstance(data, list):
            raise ValueError(f'{__class__.__name__} [FALHA]\n data não é List[DataFrame] >>{type(data)}<<')
        self._save_sheets.save(data, multi_files)
    
    def is_running(self):
        return self._save_sheets.is_running()