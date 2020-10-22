# -*- coding: utf-8 -*-
"""
Created on Fri Dec 13 12:06:41 2019

@author: admin
"""

import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np

file_list = []
for file in os.listdir():
    file_list.append(file)
    del(file)


files = {}

for file in file_list:
    if '2017.txt' in file :
        files[file] = pd.read_csv(file,sep='¬',encoding='utf-8',engine='python')
        files[file]['Exam'] = file[0:3]
        files[file]['Grade'] = file[4]
        files[file]['Year'] = file[6:10]

df = pd.concat(files)
df = df.reset_index()


del file,file_list,files



df_clean = df.loc[:,('COD_DANE','PROMEDIO','Exam','Grade','EVALUADOS')]
df_clean.columns = ('CODIGO','PROMEDIO','Exam','Grado','N')

df1 = df_clean.pivot_table(index=('CODIGO','Grado'),columns=('Exam'),values=('PROMEDIO','N'))
df1 = df1.reset_index()
df1.columns = ('CODIGO','Grado','N','NM','Lenguaje','Matemáticas')
df1 = df1.drop('NM',axis=1)


df1.columns = ('COD_DANE','N_L3','N_L5','N_L9', 'N_M3','N_M5','N_M9',
               'Lenguaje Grado 3','Lenguaje Grado 5','Lenguaje Grado 9', 
               'Matemáticas Grado 3','Matemáticas Grado 5','Matemáticas Grado 9')

df_359_Colegios = df1.copy()


dane = pd.read_csv('INFO COLEGIOS.csv',sep=';')
list(dane.columns)
dane_clean = dane.loc[:,('COD_DANE','PROMEDIO','Exam','Grade','EVALUADOS')]


[' Departamento',
 ' Municipio',
 ' Código',
 ' Nombre',
 ' Tipo Establecimiento',
 ' Sector',
 ' Zona',
 ' Cal',]
    
df1.to_csv('Colegios_Saber_359_2017.csv',sep=',',index =False)




















df_clean = df.loc[:,('MUNI_ID','MUNI_NOMBRE','DEPA_NOMBRE','PUNTAJE_PROMEDIO','Exam','Grade')]
df2 = df_clean.pivot_table(index=('MUNI_ID','MUNI_NOMBRE','DEPA_NOMBRE'),columns=('Exam','Grade'),values='PUNTAJE_PROMEDIO')
df2 = df2.reset_index()


# plot the data
fig = plt.figure(figsize=(14,8))

for n in range(100):
    x = df2.loc[n,('Lengu')]
    y = df2.loc[n,('Matem')]
    plt.scatter(x,y,c=(3,6,9))
    plt.plot(x,y)
    
plt.show()








df3 = df.loc[:,('MUNI_ID','MUNI_NOMBRE','DEPA_NOMBRE','PUNTAJE_PROMEDIO','Exam','Grade')]
df3 = df3.loc[ df3.loc[:,'Grade'] != 'Grado9' , :]
df3 = df3.pivot_table(index=('MUNI_ID','MUNI_NOMBRE','DEPA_NOMBRE'),columns=('Exam','Grade'),values='PUNTAJE_PROMEDIO')
df3 = df3.reset_index()



# plot the data
fig = plt.figure(figsize=(14,8))

for n in range(100):
    x = df3.loc[n,('Lengu')]
    y = df3.loc[n,('Matem')]
    plt.scatter(x,y,c=(3,6))
    plt.plot(x,y)
    
plt.show()


df4 = df.loc[:,('MUNI_ID','MUNI_NOMBRE','DEPA_NOMBRE','PUNTAJE_PROMEDIO','Exam','Grade')]
df4 = df4.loc[ df4.loc[:,'Grade'] != 'Grado3' , :]
df4 = df4.pivot_table(index=('MUNI_ID','MUNI_NOMBRE','DEPA_NOMBRE'),columns=('Exam','Grade'),values='PUNTAJE_PROMEDIO')
df4 = df4.reset_index()


# plot the data
fig = plt.figure(figsize=(14,8))

for n in range(3):
    x = df4.loc[n,('Lengu')]
    y = df4.loc[n,('Matem')]
    plt.scatter(x,y,c=(0.6,0.9))
    plt.plot(x,y)

plt.ylabel("Matematicas")
plt.xlabel("Lenguage")  
plt.show()







plt.plot(x, x, label='linear')






ax = fig.add_subplot(1, 1, 1)
ax.plot(g3x, g3y, color='tab:blue')
ax.plot(g5x, g5y, color='tab:orange')

# create the events marking the x data points
xevents1 = EventCollection(g3x, color='tab:blue', linelength=0.05)
xevents2 = EventCollection(g5x, color='tab:orange', linelength=0.05)

# create the events marking the y data points
yevents1 = EventCollection(g3y, color='tab:blue', linelength=0.05,
                           orientation='vertical')
yevents2 = EventCollection(g5y, color='tab:orange', linelength=0.05,
                           orientation='vertical')

# add the events to the axis
ax.add_collection(xevents1)
ax.add_collection(xevents2)
ax.add_collection(yevents1)
ax.add_collection(yevents2)

# set the limits
#ax.set_xlim([0, 1])
#ax.set_ylim([0, 1])

ax.set_title('line plot with data points')

# display the plot
plt.show()


