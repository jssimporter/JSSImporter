jss-autopkg-addon
=================

As announced [here](http://www.318.com/2014/01/introducing-jssimporter-for-autopkg/), the file in this repo is an add-on to the [autopkg project](http://autopkg.github.io/autopkg/).

Installation and Setup
=================

Make sure you've already installed the most current autopkg tools (AND RECIPES) FIRST! (Sorry to yell.) Then use the releases tab, to the right above, to download a package that will install the latest release version for you.
To customize the local(ly mounted, if it's a file share) path to your distribution point, jss URL, api user name and password, set the following preferences for the user running autopkg:

```
defaults write com.github.autopkg JSS_REPO /Volumes/JSS_Dist_Point/Packages
defaults write com.github.autopkg JSS_URL https://test.jss.private:8443
defaults write com.github.autopkg API_USERNAME apiUser
defaults write com.github.autopkg API_PASSWORD apiPassword
```

Then please help yourself to the [jss-specific recipes](https://github.com/arubdesu/jssRecipes) that rely on the ones provided by the autopkg org.

Known Issues
=================

Currently it is not possible to add a self-service policy without setting either a smart or static group, and static groups are not available via overrides, you must directly modify the jss recipe. Policies cannot currently be given a category. Recipes with unset versions may cause errors. If run as a recipe-list, an intermittent issue may occur when reaching the  policy addition/update step which may cause the entire process to be interrupted with a "Conflict" error.

Comments/Questions/Ideas
=================

Please share "ideas, patches, documentation, bug reports, or complaints..." ([source](https://github.com/logstash/logstash#contributing)) by either using [issues in this repo](https://github.com/arubdesu/jss-autopkg-addon/issues), or by contacting me in ##osx-server IRC(Allister) or on twitter, [@sacrilicious](https://twitter.com/Sacrilicious) or my email(shouldn't be too hard to find, try [the MacEnterprise list](http://www.macenterprise.org/mailing-list)). 

Please be so kind as to not report issues in the main autopkg/autopkg repo at this time! Thanks for trying it, and again, any contributions are welcome.
