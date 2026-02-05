from django.test import TestCase
from .models import *
from django.contrib.auth.models import User
from django.urls import reverse


# Create your tests here.
class PetitionsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.petition = Petition.objects.create(title='Petition', content='Petition content')

        cls.update = Update.objects.create(title='Update', content='Update content')
        cls.petition.update = cls.update
        cls.petition.save()

        cls.user_1 = User.objects.create_user(username='test', password='test')
        cls.user_2 = User.objects.create_user(username='test2', password='test2')

        cls.petition.signs.add(cls.user_1)
        cls.petition.signs.add(cls.user_2)
        cls.petition.save()

    def test_model_content(self):
        self.assertEqual(self.petition.title, 'Petition')
        self.assertEqual(self.petition.content, 'Petition content')
        self.assertEqual(self.update.title, 'Update')
        self.assertEqual(self.update.content, 'Update content')
        self.assertEqual(self.petition.update.title, 'Update')
        self.assertEqual(self.petition.update.content, 'Update content')
        self.assertEqual(self.petition.signs.count(), 2)
        self.assertEqual(self.petition.signs.first(), self.user_1)
        self.assertEqual(self.petition.signs.last(), self.user_2)

