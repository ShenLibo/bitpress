# coding:utf8

from flask import Flask, render_template,request
app = Flask(__name__)

@app.route('/edit', methods=["GET", "POST"])
def article_edit():
	if request.method == "POST":
		return request.form['content']
	else:
		return render_template('article_edit_page.html')

if __name__ == '__main__':
	app.debug = True
	app.run()