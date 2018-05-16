# ospcreator

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

# Installation

1. Install vnc_api lib (requires Python 2.7):
    ```
    sudo dpkg -i python-contrail_1.1master~0b4d1ac_amd64.deb
    ```

2. Create virtualenv and source it:
    ```
    virtualenv ospcreator
    source ospcreator/bin/activate
    ```

3. Install vnc_lib dependecies:
    ```
    (ospcreator):~# pip install bottle kombu gevent cliff pycassa kazoo consistent-hash bitarray geventhttpclient sqlalchemy psutil
    ```

4. Copy vnc_lib files to virtualenv:
    ```
    cp -r /usr/lib/python2.7/dist-packages/pysandesh ospcreator/lib/python2.7/site-packages/
    cp -r /usr/lib/python2.7/dist-packages/vnc_api ospcreator/lib/python2.7/site-packages/
    cp -r /usr/lib/python2.7/dist-packages/cfgm_common ospcreator/lib/python2.7/site-packages/
    cp -r /usr/lib/python2.7/dist-packages/sandesh_common ospcreator/lib/python2.7/site-packages/
    cp -r /usr/lib/python2.7/dist-packages/libpartition ospcreator/lib/python2.7/site-packages/
    cp -r /usr/lib/python2.7/dist-packages/vnc_api-0.1.dev0.egg-info ospcreator/lib/python2.7/site-packages/
    cp -r /usr/lib/python2.7/dist-packages/ContrailCli-0.1.egg-info ospcreator/lib/python2.7/site-packages/
    cp -r /usr/lib/python2.7/dist-packages/sandesh-0.1.dev0.egg-info ospcreator/lib/python2.7/site-packages/
    cp -r /usr/lib/python2.7/dist-packages/sandesh_common-0.1.dev0.egg-info ospcreator/lib/python2.7/site-packages/
    cp -r /usr/lib/python2.7/dist-packages/ContrailCli ospcreator/lib/python2.7/site-packages/
    cp -r /usr/lib/python2.7/dist-packages/libpartition-0.1.dev0.egg-info ospcreator/lib/python2.7/site-packages/
    cp -r /usr/lib/python2.7/dist-packages/cfgm_common-0.1.dev0.egg-info ospcreator/lib/python2.7/site-packages/
    ```

5. Install ospcreator package in virtualenv:
    ```
    cd ospcreator
    pip install .
    ```

Script should be installed and executable by command ospcreator.

# Usage

If variables.yml file is not found in working directory, then script will ask if you want to generate sample file.

Edit variables regarding needs of OpenStack project.

Variables file contains following sections and parameters:

* `project_name` - name of project (display name)
* `project_description` - text description which will be passed to project properties during creation
* `project_domain` - in which domain should be project created
* `users` - list of users which should be associated to project
* `groups` - similar to users section
* `images` - list of image ids to share to project
* `networks` - list of network dictionaries defining networks.
    * `name` - display name of network
    * `subnet` - CIDR subnet (subnet name is generater from network name)
    * `routes` - routes within subnet
        * `destination` - destination CIDR
        * `nexthop` - gateway in subnet (record above)
    * `rt_asn` - BGP ASN
    * `import_rt` - list of import route targets
    * `export_rt` - list of export route targets
    * `rt` - list of route targets
* `quotas` - section to define project quotas
    * `instances` - number of instances (VMs)
    * `fips` - number of floating IPs
    * `volumes` - number of volumes
    * `vcpus` - number of vcpus
    * `storage` - storage quota (GB)
    * `ram` - ram quota (MB)
* `osconf` - section of OpenStack (keystonerc) credentials
  * `user` - user who is executing actions
  * `project` - project with admin role
  * `auth_url` - endpoint
  * `domain` - domain
* `vncconf` - section of credentials for vnc_api lib
  * `api_host` - contrail api
  * `auth_host` - keystone api
  * `username` - contrail user
  * `password` - contrail user password (can be ommited, script will ask for password)
  * `tenant_name` - project with admin role

Variables `routes`, `rt_asn`, `import_rt`, `export_rt`, `rt` are optional.

Then just run `ospcreator`. Script will ask for password and ask about what steps you want to perform.

Actions are logged into ospcreator.log file in working directory. You can look into this file to verify if everything went well.

Optional arguments:

* -doe -- Don't override keystone endpoint
* -gv -- Generate sample variables file
