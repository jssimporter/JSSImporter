CURDIR := $(shell pwd)
MUNKIPKG := /usr/local/bin/munkipkg
PKG_ROOT := $(CURDIR)/pkg/jssimporter/payload
PKG_BUILD := $(CURDIR)/pkg/jssimporter/build
PKG_VERSION := $(shell defaults read $(CURDIR)/pkg/jssimporter/build-info.plist version)
JSS_GIT_ROOT := $(abspath $(CURDIR)/../python-jss)

objects = "$(PKG_ROOT)/Library/Application Support/JSSImporter/requests" \
	"$(PKG_ROOT)/Library/Application Support/JSSImporter/boto" \
	$(PKG_ROOT)/Library/AutoPkg/autopkglib/JSSImporter.py \
	"$(PKG_ROOT)/Library/Application Support/JSSImporter/jss"


default : $(PKG_BUILD)/jssimporter-$(PKG_VERSION).pkg
	@echo "Using python-jss git source from $(JSS_GIT_ROOT)"


$(PKG_BUILD)/jssimporter-$(PKG_VERSION).pkg: $(objects)
	cd $(CURDIR)/pkg && $(MUNKIPKG) jssimporter


"$(PKG_ROOT)/Library/Application Support/JSSImporter/boto":
	@echo "Installing boto into JSSImporter support directory"
	#pip install --install-option="--prefix=$(PKG_ROOT)/Library/Application Support/JSSImporter/boto" --ignore-installed boto
	pip install --target "$(PKG_ROOT)/Library/Application Support/JSSImporter" --ignore-installed boto


"$(PKG_ROOT)/Library/Application Support/JSSImporter/requests":
	@echo "Installing requests into JSSImporter support directory"
	#pip install --install-option="--prefix=$(PKG_ROOT)/Library/Application Support/JSSImporter/requests" --ignore-installed requests
	pip install --target "$(PKG_ROOT)/Library/Application Support/JSSImporter" --ignore-installed requests


$(PKG_ROOT)/Library/AutoPkg/autopkglib/JSSImporter.py:
	@echo "Copying JSSImporter.py into autopkglib"
	mkdir -p "$(PKG_ROOT)/Library/AutoPkg/autopkglib"
	cp $(CURDIR)/JSSImporter.py $(PKG_ROOT)/Library/AutoPkg/autopkglib/JSSImporter.py
	chmod 755 "$(PKG_ROOT)/Library/AutoPkg/autopkglib/JSSImporter.py"


"$(PKG_ROOT)/Library/Application Support/JSSImporter/jss":
	@echo "Installing python-jss"
	#@echo "Using amended PYTHONPATH inside package root, otherwise easy_install will complain we arent installing to a PYTHONPATH"
	#cd $(JSS_GIT_ROOT) && PYTHONPATH="$(PKG_ROOT)/Library/Application Support/JSSImporter" easy_install --install-dir "$(PKG_ROOT)/Library/Application Support/JSSImporter" .
	mkdir -p "$(PKG_ROOT)/Library/Application Support/JSSImporter"
	cp -Rf "$(JSS_GIT_ROOT)/jss" "$(PKG_ROOT)/Library/Application Support/JSSImporter"

.PHONY : clean
clean :
	@echo "Cleaning up package root"
	rm $(PKG_ROOT)/Library/AutoPkg/autopkglib/JSSImporter.py
	rm -rf "$(PKG_ROOT)/Library/Application Support/JSSImporter/"*
	rm $(CURDIR)/pkg/jssimporter/build/*.pkg
