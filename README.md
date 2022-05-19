# Distributing internal economic level of districts using satellite imagery and power-laws for cities (KCC 2022)

Pytorch Implementation of Distributing internal economic level of districts using satellite imagery and power-laws for cities

  * Our model consists of 3 parts, which are introduced below.
  * Step 1. We measure the hyperlocal economic scores of each grids by inferring the relative degree of individual grid image's economic development via ordinal regression.
  * Step 2. We get the core points of the districts using gradient descent, and make Voronoi cells using the points.
  * Step 3. After choosing appropriate distribution for the district, we distribute the economic statistics using the distribution. For alpha in the distribution formula, we pre-calculated the average alpha values of districts by using the existing ground-truth data.

## Quickstart
```
$ pip install -r requirements.txt
```  
