TOPLEVEL_LANG ?= verilog
SIM ?= icarus
VERILOG_SOURCES = $(shell pwd)/top.sv
TOPLEVEL := top # Verilog or SystemVerilog TOP file module name
MODULE   := spi_tb # Python file name


include $(shell cocotb-config --makefiles)/Makefile.sim
