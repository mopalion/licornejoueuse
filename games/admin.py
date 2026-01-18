from django.contrib import admin
from .models import Game, Location, Author, Illustrator, Mechanism, Label, Comment

admin.site.register(Game)
admin.site.register(Location)
admin.site.register(Label)
admin.site.register(Comment)
admin.site.register(Author)
admin.site.register(Illustrator)
admin.site.register(Mechanism)
# Register your models here.
