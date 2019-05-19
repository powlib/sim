from powlib.verify.block             import Block, InPort, OutPort
from powlib.verify.agents.BusAgent   import OP_WRITE, OP_READ
from powlib                          import Transaction

from inspect                         import isclass

# Condition functions intended to be used with SwissBlock
AllCondFunc = lambda *rdys : all(rdys)
AnyCondFunc = lambda *rdys : any(rdys)

# Constants needed by the ram block.
BYTE_WIDTH = 8
BYTE_MASK  = (1<<BYTE_WIDTH)-1

def ComposeBlocks(*blocks):
    '''
    A utility function used for quickly connecting blocks that define
    inport and outport attributes. The first block only needs an outport,
    whereas the last block only needs an inport. Every block in between
    needs both.
    '''
    previous_block = None
    for block in blocks:
        if not isinstance(block,Block):
            raise TypeError("Only blocks can be composed.")        
        if previous_block is not None:
            previous_block.outport.connect(block.inport)
        previous_block = block                  

class ComposedBlock(Block):
    '''
    A class wrapper for composing blocks. Works the same as ComposeBlocks,
    however this class contains members for the inport of the first block
    and the outport of the last block, if the ports exist.
    '''
    def __init__(self, *blocks):
        ComposeBlocks(*blocks)
        self.__inport  = blocks[0].inport   if hasattr(blocks[0], "inport")   else None
        self.__outport = blocks[-1].outport if hasattr(blocks[-1],"outport")  else None

    inport  = property(lambda self : self.__inport)
    outport = property(lambda self : self.__outport)                      

    def _behavior(self): raise NotImplementedError("Composed blocks don't implement their own behavior.")        

class SourceBlock(Block):
    '''
    A simply block whose only purpose is to provide
    data into the design.
    '''        

    def __init__(self):
        '''
        Constructor.
        '''
        self.__outport    = OutPort(block=self)

    def write(self, data):
        '''
        Writes data into the outport and executes the behavior.
        '''
        self.__outport.write(data, execute_behavior=True)

    @property
    def outport(self):
        '''
        Safely return the outport.
        '''        
        return self.__outport

    def _behavior(self):
        '''
        Implements the behavior of the block.
        '''        
        raise NotImplementedError("The behavior is not implemented for source block.")

class SwissBlock(Block):
    '''
    A block from which many other various blocks can be created.
    '''

    def __init__(self, trans_func, cond_func=AllCondFunc, inputs=1):
        '''
        Constructor. The trans_func is a function that should define the
        behavior of the swiss block. Its input parameters are the values read from each
        of the inports. If it returns a value, that value will be written to 
        the SwissBlock's outport. cond_func is a function that should determine
        when the trans_func is called. Its input parameters are the ready booleans
        of the inports. It should return another boolean, where True causes the
        trans_func to be called.
        '''
        self.__inports    = [InPort(block=self) for _ in range(inputs)]
        self.__outport    = OutPort(block=self)
        self.__trans_func = trans_func
        self.__cond_func  = cond_func

    @property
    def inport(self):
        '''
        Safely return the first inport.
        '''
        return self.inports(0)

    @property
    def outport(self):
        '''
        Safely return the outport.
        '''
        return self.__outport

    def inports(self, idx):
        '''
        Returns the specified inport.
        '''
        return self.__inports[idx]

    def _behavior(self):
        '''
        Implements the behavior of the block.
        '''

        rdys = [inp.ready() for inp in self.__inports]
        cond = self.__cond_func(*rdys)        
        if cond:
            data = [inp.read() for inp in self.__inports]
            ret  = self.__trans_func(*data)
            if ret is not None: self.__outport.write(data=ret)                      

class ScoreBlock(SwissBlock):
    '''
    Used for scoring a set of values.
    '''

    def __init__(self, inputs=2, name="", logger=None, log_score=True):
        '''
        Constructor.
        
        inputs:
            Specifies the number of inputs.
            
        name:
            String identifier for the block.
            
        logger:
            Reference to a specified logger. If set to None and log_score is True,
            the cocotb logger will be utilized.
            
        log_score:
            Enables logging if set to True.
        '''
        SwissBlock.__init__(self, trans_func=self._score_func, inputs=inputs)
        if log_score:
            if logger is None:
                from cocotb.log import SimLog        
                self.__log = SimLog("cocotb.score.{}".format(name))
            else:
                self.__log = logger
        self.__log_score = log_score

    def _score_func(self, *values):
        '''
        Checks to see if all the inputs presented in values are the same. If they're 
        the same, a True is returned, otherwise a False is returned.
        '''
        check   = values[0]
        state   = True
        message = ""
        for val in values:
            message += "{}==".format(val)
            state   &= check==val
        message += "EQUAL" if state==True else "DIFFERENT"
        if self.__log_score==True: self.__log.info(message)

        return state
    
    def compare(self, *args):
        '''
        Directly write values for comparison to the score block.
        '''
        for idx, arg in enumerate(args):
            self.inports(idx).write(data=arg)
        

class AssertBlock(SwissBlock):
    '''
    Simply throws TestFailure if a False
    is received.
    '''        
    def __init__(self, inputs=1, Class=None):
        '''
        Assigns the transfer function the 
        failure method.
        
        inputs:
            Number of inputs that can be asserted on.
            
        Class:
            Class that will be thrown on a failed assertion. If set to None, the cocotb
            TestFailure is utilized.
        '''
        SwissBlock.__init__(self, trans_func=self._failure_func, inputs=inputs)
        if Class is None:
            from cocotb.result import TestFailure
            self.__Class = TestFailure
        else:
            if not isclass(Class):
                raise TypeError("Class must be a class.")
            self.__Class = Class 

    def _failure_func(self, *states):
        '''
        If the state is False, a TestFailure()
        is raised.
        '''
        if any(state==False for state in states): raise self.__Class()

class SucceedBlock(SwissBlock):
    '''
    Simply throws TestSuccess if a True is received.
    '''     
    def __init__(self, Class=None):
        '''
        Assigns the transfer function the 
        succeed method.
        
        Class:
            Class that will be thrown on a success. If set to None, the cocotb
            TestSuccess is utilized.        
        '''
        SwissBlock.__init__(self, self._success_func)
        if Class is None:
            from cocotb.result import TestSuccess
            self.__Class = TestSuccess
        else:
            if not isclass(Class):
                raise TypeError("Class must be a class.")
            self.__Class = Class         

    def _success_func(self, state):
        '''
        If the state is False, a TestFailure()
        is raised.
        '''
        if state==True: raise self.__Class()

class CountBlock(SwissBlock):
    '''
    Increments upon an input. Returns true once
    the count reach the total.
    '''

    def __init__(self, total, inputs):
        SwissBlock.__init__(self, trans_func=self._count_func, inputs=inputs)
        self.__total = total
        self.__count = 0

    def _count_func(self, *ignore):
        self.__count += 1
        return self.__count==self.__total        

class PrintBlock(SwissBlock):
    '''
    Simply prints out the data it
    receives.
    '''
    def __init__(self, name="data", logger=None):
        SwissBlock.__init__(self, trans_func=self._print_func)
        if logger is None:
            from cocotb.log import SimLog
            self.__log = SimLog("cocotb.print.{}".format(name))
        else:
            self.__log = logger

    def _print_func(self, data):
        self.__log.info("{}".format(data))  
        
class RamBlock(SwissBlock):
    '''
    This is simulated RAM. Very useful since a test that needs RAM won't need
    RAM implemented in the hardware description.
    '''
    
    def __init__(self, bpd=4, defaultByte=0x00):
        '''
        Constructor. bpd is the bytes-per-data word. defaultByte is the byte that
        will be returned if a read is issue on a location that hasn't been written
        to.
        '''
        SwissBlock.__init__(self, trans_func=self._ram_func)
        self.__ram         = {}
        self.__bpd         = bpd
        self.__defaultByte = defaultByte&BYTE_MASK
    
    def write(self, addr, data, be=0xF):
        '''
        Writes data to the ram block. addr refers to the address. data
        refers to the word that will be written to the ram. be is the byte enable.
        '''
        for each_byte in range(self.__bpd):
            if be&1:
                byte                 = data&BYTE_MASK
                byteAddr             = addr+each_byte
                self.__ram[byteAddr] = byte
            data >>= BYTE_WIDTH
            be   >>= 1
            
    def read(self, addr):
        '''
        Reads a word from the ram. addr is the address from where the data will
        be read.
        '''
        data = 0
        for each_byte in range(self.__bpd):
            byteAddr = addr+each_byte
            byte     = self.__ram.get(byteAddr, self.__defaultByte)
            data    |= byte<<(each_byte*BYTE_WIDTH)
        return data
    
    def _ram_func(self, trans):
        '''
        Implements the behavior of the ram so that other blocks can perform
        operations with it via ports.
        '''
        if hasattr(trans, "data"):
            self.write(addr=trans.addr, data=trans.data, be=trans.be)
        else:
            return self.read(addr=trans.addr)
        
class BusRamConvertBlock(Block):
    '''
    Connects between a BusAgent and RamBlock. This allows simulated RAM, i.e.
    the RamBlock, for use in hardware.
    '''
    
    def __init__(self, bpd=4):
        '''
        Constructor. bpd is the number of bytes in a data word.
        '''
        self.__bpd        = bpd
        self.__busInport  = InPort(block=self)
        self.__busOutport = OutPort(block=self)
        self.__ramInport  = InPort(block=self)
        self.__ramOutport = OutPort(block=self)
        
    busInport  = property(lambda self : self.__busInport)
    busOutport = property(lambda self : self.__busOutport)
    ramInport  = property(lambda self : self.__ramInport)
    ramOutport = property(lambda self : self.__ramOutport)
    
    def _behavior(self):
        '''
        Implements the behavior of the converter block.
        '''
        
        if self.busInport.ready():
            trans = self.busInport.read()
            op    = int(trans.op.value)
            if   op==OP_WRITE:
                self.ramOutport.write(data=Transaction(addr=int(trans.addr),
                                                       data=int(trans.data),
                                                       be=int(trans.be)))
            elif op==OP_READ:
                self.ramOutport.write(data=Transaction(addr=int(trans.addr),
                                                       be=int(trans.be)),
                                      execute_behavior=True)
                assert(self.ramInport.ready())
                data = self.ramInport.read()
                self.busOutport.write(data=Transaction(addr=int(trans.data),
                                                       data=data,
                                                       be=int((1<<self.__bpd)-1),
                                                       op=OP_WRITE))
            else: raise ValueError("op of value {} isn't defined.".format(op))
                
            