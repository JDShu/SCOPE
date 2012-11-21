'''
This file must hold keys for translatable messages
that are used as variables
it is important that a dummy _() function is used here
this way message key will be pulled into django.po
and can still be used as a variable in python files.

In addition, some messages are repeated too many times
in the code, so we need to be able to retreive them
by a key. Therefore we have a function here, called
get_i18n_message(). Possibly all messages included in 
this file could be implemented this way.
'''
_ = lambda v:v

#NOTE: all strings must be explicitly put into this dictionary,
#because you don't want to import _ from here with import *
__all__ = []

#messages loaded in the templates via direct _ calls
_('most relevant exercises')
_('click to see most relevant exercises')
_('by relevance')
_('click to see the oldest exercises')
_('by date')
_('click to see the newest exercises')
_('click to see the least recently updated exercises')
_('by activity')
_('click to see the most recently updated exercises')
_('click to see the least problemed exercises')
_('by problems')
_('click to see the most problemed exercises')
_('click to see least voted exercises')
_('by votes')
_('click to see most voted exercises')
_('interesting')
_('ignored')
_('subscribed')
TAGS_ARE_REQUIRED_MESSAGE = _('tags are required')
TAG_WRONG_CHARS_MESSAGE = _(
    'please use letters, numbers and characters "-+.#"'
)

def get_i18n_message(key):
    messages = {
        'BLOCKED_USERS_CANNOT_POST': _(
            'Sorry, your account appears to be blocked and you cannot make new posts '
            'until this issue is resolved. Please contact the forum administrator to '
            'reach a resolution.'
        ),
        'SUSPENDED_USERS_CANNOT_POST': _(
            'Sorry, your account appears to be suspended and you cannot make new posts '
            'until this issue is resolved. You can, however edit your existing posts. '
            'Please contact the forum administrator to reach a resolution.'
        )
    }
    if key in messages:
        return messages.get(key)
    else:
        raise KeyError(key)
