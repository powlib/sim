
from cocotb.decorators       import coroutine
from cocotb.triggers         import ReadOnly, RisingEdge, Edge, NullTrigger

from powlib.verify.component import Driver, Monitor
from powlib                  import Interface

class RegisterInterface(Interface):
    '''
    The register interface consists
    of only two control signals, the clock
    and reset.
    '''
    _cntrl = Interface._cntrl + ['clk','rst']

    @coroutine
    def _wait_reset(self, active_mode=1):
        '''
        Wait until reset is in an inactive state.
        '''
        rst = self.rst        
        if str(rst.value)=='z' or str(rst.value)=='x' or int(rst.value)==active_mode:
            yield Edge(rst)    
        yield NullTrigger() 

    @coroutine
    def _synchronize(self):
        '''
        Wait until the conditions of control signals have 
        been met.
        '''
        yield ReadOnly()
        yield RisingEdge(self.clk)        

class RegisterDriver(Driver):
    '''
    Defines the register driver.
    '''    

    def __init__(self, interface, default_trans=None, reset_active_mode=1):
        '''
        Constructor. 
        
        interface should be a RegisterInterface, or a derivative thereof.
        
        default_trans should be either None, indicating no default transaction,
        or a Transaction whose member names are the data signals of the interface.
        The values assigned to the Transaction's members will be the first set
        of values assigned to the interface's data signals. These defaults will not
        be assigned again.
        
        reset_active_mode should be either 1 or 0, former indicating reset-active
        on high and the latter indicating reset-active on low.
        '''
        self.__reset_active_mode = reset_active_mode
        self.__default_trans     = default_trans
        Driver.__init__(self, self._cast_interface(interface))

    def _cast_interface(self, interface):
        '''
        Casts interface to a specific interface.
        '''
        return RegisterInterface(**vars(interface))

    @coroutine
    def _wait_reset(self):
        '''
        Wait until reset is in an inactive state.
        '''        
        yield RegisterInterface._synchronize(self._interface)
        yield self._interface._wait_reset(active_mode=self.__reset_active_mode)

    @coroutine
    def _synchronize(self):
        '''
        Wait until the conditions of control signals have 
        been met.
        '''
        yield self._interface._synchronize()

    @coroutine
    def _write_default(self):
        '''
        Writes out the specified default transaction. If no default
        transaction was specified with the constructor, simply
        set the unknown signals to zero.
        '''

        # Generate a transaction with all the data signals. Set the
        # default values.      
        default_dict = {}
        if self.__default_trans is not None:  
            default_dict = vars(self.__default_trans)        
        trans = self._interface.transaction(**default_dict)

        # If there are any data signals not assigned, assume their default
        # value should be zerp.
        for name, value in vars(trans).items():
            if value is None: setattr(trans, name, 0) 

        # Write the transaction to the interface.
        self._interface.write(trans)

        # Yielding on a null trigger is necessary since
        # every coroutine-decorate method needs to yield
        # on a trigger.
        yield NullTrigger()

    @coroutine
    def _write(self, data):
        '''
        Writes out the queued data transasction
        to the interface.
        '''
        self._interface.write(data)
        yield NullTrigger()        

    @coroutine
    def _drive(self):
        '''
        Implement how data is driven with the RegisterDriver.
        '''        
        yield self._write_default()
        yield self._wait_reset()
        while True:           
            while (self._ready()):
                yield self._write(self._read())
                yield self._synchronize()                
            yield self._event.wait()
            self._event.clear()
            yield RegisterInterface._synchronize(self._interface)

class RegisterMonitor(Monitor):
    '''
    Defines the register monitor.
    '''

    def __init__(self, interface, reset_active_mode=1):
        '''
        Constructor. 

        interface should be a RegisterInterface, or a derivative thereof.
        
        reset_active_mode should be either 1 or 0, former indicating reset-active
        on high and the latter indicating reset-active on low.        
        '''
        self.__reset_active_mode = reset_active_mode
        Monitor.__init__(self, self._cast_interface(interface))

    def _cast_interface(self, interface):
        '''
        Casts interface to a specific interface.
        '''
        return RegisterInterface(**vars(interface))        

    @coroutine
    def _wait_reset(self):
        '''
        Wait until reset is in an inactive state. Always wait the
        first clock cycle by default.
        '''          
        yield RegisterInterface._synchronize(self._interface)    
        yield self._interface._wait_reset(active_mode=self.__reset_active_mode)        
    
    @coroutine
    def _synchronize(self):
        '''
        Wait until the conditions of control signals have 
        been met.
        '''
        yield self._interface._synchronize()       

    @coroutine
    def _read(self):
        '''
        Samples from the interface and writes it out 
        on to the outport.
        '''        
        self.outport.write(self._interface.read(), execute_behavior=True)    
        yield NullTrigger()

    @coroutine
    def _monitor(self):
        '''
        Carry out the behavior of the monitor.
        '''        
        yield self._wait_reset()                
        while True:            
            yield self._synchronize()            
            yield self._read()

