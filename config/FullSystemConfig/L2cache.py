import math
from m5.objects import *

from m5.util import (
    fatal,
    panic,
)

class L2Cache(L1Cache_Controller):
    
    _version = 0

    @classmethod
    def versionCount(cls):
        cls._version += 1  # Use count for this particular type
        return cls._version - 1

    def __init__(
        self, 
        system, 
        ruby_system, 
        cpu,
        l2_size,
        l2_assoc,
        l1_request_latency,
        l1_response_latency,
        to_l2_latency,
        numL3caches,
    ):
        
        super().__init__()

        self.version = self.versionCount()
        # This is the cache memory object that stores the cache data and tags
        self.cache = RubyCache(
            size=l2_size,
            assoc=l2_assoc,
            start_index_bit=self.getBlockSizeBits(system),
        )
        self.clk_domain = cpu.clk_domain
        self.ruby_system = ruby_system
        self.l2_select_num_bits = int(math.log(numL3caches, 2))
        self.l1_request_latency = l1_request_latency
        self.l1_response_latency = l1_response_latency
        self.to_l2_latency = to_l2_latency
        self.connectQueues(ruby_system)

    def getBlockSizeBits(self, system):
        bits = int(math.log(system.cache_line_size, 2))
        if 2**bits != system.cache_line_size.value:
            panic("Cache line size not a power of 2!")
        return bits

    def connectQueues(self, ruby_system):
        self.mandatoryQueue = MessageBuffer()
        self.optionalQueue = MessageBuffer()

        # In the below terms, L2 are ruby backend terminology.
        # They are L3 in stdlib.

        # request from/to L0
        self.bufferFromL0 = MessageBuffer(ordered=False)
        # self.bufferFromL0.in_port = ruby_system.network.out_port
        self.bufferToL0 = MessageBuffer(ordered=False)
        # self.bufferToL0.out_port = ruby_system.network.in_port

        # Request from/to L2 buffers
        self.requestFromL2 = MessageBuffer(ordered=False)
        self.requestFromL2.in_port = ruby_system.network.out_port
        self.requestToL2 = MessageBuffer(ordered=False)
        self.requestToL2.out_port = ruby_system.network.in_port

        # Response from/to L2 buffers
        self.responseFromL2 = MessageBuffer(ordered=False)
        self.responseFromL2.in_port = ruby_system.network.out_port
        self.responseToL2 = MessageBuffer(ordered=False)
        self.responseToL2.out_port = ruby_system.network.in_port

        # Unblock to L2 buffer
        self.unblockToL2 = MessageBuffer(ordered=False)
        self.unblockToL2.out_port = ruby_system.network.in_port
