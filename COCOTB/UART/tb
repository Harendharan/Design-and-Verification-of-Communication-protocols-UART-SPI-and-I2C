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
        self.newd      = 0
        self.oper      = 1
        self.tx        = 0
        self.rx        = 0 
        self.dintx     = 0
        self.doutrx    = 0
        self.donetx    = 0
        self.donerx    = 0
        
        
        self.add_rand("dintx", list(range(256)))
        self.add_rand("oper", list(range(2)))
        
        #self.add_constraint(lambda dintx :  dintx < 10)
        
       
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
                print('[GEN]: ','oper:',t.oper,'dintx:', int(t.dintx))
                await self.queue.put(t)
                await self.event.wait()
                self.event.clear()
                
   
   
   
                
# Apply random transactions to DUT                

class driver():
    def __init__(self, queuegd, queueds, dut):
        self.queueds = queueds # drv and sco
        self.queuegd = queuegd # gen and drv
        self.dut = dut
        self.dout = 0
        self.rout = 0
        self.rx   = 0
        
    def reverse_Bits(self,n, no_of_bits):
        result = 0
        for i in range(no_of_bits):
            result <<= 1
            result |= n & 1
            n >>= 1
        return result    
        
    async def reset_dut(self):
        self.dut.rst.value    = 1
        self.dut.dintx.value  = 0
        self.dut.newd.value   = 0
        self.dut.rx.value     = 1
        print('--------Reset Applied','@ : ',str(get_sim_time(units = 'ns')),'----------------')
        await ClockCycles(self.dut.clk,5)
        print('--------Reset Removed','@ : ',str(get_sim_time(units = 'ns')),'----------------')
        print('-------------------------------------------------------------------------------')
        self.dut.rst.value = 0
        
    async def data_tx(self,dintx):
        await RisingEdge(self.dut.utx.uclk) #pos edge of tx clock
        self.dut.rst.value   = 0
        self.dut.newd.value  = 1
        self.dut.rx.value    = 1
        self.dut.dintx.value = dintx
        await RisingEdge(self.dut.utx.uclk)
        self.dut.newd.value  = 0
        await self.queueds.put(dintx)
        print('[DRV] : Data Transmitted ',int(dintx))
        await RisingEdge(self.dut.donetx)

        
        
    async def data_rx(self):
        await RisingEdge(self.dut.rtx.uclk)
        self.dut.rst.value   = 0
        self.dut.newd.value  = 0
        self.dut.rx.value    = 0
        await RisingEdge(self.dut.rtx.uclk)
        
        for i in range(8):
            self.rx = random.randint(0,1)
            self.dout = (self.dout << 1) | self.rx
            self.dut.rx.value   = self.rx
            await RisingEdge(self.dut.rtx.uclk)
        
        self.rout = self.reverse_Bits(self.dout,8)
        await self.queueds.put(self.rout)
        print('[DRV] : Data RCVD ',int(self.rout))
        await RisingEdge(self.dut.donerx)
        self.dut.rx.value    = 1    
            
                 
     

        
        

    async def recv_data(self):
        while True:
            temp = transaction()
            temp = await self.queuegd.get()
            dintx = temp.dintx
            if temp.oper == 1:
                await self.data_tx(dintx)
            else:
                await self.data_rx()
            
            
class monitor():
    def __init__(self, dut,queuems):
        self.dut   = dut
        self.queuems = queuems
        self.dout  = 0
        self.rout  = 0

    def reverse_Bits(self,n, no_of_bits):
        result = 0
        for i in range(no_of_bits):
            result <<= 1
            result |= n & 1
            n >>= 1
        return result 
        
        
        
    async def sample_data(self):
        while True:
            temp = transaction()
            await RisingEdge(self.dut.utx.uclk)
            if self.dut.newd.value == 1 and self.dut.rx.value == 1:
                await RisingEdge(self.dut.utx.uclk)
                for i in range(8):
                    await RisingEdge(self.dut.utx.uclk)
                    self.dout = (self.dout << 1) | self.dut.tx.value
                    
                self.rout = self.reverse_Bits(self.dout,8)
                print('[MON]: TX DATA:', int(self.rout))
                await RisingEdge(self.dut.donetx)
                await RisingEdge(self.dut.utx.uclk)
                await self.queuems.put(self.rout)
                
            elif self.dut.rx.value == 0 and self.dut.newd.value == 0:
                await RisingEdge(self.dut.donerx)
                self.rout = self.dut.doutrx.value
                print('[MON]: RX DATA:', int(self.rout))
                await RisingEdge(self.dut.utx.uclk)    
                await self.queuems.put(self.rout)

            
            

class scoreboard():
    def __init__(self,queuems,queueds,event):
        self.queuems = queuems
        self.queueds = queueds
        self.event = event

     

    async def compare_data(self):
        while True:
            tempd = await self.queueds.get()
            tempm = await self.queuems.get()
            print('[SCO]:','Drv:',int(tempd),'Mon:',int(tempm))
            

            
            if tempd == tempm:
                print('[SCO]: Data Matched')
            else:
                print('[SCO]: Data Mismatched')
                         
            print('-------------------------------------------')
   
            self.event.set()
            
  

@cocotb.test()
async def test(dut):
    queuegd = Queue()
    queueds = Queue()
    queuems = Queue()
    event = Event()
    
    gen = generator(queuegd, event,5)
    drv = driver(queuegd,queueds, dut)
    
    mon = monitor(dut,queuems)
    sco = scoreboard(queuems,queueds,event)
    
    cocotb.start_soon(Clock(dut.clk, 10, 'ns').start())
    
    await drv.reset_dut()
    
    cocotb.start_soon(gen.gen_data())
    cocotb.start_soon(drv.recv_data())
    cocotb.start_soon(mon.sample_data())
    cocotb.start_soon(sco.compare_data())

    await Timer(58000, 'ns')
