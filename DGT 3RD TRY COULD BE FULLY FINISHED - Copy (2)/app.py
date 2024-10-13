
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_migrate import Migrate

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong secret key or use environment variables

# Setup database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Liverpool2008!@localhost/dgtdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Setup Flask-Migrate
migrate = Migrate(app, db)

# User model
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True, nullable=False)
    password = db.Column(db.String(512), nullable=False)

    def check_password(self, password):
        return check_password_hash(self.password, password)

# User Team model
class UserTeam(db.Model):
    __tablename__ = 'UserTeam'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), nullable=False)
    player_name_1 = db.Column(db.String(255))
    player_name_2 = db.Column(db.String(255))
    player_name_3 = db.Column(db.String(255))
    player_name_4 = db.Column(db.String(255))
    player_name_5 = db.Column(db.String(255))
    player_name_6 = db.Column(db.String(255))
    player_name_7 = db.Column(db.String(255))
    total_price = db.Column(db.Numeric(5, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class UserFinalTeam(db.Model):
    __tablename__ = 'userfinalteam'  # Make sure the table name matches

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    player_name_1 = db.Column(db.String(255), nullable=False)
    player_name_2 = db.Column(db.String(255), nullable=False)
    player_name_3 = db.Column(db.String(255), nullable=False)
    player_name_4 = db.Column(db.String(255), nullable=False)
    player_name_5 = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'<UserFinalTeam {self.username}>'



class PlayerPoints(db.Model):
    __tablename__ = 'player_points'  # The name of your table

    id = db.Column(db.Integer, primary_key=True)
    player_name = db.Column(db.String(50), nullable=False, unique=True)
    points = db.Column(db.Integer, default=0)  # Default points to 0

    def __repr__(self):
        return f'<PlayerPoints {self.player_name}: {self.points}>'
    
class PlayerProfiles(db.Model):
    __tablename__ = 'player_profiles'  # Use the appropriate table name

    player_id = db.Column(db.Integer, primary_key=True)  # Primary key
    player_name = db.Column(db.String(50), nullable=False)  # Player name
    position = db.Column(db.String(15), nullable=False)  # Player position
    price = db.Column(db.Numeric(10, 1), nullable=True)  # Player price
    


# Load user callback
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

# Forms
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=40)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=40)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')

# Create database and tables
with app.app_context():
    db.create_all()

# Routes
@app.route('/')
def dashboard():
    return render_template('dashboard.html')  # Render the dashboard page

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = Users.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))  # Redirect to the index page
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # Check if username already exists
        if Users.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('register.html', form=form)


        # Create a new user
        hashed_password = generate_password_hash(password)
        new_user = Users(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route('/index')
@login_required  # Ensure the user is logged in to access this page
def index():
    # Query to get the top 5 players by goals
    top_scorers = db.session.execute(
        text('SELECT player_name, goals FROM playerstats ORDER BY goals DESC LIMIT 5')
    ).fetchall()

    # Query to get the top 5 players by assists
    top_assists = db.session.execute(
        text('SELECT player_name, assists FROM playerstats ORDER BY assists DESC LIMIT 5')
    ).fetchall()

    # Query to get the top 5 players by fantasy points
    top_fantasy_points = db.session.execute(
        text('SELECT player_name, fantasy_points FROM playerstats ORDER BY fantasy_points DESC LIMIT 5')
    ).fetchall()

    # Pass all three lists to the template
    return render_template('index.html', 
                           top_scorers=top_scorers, 
                           top_assists=top_assists, 
                           top_fantasy_points=top_fantasy_points)

@app.route('/transfers', methods=['GET', 'POST'])
@login_required
def transfers():
    # Check if the user has already selected their players
    if UserFinalTeam.query.filter_by(username=current_user.username).first():
        return redirect(url_for('already_selected'))

    if request.method == 'POST':
        selected_players = request.form.getlist('selected_players')
        total_cost = 0

        # Check if the user selected exactly 7 players
        if len(selected_players) != 7:
            flash('You must select exactly 7 players.', 'danger')
            return redirect(url_for('transfers'))

        existing_team = UserTeam.query.filter_by(username=current_user.username).first()

        # Store selected players in session
        selected_players_info = []

        for player in selected_players:
            player_name, price = player.split(':')  # Split player name and price
            
            # Fetch the player's position from playerprofiles table
            player_info = db.session.execute(
                text('SELECT position FROM playerprofiles WHERE player_name = :name'),
                {'name': player_name}
            ).fetchone()

            if player_info:
                position = player_info.position
                total_cost += float(price)
                selected_players_info.append({
                    'player_name': player_name,
                    'position': position,
                    'price': price
                })

                # Check for duplicates in the existing team
                if existing_team and player_name in [
                    existing_team.player_name_1,
                    existing_team.player_name_2,
                    existing_team.player_name_3,
                    existing_team.player_name_4,
                    existing_team.player_name_5,
                    existing_team.player_name_6,
                    existing_team.player_name_7
                ]:
                    flash(f'{player_name} is already in your team.', 'danger')
                    return redirect(url_for('transfers'))

                if not existing_team:
                    existing_team = UserTeam(username=current_user.username)

                # Add the player to the team
                for i in range(1, 8):
                    if getattr(existing_team, f'player_name_{i}') is None:
                        setattr(existing_team, f'player_name_{i}', player_name)
                        break
                else:
                    flash('You can only select 7 players.', 'danger')
                    return redirect(url_for('transfers'))

        if total_cost > 50:
            flash('Total cost cannot exceed 50 million.', 'danger')
            return redirect(url_for('transfers'))

        # If the existing team is updated, save it
        if existing_team:
            existing_team.total_price = total_cost
            db.session.add(existing_team)
            db.session.commit()
            flash('Players selected successfully!', 'success')

            # Store detailed player info in the session
            session['selected_players'] = selected_players_info
            return redirect(url_for('pick_team'))  # Redirect to pick_team

    # Fetch available players categorized
    forwards = db.session.execute(text('SELECT player_name, price FROM playerprofiles WHERE position = "Forward"')).fetchall()
    midfielders = db.session.execute(text('SELECT player_name, price FROM playerprofiles WHERE position = "Midfield"')).fetchall()
    defenders = db.session.execute(text('SELECT player_name, price FROM playerprofiles WHERE position IN ("Defender", "Goalkeeper")')).fetchall()

    return render_template('transfers.html', forwards=forwards, midfielders=midfielders, defenders=defenders)


@app.route('/pick_team', methods=['GET', 'POST'])
@login_required
def pick_team():
    existing_team = UserTeam.query.filter_by(username=current_user.username).first()

    if not existing_team:
        flash('You must go to the Transfers page first to select players.', 'danger')
        return redirect(url_for('transfers'))

    selected_players = session.get('selected_players', [])
    
    if request.method == 'POST':
        final_players = request.form.getlist('final_players')

        if len(final_players) != 5:
            flash('You must select exactly 5 players to start your team, including at least 2 defenders, 1 forward, and 1 midfielder.', 'danger')
            return redirect(url_for('pick_team'))

        if UserFinalTeam.query.filter_by(username=current_user.username).first():
            flash('You have already submitted a team. You cannot submit another one.', 'danger')
            return redirect(url_for('points'))

        total_price = 0
        player_names = []
        
        for player in final_players:
            player_name, position, price = player.split(':')
            total_price += float(price)
            player_names.append(player_name)
            
    
        final_team = UserFinalTeam(
            username=current_user.username,
            player_name_1=player_names[0],
            player_name_2=player_names[1],
            player_name_3=player_names[2],
            player_name_4=player_names[3],
            player_name_5=player_names[4]
        )

        db.session.add(final_team)
        db.session.commit()

        session.pop('selected_players', None)

        return redirect(url_for('points'))

    return render_template('pick_team.html', selected_players=selected_players)



@app.route('/submit_final_team', methods=['POST'])
@login_required
def submit_final_team():
    selected_players = request.form.getlist('final_players')  # Assuming this gets the 5 selected players

    if len(selected_players) == 5:
        # Create a new UserFinalTeam instance
        final_team = UserFinalTeam(
            username=current_user.username,
            player_name_1=selected_players[0],
            player_name_2=selected_players[1],
            player_name_3=selected_players[2],
            player_name_4=selected_players[3],
            player_name_5=selected_players[4]
        )
        
        # Add the new team to the database
        db.session.add(final_team)
        db.session.commit()

        flash('Your team has been submitted successfully!', 'success')
        return redirect(url_for('points'))
    else:
        flash('You must select exactly 5 players.', 'danger')
        return redirect(url_for('pick_team'))

@app.route('/points')
@login_required
def points():
    # Fetch the user's selected team
    user_team = UserFinalTeam.query.filter_by(username=current_user.username).first()

    if not user_team:
        return redirect(url_for('pick_team'))

    # Prepare a list to fetch points
    players_with_details = []
    
    # Store the player names in a list
    player_names = [
        user_team.player_name_1,
        user_team.player_name_2,
        user_team.player_name_3,
        user_team.player_name_4,
        user_team.player_name_5
    ]
    
    # Fetch points for each player
    for player_name in player_names:
        # Fetch points from playerpoints
        points_record = PlayerPoints.query.filter_by(player_name=player_name).first()
        player_points = points_record.points if points_record else 0
        
        # Append player name and points to the list
        players_with_details.append((player_name, player_points))

    return render_template('points.html', players=players_with_details)









@app.route('/already_selected')
@login_required
def already_selected():
    return render_template('already_selected.html')

@app.route('/more')
@login_required
def more():
    return render_template('more.html')


@app.route('/stats')
@login_required
def stats():
    sort_column = request.args.get('sort', 'goals')  # Default sort column
    allowed_columns = ['player_name', 'goals', 'assists', 'yellow_cards', 'red_cards', 'own_goals', 'bonus_points', 'fantasy_points']
    
    if sort_column not in allowed_columns:
        sort_column = 'goals'  # Fallback to default if invalid column

    # Query to fetch player statistics, sorted by the specified column
    player_data = db.session.execute(
        text(f'SELECT player_name, goals, assists, yellow_cards, red_cards, own_goals, bonus_points, fantasy_points '
             f'FROM playerstats ORDER BY {sort_column} DESC')
    ).fetchall()
    
    return render_template('stats.html', player_data=player_data)

@app.route('/get_player_profile/<player_name>', methods=['GET'])
def get_player_profile(player_name):
    player = db.session.execute(
        text('SELECT position, price, fantasy_points, form FROM playerprofiles WHERE player_name = :name'),
        {'name': player_name}
    ).fetchone()

    if player:
        return jsonify({
            'player_name': player_name,
            'position': player.position,
            'price': player.price,
            'fantasy_points': player.fantasy_points,
            'form': player.form
        })
    return jsonify({'error': 'Player not found.'}), 404
        


@app.route('/success')
@login_required
def success_page():
    return render_template('success.html')
@app.route('/article1')
@login_required
def article1():
    return render_template('article1.html')  # Render article1 page

@app.route('/article2')
@login_required
def article2():
    return render_template('article2.html')  # Render article2 page

@app.route('/article3')
@login_required
def article3():
    return render_template('article3.html')  # Render article3 page

@app.route('/logout')
def logout():
    # Clear the user session
    session.pop('user_id', None)  # Adjust this based on how you store user sessions
    return redirect(url_for('dashboard'))  # Redirect to the dashboard page

if __name__ == '__main__':
    app.run(debug=True)
