from flask import Flask, g, render_template, url_for, abort

app = Flask(__name__)

@app.route('/<chamber>')
def show_charts(chamber):
	if chamber.lower() != 'house' and chamber.lower() != 'senate':
		abort(404)
	else:
		return render_template('chamber_charts.html', chamber=chamber.title())

if __name__ == '__main__':
    app.run(debug=True)