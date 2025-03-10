from m5.objects import SimpleNetwork, SimpleIntLink, SimpleExtLink, Switch
from m5.params import *
from m5.proxy import *
import math

class NucaNetwork(SimpleNetwork):
    """A NUCA (Non-Uniform Cache Access) network implementing a grid topology
    for a Ruby cache system with L1, L2, L3, and Directory controllers."""
    
    type = 'NucaNetwork'
    cxx_header = "mem/ruby/network/simple/SimpleNetwork.hh"
    
    # Define parameters
    # rows = Param.Int(4, "Number of rows in the grid")
    # cols = Param.Int(4, "Number of columns in the grid")
    bandwidth_factor = Param.Int(16, "Bandwidth scaling factor")
    
    def __init__(self, ruby_system):
        super().__init__()
        self.netifs = []
        self.ruby_system = ruby_system
        
    def connectControllers(self, cols, rows, controllers):
        """Connect all controllers in the Ruby system to the network.
        
        Args:
            controllers: List of all controllers [L1s + L2s + L3s + Directories]
        """
        num_cpus = len([c for c in controllers if isinstance(c, self.ruby_system.controllers[0].__class__)])
        num_l3s = len([c for c in controllers if isinstance(c, self.ruby_system.controllers[2*num_cpus].__class__)])
        
        # Calculate grid dimensions based on L3 caches
        rows = int(math.sqrt(num_l3s))
        cols = (num_l3s + int(rows) - 1) // int(rows)  # Ceiling division

        # Create grid of routers/switches
        self.routers = []
        for i in range(rows):
            router_row = []
            for j in range(cols):
                router = Switch(
                    router_id=i*cols + j,
                    # clock="3GHz",
                    network=self
                )
                router_row.append(router)
            self.routers.append(router_row)
        
        # Connect all controllers to their nearest router
        self.ext_links = []
        link_id = 0
        
        # Connect L3 caches to routers in grid pattern
        l3_start = 2 * num_cpus  # Index where L3 controllers start
        for i in range(min(num_l3s, rows * cols)):
            row = i // int(cols)
            col = i % int(cols)
            self.ext_links.append(
                SimpleExtLink(
                    link_id=link_id,
                    ext_node=controllers[l3_start + i],
                    int_node=self.routers[row][col],
                    latency=1,
                    bandwidth_factor=self.bandwidth_factor
                )
            )
            link_id += 1
        
        # Connect L1 and L2 caches to nearest L3 router
        for i in range(num_cpus):
            # Connect L1
            row = (i // int(cols)) % int(rows)
            col = i % int(cols)
            self.ext_links.append(
                SimpleExtLink(
                    link_id=link_id,
                    ext_node=controllers[i],  # L1 controller
                    int_node=self.routers[row][col],
                    latency=1,
                    bandwidth_factor=self.bandwidth_factor
                )
            )
            link_id += 1
            
            # Connect corresponding L2
            self.ext_links.append(
                SimpleExtLink(
                    link_id=link_id,
                    ext_node=controllers[num_cpus + i],  # L2 controller
                    int_node=self.routers[row][col],
                    latency=1,
                    bandwidth_factor=self.bandwidth_factor
                )
            )
            link_id += 1
        
        # Connect directory controllers to edge routers
        dir_start = l3_start + num_l3s
        for i, ctrl in enumerate(controllers[dir_start:]):
            row = i % int(rows)
            col = cols - 1  # Connect to rightmost routers
            self.ext_links.append(
                SimpleExtLink(
                    link_id=link_id,
                    ext_node=ctrl,
                    int_node=self.routers[row][col],
                    latency=1,
                    bandwidth_factor=self.bandwidth_factor
                )
            )
            link_id += 1
        
        # Create internal links between routers (bidirectional)
        self.int_links = []
        link_id = 0
        
        # Horizontal connections
        for i in range(rows):
            for j in range(cols - 1):
                self.int_links.append(
                    SimpleIntLink(
                        link_id=link_id,
                        src_node=self.routers[i][j],
                        dst_node=self.routers[i][j + 1],
                        latency=1,
                        bandwidth_factor=self.bandwidth_factor
                    )
                )
                link_id += 1
                self.int_links.append(
                    SimpleIntLink(
                        link_id=link_id,
                        src_node=self.routers[i][j + 1],
                        dst_node=self.routers[i][j],
                        latency=1,
                        bandwidth_factor=self.bandwidth_factor
                    )
                )
                link_id += 1
        
        # Vertical connections
        for i in range(rows - 1):
            for j in range(cols):
                self.int_links.append(
                    SimpleIntLink(
                        link_id=link_id,
                        src_node=self.routers[i][j],
                        dst_node=self.routers[i + 1][j],
                        latency=1,
                        bandwidth_factor=self.bandwidth_factor
                    )
                )
                link_id += 1
                self.int_links.append(
                    SimpleIntLink(
                        link_id=link_id,
                        src_node=self.routers[i + 1][j],
                        dst_node=self.routers[i][j],
                        latency=1,
                        bandwidth_factor=self.bandwidth_factor
                    )
                )
                link_id += 1