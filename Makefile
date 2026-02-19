# Default targets
.PHONY: default usage build start stop clean install
default: usage

# Makefile setup
SHELL:=/bin/bash
 
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
NICS?=false
BRIDGES?=true
FIREWALL?=true
CMD?=cmd1
# TEMPLATEDIR?="../idris-iso-config"
TEMPLATEDIR?="."
# TEMPLATEDIR?="."

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
install-pip: $(DIR_VENV)
	source $(DIR_VENV)/bin/activate && \
		pip install --upgrade build && \
		pip install -r requirements.txt ; \
		python -m build
install-tools: #build
	sudo apt -y install python3.13 python3.13-venv python3-pip \
		qemu-kvm xorriso ovmf swtpm wimtools isolinux mkisofs randmac
	source $(DIR_VENV)/bin/activate ; pip install --editable .
build: 
	@source $(DIR_VENV)/bin/activate ; \
		python3 -m src.$(PROJECT_NAME).main  -tp build_all \
			-tw $(TEMPLATEDIR) -tt $(TEMPLATE) -to "$(OVERLAY)" -rv $(VERBOSITY)

build-all: 
	@source $(DIR_VENV)/bin/activate ; \
		python3 -m src.$(PROJECT_NAME).main  -tp build_all \
			-tw $(TEMPLATEDIR) -tt $(TEMPLATE) -to "*" -rv $(VERBOSITY)
boot: 
	@source $(DIR_VENV)/bin/activate ; \
		python3 -m src.$(PROJECT_NAME).main  -tp vm_start \
			-tw $(TEMPLATEDIR) -tt $(TEMPLATE) -to "$(OVERLAY)" \
			-rD $(DAEMONIZE) -rv $(VERBOSITY) \
			-rnpf false -rnpb false -rnpn true \
			-rov false -rbC false
install: 
	@source $(DIR_VENV)/bin/activate ; \
		python3 -m src.$(PROJECT_NAME).main  -tp vm_start -rbC true \
			-tw $(TEMPLATEDIR) -tt $(TEMPLATE) -to "$(OVERLAY)" \
			-rnpf false -rnpb false -rnpn true \
			-rD $(DAEMONIZE) -rv $(VERBOSITY) -rov true
stop:
	@source $(DIR_VENV)/bin/activate ; \
		python3 -m src.$(PROJECT_NAME).main -tp vm_stop \
			-tw $(TEMPLATEDIR) -tt $(TEMPLATE) -to "$(OVERLAY)" -rv $(VERBOSITY) \
			-rnpf false -rnpb false -rnpn true

install-all: 
	@source $(DIR_VENV)/bin/activate ; \
		python3 -m src.$(PROJECT_NAME).main -tp vm_start \
			-tw $(TEMPLATEDIR) -tt $(TEMPLATE) -to "*" \
			-rD $(DAEMONIZE) -rv $(VERBOSITY)
stop-all:
	@source $(DIR_VENV)/bin/activate ; \
		python3 -m src.$(PROJECT_NAME).main -tp vm_stop \
			-tw $(TEMPLATEDIR) -tt $(TEMPLATE) -to "*" -rv $(VERBOSITY)
exec: 
	@source $(DIR_VENV)/bin/activate ; \
		python3 -m src.$(PROJECT_NAME).main \
			-tw $(TEMPLATEDIR) -tt $(TEMPLATE) -to "$(OVERLAY)" -tp exec \
			-rD $(DAEMONIZE) -rv $(VERBOSITY) -cc "$(CMD)"
target: 
	@source $(DIR_VENV)/bin/activate ; \
		python3 -m src.$(PROJECT_NAME).main \
			-tw $(TEMPLATEDIR) -tt $(TEMPLATE) -to "$(OVERLAY)" -tp $(TARGET) \
			-rD $(DAEMONIZE) -rv $(VERBOSITY)

target-all: 
	@source $(DIR_VENV)/bin/activate ; \
		python3 -m src.$(PROJECT_NAME).main -to "*" \
			-tw $(TEMPLATEDIR) -tt $(TEMPLATE) -tp $(TARGET) \
			-rD $(DAEMONIZE) -rv $(VERBOSITY)

restart: | stop start
restart-all: | stopall startall

net-start: 
	@source $(DIR_VENV)/bin/activate ; \
		python3 -m src.$(PROJECT_NAME).main -tp net_start \
			-tw $(TEMPLATEDIR) -tt $(TEMPLATE) -to "$(OVERLAY)" -rv $(VERBOSITY) \
			-rnpf "$(FIREWALL)" -rnpb "$(BRIDGES)" -rnpn "$(NICS)"
net-stop: 
	@source $(DIR_VENV)/bin/activate ; \
		python3 -m src.$(PROJECT_NAME).main -tp net_stop \
			-tw $(TEMPLATEDIR) -tt $(TEMPLATE) -to "$(OVERLAY)" -rv $(VERBOSITY) \
			-rnpf "$(FIREWALL)" -rnpb "$(BRIDGES)" -rnpn "$(NICS)"

help: 
	@source $(DIR_VENV)/bin/activate ; \
		python3 -m src.$(PROJECT_NAME).main -h
clean:
	rm -rf build dist src/$(PROJECT_NAME).egg-info
	sudo rm -rf data/out/
