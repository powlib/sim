from cocotb.binary                       import BinaryValue
from cocotb.decorators                   import coroutine
from cocotb.triggers                     import Event
from cocotb.result                       import ReturnValue

from powlib.verify.agents.HandshakeAgent import HandshakeWriteDriver, \
                                                HandshakeReadDriver, \
                                                HandshakeMonitor
from powlib.verify.block                 import InPort
from powlib.verify.component             import Component
from powlib                              import Interface, Namespace, Transaction 
    

OP_WRITE = 0
OP_READ  = 1

class Bus(Component):
    '''
    This component implements the powlib bus protocol, an interface through 
    both simulation and hardware components can access a powlib interconnect. Please
    note that bus in this context is used to refer to the interface protocol.
    '''
    
    def __init__(self, wrInterface, rdInterface, baseAddr):
        '''
        Constructor.
        '''
        
        if not (isinstance(wrInterface, Interface) and isinstance(rdInterface, Interface)):
            raise TypeError("interfaces should be an Interface.")
        
        self.__interface   = Namespace(wr=wrInterface,rd=rdInterface)
        self.__driver      = Namespace(wr=HandshakeWriteDriver(interface=wrInterface),
                                       rd=HandshakeReadDriver(interface=rdInterface))
        self.__monitor     = Namespace(wr=HandshakeMonitor(interface=wrInterface),
                                       rd=HandshakeMonitor(interface=rdInterface))
        
        self.__rdEvent     = Event
        self.__baseAddr    = baseAddr

        
    _driver      = property(lambda self : self.__driver)
    _monitor     = property(lambda self : self.__monitor)
    inport       = property(lambda self : self._driver.wr.inport)
    outport      = property(lambda self : self._monitor.rd.outport)
        
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
            beWidth = len(self._interface.wr.be)
            be      = BinaryValue(value=((1<<beWidth)-1), bits=beWidth)
        self._driver.wr.write(data=Transaction(addr=addr,data=data,be=be,op=op))
        
    @coroutine
    def read(self, addr):
        '''
        Reads data from the bus interface. 
        '''
        rdInport = InPort(block=self)
        self._monitor.rd.outport.connect(rdInport)
        self.__rdEvent.clear()
        self.write(addr=addr, data=self.__baseAddr, op=OP_READ)
        yield self.__rdEvent.wait()
        assert(rdInport.ready())
        trans = rdInport.read()
        self._monitor.rd.outport.disconnect(rdInport)
        raise ReturnValue(trans)
        
                