# -*- coding: utf-8 -*-
from gluon.tools import Auth


db = DAL('sqlite://storage.sqlite', pool_size=1, check_reserved=['all'])

## by default give a view/generic.extension to all actions from localhost
## none otherwise. a pattern can be 'controller/function.extension'
response.generic_patterns = ['*'] if request.is_local else []

auth = Auth(db)
