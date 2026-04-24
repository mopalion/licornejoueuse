from django.db import models
from django.core.validators import MinValueValidator
from io import StringIO
from datetime import date
from .tools import generate_qrcode

# ============================================================
# CONSTANTES DE CHOIX (utilisées par les champs `choices` de Django)
# ============================================================

# Classification COL (Centre de Loisirs / classification ESAR simplifiée)
# Utilisée pour catégoriser les jeux selon leur nature principale.
# Source : https://fr.wikipedia.org/wiki/Syst%C3%A8me_ESAR
COL_CHOICES = [
    ("", ""),
    ("R", "Règles"),
    ("E", "Exercice"),
    ("S", "Symbolique"),
    ("A", "Assemblage"),
]

# Sous-catégories COL : précisent la catégorie principale ci-dessus.
# ⚠️ Attention : la clé "exp" apparaît deux fois (expression ET expérimentation).
# Django ne lèvera pas d'erreur, mais la seconde écrasera la première dans le dict interne.
COL_SUB = [
    ("sen", "sensoriel"),
    ("mot", "motricité"),
    ("man", "manipulation"),
    ("rôl", "rôles"),
    ("mis", "mise en scène"),
    ("rep", "représentation"),
    ("ass", "association"),
    ("par", "parcours"),
    ("expr", "expression"),
    ("com", "combinaison"),
    ("adr", "adresse"),
    ("ref", "réflexion"),
    ("has", "hasard"),
    ("que", "questions-réponses"),
    ("cos", "construction"),
    ("age", "agencement"),
    ("expé", "expérimentation"),
    ("fab", "fabrication"),
]


# ============================================================
# MODÈLES DE RÉFÉRENCE (entités liées aux jeux via ForeignKey ou ManyToMany)
# ============================================================

class Location(models.Model):
    """Emplacement physique où un jeu est rangé (Local, Bo-bar, etc)."""
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Author(models.Model):
    """Auteur d'un jeu (concepteur des règles)."""
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name}"


class Illustrator(models.Model):
    """Illustrateur d'un jeu (graphismes, illustrations des cartes, etc.)."""
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name}"


class Editor(models.Model):
    """Éditeur / maison d'édition ayant publié le jeu."""
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name}"


class Mechanism(models.Model):
    """Mécanisme de jeu (deck-building, placement d'ouvriers, enchères, etc.)."""
    name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name}"


class Label(models.Model):
    """
    Label ou distinction attribué à un jeu. Permet de pouvoir filtrer facilement des jeux.
    Contient un intitulé court et une description détaillée.
    """
    label = models.CharField(max_length=50)
    description = models.TextField()

    def __str__(self):
        return f"{self.label}"


class Theme(models.Model):
    """Thème d'un jeu (médiéval, spatial, enquête, etc.)."""
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name}"


# ============================================================
# FONCTION UTILITAIRE — formatage CSV
# ============================================================

def csv_sanitize(value):
    """
    Normalise une valeur pour l'export CSV.

    - Convertit les booléens en "oui" / "non" (lisibilité humaine).
    - Formate les dates au format français JJ/MM/AA.
    - Entoure systématiquement la valeur de guillemets doubles pour éviter
      les problèmes de séparateurs (;) présents dans les textes.

    :param value: valeur brute issue d'un champ du modèle
    :return: chaîne prête à être insérée dans une ligne CSV
    """
    if type(value) == type(True):  # détection d'un booléen
        if value == True:
            value = "oui"
        else:
            value = "non"
    elif type(value) == type(date.today()):  # détection d'une date
        value = value.strftime('%d/%m/%y')
    return f"\"{str(value)}\""


# ============================================================
# MODÈLE PRINCIPAL : Game
# ============================================================

class Game(models.Model):
    """
    Représente un jeu de la ludothèque.

    Ce modèle centralise toutes les informations d'un jeu :
    identité, caractéristiques ludiques, métadonnées administratives,
    et relations avec les entités (auteurs, éditeurs, etc.).
    """

    class Meta:
        # Tri par défaut des jeux par leur numéro d'inventaire croissant.
        ordering = ["number"]

    # -------- Informations générales --------
    name = models.CharField(max_length=200, blank=False)  # Titre du jeu (obligatoire)

    # -------- Classification pédagogique (ESAR / COL) --------
    games_library_categorization = models.CharField(
        max_length=1, blank=True, choices=COL_CHOICES
    )
    adapted_games_library_categorization_1 = models.CharField(
        max_length=10, blank=True, choices=COL_SUB
    )
    adapted_games_library_categorization_2 = models.CharField(
        max_length=10, blank=True, choices=COL_SUB
    )

    # -------- Caractéristiques ludiques --------
    time = models.CharField(max_length=10, blank=True)            # Durée d'une partie
    players_number = models.CharField(max_length=10, blank=True)  # Nombre de joueurs
    details = models.TextField(blank=True)                        # Description / règles résumées

    # -------- Données administratives --------
    entry_year = models.PositiveIntegerField(
        blank=False, null=True,
        validators=[MinValueValidator(2013)]  # La ludothèque existe depuis 2013
    )
    number = models.PositiveIntegerField(
        "Number", blank=False, unique=True   # Numéro d'inventaire unique
    )
    price = models.FloatField(
        blank=True, null=True,
        validators=[MinValueValidator(0)]    # Un prix ne peut pas être négatif
    )
    year = models.PositiveIntegerField(blank=True, null=True)          # Année de sortie
    myludo_path = models.CharField(max_length=200, blank=True, null=True)  # Lien vers myludo.fr
    cards_number = models.PositiveIntegerField(blank=True, null=True)
    cards_size = models.CharField(max_length=40, blank=True)
    origin = models.CharField(max_length=100, blank=True, null=True)   # Provenance (don, achat…)

    # -------- Médias --------
    # Les images sont stockées dans MEDIA_ROOT/qrcode et MEDIA_ROOT/games_images
    qrcode = models.ImageField(upload_to="qrcode", blank=True)
    image = models.ImageField(upload_to="games_images", blank=True)

    # -------- Caractéristiques complémentaires --------
    age = models.CharField(max_length=10, blank=True, null=True)
    game_type = models.CharField(
        max_length=20,
        default="boardgame",
        choices=[
            ("boardgame", "jds"),   # jeu de société
            ("rpg", "jdr"),         # jeu de rôle
            ("wooden", "bois"),     # jeu en bois
            ("toys", "jouet"),      # jouet
        ],
    )
    last_inventory_date = models.DateField("last inventory date", blank=True, null=True)
    rules_video_link = models.CharField(max_length=100, blank=True, null=True)
    for_child = models.BooleanField(
        choices=[(True, "Oui"), (False, "Non")], default=False
    )
    missing_items = models.TextField(blank=True, null=True)  # Pièces manquantes
    inventory = models.TextField(blank=True)                 # Détail de l'inventaire

    # -------- Relations --------
    # ForeignKey : un jeu a un seul emplacement. PROTECT empêche la suppression
    # d'un Location si des jeux y sont encore associés.
    location = models.ForeignKey(Location, on_delete=models.PROTECT, blank=False)

    # ManyToMany : un jeu peut avoir plusieurs auteurs/éditeurs/etc.
    illustrators = models.ManyToManyField(Illustrator, blank=True)
    authors = models.ManyToManyField(Author, blank=True)
    mechanisms = models.ManyToManyField(Mechanism, blank=True)
    editors = models.ManyToManyField(Editor, blank=True)
    labels = models.ManyToManyField(Label, blank=True)
    themes = models.ManyToManyField(Theme, blank=True)

    def __str__(self):
        """Représentation lisible : 'Nom du jeu(numéro)'."""
        return f"{self.name}({self.number})"

    def csv_data(self):
        """
        Sérialise l'instance en une ligne CSV (séparateur `;`).

        Les relations ManyToMany sont aplanies en chaînes séparées par des virgules.
        L'ordre des colonnes doit **impérativement** correspondre à celui défini
        dans `extract_data()`.
        """
        labels = ",".join([x.label for x in self.labels.all()])
        illustrators = ",".join([x.name for x in self.illustrators.all()])
        authors = ",".join([x.name for x in self.authors.all()])
        editors = ",".join([x.name for x in self.editors.all()])
        mechanisms = ",".join([x.name for x in self.mechanisms.all()])

        return (
            f"{csv_sanitize(self.number)};"
            f"{csv_sanitize(self.name)};"
            f"{csv_sanitize(self.game_type)};"
            f"{csv_sanitize(self.price)};"
            f"{csv_sanitize(self.location.name)};"
            f"{csv_sanitize(self.age)};"
            f"{csv_sanitize(labels)};"
            f"{csv_sanitize(self.for_child)};"
            f"{csv_sanitize(self.games_library_categorization)};"
            f"{csv_sanitize(self.adapted_games_library_categorization_1)};"
            f"{csv_sanitize(self.adapted_games_library_categorization_2)};"
            f"{csv_sanitize(self.time)};"
            f"{csv_sanitize(self.players_number)};"
            f"{csv_sanitize(self.details)};"
            f"{csv_sanitize(self.entry_year)};"
            f"{csv_sanitize(self.year)};"
            f"{csv_sanitize(self.myludo_path)};"
            f"{csv_sanitize(self.cards_number)};"
            f"{csv_sanitize(self.cards_size)};"
            f"{csv_sanitize(self.origin)};"
            f"{csv_sanitize(self.last_inventory_date)};"
            f"{csv_sanitize(self.rules_video_link)};"
            f"{csv_sanitize(self.missing_items)};"
            f"{csv_sanitize(self.inventory)};"
            f"{csv_sanitize(illustrators)};"
            f"{csv_sanitize(authors)};"
            f"{csv_sanitize(mechanisms)};"
            f"{csv_sanitize(editors)}"
        )

    @classmethod
    def extract_data(cls):
        """
        Exporte la totalité des jeux en CSV, renvoyé sous forme de StringIO.

        :return: objet StringIO contenant l'en-tête + une ligne par jeu.
                 ⚠️ Le curseur est positionné en fin de buffer ;
                 faire `.seek(0)` avant lecture ou utiliser `.getvalue()`.
        """
        res = StringIO()
        # Ligne d'en-tête (doit correspondre à l'ordre de `csv_data`)
        res.write(
            "numéro;nom;type;prix;localisation;ages;labels;pour enfant;col;"
            "col_adapté1;col_adapté2;durée;nombre de joueurs;description;"
            "année d’obtention;année de sortie;lien myludo;nombre de cartes;"
            "taille des cartes;origine;date d’inventaire;vidéo règle;"
            "pièces manquantes;inventaire;illustrateurs;auteurs;mécanismes;éditeurs\n"
        )
        for game in cls.objects.all():
            res.write(game.csv_data())
            res.write("\n")
        return res

    def save(self, *args, **kwargs):
        """
        Surcharge de `save()` : régénère systématiquement le QR code
        avant chaque sauvegarde en base, afin de garantir sa cohérence
        avec les données du jeu (numéro, nom, etc.).
        """
        self.qrcode = generate_qrcode(self)
        super().save(*args, **kwargs)


# ============================================================
# MODÈLE : Comment
# ============================================================

class Comment(models.Model):
    """
    Commentaire attaché à un jeu (retour d'expérience, note, observation).

    La suppression d'un jeu (`on_delete=CASCADE`) entraîne la suppression
    de tous ses commentaires.
    """
    text = models.TextField()
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    created_date = models.DateTimeField()

    def __str__(self):
        # Format : '<n° jeu>-<AAMMJJHHMM>-<20 premiers caractères du texte>'
        return f"{self.game.number}-{self.created_date.strftime('%y%m%d%H%M')}-{self.text[:20]}"

    def csv_data(self):
        """Sérialise un commentaire en ligne CSV (numéro jeu ; date ; texte)."""
        return (
            f"{csv_sanitize(self.game.number)};"
            f"{csv_sanitize(self.created_date)};"
            f"{csv_sanitize(self.text)}"
        )

    @classmethod
    def extract_data(cls):
        """
        Exporte tous les commentaires au format CSV dans un StringIO.

        :return: StringIO contenant l'en-tête + une ligne par commentaire.
        """
        res = StringIO()
        res.write("numéro du jeux;date de création;texte\n")
        for game in cls.objects.all():
            res.write(game.csv_data())
            res.write("\n")
        return res
