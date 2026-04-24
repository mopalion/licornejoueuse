from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.utils import IntegrityError
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db.models import Max
import segno
from .forms import GameFilterForm,InventoryFilterForm, BatchForm, GameForm, CommentForm, CommentForms
from os import makedirs
import requests
from .tools import generate_label_sheets
from PIL import Image, ImageDraw, ImageFont
from datetime import date, datetime
from hashlib import sha512
import pickle
from itertools import chain

from .models import Game,Location, Comment, Label
from .data import get_csv

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
    file = get_csv(file_name=None)
    
    response = HttpResponse(
        file,
        content_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="licorne_game_data.csv"'
        } 
    )
    return response

def generate_comment_csv(request):
    file = get_csv(model_to_extract=Comment, file_name=None)
    
    response = HttpResponse(
        file,
        content_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="licorne_comment_data.csv"'
        } 
    )
    return response

def get_selected_games(post_data):
    selected_games = set()

    for selected_game in filter(lambda x: x[0].startswith("selected-game-") and "on" in x[1], post_data.items()):
        selected_games.add(int(selected_game[0].replace("selected-game-","")))

    if "selected_games" in post_data and post_data["selected_games"] != "":
        for game_id in post_data["selected_games"].split(","):
            selected_games.add(int(game_id))
    
    return selected_games

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
    locations = Location.objects.all()
    labels = Label.objects.all()
    selected_games = get_selected_games(request.POST)
    modifications = {"lists": {}, "values": {}}
    modifications_hash = ""

    if selected_games == []:
        return redirect("inventory_index")
    games = Game.objects.filter(number__in=selected_games)

    if "go" in request.POST:

        object_modification = False
        labels_modifications = []
        if "labels" in request.POST and request.POST["labels"]:
            for label_name in request.POST.getlist("labels"):
                labels_modifications.append(label_name)
            modifications["lists"]["labels à ajouter"] = labels_modifications
        labels_modifications = []
        if "labels_to_remove" in request.POST and request.POST["labels_to_remove"]:
            for label_name in request.POST.getlist("labels_to_remove"):
                labels_modifications.append(label_name)
                modifications["lists"]["labels à retirer"] = labels_modifications
        if "location" in request.POST and request.POST["location"]:
            location = Location.objects.get(name=request.POST["location"])
            modifications["values"]["Localisation"] = location.name
            object_modification = True

        modifications_hash = sha512(pickle.dumps(modifications)).hexdigest()
        
        if modifications_hash == request.POST["modifications_hash"]:
            for game in games:
                if object_modification:
                    game.location = location
                    game.save()
                if "labels à ajouter" in modifications["lists"]:
                    for label_name in modifications["lists"]["labels à ajouter"]:
                        label = Label.objects.get(label=label_name)
                        game.labels.add(label)
                if "labels à retirer" in modifications["lists"]:
                    for label_name in modifications["lists"]["labels à retirer"]:
                        label = Label.objects.get(label=label_name)
                        game.labels.remove(label)

            return redirect("inventory_index")

        initial_values = {}
        if "labels à ajouter" in modifications["lists"]:
            initial_values["labels"] = modifications["lists"]["labels à ajouter"]
        if "labels à retirer" in modifications["lists"]:
            initial_values["labels_to_remove"] = modifications["lists"]["labels à retirer"]
        if "Localisation" in modifications["values"]:
            initial_values["location"] = modifications["values"]["Localisation"]

        form = BatchForm(
            locations,
            labels,
            initial = initial_values,
        )
    else:
        form = BatchForm(locations, labels)

    context = {
        "selected_games": games,
        "selected_games_ids": map(lambda x: x.number, games),
        "form": form,
        "modifications": modifications,
        "modifications_hash": modifications_hash,
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
    selected_games = get_selected_games(request.POST)

    if not selected_games:
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

        selected_games = get_selected_games(request.POST)

        if "save_btn" in request.POST:
            request.session["selected_games"] = list(selected_games)
        if "load_btn" in request.POST and "selected_games" in request.session:
            selected_games = set(request.session["selected_games"])
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
            if "labels_to_exclude" in form.cleaned_data and form.cleaned_data["labels_to_exclude"]:
                if games is None:
                    games = Game.objects
                for label in form.cleaned_data["labels_to_exclude"]:
                    games = games.exclude(labels__label=label)

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

    # Prepare shortcuts links
    shortcuts = []
    if games:
        i_games = iter(games)
        for hundred in range(0,999,100):
            quarts = []
            for quart in range(hundred, hundred +99, 25):
                while True:
                    try:
                        game = next(i_games)
                    except StopIteration:
                        break
                    value = game.number
                    if value >= quart:
                        break
                quarts.append((quart, value))

            shortcuts.append(quarts)

    context = {
        "games": games,
        "filter_form": form,
        "selected_games": selected_games,
        "selected_games_to_display": selected_games_to_display,
        "current_selected_games": current_selected_games,
        "shortcuts": shortcuts,
    }
    return render(request, "games/inventory_index.html", context)

@login_required
def update_game(request, number):
    """
    First call : display a form to update the game of number number

    Second call: if form is valid, display modifications in top of the page and ask confirmation
    Third call : update the game of number number and redirect to game_added

    Args:
        request: Django Request object.
        int: number of the game to edit
    Returns:
        the form to edit the game.
    """
    game = Game.objects.get(number=number)
    errors = []
    comments_errors = []
    modifications = []
    modifications_hash = ""

    if request.method == "POST":

        comments_forms = CommentForms(request.POST)
        if comments_forms.is_valid():
            if comments_forms.has_changed():
                modifications.append("Au moins un commentaire a été modifié.")
            comments_form_is_valid = True
        else:
            comments_errors = comments_forms.errors
            comments_form_is_valid = False

        updated_game = Game.objects.get(number=number)
        form = GameForm(request.POST, request.FILES, instance=updated_game)
        if form.is_valid():
            # we get modifications on all fields except many_to_many relationships
            for field in filter(lambda x: x not in ["id"], map(lambda x: x.name,Game._meta.fields)):
                if field == "image":
                    if "image" in request.FILES:
                        #modifications.append(f"{field} => {getattr(updated_game, field).name}")
                        pass
                else:
                    if getattr(updated_game, field) != getattr(game, field) and (getattr(updated_game, field) is not None or getattr(game, field) != ""):
                        modifications.append(f"{form.fields[field].label} => {getattr(updated_game, field)}")

            # we get modifications on many_to_many relationships
            for field in filter(lambda x: x not in ["id"], map(lambda x: x.name, Game._meta.many_to_many)):
                new_items = request.POST.getlist(field)
                items_to_remove = []
                for item in getattr(game, field).all():
                    if str(item.id) not in new_items:
                        items_to_remove.append(item)
                    else:
                        new_items.remove(str(item.id))
                items_to_add = getattr(game, field).model.objects.filter(id__in=map(lambda x: int(x), new_items))

                if items_to_add or items_to_remove:
                    modification = f"{form.fields[field].label} => "
                    for item in items_to_add:
                        modification += f"+{item.name}"
                    for item in items_to_remove:
                        modification += f"-{item.name}"
                    modifications.append(modification)


            form_is_valid = True
        else:
            for error in form.errors.items():
                detailed_error = (form.fields[error[0]].label, error[1])
                form.errors[error[0]] = detailed_error
            form_is_valid = False

        modifications_hash = sha512(pickle.dumps(modifications)).hexdigest()
        if comments_form_is_valid and form_is_valid and modifications_hash == request.POST["modifications_hash"]:
            comments_forms.save()
            form.save()
            return redirect("game_added", updated_game.number)

    else:
        form = GameForm(instance=Game.objects.get(number=number))
        comments_forms = CommentForms(queryset=Comment.objects.filter(game=game))

    context = {
        "game": game,
        "form": form,
        "comments_forms": comments_forms,
        "errors": errors,
        "comments_errors": comments_errors,
        "modifications": modifications,
        "modifications_hash": modifications_hash,
    }
    return render(request, "games/update_game.html", context)


@login_required
def add_game(request):
    """
    Allow user to add a new game. Create game if post data was sent.

    Args:
        request: Django Request object.
    Returns:
        the form to edit the game.
    """
    errors = []
    new_number = Game.objects.aggregate(Max('number'))["number__max"] + 1
    if request.method == "POST":
        form = GameForm(request.POST, request.FILES)
        if form.is_valid():
                
            game = form.save()
            return redirect("game_added", game.number)
        else:
            for error in form.errors.items():
                detailed_error = (form.fields[error[0]].label, error[1])
                form.errors[error[0]] = detailed_error
    else:
        default_values = {
            "number": new_number,
        }
        form = GameForm()
        form.fields["number"].initial = new_number
        form.fields["entry_year"].initial = date.today().year
    context = {
        "form": form,
        "errors": errors,
    }
    return render(request, "games/new_game.html", context)

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

@login_required
def new_comment(request, number):
    """
    Add a new comment for the game with indicated number

    Args:
        request: Django Request object,
        int: Number of the game that received new comment
    Returns:
        The form to add a new comment
    """
    form = None

    game = Game.objects.get(number=number)

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.created_date = datetime.now()
            comment.game = game
            comment.save()
            return redirect("comment_added")

    if form is None:
        form = CommentForm()
    return render(request, "games/new_comment.html", {"game": game, "form": form})

@login_required
def comment_added(request):
    """
    Display that a comment was added.

    Args:
        request: Django Request object.
    Returns:
        The confirmation of the upgrade.
    """

    return render(request, "games/comment_added.html")

@login_required
def delete_game(request, number):
    """
    Propose to delete the game with number number

    Args:
        request: Django Request object.
        number: number of game to delete
    Returns:
        The delete page or redirect if game is deleted
    """
    game = Game.objects.get(number=number)
    if request.method == "POST":
        game.delete()
        return redirect("game_deleted")
    return render(request, "games/delete_game.html", {"game": game})

@login_required
def game_deleted(request):
    """
    Validate the deletion of a game

    Args:
        request: Django Request object.
    Returns:
        The validation of deleted game page
    """
    return render(request, "games/game_deleted.html")
