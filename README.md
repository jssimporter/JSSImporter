jss-autopkg-addon
=================

This module adds the ability for autopkg to create groups, upload packages and scripts, and create policies for the Casper JSS. This project began from Allister Banks' original [jss-autopkg-addon project](https://github.com/arubdesu/jss-autopkg-addon), but has since diverged considerably to add greater customization options while maintaining the existing functionality.

Installation and Setup
=================

The easiest method for installing is to download the latest package installer from the "releases" section. This will add the JSSImporter.py processor to your autopkglib, and the python-jss module to your system python, which is what AutoPkg should be using. Bonus points if you grab my [recipe](https://github.com/autopkg/sheagcraig-recipes) and just use AutoPkg to build your own installer...

You will need to add some preferences to your AutoPkg preferences file.:

	```
	defaults write com.github.autopkg JSS_REPO /Volumes/JSS_Dist_Point
	defaults write com.github.autopkg JSS_URL https://test.jss.private:8443
	defaults write com.github.autopkg API_USERNAME apiUser
	defaults write com.github.autopkg API_PASSWORD apiPassword
	```

Manual Installation and Setup
=================

However, if you're keen on manually installing, follow these directions:

1. Make sure you've already installed the most current autopkg tools (AND RECIPES) FIRST! (Sorry to yell.) Then use the releases tab, to the right above, to download the code.
2. Unzip the download somewhere and copy or link the ```JSSImporter.py``` plugin file to your autopkglib folder, typically located at ```/Library/AutoPkg/autopkglib```
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

3. This project relies on [python-jss](https://github.com/sheagcraig/python-jss), and includes a copy in the release. This is a work in progress, and AutoPkg does not currently have a way to import external dependencies, so python-jss must be added to a location available to your ```PYTHONPATH```. You can either add the location of the module to your ```PYTHONPATH``` or copy/install the module to your site-packages folder.
	- Add to ```PYTHONPATH```:
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

To see a list of input variables, use ```autopkg processor-info JSSImporter```.

Ultimately, the JSSImporter is about crafting policies, which is Casper's method for installing software. However, policies require a number of other pieces of information: which groups to scope the policy to, what category the policy should be managed under, the category of the package, any scripts to include, and potentially many other policy settings, like whether to run a recon or not.

Recipes may be somewhat confusing to put together at first. Have a look at [my JSS recipes](https://github.com/sheagcraig/jss-recipes) to see it all in action.

Also, a group template and a policy template are included with the project files to give you a place to start. (Note: These files are not included if you use the package installer!)

Note on Objects
=================

It is worth noting that some objects manipulated through the web interface will be overwritten with their templated values after the next AutoPkg run of relevent recipes. This is by design, but may be a surprise if you try to edit, say, a policy, by hand after the JSSImporter creates it.

Specifically, objects that get recreated every run:
Extension Attributes
Scripts
Smart Groups
Policy

This way, you can ensure that what is specified in the recipe is what is on the JSS.

Researching your JSS
=================

While setting this all up, you will probably want to see some valid XML straight from the horses' mouth. There are a few ways to look at the XML directly:
1. The API documentation on your JSS includes a web interface for looking things up. Just add /api to your JSS's web address, i.e. https://yourcasperserver.org:8443/api
2. The [jss_helper](https://github.com/sheagcraig/jss_helper) gives you a simple commandline utility for querying the relevant objects.
3. [python-jss](https://github.com/sheagcraig/python-jss) is a python wrapper around the JSS API which will allow easy access to all objects on the JSS.


Category & Policy Category
=================

Categories are specified through the input variables ```category``` and ```policy_category```. If they don't already exist, they will be created; otherwise, they're just left alone.

```category``` corresponds to the category assigned to the package being uploaded.

```policy_category``` corresponds to the category assigned to the policy, as found in the Policy->General->Category dropdown.

Packages
=================

Not surprisingly, packages are forwarded on from ParentRecipes seamlessly. However, if you need to specify an ```os_requirement```, there's an input variable for that. The format follows that of the JSS: a comma-delimeted list of acceptable versions, with 'x' as a wildcard, e.g. ```10.8.6, 10.9.x```

Groups
=================

You may specify any number of static and smart groups to scope your policy to (including none). The ```groups``` input variable should be an array of group dictionaries. Each group dictionary needs a name. Additionally, the optional ```smart``` property should be ```True```, and you will need to include the path, ```template_path```, to an XML template for your smart group.

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
            <value>%JSSINVENTORY_NAME%</value>
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

For smart groups which use the "Application Title" as part of their criteria, you have to be careful. The JSS inventory seems to be based on the filenames of the apps in ```/Applications``` only. The %JSSINVENTORY_NAME% template variable / %jss_inventory_name% recipe input variable needs to be the name the JSS uses for its "Application Title" value, which in some cases differs from what the app is commonly called. You can look this up by creating a new smart group in the web interface, adding a criteria of "Application Title" "is" and then hit the ellipses button to see all of the inventoried apps.

So "Google Chrome.app" and "Goat Simulator.app" may be the inventory name, even though you would want your package name to be GoogleChrome and GoatSimulator.

_NOTE_: If you don't specify a ```%jss_inventory_name%``` input variable, the JSSImporter will add '.app' to the product name, since this is the case for _most_ apps. Only specify %jss_inventory_name% when you want to override the automatic behavior.

See the "Template" section for a list of all of the string replacement variables.

_NOTE_: Applications that don't install into ```/Applications``` will not be available for "Application Title" criteria. The best solution is to create an extension attribute that returns the version number of the app in question and use that value in your smart group criteria. If you look at the Adobe Flash Player, Silverlight, or Oracle Java 7 recipes in [my jss recipe repo](https://github.com/sheagcraig/jss-recipes), there are examples of how to solve this problem.

Scripts
=================

Scripts work the same way as groups. The ```scripts``` input variable should contain an array of dictionaries. Each dictionary should contain a ```name``` key, which is the path to the script file itself. It should also have a ```template_path``` item which is a path to a script template. A script template is included with this project, although you'll probably only be interested in setting the priority ("After", or "Before")

Extension Attributes
=================

Extension attributes work just like scripts. You need a complete and valid XML file for the extension attribute (although it will do variable substitution). To experiment with XML for these, again, use the API page to look through the ones on your JSS. Included with this project there is a template for extension attributes as well, although you will need to edit it to add in your script. As the extension attribute is XML, you will need to properly  HTML encode reserved characters; e.g. '<' becomes '&lt;', '>' becomes '%gt;'. Since the extension attributes value needs to be <result>Your Result</result> sent to stdout, you will need to do this manually for every extension attribute.

Solutions to handle this automatically are being considered, but at this moment, XML is not valid if there are < and > sitting around that aren't escaped.

The ```extension_attributes``` input variable should contain an array of dictionaries. Each dictionary should contain a ```name``` key, which is the name of the extension attribute. It should also have a ```ext_attribute_path``` item which is a path to extension attribute file.


Policy
=================

Policies are generated on the fly by supplying the JSSImporter with a policy template. This is a simplified XML document-essentially an empty policy object from the API. The JSSImporter will handle substituting in the scope, category, and package information as specified in the other parts of the recipe. You may, if you wish, also include elements directly. Any groups mentioned in the input variables to the recipe, for example, would get added to the scoping groups hardcoded into the supplied policy template.

Indeed, the only input variables for policies are ```policy_category```, discussed earlier, and ```policy_template```, which should be a path to a policy template, an example of which is included with this project. Again, you can experiment with values in the web interface, and then get the XML data from either an API lookup through the API documentation for your server, https://yourcasperserver:8443/api/, or if you're feeling spicy, through [jss_helper](https://github.com/sheagcraig/jss_helper) or through the [python-jss](https://github.com/sheagcraig/python-jss) wrapper.

See the "Template" section for a list of all of the string replacement variables.

Template
=================

Substitution variables available in templates include:
- ```%VERSION%```: The AutoPkg version variable.
- ```%PKG_NAME%```: The name of the package. Specifically, the display name that the JSS uses to represent that package. Usually the filename.
- ```%PROD_NAME%```: The value of the input variable ```%prod_name%```. Note, ```%prod_name%``` is a required recipe input variable.
- ```%POLICY_CATEGORY%```: The value of ```%policy_category%```, if specified, or "Unknown", if not-this is what the JSS will assign anyway.
- ```%JSSINVENTORY_NAME%```: If you want to override the default guessing of the "Application Title" for a smart group, use this along with an input variable of jss_inventory_name

Comments/Questions/Ideas
=================

Please send me feature requests or issues through the Github page.
