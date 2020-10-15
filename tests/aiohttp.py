# Copyright (C) 2018 Julien Hartmann
# This program is distributed under the MIT license, a copy of which you should
# have receveived along with it. If not, see <https://opensource.org/licenses/MIT>.
#
import asyncio
import collections
import inspect
import socket
import weakref

import aiohttp
import aiohttp.test_utils
import aiohttp.web
import pytest

# ----------------------------------------------------------------------------

_RedirectContext = collections.namedtuple("RedirectContext", "add_server session")


@pytest.fixture
async def http_redirect(ssl_certificate):
    """ An HTTP ClientSession fixture that redirects requests to local test servers """
    resolver = FakeResolver()
    connector = aiohttp.TCPConnector(
        resolver=resolver,
        ssl=ssl_certificate.client_context(),
        use_dns_cache=False,
    )
    async with aiohttp.ClientSession(connector=connector) as session:
        yield _RedirectContext(add_server=resolver.add, session=session)


class FakeResolver:
    """aiohttp resolver that hijacks a set of uris

    :param servers: a mapping of remote host:port to redirect to local servers.
    :type servers: dict(tuple(str, int), int)
    """

    __slots__ = ("_servers",)

    def __init__(self, servers=None):
        self._servers = servers or {}

    def add(self, host, port, target):
        """ Add an entry to the resolver """
        self._servers[host, port] = target

    async def resolve(self, host, port=0, family=socket.AF_INET):
        """ Resolve a host:port pair into a connectable address """
        try:
            fake_port = self._servers[host, port]
        except KeyError:
            raise OSError("Fake DNS lookup failed: no fake server known for %s" % host)
        return [
            {
                "hostname": host,
                "host": "127.0.0.1",
                "port": fake_port,
                "family": socket.AF_INET,
                "proto": 0,
                "flags": socket.AI_NUMERICHOST,
            }
        ]


# ----------------------------------------------------------------------------


class CaseControlledTestServer(aiohttp.test_utils.RawTestServer):
    """ Test server that relies on test case to supply responses and control timing """

    def __init__(self, *, ssl=None, **kwargs):
        super().__init__(self._handle_request, **kwargs)
        self._ssl = ssl
        self._requests = asyncio.Queue()
        self._responses = {}

    async def start_server(self, **kwargs):
        kwargs.setdefault("ssl", self._ssl)
        await super().start_server(**kwargs)

    async def close(self):
        for future in self._responses.values():
            future.cancel()
        await super().close()

    async def _handle_request(self, request):
        self._responses[id(request)] = response = asyncio.Future()
        self._requests.put_nowait(request)
        try:
            return await response
        finally:
            del self._responses[id(request)]

    @property
    def awaiting_request_count(self):
        return self._requests.qsize()

    async def receive_request(self, *, timeout=None):
        """Wait until the test server receives a request

        :param float timeout: Bail out after that many seconds.
        :return: received request, not yet serviced.
        :rtype: aiohttp.web.BaseRequest
        :see: :meth:`send_response`
        """
        return await asyncio.wait_for(self._requests.get(), timeout=timeout)

    def send_response(self, request, *args, **kwargs):
        """Reply to a received request.

        :param request: the request to respond to.
        :param args: forwarded to :class:`aiohttp.web.Response`.
        :param kwargs: forwarded to :class:`aiohttp.web.Response`.
        """
        self._responses[id(request)].set_result(aiohttp.web.Response(*args, **kwargs))
