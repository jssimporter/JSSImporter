### 0.2.2 (October 7, 2014) Trotter Jelly

CHANGES:

- python-jss is now a git submodule. If you clone this repo to develop on it, please remember to ```git submodule init; git submodule update``` if you need the python-jss code included with jss-autopkg-addon. This will make updating and tracking python-jss a lot easier for me.

### 0.2.1 (October 2, 2014) Sardine Taco Sauce

FIXES:

- Fixed icon handling code dropping path from filename. (Thanks Elliot Jordan for the spot!)

### 0.2.0 (September 4, 2014) Popsicle Mayonnaise

ADDITIONS:

- Add key ```JSS_REPOS``` (plural). Allows configuration of and distribution to all distribution points. See the README for details.
	- Mounts and unmounts distribution points for you. If DP is already mounted with a different mount point then JSSImporter expects, it may fail, so make sure Casper Admin is NOT open.
- Add key ```JSS_SSL_VERIFY``` which defaults to True. Override with False if you have a self-signed certificate that is causing you grief, or other SSL problems. See the README for details on dependencies for SSL/SNI.
- Add key ```self_service_description``` to allow variable substitution for Self Service descriptions in policy templates.
- Add key ```self_service_icon``` to allow uploading and associating an icon with the self service item.

CHANGES:

- Deprecated ```JSS_REPO``` key. It will still work, but the processor prioritizes ```JSS_REPOS``` over it.
- Update PolicyTemplate.xml to demonstrate further Self Service customization.
- Categories default to "Unknown", which is the JSS' behavior anyway.
