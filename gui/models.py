#!/usr/bin/env python3
#
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Dict
from pathlib import Path

import pandas
from pandas import DataFrame

from libconvert import (
    File,
    Directory
)