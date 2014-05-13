import os
from flask import Flask, g, render_template, url_for

app = Flask(__name__)

# @app.route('/numbers/<chamber>')
# def get_numbers(chamber):
# 	template = json.dumps(senate_bills)
# 	response = make_response(template)
# 	response.headers['Content-Type'] = 'applicaton/json'
# 	return response
#     url_for('static', filename = chamber + "_numbers_gchart.json")
 
# @app.route('/avgs/<chamber>')
# def get_numbers(chamber):
#     return url_for('static', filename = chamber + "_avgs_gchart.json")

@app.route('/house')
def show_charts():
    return render_template('chamber_charts.html')

@app.route('/senate')
def show_charts():
    return render_template('chamber_charts.html')

# @app.route('/avgs/<chamber>')
# def get_numbers(chamber):
#     return make_response('static/%s_avgs_gchart.json' chamber)

# @app.route('')
# def show_charts():
#     return render_template('chamber_charts.html', numbers=get_numbers(), avgs=get_avgs())

# @app.route('/senate')
# def show_charts():
#     return render_template('senate_charts.html')

if __name__ == '__main__':
    app.run(debug=True)