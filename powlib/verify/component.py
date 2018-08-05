from cocotb              import fork
from cocotb.decorators   import coroutine
from cocotb.triggers     import Event
from powlib              import Interface, Transaction
from powlib.verify.block import Block, InPort, OutPort
from collections         import deque

class Component(Block):
    '''
    A component is a block that represents the connection
    between simulation and hardware.
    '''

    def __init__(self, interface):

        if not isinstance(interface, Interface):
            raise TypeError("interface should be an Interface.")
        self.__interface = interface

    @property
    def _interface(self):
        '''
        Safely return the reference to the interface
        associated with this driver.
        '''
        return self.__interface        

class Driver(Component):
    '''
    Block intended for driving transactions onto
    an interface.
    '''

    def __init__(self, interface):
        '''
        Constructs the driver with a given
        interface.
        '''
        Component.__init__(self, interface)        
        self.__inport    = InPort(block=self)
        self.__queue     = deque()
        self.__event     = Event()
        fork(self._drive())

    @property
    def inport(self):
        '''
        Safely return the inport associated with the driver.
        '''
        return self.__inport

    def write(self, data):
        '''
        Writes data into the driver's queue.
        '''
        self.__queue.append(data)        
        self._event.set()

    def behavior(self):
        '''
        Implements the behavior of the block.
        '''
        if self.inport.ready():
            data = self.inport.read()
            self.write(data)      

    @property
    def _event(self):
        '''
        Return the event object used to synchronize the _drive coroutine
        with the parent coroutine for new data.
        '''
        return self.__event        

    def _ready(self):
        '''
        Checks to see if data is available in the driver's queue.
        '''        
        return len(self.__queue)!=0

    def _read(self):
        '''
        Reads data from the driver's queue.
        '''      
        try: return self.__queue.popLeft()  
        except IndexError: return None          

    @coroutine
    def _drive(self):
        '''
        This coroutine should be implemented such that it writes out
        data to the specified interface with the data acquired from the
        driver's queue. The _ready and _read methods should be used for 
        acquiring the data, the _event property should be used for 
        synchronization, the _interface property should be used for
        acquiring the handles.
        '''
        raise NotImplemented("The drive coroutine should be implemented.")               
        
class Monitor(Component):
    '''
    '''

    def __init__(self, interface):
        '''
        '''
        Component.__init__(self, interface)        
        self.__outport    = OutPort(block=self)
        fork(self._monitor())   

    @property
    def outport(self):
        '''
        Safely return the outport associated with the monitor.
        '''
        return self.__outport

    @coroutine
    def _monitor(self):
        raise NotImplemented("The monitor coroutine should be implemented.")        






    
