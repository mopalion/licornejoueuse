from PIL import Image, ImageDraw, ImageFont
from django.utils.text import slugify
from django.conf import settings
import segno
import img2pdf
from io import BytesIO
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
    filename_qrcode = f"medias/qrcode/{slugify(game.name)}_{game.number}_qrcode.png"
    qrcode = segno.make(f"{settings.DJANGO_HOST}/games/{game.number}")
    qrcode.save(filename_qrcode)

    return filename_qrcode

def generate_label(game):
    """
    Generate the label of a specific game.

    Args:
        game (Game): the game that qrcode must be generate.
    Returns:
        label (Image): the label to print
    """
    filename = f"medias/qrcode/{slugify(game.name)}_{game.number}.png"
    filename_qrcode = f"medias/qrcode/{slugify(game.name)}_{game.number}_qrcode.png"

    if game.price < 20:
        background=f"static/global/logo_licorne_vert.png"
    elif game.price < 40:
        background=f"static/global/logo_licorne_jaune.png"
    else:
        background=f"static/global/logo_licorne_rouge.png"

    if game.number < 10:
        coordinates = (380, 380)
    elif game.number < 100:
        coordinates = (365, 380)
    elif game.number < 1000:
        coordinates = (360, 380)
    else:
        coordinates = (340, 380)

    logo_img = Image.open(background)
    qrcode_img = Image.open(filename_qrcode)

    size = (512, 512)
    qrcode_img = qrcode_img.resize(size, Image.NEAREST)

    font = ImageFont.truetype("static/global/comic_sans_ms_bold.ttf", 80)

    height = 512
    width = qrcode_img.width + logo_img.width

    label = Image.new('RGB', (width, height))
    label.paste(logo_img, (0,0))
    label.paste(qrcode_img, (logo_img.width,0))
    draw = ImageDraw.Draw(label)
    draw.text(coordinates, str(game.number), (0, 0, 0), font=font)

    size = (826, 413)
    size = (620, 310)
    label = label.resize(size, Image.NEAREST)

    return label



def generate_label_sheets(games):
    """
    Generate sheets to print for get labels to a list of games.

    Args:
        games (List of Game): List of games to edit labels.
    Returns:
        pdf file (): the label to print
    """
    images = []
    for game in games:
        images.append(generate_label(game))

    sheets = []
    for i in range(len(images)):
        if (i%44) == 0:
            #2480 * 3508 pixels donne du A4 à 300 DPI
            sheet = Image.new('RGB', (2480, 3508),(255,255,255))
        sheet.paste(images[i], ((i%4)*620, ((i%44)//4)*310))
        if (i%44) == 43:
            bytes_io = BytesIO()
            sheet.save(bytes_io, "PNG")
            sheets.append(bytes_io)
    bytes_io = BytesIO()
    sheet.save(bytes_io, "PNG")
    sheets.append(bytes_io)

    pdf_file = BytesIO()
    a4inpt = (img2pdf.mm_to_pt(210), img2pdf.mm_to_pt(297))
    layout_fun = img2pdf.get_layout_fun(a4inpt)
    pdf_file.write(img2pdf.convert(list(map(lambda x: x.getvalue(), sheets)), layout_fun=layout_fun))
    return pdf_file 
