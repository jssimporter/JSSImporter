#!/usr/bin/env python
#
# Copyright 2014 Allister Banks
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


import os
#import urllib2
import shutil
#from xml.etree import ElementTree

import jss
from autopkglib import Processor, ProcessorError

__all__ = ["JSSImporter"]


class JSSImporter(Processor):
    """Imports a flat pkg to the JSS."""
    input_variables = {
        "prod_name": {
            "required": True,
            "description": "Name of the product.",
        },
        "pkg_path": {
            "required": True,
            "description": "Path to a pkg or dmg to import - provided by previous pkg recipe/processor.",
        },
        "version": {
            "required": True,
            "description": "Version number of software to import - provided by previous pkg recipe/processor.",
        },
        "JSS_REPO": {
            "required": True,
            "description": "Path to a mounted or otherwise locally accessible JSS dist point/share, optionally set as a key in the com.github.autopkg preference file.",
        },
        "JSS_URL": {
            "required": True,
            "description": "URL to a JSS that api the user has write access to, optionally set as a key in the com.github.autopkg preference file.",
        },
        "API_USERNAME": {
            "required": True,
            "description": "Username of account with appropriate access to jss, optionally set as a key in the com.github.autopkg preference file.",
        },
        "API_PASSWORD": {
            "required": True,
            "description": "Password of api user, optionally set as a key in the com.github.autopkg preference file.",
        },
        "category": {
            "required": False,
            "description": ("Category to create/associate imported app package with."),
        },
        "os_requirements": {
            "required": False,
            "description": "Comma-seperated list of OS version numbers to allow. Corresponds to the OS Requirements field for packages. The character 'x' may be used as a wildcard, as in '10.9.x'",
        },
        "smart_group": {
            "required": False,
            "description": "Name of scoping group to create with which to offer item to users that are not at the same version.",
        },
        "arb_group_name": {
            "required": False,
            "description": "Name of static group to offer imported item to.",
        },
        "policy_template": {
            "required": False,
            "description": "Filename of policy template file.",
        },
    }
    output_variables = {
        "jss_category_added": {
            "description": "True if category was created."
        },
        "jss_repo_changed": {
            "description": "True if item was imported."
        },
        "jss_smartgroup_added": {
            "description": "True if smartgroup was added."
        },
        "jss_smartgroup_updated": {
            "description": "True if smartgroup was updated."
        },
        "jss_staticgroup_added": {
            "description": "True if staticgroup was added."
        },
        "jss_staticgroup_updated": {
            "description": "True if staticgroup was updated."
        },
        "jss_policy_added": {
            "description": "True if policy was added."
        },
        "jss_policy_updated": {
            "description": "True if policy was updated."
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
        replace_dict['%GROUP%'] = self.group.name
        if self.env.get("policy_category"):
            replace_dict['%POLICY_CATEGORY%'] = self.env.get(
                "policy_category")
        if self.env.get("policy_name"):
            replace_dict['%POLICY_NAME%'] = self.env.get("policy_name")
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
            if not category_name == "*LEAVE_OUT*":
                try:
                    category = self.j.Category(category_name)
                    self.output("Category type: %s-'%s' already exists according to JSS, moving on" % (category_type, category_name))
                except jss.JSSGetError:
                    # Category doesn't exist
                    category_template = jss.CategoryTemplate(category_name)
                    category = self.j.Category(category_template)
                    self.env["jss_category_added"] = True
            else:
                self.output("Category creation for the pkg not desired, moving on")
                category = None
        else:
            category = None

        return category

    def handle_package(self):
        os_requirements = self.env.get("os_requirements")
        try:
            package = self.j.Package(self.pkg_name)
            if os_requirements and os_requirements != package.findtext("os_requirements"):
                package.set_os_requirements(os_requirements)
                package.update()
                self.output("Pkg updated.")

            else:
                self.output("Pkg already exists according to JSS, moving on")
        except jss.JSSGetError:
            if self.category:
                package_template = jss.PackageTemplate(self.pkg_name, self.category.name)
            else:
                package_template = jss.PackageTemplate(self.pkg_name)

            package_template.set_os_requirements(os_requirements)

            package = self.j.Package(package_template)

        source_item = self.env["pkg_path"]
        dest_item = (self.env["JSS_REPO"] + "/" + self.pkg_name)
        if os.path.exists(dest_item):
            self.output("Pkg already exists at %s, moving on" % dest_item)
        else:
            try:
                if os.path.isdir(source_item):
                    shutil.copytree(source_item, dest_item)
                else:
                    shutil.copyfile(source_item, dest_item)
                self.output("Copied %s to %s" % (source_item, dest_item))
                # set output variables
                self.env["jss_repo_changed"] = True
            except BaseException, err:
                raise ProcessorError(
                    "Can't copy %s to %s: %s" % (source_item, dest_item, err))
        return package

    def handle_group(self):
        # check for smartGroup if var set
        if self.env.get("smart_group"):
            smart_group_name = self.env.get("smart_group")
            if not smart_group_name == "*LEAVE_OUT*":
                try:
                    group = self.j.ComputerGroup(smart_group_name)
                    version_criteria_out_of_date = [crit for crit in group.findall("criteria/criterion") if crit.find("name") == "Application Version" and crit.find("value") != version]
                    if version_criteria_out_of_date:
                        version_criteria[0].find("value").text = version
                        group.update()
                        self.env["jss_smartgroup_updated"] = True
                except jss.JSSGetError:
                    group_template = jss.ComputerGroupTemplate(smart_group_name, True)
                    criterion1 = jss.SearchCriteria("Application Title", 0, 'and', 'is', prod_name)
                    criterion2 = jss.SearchCriteria("Application Version", 1, 'and', 'is not', version)
                    group_template.add_criterion(criterion1)
                    group_template.add_criterion(criterion2)
                    group = j.ComputerGroup(group_template)
                    self.env["jss_smartgroup_added"] = True
            else:
                self.output("Smart group creation not desired, moving on")
        # check for arbitraryGroupID if var set
        if self.env.get("arb_group_name"):
            static_group_name = self.env.get("arb_group_name")
            if not static_group_name == "*LEAVE_OUT*":
                try:
                    group = self.j.ComputerGroup(static_group_name)
                except:
                    group_template = jss.ComputerGroupTemplate(static_group_name)
                    group = self.j.ComputerGroup(group_template)
            else:
                self.output("Static group check/creation not desired, moving on")

        return group

    def handle_policy(self):
        if self.env.get("policy_template"):
            template_filename = self.env.get("policy_template")

            if not template_filename == "*LEAVE_OUT*":
                with open(template_filename, 'r') as f:
                    text = f.read()
                replace_dict = self.build_replace_dict()
                text = self.replace_text(text, replace_dict)
                template = jss.TemplateFromString(text)
                self.output(template)
                try:
                    policy = self.j.Policy(template.findtext('general/name'))
                    policy.delete()
                    policy = self.j.Policy(template)
                    self.env["jss_policy_updated"] = True
                except jss.JSSGetError:
                    # Object doesn't exist yet.
                    policy = self.j.Policy(template)
                    self.env["jss_policy_added"] = True
            else:
                self.output("Policy creation not desired, moving on")

    def main(self):
        # pull jss recipe-specific args, prep api auth
        repoUrl = self.env["JSS_URL"]
        authUser = self.env["API_USERNAME"]
        authPass = self.env["API_PASSWORD"]
        self.j = jss.JSS(url=repoUrl, user=authUser, password=authPass)
        self.pkg_name = os.path.basename(self.env["pkg_path"])
        self.prod_name = self.env["prod_name"]
        self.version = self.env["version"]
        # pre-set 'changed/added/updated' output checks to False
        self.env["jss_repo_changed"] = False
        self.env["jss_category_added"] = False
        self.env["jss_smartgroup_added"] = False
        self.env["jss_smartgroup_updated"] = False
        self.env["jss_staticgroup_added"] = False
        self.env["jss_staticgroup_updated"] = False
        self.env["jss_policy_added"] = False
        self.env["jss_policy_updated"] = False

        self.category = self.handle_category("category")
        self.policy_category = self.handle_category("policy_category")
        self.package = self.handle_package()
        self.group = self.handle_group()
        self.handle_policy()

if __name__ == "__main__":
    processor = JSSImporter()
    processor.execute_shell()
