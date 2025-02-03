import math

from m5.objects import *

class L3sCache(L2sCache_Controller):
    _version = 0

    @classmethod
    def versionCount(cls):
        cls._version += 1
        return cls._version - 1
    
    def __init__(
        self, 
        system, 
        ruby_system,
        l3_size,
        l3_assoc,
        l2s_request_latency,
        l2s_response_latency,
        to_l1_latency,
        numL3caches,
    ):

        super().__init__()

        self.version = self.versionCount()
        self.L2sCache = RubyCache(
            size=l3_size,
            assoc=l3_assoc,
            start_index_bit=self.getIndexBit(system, numL3caches),
        )
        self.ruby_system = ruby_system
        self.l2s_request_latency = l2s_request_latency
        self.l2s_response_latency = l2s_response_latency
        self.to_l1_latency = to_l1_latency
        self.connectQueues(ruby_system)

    def getIndexBit(self, system, numL3caches):
        l3s_bits = int(math.log(numL3caches, 2))
        bits = int(math.log(system.cache_line_size, 2)) + l3s_bits
        return bits
    
    
    def connectQueues(self, ruby_system):
        self.DirRequestFromL2scache = MessageBuffer(ordered=False)
        self.DirRequestFromL2scache.in_port = ruby_system.network.out_port
        self.L1RequestFromL2scache = MessageBuffer(ordered=False)
        self.L1RequestFromL2scache.in_port = ruby_system.network.out_port
        self.responseFromL2scache = MessageBuffer(ordered=False)
        self.responseFromL2scache.in_port = ruby_system.network.out_port
        # self.unblockToL2sCache = MessageBuffer()
        # self.unblockToL2sCache.in_port = ruby_system.network.out_port
        self.L1RequestToL2scache = MessageBuffer(ordered=False)
        self.L1RequestToL2scache.out_port = ruby_system.network.in_port
        self.responseToL2scache = MessageBuffer(ordered=False)
        self.responseToL2scache.out_port = ruby_system.network.in_port