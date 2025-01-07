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

import numpy as np
import time
from multiprocessing import Pool
import os
import rasterio
from rasterio.transform import from_origin
import shutil
import pandas as pd
from PIL import Image
from bs4 import BeautifulSoup
import multiprocessing
from pathlib import Path
import sys
from osgeo import gdal

from Parametres_a_modifier import (
    resolution_max,
    Database_Name,
    PATH,
    pixels,
    max_zoom,
    name_tsv,
    zoom_levels,
)
from Tri_CSV import tri_CSV

############################################################################################################

## Définitions de sous fonctions

############################################################################################################


"""
prepare_directory is a fonction to create or empty the files where the tiles are stock.
:param tiles_directory : path directory to the files where the tiles are stock 
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


# Dictionnaire pour stocker les correspondances vitesse -> couleur RGB
color_map = {
    0: [45, 255, 45],  # Speed 0
    1: [43, 242, 56],  # Speed 1
    2: [41, 230, 66],  # Speed 2
    3: [38, 217, 77],  # Speed 3
    4: [36, 204, 87],  # Speed 4
    5: [34, 191, 98],  # Speed 5
    6: [32, 179, 108],  # Speed 6
    7: [29, 166, 119],  # Speed 7
    8: [27, 153, 129],  # Speed 8
    9: [25, 140, 140],  # Speed 9
    10: [23, 128, 150],  # Speed 10
    11: [20, 115, 161],  # Speed 11
    12: [18, 102, 171],  # Speed 12
    13: [16, 89, 182],  # Speed 13
    14: [14, 77, 192],  # Speed 14
    15: [11, 64, 203],  # Speed 15
    16: [9, 51, 212],  # Speed 16
    17: [6, 38, 224],  # Speed 17
    18: [5, 26, 234],  # Speed 18
    19: [2, 13, 245],  # Speed 19
    20: [0, 0, 255],  # Speed 20
}


"""
get_color_from_speed does retrun the color as a function of speed.
:param speed: speed for a particular point
:return: color for the point in [R,G,B] format  
"""


def get_color_from_speed(speed):
    if speed < 0:
        raise ValueError("Vitesse doit être un nombre positif")

    # Si la vitesse est supérieure à 20, on utilise la couleur associée à 20
    if speed > 20:
        speed = 20

    # On cherche la couleur correspondante dans le dictionnaire
    return color_map[int(speed)] + [255]  # Ajoute l'alpha pour RGBA (255 pour opaque)


"""
create_subraster does create a .tif file (image) of a tile.
:param key: coordinate on the tile map
:param value: coordinate of the extreme points of the tile
:param output_directory: path to the output
:param tsv_directory: path to the .tsv file
:param resolution: resolution of the tile
:return: false if a tif is not created
"""


def create_subraster(key, values, output_directory, tsv_directory, resolution):

    x, y = key

    """Vérifie si un fichier CSV nommé '(x,y).csv' existe dans le dossier = si cette tuile contient des informations."""
    if not os.path.exists(tsv_directory):
        print(f"Le dossier {tsv_directory} n'existe pas.")
        return False

    # Construire le nom du fichier cible
    target_file = f"{x}_{y}.csv"

    # Vérifier si le fichier existe, on crée le fichier.tif de la tuile
    if target_file in os.listdir(tsv_directory):

        min_x = values[0]
        min_y = values[1]
        max_x = values[2]
        max_y = values[3]

        # Définir la transformation
        transform = from_origin(min_x, max_y, resolution, resolution)

        # Déterminer la taille du raster pour la tuile
        width = pixels
        height = pixels

        # Créer un tableau pour la tuile (4 canaux pour RGBA)
        raster_data = np.zeros((height, width, 4), dtype=np.uint8)

        tuile_path = os.path.join(tsv_directory, f"{x}_{y}.csv")

        # Lire le fichier CSV
        df = pd.read_csv(tuile_path)

        # Itérer sur les lignes du DataFrame
        for index, row in df.iterrows():

            speed = row["speed"]
            x_coord = row["lon"]
            y_coord = row["lat"]

            row_size = int((max_y - y_coord) / resolution)
            col_size = int((x_coord - min_x) / resolution)

            if 0 <= row_size < height and 0 <= col_size < width:
                color = get_color_from_speed(speed)
                # Priorité au pixel avec les vitesses les plus rapides
                if raster_data[row_size, col_size][2] < color[2]:
                    raster_data[row_size, col_size] = (
                        color  # Remplir avec la couleur correspondant à la vitesse
                    )

        # Déterminer le nom du fichier de la tuile
        tile_filename = os.path.join(output_directory, f"{x}_{y}.tif")

        # Enregistrer le raster de la tuile
        try:
            with rasterio.open(
                tile_filename,
                "w",
                driver="GTiff",
                height=height,
                width=width,
                count=4,
                dtype=rasterio.uint8,
                crs="EPSG:3857",
                transform=transform,
            ) as dst:
                dst.write(
                    raster_data.transpose(2, 0, 1)
                )  # Transposer les dimensions pour RGBA
        except Exception as e:
            print(f"Erreur lors de l'enregistrement : {str(e)}")


###########################################################
## Fonctions qui créent les ReadMe ##
###########################################################
"""
create_readme_final does create ReadMe for all category of boat.
:param resolution_max: resolution in real metres per pixel
:param hours, minutes, seconds: total programme execution time to produce all zoom levels for all categories at a given resolution
:param Path_work: path to the file
"""


def create_readme_final(resolution_max, hours, minutes, seconds, Path_work):
    # Chemin complet du fichier README
    readme_path = os.path.join(Path_work, "README.md")

    # Contenu à écrire dans le README
    content = f"""
# Données du dossier {Path_work} :

- ** Nombre de niveaux de zoom ** : {zoom_levels}
- ** Résolution maximale ** : {resolution_max} en mètres réels par pixel
- ** Nomenclature des sous dossiers et des tuiles** : 
    - Les sous dossiers de {Path_work} sont composés de sous dossier pour chaque catégories de bateaux. Chaque dossier de la catégorie possède un README qui explique le contenu
    
# Rapport de Temps d'Exécution

## Temps d'Exécution Total du Programme pour produire tous les niveau de zoom pour toutes les catégories pour une résolution de {resolution_max} m/pixel:
- **Durée** : {int(hours)} heures, {int(minutes)} minutes, {seconds:.6f} secondes
    """

    # Écriture du contenu dans le fichier README
    with open(readme_path, "w") as readme_file:
        readme_file.write(content)

    print(f"README créé à l'emplacement : {readme_path}")


"""
create_readme does create ReadMe for one category of boat.
:param zoom_levels: most precise zoom level
:param resolutionmax: resolution in real metres per pixel
:param hours, minutes, seconds: total programme execution time to produce all zoom levels for one categories at a given resolution
:param hours0, minutes0, seconds0: execution time for the creation of the .csv file
:param hours1, minutes1, seconds1: execution time to create the most precise tiles
:param hours2, minutes2, seconds2: execution time to create all the other zoom levels
:param Path_work: path to the file
"""


def create_readme(
    zoom_levels,
    resolutionmax,
    hours,
    minutes,
    seconds,
    hours0,
    minutes0,
    seconds0,
    hours1,
    minutes1,
    seconds1,
    hours2,
    minutes2,
    seconds2,
    categorie_directory,
):
    # Chemin complet du fichier README
    readme_path = os.path.join(categorie_directory, "README.md")

    # Contenu à écrire dans le README
    content = f"""
# Données du dossier {categorie_directory} :

- ** Nombre de niveaux de zoom ** : {zoom_levels}
- ** Résolution maximale ** : {resolutionmax} en mètres réels par pixel
- ** Nomenclature des sous dossiers et des tuiles** : 
    - Les sous dossiers de {categorie_directory} sont des numéros de 0 à {zoom_levels} ; 0 le niveau de zoom le moins précis. Chacun est composé des tuiles associés au niveau de zoom du sous dossier.

    - Les tuiles sont donc définies par 3 coordonnées (nombres entiers positifs ou nuls) : z,x,y avec z le niveau de zoom, x et y les coordonnées dans le plan des tuiles par rapport aux autres avec la tuile (0,0) en bas à gauche

    - Chaque dossier, numérotés de 0 à {zoom_levels} correspondant à la coordonnée z, possède des sous dossiers aux aussi numérotés. Ce numéro correspond à la position x des tuiles dans ce dossier. Les tuiles sont nommées y.png avec y la coordoonée spatiale de la tuile
        
    - On trouve des fichiers html qui permettent d'ouvrir la carte. Celui portant le nom openlayers.html est le plus efficace mais en cas de problème utiliser leaflet.html. Celui de googlemap n'est pas très fiable car la crate de fond est très volumineuse.

# Rapport de Temps d'Exécution de cette catégorie

## Temps d'Exécution pour créer les csv de chaque du niveau de zoom le plus précis avec les données du fichier AIS.tsv:
- **Durée** : {int(hours0)} heures, {int(minutes0)} minutes, {seconds0:.6f} secondes

## Temps d'Exécution pour créer les tuiles du niveau de zoom le plus précis avec les données des fichiers .csv :
- **Durée** : {int(hours1)} heures, {int(minutes1)} minutes, {seconds1:.6f} secondes

## Temps d'Exécution pour créer les niveaux de zoom supérieurs via gdal :
- **Durée** : {int(hours2)} heures, {int(minutes2)} minutes, {seconds2:.6f} secondes

## Temps d'Exécution Total du Programme pour cette catégorie :
- **Durée** : {int(hours)} heures, {int(minutes)} minutes, {seconds:.6f} secondes
    """

    # Écriture du contenu dans le fichier README
    with open(readme_path, "w") as readme_file:
        readme_file.write(content)

    print(f"README créé à l'emplacement : {readme_path}")


"""
modify_openlayers_file creates/modifies the openlayers.html file.
:param path: path where creates/modifies the openlayers file
:param max_zoom: most precise zoom level
"""


def modify_openlayers_file(path, max_zoom):

    file_path = os.path.join(path, "openlayers.html")
    new_extent_line = "                                extent: [-17650288.579405, -5408574.014009, 21099711.420595, 15617675.985991],\n"
    # Lire le fichier et modifier la ligne
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Remplacer la ligne contenant "extent:"
    updated_lines = [new_extent_line if "extent:" in line else line for line in lines]

    # Écrire les modifications dans le fichier
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(updated_lines)

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Remplacer la valeur actuelle de maxZoom
    updated_content = content.replace("maxZoom: 1", f"maxZoom: {max_zoom}")
    try:
        # Écrire ou remplacer le contenu du fichier
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(updated_content)

    except Exception as e:
        raise Exception(
            f"Une erreur est survenue lors de la création/modification du fichier : {e}"
        )


###########################################################
## Fonctions qui utilise GDAL pour créer les niveaux de zooms supérieurs ##
###########################################################

"""
merge_tiles merges two results from gdal2tiles.py (the png images for each zoom level).
:param dossier_1: path to the folders 1
:param dossier_2: path to the folders 2
"""


def merge_tiles(dossier_1, dossier_2):

    for zoom_level in os.listdir(dossier_2):
        zoom_path_2 = os.path.join(dossier_2, zoom_level)
        zoom_path_1 = os.path.join(dossier_1, zoom_level)

        # Ignorer si ce n'est pas un dossier
        if not os.path.isdir(zoom_path_2):
            continue

        # Créer le dossier de niveau de zoom dans dossier_1 s'il n'existe pas
        if not os.path.exists(zoom_path_1):
            os.makedirs(zoom_path_1)

        for x_coord in os.listdir(zoom_path_2):
            x_path_2 = os.path.join(zoom_path_2, x_coord)
            x_path_1 = os.path.join(zoom_path_1, x_coord)

            # Créer le dossier x dans dossier_1 s'il n'existe pas
            if not os.path.exists(x_path_1):
                os.makedirs(x_path_1)

            for y_file in os.listdir(x_path_2):
                y_path_2 = os.path.join(x_path_2, y_file)
                y_path_1 = os.path.join(x_path_1, y_file)

                # Si le fichier n'existe pas dans dossier_1, copier depuis dossier_2
                if not os.path.exists(y_path_1):
                    shutil.copy2(y_path_2, y_path_1)
                else:
                    # Charger les deux images en RGBA
                    img_1 = Image.open(y_path_1).convert("RGBA")
                    img_2 = Image.open(y_path_2).convert("RGBA")

                    # Convertir en tableaux NumPy
                    arr_1 = np.array(img_1)
                    arr_2 = np.array(img_2)

                    # Vérifier que les deux tableaux ont la même forme
                    if arr_1.shape != arr_2.shape:
                        print(
                            f"Les formes des images sont différentes : {arr_1.shape} vs {arr_2.shape}"
                        )
                        raise ValueError(
                            "Les deux images doivent avoir la même taille et format pour être fusionnées."
                        )

                    # Fusion : Garder les pixels avec la composante bleue (indice 2) la plus forte
                    fusion = np.where(
                        arr_2[..., 2:3] > arr_1[..., 2:3], arr_2, arr_1
                    )  # Utiliser des dimensions compatibles

                    # Convertir le tableau fusionné en image
                    img_fusion = Image.fromarray(fusion, mode="RGBA")

                    # Sauvegarder l'image fusionnée à la place de la première image
                    img_fusion.save(y_path_1)


"""
create_zoom uses gdal2tiles to create the different zoom levels of a tile.
:param name: name of the file
:param tiles_producted_directory: path to the folders where the file is supposed to be
:param process_output_directories: path to the folders where the zoom levels created are to be saved
:param zoom_levels: most precise zoom level
:return: false if the zoom is not create
"""


def create_zoom(
    name, tiles_producted_directory, process_output_directories, zoom_levels
):

    def gdal2tiles(name, tiles_producted_directory, process_output_directories):

        # Vérifier si le fichier existe, sinon on passe à la tuile suivante mais normalement on ne passe pas dans cette boucle
        if name not in os.listdir(tiles_producted_directory):
            print(
                f"le fichier {name} n'a pas été trouvé dans dossier {tiles_producted_directory}"
            )
            return

        target = os.path.join(tiles_producted_directory, name)

        # On cherche le path de gdal2tiles
        gdal2tiles_path = gdal.__file__[:-8] + '_utils/gdal2tiles.py'

        cmd = f"{sys.executable} {gdal2tiles_path} -z {zoom_levels} {target} {process_output_directories}"
        # cmd = [
        #     sys.executable,
        #     "C:/Users/louis/miniconda3/envs/pjent/Lib/site-packages/osgeo_utils/gdal2tiles.py",
        #     '-z', zoom_levels, target, process_output_directories
        #     ]

        # Exécution de la commande
        exit_code = os.system(cmd)

        # Vérification et gestion des erreurs
        if exit_code != 0:
            return f"Erreur lors de l'exécution de : {cmd}"

    # Vérifier si le répertoire de sortie existe, sinon le créer et généré les niveaux de zoom de la première tuile de ce processus
    if not os.path.exists(os.path.join(process_output_directories, "0")):
        os.makedirs(process_output_directories, exist_ok=True)
        gdal2tiles(name, tiles_producted_directory, process_output_directories)

    else:
        process__new_output_directories = os.path.join(
            process_output_directories, "nouveau_niveau_zoom"
        )
        os.makedirs(process__new_output_directories)

        # On génère les niveaux de zoom de cette tuile
        gdal2tiles(name, tiles_producted_directory, process__new_output_directories)
        # Et on fusionne les image png résultantes de gdal2tiles avec un résultat général
        merge_tiles(process_output_directories, process__new_output_directories)
        shutil.rmtree(process__new_output_directories)


"""
process_tile_group
:param group: name of a folders
:param tiles_producted_directory: path where the folders where is supposed to be
:param Gdal_directory: general directory for process outputs
:param zoom_levels: most precise zoom level
"""


def process_tile_group(group, tiles_producted_directory, Gdal_directory, zoom_levels):
    temp_dir = os.path.join(Gdal_directory, f"temp_{os.getpid()}")
    os.makedirs(temp_dir, exist_ok=True)

    for name in group:
        create_zoom(name, tiles_producted_directory, temp_dir, zoom_levels)


"""
liste_sous_dossiers generates a list of subfolder names for the path given as input
:param path: path of a folder
:return: list of the subfolders created
"""


def liste_sous_dossiers(path):
    try:
        # Liste les éléments du répertoire et filtre pour obtenir uniquement les dossiers
        sous_dossiers = [
            nom for nom in os.listdir(path) if os.path.isdir(os.path.join(path, nom))
        ]
        return sous_dossiers
    except FileNotFoundError:
        print(f"Le chemin '{path}' n'existe pas.")
        return []
    except PermissionError:
        print(f"Permission refusée pour accéder au chemin '{path}'.")
        return []


"""
liste_fichiers_tif generates a list of .tsv file names associated with each tile in the path given as input
:param path: path of a folder
:return: .tif files
"""


def liste_fichiers_tif(path):
    try:
        # Liste les éléments du répertoire et filtre pour obtenir uniquement les fichiers .tsv
        fichiers_tif = [
            nom
            for nom in os.listdir(path)
            if os.path.isfile(os.path.join(path, nom)) and nom.endswith(".tif")
        ]
        return fichiers_tif
    except FileNotFoundError:
        print(f"Le chemin '{path}' n'existe pas.")
        return []
    except PermissionError:
        print(f"Permission refusée pour accéder au chemin '{path}'.")
        return []


"""
html adjusts the html to open Openlayer
:param nouvelle_valeur_maxZoom: most precise zoom level
:param html_path: path to the .html file
"""


def htlm(nouvelle_valeur_maxZoom, html_path):
    # Charger le fichier HTML
    html_file = os.path.join(html_path, "openlayers.html")
    with open(html_file, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")

    # Rechercher et modifier maxZoom
    script_tag = soup.find("script", text=lambda t: "maxZoom" in t)
    if script_tag:
        # Modifier la ligne contenant maxZoom
        script_contenu = script_tag.string.splitlines()
        for i, ligne in enumerate(script_contenu):
            if "maxZoom" in ligne:
                # Remplacer la valeur de maxZoom par la nouvelle valeur
                script_contenu[i] = ligne.replace(
                    "maxZoom: 14", f"maxZoom: {nouvelle_valeur_maxZoom}"
                )
        script_tag.string = "\n".join(script_contenu)

    # Sauvegarder les modifications dans un nouveau fichier HTML
    html_modifie = "chemin/vers/fichier_modifie.html"
    with open(html_modifie, "w", encoding="utf-8") as file:
        file.write(str(soup))


# Verrou global pour éviter les conflits
lock = multiprocessing.Lock()

"""
merge merges two images by comparing their alpha values
:param image1_path: path to the first image file
:param image2_path: path to the second image file
:param output_path: path where the merged image will be saved
"""


def merge(image1_path, image2_path, output_path):
    img_1 = Image.open(image1_path).convert("RGBA")
    img_2 = Image.open(image2_path).convert("RGBA")

    arr_1 = np.array(img_1)
    arr_2 = np.array(img_2)

    if arr_1.shape != arr_2.shape:
        raise ValueError(f"Taille incompatible : {arr_1.shape} vs {arr_2.shape}")

    fusion = np.where(arr_2[..., 2:3] > arr_1[..., 2:3], arr_2, arr_1)

    img_fusion = Image.fromarray(fusion, mode="RGBA")
    img_fusion.save(output_path)


"""
process_tile processes a single tile from the source directories and saves it to the target directory
:param source_dirs: list of source directories containing tiles
:param target_dir: target directory to save the processed tile
:param tile_path: path to the tile to be processed
"""


def process_tile(source_dirs, target_dir, tile_path):
    global lock  # Utilisation du verrou global
    target_tile_path = target_dir / tile_path

    for source_dir in source_dirs:
        source_tile_path = source_dir / tile_path
        if source_tile_path.exists():
            with lock:
                if target_tile_path.exists():
                    temp_path = target_tile_path.with_suffix(".png")
                    merge(target_tile_path, source_tile_path, temp_path)
                    os.replace(temp_path, target_tile_path)
                else:
                    target_tile_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_tile_path, target_tile_path)


"""
parallel_merge merges tiles in parallel from multiple source directories into a target directory
:param source_dirs: list of source directories containing tiles
:param target_dir: target directory to save the merged tiles
"""


def parallel_merge(source_dirs, target_dir):
    source_dirs = [Path(d) for d in source_dirs]
    target_dir = Path(target_dir)

    all_tiles = set()
    for source_dir in source_dirs:
        for tile_path in source_dir.rglob("*.png"):
            relative_path = tile_path.relative_to(source_dir)
            all_tiles.add(relative_path)

    with Pool() as pool:
        pool.starmap(
            process_tile,
            [(source_dirs, target_dir, tile_path) for tile_path in all_tiles],
        )


############################################################################################################

## MAIN

############################################################################################################

# Appeler la fonction principale dans le bloc principal
if __name__ == "__main__":

    # Démarrer le chronomètre pour la catégorie
    start_time_total = time.time()

    # trie du fichier TSV en sous fichier associé aux tuiles par chaque catégorie
    Path_work_root = os.path.join(PATH, name_tsv)
    Path_work = os.path.join(
        Path_work_root, "Resolution_" + str(resolution_max) + "m_per_pixel"
    )

    tile_size, tuiles = tri_CSV(
        PATH, Path_work, Database_Name, resolution_max, pixels
    )  # dimension de chaque tuile du niveau de zoom k en mètres réels
    # tile_size = resolution_max*pixels
    end_time_tri_csv = time.time()
    collapse_tri_csv = end_time_tri_csv - start_time_total

    hours0, remainder = divmod(collapse_tri_csv, 3600)
    minutes0, seconds0 = divmod(remainder, 60)

    # Liste des catégories de bateaux trouvés dans le la base de donnée et un tableau récapitulatif des tuiles de ce la présence de bateaux dedans ou non
    liste_categories = liste_sous_dossiers(Path_work)

    # prepare_directory(os.path.join(Path_work,"All_Caterories"))

    for categorie in liste_categories:

        categorie_directory = os.path.join(Path_work, categorie)
        tsv_directory = os.path.join(categorie_directory, "tiles_csv")
        tiles_producted_directory = os.path.join(categorie_directory, "tiles_producted")

        # Démarrer le chronomètre pour la catégorie
        start_time = time.time()

        prepare_directory(tiles_producted_directory)
        print(
            f"Création des tuiles de la catérorie {categorie} pour une résolution de {resolution_max} m/pixel"
        )

        try:
            with Pool() as pool:
                # Passer les arguments nécessaires à create_subraster
                pool.starmap(
                    create_subraster,
                    [
                        (
                            key,
                            value,
                            tiles_producted_directory,
                            tsv_directory,
                            resolution_max,
                        )
                        for key, value in tuiles.items()
                    ],
                )
        except Exception as e:
            print(f"Erreur lors de l'exécution du pooling : {str(e)}")

        print(
            "Fin de la génération des tuiles, génèration les niveaux de zoom avec tous les processus..."
        )
        # Arrêter le chronomètre pour avoir le temps de création des tuiles du niveau de zoom le plus précis
        end_time1 = time.time()

        # Calculez le temps écoulé
        elapsed_time1 = end_time1 - start_time
        hours1, remainder = divmod(elapsed_time1, 3600)
        minutes1, seconds1 = divmod(remainder, 60)

        liste_raster = liste_fichiers_tif(tiles_producted_directory)
        max_processes = os.cpu_count()
        # Déterminer le nombre de processus disponibles
        chunk_size = (len(liste_raster) + max_processes - 1) // max_processes
        tile_groups = [
            liste_raster[i : i + chunk_size]
            for i in range(0, len(liste_raster), chunk_size)
        ]

        # Créer un répertoire général pour les sorties des processus
        Gdal_directory = os.path.join(tiles_producted_directory, "processGdal")
        os.makedirs(Gdal_directory, exist_ok=True)

        try:

            with Pool() as pool:
                pool.starmap(
                    process_tile_group,
                    [
                        (group, tiles_producted_directory, Gdal_directory, zoom_levels)
                        for group in tile_groups
                    ],
                )

        except Exception as e:
            print(f"Erreur lors de l'exécution du pooling de Gdal : {str(e)}")

        # Fusion des résultats des processus :
        print(
            "Fin de la génération des niveaux de zoom par processus, résultats en cours de fusion ..."
        )

        list_threads = liste_sous_dossiers(Gdal_directory)
        for i in range(len(list_threads)):
            list_threads[i] = os.path.join(Gdal_directory, list_threads[i])
        target_dir = categorie_directory
        parallel_merge(list_threads, target_dir)

        # Parcourir les sous-dossiers immédiats
        for entry in os.listdir(Gdal_directory):
            subdirectory_path = os.path.join(Gdal_directory, entry)
            # Vérifier si c'est un dossier
            if os.path.isdir(subdirectory_path):
                # Copier les fichiers non-dossiers vers categorie_directory s'ils n'existent pas
                for file_name in os.listdir(subdirectory_path):
                    file_path = os.path.join(subdirectory_path, file_name)
                    if os.path.isfile(file_path):  # Vérifie que c'est un fichier
                        target_path = os.path.join(categorie_directory, file_name)
                        if not os.path.exists(
                            target_path
                        ):  # Si le fichier n'existe pas déjà
                            shutil.copy2(
                                file_path, target_path
                            )  # Copier avec les métadonnées
            break

        modify_openlayers_file(categorie_directory, max_zoom)
        shutil.rmtree(tiles_producted_directory)
        shutil.rmtree(tsv_directory)

        # Arrêter le chronomètre pour avoir le temps de créations de niveaux de zooms supérieurs
        end_time2 = time.time()

        # Calculez le temps écoulé
        elapsed_time = end_time2 - end_time1
        hours2, remainder = divmod(elapsed_time, 3600)
        minutes2, seconds2 = divmod(remainder, 60)

        # Arrêter le chronomètre
        end_time = time.time()

        # Calculez le temps écoulé
        elapsed_time = end_time - start_time + collapse_tri_csv
        hours, remainder = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(remainder, 60)

        create_readme(
            zoom_levels,
            resolution_max,
            hours,
            minutes,
            seconds,
            hours0,
            minutes0,
            seconds0,
            hours1,
            minutes1,
            seconds1,
            hours2,
            minutes2,
            seconds2,
            categorie_directory,
        )

        print(
            f"Temps d'exécution de la création des tuiles pour une précision de : {resolution_max} m/pixel de la catégorie : {categorie} sur tous les niveaux de zoom avec multi-threads est de : {int(hours)} heures, {int(minutes)} minutes, {seconds:.6f} secondes"
        )

        # Arrêter le chronomètre pour avoir le temps de création des tuiles du niveau de zoom le plus précis
        end_time_total = time.time()

        # Calculez le temps écoulé
        elapsed_time_total = end_time_total - start_time_total
        hours, remainder = divmod(elapsed_time_total, 3600)
        minutes, seconds = divmod(remainder, 60)

        create_readme_final(resolution_max, hours, minutes, seconds, Path_work)

        print(
            f"Temps d'exécution de la création des tuiles pour une précision de : {resolution_max} m/pixel pour toutes les catégories sur tous les niveaux de zoom avec multi-threads est de : {int(hours)} heures, {int(minutes)} minutes, {seconds:.6f} secondes"
        )
