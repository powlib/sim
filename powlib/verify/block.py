
from collections import deque

class Block(object):
    '''
    The basic build "block". The intention is to provide
    system with which simulations can be functionally divided
    and organized.
    '''

    def _behavior(self):
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
        self.__data = deque()

    def write(self, data):
        '''
        Writes data into the inport and 
        initiates the behavior of the block associated
        with the inport.
        '''        
        self.__data.append(data)
        self._block._behavior()
    
    def ready(self):
        '''
        Returns whether or not new data has been written to
        the inport.
        '''
        return len(self.__data)!=0

    def read(self):
        '''
        Returns data written to the inport. If no data exists, None is
        returned.
        '''  
        try: return self.__data.popleft()  
        except IndexError: return None

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

    def connect(self, inport):
        '''
        Connects the specified inport to the
        output. This method also returns the
        block associated with inport.
        '''
        if not isinstance(inport, InPort):
            raise TypeError("inport should be an instance of InpPort.")
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

    def write(self, data):
        '''
        Writes data to all the inports connected to
        the this outport.
        '''
        for idx, inp in enumerate(self.__inports):            
            inp.write(data)
        


