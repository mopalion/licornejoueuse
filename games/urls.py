from django.urls import path

from . import views

urlpatterns = [
        path("", views.index, name="index"),
        path("bois", views.index, {"game_type" : "wooden"}, name="wooden_index"),
        path("jdr", views.index, {"game_type" : "rpg"}, name="rpg_index"),
        path("jouets", views.index, {"game_type" : "toys"}, name="toys_index"),
        path("locations/", views.location_index, name="location_index"),
        path("locations/<str:name>/", views.location_detail, name="location_detail"),
        path("<int:number>/", views.detail, name="detail"),
        path("<int:number>/generate", views.generate_qrcode, name="generate_qrcode"),
        ]
