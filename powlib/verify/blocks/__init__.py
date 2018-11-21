from cocotb.log          import SimLog
from cocotb.result       import TestFailure, TestSuccess
from powlib.verify.block import Block, InPort, OutPort

# Condition functions intended to be used with SwissBlock
AllCondFunc = lambda *rdys : all(rdys)
AnyCondFunc = lambda *rdys : any(rdys)

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

    def _behavior(self): raise NotImplemented("Composed blocks don't implement their own behavior.")        

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
        Writes data into the outport.
        '''
        self.__outport.write(data)

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
        raise NotImplemented("The behavior is not implemented for source block.")

class SwissBlock(Block):
    '''
    A block from which many other various blocks can be created.
    '''

    def __init__(self, trans_func, cond_func=AllCondFunc, inputs=1):
        '''
        Constructor.
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

    def __init__(self, inputs=2, name="", log_score=True):
        '''
        '''
        SwissBlock.__init__(self, trans_func=self._score_func, inputs=inputs)
        self.__log       = SimLog("cocotb.score.{}".format(name))
        self.__log_score = log_score

    def _score_func(self, *values):
        '''
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

class AssertBlock(SwissBlock):
    '''
    Simply throws TestFailure if a False
    is received.
    '''        
    def __init__(self):
        '''
        Assigns the transfer function the 
        failure method.
        '''
        SwissBlock.__init__(self, self._failure_func)

    def _failure_func(self, state):
        '''
        If the state is False, a TestFailure()
        is raised.
        '''
        if state==False: raise TestFailure()

class SucceedBlock(SwissBlock):
    '''
    Simply throws TestSuccess if a True is received.
    '''     
    def __init__(self):
        '''
        Assigns the transfer function the 
        succeed method.
        '''
        SwissBlock.__init__(self, self._success_func)

    def _success_func(self, state):
        '''
        If the state is False, a TestFailure()
        is raised.
        '''
        if state==True: raise TestSuccess()

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
    def __init__(self, name="data"):
        SwissBlock.__init__(self, trans_func=self._print_func)
        self.__log       = SimLog("cocotb.print.{}".format(name))

    def _print_func(self, data):
        self.__log.info("{}".format(data))        

