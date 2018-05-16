import yaml
import yaml.error
import logging
import os
import getpass
from keystoneauth1 import exceptions as KeystoneExceptions
from neutronclient.v2_0 import client as neutronClient
from novaclient import client as novaClient
from cinderclient import client as cinderClient
#from vnc_api import vnc_api
vncexists = False
try:
    from vnc_api import vnc_api
    vncexists = True
except ImportError:
    vncexists = False
    pass


class Network:
    name = None
    subnet = None
    import_rt = []
    export_rt = []
    rt = []
    rt_asn = None
    routes = []

    def __init__(self, name, subnet):
        self.name = name
        self.subnet = subnet
        self.import_rt = []
        self.export_rt = []
        self.rt = []
        self.routes = []
        self.rt_asn = None

    def addroute(self, dst_network, nexthop):
        route = {'destination': dst_network, 'nexthop': nexthop}
        # route["dst_network"] = dst_network
        # route["nexthop"] = nexthop
        self.routes.append(route)


def loadyaml(path):
    try:
        with open(path) as f:
            try:
                vars = f.read()
                vars = yaml.load(vars)
            except yaml.error.YAMLError as e:
                logging.error("Processing vars yaml file failed! EXITING. \n" + str(e))
                exit(1)
    except IOError as e:
        logging.error("Processing vars file failed! \n" + str(e))
        print("Variables file not found in working directory \n")
        gv = raw_input("Do you want to generate sample variables file? [Y/n]: ")
        if gv.lower() == 'y' or gv == '':
            generatevars(path)
            print("Variables file generated in working directory. Exiting.")
            exit(0)
        else:
            print("Exiting.")
            exit(0)
    return vars


def parserts(rts):
    irts = []
    for irt in rts:
        irts.append(irt)
    return irts


def parsenetworks(networks):
    ntws = []
    try:
        for network in networks:
            if "name" in network:
                ntw = Network(network["name"], network["subnet"])
                if "routes" in network:
                    for route in network["routes"]:
                        if "destination" in route and "nexthop" in route:
                            ntw.addroute(route["destination"], route["nexthop"])
                if "import_rt" in network:
                    ntw.import_rt = parserts(network["import_rt"])
                if "export_rt" in network:
                    ntw.export_rt = parserts(network["export_rt"])
                if "rt" in network:
                    ntw.rt = parserts(network["rt"])
                if "rt_asn" in network:
                    ntw.rt_asn = network["rt_asn"]
                ntws.append(ntw)
        return ntws
    except Exception as e:
        logging.warning("Processing networks failed! Skipping networks section.\n" + str(e))
        ntws = []
        return ntws


def parseimages(images):
    imgs = []
    try:
        for image in images:
            imgs.append(image)
        return imgs
    except Exception:
        logging.warning("Processing images failed! Skipping images section.")
        return False


def parseusers(users):
    usersl = []
    try:
        for user in users:
            if "name" in user and "role" in user:
                usersl.append(user)
    except Exception:
        logging.warning("Processing users failed! Skipping users section.")
        return False
    return usersl


def loadenvvariables():
    keystonerc = {}
    try:
        keystonerc["username"] = os.environ['OS_USERNAME']
        keystonerc["password"] = os.environ['OS_PASSWORD']
        keystonerc["project_name"] = os.environ['OS_PROJECT_NAME']
        keystonerc["project_domain_name"] = os.environ['OS_USER_DOMAIN_NAME']
        keystonerc["user_domain_name"] = os.environ['OS_USER_DOMAIN_NAME']
        keystonerc["auth_url"] = os.environ['OS_AUTH_URL']
        return keystonerc
    except Exception:
        keystonerc = {}
        logging.warning("Processing env variables failed! Skipping using keystonerc from env.")
        return keystonerc


def createproject(keystone, name, description, domain):
    try:
        newproject = keystone.projects.list(name=name)
        if newproject:
            pom = raw_input("Project with this name already exists. \nDo you want to exit? [Y/n]: ")
            if pom.lower() == "y" or pom == '':
                exit(0)
            newproject = newproject[0]
            print("Using project " + newproject.__getattribute__("name") + " ID: " + newproject.__getattribute__("id") +
                  "for following actions")
            return newproject
        else:
            newproject = keystone.projects.create(name=name, description=description, domain=domain)
            logging.info(newproject)
            return newproject
    except KeystoneExceptions.Forbidden as e:
        logging.error("Problem occurred during listing projects. EXITING\n" + str(e))
        exit(1)
    except Exception as e:
        logging.error("Problem occurred during listing projects. EXITING\n" + str(e))
        exit(1)


def adduserstoproject(users, project, keystone):
    for usr in users:
        try:
            role = keystone.roles.list(name=usr["role"])[0]
            user = keystone.users.list(name=usr["name"])[0]
            keystone.roles.grant(role=role, user=user, project=project)
            logging.info("Role " + usr["role"] + " granted for user " + usr["name"])
        except Exception as e:
            logging.error("Problem occurred during granting role on project for " + usr["name"] + "\n" + str(e))


def addgroupstoproject(groups, project, keystone):
    for grp in groups:
        try:
            role = keystone.roles.list(name=grp["role"])[0]
            group = keystone.groups.list(name=grp["name"])[0]
            keystone.roles.grant(role=role, group=group, project=project)
            logging.info("Role " + grp["role"] + " granted for group " + grp["name"])
        except Exception as e:
            logging.error("Problem occurred during granting role on project for " + grp["name"] + "\n" + str(e))


def shareimages(images, project, glance):
    for img in images:
        try:
            glance.image_members.create(img, project.__getattribute__("id"))
            glance.image_members.update(img, project.__getattribute__("id"), "accepted")
            logging.info("Image " + img + " shared")
        except Exception as e:
            logging.error("Problem occurred during image sharing on project for image: " + img + "\n" + str(e))


def createnetworks(networks, project, neutron, vncconf):
    vnc = None
    if vncexists:
        if vncconf:
            if "password" not in vncconf:
                vncconf["password"] = getpass.getpass('[vnc_api] Password for %s:' % vncconf["username"])
            try:
                vnc = vnc_api.VncApi(api_server_host=vncconf["api_host"],
                                     auth_host=vncconf["auth_host"],
                                     username=vncconf["username"],
                                     password=vncconf["password"],
                                     tenant_name=vncconf["tenant_name"])
                logging.info("vnc_api initialized.")
            except Exception as e:
                logging.error("Problem occurred during vnc_api initialization \n" + str(e))
    for net in networks:
        try:
            netname = net.name
            id = project.__getattribute__("id")
            network = {'name': netname,
                       'admin_state_up': 'True',
                       'tenant_id': id,
                       'project_id': id}
            nt = neutron.create_network({'network': network})
            subnetname = net.name + "_subnet"
            subnet = {"name": subnetname,
                      "tenant_id": id,
                      "cidr": net.subnet,
                      "network_id": nt["network"]["id"],
                      "ip_version": 4}
            sn = neutron.create_subnet({'subnet': subnet})
            logging.info("Subnet " + str(sn) + " created.")
            if net.routes:
                update = {'host_routes': net.routes}
                su = neutron.update_subnet(sn["subnet"]["id"], {'subnet': update})
                logging.info("Subnet " + str(su) + " updated with routes.")
        except Exception as e:
            logging.error("Problem occurred during creating network on project \n" + str(e))
        if vncexists:
            if net.rt_asn and (net.rt or net.import_rt or net.export_rt):
                processroutetarget(net, nt, vnc)


def creatertlist(rts, asn):
    rtl = vnc_api.RouteTargetList()
    for rt in rts:
        tar = "target:" + str(asn) + ":" + str(rt)
        rtl.add_route_target(tar)
    return rtl


def processroutetarget(net, nt, vnc):
    if isinstance(vnc, vnc_api.VncApi):
        try:
            # vnc = vnc_api.VncApi(api_server_host=vncconf["api_host"],
            #                      auth_host=vncconf["auth_host"],
            #                      username=vncconf["username"],
            #                      password=vncconf["password"],
            #                      tenant_name=vncconf["tenant_name"])
            if net.rt_asn:
                if net.rt:
                    rtl = creatertlist(net.rt, net.rt_asn)
                    network = vnc.virtual_network_read(id=nt["network"]["id"])
                    network.set_route_target_list(rtl)
                    vnc.virtual_network_update(network)
                    logging.info("Network " + net.name + " update with rts." + str(rtl))
                if net.import_rt:
                    rtl = creatertlist(net.import_rt, net.rt_asn)
                    network = vnc.virtual_network_read(id=nt["network"]["id"])
                    network.set_import_route_target_list(rtl)
                    vnc.virtual_network_update(network)
                    logging.info("Network " + net.name + " update with import rts." + str(rtl))
                if net.export_rt:
                    rtl = creatertlist(net.export_rt, net.rt_asn)
                    network = vnc.virtual_network_read(id=nt["network"]["id"])
                    network.set_export_route_target_list(rtl)
                    vnc.virtual_network_update(network)
                    logging.info("Network " + net.name + " update with export rts." + str(rtl))
        except KeyError as e:
            logging.error("Problem occurred during route targets assigning. KeyError: \n" + str(e))
        except Exception as e:
            logging.error("Problem occurred during route targets assigning \n" + str(e))


def setquotas(sess, project, quotas):
    try:
        neutron = neutronClient.Client(session=sess)
        fip = {'floatingip': '0'}
        if "fips" in quotas:
            fip = {'floatingip': quotas['fips']}
        elif "instances" in quotas:
            fip = {'floatingip': quotas['instances']}
        nt = neutron.update_quota(project.__getattribute__("id"), {'quota': fip})
        logging.info("Neutron quota updated " + str(nt))

        nova = novaClient.Client(version="2", session=sess)
        cores = 20
        instances = 10
        ram = 40960
        if "vcpus" in quotas:
            cores = quotas["vcpus"]
        if "instances" in quotas:
            instances = quotas["instances"]
        if "ram" in quotas:
            ram = quotas["ram"]
        no = nova.quotas.update(project.__getattribute__("id"), cores=cores, instances=instances, ram=ram)
        logging.info("Nova quota updated " + str(no))

        cinder = cinderClient.Client(version="3", session=sess)
        volumes = 10
        storage = 1000
        if "volumes" in quotas:
            volumes = quotas["volumes"]
        if "storage" in quotas:
            storage = quotas["storage"]
        ci = cinder.quotas.update(project.__getattribute__("id"), volumes=volumes, snapshots=volumes, gigabytes=storage)
        logging.info("Cinder quota updated " + str(ci))
    except Exception as e:
        logging.error("Problem occurred during setting quotas \n" + str(e))


def generatevars(path):
    v = """project_name: DemoProject
project_description: Demo project description
project_domain: default
users:
  - name: admin
    role: admin
  - name: operations
    role: Member
groups:
  - name: admin_grup
    role: Member
images:
  - adb486ef-6bc4-47d3-b0a9-27b9aab5900f
  - 8fd41391-2d25-4d53-89ef-f47d953e619e
  - a763181a-0ce0-47fe-8546-8b1cbf277e90
  - b0f4bb57-efa1-4c45-a958-a3b10e37456d
  - 832d37df-e49f-42cc-8f44-fa7d9261b3dc
networks:
  - name: networkA
    subnet: 192.168.0.0/24
    routes:
      - destination: 172.16.0.0/24
        nexthop: 192.168.0.1
      - destination: 10.16.0.0/24
        nexthop: 192.168.0.1
    rt_asn: 64651
    import_rt:
      - 60000
      - 60002
    export_rt:
      - 60001
  - name: networkB
    subnet: 10.20.30.0/24
quotas:
  instances: 10
  fips: 10
  volumes: 10
  vcpus: 20
  storage: 1000
  ram: 102400
osconf:
  user: mylogin
  project: adminproject
  auth_url: https://myopenstackdeployment.com:5000/v3
  domain: default
vncconf:
  api_host: 192.168.8.15
  auth_host: 192.168.8.11
  username: contrailadmin
  password: supersecret
  tenant_name: admin
"""
    with open(path, 'w') as f:
        f.write(v)
        f.close()
