### 0.3.5 (UNRELEASED) Hypercard

CHANGES:

- Updates to python-jss 0.5.3
- Adds ```JSS_SUPPRESS_WARNINGS``` input variable to disable urllib3 warnings (probably because you are disabling JSS_VERIFY_SSL or using a wacky certificate). Use at your own risk!

FIXES:

- Non-flat packages would not upload to a JDS. There is also the possibility of them not working on SMB fileshares as reported by @mitchelsblake. Now, non-flat packages are zipped prior to upload for all DP types. (sheagcraig/python-jss#20)
- See [my blog](http://labs.da.org/wordpress/sheagcraig/2014/12/09/zipping-non-flat-packages-for-casper/) for further info on this.

### 0.3.4 (December 5, 2014) Walrus Odor

CHANGES:

- Updates to python-jss 0.5.2

FIXES:

- JDS operations use the same session as "regular" API calls. This should honor the JSS_VERIFY_SSL setting now. (sheagcraig/python-jss#18)

### 0.3.3 (December 4, 2014) Pickles

CHANGES:

- Updates to python-jss 0.5.1
- JDS repos now need only a single key: type=JDS.
- JSSImporter will let you know if a package was *not* uploaded.

FIXES:

- Scripts ```name``` in the recipe should be the basename for ```exists``` purposes.
- Scripts could not be uploaded a second time due to name error. Closely related to above.
- Solves #9 for real.

### 0.3.2 (December 3, 2014) Terminator X

FIXES:

- Should solve #9 with update to requests 2.5. Thanks to @ocoda for figuring this out.
- Installer package should now use an _unzipped_ python-jss egg. Solves issue with missing certs.pem file #14.

CHANGES:

- Updates requirement to python-jss 0.4.4 (included in package installer).

### 0.3.1 (December 2, 2014) All of Your JDS are Belong to Us

FIXES:

- Thanks to @beckf for sorting out the JDS upload issues. JDS restrictions have been removed from jss-autopkg-addon. Go for it!
- Requires python-jss 0.4.3

CHANGES:

- Deprecated ```JSS_REPO``` key has been removed (Don't worry: ```JSS_REPOS``` still in!) All code referencing it has been removed.

### 0.3.0 (November 25, 2014) The Thing You've All Been Waiting For

FIXES:

- Example template SmartGroupTemplate.xml had a mistake with the %JSS_INVENTORY_NAME% variable.
- Fixed incorrect documentation for ```JSS_REPOS``` input variable

CHANGES:

- Marked ```JSS_REPO``` input variable as deprecated.
- Requires python-jss 0.4.2
	- This adds support for JDS distribution points.
- Added several output variables.
- Input variable help mentions the change from categories of "Unknown" to "No Category Assigned".
- Removed all use of the value "*LEAVE_OUT*" from processor. (Previously used to skip a section).
	- See README for information on individual elements of the processor. In general, leaving a key out entirely, or providing a blank value will skip that section.
- Reorganized package handling to manage JDS distribution points.

KNOWN ISSUES:

- python-jss now supports JDS distribution points. However, packages and scripts are corrupted on upload, and thus, you really should only use this for testing. We are working hard to solve this problem as soon as possible. Please see python-jss Issue [https://github.com/sheagcraig/python-jss/issues/5] for more information.

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
