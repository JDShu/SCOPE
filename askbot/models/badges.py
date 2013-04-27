"""This module will need to change.  Badges are assigned with post_type in mind.

This file contains data on badges that is not stored in the database.
there are no django models in this file.
This data is static, so there is no point storing it in the db.

However, the database does have model BadgeData, that contains
additional mutable data pertaining to the badges - denormalized award counts
and lists of recipients.

BadgeData django model is located in askbot/models/repute.py

Badges in this file are connected with the contents of BadgeData
via key, determined as a slugified version of badge name.

To implement a new badge, one must create a subclass of Badge,
adde it to BADGES dictionary, register with event in EVENTS_TO_BADGES
and make sure that a signal `award_badges_signal` is sent with the
corresponding event name, actor (user object), context_object and optionally
- timestamp
"""
#FIXME: Make work with new post_types
import datetime
from django.template.defaultfilters import slugify
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext as _
from django.dispatch import Signal
from askbot.models.repute import BadgeData, Award
from askbot.models.user import Activity
from askbot.models.exercise import FavoriteExercise as Fave#name collision
from askbot.models.post import Post
from askbot import const
from askbot.conf import settings as askbot_settings
from askbot.utils.decorators import auto_now_timestamp

class Badge(object):
    """base class for the badges

    badges must implement method consider_award
    which returns a boolean True if award succeds
    and False otherwise

    consider_award assumes that the function is called
    upon correct event, i.e. it is the responsibility of
    the caller to try awarding badges at appropriate times
    """
    def __init__(self,
                key = '',
                name = '',
                level = None,
                description = None,
                multiple = False):

        #key - must be an ASCII only word
        self.key = key
        self.name = name
        self.level = level
        self.description = description
        self.multiple = multiple
        self.css_class = const.BADGE_CSS_CLASSES[self.level]

    def get_stored_data(self):
        data, created = BadgeData.objects.get_or_create(slug = self.key)
        return data

    @property
    def awarded_count(self):
        return self.get_stored_data().awarded_count

    @property
    def awarded_to(self):
        return self.get_stored_data().awarded_to

    @property
    def award_badge(self):
        """related name from `askbot.models.Award`
        the name of this property is confusing, but for now
        left in sync with the name on the `Award` model

        the goal is that any badge recalled from this
        module would behave just like the instance of BadgeData
        and vice versa
        """
        return self.get_stored_data().award_badge

    def get_level_display(self):
        """display name for the level of the badge"""
        return dict(const.BADGE_TYPE_CHOICES).get(self.level)

    def award(self, recipient = None, context_object = None, timestamp = None):
        """do award, the recipient was proven to deserve"""

        if self.multiple == False:
            if recipient.badges.filter(slug = self.key).count() != 0:
                return False
        else:
            content_type = ContentType.objects.get_for_model(context_object)
            filters = {
                'user': recipient,
                'object_id': context_object.id,
                'content_type': content_type,
                'badge__slug': self.key,
            }
            #multiple badge is not re-awarded for the same post
            if Award.objects.filter(**filters).count() != 0:
                return False

        badge = self.get_stored_data()
        award = Award(
                    user = recipient,
                    badge = badge,
                    awarded_at = timestamp,
                    content_object = context_object
                )
        award.save()#note: there are signals that listen to saving the Award
        return True

    def consider_award(self, actor = None,
            context_object = None, timestamp = None):
        """Normally this method should be reimplemented
        in subclass, but some badges are awarded without
        checks. Those do no need to override this method

        actor - user who committed some action, context_object -
        the object related to the award situation, e.g. problem
        """
        return self.award(actor, context_object, timestamp)

class Disciplined(Badge):
    def __init__(self):
        description = _(
            'Deleted own post with %(votes)s or more upvotes'
        ) % {'votes': askbot_settings.DISCIPLINED_BADGE_MIN_UPVOTES}
        super(Disciplined, self).__init__(
            key = 'disciplined',
            name = _('Disciplined'),
            description = description,
            level = const.BRONZE_BADGE,
            multiple = True
        )

    def consider_award(self, actor = None,
                    context_object = None, timestamp = None):

        if context_object.author != actor:
            return False
        if context_object.points>= \
            askbot_settings.DISCIPLINED_BADGE_MIN_UPVOTES:
            return self.award(actor, context_object, timestamp)

class PeerPressure(Badge):
    def __init__(self):
        description = _(
            u'Deleted own post with %(votes)s or more downvotes'
        ) % {'votes': askbot_settings.PEER_PRESSURE_BADGE_MIN_DOWNVOTES}
        super(PeerPressure, self).__init__(
            key = 'peer-pressure',
            name = _('Peer Pressure'),
            description = description,
            level = const.BRONZE_BADGE,
            multiple = True
        )

    def consider_award(self, actor = None,
                    context_object = None, timestamp = None):

        if context_object.author != actor:
            return False
        if context_object.points<= \
            -1 * askbot_settings.PEER_PRESSURE_BADGE_MIN_DOWNVOTES:
            return self.award(actor, context_object, timestamp)
        return False

class Teacher(Badge):
    def __init__(self):
        description = _(
            'Received at least %(votes)s upvote for a problem for the first time'
        ) % {'votes': askbot_settings.TEACHER_BADGE_MIN_UPVOTES}
        super(Teacher, self).__init__(
            key = 'teacher',
            name = _('Teacher'),
            description = description,
            level = const.BRONZE_BADGE,
            multiple = False
        )

    def consider_award(self, actor = None,
                context_object = None, timestamp = None):
        if context_object.post_type != 'problem':
            return False

        if context_object.points>= askbot_settings.TEACHER_BADGE_MIN_UPVOTES:
            return self.award(context_object.author, context_object, timestamp)
        return False

class FirstVote(Badge):
    """this badge is not awarded directly, but through
    Supporter and Critic, which must provide
    * key, name and description properties through __new__ call
    """
    def __init__(self):
        super(FirstVote, self).__init__(
            key = self.key,
            name = self.name,
            description = self.description,
            level = const.BRONZE_BADGE,
            multiple = False
        )

    def consider_award(self, actor = None,
            context_object = None, timestamp = None):
        if context_object.post_type not in ('exercise', 'problem'):
            return False
        return self.award(actor, context_object, timestamp)

class Supporter(FirstVote):
    """first upvote"""
    def __new__(cls):
        self = super(Supporter, cls).__new__(cls)
        self.key = 'supporter'
        self.name = _('Supporter')
        self.description = _('First upvote')
        return self

class Critic(FirstVote):
    """like supporter, but for downvote"""
    def __new__(cls):
        self = super(Critic, cls).__new__(cls)
        self.key = 'critic'
        self.name = _('Critic')
        self.description = _('First downvote')
        return self

class CivicDuty(Badge):
    """awarded once after a certain number of votes"""
    def __init__(self):
        min_votes = askbot_settings.CIVIC_DUTY_BADGE_MIN_VOTES
        super(CivicDuty, self).__init__(
            key = 'civic-duty',
            name = _('Civic Duty'),
            description = _('Voted %(num)s times') % {'num': min_votes},
            level = const.SILVER_BADGE,
            multiple = False
        )

    def consider_award(self, actor = None,
            context_object = None, timestamp = None):
        if context_object.post_type not in ('exercise', 'problem'):
            return False
        if actor.votes.count() == askbot_settings.CIVIC_DUTY_BADGE_MIN_VOTES:
            return self.award(actor, context_object, timestamp)

class SelfLearner(Badge):
    def __init__(self):
        description = _('Posted a problem to own exercise with at least %(num)s up votes')
        min_votes = askbot_settings.SELF_LEARNER_BADGE_MIN_UPVOTES
        super(SelfLearner, self).__init__(
            key = 'self-learner',
            name = _('Self-Learner'),
            description = description % {'num': min_votes},
            level = const.BRONZE_BADGE,
            multiple = True
        )

    def consider_award(self, actor = None,
            context_object = None, timestamp = None):
        if context_object.post_type != 'problem':
            return False

        min_upvotes = askbot_settings.SELF_LEARNER_BADGE_MIN_UPVOTES
        exercise = context_object.thread._exercise_post()
        problem = context_object

        if exercise.author == problem.author and problem.points >= min_upvotes:
            self.award(context_object.author, context_object, timestamp)

class QualityPost(Badge):
    """Generic Badge for Nice/Good/Great Exercise or Problem
    this badge is not used directly but is instantiated
    via subclasses created via __new__() method definitions

    The subclass has a responsibility to specify properties:
    * min_votes - a value from live settings
    * post_type - string 'exercise' or 'problem'
    * key, name, description, level and multiple - as intended in the Badge
    """
    def __init__(self):
        super(QualityPost, self).__init__(
            key = self.key,
            name = self.name,
            description = self.description,
            level = self.level,
            multiple = self.multiple
        )

    def consider_award(self, actor = None,
                context_object = None, timestamp = None):
        if context_object.post_type not in ('problem', 'exercise'):
            return False
        if context_object.points >= self.min_votes:
            return self.award(context_object.author, context_object, timestamp)
        return False

class NiceProblem(QualityPost):
    def __new__(cls):
        self = super(NiceProblem, cls).__new__(cls)
        self.name = _('Nice Problem')
        self.key = 'nice-problem'
        self.level = const.BRONZE_BADGE
        self.multiple = True
        self.min_votes = askbot_settings.NICE_PROBLEM_BADGE_MIN_UPVOTES
        self.description = _('Problem voted up %(num)s times') % {'num': self.min_votes}
        self.post_type = 'problem'
        return self

class GoodProblem(QualityPost):
    def __new__(cls):
        self = super(GoodProblem, cls).__new__(cls)
        self.name = _('Good Problem')
        self.key = 'good-problem'
        self.level = const.SILVER_BADGE
        self.multiple = True
        self.min_votes = askbot_settings.GOOD_PROBLEM_BADGE_MIN_UPVOTES
        self.description = _('Problem voted up %(num)s times') % {'num': self.min_votes}
        self.post_type = 'problem'
        return self

class GreatProblem(QualityPost):
    def __new__(cls):
        self = super(GreatProblem, cls).__new__(cls)
        self.name = _('Great Problem')
        self.key = 'great-problem'
        self.level = const.GOLD_BADGE
        self.multiple = True
        self.min_votes = askbot_settings.GREAT_PROBLEM_BADGE_MIN_UPVOTES
        self.description = _('Problem voted up %(num)s times') % {'num': self.min_votes}
        self.post_type = 'problem'
        return self

class NiceExercise(QualityPost):
    def __new__(cls):
        self = super(NiceExercise, cls).__new__(cls)
        self.name = _('Nice Exercise')
        self.key = 'nice-exercise'
        self.level = const.BRONZE_BADGE
        self.multiple = True
        self.min_votes = askbot_settings.NICE_EXERCISE_BADGE_MIN_UPVOTES
        self.description = _('Exercise voted up %(num)s times') % {'num': self.min_votes}
        self.post_type = 'exercise'
        return self

class GoodExercise(QualityPost):
    def __new__(cls):
        self = super(GoodExercise, cls).__new__(cls)
        self.name = _('Good Exercise')
        self.key = 'good-exercise'
        self.level = const.SILVER_BADGE
        self.multiple = True
        self.min_votes = askbot_settings.GOOD_EXERCISE_BADGE_MIN_UPVOTES
        self.description = _('Exercise voted up %(num)s times') % {'num': self.min_votes}
        self.post_type = 'exercise'
        return self

class GreatExercise(QualityPost):
    def __new__(cls):
        self = super(GreatExercise, cls).__new__(cls)
        self.name = _('Great Exercise')
        self.key = 'great-exercise'
        self.level = const.GOLD_BADGE
        self.multiple = True
        self.min_votes = askbot_settings.GREAT_EXERCISE_BADGE_MIN_UPVOTES
        self.description = _('Exercise voted up %(num)s times') % {'num': self.min_votes}
        self.post_type = 'exercise'
        return self

class Student(QualityPost):
    def __new__(cls):
        self = super(Student , cls).__new__(cls)
        self.name = _('Student')
        self.key = 'student'
        self.level = const.BRONZE_BADGE
        self.multiple = False
        self.min_votes = 1
        self.description = _('Asked first exercise with at least one up vote')
        self.post_type = 'exercise'
        return self

class FrequentedExercise(Badge):
    """this badge is not awarded directly
    but must be subclassed by Popular, Notable and Famous Exercise
    badges via __new__() method definitions

    The subclass has a responsibility to specify properties:
    * min_views - a value from live settings
    * key, name, description and level and multiple - as intended in the Badge
    """
    def __init__(self):
        super(FrequentedExercise, self).__init__(
            key = self.key,
            name = self.name,
            description = self.description,
            level = self.level,
            multiple = True
        )

    def consider_award(self, actor = None,
                context_object = None, timestamp = None):
        if context_object.post_type != 'exercise':
            return False
        if context_object.thread.view_count >= self.min_views:
            return self.award(context_object.author, context_object, timestamp)
        return False

class PopularExercise(FrequentedExercise):
    def __new__(cls):
        self = super(PopularExercise, cls).__new__(cls)
        self.name = _('Popular Exercise')
        self.key = 'popular-exercise'
        self.level = const.BRONZE_BADGE
        self.min_views = askbot_settings.POPULAR_EXERCISE_BADGE_MIN_VIEWS
        self.description = _('Added an exercise with %(views)s views') \
                            % {'views' : self.min_views}
        return self

class NotableExercise(FrequentedExercise):
    def __new__(cls):
        self = super(NotableExercise, cls).__new__(cls)
        self.name = _('Notable Exercise')
        self.key = 'notable-exercise'
        self.level = const.SILVER_BADGE
        self.min_views = askbot_settings.NOTABLE_EXERCISE_BADGE_MIN_VIEWS
        self.description = _('Added an exercise with %(views)s views') \
                            % {'views' : self.min_views}
        return self

class FamousExercise(FrequentedExercise):
    def __new__(cls):
        self = super(FamousExercise, cls).__new__(cls)
        self.name = _('Famous Exercise')
        self.key = 'famous-exercise'
        self.level = const.GOLD_BADGE
        self.multiple = True
        self.min_views = askbot_settings.FAMOUS_EXERCISE_BADGE_MIN_VIEWS
        self.description = _('Added an exercise with %(views)s views') \
                            % {'views' : self.min_views}
        return self

class Scholar(Badge):
    """scholar badge is awarded to the asker when
    he/she accepts a problem for the first time
    """
    def __init__(self):
        description = _('Added an exercise and accepted a problem')
        super(Scholar, self).__init__(
            key = 'scholar',
            name = _('Scholar'),
            level = const.BRONZE_BADGE,
            multiple = False,
            description = description
        )

    def consider_award(self, actor = None,
            context_object = None, timestamp = None):
        if context_object.post_type != 'problem':
            return False
        problem = context_object
        if problem.thread._exercise_post().author != actor:
            return False
        return self.award(actor, context_object, timestamp)

class VotedAcceptedProblem(Badge):
    """superclass for Enlightened and Guru badges
    not awarded directly

    Subclasses must define __new__ function
    """
    def __init__(self):
        super(VotedAcceptedProblem, self).__init__(
            key = self.key,
            name = self.name,
            level = self.level,
            multiple = self.multiple,
            description = self.description
        )

    def consider_award(self, actor = None,
            context_object = None, timestamp = None):
        if context_object.post_type != 'problem':
            return None
        problem = context_object
        if problem.points >= self.min_votes and problem.accepted():
            return self.award(problem.author, problem, timestamp)

class Enlightened(VotedAcceptedProblem):
    def __new__(cls):
        self = super(Enlightened, cls).__new__(cls)
        self.key = 'enlightened'
        self.name = _('Enlightened')
        self.level = const.SILVER_BADGE
        self.multiple = False
        self.min_votes = askbot_settings.ENLIGHTENED_BADGE_MIN_UPVOTES
        descr = _('First problem was accepted with %(num)s or more votes')
        self.description = descr % {'num': self.min_votes}
        return self

class Guru(VotedAcceptedProblem):
    def __new__(cls):
        self = super(Guru, cls).__new__(cls)
        self.key = 'guru'
        self.name = _('Guru')
        self.level = const.GOLD_BADGE
        self.multiple = True
        descr = _('Problem accepted with %(num)s or more votes')
        self.min_votes = askbot_settings.GURU_BADGE_MIN_UPVOTES
        self.description = descr % {'num': self.min_votes}
        return self

class Necromancer(Badge):
    def __init__(self):
        description = _(
            'Posted a problem to an exercise more than %(days)s days '
            'later with at least %(votes)s votes'
        )
        days = askbot_settings.NECROMANCER_BADGE_MIN_DELAY
        votes = askbot_settings.NECROMANCER_BADGE_MIN_UPVOTES
        super(Necromancer, self).__init__(
            key = 'necromancer',
            name = _('Necromancer'),
            level = const.SILVER_BADGE,
            description = description % {'days':days, 'votes':votes},
            multiple = True
        )

    def consider_award(self, actor = None,
            context_object = None, timestamp = None):
        if context_object.post_type != 'problem':
            return False
        problem = context_object
        exercise = problem.thread._exercise_post()
        delta = datetime.timedelta(askbot_settings.NECROMANCER_BADGE_MIN_DELAY)
        min_score = askbot_settings.NECROMANCER_BADGE_MIN_UPVOTES
        if problem.added_at - exercise.added_at >= delta \
            and problem.points >= min_score:
            return self.award(problem.author, problem, timestamp)
        return False

class CitizenPatrol(Badge):
    def __init__(self):
        super(CitizenPatrol, self).__init__(
            key = 'citizen-patrol',
            name = _('Citizen Patrol'),
            level = const.BRONZE_BADGE,
            multiple = False,
            description = _('First flagged post')
        )

class Cleanup(Badge):
    """This badge is inactive right now.
    to make it live we need to be able to either
    detect "undo" actions or rewrite the view
    correspondingly
    """
    def __init__(self):
        super(Cleanup, self).__init__(
            key = 'cleanup',
            name = _('Cleanup'),
            level = const.BRONZE_BADGE,
            multiple = False,
            description = _('First rollback')
        )

class Pundit(Badge):
    """Inactive until it is possible to vote
    for comments.
    Pundit is someone who makes good comments.
    """
    def __init__(self):
        super(Pundit, self).__init__(
            key = 'pundit',
            name = _('Pundit'),
            level = const.SILVER_BADGE,
            multiple = False,
            description = _('Left 10 comments with score of 10 or more')
        )

class EditorTypeBadge(Badge):
    """subclassing badges are types of editors
    must provide usual parameters + min_edits
    via __new__ function
    """
    def __init__(self):
        super(EditorTypeBadge, self).__init__(
            key = self.key,
            name = self.name,
            level = self.level,
            multiple = False,
            description = self.description
        )

    def consider_award(self, actor = None,
            context_object = None, timestamp = None):

        atypes = (
            const.TYPE_ACTIVITY_UPDATE_EXERCISE,
            const.TYPE_ACTIVITY_UPDATE_PROBLEM
        )
        filters = {'user': actor, 'activity_type__in': atypes}
        if Activity.objects.filter(**filters).count() == self.min_edits:
            return self.award(actor, context_object, timestamp)

class Editor(EditorTypeBadge):
    def __new__(cls):
        self = super(Editor, cls).__new__(cls)
        self.key = 'editor'
        self.name = _('Editor')
        self.level = const.BRONZE_BADGE
        self.multiple = False
        self.description = _('First edit')
        self.min_edits = 1
        return self

class AssociateEditor(EditorTypeBadge):
    def __new__(cls):
        self = super(AssociateEditor, cls).__new__(cls)
        self.key = 'strunk-and-white'#legacy copycat name from stackoverflow
        self.name = _('Associate Editor')
        self.level = const.SILVER_BADGE
        self.multiple = False
        self.min_edits = askbot_settings.ASSOCIATE_EDITOR_BADGE_MIN_EDITS
        self.description = _('Edited %(num)s entries') % {'num': self.min_edits}
        return self

class Organizer(Badge):
    def __init__(self):
        super(Organizer, self).__init__(
            key = 'organizer',
            name = _('Organizer'),
            level = const.BRONZE_BADGE,
            multiple = False,
            description = _('First retag')
        )

class Autobiographer(Badge):
    def __init__(self):
        super(Autobiographer, self).__init__(
            key = 'autobiographer',
            name = _('Autobiographer'),
            level = const.BRONZE_BADGE,
            multiple = False,
            description = _('Completed all user profile fields')
        )

    def consider_award(self, actor = None,
            context_object = None, timestamp = None):
        user = context_object
        if user.email and user.real_name and user.website \
            and user.location and user.about:
            return self.award(user, user, timestamp)
        return False

class FavoriteTypeBadge(Badge):
    """subclass must use __new__ and in addition
    must provide min_stars property for the badge
    """
    def __init__(self):
        descr = _('Exercise favorited by %(num)s users')
        super(FavoriteTypeBadge, self).__init__(
            key = self.key,
            name = self.name,
            level = self.level,
            multiple = True,
            description = descr % {'num': self.min_stars}
        )

    def consider_award(self, actor = None,
            context_object = None, timestamp = None):
        exercise = context_object
        #model FavoriteExercise imported under alias of Fave
        count = Fave.objects.filter(
                                        thread = exercise.thread
                                    ).exclude(
                                        user = exercise.author
                                    ).count()
        if count == self.min_stars:
            return self.award(exercise.author, exercise, timestamp)
        return False

class StellarExercise(FavoriteTypeBadge):
    def __new__(cls):
        self = super(StellarExercise, cls).__new__(cls)
        self.key = 'stellar-exercise'
        self.name = _('Stellar Exercise')
        self.level = const.GOLD_BADGE
        self.min_stars = askbot_settings.STELLAR_EXERCISE_BADGE_MIN_STARS
        return self

class FavoriteExercise(FavoriteTypeBadge):
    def __new__(cls):
        self = super(FavoriteExercise, cls).__new__(cls)
        self.key = 'favorite-exercise'
        self.name = _('Favorite Exercise')
        self.level = const.SILVER_BADGE
        self.min_stars = askbot_settings.FAVORITE_EXERCISE_BADGE_MIN_STARS
        return self

class Enthusiast(Badge):
    """Awarded to a user who visits the site
    for a certain number of days in a row
    """
    def __init__(self):
        super(Enthusiast, self).__init__(
            key = 'enthusiast',
            name = _('Enthusiast'),
            level = const.SILVER_BADGE,
            multiple = False,
            description = _(
                'Visited site every day for %(num)s days in a row'
            ) % {'num': askbot_settings.ENTHUSIAST_BADGE_MIN_DAYS}
        )

    def consider_award(self, actor = None,
            context_object = None, timestamp = None):
        min_days = askbot_settings.ENTHUSIAST_BADGE_MIN_DAYS
        if actor.consecutive_days_visit_count == min_days:
            return self.award(actor, context_object, timestamp)
        return False

class Commentator(Badge):
    """Commentator is a bronze badge that is
    awarded once when user posts a certain number of
    comments"""
    def __init__(self):
        super(Commentator, self).__init__(
            key = 'commentator',
            name = _('Commentator'),
            level = const.BRONZE_BADGE,
            multiple = False,
            description = _(
                'Posted %(num_comments)s comments'
            ) % {'num_comments': askbot_settings.COMMENTATOR_BADGE_MIN_COMMENTS}
        )

    def consider_award(self, actor = None,
            context_object = None, timestamp = None):
        num_comments = Post.objects.get_comments().filter(author=actor).count()
        if num_comments >= askbot_settings.COMMENTATOR_BADGE_MIN_COMMENTS:
            return self.award(actor, context_object, timestamp)
        return False

class Taxonomist(Badge):
    """Stub badge"""
    def __init__(self):
        super(Taxonomist, self).__init__(
            key = 'taxonomist',
            name = _('Taxonomist'),
            level = const.SILVER_BADGE,
            multiple = False,
            description = _(
                'Created a tag used by %(num)s exercises'
            ) % {'num': askbot_settings.TAXONOMIST_BADGE_MIN_USE_COUNT}
        )

    def consider_award(self, actor = None,
            context_object = None, timestamp = None):

        tag = context_object
        taxonomist_threshold = askbot_settings.TAXONOMIST_BADGE_MIN_USE_COUNT
        if tag.used_count == taxonomist_threshold:
            return self.award(tag.created_by, tag, timestamp)
        return False

class Expert(Badge):
    """Stub badge"""
    def __init__(self):
        super(Expert, self).__init__(
            key = 'expert',
            name = _('Expert'),
            level = const.SILVER_BADGE,
            multiple = False,
            description = _('Very active in one tag')
        )

ORIGINAL_DATA = """

extra badges from stackexchange
* commentator - left n comments (single)
* enthusiast, fanatic - visited site n days in a row (s)
* epic, legendary - hit daily reputation cap on n days (s)
* mortarboard - hit the daily reputation cap for the first time (s)
* populist - provided a problem that outscored an accepted problem two-fold or by n points, whichever is higher (m)
* reversal - provided a problem with +n points to an exercise of -m points
    (_('Yearling'), 2, _('yearling'), _('Active member for a year'), False, 0),


    (_('Generalist'), 2, _('generalist'), _('Active in many different tags'), False, 0),
    (_('Beta'), 2, _('beta'), _('Actively participated in the private beta'), False, 0),
    (_('Alpha'), 2, _('alpha'), _('Actively participated in the private alpha'), False, 0),
"""

BADGES = {
    'strunk-and-white': AssociateEditor,#legacy slug name
    'autobiographer': Autobiographer,
    'cleanup': Cleanup,
    'citizen-patrol': CitizenPatrol,
    'civic-duty': CivicDuty,
    'commentator': Commentator,
    'critic': Critic,
    'disciplined': Disciplined,
    'editor': Editor,
    'enlightened': Enlightened,
    'enthusiast': Enthusiast,
    'expert': Expert,
    'famous-exercise': FamousExercise,
    'favorite-exercise': FavoriteExercise,
    'good-problem': GoodProblem,
    'good-exercise': GoodExercise,
    'great-problem': GreatProblem,
    'great-exercise': GreatExercise,
    'guru': Guru,
    'necromancer': Necromancer,
    'nice-problem': NiceProblem,
    'nice-exercise': NiceExercise,
    'notable-exercise': NotableExercise,
    'organizer': Organizer,
    'peer-pressure': PeerPressure,
    'popular-exercise': PopularExercise,
    'pundit': Pundit,
    'scholar': Scholar,
    'self-learner': SelfLearner,
    'stellar-exercise': StellarExercise,
    'student': Student,
    'supporter': Supporter,
    'teacher': Teacher,
    'taxonomist': Taxonomist,
}

#events are sent as a parameter via signal award_badges_signal
#from appropriate locations in the code of askbot application
#most likely - from manipulator functions that are added to the User objects
EVENTS_TO_BADGES = {
    'accept_best_problem': (Scholar, Guru, Enlightened),
    'delete_post': (Disciplined, PeerPressure,),
    'downvote': (Critic, CivicDuty),#no regard for exercise or problem for now
    'edit_problem': (Editor, AssociateEditor),
    'edit_exercise': (Editor, AssociateEditor),
    'flag_post': (CitizenPatrol,),
    'post_problem': (Necromancer,),
    'post_comment': (Commentator,),
    'retag_exercise': (Organizer,),
    'select_favorite_exercise': (FavoriteExercise, StellarExercise,),
    'site_visit': (Enthusiast,),
    'update_tag': (Taxonomist,),
    'update_user_profile': (Autobiographer,),
    'upvote_problem': (
                    Teacher, NiceProblem, GoodProblem,
                    GreatProblem, Supporter, SelfLearner, CivicDuty,
                    Guru, Enlightened, Necromancer
                ),
    'upvote_exercise': (
                    NiceExercise, GoodExercise,
                    GreatExercise, Student, Supporter, CivicDuty
                ),
    'upvote_comment':(),#todo - add some badges here
    'view_exercise': (PopularExercise, NotableExercise, FamousExercise,),
}

def get_badge(name = None):
    """Get badge object by name, if none matches the name
    raise KeyError
    """
    key = slugify(name)
    return BADGES[key]()

def init_badges():
    """Calling this function will set up badge record
    int the database for each badge enumerated in the
    `BADGES` dictionary
    """
    #todo: maybe better to redo individual badges
    #so that get_stored_data() is called implicitly
    #from the __init__ function?
    for key in BADGES.keys():
        get_badge(key).get_stored_data()
    #remove any badges from the database
    #that are no longer in the BADGES dictionary
    BadgeData.objects.exclude(
        slug__in = map(slugify, BADGES.keys())
    ).delete()

award_badges_signal = Signal(
                        providing_args=[
                            'actor', 'event', 'context_object', 'timestamp'
                        ]
                    )
#actor - user who triggers the event
#event - string name of the event, e.g 'downvote'
#context_object - database object related to the event, e.g. exercise

@auto_now_timestamp
def award_badges(event = None, actor = None,
                context_object = None, timestamp = None, **kwargs):
    """function that is called when signal `award_badges_signal` is sent
    """
    try:
        consider_badges = EVENTS_TO_BADGES[event]
    except KeyError:
        raise NotImplementedError('event "%s" is not implemented' % event)

    for badge in consider_badges:
        badge_instance = badge()
        badge_instance.consider_award(actor, context_object, timestamp)

award_badges_signal.connect(award_badges)
