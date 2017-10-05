# JSSImporter Change Log

All notable changes to this project will be documented in this file. This project adheres to [Semantic Versioning](http://semver.org/).


## [Unreleased][unreleased]

### Changed
- Installation package Makefile is included in project repo.
- python-jss is now bundled with JSSImporter, and JSSImporter will use /Library/Application Support/JSSImporter/jss.
- Bundled python-jss is the 2.0.0 release, which overhauls a number of things including HTTP requests. JSSImporter has been updated to use the (very slightly-changed) API.
	- python-jss now uses curl unless python requests is available. This avoids the need for working around Apple's ancient python and OpenSSL situation.
- JSSImporter outputs its version and python-jss's version during a verbose run.
- Reordered code.
- Fixed some style issues.
- Fixed some lint issues.
- JSSImporter now looks for categories used in templates, and creates them if they don't exist. This solves #55 (involving scripts). It does create a precedence situation for one case: if you have a `policy_category` input variable set will always win; even if there's no category tag in the policy template, even if it's not the same as `policy_category`. This should not be an issue for anybody, however.
- `version` is no longer a required input variable. It will default to "0.0.0.0" when it's not present, and issue a warning in the output because this is probably not what you want. Solves #72.

### Added
- If a mountable distribution point is mounted prior to the JSSImporter run, JSSImporter won't unmount at the conclusion of the run (#100).
- You can now set a `policy_action_type` to set the `package_configuration` section of a Policy to `Cache` or `Install Cached` in addition to the default value of `Install`. (#75).
- New Package input variables allow you to specify the priority, restart, and boot drive after imaging requirements (#87 - Thanks @jusmig!)
- Ability to add `exclusion_groups` to the policy scope. This feature works exactly like the regular scoping groups. Thanks to @BadStreff for the contribution, #93.

### Fixed
- An underscore was added to the report header for `Extension_Attributes` so AutoPkgr doesn't freak out. Thanks @homebysix (#83).

## [0.5.1] - 2015-09-30 - I've Got a Bike, You Can Ride it if You Like

### Fixed
- Updates for use with python-jss 1.4.0
- Installs templates and temporary python-jss egg installer in /usr/local/share instead of /usr/share for El Capitan friendship. (#60)

### Added
- Adds a tiny bit of increased verbose reporting: As a package is copied to each repo, you should see a line in the output telling you which repo is being targeted.

## [0.5.0] - 2015-07-24 - Careful With That Axe, Eugene

### Fixed

- Package values `package_info`, `package_notes`, and `os_requirements` couldn't be enforced as blank. (Now they can.)

### Changed

- Requires python-jss 1.2.0 for compatibility with JSS 9.73.
- Adds arguments `package_info` and `package_notes`. Thanks to @quovadimus for the suggestion. (#41)
- `os_requirements` now defaults to "".
- Set `JSS_SUPPRESS_WARNINGS` to default to `True`.
- If you have no repos configured, JSSImporter will skip the package creation/upload/update process, and won't put a package into the install policy. Log message indicates that it is skipped in case this is an accident.

## [0.4.1] - 2015-06-25 - It's not a Tumor

### Fixed

- Fix file searching mistake with path generation using recipe filename.

## [0.4.0] - 2015-06-25 - Get to the Chopper

### Changed

- Any files referenced in a JSS Recipe will now be searched for in this order:
	1. Path as specified.
	2. The parent folder of the path.
	3. First ParentRecipe's folder.
	4. First ParentRecipe's parent folder.
	5. Second ParentRecipe's folder.
	6. Second ParentRecipe's parent folder.
	7. Nth ParentRecipe's folder.
	8. Nth ParentRecipe's parent folder.

	This search-path method is primarily in place to support using recipe
	overrides. It applies to policy_template, computer group templates,
	self_service_icon, script templates, and extension attribute templates. It
	allows users to avoid having to copy the file to the override directory for
	each recipe.
- Updates required python-jss to 1.0.2.

## [0.3.8] - 2015-04-03 - The Soft Bullet In

### Added

- Adds summary reporting to AutoPkg >= 0.4.3. Reports on all new or updated elements of a recipe.
	- Some object types always get updated (e.g. smart groups, policies) as you can't really determine whether they've changed. So JSSImporter enforces the recipe values.

### Changed

- ALL AutoPkg environment variable string values are now available for text replacement in your templates.
	- Use the environment variable name wrapped in %'s, e.g. , for AUTOPKG_VERSION, use `%AUTOPKG_VERSION%` in your template, and it will get substituted.
	- Non-string types (For example, PARENT_RECIPES) are not available.
	- Inject whatever you want by adding a key to your recipe input variables with a string value. See [the blog post on this](http://labs.da.org/wordpress/sheagcraig/2015/04/01/expanding-text-replacement-in-jssimporter/)
- Moves most of the output variables to be included under a single `jss_changed_objects` output variable. Values now are object names rather than a bool.


## [0.3.7] - 2015-03-17 - Dire Weasel

### Added

- Adds support for Sites.
	- See `PolicyTemplate.xml` and `SmartGroupTemplate.xml` for example of proper block to include.
	- Will do text replacement. Adds input variables:
		- `site_id`
		- `site_name`
		- You don't need both!
- Input variable validation for groups (#33)
	- Most recipes are written to scope a policy to a group. However, if you want to override that recipe to NOT scope, it fails, because there is still a groups input variable that just isn't getting text replacement.
	- Now, you can specify blank values in the override to skip group creation.
	- Groups with un-replaced text values (i.e. anything with `%` pre/postfix) will be skipped as well.
	- This validation could be added to other inputs (scripts, extension attributes, etc) if needed.

### Removed

- Extension Attribute input variable `name` is deprecated  and removed since it is redundent and can potentially clash with the name value in the Extension Attribute template (#26).
	- Existing recipes will safely work as long as the template has a `name`.


## [0.3.6] - 2015-01-29 - Cha-Cha-Cha-Chia!

### Added

- Adds support for JSSImporter to *not* upload a package. Useful for specifying multiple JSSImporter processors in a recipe to automate policy creation. (#22)
	- You need to specify `pkg_path` with a blank value for this to work!
- Gains support for migrated JSS' with AFP/SMB distribution points case. (#19)

### Changed

- Updates to python-jss 0.5.4
- Updates SmartGroupTemplate.xml and PolicyTemplate.xml to match what I have been using and recommending with my jss-recipes repo.


## [0.3.5] - 2014-12-09 - Hypercard

### Added

- Adds `JSS_SUPPRESS_WARNINGS` input variable to disable urllib3 warnings (probably because you are disabling JSS_VERIFY_SSL or using a wacky certificate). Use at your own risk! (#18)

### Changed

- Updates to python-jss 0.5.3
- I will now refer to this project as JSSImporter instead of jss-autopkg-addon.

### Fixed

- Non-flat packages would not upload to a JDS. There is also the possibility of them not working on SMB fileshares as reported by @mitchelsblake. Now, non-flat packages are zipped prior to upload for all DP types. (sheagcraig/python-jss#20)
- See [my blog](http://labs.da.org/wordpress/sheagcraig/2014/12/09/zipping-non-flat-packages-for-casper/) for further info on this.


## [0.3.4] - 2014-12-05 - Walrus Odor

### Changed

- Updates to python-jss 0.5.2

### Fixed

- JDS operations use the same session as "regular" API calls. This should honor the JSS_VERIFY_SSL setting now. (sheagcraig/python-jss#18)


## [0.3.3] - 2014-12-04 - Pickles

### Changed

- Updates to python-jss 0.5.1
- JDS repos now need only a single key: type=JDS.
- JSSImporter will let you know if a package was *not* uploaded.

### Fixed

- Scripts `name` in the recipe should be the basename for `exists` purposes.
- Scripts could not be uploaded a second time due to name error. Closely related to above.
- Solves #9 for real.


## [0.3.2] - 2014-12-03 - Terminator X

### Fixed

- Should solve #9 with update to requests 2.5. Thanks to @ocoda for figuring this out.
- Installer package should now use an _unzipped_ python-jss egg. Solves issue with missing certs.pem file #14.

### Changed

- Updates requirement to python-jss 0.4.4 (included in package installer).


## [0.3.1] - 2014-12-02 - All of Your JDS are Belong to Us

### Fixed

- Thanks to @beckf for sorting out the JDS upload issues. JDS restrictions have been removed from jss-autopkg-addon. Go for it!
- Requires python-jss 0.4.3

### Changed

- Deprecated `JSS_REPO` key has been removed (Don't worry: `JSS_REPOS` still in!) All code referencing it has been removed.


## [0.3.0] - 2014-11-25 - The Thing You've All Been Waiting For

### Added

- Added several output variables.

### Fixed

- Example template SmartGroupTemplate.xml had a mistake with the %JSS_INVENTORY_NAME% variable.
- Fixed incorrect documentation for `JSS_REPOS` input variable

### Changed

- Marked `JSS_REPO` input variable as deprecated.
- Requires python-jss 0.4.2
	- This adds support for JDS distribution points.
- Input variable help mentions the change from categories of "Unknown" to "No Category Assigned".
- Reorganized package handling to manage JDS distribution points.

### Removed

- Removed all use of the value "*LEAVE_OUT*" from processor. (Previously used to skip a section).
	- See README for information on individual elements of the processor. In general, leaving a key out entirely, or providing a blank value will skip that section.

### Known issues

- python-jss now supports JDS distribution points. However, packages and scripts are corrupted on upload, and thus, you really should only use this for testing. We are working hard to solve this problem as soon as possible. Please see python-jss Issue [https://github.com/sheagcraig/python-jss/issues/5] for more information.


## [0.2.2] - 2015-04-03 - Trotter Jelly

### Added

- Added version number to `JSSImporter.py` to make it easier for developers to know what they have.
- Added instructions for overrides to README.

### Fixed

- python-jss' `FileUpload` ignored SSL verification preferences and thus would fail on disabled SSL for jss-autopkg-addon. This has been corrected.

### Removed

- python-jss has been removed from this project to facilitate easier updating for me. See the README for information on obtaining it for development purposes.


## [0.2.1] - 2015-04-03 - Sardine Taco Sauce

### Fixed

- Fixed icon handling code dropping path from filename. (Thanks Elliot Jordan for the spot!)


## [0.2.0] - 2015-04-03 - Popsicle Mayonnaise

### Added

- Add key `JSS_REPOS` (plural). Allows configuration of and distribution to all distribution points. See the README for details.
	- Mounts and unmounts distribution points for you. If DP is already mounted with a different mount point then JSSImporter expects, it may fail, so make sure Casper Admin is NOT open.
- Add key `JSS_SSL_VERIFY` which defaults to True. Override with False if you have a self-signed certificate that is causing you grief, or other SSL problems. See the README for details on dependencies for SSL/SNI.
- Add key `self_service_description` to allow variable substitution for Self Service descriptions in policy templates.
- Add key `self_service_icon` to allow uploading and associating an icon with the self service item.

### Changed

- Update PolicyTemplate.xml to demonstrate further Self Service customization.
- Categories default to "Unknown", which is the JSS' behavior anyway.

### Removed

- Deprecated `JSS_REPO` key. It will still work, but the processor prioritizes `JSS_REPOS` over it.


[unreleased]: https://github.com/sheagcraig/JSSImporter/compare/v0.5.1...HEAD
[0.5.1]: https://github.com/sheagcraig/JSSImporter/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/sheagcraig/JSSImporter/compare/v0.4.1...v0.5.0
[0.4.1]: https://github.com/sheagcraig/JSSImporter/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/sheagcraig/JSSImporter/compare/v0.3.8...v0.4.0
[0.3.8]: https://github.com/sheagcraig/JSSImporter/compare/v0.3.7...v0.3.8
[0.3.7]: https://github.com/sheagcraig/JSSImporter/compare/v0.3.6...v0.3.7
[0.3.6]: https://github.com/sheagcraig/JSSImporter/compare/v0.3.5...v0.3.6
[0.3.5]: https://github.com/sheagcraig/JSSImporter/compare/v0.3.4...v0.3.5
[0.3.4]: https://github.com/sheagcraig/JSSImporter/compare/v0.3.3...v0.3.4
[0.3.3]: https://github.com/sheagcraig/JSSImporter/compare/v0.3.2...v0.3.3
[0.3.2]: https://github.com/sheagcraig/JSSImporter/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/sheagcraig/JSSImporter/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/sheagcraig/JSSImporter/compare/v0.2.2...v0.3.0
[0.2.2]: https://github.com/sheagcraig/JSSImporter/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/sheagcraig/JSSImporter/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/sheagcraig/JSSImporter/compare/v0.1.0...v0.2.0
