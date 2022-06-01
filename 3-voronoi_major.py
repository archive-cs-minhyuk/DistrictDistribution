from sklearn.linear_model import LinearRegression
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import math
import argparse
import os

#arguments
parser = argparse.ArgumentParser()
parser.add_argument('--adm1', default='Busan',help='give adm1 level, default = Busan')
parser.add_argument('--dir',default='Alphas_major/',help='directory path for output .csv file')

args = parser.parse_args()
my_district = args.adm1
result_dir = args.dir

if my_district is None:
	print('Please give adm1')
	exit(0)

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
#areaid + pop dictionary (areaid_pop_dict)
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
#areaid + center point dictionary
areaid_center_dict = dict(zip(areaid_list,center_list))

corepoints = pd.read_csv('./voronoi_result/'+my_district+'_None.csv')
corepoints = corepoints[['lon','lat']]
corepoints.index = corepoints.index + 1
corepoints['corenum'] = corepoints.index

#final_csv: informations about each grid's core_idx
#This is the part where actual voronoi is performed!
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

#coredf: informations about core num - population for each core
final_csv = final_csv.fillna(0)
cores = final_csv['core_idx'].tolist()
cores_list = list(set(cores))
coredf = pd.DataFrame(columns=['core','pop'], dtype=object)
for core in cores_list:
    temp = final_csv[final_csv['core_idx']==core]
    tempsum = temp['pop'].sum()
    new_data = {'core':[int(core)], 'pop':[tempsum]}
    new_df = pd.DataFrame(new_data)
    coredf= pd.concat([coredf,new_df])
coredf = coredf.sort_values(by='pop',ascending=False)
coredf = coredf.reset_index(drop=True)
coredf.index = coredf.index + 1

#calculating alphas
def give_me_figures(dataset):
    fig = plt.figure()
    fig.subplots_adjust(hspace=0.2, wspace=0.4)

    x=dataset.index
    y=dataset['pop']

    lny = []
    for i in range(1,len(y)+1):
        lny.append(math.log1p(y[i]))
    lny = pd.DataFrame(lny)
    lnx = []
    for i in range(0,len(x)):
        lnx.append(math.log(x[i]))
    lnx = pd.DataFrame(lnx)

    plt.subplot(2, 2, 1)
    ax = sns.scatterplot(np.squeeze(lnx.values.tolist(),axis=1),np.squeeze(lny.values.tolist(),axis=1), color='tomato')
    line_fitter = LinearRegression(fit_intercept=True)
    line_fitter.fit((lnx).values.reshape(-1,1),lny)
    mya = line_fitter.coef_
    myb = line_fitter.intercept_
    myalpha = -1/mya[0][0]
    print("first")
    print(myalpha)
    plt.plot(np.squeeze(lnx.values.tolist(),axis=1),mya*lnx.values.reshape(-1,1) + myb)
    first_y = np.squeeze(lny.to_numpy(),axis=1)
    first_pred = np.squeeze(mya*lnx.values.reshape(-1,1) + myb)
    ax.set_title("lns = b - 1/alpha * lnr", size = 11, fontweight='bold')
    ax.set_xlabel("Ranking", size = 8)
    ax.set_ylabel("Population", size = 8)

    plt.subplot(2, 2, 2)
    ax = sns.scatterplot(x, y, color='tomato')
    line_fitter_2 = LinearRegression(fit_intercept=True)
    line_fitter_2.fit(x.values.reshape(-1,1),y)
    mya_2 = line_fitter_2.coef_
    myb_2 = line_fitter_2.intercept_
    myalpha_2 = -1/mya_2[0]
    print("second")
    print(mya_2[0])
    plt.plot(x,mya_2*(x.values.reshape(-1,1))+myb_2)
    ax.set_xlabel("Ranking", size = 8)
    ax.set_ylabel("Population", size = 8)
    
    plt.subplot(2,2,3)
    ax = sns.scatterplot(x, np.squeeze(lny.values.tolist(),axis=1), color='tomato')
    line_fitter_3 = LinearRegression(fit_intercept=True)
    line_fitter_3.fit(x.values.reshape(-1,1),lny)
    mya_3 = line_fitter_3.coef_
    myb_3 = line_fitter_3.intercept_
    myalpha_3 = -1/mya_3[0]
    print("third")
    print(mya_3[0][0])
    print(myb_3)
    plt.plot(x,mya_3*(x.values.reshape(-1,1))+myb_3)
    ax.set_xlabel("Ranking", size = 8)
    ax.set_ylabel("ln(Population)", size = 8)

    fig.set_figheight(8)
    fig.set_figwidth(9)
    return (myalpha, mya_2[0], mya_3[0][0])

mpoplist = coredf['pop'].tolist()
mindexlist = coredf.index.tolist()
myilist = mindexlist[:-2]

def MSE(y,pred) :
    return np.mean(np.square(y-pred))

def give_me_MSE(xlist, ylist):
    if len(xlist)<=2:
        return 0
    line_fitter = LinearRegression()
    xlist = np.array(xlist)
    line_fitter.fit(xlist.reshape(-1,1),ylist)
    mya = line_fitter.coef_
    myb = line_fitter.intercept_

    first_y = np.array(ylist)
    first_pred = np.squeeze(mya*(xlist.reshape(-1,1))+myb,axis=1)
    return MSE(first_y,first_pred)
    
anslist = []
for i in mindexlist:
    if i == len(mindexlist):
        continue
    yheadlist = list(map(math.log1p,mpoplist[1:i]))
    xheadlist = list(mindexlist[1:i])
    ytaillist = list(map(math.log1p,mpoplist[i:-1]))
    xtaillist = list(mindexlist[i:-1])
    anslist.append(give_me_MSE(xheadlist,yheadlist) + give_me_MSE(xtaillist,ytaillist))
chp =anslist.index(min(anslist))
criteria = chp
living_grids = coredf.loc[:criteria]

before_split = give_me_figures(coredf)
after_split = give_me_figures(living_grids)

alphas = pd.DataFrame(columns=["major","log_before",'notlog_before','log_after','notlog_after'],dtype='float')
new_alphaset = {"major":my_district,'log_before':before_split[0],'notlog_before':before_split[1],'log_after':after_split[0],'notlog_after':after_split[1]}
alphas = alphas.append(new_alphaset,ignore_index = True)
if not os.path.isdir(result_dir):
	os.mkdir(result_dir)
alphas.to_csv(result_dir+my_district+'_'+'None'+".csv",mode='w')
