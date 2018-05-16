ospcreator
-----------

OpenStack project creator which uses yaml variables file to setup OpenStack project.

Script will do:

* Create project or use existing project if project with defined name already exists
* Add users and grant specified roles on project for them
* Share list of images (image ids)
* Create networks inside project

    * Create network
    * Create subnet with specified CIDR
    * Update subnet with host routes if routes are specifed
    * Update network's route targets in OpenContrail if route targets are specified and vnc_api library is present

* Set defined quotas to project


Usage
-----

When running for the first time or if `variables.yml` file is not found in working directory, variables file is generated.

Edit `variables.yml` file according your needs. Authentication variables for OpenStack will be gathered from environment
if some needed variable is missing then authentication variables are fetched from variables file and user is prompted
for password.

Actions done by script are logged into ospcreator.log log file in working directory.

Optional arguments:

* -doe -- Don't override keystone endpoint
* -gv -- Generate sample variables file