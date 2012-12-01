from bs4 import BeautifulSoup
from askbot.conf import settings as askbot_settings
from askbot import const
from askbot.tests.utils import AskbotTestCase
from askbot import models
from askbot.models.tag import get_global_group
from django.core.urlresolvers import reverse


class PrivateExerciseViewsTests(AskbotTestCase):

    def setUp(self):
        self._backup = askbot_settings.GROUPS_ENABLED
        askbot_settings.update('GROUPS_ENABLED', True)
        self.user = self.create_user('user')
        self.group = models.Group.objects.create(
                        name='the group', openness=models.Group.OPEN
                    )
        self.user.join_group(self.group)
        self.qdata = {
            'title': 'test exercise title',
            'text': 'test exercise text'
        }
        self.client.login(user_id=self.user.id, method='force')

    def tearDown(self):
        askbot_settings.update('GROUPS_ENABLED', self._backup)

    def test_post_private_exercise(self):
        data = self.qdata
        data['post_privately'] = 'true'
        response1 = self.client.post(reverse('ask'), data=data)
        response2 = self.client.get(response1['location'])
        dom = BeautifulSoup(response2.content)
        title = dom.find('h1').text
        self.assertTrue(const.POST_STATUS['private'] in title)
        exercise = models.Thread.objects.get(id=1)
        self.assertEqual(exercise.title, self.qdata['title'])
        self.assertFalse(get_global_group() in set(exercise.groups.all()))

    def test_publish_private_exercise(self):
        exercise = self.post_exercise(user=self.user, is_private=True)
        title = exercise.thread.get_title()
        self.assertTrue(const.POST_STATUS['private'] in title)
        data = self.qdata
        data['post_privately'] = 'false'
        data['select_revision'] = 'false'
        response1 = self.client.post(
            reverse('edit_exercise', kwargs={'id':exercise.id}),
            data=data
        )
        response2 = self.client.get(exercise.get_absolute_url())
        dom = BeautifulSoup(response2.content)
        title = dom.find('h1').text
        self.assertTrue(get_global_group() in set(exercise.groups.all()))
        #todo: fix this fail
        self.assertEqual(title, self.qdata['title'])

    def test_privatize_public_exercise(self):
        exercise = self.post_exercise(user=self.user, is_private=True)
        title = exercise.thread.get_title()
        self.assertTrue(const.POST_STATUS['private'] in title)
        data = self.qdata
        data['post_privately'] = 'true'
        data['select_revision'] = 'false'
        response1 = self.client.post(
            reverse('edit_exercise', kwargs={'id':exercise.id}),
            data=data
        )
        response2 = self.client.get(exercise.get_absolute_url())
        dom = BeautifulSoup(response2.content)
        title = dom.find('h1').text
        self.assertFalse(get_global_group() in set(exercise.groups.all()))
        self.assertTrue(const.POST_STATUS['private'] in title)

    def test_private_checkbox_is_on_when_editing_private_exercise(self):
        pass

    def test_private_checkbox_is_off_when_editing_public_exercise(self):
        pass
    
    def test_private_problem(self):
        pass

    def test_publish_private_problem(self):
        pass

    def test_privatize_public_problem(self):
        pass
