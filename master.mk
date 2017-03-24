.PHONY: venv test regen-reqs regen-venv coverage test package

VENV_DIR=venv
PYTHON_VERSION=3.5
SITE_PACKAGES_PATH=$(VENV_DIR)/lib/python$(PYTHON_VERSION)/site-packages
SYSTEM_PYTHON=python$(PYTHON_VERSION)
PYTHON=./$(VENV_DIR)/bin/python
PACKAGEDIR=../packages
PIP=$(VENV_DIR)/bin/pip
PIPINSTALL=$(VENV_DIR)/bin/pip install --extra-index-url $(PACKAGEDIR)
SCRATCH_DIR=tmp
REGEN_VENV=$(SCRATCH_DIR)/regen_venv
REGEN_PIP=$(REGEN_VENV)/bin/pip
REGEN_PIPINSTALL=$(REGEN_VENV)/bin/pip install --extra-index-url $(PACKAGEDIR)
# These packages are only pulled in by setuptools, so don't pin them
REQ_BLACKLIST=appdirs packaging pyparsing
TESTDIR=test
TEST ?= discover
TESTOPTS=

venv: python

python:
	$(SYSTEM_PYTHON) -m venv --clear $(VENV_DIR)
	$(PIP) install -U pip setuptools wheel
	$(PIPINSTALL) -e .
	# Unfortunately tests_requires installs into the base dir, so we have
	# to use a separate requirements.txt file for the tests :(
	if [ -a $(TESTDIR)/requirements.txt ]; then \
		$(PIPINSTALL) -vvv -r $(TESTDIR)/requirements.txt; \
	fi;
	echo "#!/bin/sh" > $@
	echo 'exec $(PWD)/$(VENV_DIR)/bin/python "$$@"' >> $@
	chmod +x $@

test: venv
	$(PYTHON) -m unittest $(TEST) $(TESTOPTS)

regen-reqs:
	$(SYSTEM_PYTHON) -m venv --clear $(REGEN_VENV)
	$(REGEN_PIPINSTALL) .
	$(REGEN_PIP) freeze > requirements.txt

regen-venv: regen-reqs venv

coverage:
	-rm -f .coverage.* .coverage
	$(PIP) install -U coverage
	echo "import coverage;coverage.process_startup()" > $(SITE_PACKAGES_PATH)/sitecustomize.py
	COVERAGE_PROCESS_START=.coveragerc $(PYTHON) -m coverage run -m unittest $(TEST) $(TESTOPTS)
	-rm -f $(SITE_PACKAGES_PATH)/sitecustomize.py
	$(PYTHON) -m coverage combine
	$(PYTHON) -m coverage html -d $(SCRATCH_DIR)/coverage/html
	@echo "HTML results in $(SCRATCH_DIR)/coverage/html"
	$(PYTHON) -m coverage annotate -d $(SCRATCH_DIR)/coverage/annotations
	@echo "Annotated source files in $(SCRATCH_DIR)/coverage/annotations"
	$(PYTHON) -m coverage report

package: name := $(shell $(PYTHON) setup.py --name)
package: venv
	mkdir -p $(PACKAGEDIR)/$(name)
	$(PYTHON) setup.py sdist
	mv dist/* $(PACKAGEDIR)/$(name)
	rm -r $(name).egg-info
	rmdir dist
	# Do wheel too?  Or instead?
