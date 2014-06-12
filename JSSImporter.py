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
        "smart_group": {
            "required": False,
            "description": "Name of scoping group to create with which to offer item to users that are not at the same version.",
        },
        "arb_group_name": {
            "required": False,
            "description": "Name of static group to offer imported item to.",
        },
        "selfserve_policy": {
            "required": False,
            "description": "Name of automatically activated self-service policy for offering software to test and older-version users. Will create if not present and update if data is not current or invalid",
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

    def handle_category(self):
        if self.env.get("category"):
            category_name = self.env.get("category")
            if not category_name == "*LEAVE_OUT*":
                try:
                    category = self.j.Category(category_name)
                    self.output("Category already exists according to JSS, moving on")
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
        try:
            package = self.j.Package(str(self.pkg_name))
            self.output("Pkg already exists according to JSS, moving on")
        except jss.JSSGetError:
            if self.category:
                package_template = jss.JSSPackageTemplate(self.pkg_name, self.category.name)
            else:
                package_template = jss.JSSPackageTemplate(self.pkg_name)

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
                    group = self.j.ComputerGroup(str(smart_group_name))
                    version_criteria_out_of_date = [crit for crit in group.findall("criteria/criterion") if crit.find("name") == "Application Version" and crit.find("value") != version]
                    if version_criteria_out_of_date:
                        version_criteria[0].find("value").text = version
                        group.update()
                        self.env["jss_smartgroup_updated"] = True
                except jss.JSSGetError:
                    group_template = jss.JSSComputerGroupTemplate(str(smart_group_name), True)
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
                    group = self.j.ComputerGroup(str(static_group_name))
                except:
                    group_template = jss.ComputerGroupTemplate(str(static_group_name))
                    group = self.j.ComputerGroup(group_template)
            else:
                self.output("Static group check/creation not desired, moving on")

        return group

    def handle_policy(self):
        if self.env.get("selfserve_policy"):
            policy_name = self.env.get("selfserve_policy")
            if not policy_name == "*LEAVE_OUT*":
                try:
                    policy = self.j.Policy(str(policy_name))
                    packages_out_of_date = [p for p in policy.findall('package_configuration/packages/package') if p.findtext('id') != str(self.package.id)]
                    group_out_of_date = [g for g in policy.findall('scope/computer_groups/computer_group') if g.findtext('id') != str(self.group.id)]
                    if packages_out_of_date:
                        packages_out_of_date[0].find('id').text = str(self.package.id)
                        packages_out_of_date[0].find('name').text = self.package.name
                        policy.update()
                    if group_out_of_date:
                        group_out_of_date[0].find('id').text = str(self.group.id)
                        group_out_of_date[0].find('name').text = self.group.name
                        policy.update()
                except jss.JSSGetError:
                    policy_template = jss.PolicyTemplate(policy_name)
                    policy_template.add_pkg(self.package)
                    policy_template.add_object_to_scope(self.group)
                    policy = self.j.Policy(policy_template)
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

        self.category = self.handle_category()
        self.package = self.handle_package()
        self.group = self.handle_group()
        self.handle_policy()

if __name__ == "__main__":
    processor = JSSImporter()
    processor.execute_shell()
