from cocotb          import coroutine, fork
from cocotb.clock    import Clock
from cocotb.triggers import RisingEdge, ReadOnly, Timer

@coroutine
def start_clock(clock, period, phase=(0,"ns")):
    '''
    Starts a clock.
    clock  = SimHandle of the clock.
    period = Tuple-pair describing the period, for instance  (5,"ns").
    phase  = Tuple-pair describing the phase, for instance (5, "ns").
    '''
    yield Timer(*phase)
    fork(Clock(clock,*period).start())

@coroutine
def start_reset(reset, active_mode=1, associated_clock=None, wait_cycles=4, wait_time=(50,"ns")):
    '''
    reset            = SimHandle of the reset.
    active_mode      = Specifies the active state of the reset.
    associated_clock = If set to the SimHandle of an associated clock, the
                       reset will become inactive after the specified amount
                       of wait cycles. If set to None, the reset will instead
                       become inactive after the specified amount of time.
    wait_cycles      = Specifies the amount of clock cycles needed before the 
                       reset becomes inactive.
    wait_time        = Specifies the amount of time needed before the reset
                       becomes inactive.
    '''

    reset.value = active_mode

    if associated_clock is not None:
        for each_cycle in range(wait_cycles):
            yield ReadOnly()
            yield RisingEdge(associated_clock)
    else:
        yield Timer(*wait_time)

    reset.value = 1-active_mode


