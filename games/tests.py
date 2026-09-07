from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from games.models import Label


class LabelManagementTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="secret"
        )
        self.label = Label.objects.create(
            label="Nouveau",
            description="Jeu jamais joué."
        )

    def test_labels_views_require_login(self):
        """Les vues de gestion des labels doivent exiger une connexion."""
        urls = [
            reverse("labels_index"),
            reverse("add_label"),
            reverse("update_label", args=[self.label.id]),
            reverse("delete_label", args=[self.label.id]),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn("/accounts", response.url)

    def test_labels_index_lists_labels(self):
        self.client.login(username="testuser", password="secret")
        response = self.client.get(reverse("labels_index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nouveau")

    def test_add_label(self):
        self.client.login(username="testuser", password="secret")
        response = self.client.post(
            reverse("add_label"),
            {"label": "Abîmé", "description": "Boîte endommagée."},
        )
        self.assertRedirects(response, reverse("labels_index"))
        self.assertTrue(Label.objects.filter(label="Abîmé").exists())

    def test_add_label_requires_fields(self):
        self.client.login(username="testuser", password="secret")
        response = self.client.post(reverse("add_label"), {"label": ""})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ce champ est obligatoire.")

    def test_update_label(self):
        self.client.login(username="testuser", password="secret")
        response = self.client.post(
            reverse("update_label", args=[self.label.id]),
            {"label": "Rare", "description": "Édition limitée."},
        )
        self.assertRedirects(response, reverse("labels_index"))
        self.label.refresh_from_db()
        self.assertEqual(self.label.label, "Rare")
        self.assertEqual(self.label.description, "Édition limitée.")

    def test_delete_label(self):
        self.client.login(username="testuser", password="secret")
        response = self.client.post(
            reverse("delete_label", args=[self.label.id])
        )
        self.assertRedirects(response, reverse("labels_index"))
        self.assertFalse(Label.objects.filter(id=self.label.id).exists())
