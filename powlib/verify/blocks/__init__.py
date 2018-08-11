from cocotb.log          import SimLog
from cocotb.result       import TestFailure, TestSuccess
from powlib.verify.block import Block, InPort, OutPort

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

    def __init__(self, trans_func, cond_func = lambda *rdys : all(rdys), inputs=1):
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
        SwissBlock.__init__(self=self, trans_func=self._score_func, inputs=inputs)
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
