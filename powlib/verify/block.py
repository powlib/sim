
from collections import deque

default_bqueue = deque()

def run(bqueue=default_bqueue):
    '''
    Executes the behaviors on the specified behavior queue.
    '''
    while len(bqueue)!=0:
        bqueue.popleft()()

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

    def __init__(self, block, bqueue=default_bqueue):
        '''
        Associates the port with a single block.
        '''
        
        # Store the block associated with the Port.
        if not isinstance(block, Block):
            raise TypeError("block should be an instance of Block.")
        self.__block = block
        
        # Store the behavior queue associated with the Port.
        if not hasattr(bqueue, "popleft") or not callable(bqueue.popleft):
            raise TypeError("bqueue must have the popleft method.")        
        if not hasattr(bqueue, "append") or not callable(bqueue.append):
            raise TypeError("bqueue must have the append method.")
        if not hasattr(bqueue, "__len__") or not callable(bqueue.__len__):
            raise TypeError("bqueue must have the __len__ method.")
        self.__bqueue = bqueue
    
    @property
    def _block(self):
        '''
        Safely returns the reference to the associated block.
        '''
        return self.__block
    
    @property
    def _bqueue(self):
        '''
        Safely returns the reference to the associated bqueue.
        '''
        return self.__bqueue

class InPort(Port):
    '''
    Represents an input to a block.
    '''

    def __init__(self, block, bqueue=default_bqueue):
        '''
        Constructor.
        '''
        Port.__init__(self, block, bqueue)
        self.__data = deque()        

    def write(self, data):
        '''
        Writes data into the inport and submits the block's behavior to the 
        behavior queue.        
        '''        
        self.__data.append(data)
        self._bqueue.append(self._block._behavior)
    
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

    def __init__(self, block, bqueue=default_bqueue):
        '''
        Constructor.
        '''
        Port.__init__(self, block, bqueue)
        self.__inports = []

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

    def write(self, data, execute_behavior=False):
        '''
        Writes data to all the inports connected to
        the this outport. If execute_behavior is set, the 
        '''
        # Write data to all InPorts associated with the OutPort.
        for idx, inp in enumerate(self.__inports):            
            inp.write(data)
            
        # Execute the behavior if required.
        if execute_behavior:
            run(bqueue=self._bqueue)
        


