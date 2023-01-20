
# Simple Crawler

A simple pytho crawler 

:heavy_check_mark: Respecte la politeness 

:heavy_check_mark: Ne crawle pas un site web qui l’interdit 



## Auteur

Francois Wallyn


## Installation des packages

```bash
  pip install -r requirements.txt
```
    
## Usage/Exemples
Pour lancer un exemple de crawler 

```bash
python3 main.py --url https://ensai.fr --n_pages 50 --add_db --export_path_full ./mytext.txt
```
Avec les paramètres : 

- `--url` : URL de départ du crawler (défaut : https://ensai.fr)
- `--n_pages` : nombre de pages total à trouver (défaut 50)
- `--export_path_full` : chemin vers le fichier `.txt` pour exporter les urls (défaut vide : pas exporter)
- `--add_db` initie une base de données sqlite à la racine et ajoute les urls trouvées

Pour utiliser le framework et manipuler un crawler :

```python
from crawler import Crawler

my_crawler = Crawler(urls=["https://ensai.fr"], n_pages=50)

crawler.run()
## URL à visiter trouvées par le crawler
crawler.urls_to_visit 

## URL déjà visitées par le crawler
crawler.visited_urls 

```