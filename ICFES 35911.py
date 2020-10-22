# -*- coding: utf-8 -*-
"""
Created on Sat Dec 14 14:42:04 2019

@author: admin
"""

import pandas as pd
import numpy as np

df_11_Colegios.columns = ('CODIGO','N','Lenguaje','Matemáticas','Grado')
df_359_Colegios.columns = ('CODIGO','Grado','N','Lenguaje','Matemáticas')

df_Colegios = pd.concat([df_359_Colegios,df_11_Colegios])



Colegios = df_Colegios.pivot_table(index=('CODIGO'),
                                       columns=('Grado'),
                                       values=('Lenguaje','Matemáticas','N'))


Colegios = Colegios.reset_index()
       
Colegios.columns = ('CODIGO',
                      'Lenguaje Grado 3','Lenguaje Grado 5','Lenguaje Grado 9','Lenguaje Grado 11',
                      'Matemáticas Grado 3','Matemáticas Grado 5','Matemáticas Grado 9','Matemáticas Grado 11',
                      'N 3','N 5','N 9','N 11')


measures = ['Lenguaje Grado 3','Lenguaje Grado 5','Lenguaje Grado 9','Lenguaje Grado 11',
            'Matemáticas Grado 3','Matemáticas Grado 5','Matemáticas Grado 9','Matemáticas Grado 11']

Colegios.loc[:,measures].median()
Colegios.loc[:,measures].mean()
Colegios.loc[:,measures].std()
Colegios.loc[:,measures].max()
Colegios.loc[:,measures].min()


Colegios.loc[:,measures] = (Colegios.loc[:,measures] - Colegios.loc[:,measures].mean())/Colegios.loc[:,measures].std()


Colegios.loc[:,'Lenguaje Grado 3'] = Colegios.loc[:,'Lenguaje Grado 3'].apply( lambda x: max ( min(x,3.5),-3.5) ) 
Colegios.loc[:,'Lenguaje Grado 5'] = Colegios.loc[:,'Lenguaje Grado 5'].apply( lambda x: max ( min(x,3.5),-3.5) ) 
Colegios.loc[:,'Lenguaje Grado 9'] = Colegios.loc[:,'Lenguaje Grado 9'].apply( lambda x: max ( min(x,3.5),-3.5) ) 
Colegios.loc[:,'Lenguaje Grado 11'] = Colegios.loc[:,'Lenguaje Grado 11'].apply( lambda x: max ( min(x,3.5),-3.5) ) 

Colegios.loc[:,'Matemáticas Grado 3'] = Colegios.loc[:,'Matemáticas Grado 3'].apply( lambda x: max ( min(x,3.5),-3.5) ) 
Colegios.loc[:,'Matemáticas Grado 5'] = Colegios.loc[:,'Matemáticas Grado 5'].apply( lambda x: max ( min(x,3.5),-3.5) ) 
Colegios.loc[:,'Matemáticas Grado 9'] = Colegios.loc[:,'Matemáticas Grado 9'].apply( lambda x: max ( min(x,3.5),-3.5) ) 
Colegios.loc[:,'Matemáticas Grado 11'] = Colegios.loc[:,'Matemáticas Grado 11'].apply( lambda x: max ( min(x,3.5),-3.5) ) 






df_Municipios = pd.concat([df_359_Municipios,df_11_Municipios])

Municipios = df_Municipios.pivot_table(index=('MUNI_ID'),
                                       columns=('Grado'),
                                       values=('Lenguaje','Matemáticas','N'))

Municipios = Municipios.reset_index()

Municipios.columns = ('MUNI_ID',
                      'Lenguaje Grado 3','Lenguaje Grado 5','Lenguaje Grado 9','Lenguaje Grado 11',
                      'Matemáticas Grado 3','Matemáticas Grado 5','Matemáticas Grado 9','Matemáticas Grado 11',
                      'N 3','N 5','N 9','N 11')


del df_Municipios, df_359_Municipios, df_11_Municipios, df_Colegios , df_359_Colegios, df_11_Colegios

measures = ['Lenguaje Grado 3','Lenguaje Grado 5','Lenguaje Grado 9','Lenguaje Grado 11',
            'Matemáticas Grado 3','Matemáticas Grado 5','Matemáticas Grado 9','Matemáticas Grado 11']


Municipios.loc[:,measures].mean()
Municipios.loc[:,measures].std()
Municipios.loc[:,measures].min()
Municipios.loc[:,measures].max()

Municipios.loc[:,measures] = (Municipios.loc[:,measures] - Municipios.loc[:,measures].mean())/Municipios.loc[:,measures].std()


Municipios.loc[:,'Lenguaje Grado 3'] = Municipios.loc[:,'Lenguaje Grado 3'].apply( lambda x: max ( min(x,3.5),-3.5) ) 
Municipios.loc[:,'Lenguaje Grado 5'] = Municipios.loc[:,'Lenguaje Grado 5'].apply( lambda x: max ( min(x,3.5),-3.5) ) 
Municipios.loc[:,'Lenguaje Grado 9'] = Municipios.loc[:,'Lenguaje Grado 9'].apply( lambda x: max ( min(x,3.5),-3.5) ) 
Municipios.loc[:,'Lenguaje Grado 11'] = Municipios.loc[:,'Lenguaje Grado 11'].apply( lambda x: max ( min(x,3.5),-3.5) ) 

Municipios.loc[:,'Matemáticas Grado 3'] = Municipios.loc[:,'Matemáticas Grado 3'].apply( lambda x: max ( min(x,3.5),-3.5) ) 
Municipios.loc[:,'Matemáticas Grado 5'] = Municipios.loc[:,'Matemáticas Grado 5'].apply( lambda x: max ( min(x,3.5),-3.5) ) 
Municipios.loc[:,'Matemáticas Grado 9'] = Municipios.loc[:,'Matemáticas Grado 9'].apply( lambda x: max ( min(x,3.5),-3.5) ) 
Municipios.loc[:,'Matemáticas Grado 11'] = Municipios.loc[:,'Matemáticas Grado 11'].apply( lambda x: max ( min(x,3.5),-3.5) ) 



#cond = (Municipios.loc[:,measures] < 2.33)
#Municipios.loc[:,measures] = Municipios.loc[:,measures].where(cond,2.33)
#
#cond = (Municipios.loc[:,measures] > -2.33)
#Municipios.loc[:,measures] = Municipios.loc[:,measures].where(cond,-2.33)



Municipios.to_csv('Municipios3.csv',sep=',',index =False)
Muni_list.to_csv('Muni_list3.csv',sep=',',index =False)
Municipios.to_csv('Colegios3.csv',sep=',',index =False)


Cole_list = pd.concat([Cole_list1,Cole_list2]).drop_duplicates()
Cole_list.to_csv('Cole_list3.csv',sep=',',index =False)


