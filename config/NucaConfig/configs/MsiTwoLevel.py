# import the m5 (gem5) library created when gem5 is built
import m5
import os

# import all of the SimObjects
from m5.objects import *

# Needed for running C++ threads
m5.util.addToPath("../../")
from configs.common.FileSystemConfig import config_filesystem
from src.python.gem5.resources.resource import obtain_resource
from config.msi_caches import MyCacheSystem
# from config.mesiCaches import MyCacheSystem

from optparse import OptionParser

parser = OptionParser()
parser.add_option("--cpu_type", type="string", default="X86O3CPU", help="Type of CPU (e.g., 'X86TimingSimpleCPU', 'X86O3CPU', etc.)")
parser.add_option("--l1i_size", type="string", default="32kB", help="L1 instruction cache size")
parser.add_option("--l1i_assoc", type="int", default=2, help="L1 instruction cache associativity")
parser.add_option("--l1d_size", type="string", default="32kB", help="L1 data cache size")
parser.add_option("--l1d_assoc", type="int", default=2, help="L1 data cache associativity")
parser.add_option("--l2_size", type="string", default="256kB", help="L2 cache size")
parser.add_option("--l2_assoc", type="int", default=8, help="L2 cache associativity")
# each L3 bank have this size so if all LLC in base code is 8MB for me each l3_size should be 8MB/(2*numL3caches)
parser.add_option("--l3_size", type="string", default="256kB", help="L3 cache size")
parser.add_option("--l3_assoc", type="int", default=8, help="L3 cache associativity")
parser.add_option("--numL3caches", type="int", default=64, help="Number of L3 caches")
parser.add_option("--l1_request_latency", type="int", default=4, help="L1 request latency in cycles")
parser.add_option("--l1_response_latency", type="int", default=4, help="L1 response latency in cycles")
parser.add_option("--to_l2_latency", type="int", default=2, help="Latency to L2 private cache in cycles")
parser.add_option("--l2_request_latency", type="int", default=4, help="L2 private request latency in cycles")
parser.add_option("--l2_response_latency", type="int", default=4, help="L2 private response latency in cycles")
parser.add_option("--to_l1_latency", type="int", default=2, help="Latency back to L1 cache in cycles")

(options, args) = parser.parse_args()

# create the system we are going to simulate
system = System()

# Set the clock frequency of the system (and all of its children)
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "3GHz"
system.clk_domain.voltage_domain = VoltageDomain()

# Set up the system
system.mem_mode = "timing"  # Use timing accesses
system.mem_ranges = [AddrRange("4GiB")]  # Create an address range

# Create a pair of simple CPUs
# Create CPUs based on cpu_type option
if options.cpu_type == "TimingSimpleCPU":
    system.cpu = [TimingSimpleCPU() for _ in range(4)]
elif options.cpu_type == "X86TimingSimpleCPU":
    system.cpu = [X86TimingSimpleCPU() for _ in range(4)]
elif options.cpu_type == "X86O3CPU":
    system.cpu = [X86O3CPU() for _ in range(4)]
    for cpu in system.cpu:
        # Pipeline configuration
        cpu.fetchWidth = 4
        cpu.decodeWidth = 4
        cpu.renameWidth = 4
        cpu.dispatchWidth = 4
        cpu.issueWidth = 4
        cpu.commitWidth = 4

        # Reorder Buffer
        cpu.numROBEntries = 192

        # Load/Store Queue
        cpu.LQEntries = 32
        cpu.SQEntries = 32

        # Issue Queue sizes
        cpu.numIQEntries = 64

        # Physical Register File
        cpu.numPhysIntRegs = 256
        cpu.numPhysFloatRegs = 256

        # Branch Predictor (Tournament)
        cpu.branchPred = TournamentBP()
else:
    raise ValueError(f"Unsupported CPU type: {options.cpu_type}")
# system.cpu = [X86TimingSimpleCPU() for i in range(2)]
# system.cpu = [X86TimingSimpleCPU()]

# Create a DDR3 memory controller and connect it to the membus
system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR3_1600_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]

# create the interrupt controller for the CPU and connect to the membus
for cpu in system.cpu:
    cpu.createInterruptController()

# Create the Ruby System
system.caches = MyCacheSystem()
system.caches.setup(
    system, 
    system.cpu, 
    options.l1i_size,
    options.l1i_assoc,
    options.l1d_size,
    options.l1d_assoc,
    options.l2_size,
    options.l2_assoc,
    options.l3_size,
    options.l3_assoc,
    options.l1_request_latency,
    options.l1_response_latency,
    options.to_l2_latency,
    options.l2_request_latency,
    options.l2_response_latency,
    options.to_l1_latency,
    options.numL3caches,
    [system.mem_ctrl],
)

# Run application and use the compiled ISA to find the binary
# grab the specific path to the binary
thispath = os.path.dirname(os.path.realpath(__file__))
binary = "/home/sahel/NPB3.3.1/NPB3.3-SER/bin/cg.W.x"

process = Process()
process.cmd = [binary]  # Use the binary path in the command
for cpu in system.cpu:
    cpu.workload = process
    cpu.createThreads()

# Initialize SEWorkload with the binary file path
system.workload = SEWorkload.init_compatible(binary)

# Set up the pseudo file system for the threads function above
config_filesystem(system)

# set up the root SimObject and start the simulation
root = Root(full_system=False, system=system)
# instantiate all of the objects we've created above
# import pdb
# pdb.set_trace()
m5.instantiate()

print("Beginning simulation!")
exit_event = m5.simulate()
print(f"Exiting @ tick {m5.curTick()} because {exit_event.getCause()}")