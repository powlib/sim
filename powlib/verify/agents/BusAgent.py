
from cocotb.decorators                   import coroutine
from cocotb.triggers                     import Event
from cocotb.result                       import ReturnValue

from powlib.verify.agents.HandshakeAgent import HandshakeWriteDriver, \
                                                HandshakeReadDriver, \
                                                HandshakeMonitor
from powlib.verify.block                 import InPort
from powlib.verify.agent                 import Agent
from powlib                              import Namespace, Transaction 
    

OP_WRITE = 0
OP_READ  = 1

class BusAgent(Agent):
    '''
    This component implements the powlib bus protocol, an interface through 
    both simulation and hardware components can access a powlib interconnect. Please
    note that bus in this context is used to refer to the interface protocol.
    '''
    
    def __init__(self, wrInterface, rdInterface, baseAddr):
        '''
        Constructor.
        '''
        
        Agent.__init__(self, drivers=Namespace(wr=HandshakeWriteDriver(interface=wrInterface),
                                               rd=HandshakeReadDriver(interface=rdInterface)),
                             monitors=Namespace(wr=HandshakeMonitor(interface=wrInterface),
                                                rd=HandshakeMonitor(interface=rdInterface)))
        
        self.__rdEvent     = Event()
        self.__baseAddr    = baseAddr

    inport       = property(lambda self : self._drivers.wr.inport)
    outport      = property(lambda self : self._monitors.rd.outport)
        
    def _behavior(self):
        '''
        The behavior is only needed by the read coroutine, to indicate when the
        data has been read.
        '''
        self.__rdEvent.set()

    def write(self, addr, data, be=None, op=OP_WRITE):
        '''
        Writes data over the bus interface. addr refers to the destination
        address. data is the specified data. be is the byte enable mask. op
        is the operation, which, by default is write.
        '''
        if be is None:
            beWidth = len(self._drivers.wr._interface.be)
            be      = int(((1<<beWidth)-1))
        self._drivers.wr.write(data=Transaction(addr=addr,data=data,be=be,op=op))
        
    @coroutine
    def read(self, addr):
        '''
        Reads data from the bus interface. 
        '''
        rdInport = InPort(block=self)
        self._monitors.rd.outport.connect(rdInport)
        self.__rdEvent.clear()
        self.write(addr=addr, data=self.__baseAddr, op=OP_READ)
        yield self.__rdEvent.wait()
        assert(rdInport.ready())
        trans = rdInport.read()
        self._monitors.rd.outport.disconnect(rdInport)
        raise ReturnValue(trans)
        
                