from django.urls import path

from . import views

urlpatterns = [
        path("", views.index, name="index"),
        path("bois", views.index, {"game_type" : "wooden"}, name="wooden_index"),
        path("jdr", views.index, {"game_type" : "rpg"}, name="rpg_index"),
        path("jouets", views.index, {"game_type" : "toys"}, name="toys_index"),
        path("locations/", views.location_index, name="location_index"),
        path("locations/<str:name>/", views.location_detail, name="location_detail"),
        path("games/<int:number>/", views.detail, name="detail"),
        path("inventory/", views.inventory_index, name="inventory_index"),
        path("inventory/games/<int:number>/", views.update_game, name="update_game"),
        path("inventory/games/new/", views.add_game, name="add_game"),
        path("inventory/games/game_added/<int:number>/", views.game_added, name="game_added"),
        path("inventory/batch", views.batch, name="batch"),
        path("inventory/game_csv", views.generate_game_csv, name="generate_game_csv"),
        path("inventory/comment_csv", views.generate_comment_csv, name="generate_comment_csv"),
        path("inventory/new_comment/<int:number>/", views.new_comment, name="new_comment"),
        path("inventory/comment_added/", views.comment_added, name="comment_added"),
        path("inventory/games/delete/<int:number>/", views.delete_game, name="delete_game"),
        path("inventory/games/deleted_game/", views.game_deleted, name="game_deleted"),
        path("inventory/labels/", views.labels_index, name="labels_index"),
        path("inventory/labels/new/", views.add_label, name="add_label"),
        path("inventory/labels/<int:id>/", views.update_label, name="update_label"),
        path("inventory/labels/delete/<int:id>/", views.delete_label, name="delete_label"),
        ]
