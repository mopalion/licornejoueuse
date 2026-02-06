from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.utils import IntegrityError
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
import segno
from .forms import GameFilterForm,InventoryFilterForm, BatchForm, GameForm
from os import makedirs
import requests
from .tools import generate_label_sheets
from PIL import Image, ImageDraw, ImageFont

from .models import Game,Location, Comment, Label

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

def generate_game_csv(request):
    file = Game.extract_data()
    file.seek(0)
    
    response = HttpResponse(
        file,
        content_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="licorne_game_data.csv"'
        } 
    )
    return response

def generate_comment_csv(request):
    file = Comment.extract_data()
    file.seek(0)
    
    response = HttpResponse(
        file,
        content_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="licorne_comment_data.csv"'
        } 
    )
    return response

@login_required
def inventory_index(request):
    """
    Root request to actions or selecting games views.

    Args:
        request: Django Request object.
    Returns:
        result of rooted view
    """
    if request.method == "POST":
        if "actions" in request.POST and request.POST["actions"]:
            match request.POST["actions"]:
                case "batch":
                    return batch(request)
                case "print_labels":
                    return print_labels(request)
    return select_games(request)

@login_required
def batch(request):
    """
    Modify selected games in batch.

    Args:
        request: Django Request object.
    Returns:
        the form to select attributes to change or redirect to inventory page if attributes was modified.
    """
    form = BatchForm(Location.objects.all(), Label.objects.all())
    selected_games = []
    for selected_game in filter(lambda x: x[0].startswith("selected-game-") and "on" in x[1], request.POST.items()):
        selected_games.append(int(selected_game[0].replace("selected-game-","")))
    if selected_games == []:
        return redirect("inventory_index")
    games = Game.objects.filter(number__in=selected_games)
    if "go" in request.POST:
        for game in games:
            if "labels" in request.POST and request.POST["labels"]:
                for label_name in request.POST.getlist("labels"):
                    label = Label.objects.filter(label=label_name)[0]
                    game.labels.add(label)
            if "location" in request.POST and request.POST["location"]:
                location = Location.objects.get(name=request.POST["location"])
                game.location = location
                game.save()
        return redirect("inventory_index")
    context = {
        "selected_games": games,
        "selected_games_ids": map(lambda x: x.number, games),
        "form": form,
    }
    return render(request, "games/batch.html", context)
    
@login_required
def print_labels(request):
    """
    Create pdf with labels of each selected games.

    Args:
        request: Django Request object.
    Returns:
        the pdf file to print selected games’s labels.
    """
    selected_games = []
    for selected_game in filter(lambda x: x[0].startswith("selected-game-") and "on" in x[1], request.POST.items()):
        selected_games.append(int(selected_game[0].replace("selected-game-","")))
    if selected_games == []:
        return redirect("inventory_index")

    games = Game.objects.filter(number__in=selected_games)

    pdf = generate_label_sheets(games)
    pdf.seek(0)
    
    response = HttpResponse(
        pdf,
        content_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="etiquettes_licorne.pdf"'
        } 
    )
    return response
    return render(request, "games/batch.html", context)
    
def select_games(request):
    """
    Allow user to select games.

    Args:
        request: Django Request object.
    Returns:
        the form to select games.
    """
    games = None
    selected_games = set()
    current_selected_games = set()
    if request.method == "POST":


        for selected_game in filter(lambda x: x[0].startswith("selected-game-") and "on" in x[1], request.POST.items()):
            selected_games.add(int(selected_game[0].replace("selected-game-","")))

        form = InventoryFilterForm(Location.objects.all(), Label.objects.all(), request.POST)
        if form.is_valid():
            # Apply differents filters to games.
            if "name" in form.cleaned_data and form.cleaned_data["name"]:
                if games is None:
                    games = Game.objects
                games = games.filter(name__icontains=form.cleaned_data["name"])
            if "min_number" in form.cleaned_data and form.cleaned_data["min_number"]:
                if games is None:
                    games = Game.objects
                games = games.filter(number__gte=form.cleaned_data["min_number"])
            if "max_number" in form.cleaned_data and form.cleaned_data["max_number"]:
                if games is None:
                    games = Game.objects
                games = games.filter(number__lte=form.cleaned_data["max_number"])
            if "location" in form.cleaned_data and form.cleaned_data["location"]:
                if games is None:
                    games = Game.objects
                games = games.filter(location__name=form.cleaned_data["location"])
            if "min_entry_year" in form.cleaned_data and form.cleaned_data["min_entry_year"]:
                if games is None:
                    games = Game.objects
                games = games.filter(entry_year__gte=form.cleaned_data["min_entry_year"])
            if "max_entry_year" in form.cleaned_data and form.cleaned_data["max_entry_year"]:
                if games is None:
                    games = Game.objects
                games = games.filter(entry_year__lte=form.cleaned_data["max_entry_year"])
            if "labels" in form.cleaned_data and form.cleaned_data["labels"]:
                if games is None:
                    games = Game.objects
                for label in form.cleaned_data["labels"]:
                    games = games.filter(labels__label=label)

    else:
        form = InventoryFilterForm(Location.objects.all(), Label.objects.all())

    if games is None:
        games = Game.objects.all()

    # Allow to save selected games in previous filters.
    for game in games:
        if game.number in selected_games:
            current_selected_games.add(game.number)
            selected_games.remove(game.number)
    selected_games_to_display = Game.objects.filter(number__in=selected_games)

    context = {
        "games": games,
        "filter_form": form,
        "selected_games": selected_games,
        "selected_games_to_display": selected_games_to_display,
        "current_selected_games": current_selected_games,
    }
    return render(request, "games/inventory_index.html", context)

@login_required
def update_game(request, number):
    """
    Allow user to update a game. Update game if post data was sent.

    Args:
        request: Django Request object.
        int: number of the game to edit
    Returns:
        the form to edit the game.
    """
    game = Game.objects.get(number=number)
    errors = []
    if request.method == "POST":
        form = GameForm(request.POST, request.FILES, instance=game)
        if form.is_valid():
                
            form.save()
            return redirect("game_added", game.number)
        else:
            for error in form.errors.items():
                detailed_error = (form.fields[error[0]].label, error[1])
                form.errors[error[0]] = detailed_error
    else:
        form = GameForm(instance=Game.objects.get(number=number))
    context = {
        "game": game,
        "form": form,
        "errors": errors,
    }
    return render(request, "games/update_game.html", context)

@login_required
def game_added(request, number):
    """
    Display that a game was modified/added.

    Args:
        request: Django Request object.
        int: Number of the game that was added or updated.
    Returns:
        The confirmation of the upgrade.
    """

    game = Game.objects.get(number=number)
    return render(request, "games/game_added.html", {"game": game})
