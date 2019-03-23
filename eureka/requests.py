from eureka import __version__ as client_version
import gzip

try:
    # Python 3 and later
    from urllib.request import Request as UrllibReq
    from urllib.request import build_opener
    from urllib.error   import HTTPError
    from io import StringIO
except ImportError:
    # Python 2
    from urllib2 import Request as UrllibReq
    from urllib2 import build_opener, HTTPError
    import StringIO

class EurekaHTTPException(Exception):
    pass


class Request(UrllibReq):
    """
    Instead of requiring a version of `requests`, we use this easy wrapper around urllib2 to avoud possible
    version conflicts with people own software.
    """
    def __init__(self, url, method="GET", data=None, headers=None,
                 origin_req_host=None, unverifiable=False):
        self.method = method
        self._opener = build_opener()
        self._opener.addheaders = [
            ('User-agent', 'python-eureka v%s' % client_version)
        ]
        UrllibReq.__init__(self, url, data=data, headers=headers or {},
                                 origin_req_host=origin_req_host, unverifiable=unverifiable)

    def get_method(self):
        return self.method

    @classmethod
    def create(cls, method, url, data=None, headers=None):
        headers = headers or {}
        request = cls(url, method, data=data, headers=headers)
        try:
            response = request._opener.open(request)
        except HTTPError as e:
            return Response(e.code, e.read(), url, method)

        content = response.read()
        info = response.info()
        if "gzip" in info.get("Content-Encoding", "").lower():
            data = StringIO.StringIO(content)
            gzipper = gzip.GzipFile(fileobj=data)
            content = gzipper.read()

        return Response(response.getcode(), content, url, method)


class Response(object):
    def __init__(self, status_code, content, url, method):
        self.status_code = status_code
        self.content = content
        self.url = url
        self.method = method

    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            raise EurekaHTTPException(u"HTTP %s: %s" % (self.status_code, self.content))

    def __repr__(self):
        return "<Response: [%s]>" % self.status_code


def get(url, data=None, headers=None):
    return Request.create("GET", url, data, headers)


def post(url, data=None, headers=None):
    return Request.create("POST", url, data, headers)


def put(url, data=None, headers=None):
    return Request.create("PUT", url, data, headers)


def delete(url, data=None, headers=None):
    return Request.create("DELETE", url, data, headers)
