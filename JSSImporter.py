#!/usr/bin/python
#
# Copyright 2014 Shea Craig
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from distutils.version import StrictVersion
import os
import shutil
from sys import exit
from xml.etree import ElementTree

import jss
# Ensure that python-jss dependency is at minimum version
try:
    from jss import __version__ as PYTHON_JSS_VERSION
except ImportError:
    PYTHON_JSS_VERSION = '0.0.0'
from autopkglib import Processor, ProcessorError


__all__ = ["JSSImporter"]
__version__ = '0.3.2'
REQUIRED_PYTHON_JSS_VERSION = StrictVersion('0.5.1')


class JSSImporter(Processor):
    """Imports a flat pkg to the JSS."""
    input_variables = {
        "prod_name": {
            "required": True,
            "description": "Name of the product.",
        },
        "jss_inventory_name": {
            "required": False,
            "description": "Smart groups using the 'Application Title' "
            "criteria need to specify the app's filename, as registered in "
            "the JSS's inventory. If this variable is left out, it will "
            "generate an 'Application Title' by adding '.app' to the "
            "prod_name, e.g. prod_name='Google Chrome', calculated "
            " jss_inventory_name='Google Chrome.app'. If you need to override "
            "this behavior, specify the correct name with this variable.",
        },
        "pkg_path": {
            "required": True,
            "description": "Path to a pkg or dmg to import - provided by "
            "previous pkg recipe/processor.",
        },
        "version": {
            "required": True,
            "description": "Version number of software to import - provided "
            "by previous pkg recipe/processor.",
        },
        "JSS_REPOS": {
            "required": False,
            "description": "Array of dicts for each intended distribution "
            "point. Each distribution point type requires slightly different "
            "configuration keys and data. Please consult the documentation. ",
            "default": [],
        },
        "JSS_URL": {
            "required": True,
            "description": "URL to a JSS that api the user has write access "
            "to, optionally set as a key in the com.github.autopkg preference "
            "file.",
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
            "with the JSS will be skipped. Defaults to 'True'.",
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
        "os_requirements": {
            "required": False,
            "description": "Comma-seperated list of OS version numbers to "
            "allow. Corresponds to the OS Requirements field for packages. "
            "The character 'x' may be used as a wildcard, as in '10.9.x'",
        },
        "groups": {
            "required": False,
            "description": "Array of group dictionaries. Wrap each group in a "
            "dictionary. Group keys include 'name' (Name of the group to use, "
            "required), 'smart' (Boolean: static group=False, "
            "smart group=True, default is False, not required), and "
            "'template_path' (string: path to template file to use for group, "
            "required for smart groups, invalid for static groups)",
        },
        "scripts": {
            "required": False,
            "description": "Array of script dictionaries. Wrap each script in "
            "a dictionary. Script keys include 'name' (Name of the script to "
            "use, required), 'template_path' (string: path to template file to"
            " use for script, " "required)",
        },
        "extension_attributes": {
            "required": False,
            "description": "Array of extension attribute dictionaries. Wrap "
            "each extension attribute in a dictionary. Script keys include "
            "'name' (Name of the extension attribute to use, required), "
            "'ext_attribute_path' (string: path to extension attribute file.)",
        },
        "policy_template": {
            "required": False,
            "description": "Filename of policy template file. If key is "
            "missing or value is blank, policy creation will be skipped.",
            "default": '',
        },
        "self_service_description": {
            "required": False,
            "description": "Use to populate the %SELF_SERVICE_DESCRIPTION% "
            "variable for use in templates. Primary use is for filling the "
            "info button text in Self Service, but could be used elsewhere.",
            "default": '',
        },
        "self_service_icon": {
            "required": False,
            "description": "Path to an icon file. Use to add an icon to a "
            "self-service enabled policy. Because of the way Casper handles "
            "this, the JSSImporter will only upload if the icon's filename is "
            "different than the one set on the policy (if it even exists). "
            "Please see the README for more information.",
            "default": '',
        },
    }
    output_variables = {
        "jss_category_added": {
            "description": "True if category was created."
        },
        "jss_package_added": {
            "description": "True if package was created."
        },
        "jss_package_updated": {
            "description": "True if package was updated."
        },
        "jss_repo_updated": {
            "description": "True if item was imported."
        },
        "jss_group_added": {
            "description": "True if a group was added."
        },
        "jss_group_updated": {
            "description": "True if a group was updated."
        },
        "jss_script_added": {
            "description": "True if a script was added."
        },
        "jss_script_updated": {
            "description": "True if a script was updated."
        },
        "jss_extension_attribute_added": {
            "description": "True if an extension attribute was added."
        },
        "jss_extension_attribute_updated": {
            "description": "True if an extension attribute was updated."
        },
        "jss_policy_added": {
            "description": "True if policy was added."
        },
        "jss_policy_updated": {
            "description": "True if policy was updated."
        },
        "jss_icon_uploaded": {
            "description": "True if an icon was uploaded."
        },
    }
    description = __doc__

    def build_replace_dict(self):
        """Build a dictionary of replacement values based on available
        input variables.

        """
        replace_dict = {}
        replace_dict['%VERSION%'] = self.version
        replace_dict['%PKG_NAME%'] = self.package.name
        replace_dict['%PROD_NAME%'] = self.env.get('prod_name')
        replace_dict['%SELF_SERVICE_DESCRIPTION%'] = self.env.get(
            'self_service_description')
        replace_dict['%SELF_SERVICE_ICON%'] = self.env.get(
            'self_service_icon')
        # policy_category is not required, so set a default value if absent.
        replace_dict['%POLICY_CATEGORY%'] = self.env.get(
            "policy_category") or "Unknown"
        #if self.env.get("policy_name"):
        #    replace_dict['%POLICY_NAME%'] = self.env.get("policy_name")
        # Some applications may have a product name that differs from the name
        # that the JSS uses for its "Application Title" inventory field. If so,
        # you can set it with the jss_inventory_name input variable. If this
        # variable is not specified, it will just append .app, which is how
        # most apps work.
        if self.env.get("jss_inventory_name"):
            replace_dict['%JSS_INVENTORY_NAME%'] = self.env.get(
                "jss_inventory_name")
        else:
            replace_dict['%JSS_INVENTORY_NAME%'] = '%s.app' \
                % self.env.get('prod_name')
        return replace_dict

    def replace_text(self, text, replace_dict):
        """Substitute items in a text string.

        text: A string with embedded %tags%.
        replace_dict: A dict, where
            key: Corresponds to the % delimited tag in text.
            value: Text to swap in.

        """
        for key, value in replace_dict.iteritems():
            text = text.replace(key, value)
        return text

    def handle_category(self, category_type):
        if self.env.get(category_type):
            category_name = self.env.get(category_type)
            try:
                category = self.j.Category(category_name)
                self.output("Category type: %s-'%s' already exists "
                            "according to JSS, moving on..." %
                            (category_type, category_name))
            except jss.JSSGetError:
                # Category doesn't exist
                category = jss.Category(self.j, category_name)
                category.save()
                self.output("Category type: %s-'%s' created." % (category_type,
                                                                category_name))
                self.env["jss_category_added"] = True
        else:
            category = None

        return category

    def handle_package(self):
        """Creates or updates a package object on the jss, then uploads a
        package file to the configured distribution points.

        This will only upload a package if a file with the same name does not
        already exist on a DP. If you need to force a re-upload, you must
        delete the package on the DP first.

        Further, if you are using a JDS, it will only upload a package if a
        package object with a filename matching the AutoPkg filename does not
        exist. If you need to force a re-upload to a JDS, please delete the
        package object through the web interface first.

        """
        os_requirements = self.env.get("os_requirements")
        try:
            package = self.j.Package(self.pkg_name)
            self.output("Pkg-object already exists according to JSS, "
                        "moving on...")

            # Set os_requirements if they don't match.
            if os_requirements and os_requirements != package.findtext(
                    "os_requirements"):
                package.set_os_requirements(os_requirements)
                package.save()
                self.output("Package os_requirements updated.")
                self.env["jss_package_updated"] = True

            # Update category if necessary.
            if self.category is not None:
                recipe_name = self.category.name
            else:
                recipe_name = 'Unknown'
            if package.find('category').text != recipe_name:
                package.find('category').text = recipe_name
                package.save()
                self.output("Package category updated.")
                self.env["jss_package_updated"] = True

        except jss.JSSGetError:
            # Package doesn't exist
            if self.category is not None:
                package = jss.Package(self.j, self.pkg_name,
                                      cat_name=self.category.name)
            else:
                package = jss.Package(self.j, self.pkg_name)

            package.set_os_requirements(os_requirements)
            package.save()
            self.env["jss_package_added"] = True

        # Ensure packages are on distribution point(s)

        # If we had to make a new package object, we know we need to copy
        # the package file, regardless of DP type. This solves the issue
        # regarding the JDS.exists() method: See python-jss docs for info.
        # The problem with this method is that if you cancel an AutoPkg run
        # and the package object has been created, but not uploaded, you
        # will need to delete the package object from the JSS before
        # running a recipe again or it won't upload the package file.
        #
        # Passes the id of the newly created package object so JDS' will
        # upload to the correct package object. Ignored by AFP/SMB.
        if self.env["jss_package_added"]:
            self._copy(self.env["pkg_path"], id_=package.id)
        # For AFP/SMB shares, we still want to see if the package exists.
        # If it's missing, copy it!
        elif not self.j.distribution_points.exists(
            os.path.basename(self.env["pkg_path"])):
            self._copy(self.env["pkg_path"])
        else:
            self.output("Package upload not needed.")

        return package

    def _copy(self, source_item, id_=-1):
        """Copy a package or script using the JSS_REPOS preference."""
        self.output("Copying %s to all distribution points." % source_item)
        self.j.distribution_points.copy(source_item, id_=id_)
        self.env["jss_repo_updated"] = True
        self.output("Copied %s" % source_item)

    def handle_groups(self):
        groups = self.env.get('groups')
        computer_groups = []
        if groups:
            for group in groups:
                is_smart = group.get('smart') or False
                if is_smart:
                    computer_group = self._add_or_update_smart_group(group)
                else:
                    computer_group = self._add_or_update_static_group(group)

                computer_groups.append(computer_group)

        return computer_groups

    def _add_or_update_static_group(self, group):
        """Given a group, either add a new group or update existing group."""
        # Check for pre-existing group first
        try:
            computer_group = self.j.ComputerGroup(group['name'])
            self.output("Computer Group: %s already exists." %
                        computer_group.name)
        except jss.JSSGetError:
            computer_group = jss.ComputerGroup(self.j, group['name'])
            computer_group.save()
            self.output("Computer Group: %s created." % computer_group.name)
            self.env["jss_group_added"] = True

        return computer_group

    def _add_or_update_smart_group(self, group):
        """Given a group, either add a new group or update existing group."""
        # Build the template group object
        self.replace_dict['%group_name%'] = group['name']
        computer_group = self._update_or_create_new(
            jss.ComputerGroup, group["template_path"],
            update_env="jss_group_updated", added_env="jss_group_added")

        return computer_group

    def _update_or_create_new(self, obj_cls, template_path, name='',
                              added_env='', update_env=''):
        """Check for an existing object and update it, or create a new object.

        obj_cls:        The python-jss object class to work with.
        template_path:  The environment variable pointing to this objects
                        template.
        name:           The name to use. Defaults to the "name" property of the
                        templated object.
        added_env:      The environment var to update if an object is added.
        update_env:     The environment var to update if an object is updated.

        """
        # Create a new object from the template
        with open(os.path.expanduser(template_path), 'r') as f:
            text = f.read()
        template = self.replace_text(text, self.replace_dict)
        recipe_object = obj_cls.from_string(self.j, template)

        if not name:
            name = recipe_object.name

        # Check for an existing object with this name.
        existing_object = None
        try:
            existing_object = self.j.factory.get_object(obj_cls, name)
        except jss.JSSGetError:
            pass

        # If object is a Policy, we need to inject scope, scripts, package, and
        # an icon.
        if obj_cls is jss.Policy:
            if existing_object is not None:
                # If this policy already exists, and it has an icon set, copy
                # its icon section to our template, as we have no other way of
                # getting this information.
                icon_xml = existing_object.find(
                    'self_service/self_service_icon')
                if icon_xml is not None:
                    self.add_icon_to_policy(recipe_object, icon_xml)
            self.add_scope_to_policy(recipe_object)
            self.add_scripts_to_policy(recipe_object)
            self.add_package_to_policy(recipe_object)

        if existing_object is not None:
            # Update the existing object.
            url = existing_object.get_object_url()
            self.j.put(url, recipe_object)
            # Retrieve the updated XML.
            recipe_object = self.j.factory.get_object(obj_cls, name)
            self.output("%s: %s updated." % (obj_cls.__name__, name))
            if update_env:
                self.env[update_env] = True
        else:
            # Object doesn't exist yet.
            recipe_object.save()
            self.output("%s: %s created." % (obj_cls.__name__, name))
            if added_env:
                self.env[added_env] = True

        return recipe_object


    def handle_scripts(self):
        scripts = self.env.get('scripts')
        results = []
        if scripts:
            for script in scripts:
                script_object = self._update_or_create_new(
                    jss.Script, script['template_path'],
                    os.path.basename(script['name']),
                    added_env="jss_script_added",
                    update_env="jss_script_updated")

                # Copy the script to the distribution points.
                self._copy(script['name'], id_=script_object.id)

                results.append(script_object)
        return results

    def handle_extension_attributes(self):
        extattrs = self.env.get('extension_attributes')
        results = []
        if extattrs:
            for extattr in extattrs:
                extattr_object = self._update_or_create_new(
                    jss.ComputerExtensionAttribute,
                    extattr['ext_attribute_path'], extattr['name'],
                    update_env="jss_extension_attribute_added",
                    added_env="jss_extension_attribute_updated")

                results.append(extattr_object)
        return results

    def handle_icon(self):
        # Icons are tricky. The only way to add new ones is to use FileUploads.
        # If you manually upload them, you can add them to a policy to get
        # their ID, but there is no way to query the JSS to see what icons are
        # available. Thus, icon handling involves several cooperating methods.
        # If we just add an icon every time we run a recipe, however, we end up
        # with a ton of redundent icons, and short of actually deleting them in
        # the sql database, there's no way to delete icons. So when we run, we
        # first check for an existing policy, and if it exists, copy its icon
        # XML, which is then added to the templated Policy. If there is no icon
        # information, but the recipe specifies one, then FileUpload it up.

        # If no policy handling is desired, we can't upload an icon.
        if self.env.get("self_service_icon") and self.policy is not None:
            icon_path = self.env.get("self_service_icon")
            icon_filename = os.path.basename(icon_path)

            # Compare the filename in the policy to the one provided by the
            # recipe. If they don't match, we need to upload a new icon.
            policy_filename = self.policy.findtext(
                'self_service/self_service_icon/filename')
            if not policy_filename == icon_filename:
                icon = jss.FileUpload(self.j, 'policies', 'id', self.policy.id,
                                      icon_path)
                icon.save()
                self.env["jss_icon_uploaded"] = True
                self.output("Icon uploaded to JSS.")
            else:
                self.output("Icon matches existing icon, moving on...")

    def handle_policy(self):
        if self.env.get("policy_template"):
            template_filename = self.env.get("policy_template")
            policy = self._update_or_create_new(jss.Policy, template_filename,
                                                update_env="jss_policy_added",
                                                added_env="jss_policy_updated")
        else:
            self.output("Policy creation not desired, moving on...")
            policy = None

        return policy

    def add_scope_to_policy(self, policy_template):
        computer_groups_element = self.ensure_XML_structure(
            policy_template, 'scope/computer_groups')
        for group in self.groups:
            policy_template.add_object_to_path(group, computer_groups_element)

    def add_scripts_to_policy(self, policy_template):
        scripts_element = self.ensure_XML_structure(policy_template, 'scripts')
        for script in self.scripts:
            script_element = policy_template.add_object_to_path(
                script, scripts_element)
            priority = ElementTree.SubElement(script_element, 'priority')
            priority.text = script.findtext('priority')

    def add_package_to_policy(self, policy_template):
        packages_element = self.ensure_XML_structure(
            policy_template, 'package_configuration/packages')
        package_element = policy_template.add_object_to_path(self.package,
                                                             packages_element)
        action = ElementTree.SubElement(package_element, 'action')
        action.text = 'Install'

    def add_icon_to_policy(self, policy_template, icon_xml):
        self_service_icon_element = self.ensure_XML_structure(
            policy_template, 'self_service')
        self_service = policy_template.find('self_service')
        self_service.append(icon_xml)

    def ensure_XML_structure(self, element, path):
        """Given an XML path and a starting element, ensure that all tiers of
        the hierarchy exist.

        """
        search, slash, path = path.partition('/')
        if search:
            if element.find(search) is None:
                ElementTree.SubElement(element, search)
            return self.ensure_XML_structure(element.find(search), path)
        return element

    def main(self):
        # Ensure we have the right version of python-jss
        python_jss_version = StrictVersion(PYTHON_JSS_VERSION)
        if python_jss_version < REQUIRED_PYTHON_JSS_VERSION:
            self.output("Requires python-jss version: %s. Installed: %s" %
                  (REQUIRED_PYTHON_JSS_VERSION, python_jss_version))
            exit()

        # pull jss recipe-specific args, prep api auth
        repoUrl = self.env["JSS_URL"]
        authUser = self.env["API_USERNAME"]
        authPass = self.env["API_PASSWORD"]
        sslVerify = self.env.get("JSS_VERIFY_SSL")
        repos = self.env.get("JSS_REPOS")
        self.j = jss.JSS(url=repoUrl, user=authUser, password=authPass,
                         ssl_verify=sslVerify, repo_prefs=repos)
        self.pkg_name = os.path.basename(self.env["pkg_path"])
        self.prod_name = self.env["prod_name"]
        self.version = self.env["version"]

        # pre-set 'added/updated' output checks to False
        self.env["jss_repo_updated"] = False
        self.env["jss_category_added"] = False
        self.env["jss_package_added"] = False
        self.env["jss_package_updated"] = False
        self.env["jss_group_added"] = False
        self.env["jss_group_updated"] = False
        self.env["jss_script_added"] = False
        self.env["jss_script_updated"] = False
        self.env["jss_extension_attribute_added"] = False
        self.env["jss_extension_attribute_updated"] = False
        self.env["jss_policy_added"] = False
        self.env["jss_policy_updated"] = False
        self.env["jss_icon_uploaded"] = False

        self.category = self.handle_category("category")
        self.policy_category = self.handle_category("policy_category")
        # Get our DPs read for copying.
        self.j.distribution_points.mount()
        self.package = self.handle_package()
        # Build our text replacement dictionary
        self.replace_dict = self.build_replace_dict()

        self.extattrs = self.handle_extension_attributes()
        self.groups = self.handle_groups()
        self.scripts = self.handle_scripts()
        self.policy = self.handle_policy()
        self.handle_icon()
        # Done with DPs, unmount them.
        self.j.distribution_points.umount()


if __name__ == "__main__":
    processor = JSSImporter()
    processor.execute_shell()
