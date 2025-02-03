import argparse
from src.python.gem5.utils.requires import requires
from src.python.gem5.components.boards.simple_board import SimpleBoard
from src.python.gem5.components.memory.single_channel import SingleChannelDDR3_1600
from src.python.gem5.components.cachehierarchies.ruby.mesi_three_level_cache_hierarchy import MESIThreeLevelCacheHierarchy
from src.python.gem5.components.processors.simple_processor import SimpleProcessor
from src.python.gem5.coherence_protocol import CoherenceProtocol
from src.python.gem5.isas import ISA
from src.python.gem5.components.processors.cpu_types import CPUTypes
from src.python.gem5.resources.resource import obtain_resource
from src.python.gem5.simulate.simulator import Simulator
from src.python.gem5.simulate.exit_event import ExitEvent


# Parse command-line arguments
# parser = argparse.ArgumentParser(description="Run gem5 simulation with workload.")
# parser.add_argument(
#     "workload",
#     type=str,
#     help="Path to the binary workload file"
# )
# args = parser.parse_args()

# Check to ensure the gem5 binary is compiled to X86 and supports the MESI Three Level coherence protocol.
requires(
    isa_required=ISA.X86,
    coherence_protocol_required=CoherenceProtocol.MESI_THREE_LEVEL,
    # kvm_required=True,
)

# Set up the MESI Three Level Cache Hierarchy.
cache_hierarchy = MESIThreeLevelCacheHierarchy(
    l1i_size="32KiB",
    l1i_assoc=8,
    l1d_size="32KiB",
    l1d_assoc=8,
    l2_size="2MB",
    l2_assoc=16,
    l3_size="16MB",
    l3_assoc=32,
    num_l3_banks=8,
)

# Set up the system memory.
memory = SingleChannelDDR3_1600("2GiB")

# Set up the processor.
processor = SimpleProcessor(cpu_type=CPUTypes.TIMING, num_cores=2, isa=ISA.X86)

# Set up the board.
board = SimpleBoard(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

# print(args.workload)
# Set the workload using the path from command-line argument
# binary = obtain_resource(args.workload)
binary = obtain_resource(resource_id="x86-npb-is-size-s")
board.set_se_binary_workload(binary)

# Create and run the simulator
simulator = Simulator(board=board)
simulator.run()
