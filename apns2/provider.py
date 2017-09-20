# coding: utf-8
from client import APNSClient


class Provider(APNSClient):

    def __init__(self, mode, jwt):

        APNSClient.__init__(self, mode, None)
        self._jwt = jwt

    def get_headers(self, n, topic = None):
        headers = APNSClient.get_headers(self, n, topic)
        headers["authorization"] = "bearer " + str(self._jwt)

        return headers
