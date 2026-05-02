from dataclasses import dataclass
from http.client import HTTPConnection
from xml.dom import minidom
import base64
import random
import typing
import urllib.parse


@dataclass
class Client:
    conn: HTTPConnection

    @classmethod
    def create(cls, host: str, port: int):
        return Client(conn=HTTPConnection(host, port))

    def post(
        self, path: str, params: dict | None = None, headers: dict | None = None
    ) -> tuple[int, typing.Any]:
        if params is not None:
            if isinstance(params, dict):
                params = urllib.parse.urlencode(params)

        self.conn.request("POST", path, params or {}, headers or {})
        resp = self.conn.getresponse()
        return resp.status, resp.read().decode("utf-8")


@dataclass
class Bosh:

    client: Client
    rid: int
    sid: str | None

    @classmethod
    def create(cls):
        raise NotImplementedError

    @classmethod
    def greet(cls, client: Client):
        bosh = Bosh(client=client, rid=random.randint(0, 999**2), sid=None)
        stanza = minidom.Document()

        body = stanza.createElement("body")
        body.setAttribute("rid", str(bosh.rid))
        body.setAttribute("to", client.conn.host)
        body.setAttribute("xml:lang", "en")
        body.setAttribute("wait", "60")
        body.setAttribute("hold", "1")
        body.setAttribute("content", "text/xml; charset=utf-8")
        body.setAttribute("ver", "1.6")

        body.appendChild(stanza.createTextNode(""))

        stanza.appendChild(body)

        doc = bosh.exchange(stanza)
        sid = doc.getAttribute("sid")

        bosh.sid = sid

        return bosh

    def exchange(self, stanza: minidom.Document) -> minidom.Document:
        self.rid += 1
        pretty = stanza.toprettyxml()
        _, res = self.client.post("/bosh", pretty, {"content-type": "application/xml"})
        return minidom.parseString(res).documentElement

    def login(self, usr: str, pwd: str) -> str | None:
        stanza = minidom.Document()

        body = stanza.createElement("body")
        body.setAttribute("rid", str(self.rid))
        body.setAttribute("sid", self.sid)
        body.setAttribute("xmlns", "http://jabber.org/protocol/httpbind")

        auth = stanza.createElement("auth")
        auth.setAttribute("xmlns", "urn:ietf:params:xml:ns:xmpp-sasl")
        auth.setAttribute("mechanism", "PLAIN")

        auth.appendChild(
            stanza.createTextNode(
                base64.b64encode(bytes(f"\0{usr}\0{pwd}", "utf-8")).decode("utf-8")
            )
        )

        body.appendChild(auth)
        stanza.appendChild(body)
        error: str | None = None

        _ = self.exchange(stanza)

        if _:
            _ = next(iter(_.getElementsByTagName("failure")), None)
            if _:
                _ = next(iter(_.getElementsByTagName("text")), None)
                error = _.firstChild.nodeValue

        return error


if __name__ == "__main__":
    # for example

    c = Client.create("localhost", 5280)
    b = Bosh.greet(c)

    print(b.login(usr="user1", pwd="user1"))
