# -*- coding: utf-8 -*-
"""
Created on Fri Dec 13 12:06:41 2019

@author: admin
"""

import pandas as pd
import os
import matplotlib.pyplot as plt

file_list = []
for file in os.listdir():
    file_list.append(file)
    del(file)


files = {}

for file in file_list:
    files[file] = pd.read_csv(file,sep='¬',encoding='utf-8',engine='python').replace('Â','',regex=True)
    files[file]['Exam'] = file[0:5]
    files[file]['Grade'] = file[-25:-19]
    files[file]['Year'] = file[-18:-14]

df = pd.concat(files)

del file,file_list,files



df_clean = df.loc[:,('MUNI_ID','MUNI_NOMBRE','DEPA_NOMBRE','PUNTAJE_PROMEDIO','Exam','Grade','N')]
df1 = df_clean.pivot_table(index=('MUNI_ID','MUNI_NOMBRE','DEPA_NOMBRE'),columns=('Exam','Grade'),values=('PUNTAJE_PROMEDIO','N'))
df1 = df1.reset_index()

df1['L59'] = df1.iloc[:,11] - df1.iloc[:,10]
df1['L35'] = df1.iloc[:,10] - df1.iloc[:,9]

df1['M59'] = df1.iloc[:,14] - df1.iloc[:,13]
df1['M35'] = df1.iloc[:,13] - df1.iloc[:,12]


df1.columns = ('MUNI_ID','MUNI_NOMBRE','DEPA_NOMBRE','N_L3','N_L5','N_L9', 'N_M3','N_M5','N_M9',
               'Lenguaje Grado 3','Lenguaje Grado 5','Lenguaje Grado 9', 'Matemáticas Grado 3','Matemáticas Grado 5','Matemáticas Grado 9',  
               'Lenguaje 59', 'Lenguaje de 3 a 5', 'Matemáticas de 5 a 9', 'Matemáticas de 3 a 5')
    
df1.to_csv('Saber_359_2017.csv',sep=',',index =False)






















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


