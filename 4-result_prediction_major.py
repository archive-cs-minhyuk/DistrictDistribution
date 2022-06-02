import geopandas as gpd
import pandas as pd
import numpy as np
import glob
import math
import argparse
import os

#arguments
parser = argparse.ArgumentParser()
parser.add_argument('--adm1', default='Busan',help='give adm1 level, default = Busan')
parser.add_argument('--dir',default='Prediction_major/',help='directory path for output .csv file')
parser.add_argument('--pop', default=3420000 , help='population of the city, default = Busan')

args = parser.parse_args()
my_district = args.adm1
result_dir = args.dir
city_pop = args.pop

if my_district is None:
	print('Please give adm1')
	exit(0)

myf = pd.read_csv('zl15_32645_score_AAXXYY.csv')
myf['clamp_score'] = myf['score'].apply(lambda x: max(-20,x))
myf['clamp_score'] = myf['clamp_score'].apply(lambda x: min(20,x))
min_clamp=min(list(myf['clamp_score']))
max_clamp=max(list(myf['clamp_score']))
myf['minmax_score'] = myf['clamp_score'].apply(lambda x: (x-min_clamp)/(max_clamp-min_clamp))

path_shp = './Raw/'+my_district+'/nlsp_020001001.shp'
encoding = 'utf-8'
popfile=gpd.read_file(path_shp,encoding=encoding).to_crs({'init':'epsg:4326'})

areaid_list = []
areapop_list = []
arealbl_list = []
geom_list = []
    
for i in range(len(popfile)):
    areaid = popfile.iloc[i]['gid']
    areaid_list.append(areaid)
        
    areapop = popfile.iloc[i]['val']
    areapop_list.append(areapop)
        
    arealbl = popfile.iloc[i]['lbl']
    arealbl_list.append(arealbl)
        
    geom = popfile.iloc[i]['geometry']
    try:
        #when multipolygon
        multipoly_list = list(geom)
        geom_list.append(multipoly_list)
    except:
        #when polygon
        geom_list.append(geom)
    
new_areaid_list = []
KOR = '가나다라마바사아자차카타파하'
ENG = 'ABCDEFGHIJKLMN'
for myid in areaid_list:
    toEng = myid.translate(myid.maketrans(KOR,ENG))
    new_areaid_list.append(toEng)
areaid_list = new_areaid_list
areaid_geom_dict = dict(zip(areaid_list,geom_list))
areaid_pop_dict = dict(zip(areaid_list,areapop_list))
areaid_lbl_dict = dict(zip(areaid_list,arealbl_list))

center_list = []
for areaid in areaid_list:
    city_geom = areaid_geom_dict [areaid]
    polygon = list(zip(*city_geom.exterior.coords.xy))[:-1]
    left_top = polygon[1]
    right_bot = polygon[3]
    
    center_point = ((left_top[0]+right_bot[0])/2, (left_top[1]+right_bot[1])/2)
    center_list.append(center_point)
areaid_center_dict = dict(zip(areaid_list,center_list))

corepoints = pd.read_csv('./voronoi_result/'+my_district+'_None.csv')
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

myk = -0.0851
coredf['rank']=coredf.index
coredf['rankss']=coredf['rank']*myk
coredf['rankss']=math.e**coredf['rankss']
totalpop = city_pop
myc = totalpop/sum(coredf['rankss'])
coredf['predicted'] = myc * coredf['rankss']
coredf['predicted'] = coredf['predicted'].apply(round)
coredffinal = coredf[['core','predicted','pop']]

if not os.path.isdir(result_dir):
	os.mkdir(result_dir)
coredffinal.to_csv(result_dir+my_district+'_'+'None'+".csv",mode='w')
