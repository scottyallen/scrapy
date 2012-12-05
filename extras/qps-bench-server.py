#!/usr/bin/env python
from time import time
from collections import deque
from twisted.web.server import Site, NOT_DONE_YET
from twisted.web.resource import Resource
from twisted.internet import reactor


class Root(Resource):

    def __init__(self):
        Resource.__init__(self)
        self.concurrent = 0
        self.tail = deque(maxlen=10)
        self._reset_stats()

    def _reset_stats(self):
        self.tail.clear()
        self.start = self.lastmark = self.lasttime = time()

    def getChild(self, request, name):
        return self

    def render(self, request):
        now = time()
        delta = now - self.start

        self.tail.appendleft(delta)
        self.lasttime = now
        self.concurrent += 1

        tail_delta = self.tail[0] - self.tail[-1]
        if tail_delta:
            qps = (len(self.tail) - 1) / tail_delta
            print('time={0} samplesize={1} concurrent={2} qps={3:0.2f}'.format(delta,
                                                                               len(self.tail),
                                                                               self.concurrent,
                                                                               qps))

        if 'sleep' in request.args:
            sleep = float(request.args['sleep'][0])
            reactor.callLater(sleep, self._finish, request)
            return NOT_DONE_YET

        self.concurrent -= 1
        return ''

    def _finish(self, request):
        self.concurrent -= 1
        if not request.finished and not request._disconnected:
            request.finish()


root = Root()
factory = Site(root)
reactor.listenTCP(8880, factory)
reactor.run()
