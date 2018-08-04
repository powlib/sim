
from abc         import ABCMeta, abstractmethod
from collections import deque

class Block(metaclass=ABCMeta):

    def __init__(self):
        pass

    @abstractmethod
    def behavior(self):
        pass

class Port(object):

    def __init__(self, block):
        '''
        Associates the port with a single block.
        '''
        self.__block = block
    
    @property
    def block(self):
        '''
        Safely returns the reference to the associated block.
        '''
        return self.__block

class InPort(Port):

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
        self.block.behavior()
    
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
        try: return self.__data.popLeft()  
        except IndexError: return None

class OutPort(Port):

    def __init__(self, block):
        '''
        '''
        Port.__init__(self, block)
        self.__inports = []

    def connect(self, inport):
        '''
        Connects the specified inport to the
        output.
        '''

        self.__inports.append(inport)

    def disconnect(self, inport):
        '''
        Searches for the specified inport, and disconnects it 
        from the outport if found.
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
            return True

        return False            

    def write(self, data):
        '''
        Writes data to all the inports connected to
        the this outport.
        '''
        for inp in self.__inports:
            inp.write(data)
        


