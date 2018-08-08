
from cocotb                  import fork
from cocotb.decorators       import coroutine
from cocotb.log              import SimLog
from cocotb.triggers         import Event, NullTrigger

from powlib.utils            import start_clock, start_reset
from powlib.verify.component import Driver

class ClockDriver(Driver):
    '''
    The clock driver simply drives the system's clocks.
    '''

    def __init__(self, interface, param_namespace, name=""):
        '''
        Constructs the clock driver.
        interface       = The interface associated with the driver should contain the
                          cocotb handles to all the clocks that need to be driven.
        param_namespace = A namespace with parameters associated with each clock 
                          in interface.
        name            = String identifier needed for logging.                       
        '''
        self.__param_namespace = param_namespace
        self.__log             = SimLog("cocotb.clks.{}".format(name))
        Driver.__init__(self, interface)        

    @property
    def inport(self):
        '''
        Not data should be written to the clock driver.
        '''
        raise NotImplemented("Do not write data into the clock driver.")

    def write(self, data):
        '''
        Not data should be written to the clock driver.
        '''
        raise NotImplemented("Do not write data into the clock driver.")   

    @coroutine
    def _drive(self):        
        '''
        Implements the behavior of the clock driver.
        '''

        for name, handle in vars(self._interface).items():
            params     = getattr(self.__param_namespace, name, None)
            period     = getattr(params, "period", None)            
            phase      = getattr(params, "phase", None)
            param_dict = {}
            if period is not None: param_dict["period"] = period
            if phase  is not None: param_dict["phase"]  = phase
            self.__log.info("Starting clock {} with period {} and phase {}...".format(name, period, phase))
            fork(start_clock(clock=handle, **param_dict))

        yield NullTrigger()

class ResetDriver(Driver):
    '''
    This driver simply drives the system's resets.
    '''

    def __init__(self, interface, param_namespace, name=""):
        '''
        Constructor.                        
        interface       = The interface associated with the driver should contain the
                          cocotb handles to all the resets that need to be driven.
        param_namespace = A namespace with parameters associated with each clock 
                          in interface.
        name            = String identifier needed for logging.           
        '''
        self.__param_namespace        = param_namespace
        self.__event                  = Event()
        self.__log                    = SimLog("cocotb.rsts.{}".format(name))
        Driver.__init__(self, interface)

    @coroutine
    def wait(self):
        '''
        Yield on this method as a way to wait until
        all resets finish their operation.
        '''
        yield self.__event.wait()

    @coroutine
    def _drive(self):        
        '''
        Implements the behavior of the reset driver.
        '''

        # Define a simply function for extracting a parameter corresponding
        # to a reset.
        def add_param(params, param_name, param_dict):
            param = getattr(params, param_name, None)
            if param is not None: param_dict[param_name] = param

        # The running coroutines need to be collected.
        cos = []            

        # Collect the parameters and run each reset's respective 
        # start reset coroutine.
        for name, handle in vars(self._interface).items():        
            params     = getattr(self.__param_namespace, name, None)
            param_dict = {}
            add_param(params=params, param_name="active_mode",      param_dict=param_dict)
            add_param(params=params, param_name="associated_clock", param_dict=param_dict)
            add_param(params=params, param_name="wait_cycles",      param_dict=param_dict)
            add_param(params=params, param_name="wait_time",        param_dict=param_dict)
            self.__log.info("Initiating reset {}...".format(name))            
            self.__log.info("DEBUG: {}".format(param_dict))
            cos.append(fork(start_reset(reset=handle, **param_dict)))

        # Wait until all start reset coroutines finish their operation.
        for co in cos: yield co.join()
        self.__event.set()            
        self.__log.info("Resets have been de-asserted...")        
