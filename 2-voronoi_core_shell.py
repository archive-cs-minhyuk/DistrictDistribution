import subprocess
import pandas as pd

df = pd.read_csv('zl15_32645_noclamp_score.csv')
major_cities = ['Busan','Daegu','Daejeon','Gwangju','Incheon','Sejong','Seoul','Ulsan']
zl=15

df_minors = df[~df.adm1.isin(major_cities)]
#column_vals= df_minors[['adm1','adm2']].values.ravel()
column_vals= df_minors[['adm1','adm2']].values.ravel()
unique_vals_list= list(pd.unique(column_vals))

column_vals_adm1 = df_minors[['adm1']].values.ravel()
unique_vals_adm1= pd.unique(column_vals_adm1)
provinces = list(unique_vals_adm1)

unique_adm12 = []
curr_prov = ''
while(len(unique_vals_list)>0):
	curr_pointer = unique_vals_list.pop(0)
	if curr_pointer in provinces:
		curr_prov=curr_pointer
		continue
	unique_adm12.append([curr_prov,curr_pointer])
for adm1 in major_cities:
	unique_adm12.append([adm1,'None'])
#print(unique_adm12)

for adm12 in unique_adm12:
	adm1 = str(adm12[0])
	adm2 = str(adm12[1])
	query = ['python3','extract_core.py','--zl',str(zl),'--adm1',adm1,'--adm2',adm2]
	print(query)
	subprocess.run(query)