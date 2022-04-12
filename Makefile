CURDIR := $(shell pwd)
MUNKIPKG := /usr/local/bin/munkipkg
PKG_ROOT := $(CURDIR)/pkg/jssimporter/payload
PKG_BUILD := $(CURDIR)/pkg/jssimporter/build
PKG_VERSION := $(shell defaults read $(CURDIR)/pkg/jssimporter/build-info.plist version)
JSS_GIT_ROOT := $(abspath $(CURDIR)/../python-jss)

objects = "$(PKG_ROOT)/Library/AutoPkg/JSSImporter/requests" \
	"$(PKG_ROOT)/Library/AutoPkg/JSSImporter/boto" \
	$(PKG_ROOT)/Library/AutoPkg/autopkglib/JSSImporter.py \
	"$(PKG_ROOT)/Library/AutoPkg/JSSImporter/jss"


default : $(PKG_BUILD)/jssimporter-$(PKG_VERSION).pkg
	@echo "Using python-jss git source from $(JSS_GIT_ROOT)"


$(PKG_BUILD)/jssimporter-$(PKG_VERSION).pkg: $(objects)
	cd $(CURDIR)/pkg && python3 $(MUNKIPKG) jssimporter


"$(PKG_ROOT)/Library/AutoPkg/JSSImporter/requests":
	@echo "Installing requests into JSSImporter support directory"
	mkdir -p "$(PKG_ROOT)/Library/AutoPkg/JSSImporter"
	#pip install --install-option="--prefix=$(PKG_ROOT)/Library/AutoPkg/JSSImporter/requests" --ignore-installed requests
	# pip3 install --target "$(PKG_ROOT)/Library/AutoPkg/JSSImporter" --ignore-installed requests
	/usr/local/autopkg/python -m pip install --target "$(PKG_ROOT)/Library/AutoPkg/JSSImporter" --ignore-installed requests


"$(PKG_ROOT)/Library/AutoPkg/JSSImporter/boto":
	@echo "Installing boto into JSSImporter support directory"
	#pip install --install-option="--prefix=$(PKG_ROOT)/Library/AutoPkg/JSSImporter/boto" --ignore-installed boto
	#pip3 install --target "$(PKG_ROOT)/Library/AutoPkg/JSSImporter" --ignore-installed boto
	/usr/local/autopkg/python -m pip install --target "$(PKG_ROOT)/Library/AutoPkg/JSSImporter" --ignore-installed boto


$(PKG_ROOT)/Library/AutoPkg/autopkglib/JSSImporter.py:
	@echo "Copying JSSImporter.py into autopkglib"
	mkdir -p "$(PKG_ROOT)/Library/AutoPkg/autopkglib"
	cp $(CURDIR)/JSSImporter.py $(PKG_ROOT)/Library/AutoPkg/autopkglib/JSSImporter.py
	chmod 755 "$(PKG_ROOT)/Library/AutoPkg/autopkglib/JSSImporter.py"


"$(PKG_ROOT)/Library/AutoPkg/JSSImporter/jss":
	@echo "Installing python-jss"
	cp -Rf "$(JSS_GIT_ROOT)/jss" "$(PKG_ROOT)/Library/AutoPkg/JSSImporter"

.PHONY : clean
clean :
	@echo "Cleaning up package root"
	rm $(PKG_ROOT)/Library/AutoPkg/autopkglib/JSSImporter.py
	rm -rf "$(PKG_ROOT)/Library/AutoPkg/JSSImporter/"*
	rm $(CURDIR)/pkg/jssimporter/build/*.pkg
