# -*- coding: utf-8 -*-
# web2py URL rewriting for HySite: everything goes to the 'hypatia' application.
# Only the hypatia app is in the image (see .dockerignore), so there are no routes to web2py's
# admin, appadmin, examples or welcome apps.

default_application = 'hypatia'
default_controller = 'default'
default_function = 'index'

routes_in = (
    ('/api', '/hypatia/api'),
    ('/$app/static/$anything', '/$app/static/$anything'),
    ('/$anything', '/$anything'),
)

routes_out = (
    ('/$app/static/$anything', '/$app/static/$anything'),
    ('/$anything', '/$anything'),
)
