import os

import flask
from flask.ext import principal, blogging, bootstrap, script, sqlalchemy
from flask.ext.login import LoginManager, login_user, logout_user, UserMixin
from flask.ext.oauthlib import client as oauth_client


app = flask.Flask(__name__)

app.config["BLOGGING_URL_PREFIX"] = "/blog"
app.config["BLOGGING_DISQUS_SITENAME"] = "ditrobotics"
app.config["BLOGGING_SITEURL"] = "http://www.ditrobotics.tw"
app.config["BLOGGING_PERMISSIONS"] = True


if os.environ.get('DEBUG') == 'DEBUG':
    print('DEBUG')
    BloggingCompatibleSQLAlchemy = sqlalchemy.SQLAlchemy
    app.config['SECRET_KEY'] = 'sk'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
else:
    class BloggingCompatibleSQLAlchemy(sqlalchemy.SQLAlchemy):

        def apply_driver_hacks(self, app, info, options):
            options.setdefault('isolation_level', 'AUTOCOMMIT')
            return super().apply_driver_hacks(app, info, options)

    app.config['SECRET_KEY'] = os.environ['OPENSHIFT_SECRET_TOKEN']
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://{host}:{port}/{dbname}'.format(
            host=os.environ['OPENSHIFT_POSTGRESQL_DB_HOST'],
            port=os.environ['OPENSHIFT_POSTGRESQL_DB_PORT'],
            dbname='ditrobotics'
        )

FACEBOOK_APP_ID = int(os.environ['FACEBOOK_APP_ID'])
FACEBOOK_APP_SECRET = os.environ['FACEBOOK_APP_SECRET']


bootstrap.Bootstrap(app)
principals = principal.Principal(app)
manager = script.Manager(app)
db = BloggingCompatibleSQLAlchemy(app)
login_manager = LoginManager(app)
sql_storage = blogging.SQLAStorage(db=db)
blogging_engine = blogging.BloggingEngine(app, sql_storage)
oauth = oauth_client.OAuth()


STAFF_IDS = [
    '887556254623283',
    '943484319004930',
    '100002586754591',
    '858850527521645',
]
assert all(isinstance(staff_id, str) for staff_id in STAFF_IDS)


# Auth


facebook = oauth.remote_app(
    'facebook',
    base_url='https://graph.facebook.com/',
    request_token_url=None,
    access_token_url='/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    consumer_key=FACEBOOK_APP_ID,
    consumer_secret=FACEBOOK_APP_SECRET,
    request_token_params={'scope': 'email'}
)


class FakeUser(UserMixin):
    def __init__(self, id):
        self.id = id

    def get_name(self):
        return 'DIT Robotics Staff #{}'.format(self.id)


@login_manager.user_loader
@blogging_engine.user_loader
def load_user(id):
    return FakeUser(id)


@app.route('/login')
def login():
    return facebook.authorize(
        callback=flask.url_for('authorized', _external=True)
    )


@app.route('/authorized')
def authorized():
    resp = facebook.authorized_response()
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            flask.request.args['error_reason'],
            flask.request.args['error_description']
        )
    if isinstance(resp, oauth_client.OAuthException):
        return 'Access denied: %s' % resp.message

    flask.session['facebook_token'] = (resp['access_token'], '')
    me = facebook.get('/me')
    flask.session['username'] = me.data['name']
    flask.session['facebook_id'] = me.data['id']

    login_user(FakeUser(flask.session['facebook_id']))
    principal.identity_changed.send(flask.current_app._get_current_object(), identity=principal.Identity(flask.session['facebook_id']))

    return flask.redirect(flask.url_for('index'))


@app.route('/logout')
def logout():
    flask.session.pop('facebook_token', None)
    flask.session.pop('facebook_id', None)
    flask.session.pop('username', None)
    flask.session.pop('identity.name', None)
    flask.session.pop('identity.auth_type', None)
    logout_user()
    principal.identity_changed.send(flask.current_app._get_current_object(), identity=principal.AnonymousIdentity())
    return flask.redirect(flask.url_for('index'))


@principal.identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    if flask.session.get('facebook_id') in STAFF_IDS:
        identity.provides.add(principal.RoleNeed('blogger'))


@app.route('/profile')
def profile():
    if any(key not in flask.session for key in ['facebook_token', 'username', 'facebook_id']):
        flask.abort(403)
    return flask.render_template('profile.html')


@facebook.tokengetter
def get_facebook_oauth_token():
    return flask.session.get('facebook_token')


# static

@app.route('/')
def index():
    return flask.render_template('index.html')


@app.route('/contests/')
def contests():
    return flask.render_template('contests.html')


if __name__ == '__main__':
    app.run(debug=True)
