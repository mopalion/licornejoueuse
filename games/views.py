from django.shortcuts import render, get_object_or_404, redirect
from django.utils.text import slugify
from django.db.utils import IntegrityError
import csv
import segno
from datetime import datetime

from .models import Game,Location

def index(request, game_type="boardgame"):
    games = Game.objects.filter(game_type=game_type).order_by("number")[:]
    context = {}
    context["games"] = games
    return render(request, "games/index.html", context)

def location_index(request):
    context = {}
    context["locations"] = Location.objects.all()[:]
    return render(request, "games/location_index.html", context)

def detail(request, number):
    game = get_object_or_404(Game, number=number)
    context = {"game": game}
    return render(request, "games/game.html", context)

def location_detail(request, name):
    context = {}
    context["location"] = get_object_or_404(Location, name=name)

    return render(request, "games/location_detail.html", context)

def generate_qrcode(request, number):
    game = get_object_or_404(Game, number=number)
    qrcode = segno.make(f"{game.title} - {game.number}")
    filename = f"medias/qrcode/{slugify(game.title)}_{game.number}.png"
    qrcode.save(filename, scale=5, border=0)
    game.qrcode.name = filename
    game.save()
    context = {"game": game}
    return redirect("detail", number=game.number)


def delete_games():
    games = Game.objects.all()
    for game in games:
        game.delete()

def load_data(csvfilename):
    local = Location.objects.all()[0]
    with open(csvfilename) as csvfile:
        data = csv.DictReader(csvfile)
        for row in data:
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
            try:
                game = Game(
                    title=row["Jeux"],
                    details="",
                    add_date=datetime.strptime("01-01-1970" if row["Date d'entrée"] == "" else row["Date d'entrée"],"%d-%m-%Y"),
                    number=row["N° réf"],
                    location=local,
                    state=row["Etat"],
                    age=0 if row["Âge"] == "" else row["Âge"],
                    theme=row["Thème"],
                    token=100 if row["Jeton(s)"] == "" else row["Jeton(s)"],
                    to_sold= True if row["A vendre?"] == "oui" else False,
                    game_type=game_type,
                )
                game.save()
            except (ValueError, IntegrityError):
                print(row["Jeux"])
                continue
