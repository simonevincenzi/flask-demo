from flask import Flask, render_template, request, redirect, Markup
from bokeh.plotting import figure, output_file, show
from bokeh.models import Range1d
from bokeh.embed import components
import time
import datetime
import requests
import simplejson as json
import numpy as np
import pandas as pd

app = Flask(__name__)

app.script = ''
app.div = ''

@app.route('/')
def main():
  return redirect('/index')

@app.route('/index',methods=['GET','POST'])
def index():
    if request.method == 'GET':  
        app.script = ''
        app.div = ''
        app.stock_symbol = ''
        app.stock_name = ''
        app.closing_price = ''
        app.volume = ''
     	app.opening_price = ''
        
        return render_template('index.html') # this displays the form for data entry
    else:
        app.stock_symbol = request.form['stock_symbol']
        
        if request.form.get("closing_price"):
            app.closing_price = request.form['closing_price']
        else:
            app.closing_price = False

        if request.form.get("volume"):
            app.volume = request.form['volume']
        else:
            app.volume = False
            
        if request.form.get("opening_price"):
            app.opening_price = request.form['opening_price']
        else:
            app.opening_price = False

        if app.volume == False and app.closing_price == False and app.opening_price == False:
            app.script = ''
            app.div = ''
            
            app.msg = 'No options selected for display. Select either volume, opening, or closing prices'
            return render_template('error_page.html', msg = app.msg)
            
        mydata = requests.get("https://www.quandl.com/api/v3/datasets/WIKI/"+app.stock_symbol+".json?rows=60")
        
        if 'quandl_error' in mydata.json(): # if error is returned from the query
            app.script = ''
            app.div = ''
            
            app.msg = 'Stock symbol "' + app.stock_symbol + '" invalid. Try again'
            return render_template('error_page.html', msg = app.msg) # shows the error page
            
        else:
            df = pd.DataFrame(mydata.json()) # create pandas dataframe from mydata.json
            #ind_date = [index for (index, x) in enumerate(df.ix['column_names'].dataset) if x == 'Date']
            #ind_close = [index for (index, x) in enumerate(df.ix['column_names'].dataset) if x == 'Close']
            #ind_open = [index for (index, x) in enumerate(df.ix['column_names'].dataset) if x == 'Open']
            #ind_vol = [index for (index, x) in enumerate(df.ix['column_names'].dataset) if x == 'Volume']
            ind_date = 0
            ind_close = 4
            ind_open = 1
            ind_vol = 5
            #dates=pd.to_datetime(np.array(df.ix['data'][0])[:,int(ind_date[0])]) #extract the dates (position 0)
            dates=pd.to_datetime(np.array(df.ix['data'][0])[:,ind_date]) #extract the dates (position 0)
            closing_prices = (np.array(df.ix['data'][0])[:,ind_close]).astype(float) #extract closing_prices
            volume = (np.array(df.ix['data'][0])[:,ind_vol]).astype(float)
            opening_prices = (np.array(df.ix['data'][0])[:,ind_open]).astype(float)
            app.stock_name = df['dataset']['name']
            extra_text_index = app.stock_name.find("Prices, Dividends, Splits and Trading Volume")
            if extra_text_index != -1:
                app.stock_name = app.stock_name[0:extra_text_index-1]
            
            ##################################################
            ########Bokeh block##############################
        
            # select the tools we want
            TOOLS="pan,wheel_zoom,box_zoom,reset,save"
        
            p1 = figure(tools=TOOLS, plot_width=600, plot_height=600, x_axis_type="datetime", x_axis_label='Date')
            if app.opening_price != False:
          		p1.yaxis.axis_label = '$'
          		p1.line(dates, opening_prices, line_width = 3, color = "green", legend = "Opening price")
            if app.closing_price != False:
                p1.line(dates, closing_prices,line_width=3, color="blue", legend="Closing price")
                p1.yaxis.axis_label = '$'
            if app.volume != False:
                p1.line(dates, volume,line_width=3, color="red",legend="Volume",)
                p1.yaxis.axis_label = 'Shares'
          	
            
        
            plots = {'Red': p1}
        
            script, div = components(plots)        
            app.script = script
            app.div = div.values()[0]
            ##################################################
            ##################################################

            return redirect('/graph_page') 
            
@app.route('/graph_page')
def graph_page():
    return render_template('graph.html',stock_symbol = app.stock_symbol, 
    closing_price = app.closing_price,opening_price = app.opening_price,
    volume = app.volume,stock_name = app.stock_name, scr = Markup(app.script), diiv = Markup(app.div))

if __name__ == '__main__':
  app.run(host='0.0.0.0')
