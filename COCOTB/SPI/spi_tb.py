import cocotb
import random
import logging
from cocotb.triggers import Timer, RisingEdge, ClockCycles, Event, FallingEdge
from cocotb.clock import Clock
from cocotb_coverage.crv import Randomized
from cocotb.queue import Queue
from cocotb.utils import get_sim_time


# transaction : data members for each input and output port


class transaction(Randomized):
    def __init__(self):
        Randomized.__init__(self)
        self.newd   = 0
        self.din    = 0 
        self.dout   = 0
        
        
        self.add_rand("din", list(range(4096)))
        
    def print_in(self, tag = ""):# '[GEN]'
        print(tag,'din:',int(self.din))
       
#generator : Generate random transactions for DUT
        
class generator():
    def __init__(self, queue, event, count):
        self.queue = queue
        self.event = event
        self.count = count
        self.event.clear()

    async def gen_data(self):
            for i in range(self.count):
                t = transaction()
                t.randomize()
                t.print_in("[GEN]")
                await self.queue.put(t)
                await self.event.wait()
                self.event.clear()
                
   
   
   
                
# Apply random transactions to DUT                

class driver():
    def __init__(self, queue, dut):
        self.queue = queue
        self.dut = dut
        
    async def reset_dut(self):
        self.dut.rst.value = 1
        self.dut.din.value  = 0
        self.dut.newd.value  = 0
        print('--------Reset Applied','@ : ',str(get_sim_time(units = 'ns')),'----------------')
        await ClockCycles(self.dut.clk,5)
        print('--------Reset Removed','@ : ',str(get_sim_time(units = 'ns')),'----------------')
        print('-------------------------------------------------------------------------------')
        self.dut.rst.value = 0

    async def recv_data(self):
        while True:
            temp = transaction()
            temp = await self.queue.get()
            temp.print_in('[DRV]')  
            self.dut.din.value = temp.din #apply newdata
            self.dut.newd.value = 1
            await RisingEdge(self.dut.m1.sclk) # remove newd after 1 sclk
            self.dut.newd.value = 0 
            await RisingEdge(self.dut.done) # wait for completion of oper



# collect response of DUT

class monitor():
    def __init__(self, dut,queue):
        self.dut   = dut
        self.queue = queue


    async def sample_data(self):
        while True:
            dout = 0
            rout = 0 
            temp = transaction()
            await RisingEdge(self.dut.m1.sclk)
            temp.din = self.dut.din.value
            await RisingEdge(self.dut.done)
            temp.dout = self.dut.dout.value
            await self.queue.put(temp)
            print('[MON]','din:',int(temp.din),'dout:',int(temp.dout))
            




#compare with expected data

class scoreboard():
    def __init__(self,queue,event):
        self.queue = queue
        self.event = event
     

    async def compare_data(self):
        while True:
            temp = await self.queue.get()
            print('[SCO]','din:',int(temp.din),'dout:',int(temp.dout))
            if temp.dout == temp.din :
                print('Test Passed')
            else:
                print('Test Failed')
                         
            print('-------------------------------------------')
   
            self.event.set()
            
  
       

@cocotb.test()
async def test(dut):
    queue1 = Queue()
    queue2 = Queue()
    event = Event()
    
    gen = generator(queue1, event, 5)
    drv = driver(queue1, dut)
    
    mon = monitor(dut,queue2)
    sco = scoreboard(queue2,event)
    
    cocotb.start_soon(Clock(dut.clk, 10, 'ns').start())
    
    await drv.reset_dut()
    
    cocotb.start_soon(gen.gen_data())
    cocotb.start_soon(drv.recv_data())
    cocotb.start_soon(mon.sample_data())
    cocotb.start_soon(sco.compare_data())

    await Timer(5000, 'ns')

