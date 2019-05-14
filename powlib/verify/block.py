
from asyncio     import run, Queue, gather, QueueEmpty

_coroutines = []

async def main():
    '''
    Defines the main async function that initiates all
    the coroutines.
    '''    
    if len(_coroutines)!=0:
        while any(await gather(*(coroutine() for coroutine in _coroutines))):
            pass

class Block(object):
    '''
    The basic build "block". The intention is to provide
    system with which simulations can be functionally divided
    and organized.
    '''
    
    def __init__(self):
        '''
        Constructor. Only purpose is to add the coroutine to the 
        coroutine list.
        '''
        self.__ports = []
        _coroutines.append(self._coroutine)        
        
    def _add_port(self, port):
        '''
        Associates port with block.
        '''
        if not (isinstance(port, InPort) or isinstance(port, OutPort)):
            raise TypeError("port must be either an InPort or OutPort.")
        self.__ports.append(port)
    
    async def _coroutine(self):
        '''
        Defines the coroutine. The behavior of a coroutine only occurs when
        an InPort is ready with data.
        '''
        if any(isinstance(port, InPort) and port.ready() for port in self.__ports):
            await self._behavior()
            return any(isinstance(port, OutPort) and port._check() for port in self.__ports)
        return False

    async def _behavior(self):
        '''
        The behavior of a block is used to 
        implement the operations a block must execute
        upon the reception of new data via an inport.
        '''
        raise NotImplementedError("The behavior of the block must be implemented.")

class Port(object):
    '''
    Represents the connections between blocks.
    '''

    def __init__(self, block):
        '''
        Associates the port with a single block.
        '''
        if not isinstance(block, Block):
            raise TypeError("block should be an instance of Block.")
        block._add_port(port=self)
        self.__block = block
    
    @property
    def _block(self):
        '''
        Safely returns the reference to the associated block.
        '''
        return self.__block

class InPort(Port):
    '''
    Represents an input to a block.
    '''

    def __init__(self, block):
        '''
        Constructor.
        '''
        Port.__init__(self, block)
        self.__data = None
        
    async def _setup(self):
        '''
        '''
        self.__data = Queue(maxsize=1)
        
    async def write(self, data):
        '''
        Writes data into the inport and 
        initiates the behavior of the block associated
        with the inport.
        '''        
        await self.__data.put(data)
    
    def ready(self):
        '''
        Returns whether or not new data has been written to
        the inport.
        '''
        return not self.__data.empty()

    def read(self):
        '''
        Returns data written to the inport. If no data exists, None is
        returned.
        '''  
        try: return self.__data.get_nowait()  
        except QueueEmpty: return None

class OutPort(Port):
    '''
    Represents a output port from a block.
    '''

    def __init__(self, block):
        '''
        Constructor.
        '''
        Port.__init__(self, block)
        self.__inports = []
        self.__written = False
        
    def _check(self):
        '''
        '''
        retvalue = self.__written
        self.__written = False
        return retvalue

    def connect(self, inport):
        '''
        Connects the specified inport to the
        output. This method also returns the
        block associated with inport.
        '''
        if not isinstance(inport, InPort):
            raise TypeError("inport should be an instance of InPort.")
        self.__inports.append(inport)    
        return inport._block

    def disconnect(self, inport):
        '''
        Searches for the specified inport, and disconnects it 
        from the outport if found. Returns the block associated
        with the inport.
        '''
        
        # Look for the first instance of the inport.
        ridx = None
        for idx, inp in enumerate(self.__inports):
            if inp is inport:
                ridx = idx
                break

        # Remove the inport if it was found.                
        if ridx is not None:
            del self.__inports[idx]                            

        return inport._block            

    async def write(self, data):
        '''
        Writes data to all the inports connected to
        the this outport.
        '''
        self.__written = True
        for idx, inp in enumerate(self.__inports):            
            await inp.write(data)
        


