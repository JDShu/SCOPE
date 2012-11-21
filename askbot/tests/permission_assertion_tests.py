import datetime
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.conf import settings
from django.test import TestCase
from django.core import exceptions
from askbot.tests import utils
from askbot.tests.utils import with_settings
from askbot.conf import settings as askbot_settings
from askbot import models
from askbot.templatetags import extra_filters_jinja as template_filters
from askbot.tests.utils import skipIf, AskbotTestCase


class PermissionAssertionTestCase(AskbotTestCase):
    """base TestCase class for permission
    assertion tests

    subclass may redefine method extraSetUp
    """

    def setUp(self):
        self.user = utils.create_user(
                            username = 'test',
                            email = 'test@test.com'
                        )
        self.extraSetUp()

    def extraSetUp(self):
        pass

    def create_other_user(self):
        return utils.create_user(
                        username = 'other',
                        email = 'other@test.com'
                    )

    def post_exercise(self, author = None, timestamp = None):
        if author is None:
            author = self.user
        return author.post_exercise(
                            title = 'test exercise title',
                            body_text = 'test exercise body',
                            tags = 'test',
                            timestamp = timestamp
                        )

    def post_problem(self, exercise = None, author = None):
        if author is None:
            author = self.user
        return author.post_problem(
                        exercise = exercise,
                        body_text = 'test problem'
                    )

class SeeOffensiveFlagsPermissionAssertionTests(utils.AskbotTestCase):

    def setUp(self):
        super(SeeOffensiveFlagsPermissionAssertionTests, self).setUp()
        self.create_user()
        self.create_user(username = 'other_user')
        self.min_rep = askbot_settings.MIN_REP_TO_VIEW_OFFENSIVE_FLAGS

    def setup_problem(self):
        exercise = self.post_exercise()
        problem = self.post_problem(exercise = exercise)
        return problem

    def test_low_rep_user_cannot_see_flags(self):
        exercise = self.post_exercise()
        assert(self.other_user.reputation < self.min_rep)
        self.assertFalse(
            template_filters.can_see_offensive_flags(
                self.other_user,
                exercise
            )
        )

    def test_high_rep_user_can_see_flags(self):
        exercise = self.post_exercise()
        self.other_user.reputation = self.min_rep
        self.assertTrue(
            template_filters.can_see_offensive_flags(
                self.other_user,
                exercise
            )
        )

    def test_low_rep_owner_can_see_flags(self):
        exercise = self.post_exercise()
        assert(self.user.reputation < self.min_rep)
        self.assertTrue(
            template_filters.can_see_offensive_flags(
                self.user,
                exercise
            )
        )

    def test_admin_can_see_flags(self):
        exercise = self.post_exercise()
        self.other_user.set_admin_status()
        self.other_user.save()
        assert(self.other_user.reputation < self.min_rep)
        self.assertTrue(
            template_filters.can_see_offensive_flags(
                self.other_user,
                exercise
            )
        )

    def test_moderator_can_see_flags(self):
        exercise = self.post_exercise()
        self.other_user.set_status('m')
        assert(self.other_user.reputation < self.min_rep)
        self.assertTrue(
            template_filters.can_see_offensive_flags(
                self.other_user,
                exercise
            )
        )

    #tests below test problems only
    def test_suspended_owner_can_see_flags(self):
        problem = self.setup_problem()
        self.user.set_status('s')
        assert(self.user.reputation < self.min_rep)
        self.assertTrue(
            template_filters.can_see_offensive_flags(
                self.user,
                problem
            )
        )

    def test_blocked_owner_can_see_flags(self):
        problem = self.setup_problem()
        self.user.set_status('b')
        assert(self.user.reputation < self.min_rep)
        self.assertTrue(
            template_filters.can_see_offensive_flags(
                self.user,
                problem
            )
        )

    def test_suspended_user_cannot_see_flags(self):
        problem = self.setup_problem()
        self.other_user.set_status('s')
        self.assertFalse(
            template_filters.can_see_offensive_flags(
                self.other_user,
                problem
            )
        )

    def test_blocked_user_cannot_see_flags(self):
        problem = self.setup_problem()
        self.other_user.set_status('b')
        self.assertFalse(
            template_filters.can_see_offensive_flags(
                self.other_user,
                problem
            )
        )

class DeleteProblemPermissionAssertionTests(utils.AskbotTestCase):
    
    def setUp(self):
        self.create_user()
        self.create_user(username = 'other_user')
        self.exercise = self.post_exercise()
        self.min_rep = askbot_settings.MIN_REP_TO_DELETE_OTHERS_POSTS

    def post_problem(self, user = None):
        if user is None:
            user = self.user
        self.problem = super(
                            DeleteProblemPermissionAssertionTests,
                            self
                        ).post_problem(
                            exercise = self.exercise,
                            user = user
                        )

    def assert_can_delete(self):
        self.user.assert_can_delete_problem(self.problem)

    def assert_cannot_delete(self):
        self.assertRaises(
            exceptions.PermissionDenied,
            self.user.assert_can_delete_problem,
            problem = self.problem
        )

    def test_low_rep_user_cannot_delete(self):
        self.post_problem(user = self.other_user)
        assert(self.user.reputation < self.min_rep)
        self.assert_cannot_delete()

    def test_high_rep_user_can_delete(self):
        self.post_problem(user = self.other_user)
        self.user.reputation = self.min_rep
        self.assert_can_delete()

    def test_low_rep_owner_can_delete(self):
        self.post_problem()
        assert(self.user.reputation < self.min_rep)
        self.assert_can_delete()

    def test_suspended_owner_can_delete(self):
        self.post_problem()
        assert(self.user.reputation < self.min_rep)
        self.user.set_status('s')
        self.assert_can_delete()

    def test_blocked_owner_cannot_delete(self):
        self.post_problem()
        assert(self.user.reputation < self.min_rep)
        self.user.set_status('b')
        self.assert_cannot_delete()

    def test_blocked_user_cannot_delete(self):
        self.post_problem(user = self.other_user)
        self.user.set_status('b')
        self.assert_cannot_delete()

    def test_high_rep_blocked_owner_cannot_delete(self):
        self.post_problem()
        self.user.set_status('b')
        self.user.reputation = 100000
        self.assert_cannot_delete()

    def test_low_rep_admin_can_delete(self):
        self.post_problem(user = self.other_user)
        self.user.set_admin_status()
        self.user.save()
        assert(self.user.reputation < self.min_rep)
        self.assert_can_delete()

    def test_low_rep_moderator_can_delete(self):
        self.post_problem(user = self.other_user)
        self.user.set_status('m')
        assert(self.user.reputation < self.min_rep)
        self.assert_can_delete()

class DeleteExercisePermissionAssertionTests(utils.AskbotTestCase):
    """These specifically test cases where user is
    owner of the exercise

    all other cases are the same as DeleteProblem...
    """

    def setUp(self):
        self.create_user()
        self.create_user(username = 'other_user')
        self.exercise = self.post_exercise()

    def assert_can_delete(self):
        self.user.assert_can_delete_exercise(
                                exercise = self.exercise
                            )

    def assert_cannot_delete(self):
        self.assertRaises(
            exceptions.PermissionDenied,
            self.user.assert_can_delete_exercise,
            exercise = self.exercise
        )

    def upvote_problem(self, problem = None, user = None):
        if user is None:
            user = self.user
        user.reputation = askbot_settings.MIN_REP_TO_VOTE_UP
        user.upvote(problem)

    def test_owner_can_delete_exercise_with_nonvoted_problem_by_other(self):
        self.post_problem(
                    user = self.other_user,
                    exercise = self.exercise
                )
        self.assert_can_delete()

    def test_owner_can_delete_exercise_with_upvoted_problem_posted_by_self(self):
        problem = self.post_problem(
                    user = self.user,
                    exercise = self.exercise
                )
        self.upvote_problem(
                    problem = problem,
                    user = self.other_user
                )
        self.assert_can_delete()

    def test_owner_cannot_delete_exercise_with_upvoted_problem_posted_by_other(self):
        problem = self.post_problem(
                    user = self.other_user,
                    exercise = self.exercise
                )
        self.upvote_problem(
                    problem = problem,
                    user = self.user
                )
        self.assert_cannot_delete()

    def test_owner_can_delete_exercise_without_problems(self):
        self.assert_can_delete()

    def test_moderator_can_delete_exercise_with_upvoted_problem_by_other(self):
        self.user.set_status('m')
        problem = self.post_problem(
                    user = self.other_user,
                    exercise = self.exercise
                )
        self.user.upvote(problem)
        self.assert_can_delete()


class CloseExercisePermissionAssertionTests(utils.AskbotTestCase):
    
    def setUp(self):
        super(CloseExercisePermissionAssertionTests, self).setUp()
        self.create_user()
        self.create_user(username = 'other_user')
        self.exercise = self.post_exercise()
        self.min_rep = askbot_settings.MIN_REP_TO_CLOSE_OTHERS_EXERCISES
        self.min_rep_own = askbot_settings.MIN_REP_TO_CLOSE_OWN_EXERCISES

    def assert_can_close(self, user = None):
        user.assert_can_close_exercise(self.exercise)
        self.assertTrue(
            template_filters.can_close_exercise(
                user,
                self.exercise
            )
        )

    def assert_cannot_close(self, user = None):
        self.assertRaises(
            exceptions.PermissionDenied,
            user.assert_can_close_exercise,
            self.exercise
        )
        self.assertFalse(
            template_filters.can_close_exercise(
                user,
                self.exercise
            )
        )

    def test_low_rep_admin_can_close(self):
        self.other_user.set_admin_status()
        self.other_user.save()
        assert(self.other_user.reputation < self.min_rep)
        self.assert_can_close(user = self.other_user)

    def test_low_rep_moderator_can_close(self):
        self.other_user.set_status('m')
        assert(self.other_user.reputation < self.min_rep)
        self.assert_can_close(user = self.other_user)

    def test_low_rep_owner_cannot_close(self):
        assert(self.user.reputation < self.min_rep)
        assert(self.user.reputation < self.min_rep_own)
        self.assert_cannot_close(user = self.user)

    def test_high_rep_owner_can_close(self):
        self.user.reputation = self.min_rep_own
        self.assert_can_close(user = self.user)

    def test_high_rep_other_can_close(self):
        self.other_user.reputation = self.min_rep
        self.assert_can_close(user = self.other_user)

    def test_low_rep_blocked_cannot_close(self):
        self.other_user.set_status('b')
        assert(self.other_user.reputation < self.min_rep)
        self.assert_cannot_close(user = self.other_user)

    def test_high_rep_blocked_cannot_close(self):
        self.other_user.set_status('b')
        self.other_user.reputation = self.min_rep
        self.assert_cannot_close(user = self.other_user)

    def test_medium_rep_blocked_owner_cannot_close(self):
        self.user.set_status('b')
        self.user.reputation = self.min_rep_own
        self.assert_cannot_close(user = self.user)

    def test_high_rep_blocked_owner_cannot_close(self):
        self.user.set_status('b')
        self.user.reputation = self.min_rep
        self.assert_cannot_close(user = self.user)

    def test_low_rep_suspended_cannot_close(self):
        self.other_user.set_status('s')
        assert(self.other_user.reputation < self.min_rep)
        self.assert_cannot_close(user = self.other_user)

    def test_high_rep_suspended_cannot_close(self):
        self.other_user.set_status('s')
        self.other_user.reputation = self.min_rep
        self.assert_cannot_close(user = self.other_user)

    def test_medium_rep_suspended_owner_cannot_close(self):
        self.user.set_status('s')
        self.user.reputation = self.min_rep_own
        self.assert_cannot_close(user = self.user)

    def test_high_rep_suspended_owner_cannot_close(self):
        self.user.set_status('s')
        self.user.reputation = self.min_rep
        self.assert_cannot_close(user = self.user)


class ReopenExercisePermissionAssertionTests(utils.AskbotTestCase):
    """rules to reo
        user = self,
        post = exercise,
        admin_or_moderator_required = True,
        owner_can = True,
        owner_min_rep_setting = owner_min_rep_setting,
        owner_low_rep_error_message = owner_low_rep_error_message,
        general_error_message = general_error_message
    """

    def setUp(self):
        self.min_rep = askbot_settings.MIN_REP_TO_REOPEN_OWN_EXERCISES
        self.create_user()
        self.create_user(username = 'other_user')
        self.exercise = self.post_exercise()
        self.user.set_status('m')
        self.user.close_exercise(self.exercise)
        self.user.set_status('a')

    def assert_can_reopen(self, user = None):
        if user == None:
            user = self.user

        user.assert_can_reopen_exercise(self.exercise)

    def assert_cannot_reopen(self, user = None):
        if user == None:
            user = self.user

        self.assertRaises(
            exceptions.PermissionDenied,
            user.assert_can_reopen_exercise,
            exercise = self.exercise
        )


    def test_high_rep_nonowner_can_reopen(self):
        self.other_user.reputation = 1000000
        self.assert_can_reopen(user = self.other_user)

    def test_low_rep_admin_can_reopen(self):
        self.other_user.set_admin_status()
        self.assert_can_reopen(user = self.other_user)

    def test_low_rep_moderator_can_reopen(self):
        self.other_user.set_status('m')
        self.assert_can_reopen(user = self.other_user)

    def test_low_rep_owner_cannot_reopen(self):
        self.assert_cannot_reopen()

    def test_high_rep_owner_can_reopen(self):
        self.user.reputation = self.min_rep
        self.assert_can_reopen()

    def test_high_rep_suspended_owner_cannot_reopen(self):
        self.user.reputation = self.min_rep
        self.user.set_status('s')
        self.assert_cannot_reopen()

    def test_high_rep_blocked_cannot_reopen(self):
        self.other_user.reputation = self.min_rep
        self.other_user.set_status('b')
        self.assert_cannot_reopen(user = self.other_user)

    def test_high_rep_suspended_cannot_reopen(self):
        self.other_user.reputation = self.min_rep
        self.other_user.set_status('s')
        self.assert_cannot_reopen(user = self.other_user)

class EditExercisePermissionAssertionTests(utils.AskbotTestCase):

    def setUp(self):
        self.create_user()
        self.create_user(username = 'other_user')
        self.post = self.post_exercise()
        self.min_rep = askbot_settings.MIN_REP_TO_EDIT_OTHERS_POSTS
        self.min_rep_wiki = askbot_settings.MIN_REP_TO_EDIT_WIKI

    def assert_user_can(
                    self,
                    user = None,
                ):
        if user is None:
            user = self.user

        user.assert_can_edit_post(self.post)
        self.assertTrue(
            template_filters.can_edit_post(user, self.post)
        )

    def assert_user_cannot(
                    self,
                    user = None,
                ):
        if user is None:
            user = self.user

        self.assertRaises(
                    exceptions.PermissionDenied,
                    user.assert_can_edit_post,
                    self.post
                )
        self.assertFalse(
            template_filters.can_edit_post(user, self.post)
        )

    def assert_other_can(self):
        self.assert_user_can(user = self.other_user)

    def assert_other_cannot(self):
        self.assert_user_cannot(user = self.other_user)

    def test_admin_can_edit(self):
        self.other_user.set_admin_status()
        self.other_user.save()
        self.assert_other_can()

    def test_admin_can_edit_deleted(self):
        self.post.deleted = True
        self.other_user.set_admin_status()
        self.other_user.save()
        self.assert_other_can()

    def test_mod_can_edit(self):
        self.other_user.set_status('m')
        self.assert_other_can()

    def test_low_rep_user_cannot_edit_others_post(self):
        assert(self.other_user.reputation < self.min_rep)
        self.assert_other_cannot()

    def test_low_rep_user_cannot_edit_others_wiki(self):
        self.post.wiki = True
        assert(self.other_user.reputation < self.min_rep_wiki)
        self.assert_other_cannot()

    def test_low_rep_user_can_edit_own_wiki(self):
        self.post.wiki = True
        self.assert_user_can()

    def test_medium_rep_user_can_edit_others_wiki(self):
        self.post.wiki = True
        self.other_user.reputation = self.min_rep_wiki
        self.assert_other_can()

    def test_high_rep_user_can_edit_others_post(self):
        self.other_user.reputation = self.min_rep
        self.assert_other_can()

    #def test_medium_rep_user_can_edit_others_wiki(self):
    #def test_low_rep_user_can_edit_own_wiki(self):
    #def test_low_rep_user_cannot_edit_others_wiki(self):
    #def test_high_rep_blocked_cannot_edit_others_wiki(self):
    def test_medium_rep_user_cannot_edit_others_post(self):
        self.other_user.reputation = self.min_rep_wiki
        self.assert_other_cannot()

    def test_high_rep_user_cannot_edit_others_deleted_post(self):
        self.other_user.reputation = self.min_rep
        self.post.deleted = True
        self.assert_other_cannot()

    def test_high_rep_user_cannot_edit_others_deleted_wiki(self):
        self.other_user.reputation = self.min_rep
        self.post.deleted = True
        self.post.wiki = True
        self.assert_other_cannot()

    def test_low_rep_suspended_can_edit_own_post(self):
        self.user.set_status('s')
        assert(self.user.reputation < self.min_rep)
        self.assert_user_can()

    def test_low_rep_suspended_can_edit_own_deleted_post(self):
        self.user.set_status('s')
        self.post.deleted = True
        self.assert_user_can()

    def test_high_rep_suspended_cannot_edit_others_deleted_post(self):
        self.other_user.reputation = self.min_rep
        self.other_user.set_status('s')
        self.post.deleted = True
        self.assert_other_cannot()

    def test_high_rep_suspended_cannot_edit_others_post(self):
        self.other_user.set_status('s')
        self.other_user.reputation = self.min_rep
        self.assert_other_cannot()

    def test_high_rep_blocked_cannot_edit_own_post(self):
        self.user.set_status('b')
        self.user.reputation = self.min_rep
        self.assert_user_cannot()

    def test_high_rep_blocked_cannot_edit_others_post(self):
        self.user.set_status('b')
        self.user.reputation = self.min_rep
        self.assert_user_cannot()

    def test_high_rep_blocked_cannot_edit_others_deleted_post(self):
        self.other_user.set_status('b')
        self.other_user.reputation = self.min_rep
        self.post.deleted = True
        self.assert_other_cannot()

    def test_high_rep_blocked_cannot_edit_others_wiki(self):
        self.other_user.set_status('b')
        self.other_user.reputation = self.min_rep
        self.post.wiki = True
        self.assert_other_cannot()

class EditProblemPermissionAssertionTests(
            EditExercisePermissionAssertionTests
        ):
    def setUp(self):
        super(
                EditProblemPermissionAssertionTests,
                self,
            ).setUp()
        self.post = self.post_problem(exercise = self.post)

    def assert_user_can(
                    self,
                    user = None,
                ):
        if user is None:
            user = self.user

        user.assert_can_edit_problem(self.post)
        self.assertTrue(
            template_filters.can_edit_post(user, self.post)
        )

    def assert_user_cannot(
                    self,
                    user = None,
                ):
        if user is None:
            user = self.user

        self.assertRaises(
                    exceptions.PermissionDenied,
                    user.assert_can_edit_problem,
                    self.post
                )
        self.assertFalse(
            template_filters.can_edit_post(user, self.post)
        )


class RetagExercisePermissionAssertionTests(
            EditExercisePermissionAssertionTests
        ):

    def setUp(self):
        super(
                RetagExercisePermissionAssertionTests,
                self,
            ).setUp()
        self.min_rep = askbot_settings.MIN_REP_TO_RETAG_OTHERS_EXERCISES

    def assert_user_can(
                    self,
                    user = None,
                ):
        if user is None:
            user = self.user

        user.assert_can_retag_exercise(self.post)
        self.assertTrue(
            template_filters.can_retag_exercise(user, self.post)
        )

    def assert_user_cannot(
                    self,
                    user = None,
                ):
        if user is None:
            user = self.user

        self.assertRaises(
                    exceptions.PermissionDenied,
                    user.assert_can_retag_exercise,
                    self.post
                )
        self.assertFalse(
            template_filters.can_edit_post(user, self.post)
        )
    def test_medium_rep_user_can_edit_others_wiki(self):
        pass
    def test_low_rep_user_can_edit_own_wiki(self):
        pass
    def test_low_rep_user_cannot_edit_others_wiki(self):
        pass
    def test_high_rep_blocked_cannot_edit_others_wiki(self):
        pass
    def test_medium_rep_user_cannot_edit_others_post(self):
        pass

class FlagOffensivePermissionAssertionTests(PermissionAssertionTestCase):

    def extraSetUp(self):
        self.min_rep = askbot_settings.MIN_REP_TO_FLAG_OFFENSIVE
        self.exercise = self.post_exercise()
        self.problem = self.post_problem(exercise = self.exercise)

    def assert_user_cannot_flag(self):
        self.assertRaises(
            exceptions.PermissionDenied,
            self.user.flag_post,
            post = self.exercise
        )
        self.assertFalse(
            template_filters.can_flag_offensive(
                self.user,
                self.exercise
            )
        )
        self.assertRaises(
            exceptions.PermissionDenied,
            self.user.flag_post,
            post = self.problem
        )
        self.assertFalse(
            template_filters.can_flag_offensive(
                self.user,
                self.problem
            )
        )

    def assert_user_can_flag(self):
        self.user.flag_post(post = self.exercise)
        self.assertTrue(
            template_filters.can_flag_offensive(
                self.user,
                self.exercise
            )
        )
        self.user.flag_post(post = self.problem)
        self.assertTrue(
            template_filters.can_flag_offensive(
                self.user,
                self.problem
            )
        )

    def setup_high_rep(self):
        #there is a catch - assert_user_can_flag
        #flags twice and each time user reputation
        #suffers a hit, so test may actually fail
        #set amply high reputation
        extra_rep = -100 * askbot_settings.REP_LOSS_FOR_RECEIVING_FLAG
        #NB: REP_LOSS is negative
        self.user.reputation = self.min_rep + extra_rep
        self.user.save()

    def test_high_rep_user_cannot_exceed_max_flags_per_day(self):
        max_flags = askbot_settings.MAX_FLAGS_PER_USER_PER_DAY
        other_user = self.create_other_user()
        other_user.reputation = self.min_rep
        for i in range(max_flags):
            exercise = self.post_exercise()
            other_user.flag_post(exercise)
        exercise = self.post_exercise()
        self.assertRaises(
            exceptions.PermissionDenied,
            other_user.flag_post,
            exercise
        )

    def test_admin_has_no_limit_for_flags_per_day(self):
        max_flags = askbot_settings.MAX_FLAGS_PER_USER_PER_DAY
        other_user = self.create_other_user()
        other_user.set_admin_status()
        other_user.save()
        for i in range(max_flags + 1):
            exercise = self.post_exercise()
            other_user.flag_post(exercise)

    def test_moderator_has_no_limit_for_flags_per_day(self):
        max_flags = askbot_settings.MAX_FLAGS_PER_USER_PER_DAY
        other_user = self.create_other_user()
        other_user.set_status('m')
        for i in range(max_flags + 1):
            exercise = self.post_exercise()
            other_user.flag_post(exercise)

    def test_low_rep_user_cannot_flag(self):
        assert(self.user.reputation < self.min_rep)
        self.assert_user_cannot_flag()

    def test_high_rep_blocked_or_suspended_user_cannot_flag(self):
        self.setup_high_rep()
        self.user.set_status('b')
        self.assert_user_cannot_flag()
        self.user.set_status('s')
        self.assert_user_cannot_flag()

    def test_high_rep_user_can_flag(self):
        self.setup_high_rep()
        self.assert_user_can_flag()

    def test_low_rep_moderator_can_flag(self):
        assert(self.user.reputation < self.min_rep)
        self.user.set_status('m')
        self.assert_user_can_flag()

    def low_rep_administrator_can_flag(self):
        assert(self.user.reputation < self.min_rep)
        self.user.set_admin_status()
        self.assert_user_can_flag()

    def test_superuser_cannot_flag_exercise_twice(self):
        self.user.set_admin_status()
        self.user.save()
        self.user.flag_post(post = self.exercise)
        self.assertRaises(
            exceptions.PermissionDenied,
            self.user.flag_post,
            post = self.exercise
        )
        #here is a deviation - the link will still be shown
        #in templates
        self.assertTrue(
            template_filters.can_flag_offensive(
                self.user,
                self.exercise
            )
        )

    def test_superuser_cannot_flag_problem_twice(self):
        self.user.set_admin_status()
        self.user.save()
        self.user.flag_post(post = self.problem)
        self.assertRaises(
            exceptions.PermissionDenied,
            self.user.flag_post,
            post = self.problem
        )
        self.assertTrue(
            template_filters.can_flag_offensive(
                self.user,
                self.problem
            )
        )

    def test_high_rep_user_cannot_flag_exercise_twice(self):
        self.user.reputation = self.min_rep
        self.user.flag_post(post = self.exercise)
        self.assertRaises(
            exceptions.PermissionDenied,
            self.user.flag_post,
            post = self.exercise
        )
        self.assertTrue(
            template_filters.can_flag_offensive(
                self.user,
                self.exercise
            )
        )

    def test_high_rep_user_cannot_flag_problem_twice(self):
        self.user.reputation = self.min_rep
        self.user.flag_post(post = self.problem)
        self.assertRaises(
            exceptions.PermissionDenied,
            self.user.flag_post,
            post = self.problem
        )
        self.assertTrue(
            template_filters.can_flag_offensive(
                self.user,
                self.problem
            )
        )


class CommentPermissionAssertionTests(PermissionAssertionTestCase):

    def extraSetUp(self):
        self.min_rep = askbot_settings.MIN_REP_TO_LEAVE_COMMENTS
        self.other_user = self.create_other_user()

    def test_blocked_user_cannot_comment_own_exercise(self):
        exercise = self.post_exercise()

        self.user.set_status('b')
        self.assertRaises(
                    exceptions.PermissionDenied,
                    self.user.post_comment,
                    parent_post = exercise,
                    body_text = 'test comment'
                )
        self.assertFalse(
                template_filters.can_post_comment(
                    self.user,
                    exercise
                )
            )

    def test_blocked_user_cannot_comment_own_problem(self):
        exercise = self.post_exercise()
        problem = self.post_problem(exercise)

        self.user.set_status('b')

        self.assertRaises(
                    exceptions.PermissionDenied,
                    self.user.post_comment,
                    parent_post = problem,
                    body_text = 'test comment'
                )
        self.assertFalse(
                template_filters.can_post_comment(
                        self.user,
                        problem
                    )
            )

    def test_blocked_user_cannot_delete_own_comment(self):
        exercise = self.post_exercise()
        comment = self.user.post_comment(
                        parent_post = exercise,
                        body_text = 'test comment'
                    )
        self.user.set_status('b')
        self.assertRaises(
            exceptions.PermissionDenied,
            self.user.delete_post,
            post = comment
        )
        self.assertFalse(
            template_filters.can_delete_comment(
                self.user, 
                comment
            )
        )

    def test_low_rep_user_cannot_delete_others_comment(self):
        exercise = self.post_exercise()
        comment = self.user.post_comment(
                        parent_post = exercise,
                        body_text = 'test comment'
                    )
        assert(
            self.other_user.reputation < \
            askbot_settings.MIN_REP_TO_DELETE_OTHERS_COMMENTS
        )
        self.assertRaises(
            exceptions.PermissionDenied,
            self.other_user.delete_post,
            post = comment
        )
        self.assertFalse(
            template_filters.can_delete_comment(
                self.other_user, 
                comment
            )
        )

    def test_high_rep_user_can_delete_comment(self):
        exercise = self.post_exercise()
        comment = self.user.post_comment(
                        parent_post = exercise,
                        body_text = 'test comment'
                    )
        self.other_user.reputation = \
            askbot_settings.MIN_REP_TO_DELETE_OTHERS_COMMENTS

        self.other_user.delete_comment(comment)
        self.assertTrue(
            template_filters.can_delete_comment(
                self.other_user, 
                comment
            )
        )

    def test_low_rep_user_can_delete_own_comment(self):
        exercise = self.post_exercise()
        problem = self.other_user.post_problem(
                        exercise = exercise,
                        body_text = 'test problem'
                    )
        comment = self.user.post_comment(
                        parent_post = problem,
                        body_text = 'test comment'
                    )
        assert(
            self.user.reputation < \
            askbot_settings.MIN_REP_TO_DELETE_OTHERS_COMMENTS
        )
        self.user.delete_comment(comment)
        self.assertTrue(
            template_filters.can_delete_comment(
                self.user, 
                comment
            )
        )

    def test_moderator_can_delete_comment(self):
        exercise = self.post_exercise()
        comment = self.user.post_comment(
                        parent_post = exercise,
                        body_text = 'test comment'
                    )
        self.other_user.set_status('m')
        self.other_user.delete_comment(comment)
        self.assertTrue(
            template_filters.can_delete_comment(
                self.other_user, 
                comment
            )
        )

    def test_admin_can_delete_comment(self):
        exercise = self.post_exercise()
        comment = self.user.post_comment(
                        parent_post = exercise,
                        body_text = 'test comment'
                    )
        self.other_user.set_admin_status()
        self.other_user.save()
        self.other_user.delete_comment(comment)
        self.assertTrue(
            template_filters.can_delete_comment(
                self.other_user, 
                comment
            )
        )

    def test_high_rep_suspended_user_cannot_delete_others_comment(self):
        exercise = self.post_exercise()
        comment = self.user.post_comment(
                        parent_post = exercise,
                        body_text = 'test comment'
                    )
        self.other_user.reputation = \
            askbot_settings.MIN_REP_TO_DELETE_OTHERS_COMMENTS + 1
        self.other_user.set_status('s')
        self.assertRaises(
                exceptions.PermissionDenied,
                self.other_user.delete_post,
                post = comment
            )
        self.assertFalse(
            template_filters.can_delete_comment(
                self.other_user, 
                comment
            )
        )

    def test_suspended_user_can_delete_own_comment(self):
        exercise = self.post_exercise()
        comment = self.user.post_comment(
                        parent_post = exercise,
                        body_text = 'test comment'
                    )
        self.user.set_status('s')
        self.user.delete_comment(comment)
        self.assertTrue(
            template_filters.can_delete_comment(
                self.user, 
                comment
            )
        )

    def test_low_rep_user_cannot_comment_others(self):
        exercise = self.post_exercise(
                            author = self.other_user
                        )
        assert(self.user.reputation < self.min_rep)
        self.assertRaises(
                    exceptions.PermissionDenied,
                    self.user.post_comment,
                    parent_post = exercise,
                    body_text = 'test comment'
                )
        self.assertFalse(
                template_filters.can_post_comment(
                    self.user,
                    exercise
                )
            )

    def test_low_rep_user_can_comment_others_problem_to_own_exercise(self):
        exercise = self.post_exercise()
        assert(self.user.reputation < self.min_rep)
        problem = self.other_user.post_problem(
                        exercise = exercise,
                        body_text = 'test problem'
                    )
        comment = self.user.post_comment(
                                    parent_post = problem,
                                    body_text = 'test comment'
                                )
        self.assertTrue(isinstance(comment, models.Post) and comment.is_comment())
        self.assertTrue(
            template_filters.can_post_comment(
                self.user,
                problem
            )
        )

    def test_high_rep_user_can_comment(self):
        exercise = self.post_exercise(
                            author = self.other_user
                        )
        self.user.reputation = self.min_rep
        comment = self.user.post_comment(
                            parent_post = exercise,
                            body_text = 'test comment'
                        )
        self.assertTrue(isinstance(comment, models.Post) and comment.is_comment())
        self.assertTrue(
            template_filters.can_post_comment(
                self.user,
                exercise
            )
        )

    def test_suspended_user_cannot_comment_others_exercise(self):
        exercise = self.post_exercise(author = self.other_user)
        self.user.set_status('s')
        self.assertRaises(
                exceptions.PermissionDenied,
                self.user.post_comment,
                parent_post = exercise,
                body_text = 'test comment'
            )
        self.assertFalse(
            template_filters.can_post_comment(
                self.user,
                exercise
            )
        )

    def test_suspended_user_can_comment_own_exercise(self):
        exercise = self.post_exercise()
        self.user.set_status('s')
        comment = self.user.post_comment(
                            parent_post = exercise,
                            body_text = 'test comment'
                        )
        self.assertTrue(isinstance(comment, models.Post) and comment.is_comment())
        self.assertTrue(
            template_filters.can_post_comment(
                self.user,
                exercise
            )
        )

    def test_low_rep_admin_can_comment_others_exercise(self):
        exercise = self.post_exercise()
        self.other_user.set_admin_status()
        self.other_user.save()
        assert(self.other_user.is_administrator())
        assert(self.other_user.reputation < self.min_rep)
        comment = self.other_user.post_comment(
                            parent_post = exercise,
                            body_text = 'test comment'
                        )
        self.assertTrue(isinstance(comment, models.Post) and comment.is_comment())
        self.assertTrue(
            template_filters.can_post_comment(
                self.other_user,
                exercise
            )
        )

    def test_low_rep_moderator_can_comment_others_exercise(self):
        exercise = self.post_exercise()
        self.other_user.set_status('m')
        assert(self.other_user.is_moderator())
        assert(self.other_user.reputation < self.min_rep)
        comment = self.other_user.post_comment(
                            parent_post = exercise,
                            body_text = 'test comment'
                        )
        self.assertTrue(isinstance(comment, models.Post) and comment.is_comment())
        self.assertTrue(
            template_filters.can_post_comment(
                self.other_user,
                exercise
            )
        )

    def assert_user_can_edit_previous_comment(
                                            self,
                                            old_timestamp = None,
                                            original_poster = None
                                        ):
        """oriposts a exercise and a comment at
        an old timestamp, then posts another comment now
        then user tries to edit the first comment
        """
        self.other_user.set_admin_status()
        self.other_user.save()

        if original_poster is None:
            original_poster = self.user

        exercise = self.post_exercise(
                            author = original_poster,
                            timestamp = old_timestamp
                        )
        comment1 = original_poster.post_comment(
                                    parent_post = exercise,
                                    timestamp = old_timestamp,
                                    body_text = 'blah'
                                )
        comment2 = self.other_user.post_comment(#post this one with the current timestamp
                                    parent_post = exercise,
                                    body_text = 'blah'
                                )
        self.user.assert_can_edit_comment(comment1)

    def assert_user_can_edit_very_old_comment(self, original_poster = None):
        """tries to edit comment in the most restictive situation
        """
        askbot_settings.update('USE_TIME_LIMIT_TO_EDIT_COMMENT', True)
        askbot_settings.update('MINUTES_TO_EDIT_COMMENT', 0)
        old_timestamp = datetime.datetime.now() - datetime.timedelta(1)
        self.assert_user_can_edit_previous_comment(
                                    old_timestamp = old_timestamp,
                                    original_poster = original_poster
                                )


    def test_admin_can_edit_very_old_comment(self):
        self.user.set_admin_status()
        self.user.save()
        self.assert_user_can_edit_very_old_comment(original_poster = self.other_user)

    def test_moderator_can_edit_very_old_comment(self):
        self.user.set_status('m')
        self.user.save()
        self.assert_user_can_edit_very_old_comment(original_poster = self.other_user)

    def test_regular_user_cannot_edit_very_old_comment(self):
        self.assertRaises(
            exceptions.PermissionDenied,
            self.assert_user_can_edit_very_old_comment,
            original_poster = self.user
        )

    def test_regular_user_can_edit_reasonably_old_comment(self):
        self.user.set_status('a')
        self.user.save()
        askbot_settings.update('USE_TIME_LIMIT_TO_EDIT_COMMENT', True)
        askbot_settings.update('MINUTES_TO_EDIT_COMMENT', 10)
        #about 3 min ago
        old_timestamp = datetime.datetime.now() - datetime.timedelta(0, 200)
        self.assert_user_can_edit_previous_comment(
                                old_timestamp = old_timestamp,
                                original_poster = self.user
                            )

    def test_disable_comment_edit_time_limit(self):
        self.user.set_status('a')
        self.user.save()
        askbot_settings.update('USE_TIME_LIMIT_TO_EDIT_COMMENT', False)
        askbot_settings.update('MINUTES_TO_EDIT_COMMENT', 10)
        old_timestamp = datetime.datetime.now() - datetime.timedelta(365)#a year ago
        self.assert_user_can_edit_previous_comment(
                                old_timestamp = old_timestamp,
                                original_poster = self.user
                            )


    def test_regular_user_can_edit_last_comment(self):
        """and a very old last comment"""
        self.user.set_status('a')
        self.user.save()
        askbot_settings.update('USE_TIME_LIMIT_TO_EDIT_COMMENT', True)
        askbot_settings.update('MINUTES_TO_EDIT_COMMENT', 10)
        old_timestamp = datetime.datetime.now() - datetime.timedelta(1)
        exercise = self.post_exercise(author = self.user, timestamp = old_timestamp)
        comment = self.user.post_comment(
                                    parent_post = exercise,
                                    body_text = 'blah',
                                    timestamp = old_timestamp
                                )
        self.user.assert_can_edit_comment(comment)

#def user_assert_can_post_comment(self, parent_post):
#def user_assert_can_delete_comment(self, comment = None):

#def user_assert_can_vote_for_post(
#def user_assert_can_revoke_old_vote(self, vote):

#def user_assert_can_flag_offensive(self):

#def user_assert_can_upload_file(request_user):
#def user_assert_can_post_exercise(self):
#def user_assert_can_post_problem(self):
#def user_assert_can_edit_post(self, post = None):
#def user_assert_can_delete_Post(self, post = None):
#def user_assert_can_close_exercise(self, exercise = None):
#def user_assert_can_retag_exercises(self):

class AcceptBestProblemPermissionAssertionTests(utils.AskbotTestCase):

    def setUp(self):
        self.create_user()
        self.create_user(username = 'other_user')
        self.exercise = self.post_exercise()

    def other_post_problem(self):
        self.problem = self.post_problem(
                                exercise = self.exercise,
                                user = self.other_user
                            )

    def user_post_problem(self):
        self.problem = self.post_problem(
                                exercise = self.exercise,
                                user = self.user
                            )

    def assert_user_can(self, user = None):
        if user is None:
            user = self.user
        user.assert_can_accept_best_problem(self.problem)

    def assert_user_cannot(self, user = None):
        if user is None:
            user = self.user
        self.assertRaises(
            exceptions.PermissionDenied,
            user.assert_can_accept_best_problem,
            problem = self.problem
        )

    def test_exercise_owner_can_accept_others_problem(self):
        self.other_post_problem()
        self.assert_user_can()

    def test_suspended_exercise_owner_cannot_accept_others_problem(self):
        self.other_post_problem()
        self.user.set_status('s')
        self.assert_user_cannot()

    def test_blocked_exercise_owner_cannot_accept_others_problem(self):
        self.other_post_problem()
        self.user.set_status('b')
        self.assert_user_cannot()

    def test_problem_owner_cannot_accept_problem(self):
        self.other_post_problem()
        self.assert_user_cannot(user = self.other_user)

    def test_exercise_and_problem_owner_cannot_accept_problem(self):
        self.user_post_problem()
        self.assert_user_cannot()

    def test_low_rep_other_user_cannot_accept_problem(self):
        self.other_post_problem()
        self.create_user(username = 'third_user')
        self.third_user.reputation = askbot_settings.MIN_REP_TO_ACCEPT_ANY_PROBLEM - 1
        self.assert_user_cannot(user = self.third_user)

    @with_settings(MIN_DAYS_FOR_STAFF_TO_ACCEPT_PROBLEM=0)
    def test_high_rep_other_user_can_accept_problem(self):
        self.other_post_problem()
        self.create_user(username = 'third_user')
        self.third_user.reputation = askbot_settings.MIN_REP_TO_ACCEPT_ANY_PROBLEM
        self.assert_user_can(user = self.third_user)

    def test_moderator_cannot_accept_own_problem(self):
        self.other_post_problem()
        self.other_user.set_status('m')
        self.assert_user_cannot(user = self.other_user)

    def test_moderator_cannot_accept_others_problem_today(self):
        self.other_post_problem()
        self.create_user(username = 'third_user')
        self.third_user.set_status('m')
        self.assert_user_cannot(user = self.third_user)

    def test_moderator_can_accept_others_old_problem(self):
        self.other_post_problem()
        self.problem.added_at -= datetime.timedelta(
            days = askbot_settings.MIN_DAYS_FOR_STAFF_TO_ACCEPT_PROBLEM + 1
        )
        self.problem.save()
        self.create_user(username = 'third_user')
        self.third_user.set_admin_status()
        self.third_user.save()
        self.assert_user_can(user = self.third_user)

    def test_admin_cannot_accept_own_problem(self):
        self.other_post_problem()
        self.other_user.set_admin_status()
        self.other_user.save()
        self.assert_user_cannot(user = self.other_user)

    def test_admin_cannot_accept_others_problem_today(self):
        self.other_post_problem()
        self.create_user(username = 'third_user')
        self.third_user.set_admin_status()
        self.third_user.save()
        self.assert_user_cannot(user = self.third_user)

    def test_admin_can_accept_others_old_problem(self):
        self.other_post_problem()
        self.problem.added_at -= datetime.timedelta(
            days = askbot_settings.MIN_DAYS_FOR_STAFF_TO_ACCEPT_PROBLEM + 1
        )
        self.problem.save()
        self.create_user(username = 'third_user')
        self.third_user.set_admin_status()
        self.third_user.save()
        self.assert_user_can(user = self.third_user)

class VotePermissionAssertionTests(PermissionAssertionTestCase):
    """Tests permission for voting
    """
    def extraSetUp(self):
        self.min_rep_up = askbot_settings.MIN_REP_TO_VOTE_UP
        self.min_rep_down = askbot_settings.MIN_REP_TO_VOTE_DOWN
        self.other_user = self.create_other_user()

    def assert_cannot_vote(self, user = None, dir = None):
        assert(dir in ('up', 'down'))

        vote_func = self.get_vote_function(
                                        user = user, 
                                        dir = dir
                                    )

        self.assertRaises(
                exceptions.PermissionDenied,
                vote_func,
                self.exercise,
            )
        self.assertRaises(
                exceptions.PermissionDenied,
                vote_func,
                self.problem,
            )

    def prepare_data(self, status = 'a', rep = 1):
        self.exercise = self.post_exercise()
        self.problem = self.post_problem(exercise = self.exercise)
        self.other_user.reputation = rep
        self.other_user.set_status(status)

    def bad_user_cannot_vote(self, status = 'a', rep = 1, dir = 'up'):
        """dir - vote direction up/down
        rep - reputation
        """
        self.prepare_data(status = status)

        self.assert_cannot_vote(
                        user = self.other_user,
                        dir = dir
                    )

    def get_vote_function(self, dir = None, user = None):

        def vote_func(post):
            user.assert_can_vote_for_post(post = post, direction = dir)
        
        return vote_func


    def good_user_can_vote(self, user = None, dir = 'up'):

        if user is None:
            user = self.other_user

        vote_func = self.get_vote_function(dir = dir, user = user)

        vote_func(self.exercise)
        vote_func(self.problem)


    def test_blocked_user_cannot_vote(self):
        self.bad_user_cannot_vote(status = 'b')

    def test_suspended_user_cannot_vote(self):
        self.bad_user_cannot_vote(status = 's')

    def test_low_rep_user_cannot_upvote(self):
        self.bad_user_cannot_vote(dir = 'up')

    def test_low_rep_user_cannot_downvote(self):
        self.bad_user_cannot_vote(dir = 'down')

    def test_high_rep_user_can_upvote(self):
        self.prepare_data(rep = self.min_rep_up)
        self.good_user_can_vote(dir = 'up')

    def test_high_rep_user_can_downvote(self):
        self.prepare_data(rep = self.min_rep_down)
        self.good_user_can_vote(dir = 'down')

    def test_low_rep_admins_can_upvote_others(self):
        self.prepare_data()
        self.other_user.set_status('m')
        self.good_user_can_vote(dir = 'up')

    def test_low_rep_admins_can_downvote_others(self):
        self.prepare_data()
        self.other_user.set_status('m')
        self.good_user_can_vote(dir = 'down')

    def test_admins_cannot_upvote_self(self):
        self.prepare_data()
        self.user.set_status('m')
        self.assert_cannot_vote(
                user = self.user,
                dir = 'up'
            )

    def test_admins_cannot_downvote_self(self):
        self.prepare_data()
        self.user.set_status('m')
        self.assert_cannot_vote(
                user = self.user,
                dir = 'down'
            )

class UploadPermissionAssertionTests(PermissionAssertionTestCase):
    """Tests permissions for file uploads
    """

    def extraSetUp(self):
        self.min_rep = askbot_settings.MIN_REP_TO_UPLOAD_FILES

    def test_suspended_user_cannot_upload(self):
        self.user.set_status('s')
        self.assertRaises(
                    exceptions.PermissionDenied,
                    self.user.assert_can_upload_file
                )

    def test_blocked_user_cannot_upload(self):
        self.user.set_status('b')
        self.assertRaises(
                    exceptions.PermissionDenied,
                    self.user.assert_can_upload_file
                )
    def test_low_rep_user_cannot_upload(self):
        self.user.reputation = self.min_rep - 1
        self.assertRaises(
                    exceptions.PermissionDenied,
                    self.user.assert_can_upload_file
                )

    def test_high_rep_user_can_upload(self):
        self.user.reputation = self.min_rep
        try:
            self.user.assert_can_upload_file()
        except exceptions.PermissionDenied:
            self.fail('high rep user must be able to upload')

    def test_low_rep_moderator_can_upload(self):
        assert(self.user.reputation < self.min_rep)
        self.user.set_status('m')
        try:
            self.user.assert_can_upload_file()
        except exceptions.PermissionDenied:
            self.fail('high rep user must be able to upload')

    def test_low_rep_administrator_can_upload(self):
        assert(self.user.reputation < self.min_rep)
        self.user.set_admin_status()
        self.user.save()
        try:
            self.user.assert_can_upload_file()
        except exceptions.PermissionDenied:
            self.fail('high rep user must be able to upload')

class ClosedForumTests(utils.AskbotTestCase):
    def setUp(self):
        self.password = '123'
        self.create_user()
        self.create_user(username = 'other_user')
        self.other_user.set_password(self.password)
        self.other_user.save()
        self.exercise = self.post_exercise()
        self.test_url = self.exercise.get_absolute_url()
        self.redirect_to = settings.LOGIN_URL
        self.client = Client()
        askbot_settings.update('ASKBOT_CLOSED_FORUM_MODE', True)

    def tearDown(self):
        askbot_settings.update('ASKBOT_CLOSED_FORUM_MODE', False)

    @skipIf('askbot.middleware.forum_mode.ForumModeMiddleware' \
        not in settings.MIDDLEWARE_CLASSES,
        'no ForumModeMiddleware set')
    def test_login_page_accessable(self):
        # futher see in page_load_tests.py
        response = self.client.get(reverse('user_signin'))
        self.assertEquals(response.status_code, 200)

    @skipIf('askbot.middleware.forum_mode.ForumModeMiddleware' \
        not in settings.MIDDLEWARE_CLASSES,
        'no ForumModeMiddleware set')
    def test_anonymous_access(self):
        response = self.client.get(self.test_url)
        self.assertEquals(response.status_code, 302)
        self.assertTrue(self.redirect_to in response['Location'])

    @skipIf('askbot.middleware.forum_mode.ForumModeMiddleware' \
        not in settings.MIDDLEWARE_CLASSES,
        'no ForumModeMiddleware set')
    def test_authenticated_access(self):
        self.client.login(username=self.other_user.username, password=self.password)
        response = self.client.get(self.test_url)
        self.assertEquals(response.status_code, 200)
