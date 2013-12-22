# coding:utf8

from flask import Flask, render_template,request, url_for, send_from_directory
from flask.ext.pymongo import PyMongo
from datetime import datetime
import json
import os, string, random

app = Flask(__name__)
mongo = PyMongo(app)

# This is the path to the upload directory
app.config['UPLOAD_FOLDER'] = 'media/'
# These are the extension that we are accepting to be uploaded
app.config['ALLOWED_EXTENSIONS'] = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

# For a given file, return whether it's an allowed type or not
def allowed_file(content_type):
    return '/' in content_type and \
           content_type.rsplit('/', 1)[1] in app.config['ALLOWED_EXTENSIONS']

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for x in range(size))


@app.route('/post/<path:title>')
def post_page(title):
	try:
		post = mongo.db.post.find_one({'title':title})
	except Exception, e:
		raise e
	return render_template('post_page.html', post=post)

@app.route('/archive/')
def archive_page():
	posts = mongo.db.post.find().limit(100)
	return render_template('archive_page.html', posts=posts)

@app.route('/admin/posts/')
def admin_posts_page():
	try:
		posts = mongo.db.post.find()
	except Exception, e:
		raise e
	return render_template('admin_posts_page.html', posts=posts)

@app.route('/admin/edit/', methods=["GET", "POST"])
@app.route('/admin/edit/<path:title>', methods=["GET", "POST"])
def article_edit_page(title=""):
	if request.method == "POST":
		try:
			# if title != request.form['title'] and mongo.db.post.find({'title':request.form['title']}):
			# 	return json.dumps({'type':'error', 'message':'标题重复了诶'})

			if title:
				mongo.db.post.update({'title':title}, {'title':request.form['title'], 'content':request.form['content'],'datetime': datetime.now()})
			else:
				mongo.db.post.save({'title':request.form['title'], 'content':request.form['content'],'datetime': datetime.now()})

		except Exception, e:
			raise e
		return json.dumps({'type':'success'})
	else:
		if title:
			try:
				post = mongo.db.post.find_one({'title':title})
			except Exception, e:
				raise e
		else:
			post = []
		return render_template('article_edit_page.html', post=post, update=(title!=""))

@app.route('/media_upload/', methods=["POST"])
def media_upload_api():
	files = request.files.getlist("image")
	for file in files:
		if file and allowed_file(file.content_type):
			now = datetime.now()
			directory = os.path.join(app.config['UPLOAD_FOLDER'], str(now.year), str(now.month), str(now.day))
			if not os.path.exists(directory):
				os.makedirs(directory)
			filename = id_generator()+'.'+file.content_type.split('/',1)[1]
			while (os.path.exists(os.path.join(directory, filename))):
				filename = id_generator+'.'+file.content_type.split('/',1)[1]
			file.save(os.path.join(directory, filename))
		return url_for('uploaded_file',
                            filepath=("%s/%s/%s/%s" % (str(now.year), str(now.month), str(now.day), filename)) )
	return "xx"

@app.route('/uploads/<path:filepath>')
def uploaded_file(filepath):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filepath)


if __name__ == '__main__':
	app.debug = True
	app.run()