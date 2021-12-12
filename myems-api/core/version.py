import falcon
import simplejson as json


class VersionItem:
    @staticmethod
    def __init__():
        """"Initializes VersionItem"""
        pass

    @staticmethod
    def on_options(req, resp, id_):
        resp.status = falcon.HTTP_200

    @staticmethod
    def on_get(req, resp):

        result = {"version": 'MyEMS v1.5.0 Community Edition',
                  "release-date": '2021-12-12',
                  "website": "https://myems.io"}
        resp.text = json.dumps(result)

