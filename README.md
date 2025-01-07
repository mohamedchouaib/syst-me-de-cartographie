# Environnement Docker
Docker environnement to run the code 

## Clone the depository

```bach
git clone git@github.com:Daren42/PROJ_COM.git
```

## Add the file

Create a DataBase folder in the PROJ_COM folder with the ais tsv/csv

Change the PATH to : r"/root/Database"

Change the DataBase_Name in the Parametres_a_modifier.py to the file name of the ais csv

## Adapt your parameters

Change the parameters in the first section of the ```Parametres_a_modifier.py``` file according to the database and resolution required for the map to be produced.

## Create 

Open a cmd and get inside the directory of the PROJ_COM folder and run : 

```bach
docker build -t pjent .
```
and then :

```bach
docker run --rm -v /directory/of/the/folder:/root/ pjent
```

This will launch automatically the MAIN.py that create the tiles

# Environnement Conda
Conda environnement to run the code 

## Clone the depository

```bach
git clone git@github.com:Daren42/PROJ_COM.git
```

## Add the file

Create a DataBase folder in the PROJ_COM folder with the ais tsv/csv

Change the DataBase_Name in the Parametres_a_modifier.py to the file name of the ais csv

## Adapt your parameters

Change the parameters in the first section of the ```Parametres_a_modifier.py``` file according to the database and resolution required for the map to be produced.

## Activate the conda environnement

Download miniconda

Open the Anaconda Prompt

Get inside the directory of the PROJ_COM folder and run : 

```bach
conda env create -f pjent_env.yml -n pjent
```
and then :

```bach
conda activate pjent
```

You can now launch the python program as you would in a prompt :

```bach
python MAIN.py
```
