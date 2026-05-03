from django import forms
import datetime
from copy import copy

from games.models import Game, COL_CHOICES, COL_SUB, Comment, GAME_TYPE_CHOICES

class UnicornTextInputWidget(forms.TextInput):
    """
    Define django TextInput widget with applied tailwind classes.
    """
    def __init__(self):
        super().__init__(attrs={
            "class": "text-zinc-200 bg-zinc-800 input"
        })

class UnicornSelectWidget(forms.Select):
    """
    Define django Select widget with applied tailwind classes.
    """
    def __init__(self):
        super().__init__(attrs={
            "class": "text-zinc-200 bg-zinc-800 select"
        })

class UnicornSelectMultipleWidget(forms.SelectMultiple):
    """
    Define django SelectMultiple widget with applied tailwind classes.
    """
    def __init__(self):
        super().__init__(attrs={
            "class": "text-zinc-200 bg-zinc-800 select"
        })

class UnicornTextAreaWidget(forms.Textarea):
    """
    Define django TextArea widget with applied tailwind classes.
    """
    def __init__(self):
        super().__init__(attrs={
            "class": "text-zinc-800 bg-zinc-200 textarea w-full border-1 border-solid border-zinc-800"
        })

class GameFilterForm(forms.Form):
    games_by_page = forms.CharField(
        label="Nombre de jeux par pages",
        max_length=3,
        widget=forms.TextInput(attrs={"class": "input"})
    )
    name = forms.CharField(label="Nom du jeu", max_length=200)

class InventoryFilterForm(forms.Form):
    """
    Form to filter games in inventory selecting view.
    """
    def __init__(self, locations, labels, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"] = forms.CharField(max_length=100, required=False, label="Nom du jeu", widget=UnicornTextInputWidget)
        self.fields["game_type"] = forms.ChoiceField(choices=GAME_TYPE_CHOICES, required=False, label="Type de jeu", widget=UnicornSelectWidget)
        self.fields["min_number"] = forms.IntegerField(min_value=1,max_value=2000, required=False, label="Numéro minimal du jeu", widget=UnicornTextInputWidget)
        self.fields["max_number"] = forms.IntegerField(min_value=1,max_value=2000, required=False, label="Numéro maximal du jeu", widget=UnicornTextInputWidget)
        locations_choices = [(x.name,x.name) for x in locations]
        locations_choices.insert(0,("", "---"))
        self.fields["location"] = forms.ChoiceField(required=False, label="Localisation", choices=locations_choices, widget=UnicornSelectWidget)
        min_year = 2013
        current_year = datetime.date.today().year
        years = list(map(lambda x: (x,x),range(min_year,current_year)))
        years.insert(0, ("", "---"))
        self.fields["min_entry_year"] = forms.ChoiceField(choices=years, required=False, label="Année minimum", widget=UnicornSelectWidget)
        self.fields["max_entry_year"] = forms.ChoiceField(choices=years, required=False, label="Année maximum", widget=UnicornSelectWidget)
        labels_choices = [(x.label,x.label) for x in labels]
        self.fields["labels"] = forms.MultipleChoiceField(choices=labels_choices, required=False, label="Labels", widget=UnicornSelectMultipleWidget)
        self.fields["labels_to_exclude"] = forms.MultipleChoiceField(choices=labels_choices, required=False, label="Labels à exclure", widget=UnicornSelectMultipleWidget)

class BatchForm(forms.Form):
    """
    Form to change attributes in batch of selected games.
    """
    def __init__(self, locations, labels, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels_choices = [(x.label,x.label) for x in labels]
        self.fields["labels"] = forms.MultipleChoiceField(choices=labels_choices, required=False, label="Labels à ajouter", widget=UnicornSelectMultipleWidget)
        self.fields["labels_to_remove"] = forms.MultipleChoiceField(choices=labels_choices, required=False, label="Labels à retirer", widget=UnicornSelectMultipleWidget)
        locations = [(x.name,x.name) for x in locations]
        locations.insert(0,("", "---"))
        self.fields["location"] = forms.ChoiceField(required=False, label="Localisation", choices=locations, widget=UnicornSelectWidget)

class GameNameWidget(forms.TextInput):
    """
    Define game name TextInput widget.
    """
    def __init__(self):
        super().__init__(attrs={
            "class": "text-zinc-800 input border-orange-500 border-2 mt-2 mb-2 text-xl font-black m-auto block bg-zinc-200",
            "placeholder": "Nom du jeu",
        })

class MyludoPathWidget(forms.TextInput):
    """
    Define myludo_path TextInput widget.
    """
    def __init__(self):
        super().__init__(attrs={
            "class": "text-zinc-800 bg-zinc-200",
            "placeholder": "#!/game/12345",
        })

class ImageWidget(forms.FileInput):
    """
    Define image FileInput widget.
    """
    def __init__(self):
        super().__init__(attrs={
            "class": "text-zinc-950 bg-zinc-200 file-input",
        })

class GameForm(forms.ModelForm):
    template_name="games/GameForm.html"
    class Meta:
        model = Game
        localized_fields = "__all__"
        fields = [
                    "name",
                    "games_library_categorization",
                    "adapted_games_library_categorization_1",
                    "adapted_games_library_categorization_2",
                    "time",
                    "players_number",
                    "details",
                    "entry_year",
                    "number",
                    "price",
                    "year",
                    "myludo_path",
                    "cards_number",
                    "cards_size",
                    "origin",
                    "qrcode",
                    "image",
                    "age",
                    "themes",
                    "game_type",
                    "last_inventory_date",
                    "rules_video_link",
                    "for_child",
                    "missing_items",
                    "inventory",
                    "location",
                    "illustrators",
                    "authors",
                    "mechanisms",
                    "editors",
                    "labels",
        ]
        form_col_choices = copy(COL_CHOICES)
        form_col_choices.insert(0,("", "---"))
        form_col_sub = copy(COL_SUB)
        form_col_sub.insert(0, ("", "---"))
        games_library_categorization = forms.ChoiceField(required=False, choices=form_col_choices, widget=UnicornSelectWidget())
        adapted_games_library_categorization_1 = forms.ChoiceField(required=False, choices=form_col_sub, widget=UnicornSelectWidget())
        adapted_games_library_categorization_2 = forms.ChoiceField(required=False, choices=form_col_sub, widget=UnicornSelectWidget())
        labels = {
            "price": "prix",
            "last_inventory_date": "dernière date d’inventaire",
            "name": "nom",
            "games_library_categorization": "COL",
            "adapted_games_library_categorization_1": "COL adapté 1",
            "adapted_games_library_categorization_2": "COL adapté 2",
            "time": "durée",
            "players_number": "nombres joueurs",
            "details": "description",
            "entry_year": "année d’obtention",
            "number": "numéro",
            "year": "année",
            "myludo_path": "chemin myludo",
            "cards_number": "Nombre de cartes",
            "cards_size": "Taille des cartes",
            "origin": "Origine",
            "age": "âge conseillé",
            "themes": "thèmes",
            "game_type": "type de jeu",
            "rules_video_link": "lien vidéo règles",
            "for_child": "Pour enfants",
            "missing_items": "pièces manquantes",
            "inventory": "inventaire",
            "location": "localisation",
            "illustrators": "illustrateurs",
            "authors": "auteurs",
            "mechanisms": "mécanismes",
            "editors": "éditeurs",
        }
        widgets = {
            "name": GameNameWidget(),
            "number": forms.TextInput(),
            "price": forms.TextInput(),
            "details": UnicornTextAreaWidget(),
            "year": forms.TextInput(),
            "myludo_path": MyludoPathWidget(),
            "image": ImageWidget(),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = [
            "text",
        ]
        labels = {
            "text": "texte",
        }
        widgets = {
            "text": UnicornTextAreaWidget(),
        }

CommentForms = forms.modelformset_factory(Comment, form=CommentForm, extra=0, can_delete=True)
