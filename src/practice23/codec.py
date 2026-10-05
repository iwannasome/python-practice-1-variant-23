"""Типизированное XML-тело: int, str и вложенные list.

Строка хранится в base64 от UTF-8: XML 1.0 не допускает NUL и некоторые
управляющие символы, а XML-парсер нормализует CR. base64 сохраняет
данные без потерь. surrogatepass также сохраняет одиночные суррогаты
Python str. Внешние сущности и DTD запрещены парсером defusedxml.
"""

import base64
import binascii
from xml.etree import ElementTree as ET

from defusedxml.common import DefusedXmlException
from defusedxml.ElementTree import fromstring

MAX_DEPTH = 32


def _element(value, depth=0):
    """Рекурсивно создать XML-элемент с явным типом значения."""
    if depth > MAX_DEPTH:
        raise ValueError("Слишком большая вложенность XML")
    if type(value) is list:
        node = ET.Element("list")
        node.extend(_element(item, depth + 1) for item in value)
        return node
    if type(value) is int:
        node = ET.Element("int")
        node.text = str(value)
        return node
    if type(value) is str:
        node = ET.Element("str")
        raw = value.encode("utf-8", errors="surrogatepass")
        node.text = base64.b64encode(raw).decode("ascii")
        return node
    raise ValueError("XML поддерживает только int, str и list")


def encode(value):
    """Сериализовать значение в XML UTF-8 с декларацией кодировки."""
    return ET.tostring(_element(value), encoding="utf-8", xml_declaration=True)


def _value(node, depth=0):
    """Проверить грамматику XML и отсутствие лишних полей."""
    if depth > MAX_DEPTH or node.attrib or (node.tail or "").strip():
        raise ValueError("Недопустимая структура XML")
    if node.tag == "list":
        if (node.text or "").strip():
            raise ValueError("В list допустимы только дочерние элементы")
        return [_value(child, depth + 1) for child in node]
    if len(node):
        raise ValueError("Скалярный элемент не может содержать элементы")
    if node.tag == "int":
        return int(node.text or "")
    if node.tag == "str":
        raw = base64.b64decode(node.text or "", validate=True)
        return raw.decode("utf-8", errors="surrogatepass")
    raise ValueError("Неизвестный XML-тип")


def decode(body):
    """Восстановить значение либо сообщить контролируемую ошибку XML."""
    try:
        node = fromstring(body, forbid_dtd=True)
        return _value(node)
    except (
        ET.ParseError,
        DefusedXmlException,
        binascii.Error,
        UnicodeError,
        RecursionError,
    ) as error:
        raise ValueError("Некорректное XML-тело") from error
