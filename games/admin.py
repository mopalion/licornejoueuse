from django.contrib import admin
from .models import Game, Location, Author, Illustrator, Mechanism, Label, Comment, Theme

admin.site.register(Game)
admin.site.register(Location)
admin.site.register(Label)
admin.site.register(Comment)
admin.site.register(Author)
admin.site.register(Illustrator)
admin.site.register(Mechanism)
admin.site.register(Theme)
# Register your models here.
