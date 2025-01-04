TOPLEVEL_LANG ?= verilog
SIM ?= icarus
VERILOG_SOURCES = $(shell pwd)/i2c_top.sv
TOPLEVEL := i2c_top # Verilog or SystemVerilog TOP file module name
MODULE   := i2c_tb # Python file name


include $(shell cocotb-config --makefiles)/Makefile.sim
