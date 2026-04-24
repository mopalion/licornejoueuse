import csv
from datetime import datetime, date
from .models import Game, Location, Label, Author, Illustrator, Mechanism, Comment, Editor, Theme
import requests
from os import makedirs
from os import environ
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from django.conf import settings
import re
import traceback
from os import getenv
import shutil


def log_error_in_file(e):
    """
    Enregistre une erreur dans un fichier de log texte.

    Récupère le répertoire cible depuis la variable d'environnement DJANGO_ERRORS_DIR.
    Si celle-ci est vide, utilise le répertoire courant ("./").
    Ajoute la trace complète de l'exception, le message d'erreur et son type dans 'errors.txt'.

    :param e: L'exception à logger.
    """
    django_errors_dir = getenv("DJANGO_ERRORS_DIR")
    if django_errors_dir != '':
        django_errors_dir = "./"
    with open(f"{django_errors_dir}errors.txt", "a") as fd:
        fd.write("******************************************************")
        fd.write(traceback.format_exc())
        fd.write(str(e))
        fd.write("\n")
        fd.write(str(type(e)))
        fd.write("\n")


def delete_games():
    """
    Supprime toutes les données liées aux jeux dans la base de données.

    Supprime dans l'ordre : les jeux, les thèmes, les mécanismes,
    les auteurs, les éditeurs et les illustrateurs.
    Chaque objet est supprimé individuellement via la méthode .delete() de Django.
    """
    games = Game.objects.all()
    for game in games:
        game.delete()
    themes = Theme.objects.all()
    for theme in themes:
        theme.delete()
    mechanisms = Mechanism.objects.all()
    for mechanism in mechanisms:
        mechanism.delete()
    authors = Author.objects.all()
    for author in authors:
        author.delete()
    editors = Editor.objects.all()
    for editor in editors:
        editor.delete()
    illustrators = Illustrator.objects.all()
    for illustrator in illustrators:
        illustrator.delete()


def cast_date(string):
    """
    Convertit une chaîne de caractères en objet datetime.

    Accepte plusieurs séparateurs de date : espace, "/", et ".".
    Tous sont normalisés en "-" avant le parsing au format "%d-%m-%Y".
    Retourne une chaîne vide si l'entrée est vide.

    :param string: La date sous forme de chaîne (ex: "01/01/2023", "01.01.2023").
    :return: Un objet datetime si la chaîne est non vide, sinon une chaîne vide.
    """
    if string != "":
        date_res = datetime.strptime(string.strip().replace(" ", "-").replace("/", "-").replace(".", "-"), "%d-%m-%Y")
    else:
        date_res = ""
    return date_res


def get_game(row, site, à_vendre):
    """
    Crée et enregistre un objet Game en base de données à partir d'une ligne CSV.

    Détermine le type de jeu (wooden, rpg, boardgame) selon le thème.
    Crée les entités liées si elles n'existent pas encore (thèmes, auteurs,
    illustrateurs, mécanismes, éditeurs), puis les associe au jeu via
    des relations ManyToMany.
    Ajoute également des commentaires si des remarques ou des manques sont renseignés.

    :param row: Dictionnaire représentant une ligne du fichier CSV.
    :param site: Instance de Location à associer au jeu.
    :param à_vendre: Instance de Label "À vendre" à associer si applicable.
    """
    # Détermination du type de jeu selon le thème
    match row["Thème"]:
        case "Bois":
            game_type = "wooden"
        case "Bois - hors inventaire":
            game_type = "wooden"
        case "JDR":
            game_type = "rpg"
        case "jeu de rôle":
            game_type = "rpg"
        case _:
            game_type = "boardgame"

    # Création de l'objet Game avec les champs du CSV
    game = Game(
        name=row["Jeux"],
        details=row["description"],
        games_library_categorization=row["Classification ludothèque COL"],
        adapted_games_library_categorization_1=row["COL adapté 1"].lower(),
        adapted_games_library_categorization_2=row["COL adapté 2"].lower(),
        time=row["Duree"],
        players_number=row["Nbre de joueurs"],
        price=float(row["Prix neuf"].replace(",", ".").strip()),
        number=row["N° réf"],
        location=site,
        cards_number=row["Nbre de cartes"] if row["Nbre de cartes"] != "" else 0,
        cards_size=row["Dimension cartes"],
        origin=row["don provenance?"],
        age=0 if row["Âge"] == "" else row["Âge"],
        game_type=game_type,
        rules_video_link=row["liens vers video régles"],
        for_child=True if row["Enfants / Adultes"] == "Enfants" else False,
        missing_items=row["Manque"],
        inventory=row["Inventaire"],
    )

    # Champs optionnels : traités uniquement si la valeur est présente dans le CSV
    if row["Date d'entrée"].strip() != "":
        game.entry_year = cast_date(row["Date d'entrée"]).year
    if row["dernier inventaire"].strip() != "":
        game.last_inventory_date = cast_date(row["dernier inventaire"])
    if row["annee de sortie"].strip() != "":
        game.year = row["annee de sortie"]

    # Sauvegarde en base de données
    game.save()

    # Ajout du label "À vendre" si applicable
    if row["A vendre?"] == "oui":
        game.labels.add(à_vendre)

    # Association des thèmes (création si inexistants)
    if row["Thème"] != "":
        for theme_name in row["Thème"].split(","):
            themes = Theme.objects.filter(name=theme_name.strip().lower())
            if not themes:
                theme = Theme(name=theme_name.strip().lower())
                theme.save()
            else:
                theme = themes[0]
            game.themes.add(theme)

    # Association des illustrateurs (création si inexistants)
    if row["illustrateur"] != "":
        for illustrator_name in row["illustrateur"].split(","):
            illustrators = Illustrator.objects.filter(name=illustrator_name.strip())
            if not illustrators:
                illustrator = Illustrator(name=illustrator_name.strip())
                illustrator.save()
            else:
                illustrator = illustrators[0]
            game.illustrators.add(illustrator)

    # Association des auteurs (création si inexistants)
    if row["auteur"] != "":
        for author_name in row["auteur"].split(","):
            authors = Author.objects.filter(name=author_name.strip())
            if not authors:
                author = Author(name=author_name.strip())
                author.save()
            else:
                author = authors[0]
            game.authors.add(author)

    # Association des mécanismes (création si inexistants)
    if row["mécanisme"] != "":
        for mechanism_name in row["mécanisme"].split(","):
            mechanisms = Mechanism.objects.filter(name=mechanism_name.strip().lower())
            if not mechanisms:
                mechanism = Mechanism(name=mechanism_name.strip().lower())
                mechanism.save()
            else:
                mechanism = mechanisms[0]
            game.mechanisms.add(mechanism)

    # Ajout d'un commentaire général si renseigné
    if row["Commentaires"] != "":
        game.comment_set.create(text=row["Commentaires"], created_date=cast_date("01/01/1970"))

def load_data(csvfilename):
    """
    Charge les données depuis un fichier CSV et les insère en base de données.

    Crée ou récupère la Location "Inconnu" et le Label "À vendre" si nécessaire.
    Itère sur chaque ligne du CSV et tente de créer un jeu via get_game().
    En cas d'erreur (ValueError, IntegrityError, ValidationError, TypeError),
    l'erreur est capturée, le jeu est ignoré et l'erreur est enregistrée.
    Un fichier "errors.txt" est généré en fin de traitement avec le récapitulatif
    des jeux en erreur.

    :param csvfilename: Chemin vers le fichier CSV à importer.
    """
    # Récupération ou création de la localisation par défaut
    locations = Location.objects.filter(name="Inconnu")
    if len(locations) == 0:
        site = Location(name="Inconnu")
        site.save()
    else:
        site = locations[0]

    # Récupération ou création du label "À vendre"
    labels = Label.objects.filter(label="À vendre")
    if len(labels) == 0:
        à_vendre = Label(label="À vendre")
        à_vendre.save()
    else:
        à_vendre = labels[0]

    error_games = []

    # Lecture du CSV et traitement ligne par ligne
    with open(csvfilename) as csvfile:
        data = csv.DictReader(csvfile)
        for row in data:
            try:
                get_game(row, site, à_vendre)
            except (ValueError, IntegrityError, ValidationError, TypeError) as e:
                print(row["Jeux"])
                error_games.append((row["N° réf"], row["Jeux"], e))
                continue

        # Écriture du rapport d'erreurs dans un fichier texte
        with open("errors.txt", "w") as fd:
            for number, name, exception in error_games:
                fd.write("********************\n")
                fd.write(str(number))
                fd.write("\n")
                fd.write(name + "\n")
                fd.write(str(exception))
                fd.write("\n")


def get_csv(model_to_extract=Game, file_name=""):
    """
    Exporte les données d'un modèle Django dans un fichier CSV.

    Appelle la méthode extract_data() du modèle, qui doit retourner un objet StringIO.
    Si un nom de fichier est fourni (ou généré par défaut), le contenu est écrit sur le disque
    via shutil.copyfileobj().
    Si file_name est None, retourne directement le buffer StringIO sans écrire de fichier.

    :param model_to_extract: Classe du modèle Django à exporter (par défaut : Game).
    :param file_name: Nom du fichier de sortie. Si vide, un nom est généré automatiquement.
                      Si None, le buffer est retourné sans écriture sur disque.
    :return: Le buffer StringIO si file_name est None, sinon None.
    """
    # Génération automatique du nom de fichier si non fourni
    if file_name == "":
        file_name = f"data-{model_to_extract.__name__}.csv"

    # Extraction des données via la méthode du modèle
    buffer = model_to_extract.extract_data()
    buffer.seek(0)  # Remise du curseur au début du buffer avant lecture

    if file_name is not None:
        # Écriture du buffer dans un fichier sur le disque
        with open(file_name, "w") as file:
            shutil.copyfileobj(buffer, file)
    else:
        # Retour du buffer directement si aucun fichier n'est souhaité
        return buffer

