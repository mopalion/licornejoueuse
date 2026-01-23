from PIL import Image, ImageDraw, ImageFont
from django.utils.text import slugify
from django.conf import settings
import segno
"""
This module provides different tools.
"""

def generate_qrcode(game):
    """
    Generate the qrcode of a specific game.

    Args:
        game (Game): the game that qrcode must be generate.
    Returns:
        str: the path of qrcode.
    """
    filename = f"medias/qrcode/{slugify(game.name)}_{game.number}.png"

    qrcode = segno.make(f"{settings.DJANGO_HOST}/games/{game.number}")
    if game.price < 20:
        background=f"static/global/logo_licorne_vert.png"
    elif game.price < 40:
        background=f"static/global/logo_licorne_jaune.png"
    else:
        background=f"static/global/logo_licorne_rouge.png"
    qrcode.to_artistic(background=background, target=filename, scale=7)

    if game.number < 10:
        coordinates = (125, -7)
    elif game.number < 100:
        coordinates = (113, -7)
    elif game.number < 1000:
        coordinates = (100, -7)
    else:
        coordinates = (90, -7)
    img = Image.open(filename)
    font = ImageFont.truetype("static/global/comic_sans_ms_bold.ttf", 30)
    draw = ImageDraw.Draw(img)
    draw.text(coordinates, str(game.number), (248, 138, 17), font=font)
    img.save(filename)

    return filename
