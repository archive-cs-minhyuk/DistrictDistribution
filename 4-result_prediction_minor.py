import geopandas as gpd
import pandas as pd
import numpy as np
import glob
import math
import argparse
import os

#arguments
parser = argparse.ArgumentParser()
parser.add_argument('--adm1', default='Gyeongnam',help='give adm1 level, default = Gyeongnam')
parser.add_argument('--adm2', default="Sacheon-si",help='give adm2 level, default = "Changwon-si')
parser.add_argument('--dir',default='Prediction_minor/',help='directory path for output .csv file')
parser.add_argument('--pop', default=128000, help='population of the city, default = Changwon-si')

args = parser.parse_args()
my_province = args.adm1
my_city = args.adm2
result_dir = args.dir
city_pop = args.pop

if my_province is None:
	print('Please give adm1')
	exit(0)

myf = pd.read_csv('zl15_32645_score_AAXXYY.csv')
myf['clamp_score'] = myf['score'].apply(lambda x: max(-20,x))
myf['clamp_score'] = myf['clamp_score'].apply(lambda x: min(20,x))
min_clamp=min(list(myf['clamp_score']))
max_clamp=max(list(myf['clamp_score']))
myf['minmax_score'] = myf['clamp_score'].apply(lambda x: (x-min_clamp)/(max_clamp-min_clamp))

citycsv = pd.read_csv('./District_info/'+my_province+'/'+my_city+'.csv')
citycsv = citycsv[['gid','lbl','val','geometry']]

areaid_list = []
areapop_list = []
arealbl_list = []
geom_list = []
    
for i in range(len(citycsv)):
    areaid = citycsv.iloc[i]['gid']
    areaid_list.append(areaid)
    
    areapop = citycsv.iloc[i]['val']
    areapop_list.append(areapop)
        
    arealbl = citycsv.iloc[i]['lbl']
    arealbl_list.append(arealbl)
            
    geom = citycsv.iloc[i]['geometry']
    geom = geom[10:-2]
    geom_list.append(geom)

areaid_geom_dict = dict(zip(areaid_list,geom_list))
areaid_pop_dict = dict(zip(areaid_list,areapop_list))
areaid_lbl_dict = dict(zip(areaid_list,arealbl_list))

center_list = []
for areaid in areaid_list:
    city_geom = areaid_geom_dict [areaid]
    tempgeom = city_geom.split(',')
    left_top = tempgeom[1]
    right_bot = tempgeom[3]
    
    center_point = ((float(left_top.split(' ')[1])+float(right_bot.split(' ')[1]))/2, (float(left_top.split(' ')[2])+float(right_bot.split(' ')[2]))/2)
    center_list.append(center_point)
areaid_center_dict = dict(zip(areaid_list,center_list))

corepoints = pd.read_csv('./voronoi_result/'+my_province+'_'+my_city+'.csv')
corepoints = corepoints[['lon','lat']]
corepoints.index = corepoints.index + 1
corepoints['corenum'] = corepoints.index

final_csv = pd.DataFrame(columns=["core_idx",'core_lat','core_lon','grid','pop'],dtype='float')
for grid in areaid_center_dict:
    df_temp = corepoints
    gridlat = areaid_center_dict[grid][1]
    gridlon = areaid_center_dict[grid][0]
    df_temp['lon_diff'] = df_temp['lon'].apply(lambda x : x-gridlon)
    df_temp['lat_diff'] = df_temp['lat'].apply(lambda x : x-gridlat)
    df_temp['distance'] = df_temp['lon_diff']**2 + df_temp['lat_diff']**2
    df_temp = df_temp.sort_values(by='distance')
    df_temp = df_temp.reset_index(drop=True)
    core_idx = df_temp.loc[0,"corenum"]
    core_lat = df_temp.loc[0,"lat"]
    core_lon = df_temp.loc[0,"lon"]
    my_grid = grid
    my_pop = areaid_pop_dict[grid]
    new_data = {'core_idx':core_idx,'core_lat':core_lat,'core_lon':core_lon,'grid':my_grid,'pop':my_pop}
    final_csv = final_csv.append(new_data,ignore_index=True)
final_csv = final_csv.sort_values(by='core_idx')
final_csv = final_csv.reset_index(drop=True)
withscore = pd.merge(myf,final_csv,on='grid')
cores = withscore['core_idx'].tolist()
cores_list = list(set(cores))
coredf = pd.DataFrame(columns=['core','pop','minmax_score'], dtype=object)
for core in cores_list:
    temp = withscore[withscore['core_idx']==core]
    tempsum = temp['minmax_score'].sum()
    popsum = temp['pop'].sum()
    new_data = {'core':[int(core)],'pop':[popsum], 'minmax_score':[tempsum]}
    new_df = pd.DataFrame(new_data)
    coredf= pd.concat([coredf,new_df])
coredf = coredf.sort_values(by='minmax_score',ascending=False)
coredf = coredf.reset_index(drop=True)
coredf.index = coredf.index + 1

myk = -1.2625
coredf['rank']=coredf.index
coredf['rankss']=coredf['rank']**myk
totalpop = city_pop
myc = totalpop/sum(coredf['rankss'])
coredf['predicted'] = myc * coredf['rankss']
coredf['predicted'] = coredf['predicted'].apply(round)
coredffinal = coredf[['core','predicted','pop']]
mycorr = round(coredffinal.corr(method='spearman')['predicted']['pop'],4)
print(mycorr)

if not os.path.isdir(result_dir):
	os.mkdir(result_dir)
coredffinal.to_csv(result_dir+my_province+'_'+my_city+".csv",mode='w')
