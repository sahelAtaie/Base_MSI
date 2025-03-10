import math

from m5.objects import *

from m5.util import (
    fatal,
    panic,
)

class L1Cache(L0Cache_Controller):

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
        l1i_size,
        l1i_assoc,
        l1d_size,
        l1d_assoc,
    ):
        """CPUs are needed to grab the clock domain and system is needed for
        the cache block size.
        """
        super().__init__()

        self.version = self.versionCount()

        self.Icache = RubyCache(
            size=l1i_size,
            assoc=l1i_assoc,
            start_index_bit=self.getBlockSizeBits(system),
            is_icache=True,
            replacement_policy=LRURP(),
        )
        
        self.Dcache = RubyCache(
            size=l1d_size,
            assoc=l1d_assoc,
            start_index_bit=self.getBlockSizeBits(system),
            is_icache=False,
            replacement_policy=LRURP(),
        )

        self.clk_domain = cpu.clk_domain
        self.prefetcher = RubyPrefetcher()
        self.send_evictions = self.sendEvicts(cpu)
        self.enable_prefetch = False
        self.ruby_system = ruby_system
        self.connectQueues(ruby_system)

    def getBlockSizeBits(self, system):
        bits = int(math.log(system.cache_line_size, 2))
        if 2**bits != system.cache_line_size.value:
            panic("Cache line size not a power of 2!")
        return bits

    def sendEvicts(self, cpu):
        """True if the CPU model or ISA requires sending evictions from caches
        to the CPU. Two scenarios warrant forwarding evictions to the CPU:
        1. The O3 model must keep the LSQ coherent with the caches
        2. The x86 mwait instruction is built on top of coherence
        3. The local exclusive monitor in ARM systems

        As this is an X86 simulation we return True.
        """
        return True

    def connectQueues(self, ruby_system):
        """Connect all of the queues for this controller."""
        self.prefetchQueue = MessageBuffer()
        self.mandatoryQueue = MessageBuffer()
        self.optionalQueue = MessageBuffer()

        # bufferToL0 and bufferFromL0 are ruby backend terminology.
        # In stdlib terms, they are bufferToL2 and bufferFromL2 respectively.
        # These buffers are connections between L0 cache and L2 cache.
        # Later on, we'll need to connect those buffers to L2.
        self.bufferToL1 = MessageBuffer(ordered=False)
        # self.bufferToL1.out_port = ruby_system.network.in_port
        self.bufferFromL1 = MessageBuffer(ordered=False)
        # self.bufferFromL1.in_port = ruby_system.network.out_port

