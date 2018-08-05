from cocotb              import fork
from cocotb.decorators   import coroutine
from cocotb.triggers     import Event
from powlib              import Interface, Transaction
from powlib.verify.block import Block, InPort
from collections         import deque

class Driver(Block):

    def __init__(self, interface):
        '''
        Constructs the driver with a given
        interface.
        '''

        if not isinstance(interface, Interface):
            raise TypeError("interface should be an Interface.")
        self.__interface = interface
        self.__inport    = InPort(block=self)
        self.__queue     = deque()
        self.__event     = Event()

    @property
    def interface(self):
        '''
        Safely return the reference to the interface
        associated with this driver.
        '''
        return self.__interface

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
        self.__event.set()

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

    def behavior(self):
        '''
        Implements the behavior of the block.
        '''
        if self.inport.ready():
            data = self.inport.read()
            self.write(data)   

    def                
        





    
