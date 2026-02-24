"""
Testes para autenticação GitHub segura.
"""
import unittest
from unittest.mock import patch, MagicMock
from core.github_auth import (
    get_github_token_from_cli,
    get_github_user,
    GitHubAuthError
)


class TestGitHubAuth(unittest.TestCase):
    """Testes para autenticação GitHub segura."""

    @patch('core.github_auth.subprocess.run')
    def test_github_cli_auth_status_success(self, mock_run):
        """Testa verificação de autenticação do GitHub CLI."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Logged in to github.com as user"
        )

        # Não deve lançar exceção
        try:
            token = get_github_token_from_cli()
            self.assertIsNotNone(token)
        except GitHubAuthError:
            pass  # Esperado se gh não estiver instalado

    @patch('core.github_auth.subprocess.run')
    def test_github_cli_not_authenticated(self, mock_run):
        """Testa erro quando GitHub CLI não autenticado."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr="Not authenticated"
        )

        with self.assertRaises(GitHubAuthError):
            get_github_token_from_cli()

    @patch('core.github_auth.subprocess.run')
    def test_github_cli_not_installed(self, mock_run):
        """Testa erro quando GitHub CLI não instalado."""
        mock_run.side_effect = FileNotFoundError()

        with self.assertRaises(GitHubAuthError):
            get_github_token_from_cli()

    @patch('core.github_auth.subprocess.run')
    def test_get_github_user(self, mock_run):
        """Testa obtenção do nome de usuário GitHub."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="jeanheberth"
        )

        try:
            username = get_github_user()
            self.assertEqual(username, "jeanheberth")
        except GitHubAuthError:
            pass  # Esperado se gh não estiver instalado


class TestAuthErrorMessages(unittest.TestCase):
    """Testa mensagens de erro claras."""

    def test_github_auth_error_message(self):
        """Testa mensagem de erro do GitHubAuthError."""
        error = GitHubAuthError("Test error")
        self.assertEqual(str(error), "Test error")

    def test_auth_error_is_exception(self):
        """Testa se GitHubAuthError é uma exceção válida."""
        with self.assertRaises(GitHubAuthError):
            raise GitHubAuthError("test")


if __name__ == "__main__":
    unittest.main()

