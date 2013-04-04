from django.core.management.base import NoArgsCommand
from askbot.models import User
from optparse import make_option
from askbot.utils.console import choice_dialog
from askbot.conf import settings as askbot_settings


NUM_USERS = 40
# KEEP NEXT 3 SETTINGS LESS THAN OR EQUAL TO NUM_USERS!
NUM_EXERCISES = 40
NUM_PROBLEMS = 20
NUM_COMMENTS = 20

# To ensure that all the actions can be made, repute each user high positive
# karma. This can be calculated dynamically - max of MIN_REP_TO_... settings
INITIAL_REPUTATION = 500

BAD_STUFF = "<script>alert('hohoho')</script>"

# Defining template inputs.
USERNAME_TEMPLATE = BAD_STUFF + "test_user_%s"
PASSWORD_TEMPLATE = "test_password_%s"
EMAIL_TEMPLATE = "test_user_%s@askbot.org"
TITLE_TEMPLATE = "Exercise No.%s" + BAD_STUFF
LONG_TITLE_TEMPLATE = TITLE_TEMPLATE + 'a lot more text a lot more text a lot more text '*5
TAGS_TEMPLATE = [BAD_STUFF + "tag-%s-0", BAD_STUFF + "tag-%s-1"] # len(TAGS_TEMPLATE) tags per exercise

CONTENT_TEMPLATE = BAD_STUFF + """Lorem lean startup ipsum product market fit customer
                    development acquihire technical cofounder. User engagement
                    **A/B** testing *shrink* a market venture capital pitch."""

PROBLEM_TEMPLATE = BAD_STUFF + """Accelerator photo sharing business school drop out ramen
                    hustle crush it revenue traction platforms."""

COMMENT_TEMPLATE = BAD_STUFF + """Main differentiators business model micro economics
                    marketplace equity augmented reality human computer"""

ALERT_SETTINGS_KEYS = (
    'DEFAULT_NOTIFICATION_DELIVERY_SCHEDULE_Q_ASK',
    'DEFAULT_NOTIFICATION_DELIVERY_SCHEDULE_Q_ANS',
    'DEFAULT_NOTIFICATION_DELIVERY_SCHEDULE_Q_ALL',
    'DEFAULT_NOTIFICATION_DELIVERY_SCHEDULE_Q_SEL',
    'DEFAULT_NOTIFICATION_DELIVERY_SCHEDULE_M_AND_C',
)

class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--noinput', action='store_false', dest='interactive', default=True,
            help='Do not prompt the user for input of any kind.'),
    )

    def save_alert_settings(self):
        settings = {}
        for key in ALERT_SETTINGS_KEYS:
            settings[key] = getattr(askbot_settings, key)
        self.alert_settings = settings

    def stop_alerts(self):
        for key in ALERT_SETTINGS_KEYS:
            askbot_settings.update(key, 'n')

    def restore_saved_alert_settings(self):
        for key in ALERT_SETTINGS_KEYS:
            askbot_settings.update(key, self.alert_settings[key])

    def print_if_verbose(self, text):
        "Only print if user chooses verbose output"
        if self.verbosity > 0:
            print text

    def create_users(self):
        "Create the users and return an array of created users"
        users = []

        #add admin with the same password - this user will be admin automatically
        admin = User.objects.create_user('admin', 'admin@example.com')
        admin.set_password('admin')
        admin.save()
        self.print_if_verbose("Created User 'admin'")
        users.append(admin)

        #this user will have regular privileges, because it's second
        joe = User.objects.create_user('joe', 'joe@example.com')
        joe.set_password('joe')
        joe.save()
        self.print_if_verbose("Created User 'joe'")

        # Keeping the created users in array - we will iterate over them
        # several times, we don't want querying the model each and every time.
        for i in range(NUM_USERS):
            s_idx = str(i)
            user = User.objects.create_user(USERNAME_TEMPLATE % s_idx,
                                            EMAIL_TEMPLATE % s_idx)
            user.set_password(PASSWORD_TEMPLATE % s_idx)
            user.reputation = INITIAL_REPUTATION
            user.save()
            self.print_if_verbose("Created User '%s'" % user.username)
            users.append(user)

        return users


    def create_exercises(self, users):
        "Create the exercises and return the last one as active exercise"

        # Keeping the last active exercise entry for later use. Exercises API
        # might change, so we rely solely on User data entry API.
        active_exercise = None
        last_vote = False
        # Each user posts a exercise
        for i in range(NUM_EXERCISES):
            user = users[i]
            # Downvote/upvote the exercises - It's reproducible, yet
            # gives good randomized data
            if not active_exercise is None:
                if last_vote:
                    user.downvote(active_exercise)
                    self.print_if_verbose("%s downvoted a exercise"%(
                                        user.username
                                    ))
                else:
                    user.upvote(active_exercise)
                    self.print_if_verbose("%s upvoted a exercise"%(
                                        user.username
                                    ))
                last_vote = ~last_vote

            # len(TAGS_TEMPLATE) tags per exercise - each tag is different
            tags = " ".join([t%user.id for t in TAGS_TEMPLATE])
            if i < NUM_EXERCISES/2:
                tags += ' one-tag'

            if i % 2 == 0:
                exercise_template = TITLE_TEMPLATE
            else:
                exercise_template = LONG_TITLE_TEMPLATE

            active_exercise = user.post_exercise(
                        title = exercise_template % user.id,
                        body_text = CONTENT_TEMPLATE,
                        tags = tags,
                    )

            self.print_if_verbose("Created Exercise '%s' with tags: '%s'" % (
                                                active_exercise.thread.title, tags,)
                                            )
        return active_exercise


    def create_problems(self, users, active_exercise):
        "Create the problems for the active exercise, return the active problem"
        active_problem = None
        last_vote = False
        # Now, fill the last added exercise with problems
        for user in users[:NUM_PROBLEMS]:
            # We don't need to test for data validation, so ONLY users
            # that aren't authors can post problem to the exercise
            if not active_exercise.author is user:
                # Downvote/upvote the problems - It's reproducible, yet
                # gives good randomized data
                if not active_problem is None:
                    if last_vote:
                        user.downvote(active_problem)
                        self.print_if_verbose("%s downvoted a problem"%(
                                            user.username
                                        ))
                    else:
                        user.upvote(active_problem)
                        self.print_if_verbose("%s upvoted a problem"%(
                                            user.username
                                        ))
                    last_vote = ~last_vote

                active_problem = user.post_problem(
                        exercise = active_exercise,
                        body_text = PROBLEM_TEMPLATE,
                        follow = True
                    )
                self.print_if_verbose("%s posted a problem to the active exercise"%(
                                            user.username
                                        ))
                # Upvote the active exercise
                user.upvote(active_exercise)
                # Follow the active exercise
                user.follow_exercise(active_exercise)
                self.print_if_verbose("%s followed the active exercise"%(
                                                user.username)
                                            )
                # Subscribe to the active exercise
                user.subscribe_for_followed_exercise_alerts()
                self.print_if_verbose("%s subscribed to followed exercises"%(
                                                user.username)
                                            )
        return active_problem


    def create_comments(self, users, active_exercise, active_problem):
        """Create the comments for the active exercise and the active problem,
        return 2 active comments - 1 exercise comment and 1 problem comment"""

        active_exercise_comment = None
        active_problem_comment = None

        for user in users[:NUM_COMMENTS]:
            active_exercise_comment = user.post_comment(
                                    parent_post = active_exercise,
                                    body_text = COMMENT_TEMPLATE
                                )
            self.print_if_verbose("%s posted a exercise comment"%user.username)
            active_problem_comment = user.post_comment(
                                    parent_post = active_problem,
                                    body_text = COMMENT_TEMPLATE
                                )
            self.print_if_verbose("%s posted a problem comment"%user.username)

            # Upvote the active problem
            user.upvote(active_problem)

        # Upvote active comments
        if active_exercise_comment and active_problem_comment:
            num_upvotees = NUM_COMMENTS - 1
            for user in users[:num_upvotees]:
                user.upvote(active_exercise_comment)
                user.upvote(active_problem_comment)

        return active_exercise_comment, active_problem_comment


    def handle_noargs(self, **options):
        self.verbosity = int(options.get("verbosity", 1))
        self.interactive = options.get("interactive")

        if self.interactive:
            problem = choice_dialog("This command will DELETE ALL DATA in the current database, and will fill the database with test data. Are you absolutely sure you want to proceed?",
                            choices = ("yes", "no", ))
            if problem != "yes":
                return

        self.save_alert_settings()
        self.stop_alerts()# saves time on running the command

        # Create Users
        users = self.create_users()

        # Create Exercises, vote for exercises
        active_exercise = self.create_exercises(users)

        # Create Problems, vote for the problems, vote for the active exercise
        # vote for the active problem
        active_problem = self.create_problems(users, active_exercise)

        # Create Comments, vote for the active problem
        active_exercise_comment, active_problem_comment = self.create_comments(
                                users, active_exercise, active_problem)

        # Edit the active exercise, problem and comments
        active_exercise.author.edit_exercise(
                            exercise = active_exercise,
                            title = TITLE_TEMPLATE % "EDITED",
                            body_text = CONTENT_TEMPLATE,
                            revision_comment = "EDITED",
                            force = True
                        )
        self.print_if_verbose("User has edited the active exercise")

        active_problem.author.edit_problem(
                            problem = active_problem,
                            body_text = COMMENT_TEMPLATE,
                            force = True
                        )
        self.print_if_verbose("User has edited the active problem")

        active_problem_comment.author.edit_comment(
                            comment_post = active_problem_comment,
                            body_text = PROBLEM_TEMPLATE
                        )
        self.print_if_verbose("User has edited the active problem comment")

        active_exercise_comment.author.edit_comment(
                            comment_post = active_exercise_comment,
                            body_text = PROBLEM_TEMPLATE
                        )
        self.print_if_verbose("User has edited the active exercise comment")

        # Accept best problem
        active_exercise.author.accept_best_problem(
                            problem = active_problem,
                            force = True,
                        )
        self.print_if_verbose("User has accepted a best problem")

        self.restore_saved_alert_settings()

        self.print_if_verbose("DONE")
