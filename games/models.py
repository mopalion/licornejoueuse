from django.db import models

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

class Mechanism(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name}"

class Label(models.Model):
    label = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.label}"

class Game(models.Model):
    name = models.CharField(max_length=200, blank=False)
    games_library_categorization = models.CharField(max_length=10, blank=True)
    adapted_games_library_categorization = models.CharField(max_length=10, blank=True)
    time = models.CharField(max_length=10, blank=True)
    players_number = models.CharField(max_length=10, blank=True)
    details = models.TextField(blank=True)
    add_date = models.DateField("date added", blank=True, null=True)
    number = models.PositiveIntegerField("Number", blank=False, unique=True)
    price = models.PositiveIntegerField(blank=True, null=True)
    year = models.PositiveIntegerField(blank=True, null=True)
    trictrac_link = models.CharField(max_length=200, blank=True)
    cards_number = models.PositiveIntegerField(blank=True,null=True)
    cards_size = models.CharField(max_length=10, blank=True)
    origin = models.CharField(max_length=10, blank=True)
    qrcode = models.ImageField(upload_to="medias/qrcode", blank=True)
    image = models.ImageField(upload_to="medias/games_images", blank=True)
    state = models.CharField(max_length=20, blank=True)
    age = models.CharField(max_length=10)
    theme = models.CharField(max_length=30, blank=True) 
    token = models.PositiveIntegerField(blank=False)
    game_type = models.CharField(max_length=20, default="boardgame", choices=[("boardgame","jds"), ("rpg","jdr"), ("wooden", "bois"), ("toys", "jouet")])
    editor = models.CharField(max_length=100, blank=True)
    last_inventory_date = models.DateField("last inventory date", blank=True, null=True)
    rules_video_link = models.CharField(max_length=100, blank=True)


    location = models.ForeignKey(Location, on_delete=models.PROTECT, blank=False)
    illustrators = models.ManyToManyField(Illustrator, blank=True)
    authors = models.ManyToManyField(Author, blank=True)
    mechanisms = models.ManyToManyField(Mechanism, blank=True)
    labels = models.ManyToManyField(Label, blank=True)

    def __str__(self):
        return f"{self.name}({self.number})"

class Comment(models.Model):
    text = models.TextField()
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    created_date = models.DateTimeField()
