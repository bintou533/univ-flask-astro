from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt

# Initialisation des extensions
app = Flask(__name__)
app.config['SECRET_KEY'] = 'bintou'  
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # Base de données SQLite
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialiser l'extension SQLAlchemy et Bcrypt
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Initialiser l'extension Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Nom de la route de la page de login


# Fonction de chargement de l'utilisateur
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Route pour la page d'accueil
@app.route('/')
@login_required
def home():
    return render_template('index.html', title="Accueil")

# Route pour la page d'inscription
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        
        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        return redirect(url_for('home'))
    
    return render_template('register.html', title='Inscription')

# Route pour la page de connexion

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')  
            return redirect(next_page or url_for('home'))  
    
    return render_template('login.html', title='Connexion')


# Route pour la déconnexion
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/appareil-photo')
@login_required
def appareil_photo():
    return render_template('appareil_photo.html', appareils=photos)

@app.route('/telescope')
@login_required
def telescope():
    return render_template('telescope.html', teles=teles)

@app.route('/photographies')
@login_required
def photographies():
    return render_template('photographies.html', photos=photographies)

if __name__ == '__main__':
    app.run(debug=True)
