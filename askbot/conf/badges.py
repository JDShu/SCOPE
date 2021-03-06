"""
Settings for reputation changes that apply to 
user in response to various actions by the same
users or others
"""
from askbot.conf.settings_wrapper import settings
from askbot.conf.super_groups import REP_AND_BADGES
from askbot.deps.livesettings import ConfigurationGroup, IntegerValue
from django.utils.translation import ugettext as _

BADGES = ConfigurationGroup(
                    'BADGES',
                    _('Badge settings'),
                    ordering=2,
                    super_group = REP_AND_BADGES
                )

settings.register(
    IntegerValue(
        BADGES,
        'DISCIPLINED_BADGE_MIN_UPVOTES',
        default=3,
        description=_('Disciplined: minimum upvotes for deleted post')
    )
)

settings.register(
    IntegerValue(
        BADGES,
        'PEER_PRESSURE_BADGE_MIN_DOWNVOTES',
        default=3,
        description=_('Peer Pressure: minimum downvotes for deleted post')
    )
)

settings.register(
    IntegerValue(
        BADGES,
        'TEACHER_BADGE_MIN_UPVOTES',
        default=1,
        description=_('Teacher: minimum upvotes for the problem')
    )
)

settings.register(
    IntegerValue(
        BADGES,
        'NICE_PROBLEM_BADGE_MIN_UPVOTES',
        default=2,
        description=_('Nice Problem: minimum upvotes for the problem')
    )
)

settings.register(
    IntegerValue(
        BADGES,
        'GOOD_PROBLEM_BADGE_MIN_UPVOTES',
        default=3,
        description=_('Good Problem: minimum upvotes for the problem')
    )
)

settings.register(
    IntegerValue(
        BADGES,
        'GREAT_PROBLEM_BADGE_MIN_UPVOTES',
        default=5,
        description=_('Great Problem: minimum upvotes for the problem')
    )
)

settings.register(
    IntegerValue(
        BADGES,
        'NICE_EXERCISE_BADGE_MIN_UPVOTES',
        default=2,
        description=_('Nice Exercise: minimum upvotes for the exercise')
    )
)

settings.register(
    IntegerValue(
        BADGES,
        'GOOD_EXERCISE_BADGE_MIN_UPVOTES',
        default=3,
        description=_('Good Exercise: minimum upvotes for the exercise')
    )
)

settings.register(
    IntegerValue(
        BADGES,
        'GREAT_EXERCISE_BADGE_MIN_UPVOTES',
        default=5,
        description=_('Great Exercise: minimum upvotes for the exercise')
    )
)

settings.register(
    IntegerValue(
        BADGES,
        'POPULAR_EXERCISE_BADGE_MIN_VIEWS',
        default=15,
        description=_('Popular Exercise: minimum views')
    )
)

settings.register(
    IntegerValue(
        BADGES,
        'NOTABLE_EXERCISE_BADGE_MIN_VIEWS',
        default=25,
        description=_('Notable Exercise: minimum views')
    )
)

settings.register(
    IntegerValue(
        BADGES,
        'FAMOUS_EXERCISE_BADGE_MIN_VIEWS',
        default=50,
        description=_('Famous Exercise: minimum views')
    )
)

settings.register(
    IntegerValue(
        BADGES,
        'SELF_LEARNER_BADGE_MIN_UPVOTES',
        default=1,
        description=_('Self-Learner: minimum problem upvotes')
    )
)

settings.register(
    IntegerValue(
        BADGES,
        'CIVIC_DUTY_BADGE_MIN_VOTES',
        default=100,
        description=_('Civic Duty: minimum votes')
    )
)

settings.register(
    IntegerValue(
        BADGES,
        'ENLIGHTENED_BADGE_MIN_UPVOTES',
        default=3,
        description=_('Enlightened Duty: minimum upvotes')
    )
)

settings.register(
    IntegerValue(
        BADGES,
        'GURU_BADGE_MIN_UPVOTES',
        default=5,
        description=_('Guru: minimum upvotes')
    )
)

settings.register(
    IntegerValue(
        BADGES,
        'NECROMANCER_BADGE_MIN_UPVOTES',
        default=1,
        description=_('Necromancer: minimum upvotes')
    )
)

settings.register(
    IntegerValue(
        BADGES,
        'NECROMANCER_BADGE_MIN_DELAY',
        default=30,
        description=_('Necromancer: minimum delay in days')
    )
)

settings.register(
    IntegerValue(
        BADGES,
        'ASSOCIATE_EDITOR_BADGE_MIN_EDITS',
        default=20,
        description=_('Associate Editor: minimum number of edits')
    )
)

settings.register(
    IntegerValue(
        BADGES,
        'FAVORITE_EXERCISE_BADGE_MIN_STARS',
        default=3,
        description=_('Favorite Exercise: minimum stars')
    )
)

settings.register(
    IntegerValue(
        BADGES,
        'STELLAR_EXERCISE_BADGE_MIN_STARS',
        default=5,
        description=_('Stellar Exercise: minimum stars')
    )
)

settings.register(
    IntegerValue(
        BADGES,
        'COMMENTATOR_BADGE_MIN_COMMENTS',
        default=10,
        description=_('Commentator: minimum comments')
    )
)

settings.register(
    IntegerValue(
        BADGES,
        'TAXONOMIST_BADGE_MIN_USE_COUNT',
        default = 5,
        description = _('Taxonomist: minimum tag use count')
    )
)

settings.register(
    IntegerValue(
        BADGES,
        'ENTHUSIAST_BADGE_MIN_DAYS',
        default = 5,
        description = _('Enthusiast: minimum days')
    )
)
