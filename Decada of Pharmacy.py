import sys
import os
from io import BytesIO
import requests
from PIL import Image
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtGui import QPixmap


def get_ll(address):
    toponym_to_find = address

    geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"

    geocoder_params = {
        "apikey": '40d1649f-0493-4b70-98ba-98533de7710b',
        "geocode": toponym_to_find,
        "format": "json"}

    response = requests.get(geocoder_api_server, params=geocoder_params)

    if not response:
        return False

    json_response = response.json()
    try:
        toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
        toponym_coordinates = toponym["Point"]["pos"]
    except Exception:
        return False

    return toponym_coordinates


def get_image(address):
    try:
        address_ll = ','.join(get_ll(address).split())
    except Exception:
        return False

    search_params = {
        "apikey": "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3",
        "text": "аптека",
        "lang": "ru_RU",
        "ll": address_ll,
        "type": "biz"
    }

    response = requests.get("https://search-maps.yandex.ru/v1/", params=search_params)
    if not response:
        return False
    json_response = response.json()
    pts = []
    points_1 = []
    points_2 = []
    organizations = json_response["features"]
    try:
        for organization in organizations:
            point = organization["geometry"]["coordinates"]
            org_point = "{0},{1}".format(point[0], point[1])
            points_1.append(float(point[0]))
            points_2.append(float(point[1]))
            org_availability = organization["properties"]["CompanyMetaData"]["Hours"]["Availabilities"]
            if 'TwentyFourHours' in org_availability[0].keys():
                pts.append(f'{org_point},pm2gnm')
            elif 'Intervals' in org_availability[0].keys():
                pts.append(f'{org_point},pm2blm')
            else:
                pts.append(f'{org_point},pm2grm')
    except Exception:
        return False

    delta = str(max(max(points_1) - min(points_1), max(points_2) - min(points_2)))
    map_params = {
        "ll": address_ll,
        "spn": ",".join([delta, delta]),
        "l": "map",
        "pt": '~'.join(pts)
    }

    map_api_server = "http://static-maps.yandex.ru/1.x/"
    response = requests.get(map_api_server, params=map_params)
    image = Image.open(BytesIO(response.content))
    image.save('chemistry_near.png')
    return image


class Example(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('10_aptek.ui', self)
        self.ok_but.clicked.connect(self.load)

    def load(self):
        if get_image(self.address_line.text()):
            get_image(self.address_line.text())
            pixmap = QPixmap('chemistry_near.png')
            self.apt_photo.setPixmap(pixmap)
            os.remove('chemistry_near.png')
            self.statusBar().showMessage('')
        else:
            self.statusBar().showMessage('Что-то пошло не так')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example()
    ex.show()
    sys.exit(app.exec_())