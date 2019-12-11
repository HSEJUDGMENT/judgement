"""
этот модуль парсит дела судакта и возвращает необходимую информацию
- суд и регион суда
- дату решения
- номер дела
- имя судьи
- имя обвиняемого
- статьи, связанные с судебной практикой
"""

import re
from collections import Counter
from bs4 import BeautifulSoup
from natasha import NamesExtractor
EXTRACTOR = NamesExtractor()

# необходимые регулярные выражения

# ФИО: Иванов А.Б., А.Б. Иванов, Иванов АБ
FIO1 = re.compile(r"[А-Я][а-яА-Я\-]{1,25} [А-Я]\. ?[А-Я][.,]?")
FIO2 = re.compile(r"[А-Я]\.[А-Я]\. [А-Я][а-яА-Я\-]{1,25}")
FIO3 = re.compile(r"[А-Я][а-яА-Я\-]{1,25} [А-Я]{2}")

# Менее частые ФИО: Иванов ФИО12, ФИО12, ИВАНОВ АЛЕКСАНДР БОРИСОВИЧ
FIO_ABBR = re.compile(r"[А-Я][а-яА-Я\-]{1,25} ФИО[0-9]{1,3}")
FIO_SHORT = re.compile(r"ФИО[0-9]{1,3}")
REG_CAPS = re.compile(r"[А-Я]{1,20} [А-Я]{1,20} [А-Я]{1,20}")

# дата в формате "11 июля 2015"
REG_DATE = re.compile("[0-9]{1,2} [а-яА-Я]{1,15} [0-9]{4}")

# словарь число: месяц
MONTH_DICT = {"января": "01", "февраля": "02",
              "марта": "03", "апреля": "04", "мая": "05",
              "июня": "06", "июля": "07", "августа": "08",
              "сентября": "09", "октября": "10", "ноября": "11",
              "декабря": "12"}

# популярные указатели на регион
REGION_NAMES = ["област", "край", "республика", "якутия",
                "округ", "край", "город", "ао", "края"]


# doc_str -- html в простом строковом виде


# НОМЕР
def get_number(doc_str):
    """ достаем номер дела """
    soup_format = BeautifulSoup(doc_str)
    header = soup_format.h1.string
    if "№" not in header:
        return "undefined"
    if "по делу" in header:
        return header.split("по делу")[-1].strip(" №")
    return header.split("№")[-1].split()[0]


# ДАТА
def get_date(doc_str):
    """ достаем дату решения """
    soup_format = BeautifulSoup(doc_str)
    header = soup_format.h1.string
    date = re.findall(REG_DATE, header.split("от ")[1])[0]
    day, month, year = date.split()[0], MONTH_DICT[date.split()[1]], date.split()[2]
    return "{}-{}-{}".format(year, month, day)


# СУД
def get_court(doc_str):
    """ достаем название суда """
    soup_format = BeautifulSoup(doc_str)
    court_string = "undefined"
    # ищем в тегах соответствующий тег
    for i in soup_format.find_all("div"):
        try:
            if i["class"] == ['b-justice']:
                if i.find("a"):
                    court = i.find("a")
                else:
                    court = i
                court_string = court.string
        except KeyError:
            pass

    court_string = court_string.replace("- Уголовное", "")
    court_string = court_string.replace("- Гражданские и административные", "")
    court_string = court_string.replace("- Административные правонарушения", "")
    court_string = court_string.strip()
    return court_string


# РЕГИОН
def is_with_region(line):
    """ узнаем, есть ли регион в строке """
    for region in REGION_NAMES:
        if region in line.lower():
            return True
    return False


def get_city(doc_str):
    """ достаем название региона """
#     soup_format = BeautifulSoup(doc_str)
    court_string = get_court(doc_str)
    if "(" not in court_string:
        return "undefined"
    bracket_string = court_string.split("(")[-1].strip(")")
    if is_with_region(bracket_string):
        return bracket_string
    return "undefined"


# СУДЬЯ
def get_judge(doc_str):
    """ достаем имена судей """
    judge_str = doc_str.split("Судьи дела:")[-1]
    judge_str = judge_str.split("(судья)")[0].replace("</h3>", "").strip()
    if len(judge_str) < 50:
        return judge_str
    for line in doc_str.split("<br/>"):
        if "Судья" in line:
            judge_names = re.findall(FIO1, line)+re.findall(FIO2, line)
            if judge_names:
                return judge_names[0]
    return "undefined"


# СТАТЬЯ
def get_article(doc_str):
    """ достаем номера релевантных статей """
    articles = []
    for line in doc_str.split("<"):
        if "Судебная практика по применению" in line:
            articles.append(line.split("ст.")[-1].strip())
    articles = ", ".join(articles)
    if articles == "":
        articles = "нет информации по судебной практике"
    return articles


# ПОДСУДИМЫЙ
def get_first(doc_str):
    """ достаем шапку дела """
    header = doc_str
    for i, line in enumerate(doc_str.split("<br/>")):
        if "установил" in line.lower().replace(" ", ""):
            header = doc_str.split("<br/>")[:i]
            break
    return header


def splitting_text(header_lines):
    """ разбиваем текст на строки """
    trouble_counter = 0
    text = "\n".join(header_lines)
    lines = [line for line in text.split(",") if line.strip()]
    # выбираем разделитель, по которому мы это делаем
    # (стараемся минимизировать число имен в строке)
    for line in lines:
        if len(FIO1.findall(line) + FIO2.findall(line)) > 1:
            trouble_counter += 1
    if trouble_counter != 0:
        lines = [line for line in text.split("\n") if line.strip()]

    new_lines = []
    for line in lines:
        if len(FIO1.findall(line) + FIO2.findall(line)) > 2:
            new_lines += line.split(",")
        else:
            new_lines.append(line)
    lines = new_lines
    return lines


def get_accused_lines(doc_str):
    """ достаем строки с подозреваемым """
    header = get_first(doc_str)
    splitted_lines = splitting_text(header)
    accused_lines = []
    for line in splitted_lines:
        if ("осужденн" in line or "в отношении" in line or "подсудим" in line
        or " к " in line) and len(line) < 300:
            accused_lines.append(line)

    # короткий путь для сокращения вариантов
    for line in accused_lines:
        if "подсудим" in line and len(line) < 50:
            accused_lines = [line]
        elif " к " in line and len(line) < 50:
            accused_lines = [line]

    return accused_lines


def kill_doubles(name_list):
    """ убираем повторяющиеся случаи """
    new_list = [x.replace(" ", "") for x in name_list]
    if len(list(set(new_list))) == 1:
        return [name_list[0]]
    return name_list


def get_names(line):
    """ достаем из строки имена наташей """
    names = []
    matches = EXTRACTOR(line.title())
    for match in matches:
        fact = match.fact.as_json
        if "first" in fact.keys() and "middle" in fact.keys() and "last" in fact.keys():
            name = fact["first"][0].upper() + "." + fact["middle"][0].upper() \
                   + ". " + fact["last"].capitalize()
            names.append(name)
    return names


def find_accused(line):
    """ стандартный шаблон для начального поиска обвиняемых """
    accused_names = [x.title() for x in re.findall(FIO1, line)] + \
                    [x.title() for x in re.findall(FIO2, line)] \
                    + re.findall(FIO_ABBR, line) + re.findall(REG_CAPS, line)
    return accused_names


def get_accused_name(doc_str):
    """ рулы для поиска обвиняемых  """
    accused_names = []
    accused_lines = get_accused_lines(doc_str)

    # вытаскиваем имена из единственной строки
    if len(accused_lines) == 1:
        if "подсудимого" in accused_lines[0]:
            line = accused_lines[0]
            accused_names = find_accused(line)
            accused_names = [x.title() for x in accused_names]
            return accused_names
        if " к " in accused_lines[0]:
            line = accused_lines[0].split(" к ")[-1]
            accused_names = find_accused(line)
            accused_names = [x.title() for x in accused_names]
            return accused_names

    # ищем имена
    for line in accused_lines:
        line = line.replace("&lt;", "").replace("&gt;", "")
        accused_names += find_accused(line)
        # дополнительные попытки поиска
        if not accused_names:
            accused_names += re.findall(FIO_SHORT, line)
        if not accused_names:
            accused_names += re.findall(FIO3, line)
        if not accused_names:
            accused_names += get_names(line)

    # правим имена
    accused_names = [x.replace(",", ".") for x in accused_names]

    # убираем повторы
    if len(list(set(accused_names))) == 1:
        accused_names = list(set(accused_names))
    # выбираем самое частое имя (если среди имен были адвокаты или секретари, их это уберет)
    if accused_names:
        most_common_freq = Counter(accused_names).most_common(1)[0][1] / len(accused_names)
        if most_common_freq > 0.6:
            accused_names = [Counter(accused_names).most_common(1)[0][0]]
        else:
            accused_names = kill_doubles(accused_names)
    if not accused_names:
        accused_names = "undefined"
    return accused_names


def get_metadict(doc_str):
    """ собираем все в словарь """
    metadict = {}
    metadict["date"] = get_date(doc_str)
    metadict["number"] = get_number(doc_str)
    metadict["court"] = get_court(doc_str)
    metadict["region"] = get_city(doc_str)
    metadict["judge"] = get_judge(doc_str)
    metadict["article"] = get_article(doc_str)
    metadict["accused"] = get_accused_name(doc_str)
    return metadict