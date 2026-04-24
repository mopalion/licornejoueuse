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
    if string != "":
        date_res = datetime.strptime(string.strip().replace(" ","-").replace("/","-").replace(".","-"),"%d-%m-%Y")
    else:
        date_res = ""
    return date_res

def get_game(row, site, à_vendre):
    match row["Thème"]:
        case "Bois":
            game_type="wooden"
        case "Bois - hors inventaire":
            game_type="wooden"
        case "JDR":
            game_type="rpg"
        case "jeu de rôle":
            game_type="rpg"
        case _:
            game_type="boardgame"
    game = Game(
        name=row["Jeux"],
        details=row["description"],
        games_library_categorization=row["Classification ludothèque COL"],
        adapted_games_library_categorization_1=row["COL adapté 1"].lower(),
        adapted_games_library_categorization_2=row["COL adapté 2"].lower(),
        time=row["Duree"],
        players_number=row["Nbre de joueurs"],
        price=float(row["Prix neuf"].replace(",",".").strip()),
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
    if row["Date d'entrée"].strip() != "":
        game.entry_year=cast_date(row["Date d'entrée"]).year
    if row["dernier inventaire"].strip() != "":
        game.last_inventory_date=cast_date(row["dernier inventaire"])
    if row["annee de sortie"].strip() != "":
        game.year=row["annee de sortie"]
    game.save()
    if row["A vendre?"] == "oui":
        game.labels.add(à_vendre)
    if row["Thème"] != "":
        for theme_name in row["Thème"].split(","):
            themes = Theme.objects.filter(name=theme_name.strip().lower())  
            if not themes:
                theme = Theme(name=theme_name.strip().lower())
                theme.save()
            else:
                theme = themes[0]
            game.themes.add(theme)
    if row["illustrateur"] != "":
        for illustrator_name in row["illustrateur"].split(","):
            illustrators = Illustrator.objects.filter(name=illustrator_name.strip())
            if not illustrators:
                illustrator = Illustrator(name=illustrator_name.strip())
                illustrator.save()
            else:
                illustrator = illustrators[0]
            game.illustrators.add(illustrator)
    if row["auteur"] != "":
        for author_name in row["auteur"].split(","):
            authors = Author.objects.filter(name=author_name.strip())
            if not authors:
                author = Author(name=author_name.strip())
                author.save()
            else:
                author = authors[0]
            game.authors.add(author)
    if row["mécanisme"] != "":
        for mechanism_name in row["mécanisme"].split(","):
            mechanisms = Mechanism.objects.filter(name=mechanism_name.strip().lower())
            if not mechanisms:
                mechanism = Mechanism(name=mechanism_name.strip().lower())
                mechanism.save()
            else:
                mechanism = mechanisms[0]
            game.mechanisms.add(mechanism)
    if row["Commentaires"] != "":
        game.comment_set.create(text=row["Commentaires"], created_date=cast_date("01/01/1970"))

def load_data(csvfilename):
    locations = Location.objects.filter(name="Inconnu")
    if len(locations) == 0:
        site = Location(name="Inconnu")
        site.save()
    else:
        site = locations[0]
    labels = Label.objects.filter(label="À vendre")
    if len(labels) == 0:
        à_vendre = Label(label="À vendre")
        à_vendre.save()
    else:
        à_vendre = labels[0]


    error_games = []
    with open(csvfilename) as csvfile:
        data = csv.DictReader(csvfile)
        for row in data:
            try:
                get_game(row, site, à_vendre)
            except (ValueError, IntegrityError, ValidationError, TypeError) as e:
                print(row["Jeux"])
                error_games.append((row["N° réf"], row["Jeux"], e))
                continue
        with open("errors.txt", "w") as fd:
            for number, name, exception in error_games:
                fd.write("********************\n")
                fd.write(str(number))
                fd.write("\n")
                fd.write(name + "\n")
                fd.write(str(exception))
                fd.write("\n")


def get_csv(model_to_extract=Game, file_name=""):
    if file_name == "":
        file_name = f"data-{ model_to_extract.__name__ }.csv"
    buffer = model_to_extract.extract_data()
    buffer.seek(0)

    if file_name is not None:
        with open(file_name, "w") as file:
            shutil.copyfileobj(buffer, file)
    else:
        return buffer
