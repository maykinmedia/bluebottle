from bluebottle.test.utils import BluebottleTestCase
from django.test import TestCase
from django.utils import timezone

from rest_framework import status

from bluebottle.utils.model_dispatcher import get_task_model, get_project_model

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectFactory, ProjectPhaseFactory
from bluebottle.test.factory_models.tasks import SkillFactory, TaskFactory, TaskMemberFactory

import json

BB_TASK_MODEL = get_task_model()
BB_PROJECT_MODEL = get_project_model()


class TaskApiIntegrationTests(BluebottleTestCase):
    """ Tests for tasks. """

    def setUp(self):
        super(TaskApiIntegrationTests, self).setUp()
        self.some_user = BlueBottleUserFactory.create()
        self.some_token = "JWT {0}".format(self.some_user.get_jwt_token())

        self.another_user = BlueBottleUserFactory.create()
        self.another_token = "JWT {0}".format(self.another_user.get_jwt_token())

        self.some_project = ProjectFactory.create(owner=self.some_user)
        self.another_project = ProjectFactory.create(owner=self.another_user)

        self.skill1 = SkillFactory.create()
        self.skill2 = SkillFactory.create()
        self.skill3 = SkillFactory.create()
        self.skill4 = SkillFactory.create()

        self.task_url = '/api/bb_tasks/'
        self.task_members_url = '/api/bb_tasks/members/'

    def test_create_task(self):
        # Get the list of tasks for some project should return none (count = 0)
        response = self.client.get(self.task_url, {'project': self.some_project.slug},
                                   HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEquals(response.data['count'], 0)

        future_date = timezone.now() + timezone.timedelta(days=30)

        # Now let's create a task.
        some_task_data = {
            'project': self.some_project.slug,
            'title': 'A nice task!',
            'description': 'Well, this is nice',
            'time_needed': 5,
            'skill': '{0}'.format(self.skill1.id),
            'location': 'Overthere',
            'deadline': future_date,
            'end_goal': 'World peace'
        }
        response = self.client.post(self.task_url, some_task_data, HTTP_AUTHORIZATION=self.some_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEquals(response.data['title'], some_task_data['title'])
        self.assertEquals(response.data['end_goal'], some_task_data['end_goal'])
        self.assertEquals(response.data['location'], some_task_data['location'])
        some_task_url = "{0}{1}".format(self.task_url, response.data['id'])

        # Create a task for a project you don't own should fail...
        another_task_data = {
            'project': self.another_project.slug,
            'title': 'Translate some text.',
            'description': 'Wie kan in engels vertalen?',
            'time_needed': 5,
            'skill': '{0}'.format(self.skill2.id),
            'location': 'Tiel',
            'deadline': future_date,
            'end_goal': 'World peace'
        }
        response = self.client.post(self.task_url, another_task_data, HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

        # By now the list for this project should contain one task
        response = self.client.get(self.task_url, {'project': self.some_project.slug}, HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEquals(response.data['count'], 1)

        # Another user that owns another project can create a task for that.
        another_task_data = {
            'project': self.another_project.slug,
            'title': 'Translate some text.',
            'description': 'Wie kan Engels vertalen?',
            'time_needed': 5,
            'skill': '{0}'.format(self.skill3.id),
            'location': 'Tiel',
            'deadline': future_date,
            'end_goal': 'World peace'
        }
        response = self.client.post(self.task_url, another_task_data, HTTP_AUTHORIZATION=self.another_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEquals(response.data['title'], another_task_data['title'])

        # Go wild! Add another task to that project add some tags this time --> NO TAGS ANYMORE
        # Because we have a nesting here we should properly encode it as json
        third_task_data = {
            'project': self.another_project.slug,
            'title': 'Translate some text.',
            'description': 'Wie kan Engels vertalen?',
            'time_needed': 5,
            'skill': '{0}'.format(self.skill4.id),
            'location': 'Tiel',
            'deadline': str(future_date),
            'end_goal': 'World peace'
        }
        response = self.client.post(self.task_url, json.dumps(third_task_data), 'application/json', HTTP_AUTHORIZATION=self.another_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEquals(response.data['title'], third_task_data['title'])

        # By now the list for the second project should contain two tasks
        response = self.client.get(self.task_url, {'project': self.another_project.slug}, HTTP_AUTHORIZATION=self.another_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEquals(response.data['count'], 2)

        # Viewing task detail for the first task (other owner) should work
        response = self.client.get(some_task_url, HTTP_AUTHORIZATION=self.another_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEquals(response.data['title'], some_task_data['title'])

    def test_apply_for_task(self):
        future_date = timezone.now() + timezone.timedelta(days=60)

        # let's create a task.
        some_task_data = {
            'project': self.some_project.slug,
            'title': 'A nice task!',
            'description': 'Well, this is nice',
            'time_needed': 5,
            'skill': '{0}'.format(self.skill1.id),
            'location': 'Overthere',
            'deadline': future_date,
            'end_goal': 'World peace'
        }
        response = self.client.post(self.task_url, some_task_data, HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        response = self.client.post(self.task_members_url, {'task': 1}, HTTP_AUTHORIZATION=self.another_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEquals(response.data['status'], 'applied')

    def test_task_search_by_status(self):
        """
        Ensure we can filter task list by status
        """
        self.task1 = TaskFactory.create(
            status=BB_TASK_MODEL.TaskStatuses.in_progress,
            author=self.some_project.owner,
            project=self.some_project,
        )
        self.task2 = TaskFactory.create(
            status=BB_TASK_MODEL.TaskStatuses.open,
            author=self.another_project.owner,
            project=self.another_project,
        )

        self.assertEqual(2, BB_TASK_MODEL.objects.count())

        # Test as a different user
        response = self.client.get(self.task_url, {'status': 'open'}, HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['count'], 1)

        response = self.client.get(self.task_url, {'status': 'in progress'}, HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['count'], 1)

    def test_task_preview_search(self):
        # create project phases
        phase1 = ProjectPhaseFactory.create(viewable=True)
        phase2 = ProjectPhaseFactory.create(viewable=False)

        self.some_project.status = phase1
        self.some_project.save()
        self.another_project.status = phase2
        self.another_project.save()

        # create tasks for projects
        self.task1 = TaskFactory.create(
            status=BB_TASK_MODEL.TaskStatuses.in_progress,
            author=self.some_project.owner,
            project=self.some_project,
        )
        self.task2 = TaskFactory.create(
            status=BB_TASK_MODEL.TaskStatuses.open,
            author=self.another_project.owner,
            project=self.another_project,
        )

        self.assertEqual(2, BB_PROJECT_MODEL.objects.count())
        self.assertEqual(2, BB_TASK_MODEL.objects.count())

        api_url = self.task_url + 'previews/'

        # test that only one task preview is returned
        response = self.client.get(api_url, HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['count'], 1)

        response = self.client.get(api_url, {'status': 'in progress'}, HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['count'], 1)

        response = self.client.get(api_url, {'status': 'open'}, HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['count'], 0)

        skill = self.task1.skill
        response = self.client.get(api_url, {'skill': skill.id}, HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.task1.id)


    def test_delete_task_member(self):
        task = TaskFactory.create()
        task_member = TaskMemberFactory.create(member=self.some_user, task=task)

        self.assertEquals(task.members.count(), 1)

        response = self.client.delete('{0}{1}'.format(self.task_members_url, task_member.id), 
                        'application/json', HTTP_AUTHORIZATION=self.some_token)

        self.assertEquals(task.members.count(),0)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.data)

    def test_delete_task_member_unauthorized(self):
        task = TaskFactory.create()
        task_member = TaskMemberFactory.create(member=self.another_user, task=task)

        self.assertEquals(task.members.count(), 1)

        response = self.client.delete('{0}{1}'.format(self.task_members_url, task_member.id), 
                                        'application/json', HTTP_AUTHORIZATION=self.some_token)

        self.assertEquals(task.members.count(),1)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)


# TODO: Test edit task
# TODO: Test change TaskMember edit status
# TODO: Test File uploads
