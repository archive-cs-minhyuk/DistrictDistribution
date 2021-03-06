# Distributing internal economic level of districts using satellite imagery and power-laws for cities (KCC 2022)

Pytorch Implementation of Distributing internal economic level of districts using satellite imagery and power-laws for cities

<img src="fig/voronoi2.PNG" alt="voronoi" width="500"/>

  * Our model consists of 3 parts, which are introduced below.
  * Step 1. We measure the hyperlocal economic scores of each grids by inferring the relative degree of individual grid image's economic development via ordinal regression.
  * Step 2. We get the core points of the districts using gradient descent, and make Voronoi cells using the points.
  * Step 3. After choosing appropriate distribution for the district, we distribute the economic statistics using the distribution. For alpha in the distribution formula, we pre-calculated the average alpha values of districts by using the existing ground-truth data.

### Step 1. Measuring hyperlocal score
<hr/>

Calculating hyperlocal scores using ordinal regression model
```
usage: 1-Calculating hyperlocal scores.py [-h] [--model MODEL] [--thr1 THR1] [--thr2 THR2]
                                          [--path PATH] [--csv_name CSV]
```  
  
  

**Measuring hyperlocal score Example**
```
python3 1-Calculating hyperlocal scores.py --model ./model/proxy_ordinal.ckpt --csv_name zl15_32645_score_AAXXYY.csv
```

### Step 2-A. Extracting Core points
<hr/>

Extracting core points of districts using gradient descent
```
usage: 2-voronoi_core_shell.py
```  
Basically, running the above code will do all the works for you by surfing all the major/minor districts in Korea(under the assumption you have preliminary files. For preliminary files, check the code for detailed understandings). But in case you want to extract core points of a single district, you can use the below code for that.

Extracting core points of **single** district
```
usage: 2-(sub)-extract_core.py [-h] [--zl ZOOM LEVEL] [--adm1 PROVINCE] [--adm2 CITY]
                                          [--dir PATH FOR OUTPUT] 
```  


**Extracting core points Example**
```
python3 2-(sub)-extract_core.py --zl 15 --adm1 Chungbuk --adm2 Chungju-si --dir voronoi_result/
```



### Step 2-B. Performing Voronoi split + Calculating alpha values
<hr/>

This part of the code includes not only performing voronoi split of district with core points we got as a criteria, but also calculating alpha values of the fitted distribution models. The result csv file will give us informations about alpha values for 4 different fits, which used 'log-transformation' or 'MSE splitting'(for detailed informations, refer to our paper). The main alpha value we used for step 3 is the 'log_after' value. 

for major cities
```
usage: 3-voronoi_major.py [-h] [--adm1 CITY] [--dir PATH FOR OUTPUT] 
``` 

for minor cities
```
usage: 3-voronoi_minor.py [-h] [--adm1 PROVINCE] [--adm2 CITY] [--dir PATH FOR OUTPUT] 
```

**Voronoi split + calculating alpha Example**
```
python3 3-voronoi_minor.py --adm1 Chungbuk --adm2 Chungju-si --dir Alphas_major/
```

### Step 3. Distributing economic statistics to sub-regions
<hr/>

Note that above procedures are completely **optional**. Above procedures explain how we got the core points/alpha values we used for actual predictions, using the ground-truth population dataset. But we provided you these result datasets(hyperlocal score, core points, alpha values...) in the 'Data' directory so if you want only the prediction result, its completely fine for you to just run the below.

for major cities
```
usage: 4-result_prediction_major.py [-h] [--adm1 CITY] [--dir PATH FOR OUTPUT] 
                                    [--pop GROUND-TRUTH POPULATION]
``` 

for minor cities
```
usage: 4-result_prediction_minor.py [-h] [--adm1 PROVINCE] [--adm2 CITY] [--dir PATH FOR OUTPUT] 
                                    [--pop GROUND-TRUTH POPULATION]
``` 

**Distributing economic statistics Example**
```
python3 4-result_prediction_minor.py --adm1 Chungbuk --adm2 Chungju-si --dir Alphas_major/ --pop 212000 
```

## Results

Results for alpha values of major/minor  
<img src="fig/alpha.PNG" alt="voronoi" width="400"/>

Results for spearman correlation coefficients of major/minor  
<img src="fig/spearman.PNG" alt="voronoi" width="400"/>
