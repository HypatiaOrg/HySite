from gluon.storage import Storage
settings = Storage()

settings.migrate = True
settings.title = 'Hypatia Catalog Database Website'
settings.subtitle = 'Project Superstar'
settings.author = 'Natalie Hinkel'
settings.author_email = 'chw3k5@gmail.com'
settings.keywords = 'stellar abundance'
settings.description = 'The Hypatia Catalog Database features an interactive table and multiple plotting interfaces that allow easy access and exploration of data within the Hypatia Catalog, a multidimensional, amalgamate dataset comprised of stellar abundance measurements for FGKM-type stars within 500 pc of the Sun from carefully selected literature sources that measured both [Fe/H] and at least one other element.'
settings.layout_theme = 'Default'
settings.database_uri = 'sqlite://storage.sqlite'
settings.security_key = 'db2c6c84-301e-4205-b07c-2940d6e798ae'
settings.email_server = 'localhost'
settings.email_sender = 'you@example.com'
settings.email_login = ''
settings.login_method = 'local'
settings.login_config = ''
settings.plugins = []
