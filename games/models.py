from django.db import models

class Location(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Game(models.Model):
    title = models.CharField(max_length=200, blank=False)
    details = models.TextField(blank=True)
    add_date = models.DateTimeField("date added")
    number = models.PositiveIntegerField("Number", blank=False, unique=True)
    location = models.ForeignKey(Location, on_delete=models.PROTECT, blank=False)
    qrcode = models.ImageField(upload_to="medias/qrcode", blank=True)
    image = models.ImageField(upload_to="medias/games_images", blank=True)
    state = models.CharField(max_length=20, blank=True)
    age = models.PositiveIntegerField()
    theme = models.CharField(max_length=30, blank=True) 
    token = models.PositiveIntegerField(blank=False)
    to_sold = models.BooleanField(default=False)
    game_type = models.CharField(max_length=20, default="boardgame", choices=[("boardgame","jds"), ("rpg","jdr"), ("wooden", "bois"), ("toys", "jouet")])

    def __str__(self):
        return f"{self.title}({self.number})"
