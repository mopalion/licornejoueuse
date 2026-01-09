from django import forms

class GameFilterForm(forms.Form):
    games_by_page = forms.CharField(
        label="Nombre de jeux par pages",
        max_length=3,
        widget=forms.TextInput(attrs={"class": "input"})
    )
