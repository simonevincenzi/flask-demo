from flask import Flask, render_template, request, redirect, Markup
from bokeh.plotting import figure, output_file, show # standard bokeh import
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
     	app.daily_diff_price = ''
        
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
        
        if request.form.get("daily_diff_price"):
            app.daily_diff_price = request.form['daily_diff_price']
        else:
            app.daily_diff_price = False
            

        if app.volume == False and app.closing_price == False and app.opening_price == False and app.daily_diff_price == False:
            app.script = ''
            app.div = ''
            
            app.msg = 'No options selected for display. Select either volume, opening, closing prices, or closing - opening'
            return render_template('error_page.html', msg = app.msg)
            
        stock_data = requests.get("https://www.quandl.com/api/v3/datasets/WIKI/"+app.stock_symbol+".json?rows=60") # last 60 days of open-market data
        
        if 'quandl_error' in stock_data.json(): # when the stock symbol is not correct, a field of stock_data.json is quandl_error
            app.script = ''
            app.div = ''
            
            app.msg = 'Stock symbol "' + app.stock_symbol + '" invalid. Try again'
            return render_template('error_page.html', msg = app.msg) # shows the error page
            
         ## the problem is that occasionally the query comes back empty, I do not know how to test for it because locally it does not happen   
            
        else:
            stock_df = pd.DataFrame(stock_data.json()) # create pandas dataframe from stock_data.json
            #ind_date = [index for (index, x) in enumerate(df.ix['column_names'].dataset) if x == 'Date']
            #ind_close = [index for (index, x) in enumerate(df.ix['column_names'].dataset) if x == 'Close']
            #ind_open = [index for (index, x) in enumerate(df.ix['column_names'].dataset) if x == 'Open']
            #ind_vol = [index for (index, x) in enumerate(df.ix['column_names'].dataset) if x == 'Volume']
            # for some reason the indexes are not kept, troubling
            ind_date = 0
            ind_close = 4
            ind_open = 1
            ind_vol = 5
            #dates=pd.to_datetime(np.array(stock_df.ix['data'][0])[:,int(ind_date[0])]) #extract the dates (position 0)
            dates=pd.to_datetime(np.array(stock_df.ix['data'][0])[:,ind_date]) #extract the dates (position 0)
            closing_prices = (np.array(stock_df.ix['data'][0])[:,ind_close]).astype(float) #extract closing_prices
            volume = (np.array(stock_df.ix['data'][0])[:,ind_vol]).astype(float) # should be integer, but no problem
            opening_prices = (np.array(stock_df.ix['data'][0])[:,ind_open]).astype(float)
            diff_prices = closing_prices - opening_prices
            app.stock_name = stock_df['dataset']['name']
            # I want to report the name of the company when plotting, but I need to delete 
            # Prices, Dividends, Splits and Trading Volume, which is always after. If it is
            # not present I get back a -1
            extra_text_index = app.stock_name.find("Prices")
            if extra_text_index != -1:
                app.stock_name = app.stock_name[0:extra_text_index-1] # I only keep the part before Prices etc.
            
            ######## Plot with Bokeh ##############################
        
            # select the tools we want
            TOOLS="pan,wheel_zoom,box_zoom,reset,save" # it would be nice to have the hover option, maybe later
        
            plot_stock = figure(tools=TOOLS, plot_width=480, plot_height=480, x_axis_type="datetime", x_axis_label='Date')
            if app.opening_price != False:  # it is never set = T
          		plot_stock.yaxis.axis_label = '$'
          		plot_stock.line(dates, opening_prices, line_width = 3, color = "green", legend = "Opening price")
          		plot_stock.circle(dates, opening_prices, fill_color="white", size=8)
            if app.closing_price != False:
                plot_stock.line(dates, closing_prices,line_width=3, color="blue", legend="Closing price")
                plot_stock.yaxis.axis_label = '$'
                plot_stock.circle(dates, closing_prices, fill_color="white", size=8)
            if app.volume != False:
                plot_stock.line(dates, volume,line_width=3, color="brown",legend="Volume",)
                plot_stock.yaxis.axis_label = 'Shares'
                plot_stock.circle(dates, volume, fill_color="white", size=8)
            if app.daily_diff_price != False:
                plot_stock.line(dates, diff_prices,line_width=3, color="brown",legend="Difference between Closing and Opening prices",)
                plot_stock.yaxis.axis_label = '$'
                plot_stock.circle(dates, diff_prices, fill_color="white", size=8)
                low_box = BoxAnnotation(plot=plot_stock, top=0, fill_alpha=0.1, fill_color='red')
                high_box = BoxAnnotation(plot=plot_stock, bottom=0, fill_alpha=0.1, fill_color='blue')
                plot_stock.renderers.extend([low_box, high_box])
          	
            
        
            plots = {'Red': plot_stock}
        
            script, div = components(plots)        
            app.script = script
            app.div = div.values()[0]
            ##################################################
            ##################################################

            return redirect('/graph_page') # go to graph page for the plots
            
@app.route('/graph_page')
def graph_page():
    return render_template('graph.html',stock_symbol = app.stock_symbol, 
    closing_price = app.closing_price,opening_price = app.opening_price,
    volume = app.volume, daily_diff_price = app.daily_diff_price,stock_name = app.stock_name, scr = Markup(app.script), diiv = Markup(app.div))

if __name__ == '__main__':
  app.run(host='0.0.0.0')
