# JSSImporter Change Log

All notable changes to this project will be documented in this file. This project adheres to [Semantic Versioning](http://semver.org/).

## Known issues in latest version

-   `JCDS` mode does not currently work and will cause a recipe to fail if configured. JCDS users should use the `CDP` mode.
-   Efforts continue to be made to reduce intermittent failures of upload of packages to Jamf Cloud Distribution Points and CDPs, icons or other objects, but they may still occur. We believe this is due to the clustering involved with Jamf Cloud Distribution Points. See (#81), (#119), (#145) etc. Ultimately, we need Jamf to provide proper endpoints for package uploads and managing icons. Please bug your Jamf support and sales consultants as often as possible! Note an attempt to fix this is made in python-jss v2.1.1 which is incorporated into the package of JSSImporter v1.1.3.
-   The above efforts to improve package upload reliability may conversely cause problems on setups with multiple DPs of different types. Scenarios involving Cloud plus Local DPs are not yet tested, and there probably needs to be a more intelligent method of treating each DP as a separate package upload process than currently exists.

## [unreleased]

Changes since last release.

## [1.1.6] - 2022-01-26

Removed deprecated `boot_volume_required` key from `packages` endpoint.

## [1.1.5] - 2021-05-25

No changes to JSSImporter, but the package re-incorporates upstream changes to python-jss that were temporarily put in 1.1.2 but inadvertently removed again in 1.1.4 (because those changes were meant to be temporary and so were not in the `master` branch).

## [1.1.4] - 2021-03-26

No changes to JSSImporter, but the package incorporates upstream changes to python-jss to mount shares at /Users/Shared instead of /Volumes.

## [1.1.3] - 2020-10-19

No changes to JSSImporter, but the package incorporates upstream changes to python-jss to set a session cookie which should ensure each request goes to the same cluster node.

## [1.1.2] - 2020-09-02

This is a bugfix release which addresses #184, where `STOP_IF_NO_JSS_UPLOAD` was not being handled properly when set to `False`.

The `Makefile` now uses `/usr/local/autopkg/python` when compiling the `pip` requirements rather than `pip3` to ensure compatibility with the version of python included with AutoPkg.

## [1.1.1] - 2020-07-01

This is a bugfix release which addresses #176, #182 and #183, improving the language of the output when there is either no `JSS_REPO` set, no `pkg_path`, or `STOP_IF_NO_JSS_UPLOAD` is not set to `False`. I have also removed some verbosity when running in `-v` or zero verbosity mode. Run with at least `-vv` to retain all previous output. There are also a million minor python format changes due to the use of `black` when saving the file.

The package installer incorporates a [fix in python-jss](https://github.com/jssimporter/python-jss/pull/98).

## [1.1.0] - 2020-01-20

### Added in 1.1.0

-   Retained compatibility with AutoPkg 1.x (Python 2) while adding compatibility for AutoPkg 2.x (Python 3).
-   **Moved supporting files from `/Library/Application Support/JSSImporter` to `/Library/AutoPkg/JSSImporter`.**

## [1.0.3] - 2019-10-04

This is a bugfix release to address Issue #165 - local distribution points failing to upload new packages due to failing to obtain a package ID. The package ID check has been removed from local DPs, but left for cloud DPs. Tested and now working on JCDS and SMB DPs.

## [1.0.2] - 2019-09-25

This is the official 1.0.2 release, exactly the same as the former 1.0.2b8.

-   @grahamrpugh added a new `wait_for_id` definition, which provides a common method to check for feedback on the upload of each API object, in an attempt to reduce the chance of cloud clusters returning conflicting information about whether an object has been successfully uploaded or not.
-   Verbosity is increased with respect to reporting object IDs.
-   References to JSS are changed to "Jamf Pro Server"... except in the name `JSSImporter` of course! I think we're stuck with that one.
-   @grahamrpugh added a `do_update` feature to prevent overwriting a computer group if it already exists on the server, while continuing to create the group if it is not there.
-   @nstrauss added a `skip_scope` feature to allow the upload of a policy without changing any existing scope.
-   @nstrauss added a `skip_scripts` feature to allow the upload of a policy without changing any existing script objects in the script.
-   @grahamrpugh added a feature that prevents policies from being overwritten if there is no new package to upload, called `STOP_IF_NO_JSS_UPLOAD`. It is enabled by default. To override this behaviour and force the processor to continue and overwrite policies etc., run your autopkg recipe with the `--key STOP_IF_NO_JSS_UPLOAD=False` parameter.
-   @grahamrpugh contributed (#135) which prevents uploaded scripts from having certain special characters incorrectly escaped, namely `>`, `<` and `&`.

### Fixed in 1.0.2

-   Fixed a bug that prevented Types `AFP` and `SMB` from being accepted (was introduced in 1.0.2b5).
-   Fixed a bug that was introduced in 1.0.2b5 which prevented certain packages from uploading (relevant to #162).
-   Changed the order of the code which waits for the creation of a package id, and added a wait for the creation of a category id, to fix problems with package objects not yet existing when uploading a package.
-   Updated the embedded python-jss, which fixes a `urllib` problem when running in python2 (#151)

## [1.0.2b2] - 2018-09-22 - Bundled Dependency Testing

This release bundles dependencies to allow us to use requests again.
It also pulls in the boto library for connection to AWS S3 directly in future.
It supports a new Distribution Point Type, `JCDS`, for direct upload to JCDS. The `CDP` type will always remain for backwards compatibility.

### Changed in 1.0.2b2

-   Added updated python-jss (2.0.1) to fix issues with CDP/JCDS uploads.
-   Use `zipfile` module instead of `shutil` for archive creation to allow larger files. (Thanks @grahamrpugh)

### Fixed in 1.0.2b2

-   @mosen contributed (#125) a fix for an oversight where `jss_package_added` was never getting populated, which prevented packages from uploading.

## [1.0.0] - 2017-12-02 - Hammer Pants

This release changes a lot about how JSSImporter is packaged and delivered to users, largely in response to the changes in the Python (or lack thereof) that Apple ships with macOS. Please read the changes below very carefully prior to updating, as there may be some surprises that you were not expecting otherwise.

The brief form is that the JSSImporter package now installs the actual processor into your autopkglib, _and_ it will create a `/Library/Application Support/JSSImporter` folder and drop a copy of python-jss there. This python-jss is bundled into the package, so there won't be any pip updates or anything. What's bundled with JSSImporter is what you get. Also, JSSImporter will prioritize using that python-jss over any others.

JSSImporter, and really python-jss now uses the system `curl` to do all requests, so all SSL issues can be compared directly to normal `curl` requests.

### Changed in 1.0.0

-   JSSImporter and JSS now support version 9 and newer of the JSS.
-   Installation package Makefile is included in project repo.
-   python-jss is now bundled with JSSImporter, and JSSImporter will use /Library/Application Support/JSSImporter/jss.
-   Bundled python-jss is the 2.0.0 release, which overhauls a number of things including HTTP requests. JSSImporter has been updated to use the (very slightly-changed) API. - python-jss now uses curl unless python requests is available. This avoids the need for working around Apple's ancient python and OpenSSL situation.
-   JSSImporter outputs its version, python-jss's version, and the JSS's version, during a verbose run.
-   Reordered code.
-   Fixed some style issues.
-   Fixed some lint issues.
-   JSSImporter now looks for categories used in templates, and creates them if they don't exist. This solves #55 (involving scripts). It does create a precedence situation for one case: if you have a `policy_category` input variable set will always win; even if there's no category tag in the policy template, even if it's not the same as `policy_category`. This should not be an issue for anybody, however.
-   `version` is no longer a required input variable. It will default to "0.0.0.0" when it's not present, and issue a warning in the output because this is probably not what you want. (Solves #72).
-   JSSImporter won't mount any of your configured distribution points if your `pkg_path` is empty (falsy). (#104).

### Added in 1.0.0

-   If a mountable distribution point is mounted prior to the JSSImporter run, JSSImporter won't unmount at the conclusion of the run (#100).
-   You can now set a `policy_action_type` to set the `package_configuration` section of a Policy to `Cache` or `Install Cached` in addition to the default value of `Install`. (#75).
-   New Package input variables allow you to specify the priority, restart, and boot drive after imaging requirements (#87 - Thanks @jusmig!)
-   Ability to add `exclusion_groups` to the policy scope. This feature works exactly like the regular scoping groups. Thanks to @BadStreff for the contribution, #93. Issue #92.
-   Added `Name` and `Version` to the AutoPkg summary. Thanks for the contribution @ChrOst (#71).
-   JSSImporter will warn you that no distribution points are configured (and python-jss will fail if you configure a DP that doesn't configure correctly). (#85).
-   JSSImporter will enable python-jss's verbose output when AutoPkg has a verbosity of 4 or more (i.e. `autopkg run -vvvv yo.jss`.

### Fixed in 1.0.0

-   An underscore was added to the report header for `Extension_Attributes` so AutoPkgr doesn't freak out. Thanks @homebysix (#83).
-   JSSImporter now takes scripts, reads them in, escapes them for XML, and adds them to the script object's `script_contents` tag and does not try to copy them ever. This was needed in the past, but now presumably all JSS have been "migrated" and need the script in the DB rather than on disk. (#116).

### Removed from 1.0.0

-   The `JSS_MIGRATED` preference has been removed. If you have it in your config, it will be ignored, but there is no need for this with version 9+ of the JSS. (#118).

## [0.5.1] - 2015-09-30 - I've Got a Bike, You Can Ride it if You Like

### Fixed in 0.5.1

-   Updates for use with python-jss 1.4.0
-   Installs templates and temporary python-jss egg installer in /usr/local/share instead of /usr/share for El Capitan friendship. (#60)

### Added in 0.5.1

-   Adds a tiny bit of increased verbose reporting: As a package is copied to each repo, you should see a line in the output telling you which repo is being targeted.

## [0.5.0] - 2015-07-24 - Careful With That Axe, Eugene

### Fixed in 0.5.0

-   Package values `package_info`, `package_notes`, and `os_requirements` couldn't be enforced as blank. (Now they can.)

### Changed in 0.5.0

-   Requires python-jss 1.2.0 for compatibility with JSS 9.73.
-   Adds arguments `package_info` and `package_notes`. Thanks to @quovadimus for the suggestion. (#41)
-   `os_requirements` now defaults to "".
-   Set `JSS_SUPPRESS_WARNINGS` to default to `True`.
-   If you have no repos configured, JSSImporter will skip the package creation/upload/update process, and won't put a package into the install policy. Log message indicates that it is skipped in case this is an accident.

## [0.4.1] - 2015-06-25 - It's not a Tumor

### Fixed in 0.4.1

-   Fix file searching mistake with path generation using recipe filename.

## [0.4.0] - 2015-06-25 - Get to the Chopper

### Changed in 0.4.0

-   Any files referenced in a JSS Recipe will now be searched for in this order: 1. Path as specified. 2. The parent folder of the path. 3. First ParentRecipe's folder. 4. First ParentRecipe's parent folder. 5. Second ParentRecipe's folder. 6. Second ParentRecipe's parent folder. 7. Nth ParentRecipe's folder. 8. Nth ParentRecipe's parent folder.

This search-path method is primarily in place to support using recipe
overrides. It applies to policy_template, computer group templates,
self_service_icon, script templates, and extension attribute templates. It
allows users to avoid having to copy the file to the override directory for
each recipe.

-   Updates required python-jss to 1.0.2.

## [0.3.8] - 2015-04-03 - The Soft Bullet In

### Added in 0.3.8

-   Adds summary reporting to AutoPkg >= 0.4.3. Reports on all new or updated elements of a recipe. - Some object types always get updated (e.g. smart groups, policies) as you can't really determine whether they've changed. So JSSImporter enforces the recipe values.

### Changed in 0.3.8

-   ALL AutoPkg environment variable string values are now available for text replacement in your templates. - Use the environment variable name wrapped in %'s, e.g. , for AUTOPKG_VERSION, use `%AUTOPKG_VERSION%` in your template, and it will get substituted. - Non-string types (For example, PARENT_RECIPES) are not available. - Inject whatever you want by adding a key to your recipe input variables with a string value. See [the blog post on this](http://labs.da.org/wordpress/sheagcraig/2015/04/01/expanding-text-replacement-in-jssimporter/)
-   Moves most of the output variables to be included under a single `jss_changed_objects` output variable. Values now are object names rather than a bool.

## [0.3.7] - 2015-03-17 - Dire Weasel

### Added in 0.3.7

-   Adds support for Sites. - See `PolicyTemplate.xml` and `SmartGroupTemplate.xml` for example of proper block to include. - Will do text replacement. Adds input variables: - `site_id` - `site_name` - You don't need both!
-   Input variable validation for groups (#33) - Most recipes are written to scope a policy to a group. However, if you want to override that recipe to NOT scope, it fails, because there is still a groups input variable that just isn't getting text replacement. - Now, you can specify blank values in the override to skip group creation. - Groups with un-replaced text values (i.e. anything with `%` pre/postfix) will be skipped as well. - This validation could be added to other inputs (scripts, extension attributes, etc) if needed.

### Removed from 0.3.7

-   Extension Attribute input variable `name` is deprecated and removed since it is redundent and can potentially clash with the name value in the Extension Attribute template (#26). - Existing recipes will safely work as long as the template has a `name`.

## [0.3.6] - 2015-01-29 - Cha-Cha-Cha-Chia

### Added in 0.3.6

-   Adds support for JSSImporter to _not_ upload a package. Useful for specifying multiple JSSImporter processors in a recipe to automate policy creation. (#22) - You need to specify `pkg_path` with a blank value for this to work!
-   Gains support for migrated JSS' with AFP/SMB distribution points case. (#19)

### Changed in 0.3.6

-   Updates to python-jss 0.5.4
-   Updates SmartGroupTemplate.xml and PolicyTemplate.xml to match what I have been using and recommending with my jss-recipes repo.

## [0.3.5] - 2014-12-09 - Hypercard

### Added in 0.3.5

-   Adds `JSS_SUPPRESS_WARNINGS` input variable to disable urllib3 warnings (probably because you are disabling JSS_VERIFY_SSL or using a wacky certificate). Use at your own risk! (#18)

### Changed in 0.3.5

-   Updates to python-jss 0.5.3
-   I will now refer to this project as JSSImporter instead of jss-autopkg-addon.

### Fixed in 0.3.5

-   Non-flat packages would not upload to a JDS. There is also the possibility of them not working on SMB fileshares as reported by @mitchelsblake. Now, non-flat packages are zipped prior to upload for all DP types. (sheagcraig/python-jss#20)
-   See [my blog](http://labs.da.org/wordpress/sheagcraig/2014/12/09/zipping-non-flat-packages-for-casper/) for further info on this.

## [0.3.4] - 2014-12-05 - Walrus Odor

### Changed in 0.3.4

-   Updates to python-jss 0.5.2

### Fixed in 0.3.4

-   JDS operations use the same session as "regular" API calls. This should honor the JSS_VERIFY_SSL setting now. (sheagcraig/python-jss#18)

## [0.3.3] - 2014-12-04 - Pickles

### Changed in 0.3.3

-   Updates to python-jss 0.5.1
-   JDS repos now need only a single key: type=JDS.
-   JSSImporter will let you know if a package was _not_ uploaded.

### Fixed in 0.3.3

-   Scripts `name` in the recipe should be the basename for `exists` purposes.
-   Scripts could not be uploaded a second time due to name error. Closely related to above.
-   Solves #9 for real.

## [0.3.2] - 2014-12-03 - Terminator X

### Fixed in 0.3.2

-   Should solve #9 with update to requests 2.5. Thanks to @ocoda for figuring this out.
-   Installer package should now use an _unzipped_ python-jss egg. Solves issue with missing certs.pem file #14.

### Changed in 0.3.2

-   Updates requirement to python-jss 0.4.4 (included in package installer).

## [0.3.1] - 2014-12-02 - All of Your JDS are Belong to Us

### Fixed in 0.3.1

-   Thanks to @beckf for sorting out the JDS upload issues. JDS restrictions have been removed from jss-autopkg-addon. Go for it!
-   Requires python-jss 0.4.3

### Changed in 0.3.1

-   Deprecated `JSS_REPO` key has been removed (Don't worry: `JSS_REPOS` still in!) All code referencing it has been removed.

## [0.3.0] - 2014-11-25 - The Thing You've All Been Waiting For

### Added in 0.3.0

-   Added several output variables.

### Fixed in 0.3.0

-   Example template SmartGroupTemplate.xml had a mistake with the %JSS_INVENTORY_NAME% variable.
-   Fixed incorrect documentation for `JSS_REPOS` input variable

### Changed in 0.3.0

-   Marked `JSS_REPO` input variable as deprecated.
-   Requires python-jss 0.4.2 - This adds support for JDS distribution points.
-   Input variable help mentions the change from categories of "Unknown" to "No Category Assigned".
-   Reorganized package handling to manage JDS distribution points.

### Removed from 0.3.0

-   Removed all use of the value "_LEAVE_OUT_" from processor. (Previously used to skip a section). - See README for information on individual elements of the processor. In general, leaving a key out entirely, or providing a blank value will skip that section.

### Known issues in 0.3.0

-   python-jss now supports JDS distribution points. However, packages and scripts are corrupted on upload, and thus, you really should only use this for testing. We are working hard to solve this problem as soon as possible. Please see python-jss Issue [https://github.com/sheagcraig/python-jss/issues/5] for more information.

## [0.2.2] - 2015-04-03 - Trotter Jelly

### Added in 0.2.2

-   Added version number to `JSSImporter.py` to make it easier for developers to know what they have.
-   Added instructions for overrides to README.

### Fixed in 0.2.2

-   python-jss' `FileUpload` ignored SSL verification preferences and thus would fail on disabled SSL for jss-autopkg-addon. This has been corrected.

### Removed from 0.2.2

-   python-jss has been removed from this project to facilitate easier updating for me. See the README for information on obtaining it for development purposes.

## [0.2.1] - 2015-04-03 - Sardine Taco Sauce

### Fixed in 0.2.1

-   Fixed icon handling code dropping path from filename. (Thanks Elliot Jordan for the spot!)

## [0.2.0] - 2015-04-03 - Popsicle Mayonnaise

### Added in 0.2.0

-   Add key `JSS_REPOS` (plural). Allows configuration of and distribution to all distribution points. See the README for details. - Mounts and unmounts distribution points for you. If DP is already mounted with a different mount point then JSSImporter expects, it may fail, so make sure Casper Admin is NOT open.
-   Add key `JSS_SSL_VERIFY` which defaults to True. Override with False if you have a self-signed certificate that is causing you grief, or other SSL problems. See the README for details on dependencies for SSL/SNI.
-   Add key `self_service_description` to allow variable substitution for Self Service descriptions in policy templates.
-   Add key `self_service_icon` to allow uploading and associating an icon with the self service item.

### Changed in 0.2.0

-   Update PolicyTemplate.xml to demonstrate further Self Service customization.
-   Categories default to "Unknown", which is the JSS' behavior anyway.

### Removed from 0.2.0

-   Deprecated `JSS_REPO` key. It will still work, but the processor prioritizes `JSS_REPOS` over it.

[unreleased]: https://github.com/sheagcraig/JSSImporter/compare/v1.1.5...HEAD
[1.1.5]: https://github.com/sheagcraig/JSSImporter/compare/v1.1.4...v1.1.5
[1.1.4]: https://github.com/sheagcraig/JSSImporter/compare/v1.1.3...v1.1.4
[1.1.3]: https://github.com/sheagcraig/JSSImporter/compare/v1.1.2...v1.1.3
[1.1.2]: https://github.com/sheagcraig/JSSImporter/compare/v1.1.2...v1.1.2
[1.1.1]: https://github.com/sheagcraig/JSSImporter/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/sheagcraig/JSSImporter/compare/v1.0.3...v1.1.0
[1.0.3]: https://github.com/sheagcraig/JSSImporter/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/sheagcraig/JSSImporter/compare/1.0.2b2...v1.0.2
[1.0.2b2]: https://github.com/sheagcraig/JSSImporter/compare/v1.0.0...1.0.2b2
[1.0.0]: https://github.com/sheagcraig/JSSImporter/compare/v0.5.1...v1.0.0
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
