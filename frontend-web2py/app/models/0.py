from gluon.storage import Storage
settings = Storage()

settings.title = 'Hypatia Catalog'
settings.subtitle = 'Project Superstar'
settings.author = 'Natalie Hinkel'
settings.author_email = 'chw3k5@gmail.com'
settings.keywords = 'stellar abundance'
settings.description = 'The Hypatia Catalog features an interactive table and multiple plotting interfaces that allow easy access and exploration of data within the Hypatia Catalog, a multidimensional, amalgamate dataset comprised of stellar abundance measurements for FGKM-type stars within 500 pc of the Sun from carefully selected literature sources that measured both [Fe/H] and at least one other element.'

# behind the HTTPS edge (HyRoute), the session cookie is only ever sent over HTTPS
if request.env.http_x_forwarded_proto == 'https':
    session.secure()
