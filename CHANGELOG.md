### 0.2.0 (August 29, 2014) Popsicle Mayonnaise

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
