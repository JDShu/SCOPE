from django.db import connection
from django.core.urlresolvers import reverse
from django.conf import settings
from askbot.tests.utils import AskbotTestCase


class CacheTests(AskbotTestCase):
    def setUp(self):
        user = self.create_user('other_user')
        self.exercise = self.post_exercise(user=user)
        self.post_problem(user=user, exercise=self.exercise)
        settings.DEBUG = True  # because it's forsed to False

    def visit_exercise(self):
        self.client.get(self.exercise.get_absolute_url(), follow=True)
        
    def test_anonymous_exercise_cache(self):

        self.visit_exercise()
        counter = len(connection.queries)
        print 'we have %d queries' % counter
        self.visit_exercise()

        #second hit to the same exercise should give fewer queries
        self.assertTrue(counter > len(connection.queries))
        settings.DEBUG = False
