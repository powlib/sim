from cocotb.decorators                  import coroutine
from cocotb.triggers                    import Edge, NullTrigger
from powlib.verify.agents.RegisterAgent import RegisterInterface, RegisterDriver, RegisterMonitor

class DiscreteInterface(RegisterInterface):
    '''
    The discrete interface doesn't have any control signals,
    since synchronization is done with any changes on the data signals themselves.
    '''
    
    _cntrl = []
    
    @coroutine
    def _synchronize(self):
        '''
        Instead of synchronzing on a control signal, wait until the data changes.
        '''
        yield [Edge(handle) for sig, handle in vars(self).items()]

class DiscreteDriver(RegisterDriver):
    '''
    Defines the discrete driver.
    '''
    
    def _cast_interface(self, interface):
        '''
        Casts interface to a specific interface.
        '''
        return DiscreteInterface(**vars(interface)) 
    
    @coroutine
    def _wait_reset(self):
        '''
        Do not wait on reset; immediately start writing out any new value.
        '''        
        yield NullTrigger()     
    
    @coroutine
    def _synchronize(self):
        '''
        Remove synchronization, since the intent is to always write out any new
        data.
        '''
        yield NullTrigger() 
        
class DiscreteMonitor(RegisterMonitor):
    '''
    Defines the discrete monitor.
    '''
    
    def _cast_interface(self, interface):
        '''
        Casts interface to a specific interface.
        '''
        return DiscreteInterface(**vars(interface))    
    
    @coroutine
    def _wait_reset(self):
        '''
        Instead of waiting on a reset, immediately read the initial value on
        the interface.
        '''        
        yield self._read()    
     