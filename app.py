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
        
        return render_template('index.html')
    else:
        app.stock_symbol = request.form['stock_symbol']
        #app.closing_price = request.form['closing_price']
        #app.volume = request.form['volume']
        if request.form.get("closing_price"):
            app.closing_price = request.form['closing_price']
        else:
            app.closing_price = False

        if request.form.get("volume"):
            app.volume = request.form['volume']
        else:
            app.volume = False

        if app.volume == False and app.closing_price == False:
            app.script = ''
            app.div = ''
            
            app.msg = 'You did not select any data (e.g., volume or closing price) to be displayed.'
            return render_template('error_page.html', msg = app.msg)
            
        mydata = requests.get("https://www.quandl.com/api/v3/datasets/WIKI/"+app.stock_symbol+".json?rows=30")
        
        if 'quandl_error' in mydata.json():
            app.script = ''
            app.div = ''
            
            app.msg = 'The entered stock symbol "' + app.stock_symbol + '" is invalid.'
            return render_template('error_page.html', msg = app.msg)
            
        else:
            df = pd.DataFrame(mydata.json())
            dates=pd.to_datetime(np.array(df.ix['data'][0])[:,0])
            closing_prices = (np.array(df.ix['data'][0])[:,4]).astype(float)
            volume = (np.array(df.ix['data'][0])[:,5]).astype(float)
            factor=10**(len(str(int(volume[0]/closing_prices[0]))))
            volume = volume/factor
            app.stock_name = df['dataset']['name']
            extra_text_index = app.stock_name.find("Prices, Dividends, Splits and Trading Volume")
            if extra_text_index != -1:
                app.stock_name = app.stock_name[0:extra_text_index-1]
            
            ##################################################
            ########Bokeh block##############################
        
            # select the tools we want
            TOOLS="pan,wheel_zoom,box_zoom,reset,save"
        
            p1 = figure(tools=TOOLS, plot_width=500, plot_height=500, x_axis_type="datetime", x_axis_label='Date')
            if app.closing_price != False:
                p1.line(dates, closing_prices,line_width=2, color="blue", legend="closing price")
            if app.volume != False:
                p1.line(dates, volume,line_width=2, color="red",legend="volume/"+str(factor),)
            #p1.circle(dates, closing_prices, fill_color="red", size=6)
        
            plots = {'Red': p1}
        
            script, div = components(plots)        
            app.script = script
            app.div = div.values()[0]
            ##################################################
            ##################################################

            return redirect('/graph_page') 
            
@app.route('/graph_page')
def graph_page():
    return render_template('graph.html',stock_symbol = app.stock_symbol, closing_price = app.closing_price, volume = app.volume, stock_name = app.stock_name, scr = Markup(app.script), diiv = Markup(app.div))

if __name__ == '__main__':
  app.run(host='0.0.0.0')
