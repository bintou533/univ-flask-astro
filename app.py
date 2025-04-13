from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'bintoudame'

# Configuration de la base de données SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Modèles de la base de données ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

class AppareilPhoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    marque = db.Column(db.String(80), nullable=False)
    modele = db.Column(db.String(120), nullable=False)
    date_sortie = db.Column(db.String(20))
    score = db.Column(db.Integer)
    categorie = db.Column(db.String(50), nullable=False)
    resume = db.Column(db.Text)  # Ajout de la colonne resume

    def __repr__(self):
        return f'<AppareilPhoto {self.marque} {self.modele}>'

class Telecope(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    marque = db.Column(db.String(80), nullable=False)
    modele = db.Column(db.String(120), nullable=False)
    date_sortie = db.Column(db.String(20))
    score = db.Column(db.Integer)
    categorie = db.Column(db.String(50), nullable=False)
    resume = db.Column(db.Text)  # Ajout de la colonne resume

    def __repr__(self):
        return f'<Telecope {self.marque} {self.modele}>'

class ForumCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    threads = db.relationship('ForumThread', backref='category', lazy=True)

    def __repr__(self):
        return f'<ForumCategory {self.name}>'

class ForumThread(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='forum_threads')
    posts = db.relationship('ForumPost', backref='thread', lazy=True)
    category_id = db.Column(db.Integer, db.ForeignKey('forum_category.id'), nullable=False)

    def __repr__(self):
        return f'<ForumThread {self.title}>'

class ForumPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='forum_posts')
    thread_id = db.Column(db.Integer, db.ForeignKey('forum_thread.id'), nullable=False)

    def __repr__(self):
        return f'<ForumPost {self.content[:50]}...>'

# --- Fonction pour vérifier si l'utilisateur est connecté ---
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Vous devez être connecté pour accéder à cette page.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Routes pour le forum ---
@app.route('/forum')
def forum_index():
    categories = ForumCategory.query.all()
    return render_template('forum_index.html', categories=categories)

@app.route('/forum/category/<int:category_id>')
def forum_category(category_id):
    category = ForumCategory.query.get_or_404(category_id)
    threads = ForumThread.query.filter_by(category_id=category_id).order_by(ForumThread.created_at.desc()).all()
    return render_template('forum_category.html', category=category, threads=threads)

@app.route('/forum/thread/<int:thread_id>')
def forum_thread(thread_id):
    thread = ForumThread.query.get_or_404(thread_id)
    posts = ForumPost.query.filter_by(thread_id=thread_id).order_by(ForumPost.created_at).all()
    return render_template('forum_thread.html', thread=thread, posts=posts)

@app.route('/forum/new_thread/<int:category_id>', methods=['GET', 'POST'])
@login_required
def new_thread(category_id):
    category = ForumCategory.query.get_or_404(category_id)
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        if not title or not content:
            flash('Le titre et le contenu sont requis.')
            return render_template('new_thread.html', category=category)
        new_thread = ForumThread(title=title, category_id=category_id, user_id=session['user_id'])
        db.session.add(new_thread)
        db.session.commit()
        new_post = ForumPost(content=content, thread_id=new_thread.id, user_id=session['user_id'])
        db.session.add(new_post)
        db.session.commit()
        flash('Nouveau fil de discussion créé!')
        return redirect(url_for('forum_thread', thread_id=new_thread.id))
    return render_template('new_thread.html', category=category)

@app.route('/forum/reply/<int:thread_id>', methods=['GET', 'POST'])
@login_required
def reply_to_thread(thread_id):
    thread = ForumThread.query.get_or_404(thread_id)
    if request.method == 'POST':
        content = request.form['content']
        if not content:
            flash('Le contenu de la réponse est requis.')
            return render_template('reply_to_thread.html', thread=thread)
        new_post = ForumPost(content=content, thread_id=thread_id, user_id=session['user_id'])
        db.session.add(new_post)
        db.session.commit()
        flash('Réponse ajoutée!')
        return redirect(url_for('forum_thread', thread_id=thread_id))
    return render_template('reply_to_thread.html', thread=thread)

# --- Routes pour l'authentification ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None

        if not username:
            error = 'Le nom d\'utilisateur est requis.'
        elif not password:
            error = 'Le mot de passe est requis.'
        elif User.query.filter_by(username=username).first() is not None:
            error = f'L\'utilisateur {username} est déjà enregistré.'

        if error is None:
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Inscription réussie! Veuillez vous connecter.')
            return redirect(url_for('login'))
        else:
            flash(error)
            return render_template('register.html')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None
        user = User.query.filter_by(username=username).first()

        if user is None:
            error = 'Nom d\'utilisateur incorrect.'
        elif not check_password_hash(user.password, password):
            error = 'Mot de passe incorrect.'

        if error is None:
            session.clear()
            session['user_id'] = user.id 
            flash('Connexion réussie!')
            return redirect(url_for('index'))
        else:
            flash(error)
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Vous avez été déconnecté.')
    return redirect(url_for('index'))

# --- Routes protégées ---
@app.route('/appareil_photo')
@login_required
def appareil_photo():
    appareil = AppareilPhoto.query.all()
    return render_template('appareil_photo.html', appareil=appareil)

@app.route('/telescope')
@login_required
def telescope():
    telescope_list = Telecope.query.all()
    return render_template('telescope.html', telescope=telescope_list)

@app.route('/photographies')
@login_required
def photographies():
    return render_template('photographies.html')

# --- Routes pour les détails 
@app.route('/appareil/<int:appareil_id>')
def appareil_detail(appareil_id):
    appareil = AppareilPhoto.query.get_or_404(appareil_id)
    return render_template('appareil_photo_detail.html', appareil=appareil)

@app.route('/telescope/<int:telescope_id>')
def telescope_detail(telescope_id):
    telescope = Telecope.query.get_or_404(telescope_id)
    return render_template('telescope_detail.html', telescope=telescope)

# --- Route d'accueil ---
@app.route('/')
def index():
    return render_template('index.html')

# --- Fonction pour créer les tables ---
@app.cli.command('create_db')
def create_db():
    db.create_all()
    print('Base de données créée!')

if __name__ == '__main__':
    app.run(debug=False)

@app.teardown_appcontext
def close_connection(exception):
    db.session.remove()