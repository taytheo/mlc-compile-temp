#!/usr/bin/env python3
import importlib
try:
    m = importlib.import_module('mlc_llm')
    print('installed mlc_llm file:', getattr(m, '__file__', 'unknown'))
except Exception as e:
    print('mlc_llm import failed after pip install:', e)
