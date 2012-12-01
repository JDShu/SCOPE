"""
Settings for minimum reputation required for 
a variety of actions on the askbot askbot
"""
from askbot.conf.settings_wrapper import settings
from askbot.conf.super_groups import REP_AND_BADGES
from askbot.deps import livesettings
from django.utils.translation import ugettext as _

MIN_REP = livesettings.ConfigurationGroup(
    'MIN_REP', 
    _('Karma thresholds'),
    ordering=0,
    super_group = REP_AND_BADGES
)

settings.register(
    livesettings.IntegerValue(
        MIN_REP,
        'MIN_REP_TO_VOTE_UP',
        default=5,
        description=_('Upvote')
    )
)

settings.register(
    livesettings.IntegerValue(
        MIN_REP,
        'MIN_REP_TO_VOTE_DOWN',
        default=50,
        description=_('Downvote')
    )
)

settings.register(
    livesettings.IntegerValue(
        MIN_REP,
        'MIN_REP_TO_PROBLEM_OWN_EXERCISE',
        default=5,
        description=_('Problem own exercise immediately')
    )
)

settings.register(
    livesettings.IntegerValue(
        MIN_REP,
        'MIN_REP_TO_ACCEPT_OWN_PROBLEM',
        default=20,
        description=_('Accept own problem')
    )
)

settings.register(
    livesettings.IntegerValue(
        MIN_REP,
        'MIN_REP_TO_ACCEPT_ANY_PROBLEM',
        default=500,
        description=_('Accept any problem')
    )
)

settings.register(
    livesettings.IntegerValue(
        MIN_REP,
        'MIN_REP_TO_FLAG_OFFENSIVE',
        default=5,
        description=_('Flag offensive')
    )
)

settings.register(
    livesettings.IntegerValue(
        MIN_REP,
        'MIN_REP_TO_LEAVE_COMMENTS',
        default=10,
        description=_('Leave comments')
    )
)

settings.register(
    livesettings.IntegerValue(
        MIN_REP,
        'MIN_REP_TO_DELETE_OTHERS_COMMENTS',
        default=200,
        description=_('Delete comments posted by others')
    )
)

settings.register(
    livesettings.IntegerValue(
        MIN_REP,
        'MIN_REP_TO_DELETE_OTHERS_POSTS',
        default=500,
        description=_('Delete exercises and problems posted by others')
    )
)

settings.register(
    livesettings.IntegerValue(
        MIN_REP,
        'MIN_REP_TO_UPLOAD_FILES',
        default=10,
        description=_('Upload files')
    )
)

settings.register(
    livesettings.IntegerValue(
        MIN_REP,
        'MIN_REP_TO_CLOSE_OWN_EXERCISES',
        default=25,
        description=_('Close own exercises'),
    )
)

settings.register(
    livesettings.IntegerValue(
        MIN_REP,
        'MIN_REP_TO_RETAG_OTHERS_EXERCISES',
        default=50,
        description=_('Retag exercises posted by other people')
    )
)

settings.register(
    livesettings.IntegerValue(
        MIN_REP,
        'MIN_REP_TO_REOPEN_OWN_EXERCISES',
        default=50,
        description=_('Reopen own exercises')
    )
)

settings.register(
            livesettings.IntegerValue(
        MIN_REP,
        'MIN_REP_TO_EDIT_WIKI',
        default=75,
        description=_('Edit community wiki posts')
    )
)

settings.register(
    livesettings.IntegerValue(
        MIN_REP,
        'MIN_REP_TO_EDIT_OTHERS_POSTS',
        default=200,
        description=_('Edit posts authored by other people')
    )
)

settings.register(
    livesettings.IntegerValue(
        MIN_REP,
        'MIN_REP_TO_VIEW_OFFENSIVE_FLAGS',
        default=200,
        description=_('View offensive flags')
    )
)

settings.register(
    livesettings.IntegerValue(
        MIN_REP,
        'MIN_REP_TO_CLOSE_OTHERS_EXERCISES',
        default=200,
        description=_('Close exercises asked by others')
    )
)

settings.register(
    livesettings.IntegerValue(
        MIN_REP,
        'MIN_REP_TO_LOCK_POSTS',
        default=400,
        description=_('Lock posts')
    )
)

settings.register(
    livesettings.IntegerValue(
        MIN_REP,
        'MIN_REP_TO_HAVE_STRONG_URL',
        default=25,
        description=_('Remove rel=nofollow from own homepage'),
        help_text=_(
                    'When a search engine crawler will see a rel=nofollow '
                    'attribute on a link - the link will not count towards '
                    'the rank of the users personal site.'
                   )
    )
)

settings.register(
    livesettings.IntegerValue(
        MIN_REP,
        'MIN_REP_TO_POST_BY_EMAIL',
        default=100,
        description=_('Post problems and comments by email')
    )
)

settings.register(
    livesettings.IntegerValue(
        MIN_REP,
        'MIN_REP_TO_TRIGGER_EMAIL',
        default=15,
        description=_('Trigger email notifications'),
        help_text=_(
            'Reduces spam as notifications wont\'t be sent '
            'to regular users for posts of low karma users'
        )
    )
)
