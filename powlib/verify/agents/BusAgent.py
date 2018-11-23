
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
    
    def __init__(self, wrInterface, rdInterface, baseAddr=None, passive=False):
        '''
        Constructor. wrInterface and rdInterface should be a HandshakeInterface 
        with the signals addr, data, be, and op. wrInterface should be assosicated
        with the writing SimHandles, whereas rdInterface should be associated with
        the reading SimHandles. baseAddr should be the base address of the interface, 
        however it's optional if there's no intent to read or the BusAgent is passive.
        '''
        
        drivers = Namespace(wr=HandshakeWriteDriver(interface=wrInterface),
                            rd=HandshakeReadDriver(interface=rdInterface)) if not passive else None
        monitors = Namespace(wr=HandshakeMonitor(interface=wrInterface),
                             rd=HandshakeMonitor(interface=rdInterface))
        
        Agent.__init__(self, drivers=drivers, monitors=monitors)
        
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
        Reads data from the bus interface. addr specifies where to read. If
        addr is an int, then only a single read will occur. If addr is a list,
        a burst of reads will occur.
        '''
        
        # Create the receiving port. Clear the event.
        rdInport = InPort(block=self)
        self._monitors.rd.outport.connect(rdInport)
        
        # Prepare the list of read transactions.
        if isinstance(addr, int):
            addrList = [addr]
        elif isinstance(addr, list):
            addrList = addr
        else: raise TypeError("addr must be either int or list.")
        
        # Write out the burst read.
        for each_addr in addrList:
            self.write(addr=each_addr, data=self.__baseAddr, op=OP_READ)
            
        # Read each word.
        transList = []
        for each_read in range(len(addrList)):
            self.__rdEvent.clear()
            yield self.__rdEvent.wait()
            assert(rdInport.ready())
            trans = rdInport.read()
            transList.append(trans)
            
        # Disconnect the port.
        self._monitors.rd.outport.disconnect(rdInport)
        
        # If only a single read occurs, then return on the single transaction.
        # If a burst, then return the list.
        if len(transList)==1:
            raise ReturnValue(transList[0])
        else:
            raise ReturnValue(transList)
        
                