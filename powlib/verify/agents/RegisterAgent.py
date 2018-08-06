from cocotb.triggers         import ReadOnly, RisingEdge, Edge, NullTrigger

from powlib.verify.component import Driver
from powlib                  import Interface

class RegisterInterface(Interface):
    '''
    The register interface consists
    of only two control signals, the clock
    and reset.
    '''
    _cntrl.extend(['clk','rst'])

class RegisterDriver(Driver):
    '''
    Defines the register driver.
    '''    

    def __init__(self, interface, default_trans=None, reset_active_mode=1):
        '''
        Constructor. 
        '''
        self.__reset_active_mode = reset_active_mode
        self.__default_trans     = default_trans
        Driver.__init__(self, RegisterInterface(**vars(interface)))

    @coroutine
    def _wait_reset(self):
        '''
        Wait until reset is in an inactive state.
        '''
        rst = self._interface.rst        
        if str(rst.value)=='z' or str(rst.value)=='x' or int(rst.value)==self.__reset_active_mode:
            yield Edge(rst)    
        yield NullTrigger()        

    @coroutine
    def _synchronize(self):
        '''
        Wait until the conditions of control signals have 
        been met.
        '''
        yield ReadOnly()
        yield RisingEdge(self._interface.clk)

    @coroutine
    def _write_default(self):
        '''
        '''
        # Generate a transaction with all the data signals. Set the
        # default values.
        trans = self._interface.transaction(**vars(self.__default_trans))

        # If there are any data signals not assigned, assume their default
        # value should be zerp.
        for name, value in vars(trans).items():
            if value is None: trans[name] = 0

        # Write the transaction to the interface.
        self._interface.write(trans)

        # Yielding on a null trigger is necessary since
        # every coroutine-decorate method needs to yield
        # on a trigger.
        yield NullTrigger()

    @coroutine
    def _drive(self):
        '''
        '''
        
        yield self._write_default()

        yield self._wait_reset()

        while True:

            yield self._event.wait()
            self._event.clear()          

            yield self._synchronize()
            
            self._interface.write(self._read())

            while(self._ready()):

                yield self._synchronize()
                
                self._interface.write(self._read())

                
                