import csv
from datetime import datetime, date
from .models import Game, Location, Label, Author, Illustrator, Mechanism, Comment, Editor, Theme
import requests
from os import makedirs
from os import environ
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from django.conf import settings
import re
from playwright.sync_api import sync_playwright
import traceback
from os import getenv
from playwright._impl._errors import TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError

def log_error_in_file(e):
    django_errors_dir = getenv("DJANGO_ERRORS_DIR")
    if django_errors_dir != '':
        django_errors_dir = "./"
    with open(f"{django_errors_dir}errors.txt", "a") as fd:
        fd.write("******************************************************")
        fd.write(traceback.format_exc())
        fd.write(str(e))
        fd.write("\n")
        fd.write(str(type(e)))
        fd.write("\n")

class MyLudoBrowser():
    def __init__(self):
        self.play = sync_playwright().start()
        self.browser = self.play.chromium.launch()
        self.page = self.browser.new_page()
        self.page.goto("https://www.myludo.fr/#!", wait_until="networkidle")
        l = self.page.get_by_role("button", name="OK, accept all")
        l.click()
        self.page.set_default_timeout(3000)

    def __del__(self):
        self.browser.close()
        self.play.stop()


    def get_game_url(self, name):
        self.page.goto(f"https://www.myludo.fr/#!/search/{name}", wait_until="networkidle")
        try:
            elem = self.page.locator("p.title.grey-text.text-darken-4 > a").first
            link = elem.get_attribute("href")
        except PlaywrightTimeoutError:
            return None
        return link


    def get_game_data(self, game_number, check_game=True):
        game = Game.objects.filter(number=game_number)[0]
        if check_game:
            if game.myludo_path is not None and game.myludo_path != "":
                link = game.myludo_path
            else:
                link = self.get_game_url(game.name)
        else:
            link = self.get_game_url(game.name)
        if link is None:
            return None
        myludo_url = f"https://www.myludo.fr/{link}"
        print(f"myludo_url: {myludo_url}")
        self.page.goto(myludo_url, wait_until="networkidle")
        self.page.wait_for_timeout(1000)

        themes = []
        for theme_markup in self.page.get_by_title("Thématique").all()[1:]:
            themes.append(re.sub(r"local_offer", "", theme_markup.text_content()))
        mechanisms = []
        for mechanism_markup in self.page.get_by_title("Mécanisme").all():
            mechanisms.append(re.sub(r"settings", "", mechanism_markup.text_content()))

        descriptions = self.page.locator(".card-content > .hide-on-small-only > p").all()
        description = ""
        first = True
        for paragraph in descriptions:
            if not first:
                description += "\n\n"
            else:
                first = False
            description += f"{paragraph.text_content()}"

        contents = []
        for content in self.page.get_by_text("Contenu").locator("xpath=following-sibling::*[1]").locator("li").all():
            contents.append(content.text_content().strip())

        authors = []
        for author in self.page.get_by_text("Auteur", exact=True).locator("xpath=preceding-sibling::p[1]/a").all():
            authors.append(author.text_content())

        illustrators = []
        for illustrator in self.page.get_by_text("Illustrateur", exact=True).locator("xpath=preceding-sibling::p[1]/a").all():
            illustrators.append(illustrator.text_content())

        editors = []
        try:
            for editor in self.page.get_by_text("Éditeur", exact=True).locator("xpath=preceding-sibling::p[1]/a").all():
                editors.append(editor.text_content())
        except PlaywrightTimeoutError:
            pass

        self.page.screenshot(path="/mnt/c/Users/jujud/Documents/toto.png")

        try:
            img = self.page.query_selector("picture img").get_attribute("src")
        except AttributeError:
            img = None

        try:
            players = self.page.get_by_title("Joueurs").locator("xpath=following-sibling::*[1]").text_content()
        except PlaywrightError:
            players = None
        try:
            age = self.page.get_by_title("Âge").locator("xpath=following-sibling::*[1]").text_content()
        except PlaywrightTimeoutError:
            age = None

        infos = {
            "img": img,
            "players": players,
            "age": age,
            "time": self.page.get_by_title("Durée").locator("xpath=following-sibling::*[1]").text_content(),
            "themes": themes,
            "mechanisms": mechanisms,
            "description": description,
            "release_year": self.page.locator("span.edition").text_content().strip(),
            "contents": contents,
            "authors": authors,
            "illustrators": illustrators,
            "myludo_path": link,
            "editors": editors,
        }


        cards_size = []
        try:
             elements = self.page.locator("a.sleeve > p > strong").all()
             for elem in elements:
                 cards_size.append(elem.text_content())
             infos["cards_size"] = ",".join(cards_size)
        except PlaywrightTimeoutError:
            pass

        return infos




def complete_data(label=None, remove_label = False):
    environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
    if label is None:
        uncomplete_games = Game.objects.all() 
    else:
        filtering_label = Label.objects.filter(label=label)[0]
        uncomplete_games = filtering_label.game_set.all()
    myludo = MyLudoBrowser()
    for game in uncomplete_games:
        print(f"début: {game}")
        infos = myludo.get_game_data(game.number)
        if infos is None:
            print("go suivant")
            continue
        print("suite du début")

        if infos["img"] is not None:
            r = requests.get(infos["img"], allow_redirects=True)
            makedirs(f"{settings.MEDIA_ROOT}games_images", exist_ok=True)
            with open(f"{settings.MEDIA_ROOT}games_images/{game.name}.jpg", "wb") as fd:
                fd.write(r.content)
            game.image = f"games_images/{game.name}.jpg"
        if infos["players"] is not None:
            game.players_number = infos["players"]
        game.myludo_path = infos["myludo_path"]
        if infos["age"] is not None:
            game.age = infos["age"]
        game.time = infos["time"]
        for theme_name in infos["themes"]:
            themes = Theme.objects.filter(name=theme_name)
            if len(themes) != 0:
                theme = themes[0]
            else:
                theme = Theme(name=theme_name)
                theme.save()
            game.themes.add(theme)
        for mechanism_name in infos["mechanisms"]:
            mechanisms = Mechanism.objects.filter(name=mechanism_name)
            if len(mechanisms) != 0:
                mechanism = mechanisms[0]
            else:
                mechanism = Mechanism(name=mechanism_name)
                mechanism.save()
            game.mechanisms.add(mechanism)
        game.details = infos["description"]

        if game.year == "":
            game.year = infos["release_year"].strip().split(" ")[0]
        for editor_name in infos["editors"]:
            editors = Editor.objects.filter(name=editor_name)
            if len(editors) != 0:
                editor = editors[0]
            else:
                editor = Editor(name=editor_name)
                editor.save()
            game.editors.add(editor)
        for author_name in infos["authors"]:
            authors = Author.objects.filter(name=author_name)
            if len(authors) != 0:
                author = authors[0]
            else:
                author = Author(name=author_name)
                author.save()
            game.authors.add(author)
        for illustrator_name in infos["illustrators"]:
            illustrators = Illustrator.objects.filter(name=illustrator_name)
            if len(illustrators) != 0:
                illustrator = illustrators[0]
            else:
                illustrator = Illustrator(name=illustrator_name)
                illustrator.save()
            game.illustrators.add(illustrator)




        game.save()
        if label is not None:
            game.labels.remove(filtering_label)
