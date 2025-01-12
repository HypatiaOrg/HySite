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
(T('Elements & Properties'),request.url=='/hypatia/default/launch' and request.vars.mode==None,'/hypatia/default/launch',[]),
(T('Stars With/Without Planets'),request.url=='/hypatia/default/launch' and request.vars.mode=='hist','/hypatia/default/launch?mode=hist',[]),
]