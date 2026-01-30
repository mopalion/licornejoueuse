from django import forms
from django.db.models import Min
import datetime

class UnicornTextInputWidget(forms.TextInput):
    """
    Define django TextInput widget with applied tailwind classes.
    """
    def __init__(self):
        super().__init__(attrs={
            "class": "text-zinc-800 input"
        })

class UnicornSelectWidget(forms.Select):
    """
    Define django Select widget with applied tailwind classes.
    """
    def __init__(self):
        super().__init__(attrs={
            "class": "text-zinc-800 select"
        })

class UnicornSelectMultipleWidget(forms.SelectMultiple):
    """
    Define django SelectMultiple widget with applied tailwind classes.
    """
    def __init__(self):
        super().__init__(attrs={
            "class": "text-zinc-800 select"
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

class BatchForm(forms.Form):
    """
    Form to change attributes in batch of selected games.
    """
    def __init__(self, locations, labels, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels_choices = [(x.label,x.label) for x in labels]
        self.fields["labels"] = forms.MultipleChoiceField(choices=labels_choices, required=False, label="Labels", widget=UnicornSelectMultipleWidget)
        locations = [(x.name,x.name) for x in locations]
        locations.insert(0,("", "---"))
        self.fields["location"] = forms.ChoiceField(required=False, label="Localisation", choices=locations, widget=UnicornSelectWidget)
