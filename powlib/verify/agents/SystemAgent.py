
from cocotb                  import fork
from cocotb.decorators       import coroutine
from cocotb.log              import SimLog
from cocotb.triggers         import Event

from powlib.utils            import start_clock, start_reset
from powlib.verify.component import Driver

class ClockDriver(Driver):
    '''
    The clock driver simply drives the system's clocks.
    '''

    def __init__(self, interface, period_trans, phase_trans=None, name=""):
        '''
        Constructs the clock driver.
        interface    = The interface associated with the driver should contain the
                       cocotb handles to all the clocks that need to be driven.
        period_trans = A transaction whose member names should match that of the 
                       specified interface. The value associated with each member should
                       be a 2-tuple representing the period of the clock.
        phase_trans  = A transaction whose member names should match that of the
                       specified interface. The value associated with each member should
                       be a 2-tuple representing the phase of the clock.
        name         = String identifier needed for logging.                       
        '''
        self.__period_trans = period_trans
        self.__phase_trans  = phase_trans
        self.__log          = SimLog("cocotb.clocks.{}".format(name))
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
            period = getattr(self.__period_trans, name)
            phase  = getattr(self.__phase_trans, name, (0,"ns"))
            self.__log.info("Starting clock {} with period {} and phase {}...".format(name, period, phase))
            fork(start_clock(clock=handle, period=period, phase=phase))

class ResetDriver(Driver):
    '''

    '''

    def __init__(self, interface, active_mode_trans=None, associated_clock_trans=None, \
                                  wait_cycles_trans=None, wait_time_trans=None, name=""):
        '''
        '''
        self.__active_mode_trans      = active_mode_trans
        self.__associated_clock_trans = associated_clock_trans
        self.__wait_cycles_trans      = wait_cycles_trans
        self.__wait_time_trans        = wait_time_trans
        self.__event                  = Event()
        self.__log                    = Simlog("cocotb.resets.{}".format(name))
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
        def add_param(param_trans, param_dict, param_name, reset_name):
            param = getattr(param_trans, reset_name, None)
            if param is not None: param_dict[param_name] = param

        # The running coroutines need to be collected.
        cos = []            

        # Collect the parameters and run each reset's respective 
        # start reset coroutine.
        for name, handle in vars(self._interface).items():        
            params = {}
            add_param(param_trans=self.__active_mode_trans,      param_dict=params, param_name="active_mode",      reset_name=name)
            add_param(param_trans=self.__associated_clock_trans, param_dict=params, param_name="associated_clock", reset_name=name)
            add_param(param_trans=self.__wait_cycles_trans,      param_dict=params, param_name="wait_cycles",      reset_name=name)
            add_param(param_trans=self.__wait_time_trans,        param_dict=params, param_name="wait_time",        reset_name=name)
            self.__log.info("Initiating reset {}...".format(name))
            cos.append(start_reset(**params))

        # Wait until all start reset coroutines finish their operation.
        for co in cos: yield co.join()
        self.__event.set()            
        self.__log.info("Resets have been de-asserted...")        
