"""
Testes unitários para git_operations.
"""
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from core.git_operations import (
    GitCommandError,
    run_git_command,
    get_current_branch,
    get_default_main_branch
)


class TestGitOperations(unittest.TestCase):
    """Testes para operações Git base."""

    def setUp(self):
        """Setup comum para todos os testes."""
        self.test_repo_path = "/tmp/test_repo"

    @patch('core.git_operations.subprocess.run')
    def test_run_git_command_success(self, mock_run):
        """Testa execução bem-sucedida de comando Git."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="main\n",
            stderr=""
        )

        result = run_git_command(self.test_repo_path, ["branch"])
        self.assertEqual(result, "main")
        mock_run.assert_called_once()

    @patch('core.git_operations.subprocess.run')
    def test_run_git_command_failure(self, mock_run):
        """Testa falha em comando Git."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="fatal: not a git repository"
        )

        with self.assertRaises(GitCommandError):
            run_git_command(self.test_repo_path, ["branch"])

    @patch('core.git_operations.run_git_command')
    def test_get_current_branch(self, mock_run_git):
        """Testa obtenção de branch atual."""
        mock_run_git.return_value = "feature/new-feature"

        branch = get_current_branch(self.test_repo_path)
        self.assertEqual(branch, "feature/new-feature")

    @patch('core.git_operations.run_git_command')
    def test_get_default_main_branch_via_symbolic_ref(self, mock_run_git):
        """Testa detecção de branch principal via symbolic-ref."""
        mock_run_git.return_value = "refs/remotes/origin/main"

        branch = get_default_main_branch(self.test_repo_path)
        self.assertEqual(branch, "main")

    @patch('core.git_operations.run_git_command')
    def test_get_default_main_branch_fallback(self, mock_run_git):
        """Testa fallback de detecção de branch principal."""
        # Primeira chamada (symbolic-ref) falha
        # Segunda chamada retorna lista de branches
        mock_run_git.side_effect = [
            GitCommandError("error"),
            "  origin/main\n  origin/develop\n"
        ]

        branch = get_default_main_branch(self.test_repo_path)
        self.assertEqual(branch, "main")


class TestGitCommandError(unittest.TestCase):
    """Testes para exceção customizada."""

    def test_git_command_error_creation(self):
        """Testa criação de exceção GitCommandError."""
        error = GitCommandError("test error")
        self.assertEqual(str(error), "test error")

    def test_git_command_error_is_exception(self):
        """Testa se GitCommandError é uma exceção válida."""
        with self.assertRaises(GitCommandError):
            raise GitCommandError("test")


if __name__ == "__main__":
    unittest.main()

