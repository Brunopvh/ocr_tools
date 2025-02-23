#!/usr/bin/env python3
#
from typing import List, Dict
import shutil
from pathlib import Path
from libconvert import (
    File,
    Directory,
    KERNEL_TYPE,
)

# Diretório raiz do usuário.
USER_HOME:Directory = Directory(Path().home().absolute())

class UserFileSystem(object):
    """
        Diretórios comuns para cache e configurações de usuário.
    """
    def __init__(self, base_home:Directory=USER_HOME):
        self.baseHome:Directory = base_home
        self.userDownloads:Directory = base_home.concat('Downloads')
        self.userVarDir:Directory = base_home.concat('var')
        
    def config_dir(self) -> Directory:
        return self.userVarDir.concat('config')
    
    def cache_dir(self) -> Directory:
        return self.userVarDir.concat('cache')
    
    
class UserAppDir(object):
    """
        Diretório comun para cache e configurações do aplicativo.
    """
    def __init__(self, appname:str, *, user_file_system:UserFileSystem=UserFileSystem()):
        self.appname = appname
        self.userFileSystem:UserFileSystem = user_file_system
        self.workspaceDirApp:Directory = self.userFileSystem.userDownloads.concat(self.appname)
        self.installDir:Directory = self.userFileSystem.userVarDir.concat('opt').concat(self.appname)
        
    def cache_dir_app(self) -> Directory:
        return self.userFileSystem.cache_dir().concat(self.appname)
    
    def config_dir_app(self) -> Directory:
        #return self.userFileSystem.config_dir().concat(self.appname)
        return self.userFileSystem.userDownloads.concat(self.appname).concat('config')
    
class PackageApp(object):
    def __init__(self, *, name:str, pkg_filename:str, user_app_dir:UserAppDir, url:str):
        self.name:str = name
        self.pkgFileName = pkg_filename
        self.userAppDir:UserAppDir = user_app_dir
        self.url:str = url
        self.downloadedFile:File = self.userAppDir.cache_dir_app().join_file(self.pkgFileName)
        self.installDir:Directory = self.userAppDir.cache_dir_app().concat(self.name)
    
    

def get_user_dir_var(prefix:str='var') -> Directory:
    """
        Criar um diretório padrão na pasta do usuário para salvar cache e configurações.
    O padrão é HOME/var - altere o 'prefix' para salvar em um local diferente, exemplo
    
    - get_user_dir_var('CACHE')
    - get_user_dir_var('TMP')
    
    """
    return USER_HOME.concat(prefix)

def get_path_tesseract_system() -> File | None:
    """
        Atribuir o caminho de instalação do tesseract no sistema, se o tesseract 
    não estiver instalado no sistema, será atribuido um caminho padrão na HOME do
    usuário, no entanto se você tentar extrair textos de imagens sem instalar o tesseract 
    no caminho padrão, a operação irá falhar.
    """
    name = 'tesseract'
    if KERNEL_TYPE == 'Windows':
        # Para Windows usar tesseract.exe
        name += '.exe'
    
    # Verificar se este executável está no PATH do sistema.
    full_path = shutil.which(name)
    if full_path is None:
        _dir_local_tesseract  = get_user_dir_var().concat('opt').concat('Tesseract-OCR')
        _dir_local_tesseract.mkdir()
        path_tesseract = _dir_local_tesseract.join_file(name)
    else:
        # Padrão do sistema.
        path_tesseract = File(full_path)
    return path_tesseract

#
class UserPrefs(object):
    """
        Gravar algumas preferências do usuário.
    """
    def __init__(self, user_app_dir:UserAppDir):
        self.userAppDir:UserAppDir = user_app_dir
        self.prefs:Dict[str, str] = {}
        
        __tess_path = '-'
        if get_path_tesseract_system().path.exists():
            __tess_path = get_path_tesseract_system().absolute()
            
        self.prefs['tesseract_data'] = self.userAppDir.cache_dir_app().concat('tessdata').absolute()
        self.prefs['path_tesseract'] = __tess_path
        self.prefs['dir_output_files'] = self.userAppDir.workspaceDirApp.absolute()
        self.prefs['dir_cache'] = self.userAppDir.cache_dir_app().absolute()
        self.prefs['dir_config'] = self.userAppDir.config_dir_app().absolute()
        self.prefs['file_json'] = self.userAppDir.config_dir_app().join_file('cfg.json').absolute()
        self.prefs['initial_dir'] = self.userAppDir.userFileSystem.userDownloads.absolute()
        self.prefs['last_inputdir'] = self.userAppDir.userFileSystem.userDownloads.absolute()
        self.prefs['last_outputdir'] = self.userAppDir.userFileSystem.userDownloads.absolute()
    
 