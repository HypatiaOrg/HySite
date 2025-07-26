response.title = settings.title
response.subtitle = settings.subtitle
response.meta.author = '%(author)s <%(author_email)s>' % settings
response.meta.keywords = settings.keywords
response.meta.description = settings.description
response.google_analytics_id = "UA-104322230-1"
response.logo = A("Hypatia Catalog",
                  _class="navbar-brand", _href="/hypatia", _style="font-size:30px;",
                  _id="hypatia-logo")
response.menu = [
(T('Scatter'),request.url=='/hypatia/default/launch','/hypatia/default/launch',[]),
(T('Target Lists'),request.url=='/hypatia/default/targets','/hypatia/default/targets',[]),
(T('Density Map'),request.url=='/hypatia/default/density','/hypatia/default/density',[]),
(T('Histogram'),request.url=='/hypatia/default/hist','/hypatia/default/hist',[]),
]