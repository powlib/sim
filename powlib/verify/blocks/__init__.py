from cocotb.log          import SimLog
from powlib.verify.block import Block, InPort, OutPort

class SwissBlock(Block):
    '''
    A block from which many other various blocks can be created.
    '''

    def __init__(self, trans_func, cond_func = lambda *rdys : all(rdys), inputs=1):
        '''
        Constructor.
        '''
        self.__inports    = [InPort(parent=self) for _ in range(inputs)]
        self.__outport    = OutPort(parent=self)
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
        return self.__inports(idx)

    def _behavior(self):
        '''
        Implements the behavior of the block.
        '''

        rdys = (inp.ready() for inp in self.__inports)
        cond = self.__cond_func(*rdys)
        if cond:
            data = (inp.read() for inp in self.__inports)
            ret  = self.__trans_func(*data)
            if ret is not None: self.__outport.write(data=ret)                      

class ScoreBlock(SwissBlock):
    '''
    Used for scoring a set of values.
    '''

    def __init__(self, inputs=1, name="", log_score=True):
        '''
        '''
        SwissBlock.__init__(self, inputs, self._score_func)
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



