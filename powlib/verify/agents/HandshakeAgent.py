from powlib.verify.agents.RegisterAgent import RegisterInterface, RegisterDriver

class HandshakeInterface(RegisterInterface):
    '''
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

class HandshakeDriver(RegisterDriver):

    def _cast_interface(self, interface):
        '''
        Casts interface to a specific interface.
        '''
        return HandshakeInterface(**vars(interface))    

    @coroutine
    def _synchronize(self):
        '''
        Wait until the conditions of control signals have 
        been met.
        '''
        yield self._interface._synchronize()        