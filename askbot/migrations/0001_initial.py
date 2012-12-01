# encoding: utf-8
import os
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from askbot.migrations_api import safe_add_column

app_dir_name = os.path.basename(os.path.dirname(os.path.dirname(__file__)))

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        #1) patch the existing auth_user table
        safe_add_column('auth_user', 'website', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True, null=True), keep_default = False)
        safe_add_column('auth_user', 'about', self.gf('django.db.models.fields.TextField')(blank=True, null=True), keep_default = False)
        safe_add_column('auth_user', 'hide_ignored_exercises', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True), keep_default = False)
        safe_add_column('auth_user', 'gold', self.gf('django.db.models.fields.SmallIntegerField')(default=0), keep_default = False)
        safe_add_column('auth_user', 'email_isvalid', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True), keep_default = False)
        safe_add_column('auth_user', 'real_name', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True, null=True), keep_default = False)
        safe_add_column('auth_user', 'location', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True, null=True), keep_default = False)
        safe_add_column('auth_user', 'email_key', self.gf('django.db.models.fields.CharField')(max_length=32, null=True), keep_default = False)
        safe_add_column('auth_user', 'date_of_birth', self.gf('django.db.models.fields.DateField')(null=True, blank=True), keep_default = False)
        safe_add_column('auth_user', 'reputation', self.gf('django.db.models.fields.PositiveIntegerField')(default=1), keep_default = False)
        safe_add_column('auth_user', 'gravatar', self.gf('django.db.models.fields.CharField')(max_length=32, null=True), keep_default = False)
        safe_add_column('auth_user', 'bronze', self.gf('django.db.models.fields.SmallIntegerField')(default=0), keep_default = False)
        safe_add_column('auth_user', 'tag_filter_setting', self.gf('django.db.models.fields.CharField')(default='ignored', max_length=16), keep_default = False)
        safe_add_column('auth_user', 'last_seen', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now), keep_default = False)
        safe_add_column('auth_user', 'silver', self.gf('django.db.models.fields.SmallIntegerField')(default=0), keep_default = False),
        safe_add_column('auth_user', 'exercises_per_page', self.gf('django.db.models.fields.SmallIntegerField')(default=10), keep_default = False),
        safe_add_column('auth_user', 'response_count', self.gf('django.db.models.fields.IntegerField')(default=0), keep_default=False)

        # Adding model 'Vote'
        if app_dir_name == 'forum':
            db.create_table(u'vote', (
                ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
                ('voted_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
                ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='votes', to=orm['auth.User'])),
                ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
                ('vote', self.gf('django.db.models.fields.SmallIntegerField')()),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ))
            db.send_create_signal('forum', ['Vote'])

            # Adding unique constraint on 'Vote', fields ['content_type', 'object_id', 'user']
            db.create_unique(u'vote', ['content_type_id', 'object_id', 'user_id'])

            # Adding model 'FlaggedItem'
            db.create_table(u'flagged_item', (
                ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
                ('flagged_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
                ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='flaggeditems', to=orm['auth.User'])),
            ))
            db.send_create_signal('forum', ['FlaggedItem'])

            # Adding unique constraint on 'FlaggedItem', fields ['content_type', 'object_id', 'user']
            db.create_unique(u'flagged_item', ['content_type_id', 'object_id', 'user_id'])

            # Adding model 'Comment'
            db.create_table(u'comment', (
                ('comment', self.gf('django.db.models.fields.CharField')(max_length=300)),
                ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
                ('added_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
                ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='comments', to=orm['auth.User'])),
            ))
            db.send_create_signal('forum', ['Comment'])

            # Adding model 'Tag'
            db.create_table(u'tag', (
                ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
                ('deleted', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='created_tags', to=orm['auth.User'])),
                ('deleted_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='deleted_tags', null=True, to=orm['auth.User'])),
                ('used_count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
                ('deleted_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ))
            db.send_create_signal('forum', ['Tag'])

            # Adding model 'MarkedTag'
            db.create_table('forum_markedtag', (
                ('reason', self.gf('django.db.models.fields.CharField')(max_length=16)),
                ('tag', self.gf('django.db.models.fields.related.ForeignKey')(related_name='user_selections', to=orm['forum.Tag'])),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='tag_selections', to=orm['auth.User'])),
            ))
            db.send_create_signal('forum', ['MarkedTag'])

            # Adding model 'Exercise'
            db.create_table(u'exercise', (
                ('wiki', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('vote_up_count', self.gf('django.db.models.fields.IntegerField')(default=0)),
                ('problem_accepted', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('offensive_flag_count', self.gf('django.db.models.fields.SmallIntegerField')(default=0)),
                ('closed_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
                ('deleted_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('last_activity_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='last_active_in_exercises', to=orm['auth.User'])),
                ('view_count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
                ('locked_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
                ('score', self.gf('django.db.models.fields.IntegerField')(default=0)),
                ('author', self.gf('django.db.models.fields.related.ForeignKey')(related_name='exercises', to=orm['auth.User'])),
                ('comment_count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
                ('html', self.gf('django.db.models.fields.TextField')()),
                ('vote_down_count', self.gf('django.db.models.fields.IntegerField')(default=0)),
                ('closed', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('last_edited_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='last_edited_exercises', null=True, to=orm['auth.User'])),
                ('favourite_count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
                ('deleted', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('summary', self.gf('django.db.models.fields.CharField')(max_length=180)),
                ('problem_count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
                ('last_activity_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
                ('closed_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='closed_exercises', null=True, to=orm['auth.User'])),
                ('close_reason', self.gf('django.db.models.fields.SmallIntegerField')(null=True, blank=True)),
                ('locked', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('tagnames', self.gf('django.db.models.fields.CharField')(max_length=125)),
                ('locked_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='locked_exercises', null=True, to=orm['auth.User'])),
                ('added_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
                ('deleted_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='deleted_exercises', null=True, to=orm['auth.User'])),
                ('wikified_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
                ('title', self.gf('django.db.models.fields.CharField')(max_length=300)),
                ('last_edited_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ))
            db.send_create_signal('forum', ['Exercise'])

            # Adding M2M table for field followed_by on 'Exercise'
            db.create_table(u'exercise_followed_by', (
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
                ('exercise', models.ForeignKey(orm['forum.exercise'], null=False)),
                ('user', models.ForeignKey(orm['auth.user'], null=False))
            ))
            db.create_unique(u'exercise_followed_by', ['exercise_id', 'user_id'])

            # Adding M2M table for field tags on 'Exercise'
            db.create_table(u'exercise_tags', (
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
                ('exercise', models.ForeignKey(orm['forum.exercise'], null=False)),
                ('tag', models.ForeignKey(orm['forum.tag'], null=False))
            ))
            db.create_unique(u'exercise_tags', ['exercise_id', 'tag_id'])

            # Adding model 'ExerciseView'
            db.create_table('forum_exerciseview', (
                ('when', self.gf('django.db.models.fields.DateTimeField')()),
                ('who', self.gf('django.db.models.fields.related.ForeignKey')(related_name='exercise_views', to=orm['auth.User'])),
                ('exercise', self.gf('django.db.models.fields.related.ForeignKey')(related_name='viewed', to=orm['forum.Exercise'])),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ))
            db.send_create_signal('forum', ['ExerciseView'])

            # Adding model 'FavoriteExercise'
            db.create_table(u'favorite_exercise', (
                ('exercise', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['forum.Exercise'])),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('added_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
                ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='user_favorite_exercises', to=orm['auth.User'])),
            ))
            db.send_create_signal('forum', ['FavoriteExercise'])

            # Adding model 'ExerciseRevision'
            db.create_table(u'exercise_revision', (
                ('author', self.gf('django.db.models.fields.related.ForeignKey')(related_name='exerciserevisions', to=orm['auth.User'])),
                ('tagnames', self.gf('django.db.models.fields.CharField')(max_length=125)),
                ('text', self.gf('django.db.models.fields.TextField')()),
                ('title', self.gf('django.db.models.fields.CharField')(max_length=300)),
                ('exercise', self.gf('django.db.models.fields.related.ForeignKey')(related_name='revisions', to=orm['forum.Exercise'])),
                ('revised_at', self.gf('django.db.models.fields.DateTimeField')()),
                ('summary', self.gf('django.db.models.fields.CharField')(max_length=300, blank=True)),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('revision', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ))
            db.send_create_signal('forum', ['ExerciseRevision'])

            # Adding model 'AnonymousExercise'
            db.create_table('forum_anonymousexercise', (
                ('wiki', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('ip_addr', self.gf('django.db.models.fields.IPAddressField')(max_length=15)),
                ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True)),
                ('tagnames', self.gf('django.db.models.fields.CharField')(max_length=125)),
                ('text', self.gf('django.db.models.fields.TextField')()),
                ('title', self.gf('django.db.models.fields.CharField')(max_length=300)),
                ('added_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
                ('summary', self.gf('django.db.models.fields.CharField')(max_length=180)),
                ('session_key', self.gf('django.db.models.fields.CharField')(max_length=40)),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ))
            db.send_create_signal('forum', ['AnonymousExercise'])

            # Adding model 'Problem'
            db.create_table(u'problem', (
                ('wiki', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('vote_up_count', self.gf('django.db.models.fields.IntegerField')(default=0)),
                ('offensive_flag_count', self.gf('django.db.models.fields.SmallIntegerField')(default=0)),
                ('deleted_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('locked_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
                ('score', self.gf('django.db.models.fields.IntegerField')(default=0)),
                ('author', self.gf('django.db.models.fields.related.ForeignKey')(related_name='problems', to=orm['auth.User'])),
                ('exercise', self.gf('django.db.models.fields.related.ForeignKey')(related_name='problems', to=orm['forum.Exercise'])),
                ('comment_count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
                ('html', self.gf('django.db.models.fields.TextField')()),
                ('vote_down_count', self.gf('django.db.models.fields.IntegerField')(default=0)),
                ('last_edited_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='last_edited_problems', null=True, to=orm['auth.User'])),
                ('accepted_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
                ('deleted', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('accepted', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('locked', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('locked_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='locked_problems', null=True, to=orm['auth.User'])),
                ('added_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
                ('deleted_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='deleted_problems', null=True, to=orm['auth.User'])),
                ('wikified_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
                ('last_edited_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ))
            db.send_create_signal('forum', ['Problem'])

            # Adding model 'ProblemRevision'
            db.create_table(u'problem_revision', (
                ('author', self.gf('django.db.models.fields.related.ForeignKey')(related_name='problemrevisions', to=orm['auth.User'])),
                ('text', self.gf('django.db.models.fields.TextField')()),
                ('revised_at', self.gf('django.db.models.fields.DateTimeField')()),
                ('summary', self.gf('django.db.models.fields.CharField')(max_length=300, blank=True)),
                ('problem', self.gf('django.db.models.fields.related.ForeignKey')(related_name='revisions', to=orm['forum.Problem'])),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('revision', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ))
            db.send_create_signal('forum', ['ProblemRevision'])

            # Adding model 'AnonymousProblem'
            db.create_table('forum_anonymousproblem', (
                ('wiki', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('ip_addr', self.gf('django.db.models.fields.IPAddressField')(max_length=15)),
                ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True)),
                ('text', self.gf('django.db.models.fields.TextField')()),
                ('exercise', self.gf('django.db.models.fields.related.ForeignKey')(related_name='anonymous_problems', to=orm['forum.Exercise'])),
                ('added_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
                ('summary', self.gf('django.db.models.fields.CharField')(max_length=180)),
                ('session_key', self.gf('django.db.models.fields.CharField')(max_length=40)),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ))
            db.send_create_signal('forum', ['AnonymousProblem'])

            # Adding model 'Activity'
            db.create_table(u'activity', (
                ('is_auditted', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
                ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
                ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
                ('active_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('activity_type', self.gf('django.db.models.fields.SmallIntegerField')()),
            ))
            db.send_create_signal('forum', ['Activity'])

            # Adding model 'EmailFeedSetting'
            db.create_table('forum_emailfeedsetting', (
                ('reported_at', self.gf('django.db.models.fields.DateTimeField')(null=True)),
                ('added_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
                ('subscriber', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
                ('feed_type', self.gf('django.db.models.fields.CharField')(max_length=16)),
                ('frequency', self.gf('django.db.models.fields.CharField')(default='n', max_length=8)),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ))
            db.send_create_signal('forum', ['EmailFeedSetting'])

            # Adding model 'ValidationHash'
            db.create_table('forum_validationhash', (
                ('hash_code', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
                ('seed', self.gf('django.db.models.fields.CharField')(max_length=12)),
                ('expiration', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2010, 4, 25, 13, 14, 41, 581000))),
                ('type', self.gf('django.db.models.fields.CharField')(max_length=12)),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ))
            db.send_create_signal('forum', ['ValidationHash'])

            # Adding unique constraint on 'ValidationHash', fields ['user', 'type']
            db.create_unique('forum_validationhash', ['user_id', 'type'])

            # Adding model 'AuthKeyUserAssociation'
            db.create_table('forum_authkeyuserassociation', (
                ('added_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
                ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='auth_keys', to=orm['auth.User'])),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('key', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
                ('provider', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ))
            db.send_create_signal('forum', ['AuthKeyUserAssociation'])

            # Adding model 'Badge'
            db.create_table(u'badge', (
                ('multiple', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('description', self.gf('django.db.models.fields.CharField')(max_length=300)),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('awarded_count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
                ('type', self.gf('django.db.models.fields.SmallIntegerField')()),
                ('slug', self.gf('django.db.models.fields.SlugField')(db_index=True, max_length=50, blank=True)),
                ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ))
            db.send_create_signal('forum', ['Badge'])

            # Adding unique constraint on 'Badge', fields ['name', 'type']
            db.create_unique(u'badge', ['name', 'type'])

            # Adding model 'Award'
            db.create_table(u'award', (
                ('awarded_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
                ('notified', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
                ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='award_user', to=orm['auth.User'])),
                ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
                ('badge', self.gf('django.db.models.fields.related.ForeignKey')(related_name='award_badge', to=orm['forum.Badge'])),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ))
            db.send_create_signal('forum', ['Award'])

            # Adding model 'Repute'
            db.create_table(u'repute', (
                ('positive', self.gf('django.db.models.fields.SmallIntegerField')(default=0)),
                ('exercise', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['forum.Exercise'])),
                ('negative', self.gf('django.db.models.fields.SmallIntegerField')(default=0)),
                ('reputation_type', self.gf('django.db.models.fields.SmallIntegerField')()),
                ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
                ('reputed_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('reputation', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ))
            db.send_create_signal('forum', ['Repute'])

            # Adding model 'Book'
            db.create_table(u'book', (
                ('publication', self.gf('django.db.models.fields.CharField')(max_length=255)),
                ('short_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
                ('author', self.gf('django.db.models.fields.CharField')(max_length=255)),
                ('cover_img', self.gf('django.db.models.fields.CharField')(max_length=255)),
                ('price', self.gf('django.db.models.fields.DecimalField')(max_digits=6, decimal_places=2)),
                ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
                ('added_at', self.gf('django.db.models.fields.DateTimeField')()),
                ('pages', self.gf('django.db.models.fields.SmallIntegerField')()),
                ('tagnames', self.gf('django.db.models.fields.CharField')(max_length=125)),
                ('published_at', self.gf('django.db.models.fields.DateTimeField')()),
                ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('last_edited_at', self.gf('django.db.models.fields.DateTimeField')()),
            ))
            db.send_create_signal('forum', ['Book'])

            # Adding M2M table for field exercises on 'Book'
            db.create_table('book_exercise', (
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
                ('book', models.ForeignKey(orm['forum.book'], null=False)),
                ('exercise', models.ForeignKey(orm['forum.exercise'], null=False))
            ))
            db.create_unique('book_exercise', ['book_id', 'exercise_id'])

            # Adding model 'BookAuthorInfo'
            db.create_table(u'book_author_info', (
                ('added_at', self.gf('django.db.models.fields.DateTimeField')()),
                ('book', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['forum.Book'])),
                ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
                ('blog_url', self.gf('django.db.models.fields.CharField')(max_length=255)),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('last_edited_at', self.gf('django.db.models.fields.DateTimeField')()),
            ))
            db.send_create_signal('forum', ['BookAuthorInfo'])

            # Adding model 'BookAuthorRss'
            db.create_table(u'book_author_rss', (
                ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
                ('url', self.gf('django.db.models.fields.CharField')(max_length=255)),
                ('added_at', self.gf('django.db.models.fields.DateTimeField')()),
                ('book', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['forum.Book'])),
                ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
                ('rss_created_at', self.gf('django.db.models.fields.DateTimeField')()),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ))
            db.send_create_signal('forum', ['BookAuthorRss'])
        else:
            db.create_table(u'vote', (
                ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
                ('voted_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
                ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='votes', to=orm['auth.User'])),
                ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
                ('vote', self.gf('django.db.models.fields.SmallIntegerField')()),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ))
            db.send_create_signal('askbot', ['Vote'])

            # Adding unique constraint on 'Vote', fields ['content_type', 'object_id', 'user']
            db.create_unique(u'vote', ['content_type_id', 'object_id', 'user_id'])

            # Adding model 'FlaggedItem'
            db.create_table(u'flagged_item', (
                ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
                ('flagged_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
                ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='flaggeditems', to=orm['auth.User'])),
            ))
            db.send_create_signal('askbot', ['FlaggedItem'])

            # Adding unique constraint on 'FlaggedItem', fields ['content_type', 'object_id', 'user']
            db.create_unique(u'flagged_item', ['content_type_id', 'object_id', 'user_id'])

            # Adding model 'Comment'
            db.create_table(u'comment', (
                ('comment', self.gf('django.db.models.fields.CharField')(max_length=300)),
                ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
                ('added_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
                ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='comments', to=orm['auth.User'])),
            ))
            db.send_create_signal('askbot', ['Comment'])

            # Adding model 'Tag'
            db.create_table(u'tag', (
                ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
                ('deleted', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='created_tags', to=orm['auth.User'])),
                ('deleted_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='deleted_tags', null=True, to=orm['auth.User'])),
                ('used_count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
                ('deleted_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ))
            db.send_create_signal('askbot', ['Tag'])

            # Adding model 'MarkedTag'
            db.create_table('askbot_markedtag', (
                ('reason', self.gf('django.db.models.fields.CharField')(max_length=16)),
                ('tag', self.gf('django.db.models.fields.related.ForeignKey')(related_name='user_selections', to=orm['askbot.Tag'])),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='tag_selections', to=orm['auth.User'])),
            ))
            db.send_create_signal('askbot', ['MarkedTag'])

            # Adding model 'Exercise'
            db.create_table(u'exercise', (
                ('wiki', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('vote_up_count', self.gf('django.db.models.fields.IntegerField')(default=0)),
                ('problem_accepted', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('offensive_flag_count', self.gf('django.db.models.fields.SmallIntegerField')(default=0)),
                ('closed_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
                ('deleted_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('last_activity_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='last_active_in_exercises', to=orm['auth.User'])),
                ('view_count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
                ('locked_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
                ('score', self.gf('django.db.models.fields.IntegerField')(default=0)),
                ('author', self.gf('django.db.models.fields.related.ForeignKey')(related_name='exercises', to=orm['auth.User'])),
                ('comment_count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
                ('html', self.gf('django.db.models.fields.TextField')()),
                ('vote_down_count', self.gf('django.db.models.fields.IntegerField')(default=0)),
                ('closed', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('last_edited_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='last_edited_exercises', null=True, to=orm['auth.User'])),
                ('favourite_count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
                ('deleted', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('summary', self.gf('django.db.models.fields.CharField')(max_length=180)),
                ('problem_count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
                ('last_activity_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
                ('closed_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='closed_exercises', null=True, to=orm['auth.User'])),
                ('close_reason', self.gf('django.db.models.fields.SmallIntegerField')(null=True, blank=True)),
                ('locked', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('tagnames', self.gf('django.db.models.fields.CharField')(max_length=125)),
                ('locked_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='locked_exercises', null=True, to=orm['auth.User'])),
                ('added_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
                ('deleted_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='deleted_exercises', null=True, to=orm['auth.User'])),
                ('wikified_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
                ('title', self.gf('django.db.models.fields.CharField')(max_length=300)),
                ('last_edited_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ))
            db.send_create_signal('askbot', ['Exercise'])

            # Adding M2M table for field followed_by on 'Exercise'
            db.create_table(u'exercise_followed_by', (
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
                ('exercise', models.ForeignKey(orm['askbot.exercise'], null=False)),
                ('user', models.ForeignKey(orm['auth.user'], null=False))
            ))
            db.create_unique(u'exercise_followed_by', ['exercise_id', 'user_id'])

            # Adding M2M table for field tags on 'Exercise'
            db.create_table(u'exercise_tags', (
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
                ('exercise', models.ForeignKey(orm['askbot.exercise'], null=False)),
                ('tag', models.ForeignKey(orm['askbot.tag'], null=False))
            ))
            db.create_unique(u'exercise_tags', ['exercise_id', 'tag_id'])

            # Adding model 'ExerciseView'
            db.create_table('askbot_exerciseview', (
                ('when', self.gf('django.db.models.fields.DateTimeField')()),
                ('who', self.gf('django.db.models.fields.related.ForeignKey')(related_name='exercise_views', to=orm['auth.User'])),
                ('exercise', self.gf('django.db.models.fields.related.ForeignKey')(related_name='viewed', to=orm['askbot.Exercise'])),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ))
            db.send_create_signal('askbot', ['ExerciseView'])

            # Adding model 'FavoriteExercise'
            db.create_table(u'favorite_exercise', (
                ('exercise', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['askbot.Exercise'])),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('added_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
                ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='user_favorite_exercises', to=orm['auth.User'])),
            ))
            db.send_create_signal('askbot', ['FavoriteExercise'])

            # Adding model 'ExerciseRevision'
            db.create_table(u'exercise_revision', (
                ('author', self.gf('django.db.models.fields.related.ForeignKey')(related_name='exerciserevisions', to=orm['auth.User'])),
                ('tagnames', self.gf('django.db.models.fields.CharField')(max_length=125)),
                ('text', self.gf('django.db.models.fields.TextField')()),
                ('title', self.gf('django.db.models.fields.CharField')(max_length=300)),
                ('exercise', self.gf('django.db.models.fields.related.ForeignKey')(related_name='revisions', to=orm['askbot.Exercise'])),
                ('revised_at', self.gf('django.db.models.fields.DateTimeField')()),
                ('summary', self.gf('django.db.models.fields.CharField')(max_length=300, blank=True)),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('revision', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ))
            db.send_create_signal('askbot', ['ExerciseRevision'])

            # Adding model 'AnonymousExercise'
            db.create_table('askbot_anonymousexercise', (
                ('wiki', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('ip_addr', self.gf('django.db.models.fields.IPAddressField')(max_length=15)),
                ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True)),
                ('tagnames', self.gf('django.db.models.fields.CharField')(max_length=125)),
                ('text', self.gf('django.db.models.fields.TextField')()),
                ('title', self.gf('django.db.models.fields.CharField')(max_length=300)),
                ('added_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
                ('summary', self.gf('django.db.models.fields.CharField')(max_length=180)),
                ('session_key', self.gf('django.db.models.fields.CharField')(max_length=40)),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ))
            db.send_create_signal('askbot', ['AnonymousExercise'])

            # Adding model 'Problem'
            db.create_table(u'problem', (
                ('wiki', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('vote_up_count', self.gf('django.db.models.fields.IntegerField')(default=0)),
                ('offensive_flag_count', self.gf('django.db.models.fields.SmallIntegerField')(default=0)),
                ('deleted_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('locked_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
                ('score', self.gf('django.db.models.fields.IntegerField')(default=0)),
                ('author', self.gf('django.db.models.fields.related.ForeignKey')(related_name='problems', to=orm['auth.User'])),
                ('exercise', self.gf('django.db.models.fields.related.ForeignKey')(related_name='problems', to=orm['askbot.Exercise'])),
                ('comment_count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
                ('html', self.gf('django.db.models.fields.TextField')()),
                ('vote_down_count', self.gf('django.db.models.fields.IntegerField')(default=0)),
                ('last_edited_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='last_edited_problems', null=True, to=orm['auth.User'])),
                ('accepted_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
                ('deleted', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('accepted', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('locked', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('locked_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='locked_problems', null=True, to=orm['auth.User'])),
                ('added_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
                ('deleted_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='deleted_problems', null=True, to=orm['auth.User'])),
                ('wikified_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
                ('last_edited_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ))
            db.send_create_signal('askbot', ['Problem'])

            # Adding model 'ProblemRevision'
            db.create_table(u'problem_revision', (
                ('author', self.gf('django.db.models.fields.related.ForeignKey')(related_name='problemrevisions', to=orm['auth.User'])),
                ('text', self.gf('django.db.models.fields.TextField')()),
                ('revised_at', self.gf('django.db.models.fields.DateTimeField')()),
                ('summary', self.gf('django.db.models.fields.CharField')(max_length=300, blank=True)),
                ('problem', self.gf('django.db.models.fields.related.ForeignKey')(related_name='revisions', to=orm['askbot.Problem'])),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('revision', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ))
            db.send_create_signal('askbot', ['ProblemRevision'])

            # Adding model 'AnonymousProblem'
            db.create_table('askbot_anonymousproblem', (
                ('wiki', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('ip_addr', self.gf('django.db.models.fields.IPAddressField')(max_length=15)),
                ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True)),
                ('text', self.gf('django.db.models.fields.TextField')()),
                ('exercise', self.gf('django.db.models.fields.related.ForeignKey')(related_name='anonymous_problems', to=orm['askbot.Exercise'])),
                ('added_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
                ('summary', self.gf('django.db.models.fields.CharField')(max_length=180)),
                ('session_key', self.gf('django.db.models.fields.CharField')(max_length=40)),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ))
            db.send_create_signal('askbot', ['AnonymousProblem'])

            # Adding model 'Activity'
            db.create_table(u'activity', (
                ('is_auditted', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
                ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
                ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
                ('active_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('activity_type', self.gf('django.db.models.fields.SmallIntegerField')()),
            ))
            db.send_create_signal('askbot', ['Activity'])

            # Adding model 'EmailFeedSetting'
            db.create_table('askbot_emailfeedsetting', (
                ('reported_at', self.gf('django.db.models.fields.DateTimeField')(null=True)),
                ('added_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
                ('subscriber', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
                ('feed_type', self.gf('django.db.models.fields.CharField')(max_length=16)),
                ('frequency', self.gf('django.db.models.fields.CharField')(default='n', max_length=8)),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ))
            db.send_create_signal('askbot', ['EmailFeedSetting'])

            # Adding model 'ValidationHash'
            db.create_table('askbot_validationhash', (
                ('hash_code', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
                ('seed', self.gf('django.db.models.fields.CharField')(max_length=12)),
                ('expiration', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2010, 4, 25, 13, 14, 41, 581000))),
                ('type', self.gf('django.db.models.fields.CharField')(max_length=12)),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ))
            db.send_create_signal('askbot', ['ValidationHash'])

            # Adding unique constraint on 'ValidationHash', fields ['user', 'type']
            db.create_unique('askbot_validationhash', ['user_id', 'type'])

            # Adding model 'AuthKeyUserAssociation'
            db.create_table('askbot_authkeyuserassociation', (
                ('added_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
                ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='auth_keys', to=orm['auth.User'])),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('key', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
                ('provider', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ))
            db.send_create_signal('askbot', ['AuthKeyUserAssociation'])

            # Adding model 'Badge'
            db.create_table(u'badge', (
                ('multiple', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('description', self.gf('django.db.models.fields.CharField')(max_length=300)),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('awarded_count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
                ('type', self.gf('django.db.models.fields.SmallIntegerField')()),
                ('slug', self.gf('django.db.models.fields.SlugField')(db_index=True, max_length=50, blank=True)),
                ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ))
            db.send_create_signal('askbot', ['Badge'])

            # Adding unique constraint on 'Badge', fields ['name', 'type']
            db.create_unique(u'badge', ['name', 'type'])

            # Adding model 'Award'
            db.create_table(u'award', (
                ('awarded_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
                ('notified', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
                ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
                ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='award_user', to=orm['auth.User'])),
                ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
                ('badge', self.gf('django.db.models.fields.related.ForeignKey')(related_name='award_badge', to=orm['askbot.Badge'])),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ))
            db.send_create_signal('askbot', ['Award'])

            # Adding model 'Repute'
            db.create_table(u'repute', (
                ('positive', self.gf('django.db.models.fields.SmallIntegerField')(default=0)),
                ('exercise', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['askbot.Exercise'])),
                ('negative', self.gf('django.db.models.fields.SmallIntegerField')(default=0)),
                ('reputation_type', self.gf('django.db.models.fields.SmallIntegerField')()),
                ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
                ('reputed_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('reputation', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ))
            db.send_create_signal('askbot', ['Repute'])

            # Adding model 'Book'
            db.create_table(u'book', (
                ('publication', self.gf('django.db.models.fields.CharField')(max_length=255)),
                ('short_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
                ('author', self.gf('django.db.models.fields.CharField')(max_length=255)),
                ('cover_img', self.gf('django.db.models.fields.CharField')(max_length=255)),
                ('price', self.gf('django.db.models.fields.DecimalField')(max_digits=6, decimal_places=2)),
                ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
                ('added_at', self.gf('django.db.models.fields.DateTimeField')()),
                ('pages', self.gf('django.db.models.fields.SmallIntegerField')()),
                ('tagnames', self.gf('django.db.models.fields.CharField')(max_length=125)),
                ('published_at', self.gf('django.db.models.fields.DateTimeField')()),
                ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('last_edited_at', self.gf('django.db.models.fields.DateTimeField')()),
            ))
            db.send_create_signal('askbot', ['Book'])

            # Adding M2M table for field exercises on 'Book'
            db.create_table('book_exercise', (
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
                ('book', models.ForeignKey(orm['askbot.book'], null=False)),
                ('exercise', models.ForeignKey(orm['askbot.exercise'], null=False))
            ))
            db.create_unique('book_exercise', ['book_id', 'exercise_id'])

            # Adding model 'BookAuthorInfo'
            db.create_table(u'book_author_info', (
                ('added_at', self.gf('django.db.models.fields.DateTimeField')()),
                ('book', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['askbot.Book'])),
                ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
                ('blog_url', self.gf('django.db.models.fields.CharField')(max_length=255)),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('last_edited_at', self.gf('django.db.models.fields.DateTimeField')()),
            ))
            db.send_create_signal('askbot', ['BookAuthorInfo'])

            # Adding model 'BookAuthorRss'
            db.create_table(u'book_author_rss', (
                ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
                ('url', self.gf('django.db.models.fields.CharField')(max_length=255)),
                ('added_at', self.gf('django.db.models.fields.DateTimeField')()),
                ('book', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['askbot.Book'])),
                ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
                ('rss_created_at', self.gf('django.db.models.fields.DateTimeField')()),
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ))
            db.send_create_signal('askbot', ['BookAuthorRss'])
    
    def backwards(self, orm):
        db.delete_column('auth_user', 'website')
        db.delete_column('auth_user', 'about')
        db.delete_column('auth_user', 'hide_ignored_exercises')
        db.delete_column('auth_user', 'gold')
        db.delete_column('auth_user', 'email_isvalid')
        db.delete_column('auth_user', 'real_name')
        db.delete_column('auth_user', 'location')
        db.delete_column('auth_user', 'email_key')
        db.delete_column('auth_user', 'date_of_birth')
        db.delete_column('auth_user', 'reputation')
        db.delete_column('auth_user', 'gravatar')
        db.delete_column('auth_user', 'bronze')
        db.delete_column('auth_user', 'tag_filter_setting')
        db.delete_column('auth_user', 'last_seen')
        db.delete_column('auth_user', 'silver')
        db.delete_column('auth_user', 'exercises_per_page')
        db.delete_column('auth_user', 'response_count')
        
        if app_dir_name == 'forum':
            # Deleting model 'Vote'
            db.delete_table(u'vote')

            # Removing unique constraint on 'Vote', fields ['content_type', 'object_id', 'user']
            db.delete_unique(u'vote', ['content_type_id', 'object_id', 'user_id'])

            # Deleting model 'FlaggedItem'
            db.delete_table(u'flagged_item')

            # Removing unique constraint on 'FlaggedItem', fields ['content_type', 'object_id', 'user']
            db.delete_unique(u'flagged_item', ['content_type_id', 'object_id', 'user_id'])

            # Deleting model 'Comment'
            db.delete_table(u'comment')

            # Deleting model 'Tag'
            db.delete_table(u'tag')

            # Deleting model 'MarkedTag'
            db.delete_table('forum_markedtag')

            # Deleting model 'Exercise'
            db.delete_table(u'exercise')

            # Removing M2M table for field followed_by on 'Exercise'
            db.delete_table('exercise_followed_by')

            # Removing M2M table for field tags on 'Exercise'
            db.delete_table('exercise_tags')

            # Deleting model 'ExerciseView'
            db.delete_table('forum_exerciseview')

            # Deleting model 'FavoriteExercise'
            db.delete_table(u'favorite_exercise')

            # Deleting model 'ExerciseRevision'
            db.delete_table(u'exercise_revision')

            # Deleting model 'AnonymousExercise'
            db.delete_table('forum_anonymousexercise')

            # Deleting model 'Problem'
            db.delete_table(u'problem')

            # Deleting model 'ProblemRevision'
            db.delete_table(u'problem_revision')

            # Deleting model 'AnonymousProblem'
            db.delete_table('forum_anonymousproblem')

            # Deleting model 'Activity'
            db.delete_table(u'activity')

            # Deleting model 'EmailFeedSetting'
            db.delete_table('forum_emailfeedsetting')

            # Deleting model 'ValidationHash'
            db.delete_table('forum_validationhash')

            # Removing unique constraint on 'ValidationHash', fields ['user', 'type']
            db.delete_unique('forum_validationhash', ['user_id', 'type'])

            # Deleting model 'AuthKeyUserAssociation'
            db.delete_table('forum_authkeyuserassociation')

            # Deleting model 'Badge'
            db.delete_table(u'badge')

            # Removing unique constraint on 'Badge', fields ['name', 'type']
            db.delete_unique(u'badge', ['name', 'type'])

            # Deleting model 'Award'
            db.delete_table(u'award')

            # Deleting model 'Repute'
            db.delete_table(u'repute')

            # Deleting model 'Book'
            db.delete_table(u'book')

            # Removing M2M table for field exercises on 'Book'
            db.delete_table('book_exercise')

            # Deleting model 'BookAuthorInfo'
            db.delete_table(u'book_author_info')

            # Deleting model 'BookAuthorRss'
            db.delete_table(u'book_author_rss')
        else:
            # Deleting model 'Vote'
            db.delete_table(u'vote')

            # Removing unique constraint on 'Vote', fields ['content_type', 'object_id', 'user']
            db.delete_unique(u'vote', ['content_type_id', 'object_id', 'user_id'])

            # Deleting model 'FlaggedItem'
            db.delete_table(u'flagged_item')

            # Removing unique constraint on 'FlaggedItem', fields ['content_type', 'object_id', 'user']
            db.delete_unique(u'flagged_item', ['content_type_id', 'object_id', 'user_id'])

            # Deleting model 'Comment'
            db.delete_table(u'comment')

            # Deleting model 'Tag'
            db.delete_table(u'tag')

            # Deleting model 'MarkedTag'
            db.delete_table('askbot_markedtag')

            # Deleting model 'Exercise'
            db.delete_table(u'exercise')

            # Removing M2M table for field followed_by on 'Exercise'
            db.delete_table('exercise_followed_by')

            # Removing M2M table for field tags on 'Exercise'
            db.delete_table('exercise_tags')

            # Deleting model 'ExerciseView'
            db.delete_table('askbot_exerciseview')

            # Deleting model 'FavoriteExercise'
            db.delete_table(u'favorite_exercise')

            # Deleting model 'ExerciseRevision'
            db.delete_table(u'exercise_revision')

            # Deleting model 'AnonymousExercise'
            db.delete_table('askbot_anonymousexercise')

            # Deleting model 'Problem'
            db.delete_table(u'problem')

            # Deleting model 'ProblemRevision'
            db.delete_table(u'problem_revision')

            # Deleting model 'AnonymousProblem'
            db.delete_table('askbot_anonymousproblem')

            # Deleting model 'Activity'
            db.delete_table(u'activity')

            # Deleting model 'EmailFeedSetting'
            db.delete_table('askbot_emailfeedsetting')

            # Deleting model 'ValidationHash'
            db.delete_table('askbot_validationhash')

            # Removing unique constraint on 'ValidationHash', fields ['user', 'type']
            db.delete_unique('askbot_validationhash', ['user_id', 'type'])

            # Deleting model 'AuthKeyUserAssociation'
            db.delete_table('askbot_authkeyuserassociation')

            # Deleting model 'Badge'
            db.delete_table(u'badge')

            # Removing unique constraint on 'Badge', fields ['name', 'type']
            db.delete_unique(u'badge', ['name', 'type'])

            # Deleting model 'Award'
            db.delete_table(u'award')

            # Deleting model 'Repute'
            db.delete_table(u'repute')

            # Deleting model 'Book'
            db.delete_table(u'book')

            # Removing M2M table for field exercises on 'Book'
            db.delete_table('book_exercise')

            # Deleting model 'BookAuthorInfo'
            db.delete_table(u'book_author_info')

            # Deleting model 'BookAuthorRss'
            db.delete_table(u'book_author_rss')
        
        
    if app_dir_name == 'forum':
        models = {
            'auth.group': {
                'Meta': {'object_name': 'Group'},
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
                'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
            },
            'auth.permission': {
                'Meta': {'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
                'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
                'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
            },
            'auth.user': {
                'Meta': {'object_name': 'User'},
                'about': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
                'bronze': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
                'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'date_of_birth': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
                'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
                'email_isvalid': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'email_key': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True'}),
                'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
                'gold': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
                'gravatar': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
                'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True'}),
                'hide_ignored_exercises': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
                'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
                'last_seen': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'location': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
                'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
                'exercises_per_page': ('django.db.models.fields.SmallIntegerField', [], {'default': '10'}),
                'real_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
                'reputation': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
                'silver': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
                'tag_filter_setting': ('django.db.models.fields.CharField', [], {'default': "'ignored'", 'max_length': '16'}),
                'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'}),
                'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'}),
                'website': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
            },
            'contenttypes.contenttype': {
                'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
                'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
                'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
            },
            'forum.activity': {
                'Meta': {'object_name': 'Activity', 'db_table': "u'activity'"},
                'active_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'activity_type': ('django.db.models.fields.SmallIntegerField', [], {}),
                'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'is_auditted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
            },
            'forum.anonymousproblem': {
                'Meta': {'object_name': 'AnonymousProblem'},
                'added_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'ip_addr': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
                'exercise': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'anonymous_problems'", 'to': "orm['forum.Exercise']"}),
                'session_key': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
                'summary': ('django.db.models.fields.CharField', [], {'max_length': '180'}),
                'text': ('django.db.models.fields.TextField', [], {}),
                'wiki': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'})
            },
            'forum.anonymousexercise': {
                'Meta': {'object_name': 'AnonymousExercise'},
                'added_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'ip_addr': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
                'session_key': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
                'summary': ('django.db.models.fields.CharField', [], {'max_length': '180'}),
                'tagnames': ('django.db.models.fields.CharField', [], {'max_length': '125'}),
                'text': ('django.db.models.fields.TextField', [], {}),
                'title': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
                'wiki': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'})
            },
            'forum.problem': {
                'Meta': {'object_name': 'Problem', 'db_table': "u'problem'"},
                'accepted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'accepted_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
                'added_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'problems'", 'to': "orm['auth.User']"}),
                'comment_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
                'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'deleted_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
                'deleted_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'deleted_problems'", 'null': 'True', 'to': "orm['auth.User']"}),
                'html': ('django.db.models.fields.TextField', [], {}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'last_edited_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
                'last_edited_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'last_edited_problems'", 'null': 'True', 'to': "orm['auth.User']"}),
                'locked': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'locked_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
                'locked_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'locked_problems'", 'null': 'True', 'to': "orm['auth.User']"}),
                'offensive_flag_count': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
                'exercise': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'problems'", 'to': "orm['forum.Exercise']"}),
                'score': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
                'vote_down_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
                'vote_up_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
                'wiki': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'wikified_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
            },
            'forum.problemrevision': {
                'Meta': {'object_name': 'ProblemRevision', 'db_table': "u'problem_revision'"},
                'problem': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'revisions'", 'to': "orm['forum.Problem']"}),
                'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'problemrevisions'", 'to': "orm['auth.User']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'revised_at': ('django.db.models.fields.DateTimeField', [], {}),
                'revision': ('django.db.models.fields.PositiveIntegerField', [], {}),
                'summary': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
                'text': ('django.db.models.fields.TextField', [], {})
            },
            'forum.authkeyuserassociation': {
                'Meta': {'object_name': 'AuthKeyUserAssociation'},
                'added_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
                'provider': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'auth_keys'", 'to': "orm['auth.User']"})
            },
            'forum.award': {
                'Meta': {'object_name': 'Award', 'db_table': "u'award'"},
                'awarded_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'badge': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'award_badge'", 'to': "orm['forum.Badge']"}),
                'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'notified': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'award_user'", 'to': "orm['auth.User']"})
            },
            'forum.badge': {
                'Meta': {'unique_together': "(('name', 'type'),)", 'object_name': 'Badge', 'db_table': "u'badge'"},
                'awarded_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
                'awarded_to': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'badges'", 'through': "'Award'", 'to': "orm['auth.User']"}),
                'description': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'multiple': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
                'slug': ('django.db.models.fields.SlugField', [], {'db_index': 'True', 'max_length': '50', 'blank': 'True'}),
                'type': ('django.db.models.fields.SmallIntegerField', [], {})
            },
            'forum.book': {
                'Meta': {'object_name': 'Book', 'db_table': "u'book'"},
                'added_at': ('django.db.models.fields.DateTimeField', [], {}),
                'author': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
                'cover_img': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'last_edited_at': ('django.db.models.fields.DateTimeField', [], {}),
                'pages': ('django.db.models.fields.SmallIntegerField', [], {}),
                'price': ('django.db.models.fields.DecimalField', [], {'max_digits': '6', 'decimal_places': '2'}),
                'publication': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
                'published_at': ('django.db.models.fields.DateTimeField', [], {}),
                'exercises': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'book'", 'db_table': "'book_exercise'", 'to': "orm['forum.Exercise']"}),
                'short_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
                'tagnames': ('django.db.models.fields.CharField', [], {'max_length': '125'}),
                'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
            },
            'forum.bookauthorinfo': {
                'Meta': {'object_name': 'BookAuthorInfo', 'db_table': "u'book_author_info'"},
                'added_at': ('django.db.models.fields.DateTimeField', [], {}),
                'blog_url': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
                'book': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.Book']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'last_edited_at': ('django.db.models.fields.DateTimeField', [], {}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
            },
            'forum.bookauthorrss': {
                'Meta': {'object_name': 'BookAuthorRss', 'db_table': "u'book_author_rss'"},
                'added_at': ('django.db.models.fields.DateTimeField', [], {}),
                'book': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.Book']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'rss_created_at': ('django.db.models.fields.DateTimeField', [], {}),
                'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
                'url': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
            },
            'forum.comment': {
                'Meta': {'object_name': 'Comment', 'db_table': "u'comment'"},
                'added_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'comment': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
                'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'comments'", 'to': "orm['auth.User']"})
            },
            'forum.emailfeedsetting': {
                'Meta': {'object_name': 'EmailFeedSetting'},
                'added_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
                'feed_type': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
                'frequency': ('django.db.models.fields.CharField', [], {'default': "'n'", 'max_length': '8'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'reported_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
                'subscriber': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
            },
            'forum.favoriteexercise': {
                'Meta': {'object_name': 'FavoriteExercise', 'db_table': "u'favorite_exercise'"},
                'added_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'exercise': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.Exercise']"}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'user_favorite_exercises'", 'to': "orm['auth.User']"})
            },
            'forum.flaggeditem': {
                'Meta': {'unique_together': "(('content_type', 'object_id', 'user'),)", 'object_name': 'FlaggedItem', 'db_table': "u'flagged_item'"},
                'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
                'flagged_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'flaggeditems'", 'to': "orm['auth.User']"})
            },
            'forum.markedtag': {
                'Meta': {'object_name': 'MarkedTag'},
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'reason': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
                'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'user_selections'", 'to': "orm['forum.Tag']"}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tag_selections'", 'to': "orm['auth.User']"})
            },
            'forum.exercise': {
                'Meta': {'object_name': 'Exercise', 'db_table': "u'exercise'"},
                'added_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'problem_accepted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'problem_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
                'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'exercises'", 'to': "orm['auth.User']"}),
                'close_reason': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
                'closed': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'closed_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
                'closed_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'closed_exercises'", 'null': 'True', 'to': "orm['auth.User']"}),
                'comment_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
                'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'deleted_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
                'deleted_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'deleted_exercises'", 'null': 'True', 'to': "orm['auth.User']"}),
                'favorited_by': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'favorite_exercises'", 'through': "'FavoriteExercise'", 'to': "orm['auth.User']"}),
                'favourite_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
                'followed_by': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'followed_exercises'", 'to': "orm['auth.User']"}),
                'html': ('django.db.models.fields.TextField', [], {}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'last_activity_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'last_activity_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_active_in_exercises'", 'to': "orm['auth.User']"}),
                'last_edited_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
                'last_edited_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'last_edited_exercises'", 'null': 'True', 'to': "orm['auth.User']"}),
                'locked': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'locked_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
                'locked_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'locked_exercises'", 'null': 'True', 'to': "orm['auth.User']"}),
                'offensive_flag_count': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
                'score': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
                'summary': ('django.db.models.fields.CharField', [], {'max_length': '180'}),
                'tagnames': ('django.db.models.fields.CharField', [], {'max_length': '125'}),
                'tags': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'exercises'", 'to': "orm['forum.Tag']"}),
                'title': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
                'view_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
                'vote_down_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
                'vote_up_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
                'wiki': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'wikified_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
            },
            'forum.exerciserevision': {
                'Meta': {'object_name': 'ExerciseRevision', 'db_table': "u'exercise_revision'"},
                'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'exerciserevisions'", 'to': "orm['auth.User']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'exercise': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'revisions'", 'to': "orm['forum.Exercise']"}),
                'revised_at': ('django.db.models.fields.DateTimeField', [], {}),
                'revision': ('django.db.models.fields.PositiveIntegerField', [], {}),
                'summary': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
                'tagnames': ('django.db.models.fields.CharField', [], {'max_length': '125'}),
                'text': ('django.db.models.fields.TextField', [], {}),
                'title': ('django.db.models.fields.CharField', [], {'max_length': '300'})
            },
            'forum.exerciseview': {
                'Meta': {'object_name': 'ExerciseView'},
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'exercise': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'viewed'", 'to': "orm['forum.Exercise']"}),
                'when': ('django.db.models.fields.DateTimeField', [], {}),
                'who': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'exercise_views'", 'to': "orm['auth.User']"})
            },
            'forum.repute': {
                'Meta': {'object_name': 'Repute', 'db_table': "u'repute'"},
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'negative': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
                'positive': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
                'exercise': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.Exercise']"}),
                'reputation': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
                'reputation_type': ('django.db.models.fields.SmallIntegerField', [], {}),
                'reputed_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
            },
            'forum.tag': {
                'Meta': {'object_name': 'Tag', 'db_table': "u'tag'"},
                'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_tags'", 'to': "orm['auth.User']"}),
                'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'deleted_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
                'deleted_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'deleted_tags'", 'null': 'True', 'to': "orm['auth.User']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
                'used_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
            },
            'forum.validationhash': {
                'Meta': {'unique_together': "(('user', 'type'),)", 'object_name': 'ValidationHash'},
                'expiration': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2010, 4, 25, 13, 14, 41, 714642)'}),
                'hash_code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'seed': ('django.db.models.fields.CharField', [], {'max_length': '12'}),
                'type': ('django.db.models.fields.CharField', [], {'max_length': '12'}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
            },
            'forum.vote': {
                'Meta': {'unique_together': "(('content_type', 'object_id', 'user'),)", 'object_name': 'Vote', 'db_table': "u'vote'"},
                'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'votes'", 'to': "orm['auth.User']"}),
                'vote': ('django.db.models.fields.SmallIntegerField', [], {}),
                'voted_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'})
            }
        }
    else:
        models = {
            'auth.group': {
                'Meta': {'object_name': 'Group'},
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
                'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
            },
            'auth.permission': {
                'Meta': {'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
                'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
                'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
            },
            'auth.user': {
                'Meta': {'object_name': 'User'},
                'about': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
                'bronze': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
                'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'date_of_birth': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
                'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
                'email_isvalid': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'email_key': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True'}),
                'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
                'gold': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
                'gravatar': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
                'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True'}),
                'hide_ignored_exercises': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
                'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
                'last_seen': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'location': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
                'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
                'exercises_per_page': ('django.db.models.fields.SmallIntegerField', [], {'default': '10'}),
                'real_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
                'reputation': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
                'silver': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
                'tag_filter_setting': ('django.db.models.fields.CharField', [], {'default': "'ignored'", 'max_length': '16'}),
                'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'}),
                'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'}),
                'website': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
            },
            'contenttypes.contenttype': {
                'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
                'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
                'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
            },
            'askbot.activity': {
                'Meta': {'object_name': 'Activity', 'db_table': "u'activity'"},
                'active_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'activity_type': ('django.db.models.fields.SmallIntegerField', [], {}),
                'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'is_auditted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
            },
            'askbot.anonymousproblem': {
                'Meta': {'object_name': 'AnonymousProblem'},
                'added_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'ip_addr': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
                'exercise': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'anonymous_problems'", 'to': "orm['askbot.Exercise']"}),
                'session_key': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
                'summary': ('django.db.models.fields.CharField', [], {'max_length': '180'}),
                'text': ('django.db.models.fields.TextField', [], {}),
                'wiki': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'})
            },
            'askbot.anonymousexercise': {
                'Meta': {'object_name': 'AnonymousExercise'},
                'added_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'ip_addr': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
                'session_key': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
                'summary': ('django.db.models.fields.CharField', [], {'max_length': '180'}),
                'tagnames': ('django.db.models.fields.CharField', [], {'max_length': '125'}),
                'text': ('django.db.models.fields.TextField', [], {}),
                'title': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
                'wiki': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'})
            },
            'askbot.problem': {
                'Meta': {'object_name': 'Problem', 'db_table': "u'problem'"},
                'accepted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'accepted_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
                'added_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'problems'", 'to': "orm['auth.User']"}),
                'comment_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
                'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'deleted_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
                'deleted_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'deleted_problems'", 'null': 'True', 'to': "orm['auth.User']"}),
                'html': ('django.db.models.fields.TextField', [], {}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'last_edited_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
                'last_edited_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'last_edited_problems'", 'null': 'True', 'to': "orm['auth.User']"}),
                'locked': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'locked_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
                'locked_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'locked_problems'", 'null': 'True', 'to': "orm['auth.User']"}),
                'offensive_flag_count': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
                'exercise': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'problems'", 'to': "orm['askbot.Exercise']"}),
                'score': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
                'vote_down_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
                'vote_up_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
                'wiki': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'wikified_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
            },
            'askbot.problemrevision': {
                'Meta': {'object_name': 'ProblemRevision', 'db_table': "u'problem_revision'"},
                'problem': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'revisions'", 'to': "orm['askbot.Problem']"}),
                'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'problemrevisions'", 'to': "orm['auth.User']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'revised_at': ('django.db.models.fields.DateTimeField', [], {}),
                'revision': ('django.db.models.fields.PositiveIntegerField', [], {}),
                'summary': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
                'text': ('django.db.models.fields.TextField', [], {})
            },
            'askbot.authkeyuserassociation': {
                'Meta': {'object_name': 'AuthKeyUserAssociation'},
                'added_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
                'provider': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'auth_keys'", 'to': "orm['auth.User']"})
            },
            'askbot.award': {
                'Meta': {'object_name': 'Award', 'db_table': "u'award'"},
                'awarded_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'badge': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'award_badge'", 'to': "orm['askbot.Badge']"}),
                'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'notified': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'award_user'", 'to': "orm['auth.User']"})
            },
            'askbot.badge': {
                'Meta': {'unique_together': "(('name', 'type'),)", 'object_name': 'Badge', 'db_table': "u'badge'"},
                'awarded_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
                'awarded_to': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'badges'", 'through': "'Award'", 'to': "orm['auth.User']"}),
                'description': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'multiple': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
                'slug': ('django.db.models.fields.SlugField', [], {'db_index': 'True', 'max_length': '50', 'blank': 'True'}),
                'type': ('django.db.models.fields.SmallIntegerField', [], {})
            },
            'askbot.book': {
                'Meta': {'object_name': 'Book', 'db_table': "u'book'"},
                'added_at': ('django.db.models.fields.DateTimeField', [], {}),
                'author': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
                'cover_img': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'last_edited_at': ('django.db.models.fields.DateTimeField', [], {}),
                'pages': ('django.db.models.fields.SmallIntegerField', [], {}),
                'price': ('django.db.models.fields.DecimalField', [], {'max_digits': '6', 'decimal_places': '2'}),
                'publication': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
                'published_at': ('django.db.models.fields.DateTimeField', [], {}),
                'exercises': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'book'", 'db_table': "'book_exercise'", 'to': "orm['askbot.Exercise']"}),
                'short_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
                'tagnames': ('django.db.models.fields.CharField', [], {'max_length': '125'}),
                'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
            },
            'askbot.bookauthorinfo': {
                'Meta': {'object_name': 'BookAuthorInfo', 'db_table': "u'book_author_info'"},
                'added_at': ('django.db.models.fields.DateTimeField', [], {}),
                'blog_url': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
                'book': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['askbot.Book']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'last_edited_at': ('django.db.models.fields.DateTimeField', [], {}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
            },
            'askbot.bookauthorrss': {
                'Meta': {'object_name': 'BookAuthorRss', 'db_table': "u'book_author_rss'"},
                'added_at': ('django.db.models.fields.DateTimeField', [], {}),
                'book': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['askbot.Book']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'rss_created_at': ('django.db.models.fields.DateTimeField', [], {}),
                'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
                'url': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
            },
            'askbot.comment': {
                'Meta': {'object_name': 'Comment', 'db_table': "u'comment'"},
                'added_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'comment': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
                'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'comments'", 'to': "orm['auth.User']"})
            },
            'askbot.emailfeedsetting': {
                'Meta': {'object_name': 'EmailFeedSetting'},
                'added_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
                'feed_type': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
                'frequency': ('django.db.models.fields.CharField', [], {'default': "'n'", 'max_length': '8'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'reported_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
                'subscriber': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
            },
            'askbot.favoriteexercise': {
                'Meta': {'object_name': 'FavoriteExercise', 'db_table': "u'favorite_exercise'"},
                'added_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'exercise': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['askbot.Exercise']"}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'user_favorite_exercises'", 'to': "orm['auth.User']"})
            },
            'askbot.flaggeditem': {
                'Meta': {'unique_together': "(('content_type', 'object_id', 'user'),)", 'object_name': 'FlaggedItem', 'db_table': "u'flagged_item'"},
                'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
                'flagged_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'flaggeditems'", 'to': "orm['auth.User']"})
            },
            'askbot.markedtag': {
                'Meta': {'object_name': 'MarkedTag'},
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'reason': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
                'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'user_selections'", 'to': "orm['askbot.Tag']"}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tag_selections'", 'to': "orm['auth.User']"})
            },
            'askbot.exercise': {
                'Meta': {'object_name': 'Exercise', 'db_table': "u'exercise'"},
                'added_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'problem_accepted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'problem_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
                'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'exercises'", 'to': "orm['auth.User']"}),
                'close_reason': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
                'closed': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'closed_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
                'closed_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'closed_exercises'", 'null': 'True', 'to': "orm['auth.User']"}),
                'comment_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
                'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'deleted_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
                'deleted_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'deleted_exercises'", 'null': 'True', 'to': "orm['auth.User']"}),
                'favorited_by': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'favorite_exercises'", 'through': "'FavoriteExercise'", 'to': "orm['auth.User']"}),
                'favourite_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
                'followed_by': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'followed_exercises'", 'to': "orm['auth.User']"}),
                'html': ('django.db.models.fields.TextField', [], {}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'last_activity_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'last_activity_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_active_in_exercises'", 'to': "orm['auth.User']"}),
                'last_edited_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
                'last_edited_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'last_edited_exercises'", 'null': 'True', 'to': "orm['auth.User']"}),
                'locked': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'locked_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
                'locked_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'locked_exercises'", 'null': 'True', 'to': "orm['auth.User']"}),
                'offensive_flag_count': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
                'score': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
                'summary': ('django.db.models.fields.CharField', [], {'max_length': '180'}),
                'tagnames': ('django.db.models.fields.CharField', [], {'max_length': '125'}),
                'tags': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'exercises'", 'to': "orm['askbot.Tag']"}),
                'title': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
                'view_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
                'vote_down_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
                'vote_up_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
                'wiki': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'wikified_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
            },
            'askbot.exerciserevision': {
                'Meta': {'object_name': 'ExerciseRevision', 'db_table': "u'exercise_revision'"},
                'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'exerciserevisions'", 'to': "orm['auth.User']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'exercise': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'revisions'", 'to': "orm['askbot.Exercise']"}),
                'revised_at': ('django.db.models.fields.DateTimeField', [], {}),
                'revision': ('django.db.models.fields.PositiveIntegerField', [], {}),
                'summary': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
                'tagnames': ('django.db.models.fields.CharField', [], {'max_length': '125'}),
                'text': ('django.db.models.fields.TextField', [], {}),
                'title': ('django.db.models.fields.CharField', [], {'max_length': '300'})
            },
            'askbot.exerciseview': {
                'Meta': {'object_name': 'ExerciseView'},
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'exercise': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'viewed'", 'to': "orm['askbot.Exercise']"}),
                'when': ('django.db.models.fields.DateTimeField', [], {}),
                'who': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'exercise_views'", 'to': "orm['auth.User']"})
            },
            'askbot.repute': {
                'Meta': {'object_name': 'Repute', 'db_table': "u'repute'"},
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'negative': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
                'positive': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
                'exercise': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['askbot.Exercise']"}),
                'reputation': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
                'reputation_type': ('django.db.models.fields.SmallIntegerField', [], {}),
                'reputed_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
            },
            'askbot.tag': {
                'Meta': {'object_name': 'Tag', 'db_table': "u'tag'"},
                'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_tags'", 'to': "orm['auth.User']"}),
                'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'deleted_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
                'deleted_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'deleted_tags'", 'null': 'True', 'to': "orm['auth.User']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
                'used_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
            },
            'askbot.validationhash': {
                'Meta': {'unique_together': "(('user', 'type'),)", 'object_name': 'ValidationHash'},
                'expiration': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2010, 4, 25, 13, 14, 41, 714642)'}),
                'hash_code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'seed': ('django.db.models.fields.CharField', [], {'max_length': '12'}),
                'type': ('django.db.models.fields.CharField', [], {'max_length': '12'}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
            },
            'askbot.vote': {
                'Meta': {'unique_together': "(('content_type', 'object_id', 'user'),)", 'object_name': 'Vote', 'db_table': "u'vote'"},
                'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'votes'", 'to': "orm['auth.User']"}),
                'vote': ('django.db.models.fields.SmallIntegerField', [], {}),
                'voted_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'})
            }
        }
        
    complete_apps = [app_dir_name]
