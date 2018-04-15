CURDIR := $(shell pwd)
MUNKIPKG := /usr/local/bin/munkipkg
PKG_ROOT := $(CURDIR)/pkg/jssimporter/payload
PKG_BUILD := $(CURDIR)/pkg/jssimporter/build
VERSION := $(shell defaults read $(CURDIR)/pkg/jssimporter/build-info.plist version)

objects = $(PKG_ROOT)/Library/Application\ Support/JSSImporter/requests \
	$(PKG_ROOT)/Library/Application\ Support/JSSImporter/boto \
	$(PKG_ROOT)/Library/AutoPkg/autopkglib/JSSImporter.py


default : $(PKG_BUILD)/jssimporter-$(VERSION).pkg


$(PKG_BUILD)/jssimporter-$(VERSION).pkg: $(objects)
	cd $(CURDIR)/pkg && $(MUNKIPKG) jssimporter


$(PKG_ROOT)/Library/Application\ Support/JSSImporter/boto:
	echo "Installing boto into JSSImporter support directory"
	#pip install --install-option="--prefix=$(PKG_ROOT)/Library/Application Support/JSSImporter/boto" --ignore-installed boto
	pip install --target "$(PKG_ROOT)/Library/Application Support/JSSImporter" --ignore-installed boto


$(PKG_ROOT)/Library/Application\ Support/JSSImporter/requests:
	echo "Installing requests into JSSImporter support directory"
	#pip install --install-option="--prefix=$(PKG_ROOT)/Library/Application Support/JSSImporter/requests" --ignore-installed requests
	pip install --target "$(PKG_ROOT)/Library/Application Support/JSSImporter" --ignore-installed requests


$(PKG_ROOT)/Library/AutoPkg/autopkglib/JSSImporter.py:
	echo "Copying JSSImporter.py into autopkglib"
	cp $(CURDIR)/JSSImporter.py $(PKG_ROOT)/Library/AutoPkg/autopkglib/JSSImporter.py


.PHONY : clean
clean :
	echo "Cleaning up package root"
	rm $(PKG_ROOT)/Library/AutoPkg/autopkglib/JSSImporter.py
	rm -rf "$(PKG_ROOT)/Library/Application Support/JSSImporter/boto"
	rm -rf "$(PKG_ROOT)/Library/Application Support/JSSImporter/requests"
	rm $(CURDIR)/pkg/jssimporter/build/*.pkg
