#!/usr/bin/python
# Copyright 2014-2017 Shea G. Craig
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

from __future__ import absolute_import
import importlib
import os
import sys
import time
from collections import OrderedDict
from distutils.version import StrictVersion
from zipfile import ZipFile, ZIP_DEFLATED
from xml.sax.saxutils import escape

# ElementTree monkey patch borrowed with love from Matteo Ferla.
# https://blog.matteoferla.com/2019/02/uniprot-xml-and-python-elementtree.html
sys.modules.pop("xml.etree.ElementTree", None)
sys.modules["_elementtree"] = None
ElementTree = importlib.import_module("xml.etree.ElementTree")

sys.path.insert(0, "/Library/AutoPkg/JSSImporter")

import jss  # pylint: disable=import-error

# Ensure that python-jss dependency is at minimum version
try:
    from jss import __version__ as PYTHON_JSS_VERSION
except ImportError:
    PYTHON_JSS_VERSION = "0.0.0"

from autopkglib import Processor, ProcessorError  # pylint: disable=import-error


__all__ = ["JSSImporter"]
__version__ = "1.1.2"
REQUIRED_PYTHON_JSS_VERSION = StrictVersion("2.1.0")

# Map Python 2 basestring type for Python 3.
if sys.version_info.major == 3:
    basestring = str


# pylint: disable=too-many-instance-attributes, too-many-public-methods
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
        "prod_name": {"required": True, "description": "Name of the product.",},
        "jss_inventory_name": {
            "required": False,
            "description": "Smart groups using the 'Application Title' "
            "criteria need "
            "to specify the app's filename, as registered in the JSS's "
            "inventory. If this variable is left out, it will generate an "
            "'Application Title' by adding '.app' to the prod_name, e.g. "
            "prod_name='Google Chrome', calculated "
            "jss_inventory_name='Google Chrome.app'. If you need to "
            "override this behavior, specify the correct name with this "
            "variable.",
        },
        "pkg_path": {
            "required": False,
            "description": "Path to a pkg or dmg to import - provided by "
            "previous pkg recipe/processor.",
            "default": "",
        },
        "version": {
            "required": False,
            "description": "Version number of software to import - usually provided "
            "by previous pkg recipe/processor, but if not, defaults to "
            "'0.0.0.0'. ",
            "default": "0.0.0.0",
        },
        "JSS_REPOS": {
            "required": False,
            "description": "Array of dicts for each intended distribution point. Each "
            "distribution point type requires slightly different "
            "configuration keys and data. Please consult the "
            "documentation. ",
            "default": [],
        },
        "JSS_URL": {
            "required": True,
            "description": "URL to a Jamf Pro server that the API user has write access "
            "to, optionally set as a key in the com.github.autopkg "
            "preference file.",
        },
        "API_USERNAME": {
            "required": True,
            "description": "Username of account with appropriate access to "
            "jss, optionally set as a key in the com.github.autopkg "
            "preference file.",
        },
        "API_PASSWORD": {
            "required": True,
            "description": "Password of api user, optionally set as a key in "
            "the com.github.autopkg preference file.",
        },
        "JSS_VERIFY_SSL": {
            "required": False,
            "description": "If set to False, SSL verification in communication "
            "with the Jamf Pro server will be skipped. Defaults to 'True'.",
            "default": True,
        },
        "JSS_SUPPRESS_WARNINGS": {
            "required": False,
            "description": "Determines whether to suppress urllib3 warnings. "
            "If you choose not to verify SSL with JSS_VERIFY_SSL, urllib3 "
            "throws warnings for each of the numerous requests "
            "JSSImporter makes. If you would like to see them, set to "
            "'False'. Defaults to 'True'.",
            "default": True,
        },
        "category": {
            "required": False,
            "description": "Category to create/associate imported app "
            "package with. Defaults to 'No category assigned'.",
        },
        "policy_category": {
            "required": False,
            "description": "Category to create/associate policy with. Defaults"
            " to 'No category assigned'.",
        },
        "force_policy_state": {
            "required": False,
            "description": "If set to False JSSImporter will not override the policy "
            "enabled state. This allows creating new policies in a default "
            "state and then going and manually enabling them in the Jamf Pro server. "
            "Boolean, defaults to 'True'",
            "default": True,
        },
        "os_requirements": {
            "required": False,
            "description": "Comma-separated list of OS version numbers to "
            "allow. Corresponds to the OS Requirements field for "
            "packages. The character 'x' may be used as a wildcard, as "
            "in '10.9.x'",
            "default": "",
        },
        "package_info": {
            "required": False,
            "description": "Text to apply to the package's Info field.",
            "default": "",
        },
        "package_notes": {
            "required": False,
            "description": "Text to apply to the package's Notes field.",
            "default": "",
        },
        "package_priority": {
            "required": False,
            "description": "Priority to use for deploying or uninstalling the "
            "package. Value between 1-20. Defaults to '10'",
            "default": "10",
        },
        "package_reboot": {
            "required": False,
            "description": "Computers must be restarted after installing the package "
            "Boolean. Defaults to 'False'",
            "default": "False",
        },
        "package_boot_volume_required": {
            "required": False,
            "description": "Ensure that the package is installed on the boot drive "
            "after imaging. Boolean. Defaults to 'True'",
            "default": "True",
        },
        "groups": {
            "required": False,
            "description": "Array of group dictionaries. Wrap each group in a "
            "dictionary. Group keys include 'name' (Name of the group to "
            "use, required), 'smart' (Boolean: static group=False, smart "
            "group=True, default is False, not required), "
            "template_path' (string: path to template file to use for "
            "group, required for smart groups, invalid for static groups), "
            "and 'do_update' (Boolean: default is True, not required)",
        },
        "exclusion_groups": {
            "required": False,
            "description": "Array of group dictionaries. Wrap each group in a "
            "dictionary. Group keys include 'name' (Name of the group to "
            "use, required), 'smart' (Boolean: static group=False, smart "
            "group=True, default is False, not required), and "
            "template_path' (string: path to template file to use for "
            "group, required for smart groups, invalid for static groups), "
            "and 'do_update' (Boolean: default is True, not required)",
        },
        "scripts": {
            "required": False,
            "description": "Array of script dictionaries. Wrap each script in "
            "a dictionary. Script keys include 'name' (Name of the script "
            "to use, required), 'template_path' (string: path to template "
            "file to use for script, required)",
        },
        "extension_attributes": {
            "required": False,
            "description": "Array of extension attribute dictionaries. Wrap each "
            "extension attribute in a dictionary. Script keys include: "
            "'ext_attribute_path' (string: path to extension attribute "
            "file.)",
        },
        "policy_template": {
            "required": False,
            "description": "Filename of policy template file. If key is "
            "missing or value is blank, policy creation will be skipped.",
            "default": "",
        },
        "policy_action_type": {
            "required": False,
            "description": "Type of policy 'package_configuration' to perform. Must be "
            "one of 'Install', 'Cache', 'Install Cached'.",
            "default": "Install",
        },
        "self_service_description": {
            "required": False,
            "description": "Use to populate the %SELF_SERVICE_DESCRIPTION% variable for "
            "use in templates. Primary use is for filling the info button "
            "text in Self Service, but could be used elsewhere.",
            "default": "",
        },
        "self_service_icon": {
            "required": False,
            "description": "Path to an icon file. Use to add an icon to a "
            "self-service enabled policy. Because of the way Casper "
            "handles this, the JSSImporter will only upload if the icon's "
            "filename is different than the one set on the policy (if it "
            "even exists). Please see the README for more information.",
            "default": "",
        },
        "site_id": {"required": False, "description": "ID of the target Site",},
        "site_name": {"required": False, "description": "Name of the target Site",},
        "STOP_IF_NO_JSS_UPLOAD": {
            "required": False,
            "default": True,
            "description": (
                "If True, the processor will stop after verifying that "
                "a PKG upload was not required since a PKG of the same name "
                "is already present on the server"
            ),
        },
        "skip_scope": {
            "required": False,
            "default": False,
            "description": (
                "If True, policy scope will not be updated. By default group "
                "and policy updates are coupled together. This allows group "
                "updates without updating or overwriting policy scope."
            ),
        },
        "skip_scripts": {
            "required": False,
            "default": False,
            "description": "If True, policy scripts will not be updated.",
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
        self.exclusion_groups = None
        self.scripts = None
        self.policy = None
        self.upload_needed = False

    def create_jss(self):
        """Create a JSS object for API calls"""
        kwargs = {
            "url": self.env["JSS_URL"],
            "user": self.env["API_USERNAME"],
            "password": self.env["API_PASSWORD"],
            "ssl_verify": self.env["JSS_VERIFY_SSL"],
            "repo_prefs": self.env["JSS_REPOS"],
        }
        self.jss = jss.JSS(**kwargs)
        if self.env.get("verbose", 1) >= 4:
            self.jss.verbose = True

    def init_jss_changed_objects(self):
        """Build a dictionary to track changes to JSS objects."""
        keys = (
            "jss_repo_updated",
            "jss_category_added",
            "jss_package_added",
            "jss_package_updated",
            "jss_group_added",
            "jss_group_updated",
            "jss_script_added",
            "jss_script_updated",
            "jss_extension_attribute_added",
            "jss_extension_attribute_updated",
            "jss_policy_added",
            "jss_policy_updated",
            "jss_icon_uploaded",
        )
        self.env["jss_changed_objects"] = {key: [] for key in keys}

    def repo_type(self):
        """returns the type of repo"""
        if self.env["JSS_REPOS"]:
            try:
                repo = self.env["JSS_REPOS"][0]["type"]
            except KeyError:
                repo = "DP"
        else:
            return
        return repo

    def wait_for_id(self, obj_cls, obj_name):
        """wait for feedback that the object is there"""
        object = None
        search_method = getattr(self.jss, obj_cls.__name__)
        # limit time to wait to get a package ID.
        timeout = time.time() + 120
        while time.time() < timeout:
            try:
                object = search_method(obj_name)
                if object.id != 0:
                    self.output(
                        "{} ID '{}' verified on server".format(
                            obj_cls.__name__, object.id
                        ),
                        verbose_level=2,
                    )
                    self.upload_needed = True
                    return object
                else:
                    self.output(
                        "Waiting to get {} ID from server (reported: {})...".format(
                            obj_cls.__name__, object.id
                        ),
                        verbose_level=2,
                    )
                    time.sleep(10)
            except jss.GetError:
                self.output(
                    "Waiting to get {} ID from server (none reported)...".format(
                        obj_cls.__name__
                    ),
                    verbose_level=2,
                )
                time.sleep(10)

    def handle_category(self, category_type, category_name=None):
        """Ensure a category is present."""
        if self.env.get(category_type):
            category_name = self.env.get(category_type)

        if category_name is not None:
            try:
                category = self.jss.Category(category_name)
                category_name = category.name
                self.output(
                    "Category, type '{}', name '{}', already exists on the Jamf Pro server, "
                    "moving on...".format(category_type, category_name),
                    verbose_level=2,
                )
            except jss.GetError:
                # Category doesn't exist
                category = jss.Category(self.jss, category_name)
                category.save()
                self.wait_for_id(jss.Category, category)
                try:
                    category.id
                    self.output(
                        "Category, type '{}', name '{}', created.".format(
                            category_type, category_name
                        )
                    )
                    self.env["jss_changed_objects"]["jss_category_added"].append(
                        category_name
                    )
                except ValueError:
                    raise ProcessorError(
                        "Failed to get category ID from {}.".format(self.repo_type())
                    )
        else:
            category = None
        return category

    def handle_package(self, stop_if_no_upload):
        """Creates or updates, and copies a package object.

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
        pkg_path = self.env["pkg_path"]
        if self.repo_type() is None:
            self.output(
                "No repos are setup so JSSImporter cannot upload packages. "
                "If this is a mistake, check your JSS_REPOS array.",
                verbose_level=2,
            )
            return
        if pkg_path == "":
            self.output(
                "No 'pkg_path' key has been passed to the JSSImporter processor. "
                "Therefore, no package will be uploaded. ",
                verbose_level=2,
            )
            return

        # Ensure that `pkg_path` is valid.
        if not os.path.exists(pkg_path):
            raise ProcessorError(
                "JSSImporter can't find a package at '{}'!".format(pkg_path)
            )

        # See if the package is non-flat (requires zipping prior to
        # upload).
        if os.path.isdir(pkg_path):
            self.output("Package object is a bundle. Converting to zip...")
            pkg_path = self.zip_pkg_path(pkg_path)
            self.env["pkg_path"] = pkg_path
            # Make sure our change gets added back into the env for
            # visibility.
            self.pkg_name += ".zip"

        # now check if the package object already exists
        try:
            package = self.jss.Package(self.pkg_name)
            self.output("Package object already exists on the Jamf Pro server.")
            self.output(
                "Package ID: {}".format(package.id), verbose_level=2,
            )
            pkg_update = self.env["jss_changed_objects"]["jss_package_updated"]
            # for cloud DPs we must assume that the package object means there is an associated package
        except jss.GetError:
            # Package doesn't exist
            self.output("Package object does not already exist on the Jamf Pro server.")

            # for CDP or JDS types, the package has to be uploaded first to generate a package object
            # then we wait for the package ID, then we can continue to assign attributes to the package
            # object.
            if (
                self.repo_type() == "JDS"
                or self.repo_type() == "CDP"
                or self.repo_type() == "AWS"
            ):
                self.copy(pkg_path)
                package = self.wait_for_id(jss.Package, self.pkg_name)
                try:
                    package.id
                    pkg_update = self.env["jss_changed_objects"]["jss_package_added"]
                except ValueError:
                    raise ProcessorError(
                        "Failed to get Package ID from {}.".format(self.repo_type())
                    )

            elif (
                self.repo_type() == "DP"
                or self.repo_type() == "SMB"
                or self.repo_type() == "AFP"
                or self.repo_type() == "Local"
            ):
                # for AFP/SMB shares, we create the package object first and then copy the package
                # if it is not already there
                self.output("Creating Package object...")
                package = jss.Package(self.jss, self.pkg_name)
                pkg_update = self.env["jss_changed_objects"]["jss_package_added"]
            else:
                # repo type that is not supported
                raise ProcessorError(
                    "JSSImporter can't upload the Package at '{}'! Repo type {} is not supported. Please reconfigure your JSSImporter prefs.".format(
                        pkg_path, self.repo_type()
                    )
                )

        # For local DPs we check that the package is already on the distribution point and upload it if not
        if (
            self.repo_type() == "DP"
            or self.repo_type() == "SMB"
            or self.repo_type() == "AFP"
            or self.repo_type() == "Local"
        ):
            if self.jss.distribution_points.exists(os.path.basename(pkg_path)):
                self.output("Package upload not required.")
                self.upload_needed = False
            else:
                self.copy(pkg_path)
                self.output(
                    "Package {} uploaded to distribution point.".format(self.pkg_name)
                )
                self.upload_needed = True

        # only update the package object if an upload ad was carried out
        if stop_if_no_upload != "False" and not self.upload_needed:
            self.output(
                "Not overwriting policy as upload requirement is determined as False, "
                "and STOP_IF_NO_JSS_UPLOAD is not set to False."
            )
            self.env["stop_processing_recipe"] = True
            return
        elif not self.upload_needed:
            self.output(
                "Overwriting policy although upload requirement is determined as False, "
                "because STOP_IF_NO_JSS_UPLOAD is set to False."
            )

        # now update the package object
        os_requirements = self.env.get("os_requirements")
        package_info = self.env.get("package_info")
        package_notes = self.env.get("package_notes")
        package_priority = self.env.get("package_priority")
        package_reboot = self.env.get("package_reboot")
        package_boot_volume_required = self.env.get("package_boot_volume_required")

        if self.category is not None:
            cat_name = self.category.name
        else:
            cat_name = ""
        if (
            self.repo_type() == "JDS"
            or self.repo_type() == "CDP"
            or self.repo_type() == "AWS"
        ):
            self.wait_for_id(jss.Package, self.pkg_name)
            try:
                package.id
                pkg_update = self.env["jss_changed_objects"]["jss_package_added"]
            except ValueError:
                raise ProcessorError(
                    "Failed to get Package ID from {}.".format(self.repo_type())
                )
        self.update_object(cat_name, package, "category", pkg_update)
        self.update_object(os_requirements, package, "os_requirements", pkg_update)
        self.update_object(package_info, package, "info", pkg_update)
        self.update_object(package_notes, package, "notes", pkg_update)
        self.update_object(package_priority, package, "priority", pkg_update)
        self.update_object(package_reboot, package, "reboot_required", pkg_update)
        self.update_object(
            package_boot_volume_required, package, "boot_volume_required", pkg_update
        )
        return package

    def zip_pkg_path(self, path):
        """Add files from path to a zip file handle.

        Args:
            path (str): Path to folder to zip.

        Returns:
            (str) name of resulting zip file.
        """
        zip_name = "{}.zip".format(path)

        with ZipFile(zip_name, "w", ZIP_DEFLATED, allowZip64=True) as zip_handle:

            for root, _, files in os.walk(path):
                for member in files:
                    zip_handle.write(os.path.join(root, member))

            self.output("Closing: {}".format(zip_name))

        return zip_name

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
                    added_env="jss_extension_attribute_updated",
                )

                results.append(extattr_object)
        return results

    def handle_groups(self, groups):
        """Manage group existence and creation."""
        computer_groups = []
        if groups:
            for group in groups:
                self.output(
                    "Computer Group to process: {}".format(group["name"]),
                    verbose_level=3,
                )
                if self.validate_input_var(group):
                    is_smart = group.get("smart", False)
                    if is_smart:
                        computer_group = self.add_or_update_smart_group(group)
                    else:
                        computer_group = self.add_or_update_static_group(group)

                    computer_groups.append(computer_group)

        return computer_groups

    def handle_scripts(self):
        """Add scripts if needed."""
        scripts = self.env.get("scripts")
        results = []
        if scripts:
            for script in scripts:
                self.output(
                    "Looking for Script file {}...".format(script["name"]),
                    verbose_level=2,
                )
                script_file = self.find_file_in_search_path(script["name"])
                try:
                    with open(script_file) as script_handle:
                        script_contents = script_handle.read()
                except IOError:
                    raise ProcessorError(
                        "Script '{}' could not be read!".format(script_file)
                    )

                script_object = self.update_or_create_new(
                    jss.Script,
                    script["template_path"],
                    os.path.basename(script_file),
                    added_env="jss_script_added",
                    update_env="jss_script_updated",
                    script_contents=script_contents,
                )

                results.append(script_object)

        return results

    def handle_policy(self):
        """Create or update a policy."""
        if self.env.get("policy_template"):
            template_filename = self.env.get("policy_template")
            policy = self.update_or_create_new(
                jss.Policy,
                template_filename,
                update_env="jss_policy_updated",
                added_env="jss_policy_added",
            )
            self.output(
                "Policy object: {}".format(policy.id), verbose_level=3,
            )
        else:
            self.output("Policy creation not desired, moving on...")
            policy = None
        return policy

    def handle_icon(self):
        """Add self service icon if needed."""
        # Icons are tricky. The only way to add new ones is to use
        # FileUploads.  If you manually upload them, you can add them to
        # a policy to get their ID, but there is no way to query the Jamf Pro server
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
            self.output(
                "Looking for Icon file {}...".format(
                    self.env["self_service_icon"], verbose_level=2,
                )
            )
            icon_path = self.find_file_in_search_path(self.env["self_service_icon"])
            icon_filename = os.path.basename(icon_path)

            # Compare the filename in the policy to the one provided by
            # the recipe. If they don't match, we need to upload a new
            # icon.
            policy_filename = self.policy.findtext(
                "self_service/self_service_icon/filename"
            )
            if not policy_filename == icon_filename:
                self.output(
                    "Icon name in existing policy: {}".format(policy_filename),
                    verbose_level=2,
                )
                icon = jss.FileUpload(
                    self.jss, "policies", "id", self.policy.id, icon_path
                )
                icon.save()
                self.env["jss_changed_objects"]["jss_icon_uploaded"].append(
                    icon_filename
                )
                self.output("Icon uploaded to the Jamf Pro server.")
            else:
                self.output("Icon matches existing icon, moving on...")

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
            self.output(
                "{} '{}' updated.".format(str(obj.__class__).split(".")[-1][:-2], path)
            )
            update.append(obj.name)

    def copy(self, source_item, id_=-1):
        """Copy a package or script using the JSS_REPOS preference."""
        self.output("Copying {} to all distribution points.".format(source_item))

        def output_copy_status(connection):
            """Output AutoPkg copying status."""
            self.output("Copying to {}".format(connection["url"]))

        self.jss.distribution_points.copy(
            source_item, id_=id_, pre_callback=output_copy_status
        )
        self.env["jss_changed_objects"]["jss_repo_updated"].append(
            os.path.basename(source_item)
        )
        self.output("Copied '{}'".format(source_item))

    def build_replace_dict(self):
        """Build dict of replacement values based on available input."""
        # First, add in AutoPkg's env, excluding types that don't make
        # sense:
        replace_dict = {
            key: val
            for key, val in self.env.items()
            if val is not None and isinstance(val, basestring)
        }

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
            "self_service_description"
        )
        replace_dict["SELF_SERVICE_ICON"] = self.env.get("self_service_icon")
        # policy_category is not required, so set a default value if
        # absent.
        replace_dict["POLICY_CATEGORY"] = self.env.get("policy_category") or "Unknown"

        # Some applications may have a product name that differs from
        # the name that the JSS uses for its "Application Title"
        # inventory field. If so, you can set it with the
        # jss_inventory_name input variable. If this variable is not
        # specified, it will just append .app, which is how most apps
        # work.
        if self.env.get("jss_inventory_name"):
            replace_dict["JSS_INVENTORY_NAME"] = self.env.get("jss_inventory_name")
        else:
            replace_dict["JSS_INVENTORY_NAME"] = "%s.app" % self.env.get("prod_name")
        self.replace_dict = replace_dict

    # pylint: disable=too-many-arguments
    def update_or_create_new(
        self,
        obj_cls,
        template_path,
        name="",
        added_env="",
        update_env="",
        script_contents="",
    ):
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
            script_contents (str): XML escaped script.
            do_update (Boolean): Do not overwrite an existing group if
                set to False.

        Returns:
            The recipe object after updating.
        """
        # Create a new object from the template
        recipe_object = self.get_templated_object(obj_cls, template_path)

        # Ensure categories exist prior to using them in an object.
        # Text replacement has already happened, so categories should
        # be in place.
        try:
            category_name = recipe_object.category.text
        except AttributeError:
            category_name = None
        if category_name is not None:
            self.handle_category(obj_cls.root_tag, category_name)

        if not name:
            name = recipe_object.name

        # Check for an existing object with this name.
        existing_object = None
        search_method = getattr(self.jss, obj_cls.__name__)
        try:
            existing_object = search_method(name)
        except jss.GetError:
            pass

        # If object is a Policy, we need to inject scope, scripts,
        # package, and an icon.
        if obj_cls is jss.Policy:
            # If a policy_category has been given as an input variable,
            # it wins. Replace whatever is in the template, and add in
            # a category tag if it isn't there.
            if self.env.get("policy_category"):
                policy_category = recipe_object.find("category")
                if policy_category is None:
                    policy_category = ElementTree.SubElement(recipe_object, "category")
                policy_category.text = self.env.get("policy_category")

            if existing_object is not None:
                # If this policy already exists, and it has an icon set,
                # copy its icon section to our template, as we have no
                # other way of getting this information.
                icon_xml = existing_object.find("self_service/self_service_icon")
                if icon_xml is not None:
                    self.add_icon_to_policy(recipe_object, icon_xml)
                if not self.env.get("force_policy_state"):
                    state = existing_object.find("general/enabled").text
                    recipe_object.find("general/enabled").text = state

            # If skip_scope is True then don't include scope data.
            if self.env["skip_scope"] is not True:
                self.add_scope_to_policy(recipe_object)
            else:
                self.output(
                    "Skipping assignment of scope as skip_scope is set to {}".format(
                        self.env["skip_scope"]
                    )
                )
            # If skip_scripts is True then don't include scripts data.
            if self.env["skip_scripts"] is not True:
                self.add_scripts_to_policy(recipe_object)
            else:
                self.output(
                    "Skipping assignment of scripts as skip_scripts is set to {}".format(
                        self.env["skip_scripts"]
                    )
                )
            # add package to policy if there is one
            self.add_package_to_policy(recipe_object)

        # If object is a script, add the passed contents to the object.
        # throw it into the `script_contents` tag of the object.
        if obj_cls is jss.Script and script_contents:
            tag = ElementTree.SubElement(recipe_object, "script_contents")
            tag.text = script_contents

        if existing_object is not None:
            # Update the existing object.
            # Copy the ID from the existing object to the new one so
            # that it knows how to save itself.
            recipe_object._basic_identity["id"] = existing_object.id
            recipe_object.save()
            # get feedback that the object has been created
            object = self.wait_for_id(obj_cls, name)
            try:
                object.id
                # Retrieve the updated XML.
                recipe_object = search_method(name)
                self.output("{} '{}' updated.".format(obj_cls.__name__, name))
                if update_env:
                    self.env["jss_changed_objects"][update_env].append(name)
            except ValueError:
                raise ProcessorError(
                    "Failed to get {} ID from {}.".format(
                        obj_cls.__name__, self.repo_type()
                    )
                )

        else:
            # Object doesn't exist yet.
            recipe_object.save()
            # get feedback that the object has been created
            object = self.wait_for_id(obj_cls, name)
            try:
                object.id
                self.output("{} '{}' created.".format(obj_cls.__name__, name))
                if added_env:
                    self.env["jss_changed_objects"][added_env].append(name)
            except ValueError:
                raise ProcessorError(
                    "Failed to get {} ID from {}.".format(
                        obj_cls.__name__, self.repo_type()
                    )
                )

        return recipe_object

    # pylint: enable=too-many-arguments
    def get_templated_object(self, obj_cls, template_path):
        """Return an object based on a template located in search path.

        Args:
            obj_cls: JSSObject class (for the purposes of JSSImporter a
                Policy or a ComputerGroup)
            template_path: String filename or path to template file.
                See find_file_in_search_path() for more information on
                file searching.

        Returns:
            A JSS Object created based on the template,
            post-text-replacement.
        """
        self.output(
            "Looking for {} template file {}...".format(
                obj_cls.__name__, os.path.basename(template_path), verbose_level=2,
            )
        )
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
        parent_recipe_dirs = [
            os.path.dirname(parent) for parent in self.env["PARENT_RECIPES"]
        ]
        unique_parent_dirs = OrderedDict()
        for parent in parent_recipe_dirs:
            unique_parent_dirs[parent] = parent
        search_dirs = [os.path.dirname(path)] + list(unique_parent_dirs)

        tested = []
        final_path = ""
        # Look for the first file that exists in the search_dirs and
        # their parent folders.
        for search_dir in search_dirs:
            test_path = os.path.join(search_dir, filename)
            test_parent_folder_path = os.path.abspath(
                os.path.join(search_dir, "..", filename)
            )
            if os.path.exists(test_path):
                final_path = test_path
            elif os.path.exists(test_parent_folder_path):
                final_path = test_parent_folder_path
            tested.append(test_path)
            tested.append(test_parent_folder_path)

            if final_path:
                self.output(
                    "Found file: {}".format(final_path), verbose_level=2,
                )
                break

        if not final_path:
            raise ProcessorError(
                "Unable to find file {} at any of the following locations: {}".format(
                    filename, tested
                )
            )

        return final_path

    def replace_text(self, text, replace_dict):  # pylint: disable=no-self-use
        """Substitute items in a text string. Also escapes for XML,
        as this is the only use for this definition

        Args:
            text: A string with embedded %tags%.
            replace_dict: A dict, where
                key: Corresponds to the % delimited tag in text.
                value: Text to swap in.

        Returns:
            The text after replacement.
        """
        for key in replace_dict:
            # Wrap our keys in % to match template tags.
            value = escape(replace_dict[key])
            text = text.replace("%%%s%%" % key, value)
        return text

    def validate_input_var(self, var):  # pylint: disable=no-self-use
        """Validate the value before trying to add a group.

        Args:
            var: Dictionary to check for problems.

        Returns: False if dictionary has invalid values, or True if it
            seems okay.
        """
        # Skipping non-string values:
        # Does group name or template have a replacement var
        # that has not been replaced?
        # Does the group have a blank value? (A blank value isn't really
        # invalid, but there's no need to process it further.)
        invalid = [
            False
            for value in var.values()
            if isinstance(value, str)
            and (value.startswith("%") and value.endswith("%"))
        ]
        if not var.get("name") or not var.get("template_path"):
            invalid = True
        return False if invalid else True

    def add_or_update_smart_group(self, group):
        """Either add a new group or update existing group."""
        # Build the template group object
        self.replace_dict["group_name"] = group["name"]
        if group.get("site_id"):
            self.replace_dict["site_id"] = group.get("site_id")
        if group.get("site_name"):
            self.replace_dict["site_name"] = group.get("site_name")

        # If do_update is set to False, do not update this object
        do_update = group.get("do_update", True)
        if not do_update:
            try:
                computer_group = self.jss.ComputerGroup(group["name"])
                self.output(
                    "Computer Group '%s' already exists "
                    "and set not to update." % computer_group.name
                )
                return computer_group
            except jss.GetError:
                self.output(
                    "Computer Group '%s' does not already exist. "
                    "Creating from template." % group["name"]
                )

        computer_group = self.update_or_create_new(
            jss.ComputerGroup,
            group["template_path"],
            update_env="jss_group_updated",
            added_env="jss_group_added",
        )
        return computer_group

    def add_or_update_static_group(self, group):
        """Either add a new group or update existing group."""
        # Check for pre-existing group first
        try:
            computer_group = self.jss.ComputerGroup(group["name"])
            self.output(
                "Static Computer Group: {} already exists.".format(computer_group.name)
            )
        except jss.GetError:
            computer_group = jss.ComputerGroup(self.jss, group["name"])
            computer_group.save()
            self.output(
                "Static Computer Group '{}' created.".format(computer_group.name)
            )
            self.env["jss_changed_objects"]["jss_group_added"].append(
                computer_group.name
            )

        return computer_group

    def add_scope_to_policy(self, policy_template):
        """Incorporate scoping groups into a policy."""
        computer_groups_element = self.ensure_xml_structure(
            policy_template, "scope/computer_groups"
        )
        exclusion_groups_element = self.ensure_xml_structure(
            policy_template, "scope/exclusions/computer_groups"
        )
        for group in self.groups:
            policy_template.add_object_to_path(group, computer_groups_element)
        for group in self.exclusion_groups:
            policy_template.add_object_to_path(group, exclusion_groups_element)

    def add_scripts_to_policy(self, policy_template):
        """Incorporate scripts into a policy."""
        scripts_element = self.ensure_xml_structure(policy_template, "scripts")
        for script in self.scripts:
            script_element = policy_template.add_object_to_path(script, scripts_element)
            priority = ElementTree.SubElement(script_element, "priority")
            priority.text = script.findtext("priority")

    def add_package_to_policy(self, policy_template):
        """Add a package to a self service policy."""
        if self.package is not None:
            self.ensure_xml_structure(policy_template, "package_configuration/packages")
            action_type = self.env["policy_action_type"]
            self.output("Setting policy to '{}' package.".format(action_type))
            policy_template.add_package(self.package, action_type=action_type)

    def add_icon_to_policy(self, policy_template, icon_xml):
        """Add an icon to a self service policy."""
        self.ensure_xml_structure(policy_template, "self_service")
        self_service = policy_template.find("self_service")
        self_service.append(icon_xml)

    def ensure_xml_structure(self, element, path):
        """Ensure that all tiers of an XML hierarchy exist."""
        search, _, path = path.partition("/")
        if search:
            if element.find(search) is None:
                ElementTree.SubElement(element, search)
            return self.ensure_xml_structure(element.find(search), path)
        return element

    def get_report_string(self, items):  # pylint: disable=no-self-use
        """Return human-readable string from a list of Jamf Pro API objects."""
        return ", ".join(set(items))

    def summarize(self):
        """If anything has been added or updated, report back."""
        # Only summarize if something has happened.
        if any(value for value in self.env["jss_changed_objects"].values()):
            # Create a blank summary.
            self.env["jss_importer_summary_result"] = {
                "summary_text": "The following changes were made to the Jamf Pro Server:",
                "report_fields": [
                    "Name",
                    "Package",
                    "Categories",
                    "Groups",
                    "Scripts",
                    "Extension_Attributes",
                    "Policy",
                    "Icon",
                    "Version",
                    "Package_Uploaded",
                ],
                "data": {
                    "Name": "",
                    "Package": "",
                    "Categories": "",
                    "Groups": "",
                    "Scripts": "",
                    "Extension_Attributes": "",
                    "Policy": "",
                    "Icon": "",
                    "Version": "",
                    "Package_Uploaded": "",
                },
            }
            # TODO: This is silly. Use a defaultdict for storing changes
            # and just copy the stuff that changed.

            # Shortcut variables for lovely code conciseness
            changes = self.env["jss_changed_objects"]
            data = self.env["jss_importer_summary_result"]["data"]

            data["Name"] = self.env.get("NAME", "")
            data["Version"] = self.env.get("version", "")

            package = self.get_report_string(
                changes["jss_package_added"] + changes["jss_package_updated"]
            )
            if package:
                data["Package"] = package

            policy = changes["jss_policy_updated"] + (changes["jss_policy_added"])
            if policy:
                data["Policy"] = self.get_report_string(policy)

            if changes["jss_icon_uploaded"]:
                data["Icon"] = os.path.basename(self.env["self_service_icon"])

            # Get nice strings for our list-types.
            if changes["jss_category_added"]:
                data["Categories"] = self.get_report_string(
                    changes["jss_category_added"]
                )

            groups = changes["jss_group_updated"] + changes["jss_group_added"]
            if groups:
                data["Groups"] = self.get_report_string(groups)

            scripts = changes["jss_script_updated"] + (changes["jss_script_added"])
            if scripts:
                data["Scripts"] = self.get_report_string(scripts)

            extattrs = changes["jss_extension_attribute_updated"] + (
                changes["jss_extension_attribute_added"]
            )
            if extattrs:
                data["Extension_Attributes"] = self.get_report_string(extattrs)

            jss_package_uploaded = self.get_report_string(changes["jss_repo_updated"])
            if jss_package_uploaded:
                data["Package_Uploaded"] = "True"

    def main(self):
        """Main processor code."""
        # Ensure we have the right version of python-jss
        python_jss_version = StrictVersion(PYTHON_JSS_VERSION)
        self.output(
            "python-jss version: {}.".format(python_jss_version), verbose_level=2,
        )
        if python_jss_version < REQUIRED_PYTHON_JSS_VERSION:
            self.output(
                "python-jss version is too old. Please update to version: {}.".format(
                    REQUIRED_PYTHON_JSS_VERSION
                )
            )
            raise ProcessorError

        self.output(
            "JSSImporter version: {}.".format(__version__), verbose_level=2,
        )

        # clear any pre-existing summary result
        if "jss_importer_summary_result" in self.env:
            del self.env["jss_importer_summary_result"]

        self.create_jss()
        self.output(
            "Jamf Pro version: '{}'".format(self.jss.version()), verbose_level=2,
        )

        self.pkg_name = os.path.basename(self.env["pkg_path"])
        self.prod_name = self.env["prod_name"]
        self.version = self.env.get("version")
        if self.version == "0.0.0.0":
            self.output(
                "Warning: No `version` was added to the AutoPkg env up to "
                "this point. JSSImporter is defaulting to version {}!".format(
                    self.version
                ),
                verbose_level=2,
            )

        # Build and init jss_changed_objects
        self.init_jss_changed_objects()

        self.category = self.handle_category("category")
        self.policy_category = self.handle_category("policy_category")

        # Get our DPs ready for copying.
        if len(self.jss.distribution_points) == 0:
            self.output("Warning: No distribution points configured!")
        for dp in self.jss.distribution_points:
            self.output(
                "Checking if DP already mounted...", verbose_level=2,
            )
            dp.was_mounted = hasattr(dp, "is_mounted") and dp.is_mounted()
        # Don't bother mounting the DPs if there's no package.
        if self.env["pkg_path"]:
            self.jss.distribution_points.mount()

        # define whether we will stop based on the value of STOP_IF_NO_JSS_UPLOAD
        self.stop_if_no_upload = "{}".format(self.env.get("STOP_IF_NO_JSS_UPLOAD"))

        # handle package
        self.package = self.handle_package(self.stop_if_no_upload)

        # stop if no package was uploaded and STOP_IF_NO_JSS_UPLOAD is True
        if self.stop_if_no_upload != "False" and not self.upload_needed:
            # Done with DPs, unmount them.
            for dp in self.jss.distribution_points:
                if not dp.was_mounted:
                    self.output(
                        "Unmounting DP...", verbose_level=2,
                    )
                    self.jss.distribution_points.umount()
            self.summarize()
            return

        # Build our text replacement dictionary
        self.build_replace_dict()

        self.extattrs = self.handle_extension_attributes()

        self.groups = self.handle_groups(self.env.get("groups"))
        self.exclusion_groups = self.handle_groups(self.env.get("exclusion_groups"))

        self.scripts = self.handle_scripts()
        self.policy = self.handle_policy()
        self.handle_icon()

        # Done with DPs, unmount them.
        for dp in self.jss.distribution_points:
            if not dp.was_mounted:
                self.jss.distribution_points.umount()
        self.summarize()


# pylint: enable=too-many-instance-attributes, too-many-public-methods

if __name__ == "__main__":
    processor = JSSImporter()  # pylint: disable=invalid-name
    processor.execute_shell()
