from m5.objects import *
from m5.params import *
from .BaseTopology import SimpleTopology

class SwitchedNUCA(SimpleTopology):
    description = "Switched NUCA LLC Network with Direct L1-L2 Connections"

    def __init__(self, ruby_system):
        self.ruby_system = ruby_system
        super(SwitchedNUCA, self).__init__()

    def makeTopology(self, options, controllers):
        # Extract controllers by type
        l2_controllers = [ctrl for ctrl in controllers if isinstance(ctrl, L2Cache)]
        l3_controllers = [ctrl for ctrl in controllers if isinstance(ctrl, L3Cache)]
        dir_controllers = [ctrl for ctrl in controllers if isinstance(ctrl, DirController)]

        # Create routers/switches for L3 NUCA network
        num_rows = options.nuca_rows
        num_columns = options.num_llc_banks // num_rows
        routers = [Router(router_id=i, latency=options.router_latency) 
                  for i in range(options.num_llc_banks)]
        
        # Create links
        links = []
        link_count = 0

        # Connect L3 banks to their switches
        for i, l3_ctrl in enumerate(l3_controllers):
            links.append(
                MessageBuffer(
                    ordered=True,
                    buffer_size=0,
                    source=l3_ctrl,
                    destination=routers[i],
                )
            )
            links.append(
                MessageBuffer(
                    ordered=True,
                    buffer_size=0,
                    source=routers[i],
                    destination=l3_ctrl,
                )
            )
            link_count += 2

        # Create horizontal (data bus) connections between L3 switches
        for row in range(num_rows):
            for col in range(num_columns - 1):
                router_id = col + (row * num_columns)
                next_router_id = (col + 1) + (row * num_columns)
                
                # Bidirectional links
                links.append(
                    MessageBuffer(
                        ordered=True,
                        buffer_size=0,
                        source=routers[router_id],
                        destination=routers[next_router_id],
                        width=options.data_bus_width
                    )
                )
                links.append(
                    MessageBuffer(
                        ordered=True,
                        buffer_size=0,
                        source=routers[next_router_id],
                        destination=routers[router_id],
                        width=options.data_bus_width
                    )
                )
                link_count += 2

        # Create vertical (address bus) connections between L3 switches
        for col in range(num_columns):
            for row in range(num_rows - 1):
                router_id = col + (row * num_columns)
                next_router_id = col + ((row + 1) * num_columns)
                
                # Bidirectional links
                links.append(
                    MessageBuffer(
                        ordered=True,
                        buffer_size=0,
                        source=routers[router_id],
                        destination=routers[next_router_id],
                        width=options.address_bus_width
                    )
                )
                links.append(
                    MessageBuffer(
                        ordered=True,
                        buffer_size=0,
                        source=routers[next_router_id],
                        destination=routers[router_id],
                        width=options.address_bus_width
                    )
                )
                link_count += 2

        # Connect L2 controllers to L3 network
        for l2_ctrl in l2_controllers:
            # Find nearest router for this L2 cache
            router_id = self._find_nearest_router(l2_ctrl, routers)
            
            # Connect L2 to L3 router
            links.append(
                MessageBuffer(
                    ordered=True,
                    buffer_size=0,
                    source=l2_ctrl,
                    destination=routers[router_id],
                )
            )
            links.append(
                MessageBuffer(
                    ordered=True,
                    buffer_size=0,
                    source=routers[router_id],
                    destination=l2_ctrl,
                )
            )
            link_count += 2

        # Connect directory controllers
        for dir_ctrl in dir_controllers:
            # Connect to all routers for memory access
            for router in routers:
                links.append(
                    MessageBuffer(
                        ordered=True,
                        buffer_size=0,
                        source=dir_ctrl,
                        destination=router,
                    )
                )
                links.append(
                    MessageBuffer(
                        ordered=True,
                        buffer_size=0,
                        source=router,
                        destination=dir_ctrl,
                    )
                )
                link_count += 2

        # Set network components
        self.ruby_system.network.routers = routers
        self.ruby_system.network.netlinks = links

    def _find_nearest_router(self, controller, routers):
        # Distribute L2s evenly among L3 routers
        return hash(str(controller)) % len(routers)