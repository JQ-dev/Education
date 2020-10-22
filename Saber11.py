# -*- coding: utf-8 -*-
"""
Created on Sat Dec 14 13:06:12 2019

@author: admin
"""
import pandas as pd
import numpy as np

saber11_1 = pd.read_csv('Saber_11__2017-1.csv',sep=',',encoding='utf-8',engine='python')
saber11_2 = pd.read_csv('Saber_11__2017-2.csv',sep=',',encoding='utf-8',engine='python')


saber11 = pd.concat([saber11_1,saber11_2])

del saber11_1,saber11_2

list(saber11.columns)

keep =[  'cole_cod_dane_establecimiento',
         'cole_nombre_establecimiento',
         'cole_genero',
         'cole_naturaleza',
         'cole_caracter',
         'cole_area_ubicacion',
         'cole_cod_mcpio_ubicacion']

Cole_list2 = saber11.loc[:,keep].drop_duplicates()

Cole_list2.columns = ('COLE_COD_DANE_ESTABLECIMIENTO','COLE_NOMBRE_ESTABLECIMIENTO',
                     'COLE_GENERO','COLE_NATURALEZA','COLE_CARACTER',
                     'COLE_AREA_UBICACION','COLE_COD_MCPIO_UBICACION')










keep =[ 'periodo',
        'cole_cod_dane_establecimiento',
        'punt_lectura_critica',
        'punt_matematicas']


df_11C = saber11.loc[:,keep]

keep =[ 'periodo',
        'cole_cod_mcpio_ubicacion',
        'punt_lectura_critica',
        'punt_matematicas']

df_11M = saber11.loc[:,keep]


del saber11, keep

XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXxx


df_11C = df_11C.replace(0,np.nan)
df_11M = df_11M.replace(0,np.nan)


aggregation = { 'periodo':'count',
                'punt_lectura_critica':'mean',
                'punt_matematicas':'mean'   }


df_11_Colegios = df_11C.groupby(['cole_cod_dane_establecimiento']).agg(aggregation)
df_11_Colegios = df_11_Colegios.reset_index()

df_11_Colegios.loc[:,('punt_lectura_critica','punt_matematicas')] = df_11_Colegios.loc[:,('punt_lectura_critica','punt_matematicas')]*5

df_11_Colegios['Grado'] = 11

df_11_Colegios.columns = ('CODIGO','N','Lenguaje','Matemáticas', 'Grado')




aggregation = { 'periodo':'count',
                'punt_lectura_critica':'mean',
                'punt_matematicas':'mean'}

df_11_Municipios = df_11M.groupby(['cole_cod_mcpio_ubicacion']).agg(aggregation)
df_11_Municipios = df_11_Municipios.reset_index()


df_11_Municipios.loc[:,('punt_lectura_critica','punt_matematicas')] = df_11_Municipios.loc[:,('punt_lectura_critica','punt_matematicas')]*5

df_11_Municipios['Grado'] = 11


df_11_Municipios.columns = ('MUNI_ID','N','Lenguaje','Matemáticas','Grado')




del  df_11M, df_11C






