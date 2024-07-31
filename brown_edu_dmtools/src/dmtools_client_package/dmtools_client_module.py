from io import StringIO
import pandas as pd
import json
from urllib.request import Request, urlopen

import ssl
import urllib
context = ssl._create_unverified_context()

from itertools import cycle
import plotly.graph_objs as go
from plotly.subplots import make_subplots

class DMToolsClient():
    def __init__(self, dmtool_userid_in, dmtool_apikey_in):
        self.context = ssl._create_unverified_context()
        self.dmtool_userid = dmtool_userid_in
        self.dmtool_apikey = dmtool_apikey_in
        self.api_server = "https://dmtools.brown.edu/"
        self.data_api = "dmtool/fastapi_data/open/data/"
        self.current_url = self.api_server + self.data_api
        self.current_df = pd.DataFrame()
        self.create_request_header()

    # Define scale factors
    def get_scale_factor(self, unit):
        BARN_CM2= 1e-24
    
        if (unit == "b"):
            return BARN_CM2
        elif (unit == "mb"):
            return 1e-3*BARN_CM2
        elif (unit == "ub"):
            return 1e-6*BARN_CM2
        elif (unit == "nb"):
            return 1e-9*BARN_CM2
        elif (unit == "pb"):
            return 1e-12*BARN_CM2
        elif (unit == "fb"):
            return 1e-15*BARN_CM2
        elif (unit == "ab"):
            return 1e-18*BARN_CM2
        elif (unit == "zb"):
            return 1e-21*BARN_CM2
        elif (unit == "yb"):
            return 1e-24*BARN_CM2
        elif (unit in ("cm2","cm^2")):
            return 1
        else:
            ## assume variant of cm^2
            return 1
    
    def create_request_header(self):
        self.request_header = {'dmtool-userid': self.dmtool_userid ,'dmtool-apikey': self.dmtool_apikey, 'Content-Type': 'application/x-www-form-urlencoded'}
    
    def create_current_url(self, purpose_in, subject_in, id_in):
        self.current_url = self.api_server + self.data_api + purpose_in + "_" + subject_in
        if id_in != '':
            self.current_url = self.current_url + '?id_in=' + str(id_in)
        else:
            self.current_url = self.current_url

    def read_current_as_json(self):
        current_request = Request(self.current_url, headers=self.request_header)
        r = urllib.request.urlopen(current_request, context=self.context)
        string = r.read().decode('utf-8')
        _data_json_obj = json.loads(string)
        return _data_json_obj
    
    def read_current_as_df(self):
        current_request = Request(self.current_url, headers=self.request_header)
        r = urllib.request.urlopen(current_request, context=self.context)
        string = r.read().decode('utf-8')
        data_json_obj = json.loads(string)
        self.current_df = pd.DataFrame(data_json_obj)
        self.current_df['row_id'] = self.current_df.index
        self.current_df['updated_at'] = pd.to_datetime(self.current_df['updated_at'], errors='coerce')
        self.current_df['updated_at'] = self.current_df['updated_at'].dt.strftime('%Y%m%d%H%M')
        return self.current_df
    
    def create_current(self,data_in,url_in): ## leave url in as needed for not found error
        if url_in == '':
            encoded_data = data_in.encode('utf-8')
            create_request = urllib.request.Request(self.current_url, data=encoded_data, method='POST')
            create_request.add_header('dmtool-userid', str(self.dmtool_userid))
            create_request.add_header('dmtool-apikey', self.dmtool_apikey)
            create_request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        else:
            encoded_data = data_in.encode('utf-8')
            create_request = urllib.request.Request(url_in, data=encoded_data, method='POST')
            create_request.add_header('dmtool-userid', str(self.dmtool_userid))
            create_request.add_header('dmtool-apikey', self.dmtool_apikey)
            create_request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        
        try:
            with urllib.request.urlopen(create_request, context=self.context) as response:
                response_data = response.read().decode('utf-8')
                response_json_obj = json.loads(response_data)
                return response_json_obj
        except urllib.error.HTTPError as e:
            if e.code == 307:
                redirect_url = e.headers['Location']
                return self.create_current(data_in, redirect_url)
            else:
                raise
    
    def update_current(self,data_id_in,data_in,url_in):
        if url_in == '':
            encoded_data = data_in.encode('utf-8')
            update_url = self.api_server + self.data_api + "update_a_data/?id_in=" + str(data_id_in)
            update_request = urllib.request.Request(update_url, data=encoded_data, method='PATCH')
            update_request.add_header('dmtool-userid', str(self.dmtool_userid))
            update_request.add_header('dmtool-apikey', self.dmtool_apikey)
            #update_request.add_header('Content-Type', 'application/x-www-form-urlencoded')
            update_request.add_header('Content-Type', 'application/json')
        else:
            encoded_data = data_in.encode('utf-8')
            update_request = urllib.request.Request(url_in, data=encoded_data, method='PATCH')
            update_request.add_header('dmtool-userid', str(self.dmtool_userid))
            update_request.add_header('dmtool-apikey', self.dmtool_apikey)
            update_request.add_header('Content-Type', 'application/json')
            #create_request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        
        try:
            with urllib.request.urlopen(update_request, context=context) as response:
                response_data = response.read().decode('utf-8')
                response_json_obj = json.loads(response_data)
                return response_json_obj
        except urllib.error.HTTPError as e:
            if e.code == 307:
                redirect_url = e.headers['Location']
                return self.update_current(data_id_in,data_in, redirect_url)
            elif e.code == 422:
                print("HTTP 422 Unprocessable Entity")
                error_response = e.read().decode('utf-8')
                return "Response content:", error_response
            else:
                print(f"Error: {e.code}")
                error_response = e.read().decode('utf-8')
                return "Response content:", error_response
    
    def delete_current(self,data_in,url_in):
        if url_in == '':
            encoded_data = urllib.parse.urlencode(data_in).encode('utf-8')
            delete_request = urllib.request.Request(self.current_url, data=encoded_data, method='DELETE')
            delete_request.add_header('dmtool-userid', str(self.dmtool_userid))
            delete_request.add_header('dmtool-apikey', self.dmtool_apikey)
            delete_request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        else:
            encoded_data = urllib.parse.urlencode(data_in).encode('utf-8')
            delete_request = urllib.request.Request(url_in, data=encoded_data, method='POST')
            delete_request.add_header('dmtool-userid', str(self.dmtool_userid))
            delete_request.add_header('dmtool-apikey', self.dmtool_apikey)
            delete_request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        
        try:
            with urllib.request.urlopen(delete_request, context=self.context) as response:
                response_data = response.read().decode('utf-8')
                response_json_obj = json.loads(response_data)
                return response_json_obj
        except urllib.error.HTTPError as e:
            if e.code == 307:
                redirect_url = e.headers['Location']
                return self.update_current(data_in, redirect_url)
            elif e.code == 422:
                print("HTTP 422 Unprocessable Entity")
                error_response = e.read().decode('utf-8')
                print("Response content:", error_response)
            else:
                print(f"Error: {e.code}")
                error_response = e.read().decode('utf-8')
                print("Response content:", error_response)

    def clean_data_values(self, data_id_in):
        fastapi_url_data = self.api_server + self.data_api + "read_a_data/?id_in=" + str(data_id_in)
        request = Request(fastapi_url_data, headers=self.request_header)
        r = urllib.request.urlopen(request, context=self.context)
        string = r.read().decode('utf-8')
        a_data_json_obj = json.loads(string)
        data_string = a_data_json_obj['data_values']
        #all_plots_json_obj[1]
        #a_data_df = pd.DataFrame(a_data_json_obj, index=[0])
        data_string = data_string.replace("{[", "")
        data_string = data_string.replace("]}", "")
        #print(data_string)
        data_series = data_string.split("]")
        len(data_series)
        lol = []
        for l in range(0,len(data_series)):
            series_lol = []
            series_id = 0
            trace_id = l + 1
            single_set = data_series[l]
            set_list = single_set.split(";")
            for i in set_list:
                ## the following was added due to a different approach to data_string format
                r0 = i.replace(',[','')
                r1 = r0.replace('  ',' ')
                r2 = r1.replace('  ',' ')
                r3 = r2.replace('  ',' ')
                r4 = r3.replace('\r\n','')
                r5 = r4.replace('\t',' ')
                r6 = r5.replace(',',' ')
                r7 = r6.replace('  ',' ')
                r8 = r7.replace('  ',' ')
                r9 = r8.replace('\n',' ')
                r10 = r9.replace("', '"," ")
                r11 = r10.replace("['[",'')
                r12 = r11.replace(']','')
                r13 = r12.replace('[','')
                r14 = r13.replace(',','')
                s = r14.lstrip()
                z = s.split(" ");
                try:
                    raw_y = z[1]
                    raw_x = z[0].replace(",[", "")
                    #print('print split z >>>>', z)
                except:
                    #print(z)
                    raw_y = '0'
                    raw_x = '0'
                
                try:
                    x = float(raw_x)
                    y = float(raw_y)
                    masses =  float(raw_x)
                    cross_sections = float(raw_y)
                    formatted_x = "{:.5e}".format(x)
                    formatted_y = "{:.5e}".format(y)
                    #append_this = str(trace_id) + "," + formatted_x + "," + formatted_y
                    #append_this = '['+formatted_x+','+formatted_y+'],'
                    append_this = [formatted_x, formatted_y]
                    series_lol = series_lol + [append_this]
                except:
                    print('rejected z >> ', z)
            lol = lol + [series_lol]
            

        # Convert the nested data to a JSON string

        nested_data_string = json.dumps(lol)
        
        # Construct the payload with the nested JSON string
        payload = {
            "data": nested_data_string
        }
        
        json_data = json.dumps(payload)
        print(json_data)
        r = self.update_current(data_id_in, json_data,'')
    

    def initialise_plot(self):
        #self.this_plot = all_plots_df_in[all_plots_df_in['id']==plot_id_in]
        read_a_plot_url = self.api_server + self.data_api + "read_a_plot/?id_in="+ str(0)
        current_request = Request(read_a_plot_url, headers=self.request_header)
        r = urllib.request.urlopen(current_request, context=self.context)
        string = r.read().decode('utf-8')
        data_json_obj = json.loads(string)
        self.plot_df = pd.DataFrame(data_json_obj)
        self.plot_df['row_id'] = self.plot_df.index
        self.plot_df['updated_at'] = pd.to_datetime(self.v['updated_at'], errors='coerce')
        self.plot_df['updated_at'] = self.plot_df['updated_at'].dt.strftime('%Y%m%d%H%M')
        self.plot_start_x_range = float(self.plot_df.iloc[0]['x_min'])
        self.plot_stop_x_range = float(self.plot_df.iloc[0]['x_max'])
        self.plot_start_y_range = float(self.plot_df.iloc[0]['y_min'])
        self.plot_stop_y_range = float(self.plot_df.iloc[0]['y_max'])
        self.plot_name = self.plot_df.iloc[0]['name']
        self.plot_old_id = self.plot_df.iloc[0]['old_id']
        self.plot_fig_chart_empty = go.Figure(data=[go.Scatter(x=[], y=[])])
        self.make_blank_chart()
        
    ## need this for the inital build of the dash layout
    def make_blank_chart(self):
        y_title_text = r"$\text{WIMP Mass [GeV}/c^{2}]$"
        x_title_text = r"$\text{Cross Section [cm}^{2}\text{] (normalized to nucleon)}$"
        plot_title = 'Blank Chart'
        #plot_title
        ## create empty chart
        self.plot_fig_chart_empty = go.Figure(data=[go.Scatter(x=[], y=[])])
        self.plot_fig_chart_empty.update_layout( autosize=False, width=800, height=800, )
        self.plot_fig_chart_empty.update_layout(xaxis_range=[-1,-4])
        self.plot_fig_chart_empty.update_layout(yaxis_range=[-1,-4])
        self.plot_fig_chart_empty.update_layout(
                margin=dict(l=0, r=0, t=20, b=0),
                paper_bgcolor="LightSteelBlue",)
    
        self.plot_fig_chart_empty.update_layout(
            title=dict(text=plot_title , font=dict(size=18), automargin=True, yref='paper')
        )
        self.plot_fig_chart_empty.update_xaxes(
            #title_text=x_title_text,
            #type="log"
            type="linear"
        )
        self.plot_fig_chart_empty.update_yaxes(
            #title_text=y_title_text,
            type="log"
            #type="linear"
        )
    
    def get_data_for_plot(self, plot_id_in):
        self.plot_id = plot_id_in
        self.data_df = pd.DataFrame()
        self.data_data_df = pd.DataFrame()
        read_by_plot_data_display_url = self.api_server + self.data_api + "read_by_plot_data_display/?id_in="+ str(self.plot_id)
        current_request = Request(read_by_plot_data_display_url, headers=self.request_header)
        r = urllib.request.urlopen(current_request, context=self.context)
        string = r.read().decode('utf-8')
        data_display_json_obj = json.loads(string)
        self.data_display_df = pd.DataFrame(data_display_json_obj)
        self.data_display_df['row_id'] = self.data_display_df.index
        self.data_display_df['updated_at'] = pd.to_datetime(self.data_display_df['updated_at'], errors='coerce')
        self.data_display_df['updated_at'] = self.data_display_df['updated_at'].dt.strftime('%Y%m%d%H%M')
        for index, row in self.data_display_df.iterrows():
            #print(row['c1'], row['c2']
            #print('data id from data >>>>', row['data_id'])
            read_a_data_url = self.api_server + self.data_api + "read_a_data/?id_in="+ str(row['data_id'])
            print("read_a_data_url >>>>>>>>>>>>>" , read_a_data_url)
            current_request = Request(read_a_data_url, headers=self.request_header)
            r = urllib.request.urlopen(current_request, context=self.context)
            string = r.read().decode('utf-8')
            a_data_json_obj = json.loads(string)
            data_label = a_data_json_obj['data_label']
            data_string = a_data_json_obj['data']
            # Convert the string back to a list of lists of lists
            reconstructed_list = json.loads(data_string)
            #print("Deserialized list:", reconstructed_list)
            
            # Flatten the list and add a reference to the top-level list
            flattened_data = []
            for i, sublist in enumerate(reconstructed_list):
                for inner_list in sublist:
                    flattened_data.append([i+1] + inner_list)
            
            # Create a DataFrame from the flattened list
            columns = ['trace_id', 'x', 'y']
            data_data_resp_df = pd.DataFrame(flattened_data, columns=columns)

            data_df_resp = pd.DataFrame(data=a_data_json_obj, index=[0])

            try:
                y_rescale = float(a_data_json_obj['y_rescale'])
            except:
                y_rescale = 1
            try:
                x_rescale = float(a_data_json_obj['x_rescale'])
            except:
                x_rescale = 1
            
            ## when do we rescale?
            data_data_resp_df['cross_sections'] = data_data_resp_df['y'].astype(float).apply(lambda y: y * y_rescale)
            data_data_resp_df['masses'] = data_data_resp_df['x'].astype(float).apply(lambda x: x * x_rescale)
            data_data_resp_df['trace_name'] = data_label
            data_data_resp_df['data_id'] = row['data_id']

            self.data_data_df = pd.concat([self.data_data_df,data_data_resp_df])
            self.data_df = pd.concat([self.data_df,data_df_resp])

        #trace_list = data_data_df[['data_id','trace_id']].drop_duplicate()
        trace_list_refs = self.data_data_df[['data_id','trace_id','trace_name']].copy()
        self.trace_list = trace_list_refs.drop_duplicates()

        #data_data_df.head(5)
        self.plot_min_cross_sections = self.data_data_df['cross_sections'].min()
        self.plot_max_cross_sections = self.data_data_df['cross_sections'].max()
        self.plot_min_masses = self.data_data_df['masses'].min()
        self.plot_max_masses = self.data_data_df['masses'].max()

    
    def create_plot(self):
        read_a_plot_url = self.api_server + self.data_api + "read_a_plot/?id_in="+ str(self.plot_id)
        current_request = Request(read_a_plot_url, headers=self.request_header)
        r = urllib.request.urlopen(current_request, context=self.context)
        string = r.read().decode('utf-8')
        data_display_json_obj = json.loads(string)
        self.plot_name = data_display_json_obj['name']
        self.plot_old_id = data_display_json_obj['old_id']
        
        plot_square_dimensions = 600

        m1 = go.layout.Margin(l=20,r=10,b=20,t=20,pad=0)
        hw = go.Layout(autosize=False,width=plot_square_dimensions,height=plot_square_dimensions)
        y_title_text = r"$\text{Cross Section [cm}^{2}\text{] (normalized to nucleon)}$"

        y1 = go.layout.YAxis(#title=y_title_text,
                            title_standoff = 0,
                            #range=[start_y_range,stop_y_range],
                            type="log",
                            titlefont=go.layout.yaxis.title.Font(color='SteelBlue'))

        x_title_text = r"$\text{WIMP Mass [GeV}/c^{2}]$"
        x1 = go.layout.XAxis(#title=x_title_text,
                            title_standoff = 0,
                            type="log",
                            #type="linear",
                            #range=[start_x_range,stop_x_range],
                            titlefont=go.layout.xaxis.title.Font(color='SteelBlue'))


        ##title1=go.layout.Title(text="Dark Matter Detection Results")

        self.fig_chart_populated = go.Figure(
            data=[go.Scatter(x=[], y=[])],
            layout=go.Layout(
                margin=m1,
                yaxis= y1,
                xaxis= x1
            )
        )

        self.plot_title = self.plot_name + " - P: " + str(self.plot_id) + " - O: " + str(self.plot_old_id)

        self.fig_chart_populated.update_layout(
            title=dict(text=self.plot_title ,font=dict(size=16),automargin=True,yref='paper')
        )

        self.fig_chart_populated.update_layout(hw)

        for index, row in self.data_display_df.iterrows():
            #print(row['limit_id'])
            data_id_selected = row['data_id']
            #print('selected data_id >>', data_id_selected)
            #data_about_selected_df = self.data_about_df[self.data_about_df['data_id']==data_id_selected].copy()
            data_display_selected_df = self.data_display_df[self.data_display_df['data_id']==data_id_selected].copy()
            #data_data_selected_df = self.data_data_df[self.data_data_df['data_id']==data_id_selected].copy()
            trace_style = data_display_selected_df['style'].iloc[0]
            trace_color = data_display_selected_df['color'].iloc[0]
            pt = PlotTrace()
            print("trace_color, trace_style >>>>>>>>>>>" , trace_color, trace_style)
            pt.set_values(trace_color, trace_style)
            traces = self.trace_list[self.trace_list['data_id']==data_id_selected]
            for index, trace_row in traces.iterrows():
                #print(row)
                trace_data = self.data_data_df[(self.data_data_df['data_id']==\
                                                trace_row['data_id']) & (self.data_data_df['trace_id']==trace_row['trace_id'])]
                #print(trace_data)
                #print("trace_data >>>>" , trace_data)
                trace_name = trace_row['trace_name']
                print("trace_name, pt.__dict__ >>>>", trace_name, pt.__dict__)
                self.fig_chart_populated.add_trace(go.Scatter(pt.__dict__,
                                                x=trace_data['masses'],
                                                y=trace_data['cross_sections'],
                                                name=trace_name,
                                                        showlegend=False
                                                    ))
    def create_populated_legend(self):
        rows_list = list(range(1,20))
        cols_list = list(range(1,4))

        table_rows=20
        table_cols=3
        #plot_square_dimensions = screen_height_in / 2
        legend_width = 600 ## this will be a maximum and will shrink if screen size < 800
        legend_height = 20 * 16
        self.fig_chart_legend = make_subplots(
                        column_titles = ['data_id','format'],
                        rows=table_rows,
                        cols=table_cols,
                        horizontal_spacing = 0.00,
                        vertical_spacing = 0.00,
                        #subplot_titles=(titles)
                        column_widths=[0.1,0.8,0.1])

        self.fig_chart_legend.update_layout(
            #    autosize=False,
                width=legend_width,
                height=legend_height,
                margin=dict(
                    l=0,
                    r=0,
                    b=0,
                    t=0,
                    pad=0
                ),
                paper_bgcolor="LightSteelBlue",
            )

        self.fig_chart_legend.update_xaxes(showgrid=False)
        self.fig_chart_legend.update_yaxes(showgrid=False)
        #legend
        self.fig_chart_legend.update_layout(showlegend=False)
        #x axis
        self.fig_chart_legend.update_xaxes(visible=False)
        #y axis
        self.fig_chart_legend.update_yaxes(visible=False)

        self.fig_chart_legend.data = []
        #fig_legend_out.show()

        # Any changes to the fig must be applied to the DataFrame as the dataframe
        # will be used when the plot is saved.
        # Saving zoom is still to be implemented

        #print("CD : data_display_df>>>>>>>>>", data_display_df_in)

        self.display_legend_df = self.data_display_df[['data_id','color','style']].copy()
        self.display_legend_df.drop_duplicates(inplace=True)

        rowloop = 1
        for index, row in self.display_legend_df.iterrows():
            data_selected_df = self.data_df[self.data_df['id']==row['data_id']].copy()
            trace_name = data_selected_df['data_label'].iloc[0]
            for c in cols_list: #enumerate here to get access to i
                # STEP 2, notice position of arguments!
                #table_column_names = ['data_id','data_label','format']
                scatter_mode_list = ['text-number','text-text','format']
                table_column_names = ['data_id','trace_name','format']
                trace_style = row['style']
                trace_color = row['color']
                data_id = row['data_id']
                pt = PlotTrace()
                pt.set_values(trace_color, trace_style)
                #tc.set_row_col(rowloop, c)
                #scatter_mode_list = ['text-number','text-text','format']
                #current_column = table_column_names[c-1]
                #current_mode = scatter_mode_list[c-1]
                current_column = table_column_names[c-1]
                current_mode = scatter_mode_list[c-1]
                #print(rowloop,current_column, current_mode )
                if current_mode =='format':
                    mode = pt.__dict__['mode']
                    #fill = 'toself'
                    fill = pt.__dict__['fill']
                    if mode == 'lines' and fill == 'none':
                        x_data = [0,1]
                        y_data = [0.5,0.5]
                    elif mode == 'lines' and fill == 'toself':
                        x_data = [0,1,1,0,0]
                        y_data = [0,0,1,1,0]
                    else:
                        x_data = [0,1]
                        y_data = [0.5,0.5]

                    self.fig_chart_legend.add_trace(go.Scatter(pt.__dict__,x=x_data,
                                                y=y_data),
                                row=rowloop, #index for the subplot, i+1 because plotly starts with 1
                                col=c)

                if current_mode =='text-number':
                    self.fig_chart_legend.add_trace(go.Scatter(x=[1,2],
                                            textposition='middle right',
                                            y=[1,1],
                                            mode='text',
                                            text=[str(data_id),'']
                                            ),
                                row=rowloop, #index for the subplot, i+1 because plotly starts with 1
                                col=c)
                if current_mode =='text-text':
                    self.fig_chart_legend.add_trace(go.Scatter(x=[1,2],
                                            textposition='middle right',
                                            y=[1,1],
                                            mode='text',
                                            text=[trace_name,'']
                                            ),
                                row=rowloop, #index for the subplot, i+1 because plotly starts with 1
                                col=c)

            rowloop=rowloop+1
            self.fig_chart_legend.update_xaxes(showgrid=False)
            self.fig_chart_legend.update_yaxes(showgrid=False)
            #legend
            self.fig_chart_legend.update_layout(showlegend=False)
            #x axis
            self.fig_chart_legend.update_xaxes(visible=False)
            #y axis
            self.fig_chart_legend.update_yaxes(visible=False)
        

class PlotTrace():
    def __init__(self):
      self.mode = 'lines' ### ['lines', 'lines+markers', 'markers']
      self.line = {'color' :'red', 'width': 1, 'dash' : 'solid'}
      self.marker = {'symbol':'x'}
      self.fillcolor = 'rgba(0,255,255,0.05)'
      self.opacity = 1
      self.fill = 'toself'
    
    def color_rgba(self, color_in):
      if color_in == 'cyan':
          self.fillcolor = 'rgba(0,255,255,0.05)'
      elif color_in == 'red':
          self.fillcolor = 'rgba(255,0,0,0.05)'
      elif color_in == 'blue':
          self.fillcolor = 'rgba(0,0,255,0.05)'
      elif color_in == 'green':
          self.fillcolor = 'rgba(0,255,0,0.05)'
      elif color_in == 'black':
          self.fillcolor = 'rgba(0,0,0,0.05)'
      elif color_in == 'magenta':
          self.fillcolor = 'rgba(255,0,255,0.05)'
      elif color_in == 'yellow':
          self.fillcolor = 'rgba(255,255,0,0.05)'
      elif color_in == 'white':
          self.fillcolor = 'rgba(255,255,255,0.05)'
      else:
          self.fillcolor = 'rgba(255,0,0,0.05)'
    
    def clean_the_color_in(self, color_in):
        if color_in in ('k', 'black', 'Blk'):
            return 'black'
        elif color_in in ('r', 'red', 'Red'):
            return 'red'
        elif color_in in  ('dkg','DkG', 'green', 'Grn'):
            return 'green'
        elif color_in in  ('ltg', 'LtG'):
            return 'green'
        elif color_in in ('LtR', 'ltr'):
            return 'red'
        elif color_in in  ('b'):
            return 'blue'
        elif color_in in  ('LtB','ltb', 'Blue'):
            return 'blue'
        elif color_in in  ('c', 'Cyan'):
            return 'cyan'
        elif color_in in ('g10','g20','g30','g40','g50','g60','g70','g80','g90', 'G60'):
            return 'grey'
        elif color_in in ('blue', 'dkb', 'DkB'):
            return 'blue'
        elif color_in in ('red','dkr'):
            return 'red'
        elif color_in in ('g', 'grey'):
            return 'grey'
        elif color_in in ('m', 'magenta', 'Mag'):
            return 'magenta'
        elif color_in in ('y', 'yellow'):
            return 'yellow'
        elif color_in in ('w', 'white'):
           return 'white'
        else :
            return 'purple'
    
    def set_values(self, color_in, style_in):
        cleaned_color = self.clean_the_color_in(color_in)
        if style_in in ('dot', 'dotted', 'Dot'):
            self.mode = 'lines' ### ['lines', 'lines+markers', 'markers']
            self.line = {'color' :cleaned_color, 'width': 1, 'dash' : 'solid'}
            self.marker = {'symbol':'x'}
            _rgba = self.color_rgba(cleaned_color)
            self.fillcolor = _rgba
            self.opacity = 1
            self.fill = 'none'
        elif style_in in ('dash', 'Dash'):
            self.mode = 'lines' ### ['lines', 'lines+markers', 'markers']
            self.line = {'color' :cleaned_color, 'width': 1, 'dash' : 'dash'}
            self.marker = {'symbol':'x'}
            _rgba = self.color_rgba(cleaned_color)
            self.fillcolor = _rgba
            self.opacity = 1
            self.fill = 'none'
        elif style_in in ('fill', 'Fill'):
            self.mode = 'lines' ### ['lines', 'lines+markers', 'markers']
            self.line = {'color' :cleaned_color, 'width': 1, 'dash' : 'solid'}
            self.marker = {'symbol':'x'}
            _rgba = self.color_rgba(cleaned_color)
            self.fillcolor = _rgba
            self.opacity = 1
            self.fill = 'toself'
        elif style_in in ('Line', 'line', 'lines'):
            self.mode = 'lines' ### ['lines', 'lines+markers', 'markers']
            self.line = {'color' :cleaned_color, 'width': 1, 'dash' : 'solid'}
            self.marker = {'symbol':'x'}
            _rgba = self.color_rgba(cleaned_color)
            self.fillcolor = _rgba
            self.opacity = 1
            self.fill = 'none'
        elif style_in == "point":
            self.mode = 'lines+markers' ### ['lines', 'lines+markers', 'markers']
            self.line = {'color' :cleaned_color, 'width': 1, 'dash' : 'solid'}
            self.marker = {'symbol':'x-dot'}
            _rgba = self.color_rgba(cleaned_color)
            self.fillcolor = _rgba
            self.opacity = 1
            self.fill = 'toself'
        elif style_in in ('cross', 'Cross'):
            #self.style = 'cross'
            self.mode = 'lines+markers' ### ['lines', 'lines+markers', 'markers']
            self.line = {'color' :cleaned_color, 'width': 1, 'dash' : 'solid'}
            self.line_width = 1
            self.marker = {'symbol':'cross'}
            self.opacity = 1
            self.fill = 'none'
        elif style_in ==  "circle":
            self.mode = 'lines+markers' ### ['lines', 'lines+markers', 'markers']
            self.line = {'color' :cleaned_color, 'width': 1, 'dash' : 'solid'}
            self.marker = {'symbol':'circle'}
            _rgba = self.color_rgba(cleaned_color)
            self.fillcolor = _rgba
            self.opacity = 1
            self.fill = 'none'
        elif style_in ==  "plus":
            self.mode = 'lines+markers' ### ['lines', 'lines+markers', 'markers']
            self.line = {'color' :cleaned_color, 'width': 1, 'dash' : 'solid'}
            self.marker = {'symbol':'square-cross'}
            _rgba = self.color_rgba(cleaned_color)
            self.fillcolor = _rgba
            self.opacity = 1
            self.fill = 'toself'
        elif style_in in ("asterisk",'star'):
            self.mode = 'lines+markers' ### ['lines', 'lines+markers', 'markers']
            self.line = {'color' :cleaned_color, 'width': 1, 'dash' : 'solid'}
            self.marker = {'symbol':'star'}
            _rgba = self.color_rgba(cleaned_color)
            self.fillcolor = _rgba
            self.opacity = 1
            self.fill = 'none'
        elif style_in in ('pentagon', "pent"):
            self.mode = 'lines+markers' ### ['lines', 'lines+markers', 'markers']
            self.line = {'color' :cleaned_color, 'width': 1, 'dash' : 'solid'}
            self.marker = {'symbol':'pentagon'}
            _rgba = self.color_rgba(cleaned_color)
            self.fillcolor = _rgba
            self.opacity = 1
            self.fill = 'toself'
        elif style_in == ("hex", 'hexagon'):
            self.mode = 'lines+markers' ### ['lines', 'lines+markers', 'markers']
            self.line = {'color' :cleaned_color, 'width': 1, 'dash' : 'solid'}
            self.marker = {'symbol':'hexagon'}
            _rgba = self.color_rgba(cleaned_color)
            self.fillcolor = _rgba
            self.opacity = 1
            self.fill = 'none'
        elif style_in == ("triu", 'triangle'):
            self.mode = 'lines+markers' ### ['lines', 'lines+markers', 'markers']
            self.line = {'color' :cleaned_color, 'width': 1, 'dash' : 'solid'}
            self.marker = {'symbol':'triangle-up'}
            _rgba = self.color_rgba(cleaned_color)
            self.fillcolor = _rgba
            self.opacity = 1
            self.fill = 'none'
        elif style_in ==  "trid":
            self.mode = 'lines+markers' ### ['lines', 'lines+markers', 'markers']
            self.line = {'color' :cleaned_color, 'width': 1, 'dash' : 'solid'}
            self.marker = {'symbol':'triangle-down'}
            _rgba = self.color_rgba(cleaned_color)
            self.fillcolor = _rgba
            self.opacity = 1
            self.fill = 'toself'
        elif style_in ==  "tril":
            self.mode = 'lines+markers' ### ['lines', 'lines+markers', 'markers']
            self.line = {'color' :cleaned_color, 'width': 1, 'dash' : 'solid'}
            self.marker = {'symbol':'triangle-left'}
            _rgba = self.color_rgba(cleaned_color)
            self.fillcolor = _rgba
            self.opacity = 1
            self.fill = 'none'
        elif style_in ==  "trir":
            self.mode = 'lines+markers' ### ['lines', 'lines+markers', 'markers']
            self.line = {'color' :cleaned_color, 'width': 1, 'dash' : 'solid'}
            self.marker = {'symbol':'triangle-right'}
            _rgba = self.color_rgba(cleaned_color)
            self.fillcolor = _rgba
            self.opacity = 1
            self.fill = 'none'
        else:
            self.mode = 'lines' ### ['lines', 'lines+markers', 'markers']
            self.line = {'color' :cleaned_color, 'width': 1, 'dash' : 'solid'}
            self.marker = {'symbol':'x'}
            _rgba = self.color_rgba(cleaned_color)
            self.fillcolor = _rgba
            self.opacity = 1
            self.fill = 'none'











