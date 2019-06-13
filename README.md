JSSImporter processor for AutoPkg
=================================

This processor adds the ability for [AutoPkg](https://github.com/autopkg/autopkg) to create groups, upload packages, add scripts and extension attributes,
and create policies for the Jamf Pro Server, allowing you to fully-automate your software **testing** workflow.

---

## For details on how to use JSSImporter, please visit our [Wiki](https://github.com/jssimporter/JSSImporter/wiki).

---

How to build JSSImporter
------------------------

We provide installable packages in our GitHub repository. If you wish to build your own package, we also provide a `makefile` here. The build process is as follows:

1. You need to install `munkipkg`. For this, you need `git`.

    ```
    git clone https://github.com/munki/munki-pkg.git
    chmod +x munki-pkg/munkipkg
    sudo ln -s /path/to/munki-pkg/munkipkg /usr/local/bin/munkipkg
    ```

2. You need `python-jss` in a folder at the same level as your `JSSImporter` folder:

    ```
    git clone https://github.com/jssimporter/python-jss.git
    ```

3. Build!

    ```
    cd JSSImporter
    make
    ```


Acknowledgements
----------------

Huge thanks to Shea Craig, who wrote the bulk of this work and is still providing advice, though not currently involved in Jamf administration.

The world of Mac administration evolves fast, and continued functionality of JSSImporter and python-jss requires active engagement from the Jamf-using Mac Admin community. If you think you can help and have ideas, please go ahead and file issues and pull requests, or contact us in the MacAdmins Slack `#jss-importer` channel.
