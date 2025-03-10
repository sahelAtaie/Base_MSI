import math

from m5.objects import *

class L3Cache(L2Cache_Controller):
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
        l2_request_latency,
        l2_response_latency,
        to_l1_latency,    
        numL3caches,
    ):

        super().__init__()

        self.version = self.versionCount()
        self.L2cache = RubyCache(
            size=l3_size,
            assoc=l3_assoc,
            start_index_bit=self.getIndexBit(system, numL3caches),
        )
        self.ruby_system = ruby_system
        self.l2_request_latency = l2_request_latency
        self.l2_response_latency = l2_response_latency
        self.to_l1_latency = to_l1_latency
        self.connectQueues(ruby_system)

    def getIndexBit(self, system, numL3caches):
        l3p_bits = int(math.log(numL3caches, 2))
        bits = int(math.log(system.cache_line_size, 2)) + l3p_bits
        return bits

    def connectQueues(self, ruby_system):
        self.DirRequestFromL2Cache = MessageBuffer(ordered=False)
        self.DirRequestFromL2Cache.in_port = ruby_system.network.out_port
        self.L1RequestFromL2Cache = MessageBuffer(ordered=False)
        self.L1RequestFromL2Cache.in_port = ruby_system.network.out_port
        self.responseFromL2Cache = MessageBuffer(ordered=False)
        self.responseFromL2Cache.in_port = ruby_system.network.out_port
        self.unblockToL2Cache = MessageBuffer(ordered=False)
        self.unblockToL2Cache.out_port = ruby_system.network.in_port
        self.L1RequestToL2Cache = MessageBuffer(ordered=False)
        self.L1RequestToL2Cache.out_port = ruby_system.network.in_port
        self.responseToL2Cache = MessageBuffer(ordered=False)
        self.responseToL2Cache.out_port = ruby_system.network.in_port