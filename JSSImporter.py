#!/usr/bin/python
# Copyright 2014, 2015 Shea Craig
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
#
# See the License for the specific language governing permissions and
# limitations under the License.
"""See docstring for JSSImporter class."""


from collections import OrderedDict
from distutils.version import StrictVersion
import os
import shutil
import sys
from xml.etree import ElementTree

import jss
# Ensure that python-jss dependency is at minimum version
try:
    from jss import __version__ as PYTHON_JSS_VERSION
except ImportError:
    PYTHON_JSS_VERSION = "0.0.0"
from autopkglib import Processor, ProcessorError


__all__ = ["JSSImporter"]
__version__ = "0.5.1"
REQUIRED_PYTHON_JSS_VERSION = StrictVersion("1.4.0")


class JSSImporter(Processor):
    """Uploads packages to configured Casper distribution points.

    Optionally, creates supporting categories, computer groups, policy,
    self service icon, extension attributes, and scripts.

    File paths to support files are searched for in order:
        1. Path as specified.
        2. The parent folder of the path.
        3. First ParentRecipe's folder.
        4. First ParentRecipe's parent folder.
        5. Second ParentRecipe's folder.
        6. Second ParentRecipe's parent folder.
        7. Nth ParentRecipe's folder.
        8. Nth ParentRecipe's parent folder.

    This search-path method is primarily in place to support using
    recipe overrides. It applies to policy_template, computer group
    templates, self_service_icon, script templates, and extension
    attribute templates. It allows users to avoid having to copy the
    file to the override directory for each recipe.
    """
    input_variables = {
        "prod_name": {
            "required": True,
            "description": "Name of the product.",
        },
        "jss_inventory_name": {
            "required": False,
            "description":
                "Smart groups using the 'Application Title' " "criteria need "
                "to specify the app's filename, as registered in the JSS's "
                "inventory. If this variable is left out, it will generate an "
                "'Application Title' by adding '.app' to the prod_name, e.g. "
                "prod_name='Google Chrome', calculated "
                "jss_inventory_name='Google Chrome.app'. If you need to "
                "override this behavior, specify the correct name with this "
                "variable.",
        },
        "pkg_path": {
            "required": True,
            "description":
                "Path to a pkg or dmg to import - provided by "
                "previous pkg recipe/processor.",
        },
        "version": {
            "required": True,
            "description":
                "Version number of software to import - provided "
                "by previous pkg recipe/processor.",
        },
        "JSS_REPOS": {
            "required": False,
            "description":
                "Array of dicts for each intended distribution point. Each "
                "distribution point type requires slightly different "
                "configuration keys and data. Please consult the "
                "documentation. ",
            "default": [],
        },
        "JSS_URL": {
            "required": True,
            "description":
                "URL to a JSS that api the user has write access "
                "to, optionally set as a key in the com.github.autopkg preference "
                "file.",
        },
        "API_USERNAME": {
            "required": True,
            "description":
                "Username of account with appropriate access to "
                "jss, optionally set as a key in the com.github.autopkg "
                "preference file.",
        },
        "API_PASSWORD": {
            "required": True,
            "description":
                "Password of api user, optionally set as a key in "
                "the com.github.autopkg preference file.",
        },
        "JSS_VERIFY_SSL": {
            "required": False,
            "description":
                "If set to False, SSL verification in communication"
                " with the JSS will be skipped. Defaults to 'True'.",
            "default": True,
        },
        "JSS_MIGRATED": {
            "required": False,
            "description":
                "Set to True if you use an AFP or SMB share *and* "
                "you have migrated your JSS. Defaults to 'False'.",
            "default": False,
        },
        "JSS_SUPPRESS_WARNINGS": {
            "required": False,
            "description":
                "Determines whether to suppress urllib3 warnings. "
                "If you choose not to verify SSL with JSS_VERIFY_SSL, urllib3 "
                "throws warnings for each of the numerous requests "
                "JSSImporter makes. If you would like to see them, set to "
                "'False'. Defaults to 'True'.",
            "default": True,
        },
        "category": {
            "required": False,
            "description":
                "Category to create/associate imported app "
                "package with. Defaults to 'No category assigned'.",
        },
        "policy_category": {
            "required": False,
            "description":
                "Category to create/associate policy with. Defaults"
                " to 'No category assigned'.",
        },
        "os_requirements": {
            "required": False,
            "description":
                "Comma-seperated list of OS version numbers to "
                "allow. Corresponds to the OS Requirements field for "
                "packages. The character 'x' may be used as a wildcard, as "
                "in '10.9.x'",
            "default": ""
        },
        "package_info": {
            "required": False,
            "description": "Text to apply to the package's Info field.",
            "default": ""
        },
        "package_notes": {
            "required": False,
            "description": "Text to apply to the package's Notes field.",
            "default": ""
        },
        "groups": {
            "required": False,
            "description":
                "Array of group dictionaries. Wrap each group in a "
                "dictionary. Group keys include 'name' (Name of the group to "
                "use, required), 'smart' (Boolean: static group=False, smart "
                "group=True, default is False, not required), and "
                "template_path' (string: path to template file to use for "
                "group, required for smart groups, invalid for static groups)",
        },
        "scripts": {
            "required": False,
            "description":
                "Array of script dictionaries. Wrap each script in "
                "a dictionary. Script keys include 'name' (Name of the script "
                "to use, required), 'template_path' (string: path to template "
                "file to" " use for script, required)",
        },
        "extension_attributes": {
            "required": False,
            "description":
                "Array of extension attribute dictionaries. Wrap each "
                "extension attribute in a dictionary. Script keys include: "
                "'ext_attribute_path' (string: path to extension attribute "
                "file.)",
        },
        "policy_template": {
            "required": False,
            "description":
                "Filename of policy template file. If key is "
                "missing or value is blank, policy creation will be skipped.",
            "default": "",
        },
        "self_service_description": {
            "required": False,
            "description":
                "Use to populate the %SELF_SERVICE_DESCRIPTION% variable for "
                "use in templates. Primary use is for filling the info button "
                "text in Self Service, but could be used elsewhere.",
            "default": "",
        },
        "self_service_icon": {
            "required": False,
            "description":
                "Path to an icon file. Use to add an icon to a "
                "self-service enabled policy. Because of the way Casper "
                "handles this, the JSSImporter will only upload if the icon's "
                "filename is different than the one set on the policy (if it "
                "even exists). Please see the README for more information.",
            "default": "",
        },
        "site_id": {
            "required": False,
            "description": "ID of the target Site",
        },
        "site_name": {
            "required": False,
            "description": "Name of the target Site",
        },
    }
    output_variables = {
        "jss_changed_objects": {
            "description": "Dictionary of added or changed values."
        },
        "jss_importer_summary_result": {
            "description": "Description of interesting results."
        },
    }
    description = __doc__

    def __init__(self, env=None, infile=None, outfile=None):
        """Sets attributes here."""
        super(JSSImporter, self).__init__(env, infile, outfile)
        self.jss = None
        self.pkg_name = None
        self.prod_name = None
        self.version = None
        self.category = None
        self.policy_category = None
        self.package = None
        self.replace_dict = {}
        self.extattrs = None
        self.groups = None
        self.scripts = None
        self.policy = None

    def main(self):
        """Main processor code."""
        # Ensure we have the right version of python-jss
        python_jss_version = StrictVersion(PYTHON_JSS_VERSION)
        if python_jss_version < REQUIRED_PYTHON_JSS_VERSION:
            self.output("Requires python-jss version: %s. Installed: %s" %
                        (REQUIRED_PYTHON_JSS_VERSION, python_jss_version))
            sys.exit()

        # clear any pre-existing summary result
        if "jss_importer_summary_result" in self.env:
            del self.env["jss_importer_summary_result"]

        # pull jss recipe-specific args, prep api auth
        repo_url = self.env["JSS_URL"]
        auth_user = self.env["API_USERNAME"]
        auth_pass = self.env["API_PASSWORD"]
        ssl_verify = self.env["JSS_VERIFY_SSL"]
        jss_migrated = self.env["JSS_MIGRATED"]
        suppress_warnings = self.env["JSS_SUPPRESS_WARNINGS"]
        repos = self.env["JSS_REPOS"]
        self.jss = jss.JSS(url=repo_url, user=auth_user, password=auth_pass,
                           ssl_verify=ssl_verify, repo_prefs=repos,
                           jss_migrated=jss_migrated,
                           suppress_warnings=suppress_warnings)
        self.pkg_name = os.path.basename(self.env["pkg_path"])
        self.prod_name = self.env["prod_name"]
        self.version = self.env["version"]

        # Build and init jss_changed_objects
        self.init_jss_changed_objects()

        self.category = self.handle_category("category")
        self.policy_category = self.handle_category("policy_category")

        # Get our DPs read for copying.
        self.jss.distribution_points.mount()
        self.package = self.handle_package()
        # Build our text replacement dictionary
        self.build_replace_dict()

        self.extattrs = self.handle_extension_attributes()
        self.groups = self.handle_groups()
        self.scripts = self.handle_scripts()
        self.policy = self.handle_policy()
        self.handle_icon()
        # Done with DPs, unmount them.
        self.jss.distribution_points.umount()

        self.summarize()

    def init_jss_changed_objects(self):
        """Build a dictionary to track changes to JSS objects for
        later reporting.

        """
        self.env["jss_changed_objects"] = {
            "jss_repo_updated": [],
            "jss_category_added": [],
            "jss_package_added": [],
            "jss_package_updated": [],
            "jss_group_added": [],
            "jss_group_updated": [],
            "jss_script_added": [],
            "jss_script_updated": [],
            "jss_extension_attribute_added": [],
            "jss_extension_attribute_updated": [],
            "jss_policy_added": [],
            "jss_policy_updated": [],
            "jss_icon_uploaded": []}

    def handle_category(self, category_type):
        """Ensure a category is present."""
        if self.env.get(category_type):
            category_name = self.env.get(category_type)
            try:
                category = self.jss.Category(category_name)
                self.output("Category type: %s-'%s' already exists "
                            "according to JSS, moving on..." %
                            (category_type, category_name))
            except jss.JSSGetError:
                # Category doesn't exist
                category = jss.Category(self.jss, category_name)
                category.save()
                self.output(
                    "Category type: %s-'%s' created." % (category_type,
                                                         category_name))
                self.env["jss_changed_objects"]["jss_category_added"].append(
                    category_name)
        else:
            category = None

        return category

    def handle_package(self):
        """Creates or updates a package object on the jss, then uploads
        a package file to the configured distribution points.

        This will only upload a package if a file with the same name
        does not already exist on a DP. If you need to force a
        re-upload, you must delete the package on the DP first.

        Further, if you are using a JDS, it will only upload a package
        if a package object with a filename matching the AutoPkg
        filename does not exist. If you need to force a re-upload to a
        JDS, please delete the package object through the web interface
        first.

        """
        # Skip package handling if there is no package or repos.
        if self.env["JSS_REPOS"] and self.env["pkg_path"] != "":
            os_requirements = self.env.get("os_requirements")
            package_info = self.env.get("package_info")
            package_notes = self.env.get("package_notes")
            # See if the package is non-flat (requires zipping prior to
            # upload).
            if os.path.isdir(self.env["pkg_path"]):
                shutil.make_archive(self.env["pkg_path"], "zip",
                                    os.path.dirname(self.env["pkg_path"]),
                                    self.pkg_name)
                self.env["pkg_path"] += ".zip"
                self.pkg_name += ".zip"

            try:
                package = self.jss.Package(self.pkg_name)
                self.output("Pkg-object already exists according to JSS, "
                            "moving on...")
            except jss.JSSGetError:
                # Package doesn't exist
                package = jss.Package(self.jss, self.pkg_name)

            pkg_update = (self.env[
                "jss_changed_objects"]["jss_package_updated"])
            if self.category is not None:
                cat_name = self.category.name
            else:
                cat_name = ""
            self.update_object(cat_name, package, "category", pkg_update)
            self.update_object(os_requirements, package, "os_requirements",
                               pkg_update)
            self.update_object(package_info, package, "info", pkg_update)
            self.update_object(package_notes, package, "notes", pkg_update)

            # Ensure packages are on distribution point(s)

            # If we had to make a new package object, we know we need to
            # copy the package file, regardless of DP type. This solves
            # the issue regarding the JDS.exists() method: See
            # python-jss docs for info.  The problem with this method is
            # that if you cancel an AutoPkg run and the package object
            # has been created, but not uploaded, you will need to
            # delete the package object from the JSS before running a
            # recipe again or it won't upload the package file.
            #
            # Passes the id of the newly created package object so JDS'
            # will upload to the correct package object. Ignored by
            # AFP/SMB.
            if self.env["jss_changed_objects"]["jss_package_added"]:
                self.copy(self.env["pkg_path"], id_=package.id)
            # For AFP/SMB shares, we still want to see if the package
            # exists.  If it's missing, copy it!
            elif not self.jss.distribution_points.exists(
                    os.path.basename(self.env["pkg_path"])):
                self.copy(self.env["pkg_path"])
            else:
                self.output("Package upload not needed.")
        else:
            package = None
            self.output("Package upload and object update skipped. If this is "
                        "a mistake, ensure you have JSS_REPOS configured.")

        return package

    def handle_extension_attributes(self):
        """Add extension attributes if needed."""
        extattrs = self.env.get("extension_attributes")
        results = []
        if extattrs:
            for extattr in extattrs:
                extattr_object = self.update_or_create_new(
                    jss.ComputerExtensionAttribute,
                    extattr["ext_attribute_path"],
                    update_env="jss_extension_attribute_added",
                    added_env="jss_extension_attribute_updated")

                results.append(extattr_object)
        return results

    def handle_groups(self):
        """Manage group existence and creation."""
        groups = self.env.get("groups")
        computer_groups = []
        if groups:
            for group in groups:
                if self.validate_input_var(group):
                    is_smart = group.get("smart", False)
                    if is_smart:
                        computer_group = self.add_or_updatesmart_group(group)
                    else:
                        computer_group = \
                            self.add_or_updatestatic_group(group)

                    computer_groups.append(computer_group)

        return computer_groups

    def handle_scripts(self):
        """Add scripts if needed."""
        scripts = self.env.get("scripts")
        results = []
        if scripts:
            for script in scripts:
                script_file = self.find_file_in_search_path(
                    script["name"])
                script_object = self.update_or_create_new(
                    jss.Script,
                    script["template_path"],
                    os.path.basename(script_file),
                    added_env="jss_script_added",
                    update_env="jss_script_updated")

                # Copy the script to the distribution points.
                self.copy(script_file, id_=script_object.id)
                results.append(script_object)

        return results

    def handle_policy(self):
        """Create or update a policy."""
        if self.env.get("policy_template"):
            template_filename = self.env.get("policy_template")
            policy = self.update_or_create_new(
                jss.Policy, template_filename, update_env="jss_policy_updated",
                added_env="jss_policy_added")
        else:
            self.output("Policy creation not desired, moving on...")
            policy = None

        return policy

    def handle_icon(self):
        """Add self service icon if needed."""
        # Icons are tricky. The only way to add new ones is to use
        # FileUploads.  If you manually upload them, you can add them to
        # a policy to get their ID, but there is no way to query the JSS
        # to see what icons are available. Thus, icon handling involves
        # several cooperating methods.  If we just add an icon every
        # time we run a recipe, however, we end up with a ton of
        # redundent icons, and short of actually deleting them in the
        # sql database, there's no way to delete icons. So when we run,
        # we first check for an existing policy, and if it exists, copy
        # its icon XML, which is then added to the templated Policy. If
        # there is no icon information, but the recipe specifies one,
        # then FileUpload it up.

        # If no policy handling is desired, we can't upload an icon.
        if self.env.get("self_service_icon") and self.policy is not None:
            # Search through search-paths for icon file.
            icon_path = self.find_file_in_search_path(
                self.env["self_service_icon"])

            icon_filename = os.path.basename(icon_path)

            # Compare the filename in the policy to the one provided by
            # the recipe. If they don't match, we need to upload a new
            # icon.
            policy_filename = self.policy.findtext(
                "self_service/self_service_icon/filename")
            if not policy_filename == icon_filename:
                icon = jss.FileUpload(self.jss, "policies", "id", self.policy.id,
                                      icon_path)
                icon.save()
                self.env["jss_changed_objects"]["jss_icon_uploaded"].append(
                    icon_filename)
                self.output("Icon uploaded to JSS.")
            else:
                self.output("Icon matches existing icon, moving on...")

    def summarize(self):
        """If anything has been added or updated, report back to
        AutoPkg.

        """
        # Only summarize if something has happened.
        if [True for value in self.env["jss_changed_objects"].values()
                if value]:
            # Create a blank summary.
            self.env["jss_importer_summary_result"] = {
                "summary_text": "The following changes were made to the JSS:",
                "report_fields": ["Package", "Categories", "Groups", "Scripts",
                                  "Extension Attributes", "Policy", "Icon"],
                "data": {
                    "Package": "",
                    "Categories": "",
                    "Groups": "",
                    "Scripts": "",
                    "Extension Attributes": "",
                    "Policy": "",
                    "Icon": ""
                }
            }

            # Shortcut variables for lovely code conciseness
            changes = self.env["jss_changed_objects"]
            data = self.env["jss_importer_summary_result"]["data"]

            package = self.get_report_string(changes["jss_package_added"] +
                                             changes["jss_package_updated"])
            if package:
                data["Package"] = package

            policy = changes["jss_policy_updated"] + \
                changes["jss_policy_added"]
            if policy:
                data["Policy"] = self.get_report_string(policy)

            if changes["jss_icon_uploaded"]:
                data["Icon"] = os.path.basename(self.env["self_service_icon"])

            # Get nice strings for our list-types.
            if changes["jss_category_added"]:
                data["Categories"] = self.get_report_string(
                    changes["jss_category_added"])

            groups = changes["jss_group_updated"] + changes["jss_group_added"]
            if groups:
                data["Groups"] = self.get_report_string(groups)

            scripts = changes["jss_script_updated"] + \
                changes["jss_script_added"]
            if scripts:
                data["Scripts"] = self.get_report_string(scripts)

            extattrs = changes["jss_extension_attribute_updated"] + \
                changes["jss_extension_attribute_added"]
            if extattrs:
                data["Extension Attributes"] = self.get_report_string(extattrs)

    def update_object(self, data, obj, path, update):
        """Update an object if it differs.

        If a value differs between the recipe and the object, update
        the object to reflect the change, and add the object to a
        summary list.

        Args:
            data: Recipe string value to enforce.
            obj: JSSObject type to set data on.
            path: String path to desired XML.
            update: Summary list object to append obj to if something
                is changed.
        """
        if data != obj.findtext(path):
            obj.find(path).text = data
            obj.save()
            self.output("%s %s updated." % (
                str(obj.__class__).split(".")[-1][:-2], path))
            update.append(obj.name)

    def copy(self, source_item, id_=-1):
        """Copy a package or script using the JSS_REPOS preference."""
        self.output("Copying %s to all distribution points." % source_item)

        def output_copy_status(connection):
            """Output AutoPkg copying status."""
            self.output("Copying to %s" % connection["url"])

        self.jss.distribution_points.copy(source_item, id_=id_,
                                          pre_callback=output_copy_status)
        self.env["jss_changed_objects"]["jss_repo_updated"].append(
            os.path.basename(source_item))
        self.output("Copied %s" % source_item)

    def build_replace_dict(self):
        """Build dict of replacement values based on available input."""
        # First, add in AutoPkg's env, excluding types that don't make
        # sense:
        replace_dict = {key: val for key, val in self.env.items()
                        if val is not None and isinstance(val, basestring)}

        # Next, add in "official" and Legacy input variables.
        replace_dict["VERSION"] = self.version
        if self.package is not None:
            replace_dict["PKG_NAME"] = self.package.name
        replace_dict["PROD_NAME"] = self.env.get("prod_name")
        if self.env.get("site_id"):
            replace_dict["SITE_ID"] = self.env.get("site_id")
        if self.env.get("site_name"):
            replace_dict["SITE_NAME"] = self.env.get("site_name")
        replace_dict["SELF_SERVICE_DESCRIPTION"] = self.env.get(
            "self_service_description")
        replace_dict["SELF_SERVICE_ICON"] = self.env.get(
            "self_service_icon")
        # policy_category is not required, so set a default value if
        # absent.
        replace_dict["POLICY_CATEGORY"] = self.env.get(
            "policy_category") or "Unknown"

        # Some applications may have a product name that differs from
        # the name that the JSS uses for its "Application Title"
        # inventory field. If so, you can set it with the
        # jss_inventory_name input variable. If this variable is not
        # specified, it will just append .app, which is how most apps
        # work.
        if self.env.get("jss_inventory_name"):
            replace_dict["JSS_INVENTORY_NAME"] = self.env.get(
                "jss_inventory_name")
        else:
            replace_dict["JSS_INVENTORY_NAME"] = ("%s.app" %
                                                  self.env.get("prod_name"))
        self.replace_dict = replace_dict

    def update_or_create_new(self, obj_cls, template_path, name="",
                             added_env="", update_env=""):
        """Check for an existing object and update it, or create a new
        object.

        Args:
            obj_cls: The python-jss object class to work with.
            template_path:  String filename or path to the template
                file.  See get_templated_object() for more info.
            name: The name to use. Defaults to the "name" property of
                the templated object.
            added_env: The environment var to update if an object is
                added.
            update_env: The environment var to update if an object is
                updated.

        Returns:
            The recipe object after updating.
        """
        # Create a new object from the template
        recipe_object = self.get_templated_object(obj_cls, template_path)

        if not name:
            name = recipe_object.name

        # Check for an existing object with this name.
        existing_object = None
        try:
            existing_object = self.jss.factory.get_object(obj_cls, name)
        except jss.JSSGetError:
            pass

        # If object is a Policy, we need to inject scope, scripts,
        # package, and an icon.
        if obj_cls is jss.Policy:
            if existing_object is not None:
                # If this policy already exists, and it has an icon set,
                # copy its icon section to our template, as we have no
                # other way of getting this information.
                icon_xml = existing_object.find(
                    "self_service/self_service_icon")
                if icon_xml is not None:
                    self.add_icon_to_policy(recipe_object, icon_xml)
            self.add_scope_to_policy(recipe_object)
            self.add_scripts_to_policy(recipe_object)
            self.add_package_to_policy(recipe_object)

        if existing_object is not None:
            # Update the existing object.
            url = existing_object.get_object_url()
            self.jss.put(url, recipe_object)
            # Retrieve the updated XML.
            recipe_object = self.jss.factory.get_object(obj_cls, name)
            self.output("%s: %s updated." % (obj_cls.__name__, name))
            if update_env:
                self.env["jss_changed_objects"][update_env].append(name)
        else:
            # Object doesn't exist yet.
            recipe_object.save()
            self.output("%s: %s created." % (obj_cls.__name__, name))
            if added_env:
                self.env["jss_changed_objects"][added_env].append(name)

        return recipe_object

    def get_templated_object(self, obj_cls, template_path):
        """Return an object based on a template located in search path.

        Args:
            obj_cls: JSSObject class (for the purposes of JSSIMporter a
                Policy or a ComputerGroup)
            template_path: String filename or path to template file.
                See find_file_in_search_path() for more information on
                file searching.

        Returns:
            A JSS Object created based on the template,
            post-text-replacement.
        """
        final_template_path = self.find_file_in_search_path(template_path)

        # Open and return a new object.
        with open(final_template_path, "r") as template_file:
            text = template_file.read()
        template = self.replace_text(text, self.replace_dict)
        return obj_cls.from_string(self.jss, template)

    def find_file_in_search_path(self, path):
        """Search search_paths for the first existing instance of path.

        Searches, in order, through the following directories
        until a matching file is found:
            1. Path as specified.
            2. The parent folder of the path.
            3. First ParentRecipe's folder.
            4. First ParentRecipe's parent folder.
            5. Second ParentRecipe's folder.
            6. Second ParentRecipe's parent folder.
            7. Nth ParentRecipe's folder.
            8. Nth ParentRecipe's parent folder.

        This search-path method is primarily in place to
        support using recipe overrides. It allows users to avoid having
        to copy templates, icons, etc, to the override directory.

        Args:
            obj_cls: JSSObject class (for the purposes of JSSIMporter a
                Policy or a ComputerGroup)
            path: String filename or path to file.

                If path is just a filename, path is assumed to
                be self.env["RECIPE_DIR"].

        Returns:
            Absolute path to the first match in search paths.

        Raises:
            ProcessorError if none of the above files exist.
        """
        # Ensure input is expanded.
        path = os.path.expanduser(path)
        # Check to see if path is a filename.
        if not os.path.dirname(path):
            # If so, assume that the file is meant to be in the recipe
            # directory.
            path = os.path.join(self.env["RECIPE_DIR"], path)

        filename = os.path.basename(path)
        parent_recipe_dirs = [os.path.dirname(parent) for parent in
                              self.env["PARENT_RECIPES"]]
        unique_parent_dirs = OrderedDict()
        for parent in parent_recipe_dirs:
            unique_parent_dirs[parent] = parent
        search_dirs = ([os.path.dirname(path)] + unique_parent_dirs.keys())

        tested = []
        final_path = ""
        # Look for the first file that exists in the search_dirs and
        # their parent folders.
        for search_dir in search_dirs:
            test_path = os.path.join(search_dir, filename)
            test_parent_folder_path = os.path.abspath(
                os.path.join(search_dir, "..", filename))
            if os.path.exists(test_path):
                final_path = test_path
            elif os.path.exists(test_parent_folder_path):
                final_path = test_parent_folder_path
            tested.append(test_path)
            tested.append(test_parent_folder_path)

            if final_path:
                self.output("Found file: %s" % final_path)
                break

        if not final_path:
            raise ProcessorError(
                "Unable to find file %s at any of the following locations: %s"
                % (filename, tested))

        return final_path

    def replace_text(self, text, replace_dict):
        """Substitute items in a text string.

        text: A string with embedded %tags%.
        replace_dict: A dict, where
            key: Corresponds to the % delimited tag in text.
            value: Text to swap in.

        """
        for key, value in replace_dict.iteritems():
            # Wrap our keys in % to match template tags.
            text = text.replace("%%%s%%" % key, value)
        return text

    def validate_input_var(self, var):
        """Validate the value before trying to add a group.

        Returns False if dictionary has invalid values, or True if it
        seems okay.

        """
        # Skipping non-string values:
        # Does group name or template have a replacement var
        # that has not been replaced?
        # Does the group have a blank value? (A blank value isn't really
        # invalid, but there's no need to process it further.)
        invalid = [False for value in var.values() if isinstance(value, str)
                   and (value.startswith("%") and value.endswith("%")) or not
                   value]
        if invalid:
            result = False
        else:
            result = True

        return result

    def add_or_updatesmart_group(self, group):
        """Given a group, either add a new group or update existing
        group.

        """
        # Build the template group object
        self.replace_dict["group_name"] = group["name"]
        if group.get("site_id"):
            self.replace_dict["site_id"] = group.get("site_id")
        if group.get("site_name"):
            self.replace_dict["site_name"] = group.get("site_name")
        computer_group = self.update_or_create_new(
            jss.ComputerGroup, group["template_path"],
            update_env="jss_group_updated", added_env="jss_group_added")

        return computer_group

    def add_or_updatestatic_group(self, group):
        """Given a group, either add a new group or update existing
        group.

        """
        # Check for pre-existing group first
        try:
            computer_group = self.jss.ComputerGroup(group["name"])
            self.output("Computer Group: %s already exists." %
                        computer_group.name)
        except jss.JSSGetError:
            computer_group = jss.ComputerGroup(self.jss, group["name"])
            computer_group.save()
            self.output("Computer Group: %s created." % computer_group.name)
            self.env["jss_changed_objects"]["jss_group_added"].append(
                computer_group.name)

        return computer_group

    def add_scope_to_policy(self, policy_template):
        """Incorporate scoping groups into a policy."""
        computer_groups_element = self.ensure_xml_structure(
            policy_template, "scope/computer_groups")
        for group in self.groups:
            policy_template.add_object_to_path(group, computer_groups_element)

    def add_scripts_to_policy(self, policy_template):
        """Incorporate scripts into a policy."""
        scripts_element = self.ensure_xml_structure(policy_template, "scripts")
        for script in self.scripts:
            script_element = policy_template.add_object_to_path(
                script, scripts_element)
            priority = ElementTree.SubElement(script_element, "priority")
            priority.text = script.findtext("priority")

    def add_package_to_policy(self, policy_template):
        """Add a package to a self service policy."""
        if self.package is not None:
            self.ensure_xml_structure(policy_template,
                                      "package_configuration/packages")
            policy_template.add_package(self.package)

    def add_icon_to_policy(self, policy_template, icon_xml):
        """Add an icon to a self service policy."""
        self.ensure_xml_structure(policy_template, "self_service")
        self_service = policy_template.find("self_service")
        self_service.append(icon_xml)

    def ensure_xml_structure(self, element, path):
        """Given an XML path and a starting element, ensure that all
        tiers of the hierarchy exist.

        """
        search, _, path = path.partition("/")
        if search:
            if element.find(search) is None:
                ElementTree.SubElement(element, search)
            return self.ensure_xml_structure(element.find(search), path)
        return element

    def get_report_string(self, items):
        """Return a nice human-readable string from a list of JSS
        objects.

        """
        return ", ".join(set(items))


if __name__ == "__main__":
    processor = JSSImporter()   # pylint: disable=invalid-name
    processor.execute_shell()
