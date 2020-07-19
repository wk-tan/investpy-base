# investpy-base
A dashboard has been built to display Malaysian stock movements, with data pulled from s3 bucket accessible to permitted individuals. Partial data for local testing has been provided but only include full set of data for sectors 'Pharmaceuticals' and 'Electricity' up to 8th May 2020.

## Requirements
`python 3.8`,
`pandas 1.0.3`,
`pyarrow 0.17.0`,
`dash 1.4.1`,


##  To view dashboard
1. Download data in the `inv_data` folder, download `app.py` for the dashboard build.
2. If user has access to s3 bucket, can run `app.py` as is, else comment lines in `app.py` that connects to s3 bucket and uncomment lines for local testing. Make sure path points to data files correctly.
3. Run `app.py` with `$ python app.py`. If permission error arises, try `$ sudo python app.py`.
```
$ sudo python app.py
Password:
Running on http://127.0.0.1:8050/
```
4. Depending on your computer's localhost setup, open the link in the browser. For example, in this case copy `http://127.0.0.1:8050/` and paste in browser to open.

## Known issues/ Ideas
1. I've attempted to remove weekends using `rangebreak` but it's not working. Possible issue: https://github.com/plotly/dash/issues/1196
2. `rangeslider` is used to provide options to view at different timeframes but range of y-axis may be unfavourable.
3. Should confirm latest data by matching dates instead of using e.g `iloc[-1]['Volume']`.
4. Detect increase or decrease from previous value, use red/green to indicate change direction.
5. Add candlestick chart in place/ add chart in another tab.
6. Links to latest trading news.
7. Add additional historical price/decision making analyses.

![alt image](https://github.com/ziqing-ang/investpy-base/blob/master/images/investmy3_dash.png?raw=true)
