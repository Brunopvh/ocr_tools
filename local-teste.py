#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import re
import pandas
from pandas import DataFrame
from typing import List, Dict
from io import BytesIO

from libconvert import *
from libconvert.common import get_path_tesseract_system

def main():
    text = 'RUBRICA E MATRICULA DO DESTINATARIO- DANIELA PEREIRA DA SILVA ENTREGADOR UC- 1396768 TOI- 152211439'
    idx = text.find('UC')
    print(idx)
    text = text[idx:-1]
    print(text)

    
main()