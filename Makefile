include /usr/local/share/luggage/luggage.make

TITLE=jssimporter
REVERSE_DOMAIN=com.github.sheagcraig
PAYLOAD=\
		pack-Library-AutoPkg-autopkglib-JSSImporter \
		pack-Library-JSSImporter \

PACKAGE_VERSION=$(shell awk -F\" '/__version__ =/ { print $$2 }' JSSImporter.py)

pack-Library-AutoPkg-autopkglib-JSSImporter: l_Library
	@sudo mkdir -p ${WORK_D}/Library/AutoPkg/autopkglib
	@sudo ${INSTALL} -m 755 -g wheel -o root JSSImporter.py ${WORK_D}/Library/AutoPkg/autopkglib/

pack-Library-JSSImporter: l_Library
	@sudo mkdir -p ${WORK_D}/Library/Application\ Support/JSSImporter
	@sudo rm -rf jss/*.pyc
	@sudo rm -rf jss/contrib/*.pyc
	@sudo cp -R jss ${WORK_D}/Library/Application\ Support/JSSImporter

