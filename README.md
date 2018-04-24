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

One piece of advice: The [AutoPkg organization's jss-recipes repo](https://github.com/autopkg/jss-recipes) is a community project which adheres to the best-practices generally agreed upon by the community. If you are trying to do something beyond what these recipes or processor cover, you may need to step back and re-evaluate your goals. JSSImporter's goal is to allow you to, with AutoPkg, automate the drudgery of managing a *testing* workflow. It is not meant to deploy software straight to production machines. It is not meant as a way to bootstrap all of a JSS's policies. There is a lot you can do with the Jamf PRO API, and JSSImporter's code is an illustration of how to go about doing this. If JSSImporter and the jss-recipes still don't meet your needs, you have a couple of options. You can write your own jss-recipes. This usually involves establishing your own workflow, and writing the templates to support that. Implementing individual recipes becomes largely editing a handful of values in copies of these templates, 90% of which end up being the same.

Hint: many people have expressed a desire for JSSImporter to upload objects to multiple JSSs. The trick to doing this is to use your own jss recipes that have one JSSImporter processor for each JSS. You will need to override the `JSS_URL` and any other settings needed in-between JSSImporter invocations in the recipe.

If this still does not meet your needs, it's time to dig into python-jss and write a solution that does.
