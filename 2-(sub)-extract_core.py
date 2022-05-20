import csv
import itertools
import os
import math
import numpy as np
import pandas as pd
import plotly.express as px
import argparse


#Functions
def calculate_gradient(df,x):
    yxstring = str(x).split('_')
    yxint = list(map(int, yxstring))
    
    north = str(yxint[0]+1) + '_' + str(yxint[1])
    east = str(yxint[0]) + '_' + str(yxint[1]+1) 
    south = str(yxint[0]-1) + '_' + str(yxint[1])
    west = str(yxint[0]) + '_' + str(yxint[1]-1)
    needed_yx = [north,east,south,west]
    
    myscore = df[df['y_x'] == x].iloc[0,3]
    total = 0
    cnt = 0
    direction = 4
    for yx in needed_yx:
        try:
            wantscore = df[df['y_x'] == yx].iloc[0,3]
            cnt = cnt + 1
            tempdir = myscore - wantscore
            if tempdir <= 0 :
                direction = direction - 1
                continue
            total = total + tempdir
        except:
            continue
    if cnt == 0:
        return -20
    if direction < 4 :
        return -20
    if direction == 4:
        return 17
    return total/cnt  

#Generate_new_cores
def voronoi_cores(y_x, init_cores, answerlist):
    answerlist.append(y_x)
    y_x = y_x.split('_')
    y_x = list(map(int, y_x))
  
    ne = str(y_x[0]+1) + '_' + str(y_x[1]+1)
    nw = str(y_x[0]+1) + '_' + str(y_x[1]-1) 
    se = str(y_x[0]-1) + '_' + str(y_x[1]+1)
    sw = str(y_x[0]-1) + '_' + str(y_x[1]-1)
    possible_list = [ne,nw,se,sw]
    loopanswers = []
    for elem in possible_list:
        if elem in init_cores and (elem not in answerlist): #core point
            tempans = voronoi_cores(elem,init_cores,answerlist)
            loopanswers = loopanswers + tempans
    loopanswers = list(set(loopanswers))
    answerlist = list(set(answerlist+loopanswers))
    return answerlist

def final_cores(given_adm1, given_adm2,df,zl):
	target_df = df[df['adm1']==given_adm1]
	if given_adm2 is not None:
		target_df = target_df[target_df['adm2']==given_adm2]
	#pre-processing
	target_df['score'] = target_df['score'].apply(lambda v: max(v,-10))
	target_df['gradient'] = target_df['y_x'].apply(lambda x: calculate_gradient(target_df,x))
	#basics(원래의 코어 point) 중 인접한 점들 합치는 과정
	cores = target_df[target_df['gradient']==17]
	cores = cores.reset_index(drop=True)
	cores.index = cores.index +1
	initial_cores = list(cores['y_x'])

	finalcores = pd.DataFrame()
	while(len(initial_cores)!=0):
		core1 = initial_cores[0]
		core1_list = voronoi_cores(core1,initial_cores,[])
		initial_cores = [x for x in initial_cores if x not in core1_list] #한번 확인한 core는 제거

		tempx = list(map(lambda yx : int(yx.split('_')[1]),core1_list))
		tempy = list(map(lambda yx : int(yx.split('_')[0]),core1_list))
		core_y = np.mean(tempy)
		core_x = np.mean(tempx)
		n = 2**zl
		newcoreyx = str(core_y)+'_'+str(core_x)
		core_lon = float(core_x) / n * 360.0 - 180.0
		core_lat = math.atan(math.sinh(math.pi * (1-2*float(core_y) / n)))*180/math.pi
		new_data = {'y':np.mean(tempy),'x':np.mean(tempx), 'y_x':newcoreyx, 'lon':core_lon, 'lat':core_lat,'adm1':given_adm1, 'adm2':given_adm2, 'num_cores':len(core1_list)}
		finalcores = finalcores.append(new_data,ignore_index=True)

	return finalcores

df = pd.read_csv('zl15_32645_noclamp_score.csv')
MAPBOX_ACCESS_TOKEN = 'pk.eyJ1Ijoia2VsdHBvd2VyMCIsImEiOiJjazFiZ3cxZzUwMjVhM2hyMTBvcHYwcHlxIn0.mZTYvOHmJeqBANdFC1HFkw' #@param {type:"string"}

#arguments
parser = argparse.ArgumentParser()
parser.add_argument('--zl', default=15,help='zoom')
parser.add_argument('--adm1', default='Busan',help='give adm1 level, default = Busan')
parser.add_argument('--adm2', default=None, help ='give adm2 level, default = None')
parser.add_argument('--dir',default='voronoi_result/',help='directory path for output .csv file')

args = parser.parse_args()
given_adm1 = args.adm1
given_adm2 = args.adm2
if given_adm2=='None':
    given_adm2 = None
zl = int(args.zl)
result_dir = args.dir

if given_adm1 is None:
	print('Please give adm1')
	exit(0)

voronoi_result = final_cores(given_adm1,given_adm2,df,zl)

if not os.path.isdir(result_dir):
	os.mkdir(result_dir)
voronoi_result.to_csv(result_dir+given_adm1+'_'+args.adm2+'.csv',index=False)