from asyncpg import Pool
from quart import jsonify, session, render_template, send_file, current_app
from quart import request, redirect, url_for

from ....libraries.schema_definitions.v0 import create_default_json, get_default_record, make_default_display_data

from ....libraries.shared_operations.v0 import get_node, create_node, create_relationship, \
                                               archive_node, archive_relationship, \
                                               get_relationship, update_some_data_node

from ....libraries.helper_operations.v0 import queryresult_to_dict, convert_mass_units, get_x_label

from ....libraries.cache_operations.v0 import cache_set, cache_get, cache_delete

from ....libraries.db.v0 import init_db_pool, init_db_pool_about
from ....libraries.migration.v0 import get_style_mpl, get_clean_color_style 

import json
import base64
import io

from datetime import datetime, timezone

# for plotting
import matplotlib as mpl
mpl.rcParams['axes.unicode_minus'] = False
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import gridspec

# for legend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import numpy as np

# for axes
from matplotlib.ticker import LogFormatterMathtext

import logging

import logging

logger = logging.getLogger('quart.app')

async def make_default_display_data_session():

    result_dict = await make_default_display_data()

    cache_data = await cache_set("current_plot", result_dict)
    
    return result_dict

import logging

# You should configure logging at the top level of your application, for example:
# logging.basicConfig(level=logging.INFO)

async def fn_save_current_plot(conn, create_new_plot=True):
    import logging
    from datetime import datetime, timezone

    logger = logging.getLogger("quart.app")
    logger.info(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Starting commit_current_plot. <<<<<<<<<<<<<<<<<<<<")

    current_plot = await cache_get("dmtools_current_plot")
    if not current_plot:
        logger.error("No plot in session.")
        raise Exception("No plot in session")

    current_plot_node = current_plot["plot_node"]
    current_plot_record = current_plot_node.get("record")
    plot_record = current_plot_record
    current_plot_id = plot_record.get("id") if plot_record else -1
    current_plot_properties = current_plot_node.get("properties")
    current_plot_node["properties"]["name"] = datetime.now(timezone.utc).isoformat()
    current_display_data = current_plot.get("display_data")

    logger.info(f"Loaded plot from cache: plot_id={current_plot_id}")

    # --- 1. Check for plot record, create if missing ---
    if current_plot_id == -1 or create_new_plot:
        logger.info("No plot record found, create new or create a copy from another plot.")
        plot_nodes, status = await create_node(
            conn, current_plot_properties, "Plot", schema="data"
        )
        plot_id = plot_nodes[0].get('record').get("id")
        logger.info(f"Created new plot node with id={plot_id}, status={status}")

        # DUPLICATE ALL DISPLAYS: Set 'id' to -1 for all display records so they are always created anew
        for display in current_display_data:
            display["record"]["id"] = -1
    else:
        plot_id = plot_record.get("id")
        plot_properties = current_plot_properties
        logger.info(f"Using existing plot node with id={plot_id}")

    # --- 2. Get current plot node from DB (if already existed) ---
    plot_nodes, _ = await get_node(
        conn, plot_id, "Plot", schema="data"
    )
    logger.debug(f"DB plot properties: {plot_nodes[0].get('properties')}")
    
    db_plot_properties = plot_nodes[0].get('properties')

    # --- 3. Update plot properties if changed ---
    if db_plot_properties != plot_properties:
        logger.info(f"Updating plot node {plot_id} properties.")
        updated_plot_nodes, _ = await update_some_data_node(conn, plot_id, plot_properties, "Plot", schema="data")

    # --- 4. Get current plot->display relationships and display nodes ---
    got_relationships, status = await get_relationship(
        conn, plot_id, "PLOT_OF_DISPLAY", schema="data"
    )
    logger.debug(f"Current DB plot->display relationships: {got_relationships}")

    db_display_node_ids = {r["destination"] for r, p in got_relationships}
    cached_display_node_ids = {
        display["record"].get("id")
        for display in current_display_data
        if display["record"].get("id") not in (-1, None)
    }

    logger.info(f"DB display node ids: {db_display_node_ids}")
    logger.info(f"Cached display node ids: {cached_display_node_ids}")

    # --- 5. Archive deleted displays and relationships (but not Data nodes!) ---
    displays_to_archive = db_display_node_ids - cached_display_node_ids
    logger.info(f"Displays to archive: {displays_to_archive}")

    for display_id in displays_to_archive:
        logger.info(f"Archiving display node {display_id}")
        archived_nodes, _ = await archive_node(conn, display_id, schema="data")
        archived_relationships, _ = await archive_relationship(conn, "PLOT_OF_DISPLAY", plot_id, display_id, schema="data")
        # Archive display->data relationships, but DO NOT archive Data nodes
        display_data_rels, _ = await get_relationship(conn, "DISPLAY_OF_DATA", display_id, schema="data")
        for rel in display_data_rels:
            logger.info(
                f"Archiving display->data relationship: display_id={display_id}, data_id={rel['destination']}"
            )
            archived_relationships, _ = await archive_relationship(conn, "DISPLAY_OF_DATA", display_id, rel["destination"], schema="data")

    # --- 6. Sync or insert displays and their data relationships ---
    logger.info(f"Current Display Data : {current_display_data}")
    for display in current_display_data:
        display_id = display["record"].get("id")
        display_props = display["properties"]
        session_data = display.get("data", [])

        # If create_new_plot, all displays have id == -1 and will be created anew.
        # If not, update existing or create new as appropriate.
        if display_id not in (-1, None) and not create_new_plot and display_id in db_display_node_ids:
            logger.info(f"Updating existing display node {display_id}.")
            updated_displays, _ = await update_some_data_node(conn, display_id, display_props, "Display", schema="data")
        else:
            logger.info("Creating new display node and relationship.")
            created_displays, status = await create_node(
                conn, display_props, "Display"
            )
            display_id = created_displays[0].get('record').get("id")
            created_relationships, status = await create_relationship(
                conn, "PLOT_OF_DISPLAY", plot_id, display_id, schema="data"
            )
            logger.info(f"Created display node {display_id} and relationship status={status}")

        # Sync display->data relationships only (do not touch Data nodes)
        db_display_data_relationships, status = await get_relationship(
            conn, "DISPLAY_OF_DATA", display_id, schema="data"
        )
        db_data_ids = {r["destination"] for r, p in db_display_data_relationships}
        cached_data_ids = {
            d["record"].get("id")
            for d in session_data if d["record"].get("id")
        }

        logger.debug(f"Display {display_id} DB data ids: {db_data_ids}")
        logger.debug(f"Display {display_id} cached data ids: {cached_data_ids}")

        # Archive deleted display->data relationships (do not archive Data nodes)
        rels_to_archive = db_data_ids - cached_data_ids
        for data_id in rels_to_archive:
            logger.info(f"Archiving display->data relationship: display_id={display_id}, data_id={data_id}")
            await archive_relationship(conn, "DISPLAY_OF_DATA", display_id, data_id, schema="data")

        # Insert new display->data relationships (do not create Data nodes)
        rels_to_create = cached_data_ids - db_data_ids
        for data_id in rels_to_create:
            logger.info(f"Creating display->data relationship: display_id={display_id}, data_id={data_id}")
            created_relationships, _ = await create_relationship(conn, "DISPLAY_OF_DATA", display_id, data_id, schema="data")

    logger.info(f"Commit complete for plot_id={plot_id}")
    return {"plot_id": plot_id, "status": "updated in place" if plot_record else "created"}, 200

async def fn_commit_current_plot(conn, create_new_plot=True):
    """
    Calls fn_save_current_plot within a PostgreSQL transaction.
    Rolls back all changes if any exceptions occur.
    """
    import logging

    logger = logging.getLogger("quart.app")
    logger.info(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Starting commit_current_plot TRANSACTION WRAPPER. <<<<<<<<<<<<<<<<<<<<")

    async with conn.transaction():
        result = await fn_save_current_plot(conn, create_new_plot=create_new_plot)
    logger.info(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> commit_current_plot TRANSACTION COMPLETE. <<<<<<<<<<<<<<<<<<<<")
    
    return result

async def get_plot_display_data_nodes_cached(conn, plot_id=-1, data_id=-1, schema="data"):
    """
    If the current plot is in the session and matches plot_id, return that as the latest working copy.
    Otherwise, load from DB and update the session.
    """
    logger = logging.getLogger("dmtools.get_plot_display_data_nodes_cached")
    logger.info(f"Attempting to retrieve plot from cache for plot_id={plot_id}")

    # Testing cache
    current_plot = await cache_get("dmtools_current_plot")
    logger.debug(f"Plot data from cache: {current_plot}")
    try:
        cached_plot_id = int(current_plot["plot_node"]["record"].get("id"))
    except:
        cached_plot_id = -1
    # Check session for current plot and reuse if it matches node_id
    if (
        current_plot
        and "plot_node" in current_plot
        and "record" in current_plot["plot_node"]
        and cached_plot_id == plot_id
    ):
        logger.info(f"Returning plot from cache for plot_id={plot_id}")
        return current_plot, 200

    logger.info(f"Cached plot not found or does not match plot_id={plot_id}. Querying database.")

    # If there is no current plot in the session, or it does not match the plot_id, load from DB
    result_dict, status = await get_plot_display_data_nodes(
        conn, plot_id, data_id=data_id, user_node_id=-1, schema=schema
    )

    logger.info(f"Storing plot_id={plot_id} to cache after DB retrieval.")
    cache_return = await cache_set("dmtools_current_plot", result_dict)

    logger.info(f"Checking cached plot_id={plot_id} with status={status}")

    logger.info(f"Retrieve plot_id={plot_id} to cache after cache set.")
    plot_data = await cache_get("dmtools_current_plot")
    logger.info(f"Cached plot_data={plot_data}")

    logger.info(f"Returning plot from DB for plot_id={plot_id} with status={status}")
    return result_dict, status

async def get_plot_display_data_nodes(conn, plot_id, data_id = -1, user_node_id =-1, schema="data"):
    """
    Retrieve the plot, display, data for a given plot id

    This is designed to begin with no display or data nodes, and will return a default structure

    As Data and Displays are added or deleted this function will accomodate these changes

    It is also designed to create a Plot of Data to allow Data to be browsed

    """
    
    result_dict = await make_default_display_data_session()

    session_user_node_id = session.get("user_node_id",-1)
    
    if session_user_node_id > 0:
        user_node_id = session_user_node_id
    elif user_node_id != -1:
        user_node_id = user_node_id
    else:
        user_node_id = -1

    print(f"Debug: Starting function with plot_id={plot_id}, schema={schema}")

    async with conn.transaction():
        ## this checks if the plot is owned by the user, no further checks are done
        try:
            plot_nodes, status_code = await get_node(conn, plot_id, 'Plot', user_node_id, schema="data")
            result_dict["plot_node"] = plot_nodes[0]
        
        except:
            #return {"error": f"No plot_node found with id={node_id}"}, 404
            return result_dict, 200
    
    #plot_node = plot_nodes[0] ## get_node returns a list of nodes, we are only interested in the first one

    #if not plot_record:
    #    print(f"Debug: No plot_node found with id={node_id}")
    #    #return {"error": f"No plot_node found with id={node_id}"}, 404
    #    return result_dict, 200

    #print(f"Debug: plot_node found: {plot_record}")

    # Step 2: Get direct displays of the given plot node
    displays_query = f"""
        SELECT n.*
        FROM {schema}.node n
        JOIN {schema}.relationship r ON r.destination = n.id
        WHERE r.label = 'PLOT_OF_DISPLAY' and r.source = $1
        and n.archived IS NULL;
        """
    
    async with conn.transaction():
        displays = await conn.fetch(displays_query, plot_id)
    
    ## the following allows Data to be shown on a plot without a display
    ## it is a simple and visual way of browsing Data
    if not displays:
        print(f"Debug: No displays found but show plot for Data ID {data_id}")
        #return {"plot_node": plot_record, "displays": []}, 200
        data_nodes, status_code = await get_node(conn, data_id, 'Data', user_node_id, schema="data")
        #data_dict = {"data":[{"record": data_record, "properties": data_properties}]}
        data_properties = data_nodes[0].get('properties')
        default_color = data_properties.get('defaultColor', 'black')
        default_style = data_properties.get('defaultStyle', 'line')
        default_display_dict = {"color": default_color, "style": default_style}
        default_display_properties_dict  = {"properties":default_display_dict}
        default_display_record = get_default_record('Display')
        default_display_record_dict  = {"record":default_display_record}
        # result_dict["display_data"] = [default_display_properties_dict, data_dict]
        result_dict["display_data"] = [{**default_display_record_dict,**default_display_properties_dict, **data_dict}]
        return result_dict, 200
    
    if not displays:
        print(f"Debug: No displays found for plot_node with id={plot_id}")
        return result_dict, 200
    
    print(f"Debug: Found {len(displays)} displays for plot_node")

    # Process each display to include their data
    display_data = []
    for display in displays:
        display_dict = queryresult_to_dict(display)
        display_id = display_dict.get('record').get('id')
        current_color = display_dict.get('properties').get('color')
        current_style = display_dict.get('properties').get('style')
        try:
            clean_trace_color, clean_trace_style = get_clean_color_style(current_color,current_style)
            display_dict['properties']['color'] = clean_trace_color
            display_dict['properties']['style'] = clean_trace_style
        except:
            print("color and style error - ", current_color, " -- ", current_style)
            display_dict['properties']['color'] = 'green'
            display_dict['properties']['style'] = 'line'
        # Check if the display has a valid ID
        if not display_id:
            print(f"Debug: Skipping display_id with invalid or missing ID: {display}")
            ## some Display data may have been deleted since the plot was created
            continue

        print(f"Debug: Processing display with id={display_id}")
        print(f"Debug: Processing display cleaned color={clean_trace_color}")
        print(f"Debug: Processing display cleaned style={clean_trace_style}")

        # Fetch data of the current display
        data_query = f"""
        SELECT n.*
        FROM {schema}.node n
        JOIN {schema}.relationship r ON r.destination = n.id
        WHERE r.label = 'DISPLAY_OF_DATA' and r.source = $1
        and n.archived IS NULL;
        """
        
        async with conn.transaction():
            data_nodes = await conn.fetch(data_query, display_id)

        data_data = []
        
        for data_node in data_nodes:
            data_dict = queryresult_to_dict(data_node)
            data_id = data_dict.get('record').get('id')

            # Check if the data has a valid ID
            if not data_id:
                print(f"Debug: Skipping data with invalid or missing ID: {data_record}")
                continue

            print(f"Debug: Adding data with id={data_id}")
            data_data.append(data_dict)

        print(f"Debug: Found {len(data_data)} valid data for data_id={data_id}")

        # Add data to the display dictionary
        display_dict['data'] = data_data
        display_data.append(display_dict)

    result_dict = {
        "plot_node": plot_nodes[0],
        "display_data": display_data
    }

    ## print("Debug: Final result structure:", result_dict)
    
    return result_dict, 200

async def archive_plot_display_data_relationships(conn, plot_id, data_id, schema="data"):
    """
    Archives the PLOT_OF_DISPLAY and DISPLAY_OF_DATA relationships that link the given plot_id to the given data_id
    through an intermediate Display node. Only affects relationships involving both ends.

    Also archives the Display node.
    """

    try:
        async with conn.transaction():
            # plot_id_int = int(plot_id)
            # Step 1: Find all Display nodes directly linked to the Plot
            display_query = f"""
                SELECT r.destination AS display_id
                FROM {schema}.relationship r
                WHERE r.source = $1 AND r.label = 'PLOT_OF_DISPLAY' AND r.archived IS NULL
            """
            plot_display_rows = await conn.fetch(display_query, int(plot_id))
            display_ids = [row['display_id'] for row in plot_display_rows]

            if not display_ids:
                logger.info(f"No displays found for plot_id={plot_id}")
                return {"message": "No display relationships found."}, 200

            # Step 2: For each display, check if it connects to the given data_id
            matching_display_ids = []
            for display_id in display_ids:
                check_query = f"""
                    SELECT 1 FROM {schema}.relationship
                    WHERE source = $1 AND destination = $2 AND label = 'DISPLAY_OF_DATA' AND archived IS NULL
                """
                exists = await conn.fetchval(check_query, int(display_id), int(data_id))
                if exists:
                    matching_display_ids.append(display_id)

            if not matching_display_ids:
                logger.info(f"No displays found that link plot_id={plot_id} to data_id={data_id}")
                return {"message": "No linked display relationships to archive."}, 200

            # Step 3: Archive the DISPLAY_OF_DATA relationships
            archive_display_data_query = f"""
                UPDATE {schema}.relationship
                SET archived = CURRENT_TIMESTAMP,
                    updated = CURRENT_TIMESTAMP
                WHERE source = $1 AND destination = $2 AND label = 'DISPLAY_OF_DATA' AND archived IS NULL
                RETURNING id
            """
            matching_display_id = int(matching_display_ids[0])
            
            
            archived_dd = await conn.fetch(archive_display_data_query, matching_display_id, int(data_id))

            # Step 4: Archive the PLOT_OF_DISPLAY relationships
            archive_plot_display_query = f"""
                UPDATE {schema}.relationship
                SET archived = CURRENT_TIMESTAMP,
                    updated = CURRENT_TIMESTAMP
                WHERE source = $1 AND destination = $2 AND label = 'PLOT_OF_DISPLAY' AND archived IS NULL
                RETURNING id
            """
            archived_pd = await conn.fetch(archive_plot_display_query, int(plot_id), matching_display_id)

            logger.info(f"Archived {len(archived_dd)} DISPLAY_OF_DATA and {len(archived_pd)} PLOT_OF_DISPLAY relationships.")

            # Step 5: Archive the DISPLAY node
            archive_display_node_query = f"""
                UPDATE {schema}.node
                SET archived = CURRENT_TIMESTAMP ,
                    updated = CURRENT_TIMESTAMP
                WHERE id = $1 AND type = 'Display' AND archived IS NULL
                RETURNING id
            """
            matching_display_id = int(matching_display_ids[0])
            
            
            archived_dn = await conn.fetch(archive_display_node_query, matching_display_id)
            logger.info(f"Archived {len(archived_dn)} Display node.")

        return {
            "archived_display_of_data": len(archived_dd),
            "archived_plot_of_display": len(archived_pd),
            "archived_display_node": len(archived_dn)
        }, 200

    except Exception as e:
        logger.exception(f"Failed to archive relationships for plot_id={plot_id}, data_id={data_id}: {e}")
        return {"error": "Archiving failed"}, 500

async def get_raw_display_data():

    plot_data = await cache_get("dmtools_current_plot")
    # print("get_raw_display_data - plot_data >>>>", plot_data)

    # Iterate over each child and their grandchildren to collect display and plot data
    displays_lol = []
    for display in plot_data.get("display_data"):
        display_record = display.get("record")
        display_id = display_record.get('id')
        display_properties = display.get('properties')

        style = display_properties.get('style')
        color = display_properties.get('color')
        clean_color, clean_style = get_clean_color_style(color,style)

        for data in display.get('data'):
            data_properties = data.get('properties')
            data_record = data.get('record')
            display_data_id = data_record.get('id')
            
            trace_name = data_properties.get('label_short', 'Trace')
            
            append_this = [display_id,trace_name, clean_color, clean_style, display_data_id]
            displays_lol.append(append_this)
    
    ## add the data ids involved in the plot
    data_ids = []
    for display in displays_lol:
        data_ids.append(str(display[4]))

    cache_return = await cache_set('dmtools_selected_data_ids', data_ids)

    return displays_lol, data_ids

async def create_empty_chart_and_legend_svgs():
    
    fig, ax = plt.subplots()
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_frame_on(False)
    ax.set_title("Empty Plot")
    img = io.BytesIO()
    fig.savefig(img, format='svg', dpi=100, bbox_inches='tight', pad_inches=0.25)
    img.seek(0)
    plt.close(fig)  # Close the figure to free memory
    
    # Encode to base64
    dmtools_edit_plot_url = base64.b64encode(img.getvalue()).decode('utf8')

    # Save it to a BytesIO object
    fig, ax = plt.subplots()
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_frame_on(False)
    ax.set_title("Empty Legend")

    img = io.BytesIO()
    fig.savefig(img, format='svg', dpi=100, bbox_inches='tight', pad_inches=0.2)
    img.seek(0)
    plt.close(fig)  # Close the figure to free memory
    
    # Encode to base64
    dmtools_edit_legend_url = base64.b64encode(img.getvalue()).decode('utf8')
    plot_name = "Plot"

    cache_data = await cache_set("dmtools_plot_url", dmtools_edit_plot_url)
    cache_data = await cache_set("dmtools_legend_url", dmtools_edit_legend_url)

    return plot_name, dmtools_edit_plot_url, dmtools_edit_legend_url

async def get_and_process_edit_plot_data(conn, plot_id, data_id=-1, schema="data"):
    plot_name, dmtools_plot_url = await set_plot_data(conn, plot_id, data_id=-1, schema="data")
    dmtools_legend_url = await set_legend_data(conn, plot_id, data_id=-1, schema="data")
    return plot_name, dmtools_plot_url, dmtools_legend_url


async def set_plot_data(conn, plot_id, data_id=-1, schema="data"):
    px = 1 / 100
        
    # Create the figure
    
    ## this section is to create a suitable frame around the plot
    ## the plot was getting to tight to the edge of the container
    fig = plt.figure(figsize=(10, 10), linewidth=0, edgecolor='#D0D6DB', facecolor='#D0D6DB')
    gs = gridspec.GridSpec(64, 64)
    ax = fig.add_subplot(gs[2:63, 2:63])
    ax.set_facecolor('white')
    ax.tick_params(axis='both', labelsize=16)
    
    # Retrieve plot data
    plot_id_int = int(plot_id)
    plot_data, status_code = await get_plot_display_data_nodes_cached(conn, plot_id_int ,data_id = data_id, schema="data")
    # print("plot_operations plot_record >>>>", plot_data.get('plot_record'))
    plot_data_cache = await cache_get("dmtools_current_plot")
    # print("plot_operations - plot_record_cache >>>>", plot_data_cache.get('plot_record'))

    ## print("plot_operations - plot_data >>>>", plot_data)
    ## the following allows for a brand new plot with no data
    if status_code != 200:
        print("Failed to retrieve existing plot data.")
        plot_name, dmtools_edit_plot_url, dmtools_edit_legend_url = await create_empty_chart_and_legend_svgs()
        return plot_name, dmtools_edit_plot_url, dmtools_edit_legend_url

    # Process the plot nested json
    if plot_data_cache["plot_node"]:
        plot_node = plot_data_cache["plot_node"]
        plot_record =  plot_node["record"]
        plot_properties = plot_node["properties"]
        plot_name = plot_properties.get('name', 'Plot')
        # print("plot_operations - new plot_name >>>>", plot_name)
        plot_id = plot_record.get('id', -1)
    
    # Iterate over each child and their grandchildren to collect and plot data
    for display in plot_data_cache.get("display_data",[{}]):
        # print("plot operations - display loop >>>", display)
        display_record = display.get("record")
        display_properties = display.get('properties')
        ## print(f"\nDisplay Node - ID: {display_record.get('id')}, Type: {display_record.get('type')},\
        ##       Created At: {display_record.get('created')}, Updated At: {display_record.get('updated')}")

        for data in display.get("data"):
            data_record = data.get('record')
            data_properties = data.get('properties')
            # print(f"    Data Node - ID: {data_record.get('id')}, Type: {data_record.get('type')}, \
            #       Created At: {data_record.get('created')}, Updated At: {data_record.get('updated')}")

            # Rescaling factors with fallback values
            y_rescale = float(data_properties.get('yRescale', 1))
            x_rescale = float(data_properties.get('xRescale', 1))
            x_units = data_properties.get('xUnits', 1)
            
            trace_name = data_properties.get('label_short', 'Trace')
            list_data = data_properties.get('values',[[[0.0,0.0],[0.0,1.0]]])
            style = display_properties.get('style','line')
            color = display_properties.get('color','black')

            # Get line and fill plot styles
            # This uses a library to convert the dmtools style and color combination
            # into the required matplotlib configuration
            line_plot_kwargs = get_style_mpl(color, style)

            ## style and fill are not required for a line in matplotlib
            ## it fails if you call the plot function with them in
            line_plot_kwargs.pop('style', None)
            line_plot_kwargs.pop('fill', None)
            
            fill_plot_kwargs = get_style_mpl(color, style)
            ## a fill should have all the marker, line and fill definitions removed
            fill_plot_kwargs.pop('style', None)
            fill_plot_kwargs.pop('marker', None)
            fill_plot_kwargs.pop('markersize', None)
            fill_plot_kwargs.pop('linestyle', None)
            fill_plot_kwargs.pop('linewidth', None)
            fill_plot_kwargs.pop('fill', None)
            # print("fill_plot_kwargs >>>>", fill_plot_kwargs)

            # Plot each trace - a trace is a line
            for trace in list_data:
                               
                #try:
                x = [float(item[0]) * x_rescale for item in trace]

                ## this allows the plot to respond to changes to the x axis units
                selected_unit = plot_properties.get('xUnits', 'GeV/c^2')
                
                plot_type = plot_properties.get('plotType')

                if plot_type == "Cross Section vs WIMP Mass":
                    unit_x = [convert_mass_units(val, x_units, selected_unit) for val in x]
                    y = [float(item[1]) * y_rescale for item in trace]
                elif plot_type == "Cross Section / Mass [in GeV] vs Mass[GeV]":
                    # y should still use x in GeV for division
                    unit_x = [convert_mass_units(val, x_units, 'GeV') for val in x]
                    y = [(float(item[1]) * y_rescale) / xi for item, xi in zip(trace, unit_x)]
                else:
                    unit_x = [convert_mass_units(val, x_units, selected_unit) for val in x]
                    y = [float(item[1]) * y_rescale for item in trace]

                # Plot with line and optional fill style
                ax.plot(unit_x, y, **line_plot_kwargs)
                ##print('style >>', style)
                
                if style == 'fill':
                    ax.fill_between(x, y, **fill_plot_kwargs)
                #except:
                #    a = 1
                

    # Set scale, titles, and labels after all data is plotted
    ax.set_xscale('log')
    ax.set_yscale('log')

    # Manage the x and y axis range
    ymin_exp = plot_properties.get('yMin', '-42')
    ymin_exp = float(ymin_exp) if ymin_exp else -42  # Default to -42 if not set
    ymax_exp = plot_properties.get('yMax', '-42')
    ymax_exp = float(ymax_exp) if ymax_exp else -42  # Default to -42 if not set
    xmin = plot_properties.get('xMin', '0')
    xmin = float(xmin) if xmin else 0  # Default to 0 if not set
    xmax = plot_properties.get('xMax', '3')
    xmax = float(xmax) if xmax else 10000  # Default to 3 if not set

    # Convert to 10**exponent form
    ax.set_xlim([xmin, xmax])
    ax.set_ylim([10**ymin_exp, 10**ymax_exp])

    #####
    ax.set_ylabel(r"$\mathrm{Cross\ Section}\ [cm^{2}]\ (\mathrm{normalized\ to\ nucleon})$", fontsize=18)
    
    # The x axis label is responsive to the Units selected
    #ax.set_xlabel(r"$\mathrm{WIMP\ Mass}\ [\mathrm{GeV}/c^{2}]$", fontsize=18)
    selected_unit = plot_properties.get('xUnits', 'GeV/c^2')
    ax.set_xlabel(get_x_label(selected_unit), fontsize=18)
    plot_title_default = r"$\mathrm{WIMP\ Mass\ vs\ Cross\ Section\ (Plot\ ID:\ " + str(plot_id) + r")}$"
    plot_title = plot_name + ' (' + str(plot_id) + ')' if plot_name else plot_title_default
    ax.set_title(plot_title, fontsize=18)

    # the following was required to ensure the scientific notations displayed correctly.
    # it relies on
    # import matplotlib as mpl
    # mpl.rcParams['axes.unicode_minus'] = False
    # from matplotlib.ticker import LogFormatterMathtext

    ax.xaxis.set_major_formatter(LogFormatterMathtext())
    ax.yaxis.set_major_formatter(LogFormatterMathtext())
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontname('DejaVu Sans')

    # Save to a BytesIO object as it is not possible to directly insert python
    # into an HTML page

    # Save as SVG
    img_svg = io.BytesIO()
    fig.savefig(img_svg, format='svg', dpi=100, bbox_inches='tight', pad_inches=0.2)
    img_svg.seek(0)
    dmtools_plot_url = base64.b64encode(img_svg.getvalue()).decode('utf8')
    cache_data = await cache_set("dmtools_plot_url", dmtools_plot_url)

    # Save as PDF
    img_pdf = io.BytesIO()
    fig.savefig(img_pdf, format='pdf', dpi=100, bbox_inches='tight', pad_inches=0.2)
    img_pdf.seek(0)
    dmtools_plot_url_pdf = base64.b64encode(img_pdf.getvalue()).decode('utf8')
    cache_data = await cache_set("dmtools_plot_url_pdf", dmtools_plot_url_pdf)

    # Now close the figure
    plt.close(fig)
    
    # write the image to the cache - this is then retrieved by the javascript
    # and displayed in the rendered html

    # you will notice that none of the jinja2 templates require inputs
    # as all the data is shared via the cache
    # this was a design decision to simplify development
    
    return plot_name, dmtools_plot_url

async def set_legend_data(conn, plot_id, data_id=-1, schema="data"):
    ### get legend
    # Retrieve plot data
    plot_id_int = int(plot_id)
    plot_data, status_code = await get_plot_display_data_nodes_cached(conn, plot_id_int ,data_id = data_id, schema="data")
    # print("plot_operations plot_record >>>>", plot_data.get('plot_record'))
    plot_data_cache = await cache_get("dmtools_current_plot")
    # print("plot_operations - plot_record_cache >>>>", plot_data_cache.get('plot_record'))

    handles = []
    for display in plot_data_cache.get('display_data',[{}]):
        display_record = display.get('record')
        display_properties = display.get('properties')
        # print(f"\nDisplay Node (Legend) - ID: {display_record.get('id')}, Type: {display_record.get('type')}, \
        #   Created At: {display_record.get('created')}, Updated At: {display_record.get('updated')}")

        for data in display.get("data",[{}]):
            data_record = data.get('record',[{}])
            data_record_id = data_record.get('id',-1)
            data_properties = data.get('properties',{})
            ##print(f"    Data Node (Legend) - ID: {data_record.get('id')}, Type: {data_record.get('type')}, \
            ##       Created At: {data_record.get('created')}, Updated At: {data_record.get('updated')}")   
        
            trace_name = "(" + str(data_record_id) + "):" + data_properties.get('label_short','')
            style = display_properties.get('style','line')
            color = display_properties.get('color','black')
            
            line_plot_kwargs = get_style_mpl(color,style)
            line_plot_kwargs.pop('style',None)
            line_plot_kwargs.pop('fill',None)
            
            fill_plot_kwargs = get_style_mpl(color,style)
            fill_plot_kwargs.pop('style',None)
            fill_plot_kwargs.pop('marker',None)
            fill_plot_kwargs.pop('markersize',None)
            
            if style != 'fill':
                append_this = mlines.Line2D([], [], label=trace_name, **line_plot_kwargs)
            else:
                append_this = mpatches.Patch(label=trace_name, **fill_plot_kwargs)
            
            handles.append(append_this)
        
    labels = [handle.get_label() for handle in handles]
    
    #px = 1/plt.rcParams['figure.dpi']  # pixel in inches
    px = 1/100  # pixel in inches

    num_points = len(labels)
    #fig_height = num_points * 10 * px
    #fig_width = 5
    
    fig, ax = plt.subplots(figsize=(10,10), edgecolor='#D0D6DB', facecolor='#D0D6DB')
    #ax.set_facecolor('white')

    legend = ax.legend(handles=handles, labels=labels, loc='upper center', fontsize=24, labelspacing=1, facecolor='white')
    # Make legend background solid white
    legend.get_frame().set_alpha(1)  # Set alpha to 1 for solid background
    legend.get_frame().set_facecolor((1, 1, 1))  # Set the background to white
    
    ax.axis('off')  # Hide the axes

    # Save as SVG
    img_svg = io.BytesIO()
    fig.savefig(img_svg, format='svg', dpi=100, bbox_inches='tight', pad_inches=0.2)
    img_svg.seek(0)
    dmtools_legend_url = base64.b64encode(img_svg.getvalue()).decode('utf8')
    cache_data = await cache_set("dmtools_legend_url", dmtools_legend_url)

    # Save as PDF
    img_pdf = io.BytesIO()
    fig.savefig(img_pdf, format='pdf', dpi=100, bbox_inches='tight', pad_inches=0.2)
    img_pdf.seek(0)
    dmtools_legend_url_pdf = base64.b64encode(img_pdf.getvalue()).decode('utf8')
    cache_data = await cache_set("dmtools_legend_url_pdf", dmtools_legend_url_pdf)

    # Now close the figure
    plt.close(fig)
    
    return dmtools_legend_url


'''
async def create_plot_display_data_nodes(conn, plot_id, data_id, schema="data",
                                         plot_node_type="Plot", data_node_type="Data",
                                         display_node_type="Display"):
    """
    Create the necessary nodes and relationships to link a Plot node to a Data node via a Display node.

    made ths function more generic to allow for different chart and node types
    """
    logger.debug(f"Starting create_plot_display_data_nodes with plot_id={plot_id}, data_id={data_id}, schema={schema}")

    async with conn.transaction():
        # Ensure the Plot node exists
        plot_record, _, status_code = await get_node(conn, plot_id, plot_node_type, schema=schema)
        if not plot_record:
            logger.debug("Plot node not found. Creating a new one.")
            plot_props = create_default_json(plot_node_type)
            plot_props['name'] = 'Plot of Data : ' + str(data_id)
            plot_record, _, status_code = await create_node(conn, plot_props, plot_node_type, schema=schema)
            plot_id = plot_record.get('id')
            if not plot_id:
                logger.error("Failed to create Plot node.")
                return {"error": "Failed to create Plot node"}, 500
        else:
            logger.debug(f"Plot node found: {plot_record}")

        # Ensure the Data node exists
        data_record, _, status_code = await get_node(conn, data_id, data_node_type, schema=schema)
        if not data_record:
            logger.warning(f"No Data node found with ID: {data_id}. Using default properties.")
            data_id = -1
            data_props = create_default_json(data_node_type)
        else:
            logger.debug(f"Data node found: {data_record}")

        # Create a Display node
        display_props = create_default_json(display_node_type)
        display_record, _, status_code = await create_node(conn, display_props, display_node_type, schema=schema)
        display_id = display_record.get('id')
        if not display_id:
            logger.error("Failed to create Display node.")
            return {"error": "Failed to create Display node"}, 500

        # Try creating relationships (these will be skipped if they already exist)
        logger.debug(f"Linking Plot ({plot_id}) → Display ({display_id})")
        relationship_label = plot_node_type.upper() + '_OF_' + display_node_type.upper()
        ## default label = 'PLOT_OF_DISPLAY'
        await create_relationship(conn, relationship_label, plot_id, display_id, schema=schema)

        if data_id != -1:
            logger.debug(f"Linking Display ({display_id}) → Data ({data_id})")
            relationship_label = display_node_type.upper() + '_OF_' + data_node_type.upper()
            ## default label = 'DISPLAY_OF_DATA'
            await create_relationship(conn, relationship_label, display_id, data_id, schema=schema)

    logger.info("Nodes and relationships created successfully.")
    return {"message": "Nodes and relationships created successfully", "plot_id": plot_id}, 201
'''

async def create_plot_display_data_nodes(conn, plot_id, data_id, schema="data"):
    """
    Create the necessary nodes and relationships to link a Plot node to a Data node via a Display node.
    Only creates a Display node and relationships if one does not already exist.
    """
    logger.debug(f"Starting create_plot_display_data_nodes with plot_id={plot_id}, data_id={data_id}, schema={schema}")

    async with conn.transaction():
        # Ensure the Plot node exists
        plot_nodes, _ = await get_node(conn, plot_id, "Plot", schema=schema)
        if not plot_nodes:
            logger.debug("Plot node not found. Creating a new one.")
            plot_props = create_default_json("Plot")
            plot_props['name'] = f'Plot of Data : {data_id}'
            plot_nodes, _ = await create_node(conn, plot_props, "Plot", schema=schema)
            plot_id = plot_nodes[0].get('record').get('id')
            if not plot_id:
                logger.error("Failed to create Plot node.")
                return {"error": "Failed to create Plot node"}, 500
        else:
            logger.debug(f"Plot node found: {plot_record}")

        # Ensure the Data node exists
        data_nodes, _ = await get_node(conn, data_id, "Data", schema=schema)
        if not data_nodes:
            logger.warning(f"No Data node found with ID: {data_id}. Using default properties.")
            data_id = -1
            data_props = create_default_json("Data")
        else:
            logger.debug(f"Data node found: {data_nodes[0].get('record')}")

        # Check if a Display node already links the given Plot and Data nodes (and none are archived)
        
        query = f"""
                SELECT plot_display.destination AS display_id
                FROM {schema}.relationship AS plot_display
                JOIN {schema}.relationship AS display_data
                ON plot_display.destination = display_data.source
                WHERE plot_display.source = $1
                AND display_data.destination = $2
                AND plot_display.label = 'PLOT_OF_DISPLAY'
                AND display_data.label = 'DISPLAY_OF_DATA'
                AND plot_display.archived IS NULL
                AND display_data.archived IS NULL
                LIMIT 1
                """

        plot_id_int = int(plot_id)
        data_id_int = int(data_id)

        existing_display = await conn.fetchrow(query, plot_id_int, data_id_int)

        if existing_display:
            logger.info("Existing Display node and relationships found. Skipping creation.")
            return {"message": "Display node already exists", "plot_id": plot_id}, 200

        # Create new Display node
        display_props = create_default_json("Display")
        display_nodes, _, _ = await create_node(conn, display_props, "Display", schema=schema)
        display_id = display_nodes[0].get('record').get('id')
        if not display_id:
            logger.error("Failed to create Display node.")
            return {"error": "Failed to create Display node"}, 500

        # Create relationships
        logger.debug(f"Linking Plot ({plot_id}) → Display ({display_id})")
        await create_relationship(conn, 'PLOT_OF_DISPLAY', plot_id, display_id, schema=schema)

        if data_id_int != -1:
            logger.debug(f"Linking Display ({display_id}) → Data ({data_id})")
            await create_relationship(conn, 'DISPLAY_OF_DATA', display_id, data_id, schema=schema)

    logger.info("Nodes and relationships created successfully.")
    return {"message": "Nodes and relationships created successfully", "plot_id": plot_id}, 201



async def fn_create_or_delete_plot_display_data_cached(data_id):
    """
    Updates the cached 'dmtools_current_plot' entry by linking or unlinking a Plot node to a Data node via a Display node in-memory.
    If data_id is positive: adds the Data node to the plot (if not already present).
    If data_id is negative: removes the Data node with abs(data_id) from the plot.
    Removes any display_data entry with data_record id == -1 before adding.

    Args:
        data_id (int): The ID of the Data node to link/unlink. If -1, uses default properties.

    Returns:
        dict: Updated current_plot with changes.
    """
    data_id = int(data_id)
    current_plot = await cache_get("dmtools_current_plot")
    if not current_plot:
        current_plot = {}

    # Ensure the plot node exists
    if "plot_node" not in current_plot or not current_plot["plot_node"]:
        plot_props = create_default_json("Plot")
        plot_props['name'] = f'Plot of Data : {abs(data_id)}'
        current_plot["plot_node"] = {
            "record": {"id": -1, "type": "Plot"},
            "properties": plot_props
        }
    else:
        # Update the plot name if adding a data node
        plot_properties = current_plot["plot_node"].get("properties", {})
        plot_name = plot_properties.get("name", "")
        if plot_name.startswith("Plot of Data :") and data_id > 0:
            plot_properties["name"] = f"{plot_name},{data_id}"

    # Remove any display_data entries with data_record id == -1
    if "display_data" in current_plot:
        new_display_data = []
        for entry in current_plot["display_data"]:
            data_record = entry["data"][0].get("record", {})
            if data_record.get("id", -1) == -1:
                continue  # skip this entry
            new_display_data.append(entry)
        current_plot["display_data"] = new_display_data

    # If data_id < 0, remove that data node from display_data and return
    if data_id < 0:
        abs_id = abs(data_id)
        if "display_data" in current_plot:
            filtered_display_data = []
            for entry in current_plot["display_data"]:
                data_record = entry["data"][0].get("record", {})
                if data_record.get("id") != abs_id:
                    filtered_display_data.append(entry)
            current_plot["display_data"] = filtered_display_data
        await cache_set("dmtools_current_plot", current_plot)
        return {"message": f"Removed Data node {abs_id} from plot", "plot_id": -1}, 200

    # Add the Data node as normal ONLY IF IT DOES NOT ALREADY EXIST
    if "display_data" not in current_plot:
        current_plot["display_data"] = []

    # Check for existing entry
    for entry in current_plot["display_data"]:
        data_record = entry["data"][0].get("record", {})
        if data_record.get("id") == data_id:
            return {"message": f"Data node {data_id} already exists in plot", "plot_id": -1}, 200

    # Get the Data node record/properties, or use defaults if not found
    if data_id == -1:
        data_record = {"id": -1, "type": "Data"}
        data_properties = create_default_json("Data")
    else:
        try:
            db_pool = await init_db_pool()
            async with db_pool.acquire() as conn:
                data_nodes, _ = await get_node(conn, data_id, "Data", schema='data')
        except Exception:
            data_record = {"id": data_id, "type": "Data"}
            data_properties = create_default_json("Data")

    # Create a new display node
    display_props = create_default_json("Display")
    display_record = {"id": -1, "type": "Display"}

    # Build new display_data dict structure
    display_data_entry = {
        "record": display_record,
        "properties": display_props,
        "data": [{
            "record": data_record,
            "properties": data_properties
        }]
    }

    # Add the new display_data to current_plot
    current_plot["display_data"].append(display_data_entry)

    # Save updated plot back to cache
    await cache_set("dmtools_current_plot", current_plot)

    return {"message": "Display node with Data node copy added to session", "plot_id": -1}, 201

async def add_display_data_session(conn, data_id, schema="data"):
    """
    Add a Display node to the current_plot in session if plot_id == -1.
    The Data node is fetched for its id and properties (not created).
    """
    logger.debug(f"Starting create Display data session data_id={data_id}, schema={schema}")

    current_plot = cache_get("dmtools_current_plot")

    display_record = get_default_record("Display")
    display_properties = {}

    # Only fetch Data node if a valid data_id is provided
    data_entry = None
    if data_id != -1:
        # Fetch Data node from DB (do not create)
        db_pool = await init_db_pool()
        async with db_pool.acquire() as conn:
            data_nodes, _ = await get_node(conn, data_id, "Data", schema=schema)
        if data_nodes and data_nodes[0].get("record").get("id"):
            data_entry = [data_nodes[0]]
        else:
            data_entry = []

    display_data_entry = {
        "record": display_record,
        "properties": display_properties,
    }

    if data_entry is not None:
        display_data_entry["data"] = data_entry

    if current_plot:
        # Ensure display_data exists
        if "display_data" not in current_plot or not isinstance(current_plot["display_data"], list):
            current_plot["display_data"] = []

        # Find Default Display (id == -1) and overwrite it, otherwise append
        default_index = None
        for i, d in enumerate(current_plot["display_data"]):
            if d.get("record", {}).get("id") == -1:
                default_index = i
                break

        if default_index is not None:
            current_plot["display_data"][default_index] = display_data_entry
            logger.info("Default Display in current_plot overwritten.")
        else:
            current_plot["display_data"].append(display_data_entry)
            logger.info("Added new Display to current_plot in session.")

        #session["current_plot"] = current_plot
        cache_data = await cache_set("current_plot", current_plot)
        logger.info("Added new Display with Data node copy to current_plot in session.")
    else:
        plot_record = get_default_record("Plot")
        plot_properties = {}
        current_plot = {
            "plot_node": {
                "record": plot_record,
                "properties": plot_properties
            },
            "display_data": [display_data_entry]
        }

        cache_data = await cache_set("dmtools_current_plot", current_plot)
        
        logger.info("Created new current_plot in session with one Display and Data node copy.")

        return {"message": "Display node with Data node copy added to session", "plot_id": -1}, 201

async def fn_displays_edit():
    logger.info("Displays Edit called.")
    session_plot_id = await cache_get('dmtools_plot_id')

    logger.info("Selected Plot ID {session_plot_id}")

    db_pool = await init_db_pool()
    async with db_pool.acquire() as conn:
        
        try:
            selected_plot_id = int(session_plot_id)
        except:
            selected_plot_id = -1  # Default to -1 if conversion fails
    
        plot_title_id = f"Plot ID : {selected_plot_id}"

        plot_name, dmtools_edit_existing_plot_url, dmtools_edit_existing_legend_url = \
            await get_and_process_edit_plot_data(conn, selected_plot_id, data_id=-1)
        ## get_plot_display_data_nodes_cached
        
        data, selected_data_ids = await get_raw_display_data()
        print("fn_displays_edit - get_raw_display_data called with data >>>>>>>>>>", data)

        cache_return = await cache_set("dmtools_current_displays", data)


    return await render_template(
        'node/v0/display_edit.html'
    )


async def fn_plot_show_current():
    logger.info("Plot Show Current called.")

    db_pool = await init_db_pool()
    async with db_pool.acquire() as conn:
        try:
            current_plot = await cache_get("dmtools_current_plot")
            current_plot_id = current_plot.get("plot_node", {}).get("record", {}).get("id", -1) if current_plot else -1
            print("plot_operations - cached - current_plot_id >>>>>>>>>>>>>>>>>", current_plot_id)
            #plot_record, plot_properties, status = await get_node(conn, current_plot_id, 'Plot', schema="data")
            plot_record = current_plot.get("plot_node", {}).get("record", {})
            plot_properties = current_plot.get("plot_node", {}).get("properties", {})
            plot_title = plot_properties.get("name", "Plot")
            plot_name = f"Plot ID : {current_plot_id} - {plot_title}"
        except:
            current_plot_id = -1
            plot_name = "Plot"
            logger.error("Failed to retrieve current plot ID from cache or session.")

        plot_name, dmtools_edit_existing_plot_url, dmtools_edit_existing_legend_url = \
            await get_and_process_edit_plot_data(conn, current_plot_id, data_id=-1)
        ## get_plot_display_data_nodes_cached
        data, ids = await get_raw_display_data()

    return await render_template(
        'plot/v0/modular/plot_show.html'
    )

async def fn_plot_refresh_current():

    logger.info("Plot Refresh Current called.")

    db_pool = await init_db_pool()
    async with db_pool.acquire() as conn:
        current_plot = await cache_get("dmtools_current_plot")
        current_plot_id = current_plot.get("plot_node", {}).get("record", {}).get("id", -1) if current_plot else -1
        print("plot_operations - cached - current_plot_id >>>>>>>>>>>>>>>>>", current_plot_id)

        plot_name, dmtools_edit_existing_plot_url, dmtools_edit_existing_legend_url = \
            await get_and_process_edit_plot_data(conn, current_plot_id, data_id=-1)
        
        data, selected_ids = await get_raw_display_data()

        #cache_return = await cache_set('dmtools_selected_ids', selected_ids)

    return jsonify({"message": "Plot Refresh Current called"}), 200

async def fn_plot_show():
    logger.info("Plot Show called.")
    session_plot_id = await cache_get('dmtools_plot_id')

    logger.info("Selected Plot ID {session_plot_id}")

    db_pool = await init_db_pool()
    async with db_pool.acquire() as conn:
        
        try:
            selected_plot_id = int(session_plot_id)
        except:
            selected_plot_id = -1  # Default to -1 if conversion fails
    
        plot_title_id = f"Plot ID : {selected_plot_id}"

        plot_name, dmtools_edit_existing_plot_url, dmtools_edit_existing_legend_url = \
            await get_and_process_edit_plot_data(conn, selected_plot_id, data_id=-1)
        ## get_plot_display_data_nodes_cached
        data, selected_ids = await get_raw_display_data()

        #cache_return = await cache_set('dmtools_selected_ids', selected_ids)

    return await render_template('plot/v0/modular/plot_show.html')

## This function is used to create a new plot based on the selected data IDs
## and display the plot with the selected data
## It also handles the case where a plot ID is already selected.
async def fn_plot_new_ids():
    cache_return = await cache_delete('dmtools_plot_id')
    cache_return = await cache_delete('dmtools_data_id')
    cache_return = await cache_delete("dmtools_current_plot")
    current_plot = await make_default_display_data()
    cache_data = await cache_set("dmtools_current_plot", current_plot)
    db_pool = await init_db_pool()
    async with db_pool.acquire() as conn:
        selected_ids = await cache_get('dmtools_selected_ids')
        #selected_id_list = selected_ids.split(',') if selected_ids else []
        selected_id_list = selected_ids
        selected_node_type = await cache_get('dmtools_node_type')
        selected_data_id = await cache_get('dmtools_data_id')
        new_plot_id = -1

        ## create new plot based on the list of data ids
        if selected_node_type == 'Data' and selected_ids:
            print("Creating new plot based on the list of data ids >>>>>>>>>>>>>>", selected_ids)
            for selected_id in selected_id_list:
                print("looping >> selected_id >>>>>>>>>>>>>>>>>", selected_id)
                selected_id_int = int(selected_id)
                if selected_id_int > 0:
                    message, status = await fn_create_or_delete_plot_display_data_cached(
                        data_id=selected_id_int
                    )
                    print("add data to plot >>> message >>>>", message)
                    print("add data to plot >>> status >>>>>>", status)
                    new_plot_id = message.get("plot_id", -1)
                    selected_plot_id = int(new_plot_id)
                    print("add data to plot >>> new plot id >>>>>>", selected_plot_id)

        print("plot operations - new_plot - cached selected_ids >>>>>>>>>>>>>>>>>", selected_ids)
        print("plot operations - new_plot - cached data_id >>>>>>>>>>>>>>>>>", selected_data_id)

        plot_title_id = f"Plot of Data IDs : {selected_ids}"

        current_plot = await cache_get("dmtools_current_plot")
        current_plot["plot_node"]["properties"]["name"] = plot_title_id
        cache_data = await cache_set("dmtools_current_plot", current_plot)

        plot_name, dmtools_edit_existing_plot_url, dmtools_edit_existing_legend_url = \
            await get_and_process_edit_plot_data(conn, plot_id=new_plot_id, data_id=-1)

        data, selected_ids = await get_raw_display_data()

    return await render_template(
        'plot/v0/modular/plot_show.html'
    )

async def fn_plot_new_empty():
    cache_return = await cache_delete('dmtools_plot_id')
    cache_return = await cache_delete('dmtools_data_id')
    cache_return = await cache_delete("dmtools_current_plot")
    current_plot = await make_default_display_data()
    cache_return = await cache_set("dmtools_current_plot", current_plot)

    return await render_template(
        'plot/v0/modular/plot_show.html'
    )


async def fn_plot_edit_current():
    db_pool = await init_db_pool()
    async with db_pool.acquire() as conn:
        try:
            #plot_id = await cache_get('dmtools_plot_id')
            #plot_id_int = int(plot_id)
            #data_id = await cache_get('dmtools_data_id')
            #data_id_int = int(data_id)
            current_plot = await cache_get("dmtools_current_plot")
            print("##############################current plot##############################################")
            print("plot_operations - cached - current_plot >>>>>>>>>>>>>>>>>", current_plot)
            current_plot_id = current_plot.get("plot_node", {}).get("record", {}).get("id", -1) if current_plot else -1
            print("plot_operations - cached - current_plot_id >>>>>>>>>>>>>>>>>", current_plot_id)
            #plot_record, plot_properties, status = await get_node(conn, current_plot_id, 'Plot', schema="data")
            plot_record = current_plot.get("plot_node", {}).get("record", {})
            plot_properties = current_plot.get("plot_node", {}).get("properties", {})
            plot_title = plot_properties.get("name", "Plot")
            plot_name = f"Plot ID : {current_plot_id} - {plot_title}"

            #cache_return = await cache_set("dmtools_current_node", [plot_record, plot_properties])

            plot_name, dmtools_plot_url, dmtools_legend_url = \
                await get_and_process_edit_plot_data(conn, current_plot_id, data_id=-1)
            
            data, selected_ids = await get_raw_display_data()

            #cache_return = await cache_set('dmtools_selected_ids', selected_ids)
            
        except:
            plot_name, dmtools_edit_plot_url, dmtools_edit_legend_url = await create_empty_chart_and_legend_svgs()
        
        print("##############################current plot##############################################")
    
    return await render_template('plot/v0/modular/plot_edit.html')
    
async def fn_plot_edit():
    db_pool = await init_db_pool()
    async with db_pool.acquire() as conn:
        
        #plot_id = await cache_get('dmtools_plot_id')
        #plot_id_int = int(plot_id)
        #data_id = await cache_get('dmtools_data_id')
        #data_id_int = int(data_id)
        current_plot = await cache_get("dmtools_current_plot")
        current_plot_id = current_plot.get("plot_node", {}).get("record", {}).get("id", -1) if current_plot else -1
        print("plot_operations - cached - current_plot_id >>>>>>>>>>>>>>>>>", current_plot_id)
        #plot_record, plot_properties, status = await get_node(conn, current_plot_id, 'Plot', schema="data")
        plot_record = current_plot.get("plot_node", {}).get("record", {})
        plot_properties = current_plot.get("plot_node", {}).get("properties", {})
        plot_title = plot_properties.get("name", "Plot")
        plot_name = f"Plot ID : {current_plot_id} - {plot_title}"

        #cache_return = await cache_set("dmtools_current_node", [plot_record, plot_properties])

        plot_name, dmtools_plot_url, dmtools_legend_url = \
            await get_and_process_edit_plot_data(conn, current_plot_id, data_id=-1)
        
        data, selected_ids = await get_raw_display_data()

        cache_return = await cache_set('dmtools_selected_ids', selected_ids)
    
    return await render_template('plot/v0/modular/plot_edit.html')



async def fn_display_update(display_id_in, display_data_in):
    display_id = display_id_in
    display_data = display_data_in
    display_id_int = int(display_id)
    print("Updated Data:", display_data)
    ## conn, node_id: int, data, node_type, user_node_id_in=-1, schema="data"
    db_pool = await init_db_pool()
    async with db_pool.acquire() as conn:
        data_nodes, status_code = await update_some_data_node(conn, display_id_int, display_data, 'Display')
        print("status_code >>>", status_code)
        print("data >>>", data_nodes[0].get('properties'))
    return jsonify({"message": "Display Data updated successfully"})
