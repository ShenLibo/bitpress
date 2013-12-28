# coding:utf8

from flask import Flask, render_template,request, url_for, send_from_directory, session, redirect, escape
from flask.ext.pymongo import PyMongo
from datetime import datetime
import settings
import json
import os, string, random
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function
app = Flask(__name__)
app.secret_key = settings.SECRET_KEY
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

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" in session:
        	return f(*args, **kwargs)
        return redirect(url_for('login_page', next=request.url))
        
    return decorated_function

@app.route('/post/<int:post_id>')
def post_page(post_id):
	try:
		post = mongo.db.post.find_one({'post_id':post_id})
	except Exception, e:
		raise e
	return render_template('post_page.html', post=post)

@app.route('/archive/')
def archive_page():
	posts = mongo.db.post.find({'type':'published'}).limit(100).sort([('datetime',-1)])
	return render_template('archive_page.html', posts=posts)

@app.route('/admin/login/', methods=["GET", "POST"])
def login_page():
	if request.method == "POST":
		try:
			if (request.form["username"] == settings.USERNAME) and (request.form["password"] == settings.PASSWORD):
				session["username"] = request.form["username"]
				return "success"
			else:
				return "fail"
		except KeyError:
			return "bad request"
	else: #TODO
		return'''
	        <form action="" method="post">
	            <p><input type=text name=username placeholder="Username"></p>
	            <p><input type=password name=password placeholder="Password"></p>
	            <p><input type=submit value=Login></p>
	        </form>
	    '''

@app.route('/admin/posts/')
@login_required
def admin_posts_page():
	try:
		posts = mongo.db.post.find()
	except Exception, e:
		raise e
	return render_template('admin_posts_page.html', posts=posts)

@app.route('/admin/edit/', methods=["GET", "POST"])
@app.route('/admin/edit/<int:post_id>', methods=["GET", "POST"])
# @app.route('/admin/edit/<path:title>', methods=["GET", "POST"])
@login_required
def article_edit_page(post_id=None):
	if request.method == "POST":
		if((not post_id) and ("post_id" in request.form) and (request.form["post_id"]!="")):
			post_id = int(request.form["post_id"])
		try:
			if post_id:
				mongo.db.post.update({'post_id':post_id}, {"$set": {'post_id':post_id, 'title':request.form['title'], 'content':request.form['content'], 'type':request.form['type']}})
			else:
				post_id = mongo.db.counter.find_and_modify(update={"$inc":{"post_id":1}}, new=True).get("post_id")
				mongo.db.post.save({'post_id':post_id, 'title':request.form['title'], 'content':request.form['content'], 'datetime': datetime.now(), 'type':request.form['type']})
		except KeyError:
			return json.dumps({'type':'fail', 'message':'KeyError'})
		return json.dumps({'type':'success', 'post_id': post_id})
	else:
		if post_id:
			try:
				post = mongo.db.post.find_one({'post_id':post_id})
			except Exception, e:
				raise e
		else:
			post = []
		return render_template('article_edit_page.html', post=post, update=(post_id!=""))

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
	return "xx" #FIXME

@app.route('/uploads/<path:filepath>')
def uploaded_file(filepath):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filepath)


if __name__ == '__main__':
	app.debug = True
	app.run()