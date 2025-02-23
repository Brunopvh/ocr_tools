#!/usr/bin/env python3
#
from __future__ import annotations
from typing import List, Dict, Tuple
from enum import Enum
#
import os
import json
import platform
from pathlib import Path
from hashlib import md5


KERNEL_TYPE = platform.system()

class FilesTypes(Enum):
    IMAGE = ['.png', '.jpg', '.jpeg', '.svg']
    PDF = ['.pdf']
    EXCEL = ['.xlsx']
    CSV = ['.csv', '.txt']
    #
    SHEET = ['.csv', '.txt', '.xlsx', '.xls']
    JSON = ['.json']
    #
    ALL_TYPES = [
        '.png', '.jpg', '.jpeg', '.svg',
        '.csv', '.txt', '.xlsx', '.pdf',
        '.json',
    ]


class File(object):
    def __init__(self, filename:str):
        if os.path.isdir(filename):
            raise ValueError(f'{__class__.__name__} File() não pode ser um diretório.')

        self.filename:str = filename
        self.__path:Path = Path(os.path.abspath(self.filename))

    @property
    def path(self) -> Path:
        return self.__path
    
    @path.setter
    def path(self, new:Path):
        if not isinstance(new, Path):
            return
        self.__path = new

    def is_image(self) -> bool:
        return True if self.extension() in FilesTypes.IMAGE.value else False

    def is_pdf(self) -> bool:
        return True if self.extension() in FilesTypes.PDF.value else False

    def is_sheet(self) -> bool:
        return True if self.extension() in FilesTypes.SHEET.value else False

    def update_extension(self, e:str) -> File:
        """
            Retorna uma instância de File() no mesmo diretório com a nova
        extensão informada.
        """
        current = self.extension()
        full_path = self.absolute().replace(current, '')
        return File(os.path.join(f'{full_path}{e}'))

    def get_text(self) -> str:
        return self.__path.read_text()

    def write_string(self, s:str):
        self.__path.write_text(s)

    def write_list(self, items:List[str]):
        # Abrindo o arquivo em modo de escrita
        with open(self.filename, "w", encoding="utf-8") as file:
            for string in items:
                file.write(string + "\n")  # Adiciona uma quebra de linha após cada string

    def name(self):
        e = self.extension()
        if (e is None) or (e == ''):
            return os.path.basename(self.filename)
        return os.path.basename(self.filename).replace(e, '')
    
    def name_absolute(self) -> str:
        e = self.extension()
        if (e is None) or (e == ''):
            return os.path.abspath(self.filename)
        return os.path.abspath(self.filename).replace(e, '')

    def extension(self) -> str:
        return self.__path.suffix

    def dirname(self) -> str:
        return os.path.dirname(self.filename)

    def basename(self) -> str:
        return os.path.basename(self.filename)

    def exists(self) -> bool:
        return self.__path.exists()

    def absolute(self) -> str:
        return os.path.abspath(self.filename)
    
    def size(self):
        return os.path.getsize(self.filename)
    
    def md5(self) -> str | None:
        """Retorna a hash md5 de um arquivo se ele existir no disco."""
        if not self.path.exists():
            return None
        _hash_md5 = md5()
        with open(self.absolute(), "rb") as f:
            for _block in iter(lambda: f.read(4096), b""):
                _hash_md5.update(_block)
        return _hash_md5.hexdigest()


class Directory(object):
    def __init__(self, dirpath:str):
        self.dirpath:str = dirpath
        self.path:Path = Path(self.dirpath)
        
    def iterpaths(self) -> List[Path]:
        return self.path.rglob('*')
    
    def content_files(self) -> List[File]:
        _paths = self.iterpaths()
        values = []
        for p in _paths:
            if p.is_file():
                values.append(
                    File(
                        os.path.abspath(p.absolute())
                    )
                )
        return values
    
    def basename(self) -> str:
        return os.path.basename(self.absolute())

    def mkdir(self):
        try:
            os.makedirs(self.absolute())
        except:
            pass

    def absolute(self) -> str:
        return os.path.abspath(self.path.absolute())

    def concat(self, d:str) -> Directory:
        return Directory(
                os.path.join(self.absolute(), d)
            )

    def parent(self) -> Directory:
        return Directory(
            os.path.abspath(self.path.parent)
        )

    def join_file(self, name:str) -> File:
        return File(
            os.path.join(self.absolute(), name)
        )
   
   
class InputFiles(object):
    """
        Obeter uma lista de arquivos/documentos do diretório especificado.
    """
    def __init__(self, d:Directory, *, maxFiles:int=4000):
        self.input_dir:Directory = d
        self.max:int = maxFiles

    def get_files(self, *, file_type:FilesTypes = FilesTypes.ALL_TYPES) -> List[File]:
        """
            Retorna uma lista de File() de acordo com o tipo de arquivo
        especificado.
        - FilesTypes.ALL_TYPES => Retorna todos os arquivos do diretório.
        - FilesTypes.EXCEL     => Retornar arquivos que são planilhas, se existir
        - ...
        
        """
        _paths = self.input_dir.iterpaths()
        _all = []
        count:int = 0
        for p in _paths:
            if not p.is_file():
                continue
            e = p.suffix
            if (e is not None) and (e != ''):
                if e in file_type.value:
                    _all.append(File(p.absolute()))
                    count += 1
            if count >= self.max:
                break
        return _all


class JsonData(object):
    """
        Representação de um dado JSON apartir de uma string python.
    """
    def __init__(self, string:str):
        if not isinstance(string, str):
            raise ValueError(f'{__class__.__name__} o JSON informado precisa ser do tipo string, não {type(string)}')
        self.value:str = string
        
    def to_string(self) -> str:
        return self.value
        
    def to_dict(self) -> Dict[str, object]:
        """
            Exporta/Converte o dado atual em um dicionário python.
        """
        return JsonConvert().json_to_dict(self.value)

    def to_file(self, f:File):
        """Exporta o dado atual para um arquivo .json"""
        # Escrever em um arquivo
        print(f'[EXPORTANDO]: {f.absolute()}')
        _data = json.loads(self.value)
        with open(f.absolute(), "w", encoding="utf-8") as file:
            json.dump(_data, file, indent=4, ensure_ascii=False)


class JsonConvert(object):
    """Conversão de um dado JSON em dados python"""
    def __init__(self):
        pass

    def from_file(self, f:File) -> JsonData:
        """Gerar um dado JsonData apartir de um arquivo .json"""
        #content = f.path.read_text(encoding='utf8')
        # Ler o arquivo e carregar o JSON em um dicionário Python
        with open(f.absolute(), "r", encoding="utf-8") as file:
            data = json.load(file)
        return JsonData(
            json.dumps(data, indent=4, ensure_ascii=False, sort_keys=True)
        )

    def from_string_json(self, data:str) -> JsonData:
        return self.from_dict(self.json_to_dict(data))

    def from_dict(self, data:Dict[str, object]) -> JsonData:
        """
            Converte um dicionário em objeto JSON/JsonData.
        """
        if not isinstance(data, dict):
            raise ValueError(f'{__class__.__name__} Informe um JSON em formato dict, não {type(data)}')
        # Converter para JSON
        json_string = json.dumps(data, indent=4, ensure_ascii=False, sort_keys=True)
        return JsonData(json_string)
    
    def json_to_dict(self, string:str) -> Dict[str, object]:
        """Gerar um dicionário python apartir de uma string/JSON"""
        if not isinstance(string, str):
            raise ValueError(f'{__class__.__name__} Informe um JSON em formato string, não {type(string)}')
        # Converter para dicionário Python
        return json.loads(string)
    


class AppDirs(object):
    def __init__(self, appname:str):
        self.appname = appname
        self.user_home:Directory = Directory(Path().home())
        self.work_appdir:Directory = self.user_home.concat('Downloads').concat(self.appname)
        self.work_appdir.mkdir()
        #
        self.file_config:File = self.work_appdir.join_file('cfg.json')
        
    def get_workdir(self) -> Directory:
        return self.work_appdir
    
    def get_cache_dir(self) -> Directory:
        return self.user_home.concat('var').concat(f'cache-{self.appname}')
