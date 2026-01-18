import csv
from datetime import datetime, date
from .models import Game, Location, Label, Author, Illustrator, Mechanism, Comment
import requests
from os import makedirs
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
import re

def delete_games():
    games = Game.objects.all()
    for game in games:
        game.delete()

def cast_date(string):
    if string != "":
        date_res = datetime.strptime(string.strip().replace(" ","-").replace("/","-").replace(".","-"),"%d-%m-%Y")
    else:
        date_res = datetime.strptime("01-01-1970","%d-%m-%Y")
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
        adapted_games_library_categorization=row["COL adapté"],
        time=row["Duree"],
        players_number=row["Nbre de joueurs"],
        add_date=cast_date(row["Date d'entrée"]),
        price=float(row["Prix neuf"].replace(",",".")),
        number=row["N° réf"],
        location=site,
        state=row["Etat"],
        cards_number=row["Nbre de cartes"] if row["Nbre de cartes"] != "" else 0,
        cards_size=row["Dimension cartes"],
        origin=row["don provenance?"],
        trictrac_link=row["trictrac"],
        year=row["annee"] if row["annee"] != "" else 0,
        editor=row["editeur"],
        age=0 if row["Âge"] == "" else row["Âge"],
        theme=row["Thème"],
        token=100 if row["Jeton(s)"] == "" else row["Jeton(s)"],
        game_type=game_type,
        last_inventory_date=cast_date(row["dernier inventaire"]),
        rules_video_link=row["liens vers video régles"],
        image="medias/games_images/spirit_island.jpg"
    )
    game.save()
    if row["A vendre?"] == "oui":
        game.labels.add(à_vendre)
    if row["illustrateur"] != "":
        illustrators = Illustrator.objects.filter(name=row["illustrateur"])
        if not illustrators:
            illustrator = Illustrator(name=row["illustrateur"])
            illustrator.save()
        else:
            illustrator = illustrators[0]
        game.illustrators.add(illustrator)
    if row["auteur"] != "":
        authors = Author.objects.filter(name=row["auteur"])
        if not authors:
            author = Author(name=row["auteur"])
            author.save()
        else:
            author = authors[0]
        game.authors.add(author)
    if row["mécanisme"] != "":
        for mechanism_name in row["mécanisme"].split(","):
            mechanisms = Mechanism.objects.filter(name=mechanism_name.split())
            if not mechanisms:
                mechanism = Mechanism(name=mechanism_name.split())
                mechanism.save()
            else:
                mechanism = mechanisms[0]
            game.mechanisms.add(mechanism)
    if row["Commentaires"] != "":
        game.comment_set.create(text=row["Commentaires"], created_date=cast_date(""))
    if row["Manque"] != "":
        game.comment_set.create(text="MANQUE: "+row["Commentaires"], created_date=cast_date(""))
    if row["Inventaire"] != "":
        game.comment_set.create(text="INVENTAIRE: "+row["Commentaires"], created_date=cast_date(""))

def load_data(csvfilename):
    locations = Location.objects.all()
    if len(locations) == 0:
        site = Location(name="Local")
        site.save()
    else:
        site = locations[0]
    labels = Label.objects.filter(label="À vendre")
    if len(labels) == 0:
        à_vendre = Label(label="À vendre")
        à_vendre.save()
    else:
        à_vendre = labels[0]


    total_games = 869
    current_games = 0
    partial_games = 0
    error_games = []
    r = requests.get("https://www.myludo.fr/img/jeux/1758963873/jpg/bd/29983.jpg", allow_redirects=True)
    makedirs("medias/games_images", exist_ok=True)
    with open("medias/games_images/spirit_island.jpg", "wb") as fd:
        fd.write(r.content)
    with open(csvfilename) as csvfile:
        data = csv.DictReader(csvfile)
        for row in data:
            try:
                get_game(row, site, à_vendre)
            except (ValueError, IntegrityError, ValidationError, TypeError) as e:
                print(row["Jeux"])
                error_games.append(row["Jeux"])
                print(e)
                continue
            current_games += 1
    partial = len(Game.objects.all()) - current_games
    print(f"Jeux ok : {current_games}")
    print(f"Jeux partiel ok : {partial}")
    print(f"Jeux en erreurs : {len(error_games)}")
    print(f"Pourcentage de réussite : {current_games*100/total_games}")

