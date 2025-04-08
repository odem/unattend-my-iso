# Default targets
.PHONY: default usage build start stop clean install
default: usage

# Makefile setup
SHELL:=/bin/bash
# username ALL=(ALL) NOPASSWD: /usr/bin/mount, /usr/bin/umount, 
# /usr/bin/rm, /usr/bin/mkdir, /usr/bin/chmod, /usr/bin/chown, 
# /usr/bin/mv, /usr/bin/cp, /usr/sbin/mkfs.fat, /usr/bin/wimlib-imagex, 
# /usr/local/bin/nvim, /usr/bin/qemu-system-x86_64
 
PROJECT_NAME:=unattend_my_iso
PROJECT_AUTHOR:=jb
PROJECT_EMAIL:=foo@bar.baz
PROJECT_VERSION:=0.0.1
DIR_VENV?=.venv
TARGET?="all"
TEMPLATE?="mps"
OVERLAY?=""
VERBOSITY?=2
DAEMONIZE?=true
BRIDGES?=true
NICS?=false

# Help
usage:
	@echo "make TARGET"
	@echo "   TARGETS: "
	@echo ""
	@echo "     clean  : Cleans tempfiles"
	@echo "     build  : Help message"
	@echo "     install: Install tool"
	@echo ""
	@echo "     start  : Starts tool"
	@echo "     stop   : Stops tool"
	@echo ""
	@echo "     usage  : Help message"
	@echo ""

# Targets
$(DIR_VENV):
	if [[ ! -d $(DIR_VENV) ]]; then \
		python3 -m venv $(DIR_VENV) ; \
	fi
build-pip: $(DIR_VENV)
	source $(DIR_VENV)/bin/activate && \
		pip install --upgrade build && \
		pip install -r requirements.txt && \
		python -m build
install: build
	sudo apt install qemu-kvm xorriso ovmf swtpm wimtools isolinux mkisofs
	source $(DIR_VENV)/bin/activate && \
		pip install --editable .
build: 
	@source $(DIR_VENV)/bin/activate ; \
		python3 -m src.$(PROJECT_NAME).main \
			-tt $(TEMPLATE) -to "$(OVERLAY)" -tp build_all -rv $(VERBOSITY)

build-all: 
	@source $(DIR_VENV)/bin/activate ; \
		python3 -m src.$(PROJECT_NAME).main \
			-tt $(TEMPLATE) -to "*" -tp build_all -rv $(VERBOSITY)
start: 
	@source $(DIR_VENV)/bin/activate ; \
		python3 -m src.$(PROJECT_NAME).main \
			-tt $(TEMPLATE) -to "$(OVERLAY)" -tp vm_start \
			-rD $(DAEMONIZE) -rv $(VERBOSITY)
stop:
	@source $(DIR_VENV)/bin/activate ; \
		python3 -m src.$(PROJECT_NAME).main \
			-tt $(TEMPLATE) -to "$(OVERLAY)" -tp vm_stop -rv $(VERBOSITY)
start-all: 
	@source $(DIR_VENV)/bin/activate ; \
		python3 -m src.$(PROJECT_NAME).main \
			-tt $(TEMPLATE) -to "*" -tp vm_start \
			-rD $(DAEMONIZE) -rv $(VERBOSITY)
stop-all:
	@source $(DIR_VENV)/bin/activate ; \
		python3 -m src.$(PROJECT_NAME).main \
			-tt $(TEMPLATE) -to "*" -tp vm_stop -rv $(VERBOSITY)
target: 
	@source $(DIR_VENV)/bin/activate ; \
		python3 -m src.$(PROJECT_NAME).main \
			-tt $(TEMPLATE) -to "$(OVERLAY)" -tp $(TARGET) \
			-rD $(DAEMONIZE) -rv $(VERBOSITY)

target-all: 
	@source $(DIR_VENV)/bin/activate ; \
		python3 -m src.$(PROJECT_NAME).main \
			-tt $(TEMPLATE) -to "*" -tp $(TARGET) \
			-rD $(DAEMONIZE) -rv $(VERBOSITY)

restart: | stop start
restart-all: | stopall startall

net-start: 
	@source $(DIR_VENV)/bin/activate ; \
		python3 -m src.$(PROJECT_NAME).main \
			-tt $(TEMPLATE) -to "$(OVERLAY)" -tp net_start \
			-rv $(VERBOSITY) -rnpb "$(BRIDGES)" -rnpn "$(NICS)"
net-stop: 
	@source $(DIR_VENV)/bin/activate ; \
		python3 -m src.$(PROJECT_NAME).main \
			-tt $(TEMPLATE) -to "$(OVERLAY)" -tp net_stop \
			-rv $(VERBOSITY) -rnpb "$(BRIDGES)" -rnpn "$(NICS)"

help: 
	@source $(DIR_VENV)/bin/activate ; \
		python3 -m src.$(PROJECT_NAME).main -h
clean:
	rm -rf build dist src/$(PROJECT_NAME).egg-info
	sudo rm -rf data/out/
