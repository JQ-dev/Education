# -*- coding: utf-8 -*-
"""
Created on Mon Jan 20 12:02:44 2020

@author: admin
"""

import pandas as pd

sasfile = 'C:/Users/admin/Downloads/SAS/pisa.sas7bdat'

df = pd.read_sas(sasfile,
                    chunksize=500,iterator=True)

dfs = [] # holds data chunks

count = 0
for chunk in df:
    count += 1
    dfs.append(chunk)
    if count == 3:
        break
    
df1 = dfs[0]

A = list(df1.columns)