"""
Authorisation related functions.

This entire module will be removed some time in
the future

Many of these functions are being replaced with assertions:
User.assert_can...
"""
import datetime
from django.db import transaction
from askbot.models import Repute
#from askbot.models import Problem
from askbot.models import signals
from askbot.conf import settings as askbot_settings

###########################################
## actions and reputation changes event
###########################################
@transaction.commit_on_success
def onFlaggedItem(post, user, timestamp=None):
    if timestamp is None:
        timestamp = datetime.datetime.now()

    post.offensive_flag_count = post.offensive_flag_count + 1
    post.save()

    flagged_user = post.author

    flagged_user.receive_reputation(
        askbot_settings.REP_LOSS_FOR_RECEIVING_FLAG
    )
    flagged_user.save()

    exercise = post.thread._exercise_post()

    reputation = Repute(
                    user=flagged_user,
                    negative=askbot_settings.REP_LOSS_FOR_RECEIVING_FLAG,
                    exercise=exercise,
                    reputed_at=timestamp,
                    reputation_type=-4,#todo: clean up magic number
                    reputation=flagged_user.reputation
                )
    reputation.save()

    signals.flag_offensive.send(
        sender=post.__class__,
        instance=post,
        mark_by=user
    )

    if post.post_type == 'comment':
        #do not hide or delete comments automatically yet,
        #because there is no .deleted field in the comment model
        return

    #todo: These should be updated to work on same revisions.
    if post.offensive_flag_count ==  askbot_settings.MIN_FLAGS_TO_HIDE_POST:
        #todo: strange - are we supposed to hide the post here or the name of
        #setting is incorrect?
        flagged_user.receive_reputation(
            askbot_settings.REP_LOSS_FOR_RECEIVING_THREE_FLAGS_PER_REVISION
        )

        flagged_user.save()

        reputation = Repute(
            user=flagged_user,
            negative=\
                askbot_settings.REP_LOSS_FOR_RECEIVING_THREE_FLAGS_PER_REVISION,
            exercise=exercise,
            reputed_at=timestamp,
            reputation_type=-6,
            reputation=flagged_user.reputation
        )
        reputation.save()

    elif post.offensive_flag_count == askbot_settings.MIN_FLAGS_TO_DELETE_POST:
        flagged_user.receive_reputation(
            askbot_settings.REP_LOSS_FOR_RECEIVING_FIVE_FLAGS_PER_REVISION
        )

        flagged_user.save()

        reputation = Repute(
            user=flagged_user,
            negative=\
                askbot_settings.REP_LOSS_FOR_RECEIVING_FIVE_FLAGS_PER_REVISION,
            exercise=exercise,
            reputed_at=timestamp,
            reputation_type=-7,
            reputation=flagged_user.reputation
        )
        reputation.save()

        post.deleted = True
        #post.deleted_at = timestamp
        #post.deleted_by = Admin
        post.save()


@transaction.commit_on_success
def onUnFlaggedItem(post, user, timestamp=None):
    if timestamp is None:
        timestamp = datetime.datetime.now()

    post.offensive_flag_count = post.offensive_flag_count - 1
    post.save()

    flagged_user = post.author

    flagged_user.receive_reputation(
        - askbot_settings.REP_LOSS_FOR_RECEIVING_FLAG
    )
    flagged_user.save()

    exercise = post.thread._exercise_post()

    reputation = Repute(
                    user=flagged_user,
                    positive=askbot_settings.REP_LOSS_FOR_RECEIVING_FLAG,
                    exercise=exercise,
                    reputed_at=timestamp,
                    reputation_type=-4,#todo: clean up magic number
                    reputation=flagged_user.reputation
                )
    reputation.save()

    signals.remove_flag_offensive.send(
        sender=post.__class__,
        instance=post,
        mark_by=user
    )

    if post.post_type == 'comment':
        #do not hide or delete comments automatically yet,
        #because there is no .deleted field in the comment model
        return

    #todo: These should be updated to work on same revisions.
    # The post fell below HIDE treshold - unhide it.
    if post.offensive_flag_count ==  askbot_settings.MIN_FLAGS_TO_HIDE_POST - 1:
        #todo: strange - are we supposed to hide the post here or the name of
        #setting is incorrect?
        flagged_user.receive_reputation(
            - askbot_settings.REP_LOSS_FOR_RECEIVING_THREE_FLAGS_PER_REVISION
        )

        flagged_user.save()

        reputation = Repute(
            user=flagged_user,
            positive=\
                askbot_settings.REP_LOSS_FOR_RECEIVING_THREE_FLAGS_PER_REVISION,
            exercise=exercise,
            reputed_at=timestamp,
            reputation_type=-6,
            reputation=flagged_user.reputation
        )
        reputation.save()
    # The post fell below DELETE treshold, undelete it
    elif post.offensive_flag_count == askbot_settings.MIN_FLAGS_TO_DELETE_POST-1 :
        flagged_user.receive_reputation(
            - askbot_settings.REP_LOSS_FOR_RECEIVING_FIVE_FLAGS_PER_REVISION
        )

        flagged_user.save()

        reputation = Repute(
            user=flagged_user,
            positive =\
                askbot_settings.REP_LOSS_FOR_RECEIVING_FIVE_FLAGS_PER_REVISION,
            exercise=exercise,
            reputed_at=timestamp,
            reputation_type=-7,
            reputation=flagged_user.reputation
        )
        reputation.save()

        post.deleted = False
        post.save()

@transaction.commit_on_success
def onProblemAccept(problem, user, timestamp=None):
    problem.thread.set_accepted_problem(problem=problem, timestamp=timestamp)
    exercise = problem.thread._exercise_post()

    if problem.author != user:
        problem.author.receive_reputation(
            askbot_settings.REP_GAIN_FOR_RECEIVING_PROBLEM_ACCEPTANCE
        )
        problem.author.save()
        reputation = Repute(user=problem.author,
                   positive=askbot_settings.REP_GAIN_FOR_RECEIVING_PROBLEM_ACCEPTANCE,
                   exercise=exercise,
                   reputed_at=timestamp,
                   reputation_type=2,
                   reputation=problem.author.reputation)
        reputation.save()

    if problem.author == exercise.author and user == exercise.author:
        #a plug to prevent reputation gaming by posting a exercise
        #then probleming and accepting as best all by the same person
        return

    user.receive_reputation(askbot_settings.REP_GAIN_FOR_ACCEPTING_PROBLEM)
    user.save()
    reputation = Repute(user=user,
               positive=askbot_settings.REP_GAIN_FOR_ACCEPTING_PROBLEM,
               exercise=exercise,
               reputed_at=timestamp,
               reputation_type=3,
               reputation=user.reputation)
    reputation.save()

@transaction.commit_on_success
def onProblemAcceptCanceled(problem, user, timestamp=None):
    if timestamp is None:
        timestamp = datetime.datetime.now()
    problem.thread.set_accepted_problem(problem=None, timestamp=None)
    exercise = problem.thread._exercise_post()

    if user != problem.author:
        problem.author.receive_reputation(
            askbot_settings.REP_LOSS_FOR_RECEIVING_CANCELATION_OF_PROBLEM_ACCEPTANCE
        )
        problem.author.save()
        reputation = Repute(
            user=problem.author,
            negative=\
             askbot_settings.REP_LOSS_FOR_RECEIVING_CANCELATION_OF_PROBLEM_ACCEPTANCE,
            exercise=exercise,
            reputed_at=timestamp,
            reputation_type=-2,
            reputation=problem.author.reputation
        )
        reputation.save()

    if problem.author == exercise.author and user == exercise.author:
        #a symmettric measure for the reputation gaming plug
        #as in the onProblemAccept function
        #here it protects the user from uwanted reputation loss
        return

    user.receive_reputation(
        askbot_settings.REP_LOSS_FOR_CANCELING_PROBLEM_ACCEPTANCE
    )
    user.save()
    reputation = Repute(user=user,
               negative=askbot_settings.REP_LOSS_FOR_CANCELING_PROBLEM_ACCEPTANCE,
               exercise=exercise,
               reputed_at=timestamp,
               reputation_type=-1,
               reputation=user.reputation)
    reputation.save()

@transaction.commit_on_success
def onUpVoted(vote, post, user, timestamp=None):
    if timestamp is None:
        timestamp = datetime.datetime.now()
    vote.save()

    if post.post_type != 'comment':
        post.vote_up_count = int(post.vote_up_count) + 1
    post.points = int(post.points) + 1
    post.save()

    if post.post_type == 'comment':
        #reputation is not affected by the comment votes
        return

    if not (post.wiki or post.is_anonymous):
        author = post.author
        todays_rep_gain = Repute.objects.get_reputation_by_upvoted_today(author)
        if todays_rep_gain <  askbot_settings.MAX_REP_GAIN_PER_USER_PER_DAY:
            author.receive_reputation(
                askbot_settings.REP_GAIN_FOR_RECEIVING_UPVOTE
            )
            author.save()

            exercise = post.thread._exercise_post() # TODO: this is suboptimal if post is already a exercise

            reputation = Repute(user=author,
                       positive=askbot_settings.REP_GAIN_FOR_RECEIVING_UPVOTE,
                       exercise=exercise,
                       reputed_at=timestamp,
                       reputation_type=1,
                       reputation=author.reputation)
            reputation.save()

@transaction.commit_on_success
def onUpVotedCanceled(vote, post, user, timestamp=None):
    if timestamp is None:
        timestamp = datetime.datetime.now()
    vote.delete()

    if post.post_type != 'comment':
        post.vote_up_count = int(post.vote_up_count) - 1
        if post.vote_up_count < 0:
            post.vote_up_count  = 0

    post.points = int(post.points) - 1
    post.save()

    if post.post_type == 'comment':
        #comment votes do not affect reputation
        return

    if not (post.wiki or post.is_anonymous):
        author = post.author
        author.receive_reputation(
            askbot_settings.REP_LOSS_FOR_RECEIVING_UPVOTE_CANCELATION
        )
        author.save()

        exercise = post.thread._exercise_post() # TODO: this is suboptimal if post is already a exercise

        reputation = Repute(
            user=author,
            negative=askbot_settings.REP_LOSS_FOR_RECEIVING_UPVOTE_CANCELATION,
            exercise=exercise,
            reputed_at=timestamp,
            reputation_type=-8,
            reputation=author.reputation
        )
        reputation.save()

@transaction.commit_on_success
def onDownVoted(vote, post, user, timestamp=None):
    if timestamp is None:
        timestamp = datetime.datetime.now()
    vote.save()

    post.vote_down_count = int(post.vote_down_count) + 1
    post.points = int(post.points) - 1
    post.save()

    if not (post.wiki or post.is_anonymous):
        author = post.author
        author.receive_reputation(
            askbot_settings.REP_LOSS_FOR_RECEIVING_DOWNVOTE
        )
        author.save()

        exercise = post.thread._exercise_post() # TODO: this is suboptimal if post is already a exercise

        reputation = Repute(user=author,
                   negative=askbot_settings.REP_LOSS_FOR_RECEIVING_DOWNVOTE,
                   exercise=exercise,
                   reputed_at=timestamp,
                   reputation_type=-3,
                   reputation=author.reputation)
        reputation.save()

        user.receive_reputation(
            askbot_settings.REP_LOSS_FOR_DOWNVOTING,
        )
        user.save()

        reputation = Repute(user=user,
                   negative=askbot_settings.REP_LOSS_FOR_DOWNVOTING,
                   exercise=exercise,
                   reputed_at=timestamp,
                   reputation_type=-5,
                   reputation=user.reputation)
        reputation.save()

@transaction.commit_on_success
def onDownVotedCanceled(vote, post, user, timestamp=None):
    if timestamp is None:
        timestamp = datetime.datetime.now()
    vote.delete()

    post.vote_down_count = int(post.vote_down_count) - 1
    if post.vote_down_count < 0:
        post.vote_down_count  = 0
    post.points = post.points + 1
    post.save()

    if not (post.wiki or post.is_anonymous):
        author = post.author
        author.receive_reputation(
            askbot_settings.REP_GAIN_FOR_RECEIVING_DOWNVOTE_CANCELATION
        )
        author.save()

        exercise = post.thread._exercise_post() # TODO: this is suboptimal if post is already a exercise

        reputation = Repute(user=author,
                positive=\
                    askbot_settings.REP_GAIN_FOR_RECEIVING_DOWNVOTE_CANCELATION,
                exercise=exercise,
                reputed_at=timestamp,
                reputation_type=4,
                reputation=author.reputation
            )
        reputation.save()

        user.receive_reputation(askbot_settings.REP_GAIN_FOR_CANCELING_DOWNVOTE)
        user.save()

        reputation = Repute(user=user,
                   positive=askbot_settings.REP_GAIN_FOR_CANCELING_DOWNVOTE,
                   exercise=exercise,
                   reputed_at=timestamp,
                   reputation_type=5,
                   reputation=user.reputation)
        reputation.save()
