# Default targets
.PHONY: default usage build start stop clean
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
TARGET ?= "vmbuild_all"
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
update_dummies:
	@find . -type f \( -name "*.md" -o -name "*.py" -o -name "*.toml" -o -name "*.cfg" -o -name "*.in" \) \
		-exec sed -i "s/DUMMY_NAME/$(PROJECT_NAME)/g" {} +
	@find . -type f \( -name "*.md" -o -name "*.py" -o -name "*.toml" -o -name "*.cfg" -o -name "*.in" \) \
		-exec sed -i "s/DUMMY_AUTHOR/$(PROJECT_AUTHOR)/g" {} +
	@find . -type f \( -name "*.md" -o -name "*.py" -o -name "*.toml" -o -name "*.cfg" -o -name "*.in" \) \
		-exec sed -i "s/DUMMY_EMAIL/$(PROJECT_EMAIL)/g" {} +
	@find . -type f \( -name "*.md" -o -name "*.py" -o -name "*.toml" -o -name "*.cfg" -o -name "*.in" \) \
		-exec sed -i "s/DUMMY_VERSION/$(PROJECT_VERSION)/g" {} +
build: | update_dummies $(DIR_VENV)
	source $(DIR_VENV)/bin/activate && \
		pip install --upgrade build && \
		pip install -r requirements.txt && \
		python -m build
install: build
	sudo apt install qemu-kvm xorriso ovmf swtpm wimtools isolinux mkisofs
	source $(DIR_VENV)/bin/activate && \
		pip install --editable .
debugbuild: 
	@source $(DIR_VENV)/bin/activate ; \
		python3 -m src.$(PROJECT_NAME).main $(TARGET)
debugrun: 
	@source $(DIR_VENV)/bin/activate ; \
		python3 -m src.$(PROJECT_NAME).main "vmrun"

fullstart: build
	source $(DIR_VENV)/bin/activate ; \
		$(PROJECT_NAME)
stop:
	echo "Stop"
clean:
	rm -rf build dist src/$(PROJECT_NAME).egg-info
	sudo rm -rf data/out/
