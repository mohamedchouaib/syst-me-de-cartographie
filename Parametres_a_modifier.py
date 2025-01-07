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

############################################################################################################

## Définition des variables

############################################################################################################

## A DEFINIR PAR L'UTILISATEUR

############################################################################################################

# Chemin d'accès aux données (sans le nom du fichier AIS.tsv)
# si Docker : PATH = r"/root/Database"
PATH = r"/root/Database"

# Nom de la base de données (ex : dataBase.tsv)
Database_Name = "ALL_01072023_IMT.tsv"

## Paramètres d'exécution : ##
####

# Niveau de zoom | Résolution (m/px) | Taille (px) | Nombre de tuiles
# 0              | 156543.033928041  | 256 x 256   | 1
# 1              | 78271.51696402048 | 512 x 512   | 4
# 2              | 39135.75848201024 | 1024 x 1024 | 16
# 3              | 19567.87924100512 | 2048 x 2048 | 64
# 4              | 9783.939620502561 | 4096 x 4096 | 256
# 5              | 4891.96981025128  | 8192 x 8192 | 1024
# 6              | 2445.98490512564  | 16384 x 16384 | 4096
# 7              | 1222.99245256282  | 32768 x 32768 | 16384
# 8              | 611.49622628141   | 65536 x 65536 | 65536
# 9              | 305.748113140705  | 131072 x 131072 | 262144
# 10             | 152.8740565703525 | 262144 x 262144 | 1048576
# 11             | 76.43702828517625 | 524288 x 524288 | 4194304
# 12             | 38.21851414258813 | 1048576 x 1048576 | 16777216
# 13             | 19.109257071294063 | 2097152 x 2097152 | 67108864
# 14             | 9.554628535647032 | 4194304 x 4194304 | 268435456
# 15             | 4.777314267823516 | 8388608 x 8388608 | 1073741824
# 16             | 2.388657133911758 | 16777216 x 16777216 | 4294967296
# 17             | 1.194328566955879 | 33554432 x 33554432 | 17179869184
# 18             | 0.5971642834779395 | 67108864 x 67108864 | 68719476736


###

# Mettre un entier entre 1 et 18 suivant la résolution maximale souhaitée
# !! ATTENTION !! un résolution plus précise que 14 commence à rendre les points très difficilement visibles en contraste avec la carte, à réserver pour une observation ponctuelle
max_zoom = 6

############################################################################################################
## NE PAS MODIFIER
############################################################################################################

zoom_levels = f"0-{max_zoom}"

zoom_resolutions = {
    0: 156543.033928041,
    1: 78271.51696402048,
    2: 39135.75848201024,
    3: 19567.87924100512,
    4: 9783.939620502561,
    5: 4891.96981025128,
    6: 2445.98490512564,
    7: 1222.99245256282,
    8: 611.49622628141,
    9: 305.748113140705,
    10: 152.8740565703525,
    11: 76.43702828517625,
    12: 38.21851414258813,
    13: 19.109257071294063,
    14: 9.554628535647032,
    15: 4.777314267823516,
    16: 2.388657133911758,
    17: 1.194328566955879,
    18: 0.5971642834779395,
}

# Résolution maximale on prend 80/100 de la résoltion du zoom max pour être sur de ne pas perdre de l'information
resolution_max = int(zoom_resolutions[max_zoom] * 90 / 100)

# Nombre de pixel par coté à chaque tuile, moins il y a de tuiles plus le calcul est rapide mais plus cela consomme de ram (optimal ~3000 pixels de côté)
pixels = 3000

name_tsv = Database_Name.split(".")[0]
