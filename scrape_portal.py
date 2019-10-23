from ingressAPI import IntelMap, MapTiles
import argparse
import json
from pymysql import connect
import math
import datetime

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

PORTAL_UPDATE_QUERY = """INSERT INTO {db_ingress}.ingress_portals(external_id, name, url, lat, lon, updated, imported) VALUES(%s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE updated =%s, name=%s, url=%s, lat=%s, lon=%s"""

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
    config['db_ingress'] = config_raw.get(
        'DB',
        'DB_INGRESS')
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
    config['bbox'] = config_raw.get(
        'Area',
        'BBOX')

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

def get_all_portals(login, bbox):
    mTiles = MapTiles(bbox)
    tiles = mTiles.getTiles()
    total_tiles = len(tiles)
    print("Number of tiles in boundry are : ",total_tiles)
    timed_out_items = []
    portals = []
    portal_id = []
    for idx, tile in enumerate(tiles):
        iitc_xtile = int( tile[0] )
        iitc_ytile = int( tile[1] )
        
        iitc_tile_name  = ('{0}_{1}_{2}_0_8_100').format(zoom, iitc_xtile, iitc_ytile)
        current_tile = idx+1
        print(str("{0}/{1} Getting portals from tile : {2}").format(current_tile, total_tiles, iitc_tile_name))
        tiles_data = login.get_entities([iitc_tile_name])

        if 'result' in tiles_data:
                for data in tiles_data['result']['map']:
                    if 'error' in tiles_data['result']['map'][data]:
                        timed_out_items.append(data)
                    else:
                        for entry in tiles_data['result']['map'][data]['gameEntities']:
                            #print(entry)
                            if entry[2][0] == 'p':
                                portal_id.append(entry[0])
                                portals.append(entry[2])
                                #print(entry[0])
    return portals, portal_id

if __name__ == "__main__":
    portal_name = 8
    portal_url = 7
    zoom = 15
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p", "--pokestop", action='store_true', help="updates pokestop only")
    parser.add_argument(
        "-g", "--gym", action='store_true', help="updates gyms only")
    parser.add_argument(
        "-all", "--all_poi", action='store_true', help="updates gyms, pokestops and ingress portals")
    parser.add_argument(
        "-i", "--ingress", action='store_true', help="updates ingress portal table")
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
    updated_gyms = 0
    updated_pokestops = 0
    
    IngressLogin = IntelMap(config['cookies'], config['username'], config['pwd'])

    if args.all_poi or args.ingress:
        bbox = list(map(float, config['bbox'].split(',')))
        bbox.append(zoom)
        all_portal_details, all_portals_id = get_all_portals(IngressLogin, bbox)
        
    if args.ingress:
    
        print("Initialize/Start DB Session")
        mydb_r = connect(
            host=config['db_r_host'],
            user=config['db_r_user'],
            passwd=config['db_r_pass'],
            database=config['db_ingress'],
            port=config['db_r_port'],
            charset=config['db_r_charset'],
            autocommit=True)

        mycursor_ingres = mydb_r.cursor()
        print("Connection clear")
    
        portal_update_query = PORTAL_UPDATE_QUERY.format(
                db_ingress=config['db_ingress']
            )
        for idx, val in enumerate(all_portals_id):
            lat = (all_portal_details[idx][2])/1e6
            lon = (all_portal_details[idx][3])/1e6
            updated_ts = datetime.datetime.now().strftime("%s")
            insert_portal_args = (val,  all_portal_details[idx][portal_name],  all_portal_details[idx][portal_url], lat, lon, updated_ts, updated_ts, updated_ts, all_portal_details[idx][portal_name],  all_portal_details[idx][portal_url], , lat, lon)
            try:
                mycursor_ingres.execute(portal_update_query, insert_portal_args)
                print("~"*50)
                print("inserted ", all_portal_details[idx][portal_name]," ", all_portal_details[idx][portal_name], " into ingress table")
                print("~"*50)
            except Exception as e:
                print(e)
                print("#"*50)
                print('could not put in db {0} ').format(val)
                print("#"*50)

    if args.all_poi:
        
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
            try:
                single_portal_detail = all_portal_details[all_portals_id.index(gym_id[0])]
                insert_args = (single_portal_detail[portal_name],  single_portal_detail[portal_url],  gym_id[0] )
                try:
                    mycursor_r.execute(gym_update_query, insert_args)
                    updated_gyms = updated_gyms +1
                    print(gym_id[0], single_portal_detail[portal_name], single_portal_detail[portal_url], ' succeeded and updated in DB')
                except Exception as e:
                    print("~"*15)
                    print(gym_id[0], ' Could not update in DB')
                    print("~"*15)
                    print(e)
                    print("~"*15)
            except Exception as e:
                print(e)
                print('Did not {0} find missing gym_id in given BBOX boundry').format(gym_id)
        print('Total gyms updated: ', updated_gyms)

    
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
            try:
                single_portal_detail = all_portal_details[all_portals_id.index(stop_id[0])]
                insert_args = (single_portal_detail[portal_name],  single_portal_detail[portal_url],  stop_id[0] )                
                try:
                    mycursor_r.execute(pokestop_update_query, insert_args)
                    updated_pokestops = updated_pokestops + 1
                    print(stop_id[0], single_portal_detail[portal_name], single_portal_detail[portal_url], ' succeeded and updated in DB')
                except Exception as e:
                    print("~"*15)
                    print(stop_id[0], ' Could not update in DB')
                    print("~"*15)
                    print(e)
                    print("~"*15)
                    
            except Exception as e:
                print('Did not find missing pokestop_id in given BBOX boundry' )
        print('Total pokestops updated: ', updated_pokestops)

    else:
        if args.gym:
        
            gym_sel_query = GYM_SELECT_QUERY.format(
                        db_gym_id=config['db_gym_id'],
                        db_name=config['db_r_name'],
                        db_gym=config['db_gym'],
                        db_gym_name=config['db_gym_name']
                    )
            mycursor_r.execute(gym_sel_query)
            gym_result_ids = mycursor_r.fetchall()
            
            print('Total gyms found: ', len(gym_result_ids))
            
            gym_update_query = GYM_UPDATE_QUERY.format(
                    db_name=config['db_r_name'],
                    db_gym=config['db_gym'],
                    db_gym_name=config['db_gym_name'],
                    db_gym_image=config['db_gym_image'],
                    db_gym_id=config['db_gym_id'],
                )
                
            for gym_id in gym_result_ids:
                ingress_portal_details = IngressLogin.get_portal_details(gym_id[0])
                if ingress_portal_details is not None:
                    insert_args = (ingress_portal_details.get('result')[portal_name],  ingress_portal_details.get('result')[portal_url],  gym_id[0] )
                    try:
                        mycursor_r.execute(gym_update_query, insert_args)
                        updated_gyms = updated_gyms +1
                        print(gym_id[0], ingress_portal_details.get('result')[portal_name], ingress_portal_details.get('result')[portal_url], ' succeeded and updated in DB')
                    except Exception as e:
                        print("~"*15)
                        print(gym_id[0], ' Could not update in DB')
                        print("~"*15)
                        print(e)
                        print("~"*15)
                else:
                    print('Could not parse portal info for ', gym_id[0], 'check if it is valid portal', )
                    
            print('Total gyms updated: ', updated_gyms)
            
        if args.pokestop:
        
            pokestop_sel_query = POKESTOP_SELECT_QUERY.format(
                        db_pokestop_id=config['db_pokestop_id'],
                        db_name=config['db_r_name'],
                        db_pokestop=config['db_pokestop'],
                        db_pokestop_name=config['db_pokestop_name']
                    )
            mycursor_r.execute(pokestop_sel_query)
            pokestop_result_ids = mycursor_r.fetchall()
            
            print('Total pokestops found: ', len(pokestop_result_ids))
            
            pokestop_update_query = POKESTOP_UPDATE_QUERY.format(
                        db_name=config['db_r_name'],
                        db_pokestop=config['db_pokestop'],
                        db_pokestop_name=config['db_pokestop_name'],
                        db_pokestop_image=config['db_pokestop_image'],
                        db_pokestop_id=config['db_pokestop_id'],
                    )
                    
            for stop_id in pokestop_result_ids:
                ingress_portal_details = IngressLogin.get_portal_details(stop_id[0])
                if ingress_portal_details is not None:
                    print(ingress_portal_details.get('result')[portal_name], ingress_portal_details.get('result')[portal_url])
                    insert_args = (ingress_portal_details.get('result')[portal_name],  ingress_portal_details.get('result')[portal_url],  stop_id[0] )                
                    try:
                        mycursor_r.execute(pokestop_update_query, insert_args)
                        print(stop_id[0], ingress_portal_details.get('result')[portal_name], ingress_portal_details.get('result')[portal_url], ' succeeded and updated in DB')
                        updated_pokestops = updated_pokestops + 1
                    except Exception as e:
                        print("~"*15)
                        print(stop_id[0], ' Could not update in DB')
                        print("~"*15)
                        print(e)
                        print("~"*15)
                        
                else:
                    print('Could not parse portal info for ', stop_id[0], 'check if it is valid portal', )
                    
            print('Total pokestops updated: ', updated_pokestops)
