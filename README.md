This processor adds the ability for AutoPkg to create groups, upload packages and scripts, add extension attributes, and create policies for the Casper JSS, allowing you to fully-automate your software *testing* workflow. 

This project began from Allister Banks' original [jss-autopkg-addon project](https://github.com/arubdesu/jss-autopkg-addon), but has since diverged ~~considerably~~ completely to add greater customization options while maintaining the existing functionality.

# Getting Started
Getting your software testing workflow constructed using AutoPkg and JSSImporter can be daunting. This document will go over the various configuration and usage information you will need for success. There are, however, numerous helpful resources in the Macadmin community for best-practices in setting this up. A quick glance through previous years' session videos from any of the Mac Admin conferences (I attend Penn State MacAdmins most years, see what they have: [https://www.youtube.com/user/psumacconf]

While JSSImporter has a lot of options for crafting the workflow best-suited for your organization's needs, there are best-practices expressed in the [AutoPkg organization's jss-recipes repo](https://github.com/autopkg/jss-recipes) that drive the design of JSSImporter.

The workflow used in the AutoPkg org's jss-recipes repo goes something like this:

JSS recipes use recipes that produce standard Apple package (pkg) files as parents. This ensures that a pkg can be uploaded to the distribution points.
The resulting package file's name includes the software's name and version number (e.g. Firefox-38.0.5.pkg).
The package file's metadata includes any OS version restrictions that govern that product's installation.
The JSS recipe specifies the category for the package file itself, which is chosen from among a limited set of approved categories. (See the list of categories in the Style guide below.) If the category doesn't exist, it will be created.
JSSImporter uploads the package file to all configured distribution points.
The SmartGroupTemplate.xml file tells JSSImporter to create or update a smart group called [SoftwareName]-update-smart. The criteria of this group are:
- the computer has the software in question installed
- the version does not match the newest version that AutoPkg found
- the computer is a member of a group called "Testing" (which is created and maintained manually by the Jamf admin)
The PolicyTemplate.xml file tells JSSImporter to create a single Self Service policy for each product, called Install Latest [SoftwareName]. The policy:
- installs the latest package file.
- is scoped to the smart group mentioned above.
- includes a Self Service icon and description.
- category is Testing. This groups policies together under the Testing category on the Policies page of the JSS web interface to separate and distinguish them from other policies. If the Testing category doesn't exist, it will be created.
- has an execution frequency of "Ongoing" to allow multiple runs should tests fail. However, following a successful installation, the Self Service policy performs a recon run, which will drop the computer out of the smart group, thus preventing further executions until the next update is made available. This also enables reuse of the same policy without needing to "Flush All" the policy logs.

No groups other than the smart group mentioned above are created or modified.

In the rare case of needing an extension attribute to determine whether a package is out-of-date, and thus used to determine membership in the smart group, extension attributes will be created and/or updated. A separate [SoftwareName]ExtensionAttribute.xml file is required for this. This is most commonly the case with apps that either don't live in /Applications or report different version numbers for CFBundleShortVersionString and CFBundleVersion (Jamf only uses CFBundleShortVersionString for inventory).

One piece of advice: The [AutoPkg organization's jss-recipes repo](https://github.com/autopkg/jss-recipes) is a community project which adheres to the best-practices generally agreed upon by the community. If you are trying to do something beyond what these recipes or processor cover, you may need to step back and re-evaluate your goals. JSSImporter's goal is to allow you to, with AutoPkg, automate the drudgery of managing a *testing* workflow. It is not meant to deploy software straight to production machines. It is not meant as a way to bootstrap all of a JSS's policies. There is a lot you can do with the Jamf PRO API, and JSSImporter's code is an illustration of how to go about doing this. If JSSImporter and the jss-recipes still don't meet your needs, you have a couple of options. You can write your own jss-recipes. This usually involves establishing your own workflow, and writing the templates to support that. Implementing idividual recipes becomes largely editing a handful of values in copies of these templates, 90% of which end up being the same.

Hint: many people have expressed a desire for JSSImporter to upload objects to multiple JSSs. The trick to doing this is to use your own jss recipes that have one JSSImporter processor for each JSS. You will need to override the `JSS_URL` and any other settings needed in-between JSSImporter invocations in the recipe.

If this still does not meet your needs, it's time to dig into python-jss and write a solution that does.

## Installation
To install, download the latest package installer from the "releases" section. This will add the JSSImporter.py processor to your autopkglib folder, and the python-jss package to `/Library/Application Support/JSSImporter`.

Note: This installation strategy is a change from past JSSImporter versions. See below if you're interested in how.

## Setup
Prior to using the JSSImporter, You will need to add some preferences to your AutoPkg preferences file:
- The URL to your jss
- The username and password of an API privileged user. If you haven't done so already, you'll need to create a service account for JSSImporter to interact with the API as.
	- It is recommended to create a user named something like "AutoPkg". It will need Create, Read, and Update privileges on:
		- Categories
		- Computer Extension Attributes
		- Computer Groups
		- Distribution Points (only needs "Read")
		- Packages
		- Policies
		- Scripts
	- This all goes down at "System Settings => JSS User Accounts & Groups"
- Your distribution points.

### Example: Adding basic preferences.
The preferences you will definitely need are `JSS_URL`, `API_USERNAME`, and `API_PASSWORD`. You will probably also want to configure distribution points so your packages can get synced to them. Distribution points are covered later.

```
defaults write com.github.autopkg JSS_URL https://test.jss.private:8443
defaults write com.github.autopkg API_USERNAME apiUser
defaults write com.github.autopkg API_PASSWORD apiPassword
```

### SSL

If your JSS uses a self-signed certificate, please consider switching to a real certificate. Please.

The bundled python-jss uses curl for HTTP requests if the [requests](http://python-requests.org/) python module is not available on the system; you can investigate adding the self-signed certificate to a curl.rc file for the user account autopkg runs as. This is left as an exercise for the non-security-minded admin. If you are testing or are running with scissors in YOLO mode, you can disable certificate verification by using the following preference:

```
defaults write com.github.autopkg JSS_VERIFY_SSL -bool false
```

This value defaults to true, because you should want to verify both where you're uploading to and that what you upload isn't harmed in transit. It's worth it before you push this to an installer that runs as root on all the computers you manage.

## Additional Preferences
In addition the URL, user, and password preferences, there are a few others you may want to use.
- `JSS_VERIFY_SSL`: Boolean (True or False). Whether or not to verify SSL traffic. Defaults to `True`, and recommended. (See SSL section above).
- `JSS_SUPPRESS_WARNINGS`: Boolean. Determines whether to suppress urllib3 warnings *when* you are using python requests as the request handler. This has no effect on curl. If you choose not to verify SSL with JSS_VERIFY_SSL, urllib3 throws warnings for each of the numerous requests JSSImporter makes. If you would like to see them, set to `False`. Defaults to `True`.

## A note on passwords
These instructions walk you through setting preferences through bash commandline tools (PlistBuddy, defaults). JSSImporter is written in Python. JSSImporter is often used in AutoPkgr which adds Objective-C to the mix. And the templates are all XML. Each of these languages has reserved characters, some of which may be in your API user's or distribution point's password. If you are having weird issues with authentication errors, even though you *know* you are typing the password in correctly to `defaults`/AutoPkgr/etc, please sidestep the issue entirely and create a password that is truly secure and try again. "Special characters" do not automatically create password complexity. Just randomly generate a very long alphanumeric password and you'll be golden. You won't be typing it in pretty much ever, so the length is not going to be a nuisance, compared to the anxiety attacks you may experience trying to figure out the intracies of encoding and decoding passwords back and forth through all of these different languages. This is not to say that JSSImporter doesn't do its best job trying to handle these correctly; but rather that there are enough FAQ password issues that it makes sense to just call it out and spare yourself the mysterious issues introduced when bash expands the `!` or `$` in your password to something *mysterious*.

## Adding distribution points.
You will need to specify your distribution points in the preferences as well. The JSSImporter will copy packages and scripts to all configured distribution points using the `JSS_REPOS` key. The value of this key is an array of dictionaries, which means you have to switch tools and use PlistBuddy. Of course, if you want to go all punk rock and edit this by hand like a savage, go for it. At least use vim.

### AFP/SMB Distribution Points
AFP and SMB distribution points are easy to configure. Each distribution point is represented by a simple dictionary, with two keys: `name`, and `password`. The rest of the information is pulled automatically from the JSS.
- `name` is the name of your Distribution Point as specified in the JSS' "Computer Management => File Share Distribution Points" page.
- `password` is the password for the user specified for the "Read/Write" account for this distribution point at "Computer Management => File Share Distribution Points => File Sharing => Read/Write Account => Password", NOT the API user's password (They are different, right?)

#### Example:
```
# Create our key and array
/usr/libexec/PlistBuddy -c "Add :JSS_REPOS array" ~/Library/Preferences/com.github.autopkg.plist

# For each distribution point, add a dict. This is the first array element, so it is index 0.
/usr/libexec/PlistBuddy -c "Add :JSS_REPOS:0 dict" ~/Library/Preferences/com.github.autopkg.plist
/usr/libexec/PlistBuddy -c "Add :JSS_REPOS:0:name string USRepository" ~/Library/Preferences/com.github.autopkg.plist
/usr/libexec/PlistBuddy -c "Add :JSS_REPOS:0:password string abc123" ~/Library/Preferences/com.github.autopkg.plist

# Second distribution point... (Notice the incremented array index.
/usr/libexec/PlistBuddy -c "Add :JSS_REPOS:1 dict" ~/Library/Preferences/com.github.autopkg.plist
/usr/libexec/PlistBuddy -c "Add :JSS_REPOS:1:name string MSRepository" ~/Library/Preferences/com.github.autopkg.plist
/usr/libexec/PlistBuddy -c "Add :JSS_REPOS:1:password string abc123" ~/Library/Preferences/com.github.autopkg.plist

# and so on...
```
So that section of your AutoPkg preferences should look roughly like this:
```
plutil -convert xml1 -o - ~/Library/Preferences/com.github.autopkg.plist
#...Relevent snippet...
	<key>API_PASSWORD</key>
	<string>xyzzy</string>
	<key>API_USERNAME</key>
	<string>apiUser</string>
	<key>JSS_REPOS</key>
	<array>
		<dict>
			<key>name</key>
			<string>USRepository</string>
			<key>password</key>
			<string>abc123</string>
		</dict>
		<dict>
			<key>name</key>
			<string>MSRepository</string>
			<key>password</key>
			<string>abc123</string>
		</dict>
	</array>
	<key>JSS_URL</key>
	<string>https://test.jss.private:8443</string>
#...
```

If you really want to, you can explicitly configure the required connection information. Here are the required keys (all values should be of type string):
- AFP
	- name (optional)
	- URL
	- type='AFP'
	- port (optional)
	- share_name
	- username (rw user)
	- password
- SMB
	- name (optional)
	- URL
	- domain
	- type='SMB'
	- port (optional)
	- share_name
	- username (rw user)
	- password

#### Troubleshooting AFP and SMB distribution points
If JSSImporter is having issues mounting your distribution points, the best troubleshooting step you can do is attempt to mount the share in question manually through the Finder or mount command.

### CDP and JDS: Cloud Distribution Point and Jamf Distribution Servers
Configuring a CDP or JDS is pretty easy too.

There are some caveats to using a CDP or JDS. At this time, there is no
officially documented way to upload files, or check for their existence on the
distribution server. python-jss works around this as best it can, but there is a possibility
that a package object can be created, with no package file uploaded (for
example, by CTRL-C'ing out of an AutoPkg run while an upload is happening). If
things get crazy, or packages seem to be missing, just delete the package
object with the web interface and run again.

Required keys:
- type='JDS' or 'CDP'

Your `JSS_REPOS` section should then simply look like this:
JDS:
```
	<key>JSS_REPOS</key>
	<array>
		<dict>
			<key>type</key>
			<string>JDS</string>
		</dict>
	</array>
```
CDP:
```
	<key>JSS_REPOS</key>
	<array>
		<dict>
			<key>type</key>
			<string>CDP</string>
		</dict>
	</array>
```

### Local Repository

If you prefer to use a Local Repository, use these keys (all values should be of type string):

- Local
	- type='Local'
	- mount_point (use absolute path)
	- share_name (use directory name)

#### Example

Note: Make sure you change the index number (here=0).

```
/usr/libexec/PlistBuddy -c "Add :JSS_REPOS array" ~/Library/Preferences/com.github.autopkg.plist
/usr/libexec/PlistBuddy -c "Add :JSS_REPOS:0 dict" ~/Library/Preferences/com.github.autopkg.plist
/usr/libexec/PlistBuddy -c "Add :JSS_REPOS:0:type string Local" ~/Library/Preferences/com.github.autopkg.plist
/usr/libexec/PlistBuddy -c "Add :JSS_REPOS:0:mount_point string /Users/Shared/JAMFdistrib" ~/Library/Preferences/com.github.autopkg.plist
/usr/libexec/PlistBuddy -c "Add :JSS_REPOS:0:share_name string JAMFdistrib" ~/Library/Preferences/com.github.autopkg.plist
```

Your `JSS_REPOS` section should then simply look like this:
```
    "JSS_REPOS" =     (
                {
            "mount_point" = "/Users/Shared/JAMFdistrib";
            "share_name" = JAMFdistrib;
            type = Local;
        }
    );
```

# Basic Usage

To see a list of input variables, use `autopkg processor-info JSSImporter`.

Ultimately, the JSSImporter is about crafting policies, which is Casper's method for installing software. However, policies require a number of other pieces of information: which groups to scope the policy to, what category the policy should be managed under, the category of the package, any scripts to include, and potentially many other policy settings, like whether to run a recon or not.

Recipes may be somewhat confusing to put together at first. Have a look at [the AutoPkg org's JSS recipes](https://github.com/autopkg/jss-recipes) to see it all in action.

Also, a group template and a policy template are included in this project to give you a place to start. (Note: They're in the example_templates folder)

## Filenames and Paths

For any argument to JSSImporter that requires a filename, you may use *just* a filename, *or* a full path to that file. Since these values often contain substitution variables (e.g. `%RECIPE_DIR%`) or may be overridden, JSSImporter follows a set series of search directories until it finds the filename specified.

These directories are:

1. The path as specified.
2. The parent folder of the path.
3. First ParentRecipe's folder.
4. First ParentRecipe's parent folder.
5. Second ParentRecipe's folder.
6. Second ParentRecipe's parent folder.
7. Nth ParentRecipe's folder.
8. Nth ParentRecipe's parent folder.

In most cases, it is probably best to simply specify the filename of the file in question, and let JSSImporter find it in the expected folders.

This searching applies to policy_template, computer group templates,
self_service_icon, scripts and script templates, and extension attribute templates.

It allows users to avoid having to copy the file to the override directory for
each recipe. It also allows users to structure a repository of JSS recipes in
subfolders, without having to copy shared support files into each product's
subdirectory.

## Note on Objects

It is worth noting that some objects manipulated through the web interface will be overwritten with their templated values after the next AutoPkg run of relevent recipes. This is by design, but may be a surprise if you try to edit, say, a policy, by hand after the JSSImporter creates it.

Specifically, objects that get recreated every run:
- Extension Attributes
- Scripts
- Smart Groups
- Policy

This way, you can ensure that what is specified in the recipe is what is on the JSS.

## Researching your JSS

While setting this all up, you will probably want to see some valid XML straight from the horse's mouth. There are a few ways to look at the XML directly:

1. The API documentation on your JSS includes a web interface for looking things up. Just add /api to your JSS's web address, i.e. https://yourcasperserver.org:8443/api
2. The [jss_helper](https://github.com/sheagcraig/jss_helper) gives you a simple commandline utility for querying the relevant objects.
3. [python-jss](https://github.com/sheagcraig/python-jss) is a python wrapper around the JSS API which will allow easy access to all objects on the JSS.


## Category & Policy Category

Categories are specified through the input variables `category` and `policy_category`. If they don't already exist, they will be created; otherwise, they're just left alone.

`category` corresponds to the category assigned to the package being uploaded.

`policy_category` corresponds to the category assigned to the policy, as found in the Policy->General->Category dropdown.

If you don't specify a category when adding a package or a policy, the JSS will assign it the category of "Unknown", which therefore is JSSImporter's behavior as well.

## Packages

Not surprisingly, packages are forwarded on from ParentRecipes seamlessly. However, if you need to specify an `os_requirements` setting, there's an input variable for that. The format follows that of the JSS: a comma-delimeted list of acceptable versions, with 'x' as a wildcard, e.g. `10.8.6, 10.9.x`.

Packages accept several other arguments: `package_notes` and `package_info` for specifying the corresponding fields on the package object, and `package_priority`, `package_reboot`, and `package_boot_volume_required` for controlling various installation settings.

### Package input variables:
|Variable|Description|Default|
|--------|-----------|-------|
|`os_requirements`|Comma-delimited list of acceptable versions, using `x` as a wildcard character|None|
|`package_notes`|Notes field on package object|None|
|`package_info`|Info field on package object|None|
|`package_priority`|Priority to use for deploying or uninstalling the package. String value between 1 and 20.|"10"|
|`package_reboot`|Specify whether computers must be restarted after installation. Accepts boolean values.|False|
|`package_boot_volume_required`|Ensures that the package is installed on the boot volume after imaging. Accepts boolean values.|True|

To save on time spent uploading, the JSSImporter processor only uploads a package to the distribution points when it think it is needed. Specifically, on AFP/SMB DP's, it compares the filename of the package just created with those on the DP, and uploads if it is missing. On a JDS, it only uploads a package if a new package-object was created.

This means that if your package recipe changes, but the output package filename stays the same, AFP/SMB DP's will not get the new package uploaded to them: please manually delete the package from the file shares and re-run your recipe.
For JDS DP's, packages are only uploaded if a package-object was created. To re-trigger uploading for the next run, delete the package from the JSS web interface in the Computer Management->Packages section.

If you would like to _not_ upload a package and _not_ add a package install action to a Policy, specify a `pkg_path` with a blank value to let JSSImporter know to skip package handling. Chances are extremely good that a previous step in a Parent pkg recipe set `pkg_path`, so you need to *un*-set it. Why would this be useful? Some organizations are using AutoPkg and JSSImporter to automate the creation of multiple policies per product-one to actually install the product, and another to notify the user of an available update. This is a lot of work to go through to try to be [Munki](https://www.munki.org), but it may improve the experience for users, since Casper will happily install apps while a user is logged in. Regardless, you can simply specify a second JSSImporter processor in your jss recipe, making sure to set `pkg_path` to a blank value (e.g: `<string/>`), and crafting the arguments and templates appropriately.

## Groups & Scope

You may specify any number of static and smart groups to scope your policy to (including none). The `groups` input variable should be an array of group dictionaries. Each group dictionary needs a name. Additionally, the optional `smart` property should be `True`, and you will need to include the path, `template_path`, to an XML template for your smart group.

Static groups need only a name.

Here is an example `groups` array from the jss-recipes repo:
```
<key>groups</key>
<array>
	<dict>
		<key>name</key>
		<string>%GROUP_NAME%</string>
		<key>smart</key>
		<true/>
		<key>template_path</key>
		<string>%GROUP_TEMPLATE%</string>
	</dict>
</array>
```

Smart groups require an XML template, but, like for policies, the template can do some variable substitution, so you can often get away with a single template file for all of your recipes. The easiest way to see the correct XML structure for a smart gruop is to create one in the web interface, and then look it up with the api at https://yourcasperserver:8443/api/#!/computergroups/findComputerGroupsByName_get

Here is an example of the smart group template that I use:
```
<computer_group>
    <name>%group_name%</name>
    <is_smart>true</is_smart>
    <criteria>
        <criterion>
            <name>Application Title</name>
            <priority>0</priority>
            <and_or>and</and_or>
            <search_type>is</search_type>
            <value>%JSS_INVENTORY_NAME%</value>
        </criterion>
        <criterion>
            <name>Application Version</name>
            <priority>1</priority>
            <and_or>and</and_or>
            <search_type>is not</search_type>
            <value>%VERSION%</value>
        </criterion>
        <criterion>
            <name>Computer Group</name>
            <priority>2</priority>
            <and_or>and</and_or>
            <search_type>member of</search_type>
            <value>Testing</value>
        </criterion>
    </criteria>
</computer_group>
```

This smart group applies to computers who are members of the Testing static group, who don't have the latest version of the app in question. You can see how, like elsewhere in AutoPkg recipes, variable substitution occurs with a %wrapped% variable name.

For smart groups which use the "Application Title" as part of their criteria, you have to be careful. The JSS inventory seems to be based on the filenames of the apps in `/Applications` only. The %JSS_INVENTORY_NAME% template variable / %jss_inventory_name% recipe input variable needs to be the name the JSS uses for its "Application Title" value, which in some cases differs from what the app is commonly called. You can look this up by creating a new smart group in the web interface, adding a criteria of "Application Title" "is" and then hit the ellipses button to see all of the inventoried apps.

So "Google Chrome.app" and "Goat Simulator.app" may be the inventory name, even though you would want your package name to be GoogleChrome and GoatSimulator.

_NOTE_: If you don't specify a `%jss_inventory_name%` input variable, the JSSImporter will add '.app' to the product name, since this is the case for _most_ apps. Only specify %jss_inventory_name% when you want to override the automatic behavior.

See the "Template" section for a list of all of the string replacement variables.

_NOTE_: Applications that don't install into `/Applications` will not be available for "Application Title" criteria. The best solution is to create an extension attribute that returns the version number of the app in question and use that value in your smart group criteria. If you look at the Adobe Flash Player, Silverlight, or Oracle Java 7 recipes in [my jss recipe repo](https://github.com/sheagcraig/jss-recipes), there are examples of how to solve this problem.

You can of course *also*/*instead* set the Computer Management/Computer Inventory Collection/Software/Plug-ins setting in Casper to "Collect Plug-ins", which should already know the right path to check for Internet Plugins.

### Exclusion Groups
JSSImporter can use group exclusions in its scope as well. Specify an `exclusion_groups` array of group dictionaries exactly as per groups above to do so.

## Scripts

Scripts work the same way as groups. The `scripts` input variable should contain an array of one dictionary for each script. You can skip the `scripts` key entirely if you don't need any scripts. Each dictionary should contain a `name` key, which is the path to the script file itself. It should also have a `template_path` item which is a path to a script template. A script template is included with this project, although you'll probably only be interested in setting the priority ("After", or "Before")

Unlike packages, scripts are uploaded every run, as presumably, they are signicantly smaller than even modestly-sized packages.

## Extension Attributes

Extension attributes work just like scripts. You need a complete and valid XML file for the extension attribute (although it will do variable substitution). To experiment with XML for these, again, use the API page to look through the ones on your JSS. Included with this project there is a template for extension attributes as well, although you will need to edit it to add in your script. As the extension attribute is XML, you will need to properly HTML encode reserved characters; e.g. '<' becomes '&lt;', '>' becomes '%gt;'. Since the extension attributes value needs to be <result>Your Result</result> sent to stdout, you will need to do this manually for every extension attribute.

Solutions to handle this automatically are being considered, but at this moment, XML is not valid if there are < and > sitting around that aren't escaped.

The `extension_attributes` input variable should contain an array of dictionaries. Each dictionary should contain an `ext_attribute_path` item which is a path to the extension attribute file. You may also skip this key entirely if you don't need extension attributes for your recipe.

## Policy

Policies are generated on the fly by supplying the JSSImporter with a policy template. This is a simplified XML document-essentially an empty policy object from the API. The JSSImporter will handle substituting in the scope, category, and package information as specified in the other parts of the recipe. You may, if you wish, also include elements directly. Any groups mentioned in the input variables to the recipe, for example, would get added to the scoping groups hardcoded into the supplied policy template.

When adding a package to a policy, the `policy_action_type` input variable is used to determine the type of package action to perform. The default is `Install`. Valid arguments also include `Cache` and `Install Cached`.

Indeed, the only input variables for policies are `policy_category`, discussed earlier, and `policy_template`, which should be a path to a policy template, an example of which is included with this project. Again, you can experiment with values in the web interface, and then get the XML data from either an API lookup through the API documentation for your server, https://yourcasperserver:8443/api/, or if you're feeling spicy, through [jss_helper](https://github.com/sheagcraig/jss_helper) or through the [python-jss](https://github.com/sheagcraig/python-jss) wrapper.

If the `policy_category` value is set, it will be used to create a category, even if the policy template doesn't template that value into the policy's category spot using the `$POLICY_CATEGORY%` replacement variable. Likewise, if you set input variable `policy_category`, it will be used in the policy template even if it doesn't use the replacemement tag or doesn't have a category tag to begin with. If you make a mistake and specify `policy_category` and hardcode a category into the policy template, only the `policy_category` will be created, and the policy will use it, e.g. `policy_category` *wins*.

See the "Template" section for a list of all of the string replacement variables.

You can skip policy creation by leaving out the `policy_template` key, or specifying an empty value for the `policy_template`. I.e.:
```
<key>policy_template</key>
<string></string>
```

## Self Service Icons

Having icons is nice. That being said, they are kind of tricky to implement. There is no way to query the JSS for a list of available icons through the API. You can view them in the web interface, but this doesn't expose the ID number or name properties. Through the API, you can only upload and attach an icon to a specific policy. For more information, take a look at the source!

So, if you want to include icons in your recipes, first off, you'll need the icon files. I imagine most icons are copyrighted material, so distributing them with recipes is not okay (otherwise, JAMF would just include them with Casper...) For information on grabbing and saving these icons, see: [Icon file to use in Self Service app?](https://jamfnation.jamfsoftware.com/discussion.html?id=873) and [Icon Formats](https://jamfnation.jamfsoftware.com/article.html?id=106) for help on grabbing these files.

Then, to include in a recipe, use the `self_service_icon` key, with a string value of the path to the icon file.

If you don't want to worry about icons, just leave out the `self_service_icon` key and JSSImporter will skip it.

## Template Substitution Variables

All templates used in JSS recipes will perform text substitution before attempting to upload to the JSS. A text substitution variable is indicated by surrounding a variable name in "%"'s. Substitution will occur if an AutoPkg environement variable exists for that substition (i.e., if you put `%giant_burrito%` in your template, and there's no AutoPkg "giant_burrito", then nothing will happen).

JSSImporter defines the following default substitution variables:
- `%VERSION%`: The AutoPkg version variable. If this hasn't been provided anywhere, JSSImporter uses "0.0.0.0" (and outputs a warning) since the jss-recipes repo heavily uses `%VERSION%`.
- `%PKG_NAME%`: The name of the package. Specifically, the display name that the JSS uses to represent that package. Usually the filename.
- `%PROD_NAME%`: The value of the input variable `%prod_name%`. Note, `%prod_name%` is a required recipe input variable.
- `%POLICY_CATEGORY%`: The value of `%policy_category%`, if specified, or "Unknown", if not-this is what the JSS will assign anyway.
- `%SELF_SERVICE_DESCRIPTION%`: Used to specify the contents of the description field for self service items. Use this input variable in concert with ensuring that it is added to the policy template.
- `%JSSINVENTORY_NAME%`: If you want to override the default guessing of the "Application Title" for a smart group, use this along with an input variable of jss_inventory_name
- `%SITE_NAME%`: If you want to specify a SITE for you policy or group.
- `%SITE_ID%`: If you want to specify a SITE for you policy or group.

However, any AutoPkg environment variable may be accessed in this manner. For example, `AUTOPKG_VERSION` can be substituted in a template by wrapping in "%", i.e. `%AUTOPKG_VERSION%`. 

## Using Overrides

All of my recipes are designed to allow you to use overrides to change the major input variables. However, if you *do* use overrides, you may experience unexpected difficulties. Since the override recipe lives in your `~/Library/AutoPkg/RecipeOverrides/` folder, the %RECIPE_DIR% substitution in those recipes now points to the RecipeOverrides folder rather than the base jss.recipe. You will probably need to copy all of the recipe's needed support files: templates, scripts, and icons, to the override directory. Hopefully some time soon AutoPkg can add a %PARENT_RECIPE_DIR% variable for overrides to use.

# Notes for Developers and the Intrigued

## Developer Setup

If you want to hack on the code, you will need to fork & clone the project. An easy way to work is to symlink JSSImporter.py into your autopkglib folder (i.e. `ln -sf /Library/AutoPkg/autopkglib/JSSImporter.py <this_repos_dir>`). If you are using a different python-jss release, replace the copy in /Library/Application Support/JSSImporter.

If you want to build JSSImporter packages, you will need the following dependencies:

- [The Luggage](https://github.com/unixorn/luggage)
- A copy of the python-jss you intend to package, placed in the JSSImporter repo folder 
	- e.g. put the python-jss repo's `jss` folder in this folder.

Then you can do `make pkg` from the repo directory to generate an installer package.

## How JSSImporter is Installed

JSSImporter is available primarily as an Apple installer package, which installs two things:

- JSSImporter.py is put into /Library/AutoPkg/autopkglib so AutoPkg can "find" it.
- python-jss, which does all of the actual API calls, is put into /Library/Application Support/JSSImporter. JSSImporter inserts this path into the first entry of its python system path so that it will use the python-jss bundled in the installer package over any other instance.

In the past, python-jss was installed from the Python Packaging Index like any other python package. This is a common practice for python developers, but can cause confusion when you're only interested in running AutoPkg. This made it easier to install python requests, which was a dependency prior to the 2.0 versions of python-jss.

Therefore, the decision was made to make a dedicated support folder for JSSImporter and use it for storing a copy of python-jss. Also, python-jss 2.0+ can use the system curl when python-requests is not available, so there is no need to pip install requests any longer.

This can complicate casually testing upcoming JSSImporter or python-jss releases, but fear not. Read below...

## I want to test a newer python-jss or JSSImporter

If you are interested in testing a newer version of either JSSImporter or python-jss, you can do so by cloning or downloading the testing branch desired from either project and copying them into the locations listed above in the "How JSSImporter is Installed" section.

JSSImporter will output its version, and that of python-jss, so verbose invocations of AutoPkg will include confirmation of the versions in use.

Python will look in the current working directory for imports before anything in the path, so if you're still seeing older versions listed, make sure you don't have a copy of python-jss in the /Library/AutoPkg/autopkglib folder.
