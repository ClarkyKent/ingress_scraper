from ingressAPI import IntelMap
import argparse
import json
from pymysql import connect

# Python2 and Python3 compatibility
try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser

DEFAULT_CONFIG = "default.ini"

# SQL Queries #
###############

GYM_SELECT_QUERY = """SELECT {db_gym_id} FROM {db_name}.{db_gym} WHERE {db_gym_name} is NULL AND {db_gym_id} like '%.%'"""
GYM_UPDATE_QUERY = """UPDATE {db_name}.{db_gym} set {db_gym_name}= %s, {db_gym_image} = %s WHERE {db_gym_id} = %s"""

POKESTOP_SELECT_QUERY = """SELECT {db_pokestop_id} FROM {db_name}.{db_pokestop} WHERE {db_pokestop_name} is NULL AND {db_pokestop_id} like '%.%'"""
POKESTOP_UPDATE_QUERY = """UPDATE {db_name}.{db_pokestop} set {db_pokestop_name}= %s, {db_pokestop_image} = %s WHERE {db_pokestop_id} = %s"""

def create_config(config_path):
    """ Parse config. """
    config = dict()
    config_raw = ConfigParser()
    config_raw.read(DEFAULT_CONFIG)
    config_raw.read(config_path)
    config['db_r_host'] = config_raw.get(
        'DB',
        'HOST')
    config['db_r_name'] = config_raw.get(
        'DB',
        'NAME')
    config['db_r_user'] = config_raw.get(
        'DB',
        'USER')
    config['db_r_pass'] = config_raw.get(
        'DB',
        'PASSWORD')
    config['db_r_port'] = config_raw.getint(
        'DB',
        'PORT')
    config['db_r_charset'] = config_raw.get(
        'DB',
        'CHARSET')
    config['db_gym'] = config_raw.get(
        'DB',
        'TABLE_GYM')
    config['db_gym_id'] = config_raw.get(
        'DB',
        'TABLE_GYM_ID')
    config['db_gym_name'] = config_raw.get(
        'DB',
        'TABLE_GYM_NAME')
    config['db_gym_image'] = config_raw.get(
        'DB',
        'TABLE_GYM_IMAGE')
    config['db_pokestop'] = config_raw.get(
        'DB',
        'TABLE_POKESTOP')
    config['db_pokestop_id'] = config_raw.get(
        'DB',
        'TABLE_POKESTOP_ID')
    config['db_pokestop_name'] = config_raw.get(
        'DB',
        'TABLE_POKESTOP_NAME')
    config['db_pokestop_image'] = config_raw.get(
        'DB',
        'TABLE_POKESTOP_IMAGE')
    config['username'] = config_raw.get(
        'Ingress',
        'USERNAME')
    config['pwd'] = config_raw.get(
        'Ingress',
        'PASSWORD')
    config['cookies'] = config_raw.get(
        'Ingress',
        'COOKIES')
    config['encoding'] = config_raw.get(
        'Other',
        'ENCODING')


    return config


def print_configs(config):
    """Print the used config."""
    print("\nFollowing Configs will be used:")
    print("-"*15)    
    print("")
    print("DB:")
    print("Host: {}".format(config['db_r_host']))
    print("Name: {}".format(config['db_r_name']))
    print("User: {}".format(config['db_r_user']))
    print("Password: {}".format(config['db_r_pass']))
    print("Port: {}".format(config['db_r_port']))
    print("Charset: {}".format(config['db_r_charset']))
    print("")
    print("~"*15)


if __name__ == "__main__":
    portal_name = 8
    portal_url = 7
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p", "--pokestop", action='store_true', help="updates pokestop only")
    parser.add_argument(
        "-g", "--gym", action='store_true', help="updates gyms only")
    parser.add_argument(
        "-c", "--config", default="default.ini", help="Config file to use")
    args = parser.parse_args()
    config_path = args.config
    config = create_config(config_path)
    print_configs(config)

    print("Initialize/Start DB Session")
    mydb_r = connect(
        host=config['db_r_host'],
        user=config['db_r_user'],
        passwd=config['db_r_pass'],
        database=config['db_r_name'],
        port=config['db_r_port'],
        charset=config['db_r_charset'],
        autocommit=True)

    mycursor_r = mydb_r.cursor()
    print("Connection clear")
    
    
    IngressLogin = IntelMap(config['cookies'], config['username'], config['pwd'])
    
    if args.gym:
        
        gym_sel_query = GYM_SELECT_QUERY.format(
                    db_gym_id=config['db_gym_id'],
                    db_name=config['db_r_name'],
                    db_gym=config['db_gym'],
                    db_gym_name=config['db_gym_name']
                )
        mycursor_r.execute(gym_sel_query)
        gym_result_ids = mycursor_r.fetchall()
        
        gym_update_query = GYM_UPDATE_QUERY.format(
                db_name=config['db_r_name'],
                db_gym=config['db_gym'],
                db_gym_name=config['db_gym_name'],
                db_gym_image=config['db_gym_image'],
                db_gym_id=config['db_gym_id'],
            )
            
        for gym_id in gym_result_ids:
            ingress_portal_details = IngressLogin.get_portal_details(gym_id[0]).get('result')
            if ingress_portal_details is not None:
                print(ingress_portal_details[portal_name], ingress_portal_details[portal_url])
                insert_args = (ingress_portal_details[portal_name],  ingress_portal_details[portal_url],  gym_id[0] )
                mycursor_r.execute(gym_update_query, insert_args)
            
    if args.pokestop:
    
        pokestop_sel_query = POKESTOP_SELECT_QUERY.format(
                    db_pokestop_id=config['db_pokestop_id'],
                    db_name=config['db_r_name'],
                    db_pokestop=config['db_pokestop'],
                    db_pokestop_name=config['db_pokestop_name']
                )
        mycursor_r.execute(pokestop_sel_query)
        pokestop_result_ids = mycursor_r.fetchall()
    
        pokestop_update_query = POKESTOP_UPDATE_QUERY.format(
                    db_name=config['db_r_name'],
                    db_pokestop=config['db_pokestop'],
                    db_pokestop_name=config['db_pokestop_name'],
                    db_pokestop_image=config['db_pokestop_image'],
                    db_pokestop_id=config['db_pokestop_id'],
                )
                
        for stop_id in pokestop_result_ids:
            ingress_portal_details = IngressLogin.get_portal_details(stop_id[0]).get('result')
            if ingress_portal_details is not None:
                print(ingress_portal_details[portal_name], ingress_portal_details[portal_url])
                insert_args = (ingress_portal_details[portal_name],  ingress_portal_details[portal_url],  stop_id[0] )
                mycursor_r.execute(pokestop_update_query, insert_args)