from m5.objects import *
from m5.util import (
    fatal,
    panic,
)

class DirController(Directory_Controller):

    _version = 0

    @classmethod
    def versionCount(cls):
        cls._version += 1  # Use count for this particular type
        return cls._version - 1

    def __init__(self, ruby_system, ranges, mem_ctrls):
        """ranges are the memory ranges assigned to this controller."""
        if len(mem_ctrls) > 1:
            panic("This cache system can only be connected to one mem ctrl")
        super().__init__()
        self.version = self.versionCount()
        self.addr_ranges = ranges
        self.ruby_system = ruby_system
        self.directory = RubyDirectoryMemory()
        # Connect this directory to the memory side.
        self.memory_out_port = mem_ctrls[0].port
        self.connectQueues(ruby_system)

    def connectQueues(self, ruby_system):
        self.requestToDir = MessageBuffer()
        self.requestToDir.in_port = ruby_system.network.out_port
        self.responseToDir = MessageBuffer()
        self.responseToDir.in_port = ruby_system.network.out_port
        self.responseFromDir = MessageBuffer()
        self.responseFromDir.out_port = ruby_system.network.in_port
        self.requestToMemory = MessageBuffer()
        self.responseFromMemory = MessageBuffer()
