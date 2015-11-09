

This processor adds the ability for AutoPkg to create groups, upload packages and scripts, add extension attributes, and create policies for the Casper JSS, allowing you to fully-automate your software testing workflow. 

This project began from Allister Banks' original [jss-autopkg-addon project](https://github.com/arubdesu/jss-autopkg-addon), but has since diverged ~~considerably~~ completely to add greater customization options while maintaining the existing functionality.

Getting Started
=================

### Installation
To install, download the latest package installer from the "releases" section. This will add the JSSImporter.py processor to your autopkglib folder, and the proper python-jss package to your system python's site-packages. This allows you to start using JSSImporter right away. Of course, you can also use the new (as of AutoPkg 0.4.0) shared processor system to include the JSSImporter in the same folder as your recipes, but you'll still need python-jss available to the system python.

python-jss is pulled from pypi.org using easy_install, so please ensure you have an active internet connection.

### Setup
Prior to using the JSSImporter, You will need to add some preferences to your AutoPkg preferences file:
- The URL to your jss
- The username and password of an API privileged user.
	- It is recommended to create a user named something like "AutoPkg". It will need Create, Read, and Update privileges on:
		- Categories
		- Computer Groups
		- Distribution Points (only needs "Read")
		- Extension Attributes
		- Packages
		- Policies
		- Scripts
	- This all goes down at "System Settings => JSS User Accounts & Groups"
- Your distribution points.

### Example: Adding basic preferences.
```
defaults write com.github.autopkg JSS_URL https://test.jss.private:8443
defaults write com.github.autopkg API_USERNAME apiUser
defaults write com.github.autopkg API_PASSWORD apiPassword
```

### Additional Preferences
In addition the URL, user, and password preferences, there are a few others you may want to use.
- `JSS_VERIFY_SSL`: Boolean (True or False). Whether or not to verify SSL traffic. Defaults to `True`, and recommended. (See below).
- `JSS_MIGRATED`: Boolean. If you have "migrated" your JSS (uses the web interface to edit scripts), set to `True`. Defaults to `False`. This only really comes into play if you have an AFP or SMB share *and* have migrated.
- `JSS_SUPPRESS_WARNINGS`: Boolean. Determines whether to suppress urllib3 warnings.  If you choose not to verify SSL with JSS_VERIFY_SSL, urllib3 throws warnings for each of the numerous requests JSSImporter makes. If you would like to see them, set to `False`. Defaults to `True`.

### Adding distribution points.
You will need to specify your distribution points in the preferences as well. The JSSImporter will copy packages and scripts to all configured distribution points using the `JSS_REPOS` key. The value of this key is an array of dictionaries, which means you have to switch tools and use PlistBuddy. Of course, if you want to go all punk rock and edit this by hand like a savage, go for it. At least use vim.

#### AFP/SMB Distribution Points
AFP and SMB distribution points are easy to configure. Each distribution point is represented by a simple dictionary, with two keys: `name`, and `password`. The rest of the information is pulled automatically from the JSS.
- `name` is the name of your Distribution Point as specified in the JSS' "Computer Management => File Share Distribution Points" page.
- `password` is the password for the user specified for the "Read/Write" account for this distribution point at "Computer Management => File Share Distribution Points => File Sharing => Read/Write Account => Password", NOT the API user's password (They are different, right?)

##### Example:
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

#### CDP and JDS: Cloud Distribution Point and Jamf Distribution Servers
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

#### Local Repository

If you prefer to use a Local Repository, use these keys (all values should be of type string):

- Local
	- type='Local'
	- mount_point (use absolute path)
	- share_name (use directory name)

##### Example

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

Manual Installation and Setup, and Developer Access
=================
Developers should just fork and clone the project. The python-jss project will be required, and should be located wherever your python of choice can find it.

If you're keen on manually installing for normal usage, follow these directions:

1. Make sure you've already installed the most current autopkg tools (AND RECIPES) FIRST! (Sorry to yell.) Then use the releases tab, to the right above, to download the code.
2. Unzip the download somewhere and copy or link the `JSSImporter.py` plugin file to your autopkglib folder, typically located at `/Library/AutoPkg/autopkglib`
	- i.e. 
	```
	sudo cp ~/Downloads/jss-autopkg-addon/JSSImporter.py /Library/AutoPkg/autopkglib
	```
	or
	```
	sudo ln -s ~/Downloads/jss-autopkg-addon/JSSImporter.py /Library/AutoPkg/autopkglib/JSSImporter.py
	```
2. You will need to add some preferences to your AutoPkg preferences file.:

	```
	defaults write com.github.autopkg JSS_REPO /Volumes/JSS_Dist_Point
	defaults write com.github.autopkg JSS_URL https://test.jss.private:8443
	defaults write com.github.autopkg API_USERNAME apiUser
	defaults write com.github.autopkg API_PASSWORD apiPassword
	```

3. This project relies on [python-jss](https://github.com/sheagcraig/python-jss), and includes a copy in the release. This is a work in progress, and AutoPkg does not currently have a way to import external dependencies, so python-jss must be added to a location available to your `PYTHONPATH`. You can either add the location of the module to your `PYTHONPATH` or copy/install the module to your site-packages folder.
	- Add to `PYTHONPATH`:
	  ```
	  PYTHONPATH=$PYTHONPATH:~/Downloads/jss-autopkg-addon
	  ```
    	- Add to your .bash_profile if you want it to be set automatically.
	- Copy python-jss to site-packages:
	  This requires knowing where your python's site packages are... On the Apple python, it would look like this:
	  ```
	  sudo cp -R ~/Downloads/jss-autopkg-addon/jss /Library/Python/2.7/site-packages/
	  ```
	- Or just pip install it:
	  ```
	  pip install python-jss
	  ```

Basic Usage
=================

To see a list of input variables, use `autopkg processor-info JSSImporter`.

Ultimately, the JSSImporter is about crafting policies, which is Casper's method for installing software. However, policies require a number of other pieces of information: which groups to scope the policy to, what category the policy should be managed under, the category of the package, any scripts to include, and potentially many other policy settings, like whether to run a recon or not.

Recipes may be somewhat confusing to put together at first. Have a look at [my JSS recipes](https://github.com/sheagcraig/jss-recipes) to see it all in action.

Also, a group template and a policy template are included with the project files to give you a place to start. (Note: They're in `/usr/share/jss-autopkg-addon`)

Filenames and Paths
===================
For any argument to JSSImporter that requires a filename, you may use *just* a filename, *or* a full path to that file. Since these values often contain substitution variables (e.g. `%RECIPE\_DIR%`) or may be overridden, JSSImporter follows a set series of search directories until it finds the filename specified.

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

Note on Objects
=================

It is worth noting that some objects manipulated through the web interface will be overwritten with their templated values after the next AutoPkg run of relevent recipes. This is by design, but may be a surprise if you try to edit, say, a policy, by hand after the JSSImporter creates it.

Specifically, objects that get recreated every run:
- Extension Attributes
- Scripts
- Smart Groups
- Policy

This way, you can ensure that what is specified in the recipe is what is on the JSS.

Researching your JSS
=================

While setting this all up, you will probably want to see some valid XML straight from the horse's mouth. There are a few ways to look at the XML directly:

1. The API documentation on your JSS includes a web interface for looking things up. Just add /api to your JSS's web address, i.e. https://yourcasperserver.org:8443/api
2. The [jss_helper](https://github.com/sheagcraig/jss_helper) gives you a simple commandline utility for querying the relevant objects.
3. [python-jss](https://github.com/sheagcraig/python-jss) is a python wrapper around the JSS API which will allow easy access to all objects on the JSS.


Category & Policy Category
=================

Categories are specified through the input variables `category` and `policy_category`. If they don't already exist, they will be created; otherwise, they're just left alone.

`category` corresponds to the category assigned to the package being uploaded.

`policy_category` corresponds to the category assigned to the policy, as found in the Policy->General->Category dropdown.

If you don't specify a category when adding a package or a policy, the JSS will assign it the category of "Unknown", which therefore is JSSImporter's behavior as well.

Packages
=================

Not surprisingly, packages are forwarded on from ParentRecipes seamlessly. However, if you need to specify an `os_requirements` setting, there's an input variable for that. The format follows that of the JSS: a comma-delimeted list of acceptable versions, with 'x' as a wildcard, e.g. `10.8.6, 10.9.x`.

Packages accept two other arguments: `package_notes` and `package_info` for specifying the corresponding fields on the package object. 

To save on time spent uploading, the JSSImporter processor only uploads a package to the distribution points when it think it is needed. Specifically, on AFP/SMB DP's, it compares the filename of the package just created with those on the DP, and uploads if it is missing. On a JDS, it only uploads a package if a new package-object was created.

This means that if your package recipe changes, but the output package filename stays the same, AFP/SMB DP's will not get the new package uploaded to them: please manually delete the package from the file shares and re-run your recipe.
For JDS DP's, packages are only uploaded if a package-object was created. To re-trigger uploading for the next run, delete the package from the JSS web interface in the Computer Management->Packages section.

If you would like to _not_ upload a package and _not_ add a package install action to a Policy, specify a `pkg_path` with a blank value to let JSSImporter know to skip package handling. Chances are extremely good that a previous step in a Parent pkg recipe set `pkg_path`, so you need to *un*-set it. Why would this be useful? Some organizations are using AutoPkg and JSSImporter to automate the creation of multiple policies per product-one to actually install the product, and another to notify the user of an available update. This is a lot of work to go through to try to be [Munki](https://www.munki.org), but it may improve the experience for users, since Casper will happily install apps while a user is logged in. Regardless, you can simply specify a second JSSImporter processor in your jss recipe, making sure to set `pkg_path` to a blank value (e.g: `<string/>`), and crafting the arguments and templates appropriately.

Groups
=================

You may specify any number of static and smart groups to scope your policy to (including none). The `groups` input variable should be an array of group dictionaries. Each group dictionary needs a name. Additionally, the optional `smart` property should be `True`, and you will need to include the path, `template_path`, to an XML template for your smart group.

Static groups need only a name.

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

Scripts
=================

Scripts work the same way as groups. The `scripts` input variable should contain an array of one dictionary for each script. You can skip the `scripts` key entirely if you don't need any scripts. Each dictionary should contain a `name` key, which is the path to the script file itself. It should also have a `template_path` item which is a path to a script template. A script template is included with this project, although you'll probably only be interested in setting the priority ("After", or "Before")

Unlike packages, scripts are uploaded every run, as presumably, they are signicantly smaller than even modestly-sized packages.

Extension Attributes
=================

Extension attributes work just like scripts. You need a complete and valid XML file for the extension attribute (although it will do variable substitution). To experiment with XML for these, again, use the API page to look through the ones on your JSS. Included with this project there is a template for extension attributes as well, although you will need to edit it to add in your script. As the extension attribute is XML, you will need to properly HTML encode reserved characters; e.g. '<' becomes '&lt;', '>' becomes '%gt;'. Since the extension attributes value needs to be <result>Your Result</result> sent to stdout, you will need to do this manually for every extension attribute.

Solutions to handle this automatically are being considered, but at this moment, XML is not valid if there are < and > sitting around that aren't escaped.

The `extension_attributes` input variable should contain an array of dictionaries. Each dictionary should contain an `ext_attribute_path` item which is a path to the extension attribute file. You may also skip this key entirely if you don't need extension attributes for your recipe.

Policy
=================

Policies are generated on the fly by supplying the JSSImporter with a policy template. This is a simplified XML document-essentially an empty policy object from the API. The JSSImporter will handle substituting in the scope, category, and package information as specified in the other parts of the recipe. You may, if you wish, also include elements directly. Any groups mentioned in the input variables to the recipe, for example, would get added to the scoping groups hardcoded into the supplied policy template.

Indeed, the only input variables for policies are `policy_category`, discussed earlier, and `policy_template`, which should be a path to a policy template, an example of which is included with this project. Again, you can experiment with values in the web interface, and then get the XML data from either an API lookup through the API documentation for your server, https://yourcasperserver:8443/api/, or if you're feeling spicy, through [jss_helper](https://github.com/sheagcraig/jss_helper) or through the [python-jss](https://github.com/sheagcraig/python-jss) wrapper.

See the "Template" section for a list of all of the string replacement variables.

You can skip policy creation by leaving out the `policy_template` key, or specifying an empty value for the `policy_template`. I.e.:
```
<key>policy_template</key>
<string></string>
```

Self Service Icons
=================

Having icons is nice. That being said, they are kind of tricky to implement. There is no way to query the JSS for a list of available icons through the API. You can view them in the web interface, but this doesn't expose the ID number or name properties. Through the API, you can only upload and attach an icon to a specific policy. For more information, take a look at the source!

So, if you want to include icons in your recipes, first off, you'll need the icon files. I imagine most icons are copyrighted material, so distributing them with recipes is not okay (otherwise, JAMF would just include them with Casper...) For information on grabbing and saving these icons, see: [Icon file to use in Self Service app?](https://jamfnation.jamfsoftware.com/discussion.html?id=873) and [Icon Formats](https://jamfnation.jamfsoftware.com/article.html?id=106) for help on grabbing these files.

Then, to include in a recipe, use the `self_service_icon` key, with a string value of the path to the icon file.

If you don't want to worry about icons, just leave out the `self_service_icon` key and JSSImporter will skip it.

Template Substitution Variables
===============================
All templates used in JSS recipes will perform text substitution before attempting to upload to the JSS. A text substitution variable is indicated by surrounding a variable name in "%"'s. Substitution will occur if an AutoPkg environement variable exists for that substition (i.e., if you put `%giant_burrito%` in your template, and there's no AutoPkg "giant_burrito", then nothing will happen).

JSSImporter defines the following default substitution variables:
- `%VERSION%`: The AutoPkg version variable.
- `%PKG_NAME%`: The name of the package. Specifically, the display name that the JSS uses to represent that package. Usually the filename.
- `%PROD_NAME%`: The value of the input variable `%prod_name%`. Note, `%prod_name%` is a required recipe input variable.
- `%POLICY_CATEGORY%`: The value of `%policy_category%`, if specified, or "Unknown", if not-this is what the JSS will assign anyway.
- `%SELF_SERVICE_DESCRIPTION%`: Used to specify the contents of the description field for self service items. Use this input variable in concert with ensuring that it is added to the policy template.
- `%JSSINVENTORY_NAME%`: If you want to override the default guessing of the "Application Title" for a smart group, use this along with an input variable of jss_inventory_name
- `%SITE_NAME%`: If you want to specify a SITE for you policy or group.
- `%SITE_ID%`: If you want to specify a SITE for you policy or group.

However, any AutoPkg environment variable may be accessed in this manner. For example, `AUTOPKG_VERSION` can be substituted in a template by wrapping in "%", i.e. `%AUTOPKG_VERSION%`. 

Using Overrides
=================
All of my recipes are designed to allow you to use overrides to change the major input variables. However, if you *do* use overrides, you may experience unexpected difficulties. Since the override recipe lives in your `~/Library/AutoPkg/RecipeOverrides/` folder, the %RECIPE_DIR% substitution in those recipes now points to the RecipeOverrides folder rather than the base jss.recipe. You will probably need to copy all of the recipe's needed support files: templates, scripts, and icons, to the override directory. Hopefully some time soon AutoPkg can add a %PARENT_RECIPE_DIR% variable for overrides to use.

SSL
===
If you have issues with certificate validation (either a self-signed certificate on a JSS instance, or issues due to Python's weak SSL support in 2.x on OS X), there is an additional boolean preference you can set to disable SSL verification:

    defaults write com.github.autopkg JSS_VERIFY_SSL -bool false

This value defaults to true.

Comments/Questions/Ideas
=================

Please send me feature requests or issues through the Github page.

I'm working on a series of blog posts covering software testing best practices with Casper, and how to configure JSSImporter, and write recipes for it, on my [blog](http://labs.da.org/wordpress/sheagcraig/)
