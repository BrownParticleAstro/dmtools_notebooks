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
            encoded_data = urllib.parse.urlencode(data_in).encode('utf-8')
            create_request = urllib.request.Request(self.current_url, data=encoded_data, method='POST')
            create_request.add_header('dmtool-userid', str(self.dmtool_userid))
            create_request.add_header('dmtool-apikey', self.dmtool_apikey)
            create_request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        else:
            encoded_data = urllib.parse.urlencode(data_in).encode('utf-8')
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
    
    '''
    def get_data_for_plot(self, plot_id_in):
        data_display_df = get_data_displays_for_plot(plot_id_in)
        data_df_ret = pd.DataFrame()
        data_data_df_ret = pd.DataFrame()
        for index, row in data_display_df.iterrows():
            #print(row['c1'], row['c2']
            #print('data id from data >>>>', row['data_id'])
            fastapi_url_data = api_server + data_api + "read_a_data/?id_in="+str(row['data_id'])
            request = Request(fastapi_url_data, headers=request_header)
            r = urllib.request.urlopen(request, context=context)
            string = r.read().decode('utf-8')
            a_data_json_obj = json.loads(string)
            #print(a_data_json_obj)
            #a_data_df = pd.DataFrame(a_data_json_obj, index=[0])
            data_label = a_data_json_obj['data_label']
            data_string = a_data_json_obj['data']
            #print(data_string)
            string_csv = StringIO(data_string)
            data_data_resp_df = pd.read_csv(string_csv,sep=",", lineterminator="|")
            data_data_resp_df['data_id'] = row['data_id']
    
            data_df_resp = pd.DataFrame(data=a_data_json_obj, index=[0])
            #a_data_json_obj
            #print(a_data_json_obj)
            try:
                y_rescale = float(data_df_resp['y_rescale'].iloc[0])
            except:
                y_rescale = 1
            try:
                x_rescale = float(data_df_resp['x_rescale'].iloc[0])
            except:
                x_rescale = 1
            
            ## when do we rescale?
            data_data_resp_df['cross_sections'] = data_data_resp_df['y'].astype(float).apply(lambda y: y * y_rescale)
            data_data_resp_df['masses'] = data_data_resp_df['x'].astype(float).apply(lambda x: x * x_rescale)
            data_data_resp_df['trace_name'] = data_label
    
            data_data_df_ret = pd.concat([data_data_df_ret,data_data_resp_df])
            data_df_ret = pd.concat([data_df_ret,data_df_resp])
    
        return data_df_ret , data_data_df_ret
        '''

class Plot():
    def __init__(self):
        self.fig_chart_empty = go.Figure(data=[go.Scatter(x=[], y=[])])
        self.make_blank_chart('plot',0,0)
        
    ## need this for the inital build of the dash layout
    def make_blank_chart(self, plot_name_in, plot_id_in, old_plot_id_in):
        y_title_text = r"$\text{WIMP Mass [GeV}/c^{2}]$"
        x_title_text = r"$\text{Cross Section [cm}^{2}\text{] (normalized to nucleon)}$"
        plot_title = plot_name_in + " - Plot Reference:" + str(plot_id_in) + " - Old Plot ID:" + str(old_plot_id_in)
        #plot_title
        ## create empty chart
        self.fig_chart_empty = go.Figure(data=[go.Scatter(x=[], y=[])])
        self.fig_chart_empty.update_layout( autosize=False, width=800, height=800, )
        self.fig_chart_empty.update_layout(xaxis_range=[-1,-4])
        self.fig_chart_empty.update_layout(yaxis_range=[-1,-4])
        self.fig_chart_empty.update_layout(
                margin=dict(l=0, r=0, t=20, b=0),
                paper_bgcolor="LightSteelBlue",)
    
        self.fig_chart_empty.update_layout(
            title=dict(text=plot_title , font=dict(size=18), automargin=True, yref='paper')
        )
        self.fig_chart_empty.update_xaxes(
            #title_text=x_title_text,
            #type="log"
            type="linear"
        )
        self.fig_chart_empty.update_yaxes(
            #title_text=y_title_text,
            type="log"
            #type="linear"
        )
        

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











