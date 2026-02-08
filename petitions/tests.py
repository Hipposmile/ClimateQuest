import io

from PIL import Image
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import *


# Create your tests here.
class PetitionModelTest(TestCase):
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


"""def generate_test_image():
    file = io.BytesIO()
    image = Image.new("RGB", (10, 10), "white")
    image.save(file, "JPEG")
    file.seek(0)
    return SimpleUploadedFile("test.jpg", file.read(), content_type="image/jpeg")


class AddPetitionTests(TestCase):
    def test_missing_fields_shows_error(self):
        response = self.client.post(reverse("add_petition"), {
            "title": "",
            "content": "",
        })

        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("missing_required_inputs", "".join(messages))
        self.assertEqual(Petition.objects.count(), 0)

    def test_invalid_extension(self):
        fake_file = SimpleUploadedFile("test.txt", b"dummy", content_type="text/plain")

        response = self.client.post(reverse("add_petition"), {
            "title": "Test",
            "content": "Test",
        }, files={"img": fake_file})

        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("invalid_file_extension", "".join(messages))
        self.assertEqual(Petition.objects.count(), 0)

    def test_file_too_large(self):
        max_file_size_mb = 5
        big_content = b"a" * (max_file_size_mb * 1024 * 1024 + 1)
        big_file = SimpleUploadedFile("big.jpg", big_content, content_type="image/jpeg")

        response = self.client.post(reverse("add_petition"), {
            "title": "Test",
            "content": "Test",
        }, files={"img": big_file})

        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("size_exceeded_maximum", "".join(messages))
        self.assertEqual(Petition.objects.count(), 0)

    def test_invalid_image(self):
        not_an_image = SimpleUploadedFile("fake.jpg", b"not-an-image", content_type="image/jpeg")

        response = self.client.post(reverse("add_petition"), {
            "title": "Test",
            "content": "Test",
        }, files={"img": not_an_image})

        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("invalid_img", "".join(messages))
        self.assertEqual(Petition.objects.count(), 0)

    def test_successful_petition_creation(self):
        img = generate_test_image()

        response = self.client.post(reverse("add_petition"), {
            "title": "My Petition",
            "content": "Some content",
        }, files={"img": img})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("home"))
        self.assertEqual(Petition.objects.count(), 1)

        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("petition_added", "".join(messages))
"""