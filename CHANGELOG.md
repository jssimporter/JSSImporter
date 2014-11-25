### 0.2.3 (UNRELEASED) The Thing You've All Been Waiting For

FIXES:

- Example template SmartGroupTemplate.xml had a mistake with the %JSS_INVENTORY_NAME% variable.

### 0.2.2 (October 8, 2014) Trotter Jelly

CHANGES:

- python-jss has been removed from this project to facilitate easier updating for me. See the README for information on obtaining it for development purposes.
- Added version number to ```JSSImporter.py``` to make it easier for developers to know what they have.
- Added instructions for overrides to README.

FIXES:

- python-jss' ```FileUpload``` ignored SSL verification preferences and thus would fail on disabled SSL for jss-autopkg-addon. This has been corrected.

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
