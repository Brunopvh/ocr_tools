#!/usr/bin/env python3
#
from __future__ import annotations
from datetime import datetime
from pandas import Timestamp
import re


def is_valid_date(d) -> bool:
    valid_formats = (
            '%d-%m-%Y',  # Exemplo: 11-01-2025
            '%d/%m/%y',
            '%d-%m-%y',
            '%Y/%m/%d',  # Exemplo: 2025/01/11
            '%d/%m/%Y',  # Exemplo: 11/01/2025
            '%Y-%m-%d',  # Exemplo: 2025-01-11
            '%d %B %Y',  # Exemplo: 11 Janeiro 2025
            '%b %d, %Y', # Exemplo: Jan 11, 2025
            '%A, %d %B %Y', # Exemplo: Sábado, 11 Janeiro 2025
            '%H:%M:%S',  # Exemplo: 08:35:00
            '%H:%M',     # Exemplo: 08:35
            '%I:%M %p',  # Exemplo: 08:35 AM
            '%Y-%m-%d %H:%M:%S',  # Exemplo: 2025-01-11 08:35:00
            '%Y-%m-%dT%H:%M:%S',  # Exemplo: 2025-01-11T08:35:00 (Formato ISO 8601)
            '%Y%m%dT%H%M%S',      # Exemplo: 20250111T083500 (Formato compactado)
        )
        #
        
    _valid = False
    for fmt in valid_formats:
        try:
            datetime.strptime(d, fmt)
            _valid = True
            break
        except ValueError:
            pass
    #
    return _valid


class FormatDate(object):
    def __init__(self):
        """
        -
        """
        
        self.valid_formats = (
            '%d-%m-%Y',  # Exemplo: 11-01-2025
            '%d/%m/%y',
            '%d-%m-%y',
            '%Y/%m/%d',  # Exemplo: 2025/01/11
            '%d/%m/%Y',  # Exemplo: 11/01/2025
            '%Y-%m-%d',  # Exemplo: 2025-01-11
            '%d %B %Y',  # Exemplo: 11 Janeiro 2025
            '%b %d, %Y', # Exemplo: Jan 11, 2025
            '%A, %d %B %Y', # Exemplo: Sábado, 11 Janeiro 2025
            '%H:%M:%S',  # Exemplo: 08:35:00
            '%H:%M',     # Exemplo: 08:35
            '%I:%M %p',  # Exemplo: 08:35 AM
            '%Y-%m-%d %H:%M:%S',  # Exemplo: 2025-01-11 08:35:00
            '%Y-%m-%dT%H:%M:%S',  # Exemplo: 2025-01-11T08:35:00 (Formato ISO 8601)
            '%Y%m%dT%H%M%S',      # Exemplo: 20250111T083500 (Formato compactado)
        )
        #
        # Dicionário de mapeamento de nomes de meses em português para inglês
        self.meses = {
            'Janeiro': 'January',
            'Fevereiro': 'February',
            'Março': 'March',
            'Abril': 'April',
            'Maio': 'May',
            'Junho': 'June',
            'Julho': 'July',
            'Agosto': 'August',
            'Setembro': 'September',
            'Outubro': 'October',
            'Novembro': 'November',
            'Dezembro': 'December',
        }

    def _is_valid_date(self, d:str) -> bool:
        for fmt in self.valid_formats:
            try:
                datetime.strptime(d, fmt)
                return True
            except ValueError:
                pass
        #
        if ',' in d:
            try:
                d = self._ptbr_to_eng(d)
            except:
                pass
            else:
                return True
        if self._is_timestamp(d):
            return True
        return False
    
    def _is_timestamp(self, d:object) -> bool:
        """
            Verifica se o objeto atual é timestamp
        """
        if isinstance(d, Timestamp):
            return True
        return False
    
    def _ptbr_to_eng(self, data_string:str, fmt:str='%A, %d %B %Y') -> str:
        
        # Exemplo de data em string com o dia da semana em português
        data_string = 'Sábado, 11 Janeiro 2025'

        # Remover o dia da semana da string
        new_string_date = data_string.split(", ")[1]

        # Formato da data sem o dia da semana
        current_data_fmt = '%d %B %Y'

        # Substituir o nome do mês em português pelo nome em inglês
        for pt_mes, en_mes in self.meses.items():
            new_string_date = new_string_date.replace(pt_mes, en_mes)

        # Converter a string para um objeto datetime
        to_datetime = datetime.strptime(new_string_date, current_data_fmt)

        # Formatando o objeto datetime para o formato desejado "dia/mês/ANO"
        return to_datetime.strftime(fmt)

    def convert(self, date:str, fmt:str='%d/%m/%Y') -> str:
        """
            Converter uma data em string para um formato qualquer.
        """
        if not self._is_valid_date(date):
            return None
        if ',' in date:
            date = self._ptbr_to_eng(date)
        if self._is_timestamp(date):
            date = datetime.fromtimestamp(date).strftime(fmt)
        
        date_obj:datetime = None
        for f in self.valid_formats:
            try:
                date_obj = datetime.strptime(date, f)
            except:
                pass
            else:
                break
        return date_obj.strftime(fmt)
        
class FormatString(object):
    def __init__(self, value:str):
        self.value = value
        
    def is_null(self) -> bool:
        if (self.value is None) or (self.value == ''):
            return True
        return False

    def to_utf8(self) -> FormatString:
        items_for_remove = [
                        '\xa0T\x04'
                    ]
        try:
            for i in items_for_remove:
                REG = re.compile(i)
                self.value = REG.sub("_", self.value)
        except:
            return self
        else:
            self.value = self.value.encode("utf-8", errors="replace").decode("utf-8")
        return self
    
    def to_upper(self) -> FormatString:
        self.value = self.value.upper()
        return self
    
    def replace_all(self, char:str, new_char:str='_') -> FormatString:
        """
            Usar expressão regular para substituir caracteres.
        """
        # re.sub(r'{}'.format(char), new_char, text)
        self.value = re.sub(re.escape(char), new_char, self.value)
        return self

    def replace_bad_chars(self, *, new_char='-') -> FormatString:
        char_for_remove = [
                            ':', ',', ';', '$', '=', 
                            '!', '}', '{', '(', ')', 
                            '|', '\\', '‘', '*'
                            '¢', '“', '\'', '¢', '"', 
                            '#', '.', '<', '?', '>', 
                            '»', '@', '+', '[', ']',
                            '%', '%', '~', '¥', '«',
                            '°', '¢', '”', '&', 'º',
                ]

        for char in char_for_remove:
            #self.value = self.value.replace(char, new_char)
            self.replace_all(char, new_char)
        # Substituir outros caracteres
        #self.value = re.sub(r'\s+', '_', self.value)
        format_chars = [
            '-_', '_-', '--', '__',
        ]
        for c in format_chars:
            self.replace_all(c)
        return self
    
    
class Array(object):
    def __init__(self, values:list):
        self.values = values

    def for_each(self, cmd:callable):
        for i in self.values:
            cmd(i)

