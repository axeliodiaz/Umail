import json
import os
import subprocess
import sys
from unittest.mock import MagicMock, patch

from django.core.mail import EmailMultiAlternatives
from django.test import SimpleTestCase, override_settings

from django_messages.models import Message
from django_messages.utils import new_message_email


def _settings_probe(extra_env):
    """Load umail.settings in a subprocess with a clean environment."""
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = {
        'PATH': os.environ.get('PATH', ''),
        'HOME': os.environ.get('HOME', ''),
        'DJANGO_SETTINGS_MODULE': 'umail.settings',
        'PYTHONPATH': repo_root,
    }
    env.update(extra_env)
    code = (
        'import django\n'
        'from django.conf import settings\n'
        'django.setup()\n'
        'print(settings.EMAIL_BACKEND)\n'
        'print(settings.DEFAULT_FROM_EMAIL)\n'
    )
    result = subprocess.run(
        [sys.executable, '-c', code],
        cwd=repo_root,
        env={**os.environ, **env},
        capture_output=True,
        text=True,
        check=True,
    )
    lines = result.stdout.strip().splitlines()
    return lines[0], lines[1]


class EmailSettingsTests(SimpleTestCase):
    def test_console_backend_without_resend_key(self):
        backend, _from = _settings_probe({'RESEND_API_KEY': ''})
        self.assertEqual(backend, 'django.core.mail.backends.console.EmailBackend')

    def test_resend_backend_when_api_key_set(self):
        backend, _from = _settings_probe({'RESEND_API_KEY': 're_test_key_not_real'})
        self.assertEqual(backend, 'anymail.backends.resend.EmailBackend')

    def test_default_from_email_default(self):
        _backend, from_email = _settings_probe({'RESEND_API_KEY': ''})
        self.assertEqual(from_email, 'Umail <noreply@mail.axeldiaz.com>')

    def test_default_from_email_override(self):
        _backend, from_email = _settings_probe({
            'RESEND_API_KEY': '',
            'DEFAULT_FROM_EMAIL': 'Custom <custom@example.com>',
        })
        self.assertEqual(from_email, 'Custom <custom@example.com>')


@override_settings(
    EMAIL_BACKEND='anymail.backends.resend.EmailBackend',
    ANYMAIL={'RESEND_API_KEY': 're_test_key_not_real'},
    DEFAULT_FROM_EMAIL='Umail <noreply@mail.axeldiaz.com>',
)
class ResendPayloadTests(SimpleTestCase):
    @patch('anymail.backends.base_requests.AnymailRequestsBackend.post_to_esp')
    def test_text_and_html_email_payload_to_resend(self, mock_post):
        response = MagicMock()
        response.status_code = 200
        response.text = json.dumps({'id': 'msg_123'})
        response.headers = {}
        mock_post.return_value = response

        msg = EmailMultiAlternatives(
            subject='Test subject',
            body='Plain body',
            from_email='Umail <noreply@mail.axeldiaz.com>',
            to=['recipient@example.com'],
        )
        msg.attach_alternative('<p>HTML body</p>', 'text/html')
        msg.send()

        self.assertTrue(mock_post.called)
        payload = mock_post.call_args[0][0]
        data = payload.data
        self.assertEqual(data['from'], 'Umail <noreply@mail.axeldiaz.com>')
        self.assertEqual(data['to'], ['recipient@example.com'])
        self.assertEqual(data['subject'], 'Test subject')
        self.assertEqual(data['text'], 'Plain body')
        self.assertEqual(data['html'], '<p>HTML body</p>')


class NewMessageEmailTests(SimpleTestCase):
    def _message_instance(self, pk=42):
        recipient = MagicMock()
        recipient.email = 'recipient@example.com'
        message = MagicMock()
        message.pk = pk
        message.subject = 'Hola'
        message.recipient = recipient
        return message

    @override_settings(DEFAULT_FROM_EMAIL='Umail <noreply@mail.axeldiaz.com>')
    @patch('django_messages.utils.render_to_string', return_value='notification body')
    @patch('django_messages.utils.Site.objects.get_current')
    @patch('django_messages.utils.send_mail')
    def test_new_message_email_sends_notification(
        self, mock_send_mail, mock_get_site, _mock_render,
    ):
        mock_get_site.return_value.domain = 'example.com'
        message = self._message_instance()
        new_message_email(Message, message, signal=None, created=True)
        mock_send_mail.assert_called_once()
        args = mock_send_mail.call_args[0]
        self.assertIn('Hola', args[0])
        self.assertEqual(args[2], 'Umail <noreply@mail.axeldiaz.com>')
        self.assertEqual(args[3], ['recipient@example.com'])

    @override_settings(DEFAULT_FROM_EMAIL='Umail <noreply@mail.axeldiaz.com>')
    @patch('django_messages.utils.render_to_string', return_value='notification body')
    @patch('django_messages.utils.Site.objects.get_current')
    @patch('django_messages.utils.send_mail')
    def test_new_message_email_uses_default_from(
        self, mock_send_mail, mock_get_site, _mock_render,
    ):
        mock_get_site.return_value.domain = 'example.com'
        message = self._message_instance()
        new_message_email(Message, message, signal=None, created=True)
        self.assertEqual(mock_send_mail.call_args[0][2], 'Umail <noreply@mail.axeldiaz.com>')

    @patch('django_messages.utils.render_to_string', return_value='notification body')
    @patch('django_messages.utils.Site.objects.get_current')
    @patch('django_messages.utils.logger.warning')
    @patch(
        'django_messages.utils.send_mail',
        side_effect=RuntimeError('API error for recipient@secret.example body leaked'),
    )
    def test_new_message_email_logs_sanitized_failure(
        self, _mock_send, mock_warning, mock_get_site, _mock_render,
    ):
        mock_get_site.return_value.domain = 'example.com'
        message = self._message_instance(pk=99)
        new_message_email(Message, message, signal=None, created=True)
        mock_warning.assert_called_once()
        log_args = ' '.join(str(a) for a in mock_warning.call_args[0])
        self.assertIn('message_id', log_args)
        self.assertIn('99', log_args)
        self.assertNotIn('recipient@secret.example', log_args)
        self.assertNotIn('Private', log_args)
        self.assertNotIn('leaked', log_args)
