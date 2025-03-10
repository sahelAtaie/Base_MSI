from m5.objects import *

class MyNetwork(SimpleNetwork):
    """A crossbar network."""

    def __init__(self, ruby_system):
        super().__init__()
        self.netifs = []
        self.ruby_system = ruby_system

    def connectControllers(self, controllers):
        # Create a single central switch/router
        self.central_router = Switch(router_id=0)

        # Add the central router to the list of routers
        self.routers = [self.central_router]

        # Create links from each controller to the central router
        self.ext_links = [
            SimpleExtLink(link_id=i, ext_node=c, int_node=self.central_router)
            for i, c in enumerate(controllers)
        ]

        # No internal links are needed for a crossbar topology
        self.int_links = []
