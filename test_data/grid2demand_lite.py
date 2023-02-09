import os
import pandas as pd
import numpy as np
import math
import csv
import sys


g_output_folder = ''

# node
g_node_list = []
g_node_id_to_index = {}
g_number_of_original_nodes = 0

# boundary
g_boundary_node_list = []
g_outside_boundary_node_list = []
g_outside_boundary_node_id_index = {}

g_access_node_list = []
g_access_node_id_index = {}
g_access_node_id_to_node = {}

# zone
g_zone_list = []
g_number_of_zones = 0
g_zone_id_list = []
g_zone_index_dict = {}
g_node_zone_dict = {}
g_used_latitude = 0

# lattitude
g_average_latitude = 0
g_scale_list = [0.006, 0.005, 0.004, 0.003, 0.002, 0.001]
g_degree_length_dict = {60: 55.8, 51: 69.47, 45: 78.85, 30: 96.49, 0: 111.3}

# matrix
g_o_zone_id_list = []
g_o_zone_name_list = []
g_d_zone_id_list = []
g_d_zone_name_list = []
g_od_distance_list = []
g_od_geometry_list = []
g_distance_matrix = []

# demand
g_node_prod_list = []
g_node_attr_list = []
g_node_id_list = []
g_node_zone_id_list = []
g_node_production_dict = {}
g_node_attraction_dict = {}
g_trip_matrix = []
g_total_production_list = []
g_total_attraction_list = []
g_zone_to_access_nodes_dict = {}

alphabet_list = []
for letter in range(65, 91):
    alphabet_list.append(chr(letter))

for letter_1 in range(65, 91):
    for letter_2 in range(65, 91):
        alphabet_list.append(chr(letter_1)+chr(letter_2))

for letter_1 in range(65, 91):
    for letter_2 in range(65, 91):
        for letter_3 in range(65, 91):
            alphabet_list.append(chr(letter_1)+chr(letter_2)+chr(letter_3))


class Node:
    def __init__(self):
        self.id = 0
        self.zone_id = None
        # commments: default is 0, or no value; only three conditions for a node to become an activity node
        # and zone_id != 0: 1) POI node, 2) is_boundary node(freeway) 3) residential in activity_type
        self.node_type = ''
        self.x_coord = 0
        self.y_coord = 0
        self.production = 0 # commments: = 0 (current node is not poi node)
        self.attraction = 0 # commments: = 0 (current node is not poi node)
        self.boundary_flag = 0  # comments: = 1 (current node is boundry node)
        self.poi_id = ''  # commments: default = None; to be assigned to a POI ID after reading poi.csv
        # if current node is poi ndoe
        self.activity_type = '' # commments: provided from osm2gmns such as motoway, residential, ...
        self.activity_location_tab = ''
        self.osm_node_id = ''


class Zone: # comments: area of grid zone
    def __init__(self):
        self.id = 0
        self.name = '' # comments: internal No., such as A1, A2,...
        self.centroid_x = 0
        self.centroid_y = 0
        self.centroid = '' # comments: centroid coordinate (x, y) based on wkt format
        self.x_max = 0  # comments: boundary coordinate for this zone
        self.x_min = 0
        self.y_max = 0
        self.y_min = 0
        self.poi_count = 0 # comments: total poi counts in this zone
        self.residential_count = 0  # number of residential poi nodes in the zone
        self.office_count = 0  # number of office poi nodes in the zone
        self.shopping_count = 0  # number of shopping poi nodes in the zone
        self.school_count = 0  # number of school poi nodes in the zone
        self.parking_count = 0  # number of parking poi nodes in the zone
        self.boundary_count = 0  # number of boundary nodes in the zone
        self.node_id_list = [] # comments: nodes which belong to this zone
        self.access_node_id_list = [] # comments: access nodes which belong to this zone
        self.poi_node_list = []
        self.polygon = '' # comments: study area boundary based on wkt format
        self.connector_list = []
        self.centroid_node = None
        self.attraction = 0
        self.production = 0


def read_node_csv(input_folder=None):
    global g_poi_id_type_dict
    global g_poi_id_area_dict
    global g_output_folder
    global g_average_latitude
    global g_number_of_original_nodes
    global g_access_node_list
    global g_access_node_id_index

    if input_folder:
        node_filepath = os.path.join(input_folder, 'node.csv')
        poi_filepath = os.path.join(input_folder, 'poi.csv')
        g_output_folder = input_folder
        logfile = os.path.join(g_output_folder, 'log.txt')
    else:
        node_filepath = 'node.csv'
        poi_filepath = 'poi.csv'
        logfile = 'log.txt'


    access_node_index = 0
    with open(node_filepath, errors='ignore') as fp:
        reader = csv.DictReader(fp)
        exclude_boundary_node_index = 0
        poi_flag = 0
        log_flag = 0
        index = 0
        for line in reader:
            if line['node_id'] != '' and line['poi_id'] == '' and \
                    int(float(line['is_boundary'])) >= -1 and int(float(line['is_boundary'])) <= 2:
                node = Node()
                node_id = line['node_id']
                if node_id:
                    node.id = int(float(node_id))
                    g_node_id_to_index[node.id] = index
                else:
                    print("node_id is not defined in node.csv, please check it!")
                    sys.exit(0)

                try:
                    osm_node_id = line['osm_node_id']
                    if osm_node_id:
                        node.osm_node_id = str(osm_node_id)
                except:
                    node.osm_node_id = None

                try:
                    activity_type = line['activity_type']
                    if activity_type:
                        node.activity_type = str(activity_type)
                        if node.activity_type == 'residential':
                            node.activity_location_tab = 'residential'
                        if node.activity_type == 'poi':
                            node.activity_location_tab = 'poi'
                except:
                    node.activity_type = None

                x_coord = line['x_coord']
                if x_coord:
                    node.x_coord = round(float(x_coord),7)
                else:
                    # print('Error: x_coord is not defined in node.csv, please check it!')
                    print("x_coord is not defined in node.csv, please check it!")
                    sys.exit(0)

                y_coord = line['y_coord']
                if y_coord:
                    node.y_coord = round(float(y_coord),7)
                else:
                    # print('Error: y_coord is not defined in node.csv, please check it!')
                    print("y_coord is not defined in node.csv, please check it!")
                    sys.exit(0)

                try:
                    poi_id = line['poi_id']
                    if poi_id:
                        node.poi_id = str(poi_id)
                        poi_flag = 1  # comments: = 1 if poi_id exists
                except:
                    print("poi_id is not defined. Please check it in node.csv.")

                try:
                    boundary_flag = int(float(line['is_boundary']))
                    if boundary_flag:
                        node.boundary_flag = boundary_flag
                        if node.boundary_flag == -1:
                            node.activity_location_tab = 'boundary node only with incoming links'
                        elif node.boundary_flag == 1:
                            node.activity_location_tab = 'boundary node only with outgoing links'
                        elif node.boundary_flag == 2:
                            node.activity_location_tab = 'boundary node with both incoming and outgoing links'
                    else:
                        #print("is_boundary is not defined in node.csv. Default value is 0.")
                        node.boundary_flag = int(0)
                except:
                    print("is_boundary is not defined in node.csv. Default value is 0.")
                    node.boundary_flag = int(0)

                # g_node_id_to_node[node.id] = node
                g_node_list.append(node)

                if node.boundary_flag == 1 or node.boundary_flag == -1 or node.boundary_flag == 2:
                    g_boundary_node_list.append(node)
                    g_access_node_list.append(node)
                    g_access_node_id_index[node.id] = access_node_index
                    g_access_node_id_to_node[node.id] = node
                    access_node_index += 1
                else:
                    g_outside_boundary_node_list.append(node) # comments: outside boundary node
                    g_outside_boundary_node_id_index[node.id] = exclude_boundary_node_index
                    exclude_boundary_node_index += 1

                index += 1

        g_number_of_original_nodes = index

        if poi_flag == 0:
            if (log_flag == 0):
                # print('Field poi_id is not in node.csv. Please check it!')
                # logger.warning('Field poi_id is NOT defined in node.csv. Please check node.csv! '
                #                '(It could lead to empty demand volume and zero agent. '
                #                'Please ensure including POI=True when running osm2gmns.)')
                log_flag = 1

        try:
            g_latitude_list = [node.y_coord for node in g_node_list]
            g_average_latitude = sum(g_latitude_list) / len(g_latitude_list)
        except:
            g_average_latitude = 99
            print('Please check y_coord in node.csv!')


def nodes_to_zone_grids(number_of_x_blocks=None, number_of_y_blocks=None, latitude=None):

    global g_number_of_zones
    global g_zone_id_list
    global g_zone_index_dict
    global g_node_zone_dict
    global g_used_latitude
    global g_average_latitude
    global g_number_of_original_nodes
    global g_access_node_list
    global g_access_node_id_index
    global access_node_vector_list

    # initialize parameters
    x_max = max(node.x_coord for node in g_node_list)
    x_min = min(node.x_coord for node in g_node_list)
    y_max = max(node.y_coord for node in g_node_list)
    y_min = min(node.y_coord for node in g_node_list)

    if latitude is None:  # use the average latitude according to node.csv
        if g_average_latitude == 99:
            latitude = 30  # comments: default value if no given latitude value
            flat_length_per_degree_km = g_degree_length_dict[latitude]
            g_used_latitude = latitude
            #logger.warning('Please check y_coord in node.csv! Default latitude is 30 degree!')
        else:
            # match the closest latitude key according to the given latitude
            dif = float('inf')
            for i in g_degree_length_dict.keys():
                if abs(abs(g_average_latitude) - i) < dif:
                    temp_latitude = i
                    dif = abs(abs(g_average_latitude) - i)
                    # temp_latitude = 30
                    g_used_latitude = temp_latitude
            flat_length_per_degree_km = g_degree_length_dict[temp_latitude]
    else:  # use the given latitude
        # match the closest latitude key according to the given latitude
        dif = float('inf')
        for i in g_degree_length_dict.keys():
            if abs(abs(latitude) - i) < dif:
                temp_latitude = i
                dif = abs(abs(latitude) - i)
                g_used_latitude = temp_latitude
        flat_length_per_degree_km = g_degree_length_dict[temp_latitude]


    print('\nLatitude used for grid partition = ', g_used_latitude)


    # Case 0: Default
    if (number_of_x_blocks is None) and (number_of_y_blocks is None):
        x_length_range = (x_max - x_min) * flat_length_per_degree_km
        y_length_range = (y_max - y_min) * flat_length_per_degree_km
        default_scale = 0.005 * math.ceil(max(x_length_range, y_length_range)/10)
        scale_x = default_scale
        scale_y = default_scale
        # scale_x = g_scale_list[0]
        # scale_y = g_scale_list[0]
        x_max = math.ceil(x_max / scale_x) * scale_x
        x_min = math.floor(x_min / scale_x) * scale_x
        y_max = math.ceil(y_max / scale_y) * scale_y
        y_min = math.floor(y_min / scale_y) * scale_y
        number_of_x_blocks = round((x_max - x_min) / scale_x)
        number_of_y_blocks = round((y_max - y_min) / scale_y)

    # Case 1: Given number_of_x_blocks and number_of_y_blocks
    if (number_of_x_blocks is not None) and (number_of_y_blocks is not None):
        scale_x = round((x_max - x_min) / number_of_x_blocks, 5) + 0.00001
        scale_y = round((y_max - y_min) / number_of_y_blocks, 5) + 0.00001
        x_max = round(x_min + scale_x * number_of_x_blocks, 5)
        y_min = round(y_max - scale_y * number_of_y_blocks, 5)

    block_numbers = number_of_x_blocks * number_of_y_blocks
    x_temp = round(x_min, 5)
    y_temp = round(y_max, 5)

    for block_no in range(1, block_numbers + 1):
        block = Zone()
        block.id = block_no
        block.x_min = x_temp
        block.x_max = x_temp + scale_x
        block.y_max = y_temp
        block.y_min = y_temp - scale_y

        for node in g_node_list:
            if ((node.x_coord <= block.x_max) and (node.x_coord >= block.x_min) \
                    and (node.y_coord <= block.y_max) and (node.y_coord >= block.y_min)):
                node.zone_id = str(block.id)

            if ((node.x_coord <= block.x_max) and (node.x_coord >= block.x_min)\
                & (node.y_coord <= block.y_max) and (node.y_coord >= block.y_min)) and \
                    (node.boundary_flag != -2 and node.boundary_flag != 0):
                node.zone_id = str(block.id)
                g_node_zone_dict[node.id] = block.id
                block.node_id_list.append(node.id)

            # Boundary nodes will be acted as access nodes.
            if ((node.x_coord <= block.x_max) and (node.x_coord >= block.x_min) \
                and (node.y_coord <= block.y_max) and (node.y_coord >= block.y_min)) and \
                    (node.boundary_flag == -1 or node.boundary_flag == 1 or node.boundary_flag == 2):
                block.access_node_id_list.append(node.id)

        # for poi in g_poi_list:
        #     if ((poi.x_coord <= block.x_max) and (poi.x_coord >= block.x_min) \
        #             and (poi.y_coord <= block.y_max) and (poi.y_coord >= block.y_min)):
        #         poi.zone_id = block.id
        #         g_poi_zone_dict[poi.id] = block.id
        #         block.access_node_id_list.append(poi.node_id)
        #         block.poi_node_list.append(poi)

        # get centroid coordinates of each zone with nodes by calculating average x_coord and y_coord
        if len(block.node_id_list) != 0:
            #block.poi_count = len(block.poi_node_list)
            try:
                block.centroid_x = sum(g_access_node_list[g_access_node_id_index[node_id]].x_coord for
                                       node_id in block.access_node_id_list) / len(block.access_node_id_list)
                block.centroid_y = sum(g_access_node_list[g_access_node_id_index[node_id]].y_coord for
                                       node_id in block.access_node_id_list) / len(block.access_node_id_list)
            except:
                block.centroid_x = (block.x_max + block.x_min) / 2
                block.centroid_y = (block.y_max + block.y_min) / 2

            str_name_a = str(alphabet_list[math.ceil(block.id / number_of_x_blocks) - 1])
            if int(block.id % number_of_x_blocks) != 0:
                str_name_no = str(int(block.id % number_of_x_blocks))
            else:
                str_name_no = str(number_of_x_blocks)
            block.name = str_name_a + str_name_no

            str_polygon = 'POLYGON ((' + \
                          str(block.x_min) + ' ' + str(block.y_min) + ',' + \
                          str(block.x_min) + ' ' + str(block.y_max) + ',' + \
                          str(block.x_max) + ' ' + str(block.y_max) + ',' + \
                          str(block.x_max) + ' ' + str(block.y_min) + ',' + \
                          str(block.x_min) + ' ' + str(block.y_min) + '))'
            block.polygon = str_polygon

            str_centroid = 'POINT (' + str(block.centroid_x) + ' ' + str(block.centroid_y) + ')'
            block.centroid = str_centroid

            centroid_node = Node()
            centroid_node.id = int(g_node_list[-1].id + 1)
            centroid_node.zone_id = block.id
            centroid_node.x_coord = block.centroid_x
            centroid_node.y_coord = block.centroid_y
            centroid_node.node_type = 'centroid'
            centroid_node.boundary_flag = int(-2)
            g_node_list.append(centroid_node)
            block.centroid_node = centroid_node
            g_zone_list.append(block)

        # centroid of each zone with zero node is the center point of the grid
        if (len(block.node_id_list) == 0):
            # block.poi_count = len(block.poi_node_list)
            block.centroid_x = (block.x_max + block.x_min) / 2
            block.centroid_y = (block.y_max + block.y_min) / 2
            str_name_a = str(alphabet_list[math.ceil(block.id / number_of_x_blocks) - 1])
            if int(block.id % number_of_x_blocks) != 0:
                str_name_no = str(int(block.id % number_of_x_blocks))
            else:
                str_name_no = str(number_of_x_blocks)
            block.name = str_name_a + str_name_no

            str_polygon = 'POLYGON ((' + \
                          str(block.x_min) + ' ' + str(block.y_min) + ',' + \
                          str(block.x_min) + ' ' + str(block.y_max) + ',' + \
                          str(block.x_max) + ' ' + str(block.y_max) + ',' + \
                          str(block.x_max) + ' ' + str(block.y_min) + ',' + \
                          str(block.x_min) + ' ' + str(block.y_min) + '))'
            block.polygon = str_polygon

            str_centroid = 'POINT (' + str(block.centroid_x) + ' ' + str(block.centroid_y) + ')'
            block.centroid = str_centroid

            centroid_node = Node()
            centroid_node.id = int(g_node_list[-1].id + 1)
            centroid_node.zone_id = None
            centroid_node.x_coord = block.centroid_x
            centroid_node.y_coord = block.centroid_y
            centroid_node.node_type = 'centroid'
            centroid_node.boundary_flag = int(-2)
            g_node_list.append(centroid_node)
            block.centroid_node = centroid_node
            g_zone_list.append(block)

        if round(abs(x_temp + scale_x - x_max) / scale_x) >= 1:
            x_temp = x_temp + scale_x
        else:
            x_temp = x_min
            y_temp = y_temp - scale_y

    # generate the grid address for boundary nodes and generate virtual zones around the boundary of the area

    g_number_of_zones = len(g_zone_list)
    print('\nNumber of zones including virtual zones = ' + str(g_number_of_zones))
    g_zone_id_list = [zone.id for zone in g_zone_list]

    # get zone index
    for i in range(g_number_of_zones):
        g_zone_index_dict[g_zone_id_list[i]] = i

    # create zone.csv

    data_zone = pd.DataFrame([zone.id for zone in g_zone_list])
    data_zone.columns = ["activity_zone_id"]

    data_zone['name'] = pd.DataFrame([zone.name for zone in g_zone_list])
    data_zone['geometry'] = pd.DataFrame([zone.polygon for zone in g_zone_list])
    data_zone['centroid'] = pd.DataFrame([zone.centroid for zone in g_zone_list])
    data_zone['centroid_x'] = pd.DataFrame([zone.centroid_x for zone in g_zone_list])
    data_zone['centroid_y'] = pd.DataFrame([zone.centroid_y for zone in g_zone_list])
    access_node_vector_list = []
    for zone in g_zone_list:
        temp_access_node_vector = str()
        for i in zone.access_node_id_list:
            if i != max(zone.access_node_id_list):
                temp_access_node_vector = temp_access_node_vector + str(i) + ';'
            else:
                temp_access_node_vector = temp_access_node_vector + str(i)
        access_node_vector_list.append(temp_access_node_vector)
    data_zone['access_node_vector'] = pd.DataFrame(access_node_vector_list)
    data_zone['total_poi_count'] = pd.DataFrame([zone.poi_count for zone in g_zone_list])


    # # print(data_zone)
    data_zone.to_csv('zone.csv', index=False, line_terminator='\n')

    #
    # # update node.csv with zone_id
    # # append POIs and centroids to node.csv
    # node_filepath = 'node.csv'
    # with open(node_filepath, errors='ignore') as fp:
    #     reader = csv.DictReader(fp)
    #     node_name_column = []
    #     osm_node_id_column = []
    #     osm_highway_column = []
    #     new_zone_id_column = []
    #     ctrl_type_column = []
    #     intersection_id_column = []
    #     notes_column = []
    #     for row in reader:
    #         node_name_column.append(row['name'])
    #         osm_node_id_column.append(row['osm_node_id'])
    #         osm_highway_column.append(row['osm_highway'])
    #         new_zone_id_column.append('')
    #         ctrl_type_column.append(row['ctrl_type'])
    #         #intersection_id_column.append(row['intersection_id'])
    #         notes_column.append(row['notes'])
    # for i in range(len(g_node_list) - g_number_of_original_nodes):
    #     node_name_column.append('')
    #     osm_node_id_column.append('')
    #     osm_highway_column.append('')
    #     new_zone_id_column.append('')
    #     ctrl_type_column.append('')
    #     #intersection_id_column.append('')
    #     notes_column.append('')
    # df_node_data = pd.DataFrame(node_name_column)
    # df_node_data.columns = ["name"]
    # df_node_data["node_id"] = pd.DataFrame([int(node.id) for node in g_node_list])
    # df_node_data['osm_node_id'] = pd.DataFrame(osm_node_id_column)
    # df_node_data['osm_highway'] = pd.DataFrame(osm_highway_column)
    # df_node_data['zone_id'] = pd.DataFrame([node.zone_id for node in g_node_list])
    # # df_node_data['zone_id'] = pd.DataFrame(new_zone_id_column)
    # df_node_data['ctrl_type'] = pd.DataFrame(ctrl_type_column)
    # df_node_data['node_type'] = pd.DataFrame([node.node_type for node in g_node_list])
    # df_node_data['activity_type'] = pd.DataFrame([node.activity_type for node in g_node_list])
    # df_node_data['is_boundary'] = pd.DataFrame([int(node.boundary_flag) for node in g_node_list])
    # df_node_data['x_coord'] = pd.DataFrame([node.x_coord for node in g_node_list])
    # df_node_data['y_coord'] = pd.DataFrame([node.y_coord for node in g_node_list])
    # #df_node_data['intersection_id'] = pd.DataFrame(intersection_id_column)
    # df_node_data['poi_id'] = pd.DataFrame([node.poi_id for node in g_node_list])
    # df_node_data['notes'] = pd.DataFrame(notes_column)
    #
    # df_node_data.to_csv(node_filepath, index=False)


def zone_distance_matrix(latitude=None):
    global g_o_zone_id_list
    global g_o_zone_name_list
    global g_d_zone_id_list
    global g_d_zone_name_list
    global g_od_distance_list
    global g_od_geometry_list
    global g_distance_matrix
    global g_output_folder
    global g_used_latitude
    global g_average_latitude

    g_distance_matrix = np.ones((g_number_of_zones, g_number_of_zones)) * 9999  # initialize distance matrix

    if latitude is None:  # use the average latitude according to node.csv
        if g_average_latitude == 99:

            latitude = 30  # comments: default value if no given latitude
            flat_length = g_degree_length_dict[latitude]
            g_used_latitude = latitude
        else:
            # match the closest latitude key according to the given latitude
            dif = float('inf')
            for i in g_degree_length_dict.keys():
                if abs(abs(g_average_latitude) - i) < dif:
                    temp_latitude = i
                    dif = abs(abs(g_average_latitude) - i)
                    g_used_latitude = temp_latitude
            flat_length = g_degree_length_dict[temp_latitude]
    else:  # use the given latitude
        # match the closest latitude key according to the given latitude
        dif = float('inf')
        for i in g_degree_length_dict.keys():
            if abs(abs(latitude) - i) < dif:
                temp_latitude = i
                dif = abs(abs(latitude) - i)
                g_used_latitude = temp_latitude
        flat_length = g_degree_length_dict[temp_latitude]

    print('\nLatitude used for zone partition= ', g_used_latitude)

    # define accessibility by calculating straight distance between zone centroids
    accessibility_filepath = 'accessibility.csv'

    g_o_zone_id_list = []
    g_o_zone_name_list = []
    g_d_zone_id_list = []
    g_d_zone_name_list = []
    g_od_distance_list = []
    g_od_geometry_list = []

    for o_zone in g_zone_list:
        for d_zone in g_zone_list:
            g_o_zone_id_list.append(o_zone.id)
            g_o_zone_name_list.append(o_zone.name)
            g_d_zone_id_list.append(d_zone.id)
            g_d_zone_name_list.append(d_zone.name)
            g_od_geometry_list.append(
                'LINESTRING (' + str(round(o_zone.centroid_x, 7)) + ' ' + str(round(o_zone.centroid_y, 7))
                + ',' + str(round(d_zone.centroid_x, 7)) + ' ' + str(round(d_zone.centroid_y, 7)) + ')')
            distance_km = (((float(o_zone.centroid_x) - float(d_zone.centroid_x)) * flat_length) ** 2 +
                           ((float(o_zone.centroid_y) - float(d_zone.centroid_y)) * flat_length) ** 2) ** 0.5
            g_od_distance_list.append(distance_km)
            o_zone_index = g_zone_index_dict[o_zone.id]
            d_zone_index = g_zone_index_dict[d_zone.id]
            g_distance_matrix[o_zone_index][d_zone_index] = distance_km

    # create accessibility.csv
    data = pd.DataFrame(g_o_zone_id_list)
    print('\nNumber of distance pairs between zones= ', len(g_o_zone_id_list))
    data.columns = ["o_zone_id"]
    data["o_zone_name"] = pd.DataFrame(g_o_zone_name_list)

    data1 = pd.DataFrame(g_d_zone_id_list)
    data['d_zone_id'] = data1
    data["d_zone_name"] = pd.DataFrame(g_d_zone_name_list)

    data2 = pd.DataFrame(g_od_distance_list)
    data['accessibility'] = data2
    max_accessibility_index = g_od_distance_list.index(max(g_od_distance_list))
    sum = 0
    for i in g_od_distance_list:
        sum += float(i)
    print('\nLargest straight distance = '+str(round(g_od_distance_list[max_accessibility_index],2))+' km')
    print('Average straight distance between zones = '+str(round(sum/len(g_od_distance_list),2))+' km')

    data3 = pd.DataFrame(g_od_geometry_list)
    data['geometry'] = data3

    # print(data)
    if g_output_folder is not None:
        accessibility_filepath = os.path.join(g_output_folder, 'zone_distance.csv')
        data.to_csv(accessibility_filepath, index=False, line_terminator='\n')
    else:
        data.to_csv('zone_distance.csv', index=False, line_terminator='\n')


def trip_generation(residential_production = None, residential_attraction = None,
                  boundary_production = None, boundary_attraction = None):

    global g_node_prod_list
    global g_node_attr_list
    global g_node_production_dict
    global g_node_attraction_dict
    global g_node_list
    global g_node_id_list
    global g_output_folder
    global g_trip_matrix
    global access_node_vector_list

    if residential_production is None:
        residential_production = 20  # comments: default value if no given latitude
    if residential_attraction is None:
        residential_attraction = 20  # comments: default value if no given latitude
    if boundary_production is None:
        boundary_production = 1000  # comments: default value if no given latitude
    if boundary_attraction is None:
        boundary_attraction = 1000  # comments: default value if no given latitude

    # calculate production/attraction values of each node
    for node in g_node_list:
        if node.activity_location_tab == 'residential':  # residential node
            g_node_prod_list.append(residential_production)  # comments: default production value of residential node
            node.production = residential_production
            g_node_attr_list.append(residential_attraction)  # comments: default attraction value of residential node
            node.attraction = residential_attraction

        elif node.activity_location_tab == 'boundary node only with incoming links':
            g_node_prod_list.append(0)  # comments: default production value of boundary node
            node.production = 0
            g_node_attr_list.append(boundary_attraction)  # comments: default attraction value of boundary node
            node.attraction = boundary_attraction

        elif node.activity_location_tab == 'boundary node only with outgoing links':
            g_node_prod_list.append(boundary_production)  # comments: default production value of boundary node
            node.production = boundary_production
            g_node_attr_list.append(0)  # comments: default attraction value of boundary node
            node.attraction = 0

        elif node.activity_location_tab == 'boundary node with both incoming and outgoing links':
            g_node_prod_list.append(boundary_production)  # comments: default production value of boundary node
            node.production = boundary_production
            g_node_attr_list.append(boundary_attraction)  # comments: default attraction value of boundary node
            node.attraction = boundary_attraction

        else:
            g_node_prod_list.append(0)
            node.production = 0

            g_node_attr_list.append(0)
            node.attraction = 0

    for node in g_node_list:
        g_node_production_dict[node.id] = float(node.production)
        g_node_attraction_dict[node.id] = float(node.attraction)
        g_node_id_list.append(node.id)
        g_node_zone_id_list.append(node.zone_id)
        if node.zone_id != '' and node.zone_id not in g_zone_to_access_nodes_dict.keys() and \
                (int(node.boundary_flag) >= 2 or int(node.boundary_flag) == -1 or int(node.boundary_flag) == 1):
            g_zone_to_access_nodes_dict[node.zone_id] = list()
            g_zone_to_access_nodes_dict[node.zone_id].append(node.id)
        elif node.zone_id != '' and \
                (int(node.boundary_flag) >= 2 or int(node.boundary_flag) == -1 or int(node.boundary_flag) == 1):
            g_zone_to_access_nodes_dict[node.zone_id].append(node.id)

    g_number_of_nodes = len(g_node_list) - g_number_of_zones

    "deal with multiple nodes within one zone"
    g_zone_production = np.zeros(g_number_of_zones)
    g_zone_attraction = np.zeros(g_number_of_zones)
    error_flag = 0

    for i in range(g_number_of_nodes):
        if g_node_list[i].boundary_flag != 0 and \
                g_node_list[i].boundary_flag != -2:
            node_id = g_node_id_list[i]
            if g_node_zone_dict.get(node_id) is not None:
                zone_id = g_node_zone_dict[node_id]
                zone_index = g_zone_index_dict[zone_id]
                node_prod = g_node_production_dict[node_id]
                node_attr = g_node_attraction_dict[node_id]
                g_zone_production[zone_index] = g_zone_production[zone_index] + node_prod
                g_zone_attraction[zone_index] = g_zone_attraction[zone_index] + node_attr
                error_flag += 1

    if error_flag == 0:
        # print("There is no node with activity_type = 'poi/residential' or is_boundary = '1'. Please check
        # node.csv!")
        print("There is no node with activity_type = 'poi/residential' or is_boundary = '1'. Please check "
                     "node.csv!")
        sys.exit(0)

    for zone in g_zone_list:
        zone_index = g_zone_index_dict[zone.id]
        g_total_production_list.append(g_zone_production[zone_index])
        g_total_attraction_list.append(g_zone_attraction[zone_index])
        zone.production = g_zone_production[zone_index]
        zone.attraction = g_zone_attraction[zone_index]

    # update zone.csv with total production and attraction in each zone
    data_list = [zone.id for zone in g_zone_list]
    data_zone = pd.DataFrame(data_list)
    data_zone.columns = ["activity_zone_id"]

    data_zone_name_list = [zone.name for zone in g_zone_list]
    data1 = pd.DataFrame(data_zone_name_list)
    data_zone['name'] = data1

    data_list = [zone.polygon for zone in g_zone_list]
    data1 = pd.DataFrame(data_list)
    data_zone['geometry'] = data1

    data_list = [zone.centroid for zone in g_zone_list]
    data1 = pd.DataFrame(data_list)
    data_zone['centroid'] = data1

    data_list = [zone.centroid_x for zone in g_zone_list]
    data1 = pd.DataFrame(data_list)
    data_zone['centroid_x'] = data1

    data_list = [zone.centroid_y for zone in g_zone_list]
    data1 = pd.DataFrame(data_list)
    data_zone['centroid_y'] = data1

    data1 = pd.DataFrame(access_node_vector_list)
    data_zone['access_node_vector'] = data1

    data_list = [zone.poi_count for zone in g_zone_list]
    data1 = pd.DataFrame(data_list)
    data_zone['total_poi_count'] = data1

    data_list = [zone.residential_count for zone in g_zone_list]
    data1 = pd.DataFrame(data_list)
    data_zone['residential_poi_count'] = data1

    data_list = [zone.office_count for zone in g_zone_list]
    data1 = pd.DataFrame(data_list)
    data_zone['office_poi_count'] = data1

    data_list = [zone.shopping_count for zone in g_zone_list]
    data1 = pd.DataFrame(data_list)
    data_zone['shopping_poi_count'] = data1

    data_list = [zone.school_count for zone in g_zone_list]
    data1 = pd.DataFrame(data_list)
    data_zone['school_poi_count'] = data1

    data_list = [zone.parking_count for zone in g_zone_list]
    data1 = pd.DataFrame(data_list)
    data_zone['parking_poi_count'] = data1

    data_list = [zone.boundary_count for zone in g_zone_list]
    data1 = pd.DataFrame(data_list)
    data_zone['boundary_node_count'] = data1

    data_zone['total_production'] = pd.DataFrame(g_total_production_list)
    data_zone['total_attraction'] = pd.DataFrame(g_total_attraction_list)

    max_prod_o_zone_index = g_total_production_list.index(max(g_total_production_list))
    max_attr_d_zone_index = g_total_attraction_list.index(max(g_total_attraction_list))
    print('Origin zone with largest production volume is ' + str(data_zone_name_list[max_prod_o_zone_index]))
    print('Destination zone with largest attraction volume is ' + str(data_zone_name_list[max_attr_d_zone_index]))

    # print(data_zone)
    if g_output_folder is not None:
        zone_filepath = os.path.join(g_output_folder, 'zone.csv')
        data_zone.to_csv(zone_filepath, index=False, line_terminator='\n')
    else:
        data_zone.to_csv('zone.csv', index=False, line_terminator='\n')


def demand_distributon() -> pd.DataFrame:

    global g_output_folder

    # Generate gamma function coefficients for friction factors
    trip_purpose_list = ['HBW', 'HBO', 'NHB']
    a_list = [28507, 139173, 219113]
    b_list = [-0.02, -1.285, -1.332]
    c_list = [-0.123, -0.094, -0.1]

    data = pd.DataFrame({
        'trip_purpose': trip_purpose_list,
        'a': a_list,
        'b': b_list,
        'c': c_list})

    # Calculate travel time between zones (unit: km/h)
    average_travel_speed = 30
    trip_purpose_index = 0
    a, b, c = [factor[trip_purpose_index] for factor in [a_list, b_list, c_list]]

    # Create od friction factor list
    od_friction_factor_list = []
    for i in range(len(g_o_zone_id_list)):
        od_distance = g_od_distance_list[i]
        travel_time = (max(od_distance, 0.001) / 1000) / average_travel_speed*60  # unit: min
        friction_factor = a * (travel_time ** b) * (np.exp(c * travel_time))

        od_friction_factor_list.append(
            friction_factor) if od_distance != 0 else od_friction_factor_list.append(0)

    # Create od friction facotr matrix
    number_of_zones = len(g_zone_list)
    friction_factor_matrix = np.zeros((number_of_zones, number_of_zones))
    for i in range(len(od_friction_factor_list)):
        o_zone_id = g_o_zone_id_list[i]
        o_zone_index = g_zone_index_dict[o_zone_id]
        d_zone_id = g_d_zone_id_list[i]
        d_zone_index = g_zone_index_dict[d_zone_id]
        friction_factor_matrix[o_zone_index][d_zone_index] = od_friction_factor_list[i]
    # print(friction_factor_matrix)

    # Generate attraction friction
    len_zone_list = len(g_zone_list)
    total_attraction_friction_list = np.zeros(len_zone_list)
    for i in range(len_zone_list):
        prod_zone_id = g_zone_list[i].id
        prod_zone_index = g_zone_index_dict[prod_zone_id]
        for j in range(len_zone_list):
            attr_zone_id = g_zone_list[j].id
            attr_zone_index = g_zone_index_dict[attr_zone_id]
            total_attraction_friction_list[prod_zone_index] += g_zone_list[attr_zone_index].attraction * \
                friction_factor_matrix[prod_zone_index][attr_zone_index]

    # Generate OD volume
    od_volume_list = []
    for i in range(len(g_o_zone_id_list)):
        prod_zone_id = g_o_zone_id_list[i]
        prod_zone_index = g_zone_index_dict[prod_zone_id]
        attr_zone_id = g_d_zone_id_list[i]
        attr_zone_index = g_zone_index_dict[attr_zone_id]
        od_volume = g_zone_list[prod_zone_index].production * g_zone_list[attr_zone_index].attraction * od_friction_factor_list[i] \
            / max(0.000001, total_attraction_friction_list[prod_zone_index])
        od_volume_list.append(round(od_volume))
    print('total travel demand:', sum(od_volume_list))

    # Update OD
    print('\nTop 10 O/D Volume:')
    volume_idx = sorted(enumerate(od_volume_list), key=lambda od_id: od_id[1], reverse=True)
    for od in range(10):
        index_truple = volume_idx[od]
        print(
            f'Top {str(od + 1)} O/D pair: zone {str(g_o_zone_id_list[index_truple[0]])} ->zone {str(g_d_zone_id_list[index_truple[0]])}, volume = {str(index_truple[1])}')

    data_demand = pd.DataFrame({
        "o_zone_id": g_o_zone_id_list,
        "o_zone_name": g_o_zone_name_list,
        "d_zone_id": g_d_zone_id_list,
        "d_zone_name": g_d_zone_name_list,
        "accessibility": g_od_distance_list,
        "volume": od_volume_list,
        "geometry": g_od_geometry_list
    })

    print('\n', data_demand)

    if g_output_folder is not None:
        demand_filepath = os.path.join(g_output_folder, 'demand.csv')
        data_demand.to_csv(demand_filepath, index=False, line_terminator='\n')
    else:
        data_demand.to_csv('demand.csv', index=False, line_terminator='\n')

    return data_demand
