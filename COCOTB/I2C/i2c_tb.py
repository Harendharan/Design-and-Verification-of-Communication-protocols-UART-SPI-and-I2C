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
        self.newd    = 0
        self.op      = 0
        self.addr    = 0
        self.din     = 0 
        self.dout    = 0
        self.busy    = 0
        self.ack_err = 0
        
        
        self.add_rand("op", list(range(2)))
        self.add_rand("addr", list(range(128)))
        self.add_rand("din", list(range(256)))
        
        self.add_constraint(lambda addr :  addr == 1)
        self.add_constraint(lambda din  :  din < 50)
        
        
    def print_in(self, tag = ""):
        print(tag,'op:',self.op, 'addr:',self.addr,'din:',int(self.din))
        
    def print_out(self, tag = ""):
        print(tag,'op:',self.op, 'addr:',int(self.addr),'din:',int(self.din),'dout:',int(self.dout))
       
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
        self.dut.rst.value  = 1
        self.dut.din.value  = 0
        self.dut.newd.value = 0
        self.dut.addr.value = 0
        self.dut.op.value   = 0
        print('--------Reset Applied','@ : ',str(get_sim_time(units = 'ns')),'----------------')
        await ClockCycles(self.dut.clk,5)
        print('--------Reset Removed','@ : ',str(get_sim_time(units = 'ns')),'----------------')
        print('-------------------------------------------------------------------------------')
        self.dut.rst.value = 0
        
    async def wr_op(self,tr):
        self.dut.rst.value   = 0
        self.dut.newd.value  = 1
        self.dut.din.value   = tr.din
        self.dut.addr.value  = tr.addr
        self.dut.op.value    = 0
        tr.print_in("[DRV]")
        await ClockCycles(self.dut.clk,5)
        self.dut.newd.value  = 0
        await RisingEdge(self.dut.done)
        
        
    async def rd_op(self,tr):
        self.dut.rst.value   = 0
        self.dut.newd.value  = 1
        self.dut.din.value   = 0
        self.dut.addr.value  = tr.addr
        self.dut.op.value    = 1
        await ClockCycles(self.dut.clk,5)
        self.dut.newd.value  = 0
        await RisingEdge(self.dut.done)
        tr.dout              = self.dut.dout.value
        tr.print_out("[DRV]")
     

        
        

    async def recv_data(self):
        while True:
            temp = transaction()
            temp = await self.queue.get()
            if temp.op == 0:
                await self.wr_op(temp)
            else:
                await self.rd_op(temp)


# collect response of DUT

class monitor():
    def __init__(self, dut,queue):
        self.dut   = dut
        self.queue = queue


    async def sample_data(self):
        while True:
            temp = transaction()
            await RisingEdge(self.dut.done)
            temp.din = self.dut.din.value
            temp.op = self.dut.op.value
            temp.addr = self.dut.addr.value
            temp.dout = self.dut.dout.value
            await self.queue.put(temp)
            temp.print_out('[MON]')
            




#compare with expected data

class scoreboard():
    def __init__(self,queue,event):
        self.queue = queue
        self.event = event
        self.mem   = dict() 
        
        #initialize all the elements to zero
        for i in range(128):
            self.mem.update({i:i})
     

    async def compare_data(self):
        while True:
            temp = await self.queue.get()
            temp.print_out('[SCO]')
            addr = int(temp.addr)
            din  = int(temp.din)
            dout = int(temp.dout)
            
            if temp.op == 0:
                self.mem.update({addr:din})
                print('[SCO]: Added new data in mem')
            else:
                dout = self.mem.get(addr)
                if temp.dout == dout:
                    print('[SCO] : TEST PASS',dout)
                else:
                    print('[SCO] : Test FAIL',dout)
                         
            print('-------------------------------------------')
   
            self.event.set()
            
  
       

@cocotb.test()
async def test(dut):
    queue1 = Queue()
    queue2 = Queue()
    event = Event()
    
    gen = generator(queue1, event,5)
    drv = driver(queue1, dut)
    
    mon = monitor(dut,queue2)
    sco = scoreboard(queue2,event)
    
    cocotb.start_soon(Clock(dut.clk, 10, 'ns').start())
    
    await drv.reset_dut()
    
    cocotb.start_soon(gen.gen_data())
    cocotb.start_soon(drv.recv_data())
    cocotb.start_soon(mon.sample_data())
    cocotb.start_soon(sco.compare_data())

    await Timer(640000, 'ns')

