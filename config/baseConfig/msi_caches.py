# Copyright (c) 2017 Jason Power
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

""" This file creates a set of Ruby caches, the Ruby network, and a simple
point-to-point topology.
See Part 3 in the Learning gem5 book:
http://gem5.org/documentation/learning_gem5/part3/MSIintro

IMPORTANT: If you modify this file, it's likely that the Learning gem5 book
           also needs to be updated. For now, email Jason <jason@lowepower.com>

"""

import math
import os

import m5
from m5.defines import buildEnv
from m5.objects import *
from m5.util import (
    fatal,
    panic,
)

from .L1cache import L1Cache
from .L2cache import L2Cache
from .L3pcache import L3Cache
# from .L3scache import L3sCache
from .Dir import DirController
# from .testNetwork import MyNetwork
m5.util.addToPath("../")

from src.python.gem5.components.cachehierarchies.ruby.topologies.simple_pt2pt import SimplePt2Pt

class MyCacheSystem(RubySystem):
    def __init__(self):
        if not "RUBY_PROTOCOL_MSI" in buildEnv:
            fatal("This system assumes MSI from learning gem5!")

        super().__init__()

    def setup(
        self, 
        system, 
        cpus, 
        l1i_size: str,
        l1i_assoc: str,
        l1d_size: str,
        l1d_assoc: str,
        l2_size: str,
        l2_assoc: str,
        l3_size: str,
        l3_assoc: str,
        l1_request_latency: int, 
        l1_response_latency: int, 
        to_l2_latency: int, 
        l2_request_latency: int, 
        l2_response_latency: int, 
        to_l1_latency: int, 
        numL3caches: int, 
        mem_ctrls,
    ):
        """Set up the Ruby cache subsystem. Note: This can't be done in the
        constructor because many of these items require a pointer to the
        ruby system (self). This causes infinite recursion in initialize()
        if we do this in the __init__.
        """
        # Ruby's global network.
        self.network = SimplePt2Pt(self)

        # MSI uses 3 virtual networks. One for requests (lowest priority), one
        # for responses (highest priority), and one for "forwards" or
        # cache-to-cache requests. See *.sm files for details.
        self.number_of_virtual_networks = 4
        self.network.number_of_virtual_networks = 4

        # There is a single global list of all of the controllers to make it
        # easier to connect everything to the global network. This can be
        # customized depending on the topology/network requirements.
        # Create one controller for each L1 cache (and the cache mem obj.)
        # Create a single directory controller (Really the memory cntrl)
        self.controllers = [
            L1Cache(
                system, 
                self, 
                cpu,
                l1i_size,
                l1i_assoc,
                l1d_size,
                l1d_assoc,
            ) for cpu in cpus] + [
            L2Cache(
                system, 
                self, 
                cpu,
                l2_size,
                l2_assoc,
                l1_request_latency,
                l1_response_latency,
                to_l2_latency,
                numL3caches,
            ) for cpu in cpus ] + [
            L3Cache(
                system, 
                self,
                l3_size,
                l3_assoc,
                l2_request_latency,
                l2_response_latency,
                to_l1_latency,   
                numL3caches,
            ) for _ in range(numL3caches) ] + [
            DirController(
                self, 
                system.mem_ranges, 
                mem_ctrls
            ) ]

        for i in range(len(cpus)):
            self.controllers[i].bufferToL1 = self.controllers[i+len(cpus)].bufferFromL0
            self.controllers[i].bufferFromL1 = self.controllers[i+len(cpus)].bufferToL0
        
        startL2p = 2 * len(cpus)
        startL2s = startL2p + numL3caches
        directory = startL2s + numL3caches

        # for i in range(startL2p, startL2s):
        #     self.controllers[i].DirRequestFromL2Cache = self.controllers[directory].requestToDirFromL2p
        
        # for i in range(startL2s, directory):
        #     self.controllers[i].DirRequestFromL2Cache = self.controllers[directory].requestToDirFromL2s
        # Create one sequencer per CPU. In many systems this is more
        # complicated since you have to create sequencers for DMA controllers
        # and other controllers, too.
        self.sequencers = [
            RubySequencer(
                version=i,
                # I/D cache is combined and grab from ctrl
                dcache=self.controllers[i].Dcache,
                clk_domain=self.controllers[i].clk_domain,
                ruby_system=self,
            )
            for i in range(len(cpus))
        ]

        # We know that we put the controllers in an order such that the first
        # N of them are the L1 caches which need a sequencer pointer
        for i, c in enumerate(self.controllers[0 : len(self.sequencers)]):
            c.sequencer = self.sequencers[i]

        self.num_of_sequencers = len(self.sequencers)

        # Create the network and connect the controllers.
        # NOTE: This is quite different if using Garnet!
        self.network.connectControllers(self.controllers)
        self.network.setup_buffers()

        # Set up a proxy port for the system_port. Used for load binaries and
        # other functional-only things.
        self.sys_port_proxy = RubyPortProxy(ruby_system=self)
        system.system_port = self.sys_port_proxy.in_ports

        # Connect the cpu's cache, interrupt, and TLB ports to Ruby
        for i, cpu in enumerate(cpus):
            self.sequencers[i].connectCpuPorts(cpu)
