JSS Production Recipes
======================

**Warning: in active, but early, development!**

JSS Production Recipes (`.jss-prod`) are intended to work alongside `.jss` recipes in order to control the promotion of products to production.

Why?
----

`jss_helper` can easily add a package to an existing policy. So, if you are happy to manually create the production policies, you probably don't need to read any further. However, if you wish to automate the creation of your production policies and associated smart groups, these recipes can do that for you.

These recipes are also designed to create a separate, trigger-only policy scoped to all computers. This allows you to build a list of triggers that can be used in onboarding scripts, DEPNotify, SplashBuddy etc., or for separate, auto-install and auto-update policies. (A further iteration of this project, already in use internally at my organisation, automatically creates those policies too.)

How?
----

Rather than have the `.pkg` recipe as the Parent Recipe, this project includes a Processor named `JSSRecipeReceiptChecker`. This reads the latest receipt from the AutoPkg run of the `.jss` recipe of the same `NAME` as the `.jss-prod` recipe, and gathers the required information to produce the production policy and smart group:

* `pkg_path`
* `version`
* `CATEGORY`
* `SELF_SERVICE_DESCRIPTION`

Since there is no parent recipe, and the pkg source is predictable as the Cache folder of the `.jss` recipe, a single recipe named `ProdSelfService.jss-prod.recipe` can be used for most production policies. All that is required is to make a Recipe Override for each application, substituting the `NAME` value.

It is also possible to override many other keys if required - just check out the `Input` variables in `ProdSelfService.jss-prod.recipe` to see what's overridable.  

I am providing some `.jss-prod` recipes in this folder, which take `com.github.grahampugh.recipes.jss-prod.prod-self-service` as the parent. In most cases it isn't actually required to have a recipe for all apps, just an override, but it is a valid option, and could make it easier for people to use.
