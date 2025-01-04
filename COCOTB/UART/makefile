TOPLEVEL_LANG ?= verilog
SIM ?= icarus
VERILOG_SOURCES = $(shell pwd)/uart_top.sv
TOPLEVEL := uart_top # Verilog or SystemVerilog TOP file module name
MODULE   := uart_tb # Python file name


include $(shell cocotb-config --makefiles)/Makefile.sim
