
from powlib.verify.block     import Block
from powlib.verify.component import Driver, Monitor
from powlib                  import Namespace

class Agent(Block):
    '''
    In general agent in the context of the powlib simulation
    libraries refer to a group of associated drivers and monitors. 
    This association can be loose, such as the HandshakeAgent. 
    Alternatively, this association can be strict, agents that derive
    from this agent base class. Interfaces such as AXI and powlib bus 
    can derive from this class since they're composed of drivers and/or
    monitors.
    '''
    
    def __init__(self, drivers, monitors=None):
        '''
        Constructor. drivers should be a Namespace of Drivers, whereas 
        the optional monitors should be a Namespace of Monitors.
        '''
        
        if not isinstance(drivers, Namespace):
            raise TypeError("drivers must be a Namespace.")
            
        for key, item in vars(drivers):
            if not isinstance(item, Driver):
                raise TypeError("drivers must be a Namespace of Drivers.")
            
        if monitors is not None:
            if not isinstance(monitors, Namespace):
                raise TypeError("monitors must be a Namespace.")
            for key, item in vars(monitors):
                if not isinstance(item, Monitor):
                    raise TypeError("monitors must be a Namespace of Monitors.")  
                    
        self.__drivers  = drivers
        self.__monitors = monitors
        
    _drivers  = property(lambda self : self.__drivers)
    _monitors = property(lambda self : self.__monitors)