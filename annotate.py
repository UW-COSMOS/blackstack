import sys
from bs4 import BeautifulSoup
from PIL import Image
import matplotlib as mpl
from matplotlib import pyplot
import codecs
mpl.use('TkAgg')

def makeBox(bbox):
    return {
        '_left': int(bbox[0]),
        '_top': int(bbox[1]),
        '_right': int(bbox[2]),
        '_bottom': int(bbox[3]),
        'width': int(bbox[2]) - int(bbox[0]),
        'height': int(bbox[3]) - int(bbox[1])
    }

def getbbox(title):
    title_parts = title.split(';')
    for part in title_parts:
        if part.strip()[0:4] == 'bbox':
            return part.replace('bbox', '').strip().split()

    return

def tess(infile, outfile):
    with codecs.open(infile, "r", "utf-8") as hocr:
        text = hocr.read()

    soup = BeautifulSoup(text, "html.parser")
    pages = soup.find_all('div', 'ocr_page')
    careas = soup.find_all('div', 'ocr_carea')
    pars = soup.find_all('p', 'ocr_par')
    lines = soup.find_all('span', 'ocr_line')
    words = soup.find_all('span', 'ocrx_word')

    page_boxes = [makeBox(getbbox(page.get('title'))) for page in pages]
    carea_boxes = [makeBox(getbbox(carea.get('title'))) for carea in careas]
    par_boxes = [makeBox(getbbox(par.get('title'))) for par in pars]
    line_boxes = [makeBox(getbbox(line.get('title'))) for line in lines]
    word_boxes = [makeBox(getbbox(word.get('title'))) for word in words]

    fig = pyplot.figure()
    ax = fig.add_subplot(111, aspect='equal')

    for box in page_boxes:
        ax.add_patch(mpl.patches.Rectangle(
            (box['_left'], box['_top']),
            box['_right'] - box['_left'],
            box['_bottom'] - box['_top'],
            fill=False,
            linewidth=0.5,
            edgecolor="#FF00FF"
            )
            )

    for box in carea_boxes:
        ax.add_patch(mpl.patches.Rectangle(
            (box['_left'], box['_top']),
            box['_right'] - box['_left'],
            box['_bottom'] - box['_top'],
            fill=False,
            linewidth=0.5,
            edgecolor="#0000FF"
            )
            )

    for box in par_boxes:
        ax.add_patch(mpl.patches.Rectangle(
            (box['_left'], box['_top']),
            box['_right'] - box['_left'],
            box['_bottom'] - box['_top'],
            fill=False,
            linewidth=0.1,
            edgecolor="#F0F0F0"
            )
            )

    for box in line_boxes:
        ax.add_patch(mpl.patches.Rectangle(
            (box['_left'], box['_top']),
            box['_right'] - box['_left'],
            box['_bottom'] - box['_top'],
            fill=False,
            linewidth=0.1,
            edgecolor="#FF0000"
            )
            )
    for box in word_boxes:
        ax.add_patch(mpl.patches.Rectangle(
            (box['_left'], box['_top']),
            box['_right'] - box['_left'],
            box['_bottom'] - box['_top'],
            fill=False,
            linewidth=0.1,
            edgecolor="#000000"
            )
            )

    pyplot.ylim(0,page_boxes[0]['_bottom'])
    pyplot.xlim(0,page_boxes[0]['_right'])
    pyplot.axis("off")
    ax = pyplot.gca()
    ax.invert_yaxis()
    pyplot.axis('off')
    fig.savefig(outfile, dpi=400, bbox_inches='tight', pad_inches=0)


if len(sys.argv) == 3:
    tess(sys.argv[1], sys.argv[2])
else:
    print('Script requires two parameters: an input Tesseract HOCR file and an output file name and location')
