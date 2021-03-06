from flask import Flask, render_template, url_for, flash, redirect, request, session, logging
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from wtforms.fields.html5 import EmailField
from passlib.hash import sha256_crypt
import os
from werkzeug.utils import secure_filename
from functools import wraps

##########################  CONFIG  ####################################

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///unite.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

app.secret_key = 'testing321'

app.config['UPLOAD_FOLDER'] = 'C:/Users/VINOD/Desktop/twitter/twitter-ngo/flaskapp/static/profile_pics'
app.config['UPLOAD_POST_PIC'] = 'C:/Users/VINOD/Desktop/twitter/twitter-ngo/flaskapp/static/post_img'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'JPG', 'PNG'])


############################    MODELS  ##################################

# Likes association table (associates between users and likes with to columns)
likes = db.Table('likes',
                 db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                 db.Column('post_id', db.Integer, db.ForeignKey('post.id'))
                 )


# Likes association table (associates between users and likes with to columns)
followers = db.Table('follows',
                     db.Column('follower_id', db.Integer,
                               db.ForeignKey('user.id'), nullable=True),
                     db.Column('followed_id', db.Integer,
                               db.ForeignKey('user.id'), nullable=True)
                     )


# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), default='default.jpg')
    password = db.Column(db.String(64), nullable=False)
    verified = db.Column(db.Integer, default=0, nullable=True)
    posts = db.relationship('Post', backref='author', lazy=True)
    likes = db.relationship('Post', secondary=likes,
                            backref=db.backref('likes', lazy='dynamic'), lazy='dynamic')
    followed = db.relationship('User', secondary=followers,
                               primaryjoin=(followers.c.follower_id == id),
                               secondaryjoin=(followers.c.followed_id == id),
                               backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    # Defines how a user object will be printed in the shell
    def __repr__(self):
        return "User ('{self.username}', '{self.email}', '{self.id}')"


class NGOID(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ngo_id = db.Column(db.Integer,primary_key=True)

class Ngo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ngo_id = db.Column(db.Integer)
    ngo_name = db.Column(db.String(25), unique=True, nullable=False)
    ngo_email = db.Column(db.String(120), unique=True, nullable=False)
    ngo_image_file = db.Column(db.String(20), default='default.jpg')
    ng_info = db.Column(db.Text)
    ngo_password = db.Column(db.String(64), nullable=False)
    ngo_verified = db.Column(db.Integer, default=0, nullable=True)

    # Defines how a user object will be printed in the shell
    def __repr__(self):
        return "User ('{self.ngo_name}', '{self.ngo_email}', '{self.ngo_id}')"


# Post model
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_posted = db.Column(db.DateTime, nullable=False,
                            default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    post_img = db.Column(db.String(30))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    retweet = db.Column(db.Integer, default=None, nullable=True, unique=False)

    # Defines how a post object will be printed in the shell
    def __repr__(self):
        return "Post ('{self.id}', '{self.date_posted}')"


##################################  UTILS #####################################

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap


# Returns current user
def current_user():
    if len(session) > 0:
        return User.query.filter_by(username=session['username']).first()
    else:
        return None


############################    ROUTES  #####################################

# Home route (default)
@app.route('/')
def home():
    posts = Post.query.all()
    follow_suggestions = User.query.all()[0:]
    follow_suggestions_ngo = Ngo.query.all()[0:]
    # post_img = Post.query.all()[0:]
    # Remove current user from follow suggestions
    if current_user():  # If there is a user in the session
        if current_user() in follow_suggestions:  # If the current user is in the user's follow suggestions
            follow_suggestions.remove(current_user())

    if current_user():  # If there is a user in the session
        if current_user() in follow_suggestions_ngo:  # If the current user is in the user's follow suggestions
            follow_suggestions_ngo.remove(current_user())

    return render_template('home.html', posts=posts, user=current_user(), Post_model=Post, likes=likes, follow_suggestions=follow_suggestions,follow_suggestions_ngo=follow_suggestions_ngo, User=User)

@app.route('/admin')
def admin():
    posts = Post.query.all()
    ngo = Ngo.query.filter_by(ngo_id=session['ngo_id']).first()

    # # Remove current user from follow suggestions
    # if current_user():  # If there is a user in the session
    #     if current_user() in follow_suggestions:  # If the current user is in the user's follow suggestions
    #         follow_suggestions.remove(current_user())

    return render_template('admin.html', posts=posts, Post_model=Post, likes=likes, ngo=ngo)


# Home route (following)
@app.route('/home_following')
@is_logged_in
def home_following():
    posts = []
    follow_suggestions = User.query.all()[0:]

    follows = current_user().followed.all()

    for follow in follows:  # Get all posts by folled accounts
        user_posts = Post.query.filter_by(author=follow)
        posts += user_posts

    posts.sort(key=lambda r: r.date_posted)  # Sorts posts by date

    # Remove current user from follow suggestions
    if current_user():  # If there is a user in the session
        if current_user() in follow_suggestions:  # If the current user is in the user's follow suggestions
            follow_suggestions.remove(current_user())

    return render_template('home.html', posts=posts, user=current_user(), Post_model=Post, likes=likes, follow_suggestions=follow_suggestions, User=User)


# Single post route
@app.route('/post/<string:id>')
def post(id):

    post = Post.query.filter_by(id=id).first()

    return render_template('post.html', id=id, post=post)


# Register form class
class RegisterForm(Form):
    username = StringField('Username', [validators.Length(min=1, max=25)])
    email = EmailField('Email', [validators.Length(min=6, max=120),validators.Email()])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')


class AdminRegisterForm(Form):
    ngo_name = StringField('NGO Name', [validators.Length(min=1, max=25),validators.Required()])
    ngo_email = EmailField('Email', [validators.Length(min=6, max=120),validators.Email()])
    ngo_reg_id = StringField('NGO REGISTER ID', [validators.Length(min=4, max=120),validators.Required()])
    ngo_password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('ngo_confirm', message='Passwords do not match')
    ])
    ngo_confirm = PasswordField('Confirm Password')

# NGO Register
@app.route('/ngo_register', methods=['GET', 'POST'])
def ngo_register():
    ngoid = [19001,19002,19003,19004,19005,19006,19007,19008,19009,19010,19011,19012,19013,19014,19015,19016]
    form = AdminRegisterForm(request.form)
    if request.method == 'POST' and form.validate():

        # Get form data
        ngo_name = form.ngo_name.data
        ngo_email = form.ngo_email.data.lower()
        ngo_reg_id = form.ngo_reg_id.data
        ngo_info = request.form['content']
        ngo_password = sha256_crypt.encrypt(str(form.ngo_password.data))
        file = request.files['file']

        # Get NGO ID 
        ngo_id = False

        for i in ngoid:
            if i == int(ngo_reg_id):
                ngo_id = True
                break
            else:
                ngo_id = False

        if ngo_id:
            # Make user object with form data
            ngo = Ngo(ngo_name=ngo_name, ngo_email=ngo_email,ngo_id=ngo_reg_id,ngo_image_file=file.filename,ng_info=ngo_info, ngo_password=ngo_password)

            # Add user object to session
            db.session.add(ngo)
  
            # Commit session to db
            db.session.commit()

            flash('You are now registered and can log in', 'success')

            return redirect(url_for('login'))
        else:
            flash('Enter Valid NGO ID', 'warning')  

    return render_template('ngo_register.html', form=form)



# Donate route
@app.route('/doante_ngo', methods=['GET', 'POST'])
def donate_ngo():
    user = User.query.all()[0:]

    return render_template('donate_ngo.html', User=user)

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():

        # Get form data
        username = form.username.data
        email = form.email.data.lower()
        password = sha256_crypt.encrypt(str(form.password.data))

        # Make user object with form data
        user = User(username=username, email=email, password=password)
        # Add user object to session
        db.session.add(user)
            

        # Commit session to db
        db.session.commit()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))

    return render_template('register.html', form=form)


# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get form fields
        email = request.form['email'].lower()
        password_candidate = request.form['password']
        role = request.form['role'].lower()

        # Get user by email
        user = User.query.filter_by(email=email).first()
        ngo  = Ngo.query.filter_by(ngo_email=email).first()

        if role != 'ngo':
            # If there is a user with the email
            if user != None:  
                # Get stored hash
                password = user.password

                # If passwords match
                if sha256_crypt.verify(password_candidate, password):
                # Passed
                    session['logged_in'] = True
                    session['username'] = user.username
                    session['user_id'] = user.id

                    app.logger.info('{user.username} LOGGED IN SUCCESSFULLY')
                    flash('You are now logged in', 'success')
                    return redirect(url_for('home'))

                    # If passwords don't match
                else:
                    error = 'Invalid password'
                    return render_template('login.html', error=error)

            # No user with the email
            else:
                error = 'Email not found'
                return render_template('login.html', error=error)
        else:
            if ngo != None:  
                # Get stored hash
                ngo_password = ngo.ngo_password

                # If passwords match
                if sha256_crypt.verify(password_candidate, ngo_password):
                # Passed
                    session['logged_in'] = True
                    session['ngo_name'] = ngo.ngo_name
                    session['ngo_id'] = ngo.ngo_id

                    app.logger.info('{ngo.ngo_name} LOGGED IN SUCCESSFULLY')
                    flash('You are now logged in', 'success')
                    return redirect(url_for('admin'))

                    # If passwords don't match
                else:
                    error = 'Invalid password'
                    return render_template('login.html', error=error)

            # No user with the email
            else:
                error = 'Email not found'
                return render_template('login.html', error=error)

    # GET Request
    return render_template('login.html')


# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# Profile route
@app.route('/profile')
@is_logged_in
def profile():
    profile_pic = url_for('static', filename='profile_pics/' + current_user().image_file)
    user = User.query.filter_by(username=session['username']).first()
    return render_template('profile.html', profile_pic=profile_pic,user=user,Post_model=Post,User=User,likes=likes)


# Post form class
class PostForm(Form):
    content = TextAreaField('Content', [validators.Length(min=1, max=280)])
    

# New Post
@app.route('/new_post', methods=['GET', 'POST'])
@is_logged_in
def new_post():
    form = PostForm(request.form)
    if request.method == 'POST' and form.validate():
        # Get form content
        content = form.content.data

        # Make post object
        post = Post(content=content, author=current_user())

        if 'post_pic' not in request.files:
            db.session.add(post)
            db.session.commit()
            
            flash('Your new post has been created!', 'success')
            return redirect(url_for('home',user=current_user(),Post_model=Post))

        file = request.files['post_pic']

    
        if file and allowed_file(file.filename):

            filename = secure_filename(file.filename)

            post.post_img = filename

            file.save(os.path.join(app.config['UPLOAD_POST_PIC'], filename))

        # Add post to db session
        db.session.add(post)

        # Commit session to db
        db.session.commit()
        
        # return render_template('home.html', user=current_user(),Post_model=Post)
        
        flash('Your new post has been created!', 'success')
        return redirect(url_for('home',user=current_user(),Post_model=Post))

    return render_template('new_post.html', form=form)


# Like post
@app.route('/like/<id>')
@is_logged_in
def like_post(id):

    post = Post.query.filter_by(id=id).first()

    # If the requested post does not exist
    if post is None:
        flash("Post '{id}' not found", 'warning')
        return redirect(url_for('home'))

    # If the user has already liked the post
    if current_user() in post.likes.all():
        post.likes.remove(current_user())
        db.session.commit()
        return redirect(url_for('home', _anchor=id))
    # If the user has not liked the post yet
    else:
        post.likes.append(current_user())
        db.session.commit()
        return redirect(url_for('home', _anchor=id))


# Split filename into file extension
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Update picture
@app.route('/update_photo', methods=['GET', 'POST'])
@is_logged_in
def update_photo():

    if request.method == 'POST':

        # No file selected
        if 'file' not in request.files:

            flash('No file selected', 'danger')
            return redirect(url_for('update_photo'))

        file = request.files['file']
        # If empty file
        if file.filename == '':

            flash('No file selected', 'danger')
            return redirect(url_for('update_photo'))

        # If there is a file and it is allowed
        if file and allowed_file(file.filename):

            filename = secure_filename(file.filename)

            current_user().image_file = filename
            db.session.commit()

            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            flash(
                'Succesfully changed profile picture', 'success')
            return redirect(url_for('profile'))

    return render_template('update_photo.html', user=current_user())


# Search route
@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':

        # Get query from form
        query = request.form['search']

        # Search and save posts
        posts = Post.query.filter(
            Post.content.like('%' + query + '%'))
        user = User.query.filter(
            User.username.like('%' +query +  '%'))

        return render_template('results.html',posts=posts, Post_model=Post, user=current_user(), query=query,User=user)

@app.route('/search_ngo', methods=['GET', 'POST'])
def search_ngo():
    if request.method == 'POST':

        # Get query from form
        query = request.form['search']
        follow_suggestions = User.query.all()[0:]
 
        # post_img = Post.query.filter_by(post_img=current_user().id)
        # Remove current user from follow suggestions
        if current_user():  # If there is a user in the session
            if current_user() in follow_suggestions:  # If the current user is in the user's follow suggestions
                follow_suggestions.remove(current_user())
        # Search
        user = User.query.filter(
            User.username.like('%' +query +  '%'))
        ngo = Ngo.query.filter(
            Ngo.ngo_name.like('%' +query +  '%'))

        return render_template('follower.html',Post_model=Post, user=current_user(),follow_suggestions=follow_suggestions, query=query,User=user,ngo=ngo)


# Follow route
@app.route('/follow/<id>')
@is_logged_in
def follow(id):

    # Get current user
    user_following = current_user()
    # Find user being followed by id
    user_followed = User.query.filter_by(id=id).first()

    if user_following == user_followed:

        flash("You can't follow yourself -_-", 'danger')
        return redirect(url_for('home'))

    else:
        # Follow user
        user_following.followed.append(user_followed)

        # Commit to db
        db.session.commit()

        flash('Followed', 'success')
        return redirect(url_for('home'))


# Unfollow route
@app.route('/unfollow/<id>')
@is_logged_in
def unfollow(id):
    # Get current user
    user_unfollowing = current_user()
    # Get user being unfollowed by id
    user_unfollowed = User.query.filter_by(id=id).first()

    if user_unfollowing == user_unfollowed:

        flash('You cant unfollow yourself -_-', 'danger')
        return redirect(url_for('home'))

    else:
        # Unfollow
        user_unfollowing.followed.remove(user_unfollowed)

        # Commit to db
        db.session.commit()

        flash('Unfollowed', 'warning')
        return redirect(url_for('home'))


# Retweet route
@app.route('/retweet/<id>')
@is_logged_in
def retweet(id):
    re_post = Post.query.filter_by(id=id).first()
    
    post = Post(content='', user_id=current_user().id, retweet=id)

    if re_post.retweet != None:
        flash("You can't retweet a retweeted tweet :(", 'danger')
        return redirect(url_for('home'))

    if Post.query.filter_by(user_id=current_user().id).filter_by(retweet=id).all():
        rm_post = Post.query.filter_by(
            user_id=current_user().id).filter_by(retweet=id).first()
        db.session.delete(rm_post)
        db.session.commit()

        flash('Unretweeted successfully', 'warning')
        return redirect(url_for('home'))

    # if file and allowed_file(file.filename):

    #     filename = secure_filename(file.filename)

    #     post.post_img = filename

    #     file.save(os.path.join(app.config['UPLOAD_POST_PIC'], filename))

 
    db.session.add(post)
    db.session.commit()

    flash('Retweeted successfully', 'success')
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
