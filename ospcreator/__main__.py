import sys
from functions import *
import argparse
import getpass
import logging
from keystoneauth1 import identity
from keystoneauth1 import session
from neutronclient.v2_0 import client as neutronClient
from keystoneclient.v3 import client as keystoneClient
from glanceclient.v2 import client as glanceClient

def main(args=None):
    """The main routine."""
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser()
    parser.add_argument('-deo', help='Don\'t do endpoint override', action='store_true')
    parser.add_argument('-gv', help='Generate sample variables yaml file', action='store_true')
    args, unknown = parser.parse_known_args()

    path = os.getcwd()
    varsPath = os.path.join(path, "variables.yml")

    if args.gv:
        generatevars(varsPath)
        exit(0)

    vars = loadyaml(varsPath)
    logging.basicConfig(filename=os.path.join(path, "ospcreator.log"), level=logging.INFO,
                        format='%(asctime)s %(levelname)s:%(message)s')
    logging.info('Started')

    env = loadenvvariables()
    if env:
        username = env["username"]
        password = env["password"]
        project_name = env["project_name"]
        project_domain_name = env["project_domain_name"]
        user_domain_name = env["user_domain_name"]
        auth_url = env["auth_url"]
        logging.info("All env variables loaded.")
    elif "osconf" in vars:
        try:
            username = vars["osconf"]["user"]
            project_name = vars["osconf"]["project"]
            project_domain_name = vars["osconf"]["domain"]
            user_domain_name = vars["osconf"]["domain"]
            auth_url = vars["osconf"]["auth_url"]
            password = getpass.getpass('Password for %s:' % username)
        except Exception as e:
            logging.error("Failed to load authentication variables. Exiting.")
            exit(0)

    auth = identity.Password(auth_url=auth_url,
                             username=username,
                             password=password,
                             project_name=project_name,
                             project_domain_name=project_domain_name,
                             user_domain_name=user_domain_name)
    sess = session.Session(auth=auth)

    try:
        if args.deo:
            keystone = keystoneClient.Client(session=sess)
        else:
            keystone = keystoneClient.Client(session=sess,
                                             endpoint_override=auth_url)
    except Exception as e:
        logging.error("Keystone client could not be initialized. EXITING \n" + str(e))
        exit(1)
        keystone.users.create()

    if "project_name" in vars and "project_description" in vars and "project_domain" in vars:
        newproject = createproject(keystone, vars["project_name"], vars["project_description"], vars["project_domain"])
    else:
        print("Missing project_name or project_description or project_domain in vars file. EXITING")
        exit(1)

    su = raw_input("Assign users and groups to project? [Y/n]: ")
    if su.lower() == 'y' or su == '':
        if "users" in vars:
            users = parseusers(vars["users"])
            if users:
                adduserstoproject(users, newproject, keystone)

        if "groups" in vars:
            groups = parseusers(vars["groups"])
            if groups:
                addgroupstoproject(groups, newproject, keystone)

    si = raw_input("Share images to project? [Y/n]: ")
    if (si.lower() == 'y' or si == '') and "images" in vars:
        images = parseimages(vars["images"])
        if images:
            glance = glanceClient.Client(session=sess)
            shareimages(images, newproject, glance)

    nt = raw_input("Create project networks? [Y/n]: ")
    networks = []
    if (nt.lower() == 'y' or nt == '') and "networks" in vars:
        networks = parsenetworks(vars["networks"])
        if "vncconf" in vars:
            vncconf = vars["vncconf"]
        else:
            vncconf = False
        if networks:
            neutron = neutronClient.Client(session=sess)
            createnetworks(networks, newproject, neutron, vncconf)

    sq = raw_input("Set quotas to project? [Y/n]: ")
    if (sq.lower() == 'y' or sq == '') and "quotas" in vars:
        quotas = vars["quotas"]
        if quotas:
            setquotas(sess, newproject, quotas)

    print("Script finished.")
    logging.warning("FINISHED!")

if __name__ == "__main__":
    main()
