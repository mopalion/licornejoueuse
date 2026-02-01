from django.db import models
from io import StringIO
from datetime import date
from .tools import generate_qrcode

class Location(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Author(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name}"

class Illustrator(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name}"

class Editor(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name}"

class Mechanism(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name}"

class Label(models.Model):
    label = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.label}"

class Theme(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name}"

def csv_sanitize(value):
    if type(value) == type(True):
        if value == True:
            value = "oui"
        else:
            value = "non"
    elif type(value) == type(date.today()):
        value = value.strftime('%d/%m/%y')
    return f"\"{str(value)}\""

class Game(models.Model):
    name = models.CharField(max_length=200, blank=False)
    games_library_categorization = models.CharField(max_length=10, blank=True)
    adapted_games_library_categorization_1 = models.CharField(max_length=10, blank=True)
    adapted_games_library_categorization_2 = models.CharField(max_length=10, blank=True)
    time = models.CharField(max_length=10, blank=True)
    players_number = models.CharField(max_length=10, blank=True)
    details = models.TextField(blank=True)
    entry_year = models.PositiveIntegerField(blank=False, null=False)
    number = models.PositiveIntegerField("Number", blank=False, unique=True)
    price = models.FloatField(blank=True, null=True)
    year = models.PositiveIntegerField(blank=True, null=True)
    myludo_path = models.CharField(max_length=200, blank=True, null=True)
    cards_number = models.PositiveIntegerField(blank=True,null=True)
    cards_size = models.CharField(max_length=40, blank=True)
    origin = models.CharField(max_length=100, blank=True, null=True)
    qrcode = models.ImageField(upload_to="medias/qrcode", blank=True)
    image = models.ImageField(upload_to="medias/games_images", blank=True)
    age = models.CharField(max_length=10)
    game_type = models.CharField(max_length=20, default="boardgame", choices=[("boardgame","jds"), ("rpg","jdr"), ("wooden", "bois"), ("toys", "jouet")])
    last_inventory_date = models.DateField("last inventory date", blank=True, null=True)
    rules_video_link = models.CharField(max_length=100, blank=True, null=True)
    for_child = models.BooleanField()
    missing_items = models.TextField(blank=True, null=True)
    inventory = models.TextField(blank=True)


    location = models.ForeignKey(Location, on_delete=models.PROTECT, blank=False)
    illustrators = models.ManyToManyField(Illustrator, blank=True)
    authors = models.ManyToManyField(Author, blank=True)
    mechanisms = models.ManyToManyField(Mechanism, blank=True)
    editors = models.ManyToManyField(Editor, blank=True)
    labels = models.ManyToManyField(Label, blank=True)
    themes = models.ManyToManyField(Theme, blank=True)

    def __str__(self):
        return f"{self.name}({self.number})"

    def csv_data(self):
        labels = ",".join([x.label for x in self.labels.all()])
        illustrators = ",".join([x.name for x in self.illustrators.all()])
        authors = ",".join([x.name for x in self.authors.all()])
        editors = ",".join([x.name for x in self.editors.all()])
        mechanisms = ",".join([x.name for x in self.mechanisms.all()])
        return f"{csv_sanitize(self.number)};{csv_sanitize(self.name)};{csv_sanitize(self.game_type)};{csv_sanitize(self.price)};{csv_sanitize(self.location.name)};{csv_sanitize(self.age)};{csv_sanitize(labels)};{csv_sanitize(self.for_child)};{csv_sanitize(self.games_library_categorization)};{csv_sanitize(self.adapted_games_library_categorization_1)};{csv_sanitize(self.adapted_games_library_categorization_2)};{csv_sanitize(self.time)};{csv_sanitize(self.players_number)};{csv_sanitize(self.details)};{csv_sanitize(self.entry_year)};{csv_sanitize(self.year)};{csv_sanitize(self.myludo_path)};{csv_sanitize(self.cards_number)};{csv_sanitize(self.cards_size)};{csv_sanitize(self.origin)};{csv_sanitize(self.last_inventory_date)};{csv_sanitize(self.rules_video_link)};{csv_sanitize(self.missing_items)};{csv_sanitize(self.inventory)};{csv_sanitize(illustrators)};{csv_sanitize(authors)};{csv_sanitize(mechanisms)};{csv_sanitize(editors)}"

    @classmethod
    def extract_data(cls):
        res = StringIO()
        res.write("numéro;nom;type;prix;localisation;ages;labels;pour enfant;col;col_adapté1;col_adapté2;durée;nombre de joueurs;description;année d’obtention;année de sortie;lien myludo;nombre de cartes;taille des cartes;origine;date d’inventaire;vidéo règle;pièces manquantes;inventaire;illustrateurs;auteurs;mécanismes;éditeurs\n")
        for game in cls.objects.all():
            res.write(game.csv_data())
            res.write("\n")
        return res

    def save(self, *args, **kwargs):
        self.qrcode.name = generate_qrcode(self)
        super().save(*args, **kwargs)

class Comment(models.Model):
    text = models.TextField()
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    created_date = models.DateTimeField()

    def csv_data(self):
        return f"{csv_sanitize(self.game.number)};{csv_sanitize(self.created_date)};{csv_sanitize(self.text)}"

    @classmethod
    def extract_data(cls):
        res = StringIO()
        res.write("numéro du jeux;date de création;texte\n")
        for game in cls.objects.all():
            res.write(game.csv_data())
            res.write("\n")
        return res
