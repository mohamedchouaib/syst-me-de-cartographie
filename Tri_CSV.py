# /**
#  * Copyright 2024 Abdelkefi Mohamed, Balland Nolan, Bottin Elodie, Cancouët Titouan,
# Laudereau Louis, Le Mentec Jonathan et Noël Mathieu
#  *
#  * Licensed under the Apache License, Version 2.0 (the "License");
#  * you may not use this file except in compliance with the License.
#  * You may obtain a copy of the License at
#  *
#  *     http://www.apache.org/licenses/LICENSE-2.0
#  *
#  * Unless required by applicable law or agreed to in writing, software
#  * distributed under the License is distributed on an "AS IS" BASIS,
#  * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  * See the License for the specific language governing permissions and
#  * limitations under the License.
#  */

import pandas as pd
import numpy as np
from pyproj import Transformer
import os
import shutil

############################################################################################################

## Traitement de la base de données

############################################################################################################
"""
tri_CSV processes the database
:param Path: path where the file of the database is
:param Path_work: path where the tile CSV files will be stored.
:param Database_Name: name of the file
:param resolution_max: maximum resolution.
:param pixels: size in pixels used to calculate the tile size.
:return: 
    - tile_size: the physical size of each tile.
    - tuiles: a dictionary of tiles.
"""


def tri_CSV(Path, Path_work, Database_Name, resolution_max, pixels):

    data = pd.read_csv(os.path.join(Path, Database_Name), sep="\t")

    # Transformation des coordonnées géographiques du dataset en coordonnées WebMercator
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857")
    data["x"], data["y"] = transformer.transform(data["lat"].values, data["lon"].values)

    # Suppression des colonnes "datetime", "mmsi", "cog", "lon" et "lat"
    data = data.drop(columns=["datetime", "mmsi", "cog", "lon", "lat"])

    # Renommer les colonnes "x" en "lon" et "y" en "lat"
    data = data.rename(columns={"sog": "speed", "x": "lon", "y": "lat"})

    data = data.sort_values(by="lon")

    ## Définition des variables
    max_lon = max(data["lon"])
    min_lon = min(data["lon"])
    max_lat = max(data["lat"])
    min_lat = min(data["lat"])

    tile_size = resolution_max * pixels

    # Création des CSV des tuiles
    tuiles, nb_tuiles = tiles_creator(tile_size, min_lon, max_lon, min_lat, max_lat)
    print(f"Il y a au plus {nb_tuiles} cvs à produire dans chaque catégorie de bateaux")
    data_ti = data_tiles_info_creator(tuiles)
    tiles_sort_to_csv(data, data_ti, tuiles, Path_work)

    return tile_size, tuiles


############################################################################################################

## Définition des fonctions

############################################################################################################

"""
tiles_creator Generates a grid of tiles.
:param tile_size: the size of each tile.
:param min_lon: the minimum longitude.
:param max_lon: the maximum longitude.
:param min_lat: the minimum latitude.
:param max_lat: the maximum latitude.
:return: 
    - tuiles: a dictionary where each key is a tuple representing the tile indices, and values are tuples representing the boundaries of each tile.
    - nb_tuiles: the total number of tiles created.
"""


def tiles_creator(tile_size, min_lon, max_lon, min_lat, max_lat):

    # Calculer les tuiles
    x_list = np.arange(min_lon, max_lon, tile_size)
    y_list = np.arange(min_lat, max_lat, tile_size)

    # Utilisation d'un dictionnaire de tuiles pour enregistrer les coordonnées dans le système de tuiles (dimension des tuiles) et les associer aux coordonnées géographiques de la carte.
    # Cela permet d'accéder plus rapidement à un ensemble de données, où les clés sont les coordonnées X/Y dans le référentiel des tuiles et les valeurs sont les coordonnées géographiques maximales et minimales (latitude et longitude) de chaque tuile.
    tuiles = {}

    nb_tuiles = 0
    for i in range(len(x_list)):
        for j in range(len(y_list)):

            # Gestion des cas d'extrémité, on produit une tuile plus petite si besoin pour bien recouvrir toute la carte
            if i == len(x_list) - 1 or j == len(y_list) - 1:
                if (
                    i == len(x_list) - 1
                    and j != len(y_list) - 1
                    and x_list[i] != max_lon
                ):
                    tuiles[(i, j)] = (x_list[i], y_list[j], max_lon, y_list[j + 1])
                if (
                    i != len(x_list) - 1
                    and j == len(y_list) - 1
                    and y_list[j] != max_lat
                ):
                    tuiles[(i, j)] = (x_list[i], y_list[j], x_list[i + 1], max_lat)
                if (
                    i == len(x_list) - 1
                    and j == len(y_list) - 1
                    and x_list[i] != max_lon
                    and y_list[j] != max_lat
                ):
                    tuiles[(i, j)] = (x_list[i], y_list[j], max_lon, max_lat)
            else:
                tuiles[(i, j)] = (x_list[i], y_list[j], x_list[i + 1], y_list[j + 1])
            nb_tuiles += 1
    return tuiles, nb_tuiles


"""
data_tiles_info_creator Creates a structured dataset containing information about tiles.
:param tuiles: a dictionary where each key is a tuple representing the tile indices, and values are tuples representing the boundaries of each tile.
:return: 
    - dataset_tuiles: a pandas DataFrame containing informations about tiles.
"""


def data_tiles_info_creator(tuiles):
    dataset_tuiles_coord = pd.DataFrame(
        tuiles.keys(), columns=["x_coord_tile", "y_coord_tile"]
    )
    dataset_tuiles_lon_lat = pd.DataFrame(
        tuiles.values(), columns=["min_lon", "min_lat", "max_lon", "max_lat"]
    )
    dataset_tuiles = pd.concat([dataset_tuiles_coord, dataset_tuiles_lon_lat], axis=1)
    dataset_tuiles["HasBoat"] = 0
    return dataset_tuiles


"""
prepare_directory Prepares a directory for storing files
:param tiles_directory: The path to the directory to prepare. 
"""


def prepare_directory(tiles_directory):
    # Si le dossier existe, le vider
    if os.path.exists(tiles_directory):
        shutil.rmtree(tiles_directory)
        os.makedirs(tiles_directory)
    ##        print(f"Dossier '{tiles_directory}' vidé et recréé.")
    else:
        os.makedirs(tiles_directory)


##        print(f"Dossier '{tiles_directory}' créé.")


"""
tiles_sort_to_csv sort data into .csv tile
:param data: Dataset to sort
:param data_tiles: Information about the tile
:param tuiles: A dictionary where each key is a tuple representing the tile indices, and values are tuples representing the boundaries of each tile.
:param Path_work: Path where the tile CSV files will be stored.
"""


def tiles_sort_to_csv(data, data_tiles, tuiles, Path_work):
    # Sélectionner la colonne 'QO_category' et obtenir les valeurs uniques
    categories = data["QO_category"].unique()
    # Ajouter "All" au tableau NumPy => représentant la catégorie avec tout les bateaux
    categories = np.append(categories, "All")

    paths = {}
    # Trie des bateaux par catégories et par tuiles
    for cat in categories:
        tiles_csv_cat_files = os.path.join(os.path.join(Path_work, cat), "tiles_csv")
        paths[cat] = tiles_csv_cat_files
        prepare_directory(tiles_csv_cat_files)

    last_xtiles_min = 0
    for (x, y), (x_tiles_min, y_tiles_min, x_tiles_max, y_tiles_max) in tuiles.items() :
        if last_xtiles_min != x_tiles_min:
            data_filtre_lon = data[
                (data["lon"] >= x_tiles_min) & (data["lon"] <= x_tiles_max)
            ]
            last_xtiles_min = x_tiles_min
        data_filtre_lon_lat = data_filtre_lon[
            (data_filtre_lon["lat"] >= y_tiles_min)
            & (data_filtre_lon["lat"] <= y_tiles_max)
        ]

        for cat in categories:

            if cat == "All":

                data_filtre_final = data_filtre_lon_lat

                if data_filtre_final.shape[0] > 0:
                    # print(f"nous avons {data_filtre_final.shape[0]} instances dans la tuile {numero} de catégorie {cat}")
                    sous_dossier = paths[cat]
                    chemin_fichier = os.path.join(
                        sous_dossier, f"{x}_{y}.csv"
                    )
                    data_filtre_final.to_csv(chemin_fichier, index=False)
                    data_tiles.loc[
                        (data_tiles["x_coord_tile"] == x)
                        & (data_tiles["y_coord_tile"] == y),
                        "HasBoat",
                    ] = 1

            else:
                data_filtre_final = data_filtre_lon_lat[
                    (data_filtre_lon_lat["QO_category"] == cat)
                ]
                # Enregistrement d'un CSV d'une tuile seulement si un bateau minimun est présent dans la tuile
                if data_filtre_final.shape[0] > 0:
                    # print(f"nous avons {data_filtre_final.shape[0]} instances dans la tuile {numero} de catégorie {cat}")
                    sous_dossier = paths[cat]
                    chemin_fichier = os.path.join(
                        sous_dossier, f"{x}_{y}.csv"
                    )
                    data_filtre_final.to_csv(chemin_fichier, index=False)
                    data_tiles.loc[
                        (data_tiles["x_coord_tile"] == x)
                        & (data_tiles["y_coord_tile"] == y),
                        "HasBoat",
                    ] = 1

    # Enregistrement du csv contenant les informations des tuiles

    chemin_fichier = os.path.join(Path_work, "Data_tuiles_info.csv")
    data_tiles.to_csv(chemin_fichier, index=False)

