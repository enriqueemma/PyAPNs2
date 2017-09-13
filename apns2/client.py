# coding: utf-8

from notification import Notification
from response import Response

from hyper.tls import init_context
from hyper import HTTP20Connection
import json
from threading import RLock

MODE_PROD = "prod"
MODE_DEV = "dev"


class APNSClient(object):

    def __init__(self, mode, certfile):

        if mode == MODE_PROD:
            self.host = "api.push.apple.com"
        elif mode == MODE_DEV:
            self.host = "api.development.push.apple.com"
        else:
            raise ValueError("invalid mode: {}".format(mode))

        self._lock = RLock()

        self.conn = HTTP20Connection(
            host=self.host,
            port=443,
            secure=True,
            ssl_context=init_context(cert=certfile),
            force_proto="h2"
        )

    def get_headers(self, n, topic = None):
        headers = {"Content-Type": "application/json; charset=utf-8"}
        if topic:
            headers["apns-topic"] = str(topic)
        if n.apns_id:
            headers["apns-id"] = str(n.apns_id)
        if n.collapse_id:
            headers["apns-collapse-id"] = str(n.collapse_id)
        if n.priority:
            headers["apns-priority"] = str(n.priority)
        if n.expiration:
            headers["apns-expiration"] = str(n.expiration)
        return headers

    def push(self, n, device_token, topic=None):

        response = None
        apns_response = None

        url = "/3/device/{}".format(device_token)
        payload = n.payload.to_json()
        headers = self.get_headers(n, topic=topic)

        # la llamada es thread - safe.
        stream_id = self.conn.request(
            method="POST",
            url=url,
            body=payload,
            headers=headers,
        )
        apns_response = self.conn.get_response(stream_id=stream_id)

        apns_ids = apns_response.headers.get("apns-id")
        apns_id = apns_ids[0] if apns_ids else None
        response = Response(status_code=apns_response.status, apns_id=apns_id)

        if apns_response.status != 200:
            body = apns_response.read()
            apns_data = json.loads(body)
            response.timestamp = apns_data.get("timestamp")
            response.reason = apns_data["reason"]

        return response
