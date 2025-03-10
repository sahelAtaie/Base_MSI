from m5.objects import System, SrcClockDomain, VoltageDomain
from m5.objects.ruby import RubySystem
from m5.objects.ruby.topologies import SimplePt2Pt
from .msi_caches import MyCacheSystem

# Create the NoC mesh with a fully connected topology
def create_noc_mesh(num_nodes):
    switches = [Switch(name=f"switch_{i}") for i in range(num_nodes)]
    links = []
    
    for i in range(num_nodes):
        for j in range(num_nodes):
            if i != j:  # Fully connected mesh
                links.append(SimplePt2Pt(
                    delay='1ns',
                    src=switches[i].port,
                    dest=switches[j].port
                ))
    
    return switches, links

# Configure the system with MESI-based controllers and NoC
class SystemWithMesiNuca(System):
    def __init__(self, cpus, mem_ctrls):
        super(SystemWithMesiNuca, self).__init__()
        self.clk_domain = SrcClockDomain(clock='1GHz', voltage_domain=VoltageDomain())
        
        # Create cache system with MESI-based controllers
        self.cache_system = MyCacheSystem()
        self.cache_system.setup(
            self,
            cpus,
            l1i_size='32kB',
            l1i_assoc='2',
            l1d_size='32kB',
            l1d_assoc='2',
            l2_size='256kB',
            l2_assoc='8',
            l3_size='2MB',
            l3_assoc='16',
            l1_request_latency=2,
            l1_response_latency=2,
            to_l2_latency=10,
            l2_request_latency=10,
            l2_response_latency=10,
            to_l1_latency=5,
            numL3caches=4,
            mem_ctrls=mem_ctrls
        )
        
        num_controllers = len(self.cache_system.controllers)
        
        # Create NoC mesh
        self.switches, self.links = create_noc_mesh(num_controllers)
        
        # Connect controllers to NoC switches
        for i, controller in enumerate(self.cache_system.controllers):
            controller.requestToNoc = self.switches[i].port
            controller.responseFromNoc = self.switches[i].port
        
        # Connect NoC to Ruby network
        self.cache_system.network.switches = self.switches
        self.cache_system.network.links = self.links
