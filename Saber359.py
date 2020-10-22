# -*- coding: utf-8 -*-
"""
Created on Sat Dec 14 13:06:12 2019

@author: admin
"""
import pandas as pd

saber359 = pd.read_csv('SABER359_2017.csv',sep=',',encoding='utf-8',engine='python')







list(saber359.columns)

keep =[  'COLE_COD_DANE_ESTABLECIMIENTO',
         'COLE_NOMBRE_ESTABLECIMIENTO',
         'COLE_GENERO',
         'COLE_NATURALEZA',
         'COLE_CARACTER',
         'COLE_AREA_UBICACION',
         'COLE_COD_MCPIO_UBICACION']

Cole_list1 = saber359.loc[:,keep].drop_duplicates('COLE_COD_DANE_ESTABLECIMIENTO')


keep =[  'COLE_COD_MCPIO_UBICACION',
         'COLE_MCPIO_UBICACION',
         'COLE_COD_DEPTO_UBICACION',
         'COLE_DEPTO_UBICACION']

Muni_list = saber359.loc[:,keep].drop_duplicates()


keep =['PERIODO',
'COLE_COD_MCPIO_UBICACION',
'PUNT_LENGUAJE',
'PUNT_MATEMATICAS',
'ESTU_GRADO',]


df_359M = saber359.loc[:,keep]



keep =[ 'PERIODO',
       'COLE_NOMBRE_ESTABLECIMIENTO',
        'COLE_COD_DANE_ESTABLECIMIENTO',
        'PUNT_LENGUAJE',
        'PUNT_MATEMATICAS',
        'ESTU_GRADO']

df_359C = saber359.loc[:,keep]


del saber359

XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

df_359C = df_359C.replace(100,np.nan)
df_359M = df_359M.replace(100,np.nan)


aggregation = { 'PERIODO':'count',
                'PUNT_LENGUAJE':'mean',
                'PUNT_MATEMATICAS':'mean' }


df_359_Colegios = df_359C.groupby(['COLE_COD_DANE_ESTABLECIMIENTO','ESTU_GRADO']).agg(aggregation)
df_359_Colegios = df_359_Colegios.reset_index()


df_359_Colegios.columns = ('CODIGO','Grado','N','Lenguaje','Matemáticas')


aggregation = { 'PERIODO':'count',
                'PUNT_LENGUAJE':'mean',
                'PUNT_MATEMATICAS':'mean' }


df_359_Municipios = df_359M.groupby(['COLE_COD_MCPIO_UBICACION','ESTU_GRADO']).agg(aggregation)
df_359_Municipios = df_359_Municipios.reset_index()



df_359_Municipios.columns = ('MUNI_ID','Grado','N','Lenguaje','Matemáticas')


del  df_359M, df_359C










