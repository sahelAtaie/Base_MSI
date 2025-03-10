from src.python.gem5.utils.requires import requires
from src.python.gem5.components.boards.x86_board import X86Board
from src.python.gem5.components.memory.single_channel import SingleChannelDDR3_1600
from src.python.gem5.components.processors.simple_switchable_processor import SimpleSwitchableProcessor
from src.python.gem5.components.processors.simple_processor import SimpleProcessor
from src.python.gem5.components.processors.cpu_types import CPUTypes
from src.python.gem5.coherence_protocol import CoherenceProtocol
from src.python.gem5.isas import ISA
from src.python.gem5.resources.resource import Resource
from src.python.gem5.simulate.simulator import Simulator
from src.python.gem5.simulate.exit_event import ExitEvent
# from src.python.gem5.components.cachehierarchies.ruby.cache_hierarchy import RubyCacheHierarchy
# from src.python.gem5.components.workloads.binary_workload import BinaryWorkload

import m5
from m5.objects import *
import m5.util
import argparse
import sys

# Make sure we can find your cache hierarchy
m5.util.addToPath("../../")
from config.FullSystemConfig.msi_caches import MyCacheSystem

class MSICacheWrapper(RubySystem):
    """
    A wrapper class that adapts your MyCacheSystem to work with the 
    component-based gem5 APIs
    """
    def __init__(
        self,
        l1i_size,
        l1i_assoc,
        l1d_size,
        l1d_assoc,
        l2_size,
        l2_assoc,
        l3_size,
        l3_assoc,
        num_l3_caches,
        l1_request_latency,
        l1_response_latency,
        to_l2_latency,
        l2_request_latency,
        l2_response_latency,
        to_l1_latency,
    ):
        """Initialize the cache wrapper with parameters"""
        super().__init__(
            protocol=CoherenceProtocol.MESI_THREE_LEVEL
        )
        
        self.l1i_size = l1i_size
        self.l1i_assoc = l1i_assoc
        self.l1d_size = l1d_size
        self.l1d_assoc = l1d_assoc
        self.l2_size = l2_size
        self.l2_assoc = l2_assoc
        self.l3_size = l3_size
        self.l3_assoc = l3_assoc
        self.num_l3_caches = num_l3_caches
        self.l1_request_latency = l1_request_latency
        self.l1_response_latency = l1_response_latency
        self.to_l2_latency = to_l2_latency
        self.l2_request_latency = l2_request_latency
        self.l2_response_latency = l2_response_latency
        self.to_l1_latency = to_l1_latency

    def incorporate_cache(self, board):
        """
        This method is called by gem5 to include this cache hierarchy in the system
        """
        # Create Ruby system and set it as the board's cache hierarchy
        ruby_system = MyCacheSystem()
        board.system.ruby = ruby_system
        board.cache_hierarchy = ruby_system
        
        # Get memory controllers from the memory system
        memory_controllers = board.get_memory().get_memory_controllers()
        
        # Set up the cache system using the board's system and cores
        ruby_system.setup(
            board.system, 
            board.get_processor().get_cores(), 
            self.l1i_size,
            self.l1i_assoc,
            self.l1d_size,
            self.l1d_assoc,
            self.l2_size,
            self.l2_assoc,
            self.l3_size,
            self.l3_assoc,
            self.l1_request_latency,
            self.l1_response_latency,
            self.to_l2_latency,
            self.l2_request_latency,
            self.l2_response_latency,
            self.to_l1_latency,
            self.num_l3_caches,
            memory_controllers,
        )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cpu_type", type=str, default="X86O3", 
                       choices=["X86O3", "TIMING", "KVM", "ATOMIC"],
                       help="Type of CPU to use")
    parser.add_argument("--l1i_size", type=str, default="32kB", help="L1 instruction cache size")
    parser.add_argument("--l1i_assoc", type=int, default=2, help="L1 instruction cache associativity")
    parser.add_argument("--l1d_size", type=str, default="32kB", help="L1 data cache size")
    parser.add_argument("--l1d_assoc", type=int, default=2, help="L1 data cache associativity")
    parser.add_argument("--l2_size", type=str, default="256kB", help="L2 cache size")
    parser.add_argument("--l2_assoc", type=int, default=8, help="L2 cache associativity")
    parser.add_argument("--l3_size", type=str, default="256kB", help="L3 cache size")
    parser.add_argument("--l3_assoc", type=int, default=8, help="L3 cache associativity")
    parser.add_argument("--numL3caches", type=int, default=64, help="Number of L3 caches")
    parser.add_argument("--l1_request_latency", type=int, default=4, help="L1 request latency in cycles")
    parser.add_argument("--l1_response_latency", type=int, default=4, help="L1 response latency in cycles")
    parser.add_argument("--to_l2_latency", type=int, default=2, help="Latency to L2 private cache in cycles")
    parser.add_argument("--l2_request_latency", type=int, default=4, help="L2 private request latency in cycles")
    parser.add_argument("--l2_response_latency", type=int, default=4, help="L2 private response latency in cycles")
    parser.add_argument("--to_l1_latency", type=int, default=2, help="Latency back to L1 cache in cycles")
    parser.add_argument("--num_cores", type=int, default=4, help="Number of CPU cores")
    parser.add_argument("--binary", type=str, default="/home/sahel/NPB3.3.1/NPB3.3-SER/bin/cg.W.x", 
                       help="Path to binary for SE mode")
    parser.add_argument("--mem_size", type=str, default="4GiB", help="System memory size")
    parser.add_argument("--full_system", action="store_true", help="Run in full system mode")
    
    args = parser.parse_args()

    # Map CPU type string to CPUTypes enum
    cpu_type_map = {
        "X86O3": CPUTypes.O3,
        "TIMING": CPUTypes.TIMING,
        "KVM": CPUTypes.KVM,
        "ATOMIC": CPUTypes.ATOMIC,
    }
    
    cpu_type = cpu_type_map[args.cpu_type]
    
    # Define requirements for the simulation
    requires(
        isa_required=ISA.X86,
        coherence_protocol_required=CoherenceProtocol.MESI_THREE_LEVEL,
        kvm_required=(cpu_type == CPUTypes.KVM)
    )
    
    # Create the cache hierarchy with your parameters
    cache_hierarchy = MSICacheWrapper(
        l1i_size=args.l1i_size,
        l1i_assoc=args.l1i_assoc,
        l1d_size=args.l1d_size,
        l1d_assoc=args.l1d_assoc,
        l2_size=args.l2_size,
        l2_assoc=args.l2_assoc,
        l3_size=args.l3_size,
        l3_assoc=args.l3_assoc,
        num_l3_caches=args.numL3caches,
        l1_request_latency=args.l1_request_latency,
        l1_response_latency=args.l1_response_latency,
        to_l2_latency=args.to_l2_latency,
        l2_request_latency=args.l2_request_latency,
        l2_response_latency=args.l2_response_latency,
        to_l1_latency=args.to_l1_latency,
    )
    
    # Create memory system
    memory = SingleChannelDDR3_1600(args.mem_size)
    
    # Create processor based on mode and type
    if args.full_system:
        # For full system mode with option to switch CPU types
        processor = SimpleSwitchableProcessor(
            starting_core_type=cpu_type,
            switch_core_type=CPUTypes.TIMING,
            num_cores=args.num_cores,
        )
    else:
        # For system emulation mode with a fixed CPU type
        processor = SimpleProcessor(
            cpu_type=cpu_type,
            num_cores=args.num_cores,
        )
    
    # Create the system board
    board = X86Board(
        clk_freq="3GHz",
        processor=processor,
        memory=memory,
        cache_hierarchy=cache_hierarchy,
    )
    
    # Set up the workload based on mode
    if args.full_system:
        # Full system setup with Linux
        command = "m5 exit;" \
                + "echo 'Running simulation with MSI cache hierarchy';" \
                + "sleep 1;" \
                + "m5 exit;"
        
        board.set_kernel_disk_workload(
            kernel=Resource("x86-linux-kernel-5.4.49"),
            disk_image=Resource("x86-ubuntu-18.04-img"),
            readfile_contents=command,
        )
        
        # Set up simulator with CPU switching on exit
        simulator = Simulator(
            board=board,
            on_exit_event={
                ExitEvent.EXIT: (processor.switch,),
            },
        )
    else:
        # System emulation mode with binary workload
        binary_path = args.binary
        workload = BinaryWorkload(binary_path)
        board.set_workload(workload)
        
        # Simple simulator without special exit handling
        simulator = Simulator(board=board)
    
    # Run the simulation
    print(f"Starting simulation with {args.num_cores} cores using {args.cpu_type} CPU type")
    if args.full_system:
        print("Running in Full System mode")
    else:
        print(f"Running in System Emulation mode with binary: {args.binary}")
    
    simulator.run()
    
    print("Simulation completed")

if __name__ == "__main__":
    main()