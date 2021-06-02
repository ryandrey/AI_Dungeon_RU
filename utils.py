import re

import textwrap
import random
import os
import sys

from getconfig import colors, settings
from shutil import get_terminal_size


def getTermWidth():
    termWidth = get_terminal_size()[0]
    if termWidth < 5:
        termWidth = 999999999
    return termWidth


termWidth = getTermWidth()


def format_input(text):
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def format_result(text):
    text = re.sub(r"\n{3,}", "<br>", text)
    text = re.sub(r" {2,}", " ", text)
    text = re.sub(r"\n", " ", text)
    text = re.sub(r"<br>", "\n", text)
    text = re.sub(r"(\"[.!?]) ([A-Z])", "\\1\n\n\\2", text)
    text = re.sub(r"([^\"][.!?]) \"", "\\1\n\n\"", text)
    text = re.sub(r"([\".!?]) \"", "\\1\n\"", text)
    return text.strip()


def list_items(items, col='menu', start=0, end=None, wrap=False):
    i = start
    digits = len(str(len(items)-1))
    for s in items:
        output(str(i).rjust(digits) + ") " + s, col, end='', wrap=wrap)
        i += 1
    if end is not None:
        output('', end=end, wrap=wrap)


def end_sentence(text):
    if text[-1] not in [".", "?", "!"]:
        text = text + "."
    return text


def select_file(p, e, d=0):
    if p.is_dir():
        t_dirs = sorted([x for x in p.iterdir() if x.is_dir()])
        t_files = sorted([x for x in p.iterdir() if x.is_file() and x.name.endswith(e)])
        files = t_dirs + t_files
        list_items(
            ["(Выбрать случайно)"] +
            [f.name[:-len(e)] if f.is_file() else f.name + "/" for f in files] +
            ["(Отмена)" if d == 0 else "(Вернуться)"],
            "menu"
        )
        count = len(files) + 1
        i = input_number(count)
        if i == 0:
            try:
                i = random.randrange(1, count-1)
            except ValueError:
                i = 1
        if i == count:
            if d == 0:
                output("Action cancelled. ", "message")
                return None
            else:
                return select_file(p.parent, e, d-1)
        else:
            return select_file(files[i-1], e, d+1)
    else:
        return p


def input_line(str, col1="default", default=""):
    clb1 = "\x1B[{}m".format(colors[col1]) if col1 and colors[col1] and colors[col1][0].isdigit() else ""
    cle1 = "\x1B[0m" if col1 and colors[col1] and colors[col1][0].isdigit() else ""
    val = input(clb1 + str + cle1)
    print("\x1B[0m", end="")
    return val


def input_bool(prompt, col1="default", default: bool = False):
    val = input_line(prompt, col1).strip().lower()
    if not val or val[0] not in "yn":
        return default
    return val[0] == "y"


def input_number(max_choice, default=0):
    if default == -1:
        default = max_choice
    print()
    val = input_line(f"Напишите число (default {default}):", "selection-prompt")
    if not val:
        return default
    elif not re.match("^\d+$", val) or 0 > int(val) or int(val) > max_choice:
        output("Некоректный выбор. ", "error")
        return input_number(max_choice)
    else:
        return int(val)

    
def fill_text(text, width):
    texts = text.split('\n')
    for i in range(0, len(texts)):
        texts[i] = textwrap.fill(
            texts[i],
            width,
            replace_whitespace=False,
            drop_whitespace=False
        )
    return '\n'.join(texts)
    
    
def output(text1, col1=None,
           text2=None, col2=None,
           wrap=True,
           beg=None, end='\n', sep=' ',
           rem_beg_spaces=True):
    print('', end=beg)
    
    if wrap:
        width = settings.getint("text-wrap-width")
        width = 999999999 if width < 2 else width
        width = min(width, termWidth)
        wtext = text1 + '\u200D' + sep + '\u200D' + text2 if text2 is not None else text1
        wtext = fill_text(wtext, width)
        wtext = re.sub(r"\n[ \t]+", "\n", wtext) if rem_beg_spaces else wtext
        wtext = wtext.split('\u200D')
        text1 = wtext[0]
        if text2 is not None:
            sep = wtext[1]
            text2 = ' '.join(wtext[2:])
    
    col1 = colors[col1] if col1 and colors[col1] and colors[col1][0].isdigit() else None
    col2 = colors[col2] if col2 and colors[col2] and colors[col2][0].isdigit() else None

    clb1 = "\x1B[{}m".format(col1) if col1 else ""
    clb2 = "\x1B[{}m".format(col2) if col2 else ""
    cle1 = "\x1B[0m" if col1 else ""
    cle2 = "\x1B[0m" if col2 else ""
    text1 = clb1 + text1 + cle1
    if text2 is not None:
        text2 = clb2 + text2 + cle2
        print(text1, end='')
        print(sep, end='')
        print(text2, end=end)
    else:
        print(text1, end=end)

    linecount = 1
    if beg:
        linecount += beg.count('\n')
    if text1:
        linecount += text1.count('\n')
    if end:
        linecount += end.count('\n')
    if text2:
        linecount += text2.count('\n')
        if sep:
            linecount += sep.count('\n')
    return linecount
