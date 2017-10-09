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

pack-Library-JSSImporter: l_Library clean_jss
	@sudo mkdir -p ${WORK_D}/Library/Application\ Support/JSSImporter
	@sudo cp -R jss ${WORK_D}/Library/Application\ Support/JSSImporter

clean_jss:
	find jss -name '*.pyc' -exec rm -f {} \;
	find jss -name '*.swp' -exec rm -f {} \;
	echo 'Do a double-check to make sure there are no old bytecode files in the package! The luggage seems to want to include them if they are in the cache.'
