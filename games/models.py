from django.db import models
from django.core.validators import MinValueValidator
from io import StringIO
from datetime import date
from .tools import generate_qrcode

COL_CHOICES = [("", ""),("R", "Règles"),("E", "Exercice"),("S", "Symbolique"),("A", "Assemblage")]
COL_SUB = [
    ("sen","sensoriel"),
    ("mot","motricité"),
    ("man","manipulation"),
    ("rôl","rôles"),
    ("mis","mise en scène"),
    ("rep","représentation"),
    ("ass","association"),
    ("par","parcours"),
    ("exp","expression"),
    ("com","combinaison"),
    ("adr","adresse"),
    ("ref","réflexion"),
    ("has","hasard"),
    ("que","questions-réponses"),
    ("cos","construction"),
    ("age","agencement"),
    ("exp","expérimentation"),
    ("fab","fabrication"),
]

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

col_choices = [

]
class Game(models.Model):
    class Meta:
        ordering = ["number"]

    name = models.CharField(max_length=200, blank=False)
    
    games_library_categorization = models.CharField(max_length=1, blank=True, choices=COL_CHOICES)
    adapted_games_library_categorization_1 = models.CharField(max_length=10, blank=True, choices=COL_SUB)
    adapted_games_library_categorization_2 = models.CharField(max_length=10, blank=True, choices=COL_SUB)
    time = models.CharField(max_length=10, blank=True)
    players_number = models.CharField(max_length=10, blank=True)
    details = models.TextField(blank=True)
    entry_year = models.PositiveIntegerField(blank=False, null=True, validators=[MinValueValidator(2013)])
    number = models.PositiveIntegerField("Number", blank=False, unique=True)
    price = models.FloatField(blank=True, null=True, validators=[MinValueValidator(0)])
    year = models.PositiveIntegerField(blank=True, null=True)
    myludo_path = models.CharField(max_length=200, blank=True, null=True)
    cards_number = models.PositiveIntegerField(blank=True,null=True)
    cards_size = models.CharField(max_length=40, blank=True)
    origin = models.CharField(max_length=100, blank=True, null=True)
    qrcode = models.ImageField(upload_to="qrcode", blank=True)
    image = models.ImageField(upload_to="games_images", blank=True)
    age = models.CharField(max_length=10, blank=True, null=True)
    game_type = models.CharField(max_length=20, default="boardgame", choices=[("boardgame","jds"), ("rpg","jdr"), ("wooden", "bois"), ("toys", "jouet")])
    last_inventory_date = models.DateField("last inventory date", blank=True, null=True)
    rules_video_link = models.CharField(max_length=100, blank=True, null=True)
    for_child = models.BooleanField(choices=[(True, "Oui"), (False, "Non")], default=False)
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
        self.qrcode = generate_qrcode(self)
        super().save(*args, **kwargs)

class Comment(models.Model):
    text = models.TextField()
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    created_date = models.DateTimeField()

    def __str__(self):
        return f"{self.game.number}-{self.created_date.strftime('%y%m%d%H%M')}-{self.text[:20]}"

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
