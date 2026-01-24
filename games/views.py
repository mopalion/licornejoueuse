from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.utils import IntegrityError
from .forms import GameFilterForm
from os import makedirs
import requests
from .tools import generate_qrcode
from PIL import Image, ImageDraw, ImageFont


from .models import Game,Location

def generate_parameters(parameters):
    get_parameters = ""
    first_parameter = True
    for k,v in parameters.items():
        if first_parameter:
            get_parameters += "?"
            first_parameter = False
        else:
            get_parameters += "&"
        get_parameters += f"{k}={v}"
    return get_parameters


def index(request, game_type="boardgame"):
    parameters = {}
    if 'page' in request.GET:
        page_number = int(request.GET["page"])
    else:
        page_number = 1
    if 'games_by_page' in request.GET:
        games_by_page  = int(request.GET["games_by_page"])

    if request.GET:
        filter_form = GameFilterForm(request.GET)
        if filter_form.is_valid():
            if 'name' in filter_form.cleaned_data and filter_form.cleaned_data['name']:
                games = Game.objects.filter(game_type=game_type, name__contains=filter_form.cleaned_data['name'])
            for k,v in filter_form.cleaned_data.items():
                parameters[k] = v
        else:
            filter_form = GameFilterForm()
    else:
        filter_form = GameFilterForm()
    if 'games_by_page' not in locals():
        games_by_page = 9
    if 'games' not in locals():
        games = Game.objects.filter(game_type=game_type).order_by("number")[:]
    pagination = Paginator(games, games_by_page)
    page = pagination.page(page_number)

    match game_type:
        case "boardgame":
            path = "index"
        case "wooden":
            path = "wooden_index"
        case "rpg":
            path = "rpg_index"
        case "toys":
            path = "toys_index"
    if page.has_previous():
        parameters["page"] = page.previous_page_number()
        previous_parameters = generate_parameters(parameters)
    else:
        previous_parameters = None
    if page.has_next():
        parameters["page"] = page.next_page_number()
        next_parameters = generate_parameters(parameters)
    else:
        next_parameters = None
    context = {
        "games" : page.object_list,
        "pagination" : {
            "previous": page.previous_page_number() if page.has_previous() else None,
            "previous_parameters": previous_parameters,
            "next": page.next_page_number() if page.has_next() else None,
            "next_parameters": next_parameters,
            "number": page_number,
            "max": pagination.num_pages,
        },
        "path" : path,
        "filter_form" : filter_form,
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

def toto():
    toto = [4,9,42,471,792,829,2222]
    games = []
    images = []
    for nb in toto:
        game = Game.objects.filter(number=nb)[0]
        games.append(game)
        filename = generate_qrcode(game)
        img = Image.open(filename)
        rgb = Image.new('RGB', img.size, (255,255,255))
        rgb.paste(img, mask=img.split()[3])
        images.append(rgb)
    images[0].save("toto.pdf", 'PDF', resolution=100.00, save_all=True, append_images=images[1:])



