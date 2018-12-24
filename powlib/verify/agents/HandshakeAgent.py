from cocotb.decorators                  import coroutine
from cocotb.triggers                    import RisingEdge, NullTrigger
from powlib.verify.agents.RegisterAgent import RegisterInterface, RegisterDriver, RegisterMonitor
from random                             import randint
from types                              import GeneratorType

CoinTossAllow = (randint(0, 1)==True for _ in iter(int, 1))
AlwaysAllow   = (True                for _ in iter(int, 1)) 
NeverAllow    = (False               for _ in iter(int, 1)) 

class AllowFeature(object):
    '''
    This feature is intended to simulate congestion.
    '''

    @property
    def allow(self):
        '''
        Safely returns the allow generator.
        '''
        return self.__allow

    @allow.setter
    def allow(self, value):
        '''
        Sets the allow generator. This generator can be used
        to control data flow of this driver.
        '''
        if not isinstance(value, GeneratorType):
            raise TypeError("Allow must be a generator that returns either True or False.")
        self.__allow = value     

class HandshakeInterface(RegisterInterface):
    '''
    The handshake interface extends the register interface
    with a valid and ready control signals. Valid indicates
    data is available to be read, whereas ready indicates
    something is ready to receive the data. The transaction
    occurs when both valid and ready are asserted.
    '''

    _cntrl = RegisterInterface._cntrl + ['vld','rdy']

    @coroutine
    def _synchronize(self):
        '''
        Yield to the simulator (or to other coroutines)
        until both handshaking signals are high.
        '''
        yield RegisterInterface._synchronize(self)
        while int(self.vld.value)==0 or int(self.rdy.value)==0:
            if int(self.vld.value)==0:
                yield RisingEdge(self.vld)
                yield RegisterInterface._synchronize(self)
            if int(self.rdy.value)==0:
                yield RisingEdge(self.rdy)
                yield RegisterInterface._synchronize(self)       

class HandshakeWriteDriver(RegisterDriver, AllowFeature):
    '''
    Carries out the writing side of the handshaking
    protocol.
    '''

    def __init__(self, allow=AlwaysAllow, *args, **kwargs):
        '''
        This constructor extends the register driver's
        constructor to permit the selection of an 
        allow generator.
        '''
        RegisterDriver.__init__(self, *args, **kwargs)
        self.allow = allow

    def _cast_interface(self, interface):
        '''
        Casts interface to a specific interface.
        '''
        return HandshakeInterface(**vars(interface))    

    @coroutine
    def _write_default(self):
        '''
        Writes out the default state of the handshake interface.
        '''
        self._interface.vld.value = 0
        yield RegisterDriver._write_default(self)

    @coroutine
    def _synchronize(self):
        '''
        Wait until the conditions of control signals have 
        been met.
        '''
        yield self._interface._synchronize()
        if self._ready()==False: 
            self._interface.vld.value = 0   

    @coroutine
    def _write(self, data):
        '''
        Writes out the queued data transasction
        to the interface.
        '''

        # Write out the data.
        self._interface.write(data)

        # Check the allow to determine if the driver is
        # allowed to set its valid.
        while next(self.allow)==False:
            self._interface.vld.value = 0
            yield RegisterInterface._synchronize(self._interface)

        # Once it's finally allowed to write data, set
        # the valid and continue.
        self._interface.vld.value = 1
        yield NullTrigger()           

class HandshakeReadDriver(RegisterDriver, AllowFeature): 
    '''
    Carries out the reading side of the handshaking
    protocol.
    '''

    def __init__(self, allow=AlwaysAllow, *args, **kwargs):
        '''
        This constructor extends the register driver's
        constructor to permit the selection of an 
        allow generator.
        '''
        RegisterDriver.__init__(self, *args, **kwargs)
        self.allow = allow 

    def _cast_interface(self, interface):
        '''
        Casts interface to a specific interface.
        '''
        return HandshakeInterface(**vars(interface))       

    @coroutine
    def _write_default(self):
        '''
        Writes out the default state of the handshake interface. Do not
        write over the data signals since we're reading from them.
        '''
        self._interface.rdy.value = 0 
        yield NullTrigger()            

    @coroutine
    def _write(self):
        '''
        Writes out the queued data transasction
        to the interface.
        '''

        # Check the allow to determine if the driver is
        # allowed to set its ready.
        while next(self.allow)==False:
            self._interface.rdy.value = 0
            yield RegisterInterface._synchronize(self._interface)

        # Once it's finally allowed to read, set
        # the ready and continue.
        self._interface.rdy.value = 1
        yield NullTrigger()    

    @coroutine
    def _drive(self):
        '''
        Implement how data is driven with the RegisterDriver.
        '''        
        yield self._write_default()
        yield self._wait_reset()
        while True:           
            yield self._write()
            yield self._synchronize()            

    @property
    def inport(self):
        '''
        Do not used this method with read port.
        '''
        raise NotImplementedError("inport should not be used with the read driver.")

    def write(self, data):
        '''
        Do not used this method with read port.
        '''
        raise NotImplementedError("write should not be used with the read driver.")

    @coroutine
    def flush(self):
        '''
        Do not used this method with read port.
        '''
        raise NotImplementedError("flush should not be used with the read driver.")
        yield NullTrigger()          

class HandshakeMonitor(RegisterMonitor):
    '''
    Used to monitor the data transmitted across a handshake
    interface.
    '''

    def _cast_interface(self, interface):
        '''
        Casts interface to a specific interface.
        '''
        return HandshakeInterface(**vars(interface))   

