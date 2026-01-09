from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.utils.text import slugify
from django.db.utils import IntegrityError
import csv
import segno
from datetime import datetime
from .forms import GameFilterForm

from .models import Game,Location

def index(request, game_type="boardgame", page_number=1):
    parameters = ""
    if request.GET:
        filter_form = GameFilterForm(request.GET)
        if filter_form.is_valid():
            games_by_page  = int(filter_form.cleaned_data["games_by_page"])
            first_parameter = True
            for k,v in filter_form.cleaned_data.items():
                if first_parameter:
                    parameters += "?"
                    first_parameter = False
                else:
                    parameters += "&"
                parameters += f"{k}={v}"
        else:
            filter_form = GameFilterForm()
    else:
        filter_form = GameFilterForm()
    if 'games_by_page' not in locals():
        games_by_page = 9
    games = Game.objects.filter(game_type=game_type).order_by("number")[:]
    pagination = Paginator(games, games_by_page)
    page = pagination.page(page_number)

    match game_type:
        case "boardgame":
            path = "numbered_index"
        case "wooden":
            path = "numbered_wooden_index"
        case "rpg":
            path = "numbered_rpg_index"
        case "toys":
            path = "numbered_toys_index"
    context = {
        "games" : page.object_list,
        "pagination" : {
            "previous": page.previous_page_number() if page.has_previous() else None,
            "next": page.next_page_number() if page.has_next() else None,
            "number": page_number,
            "max": pagination.num_pages,
        },
        "path" : path,
        "filter_form" : filter_form,
        "parameters": parameters
    }
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
