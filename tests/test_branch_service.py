"""
Testes unitários para branch_service.
"""
import unittest
from unittest.mock import patch, MagicMock
from services.branch_service import (
    list_branches,
    list_remote_branches,
    create_branch,
    checkout_branch,
    safe_checkout
)
from core.git_operations import GitCommandError


class TestBranchService(unittest.TestCase):
    """Testes para operações de branches."""

    def setUp(self):
        """Setup comum para todos os testes."""
        self.test_repo_path = "/tmp/test_repo"
        # Limpar cache antes de cada teste
        from core.cache import get_cache
        get_cache().clear()

    @patch('services.branch_service.run_git_command')
    def test_list_branches(self, mock_run_git):
        """Testa listagem de branches."""
        mock_run_git.return_value = "* main\n  feature/new\n  develop\n"

        branches = list_branches(self.test_repo_path)
        self.assertIn("main", branches)
        self.assertIn("feature/new", branches)
        self.assertIn("develop", branches)
        self.assertEqual(len(branches), 3)

    @patch('services.branch_service.run_git_command')
    def test_list_branches_empty(self, mock_run_git):
        """Testa listagem vazia de branches."""
        mock_run_git.return_value = ""

        branches = list_branches(self.test_repo_path)
        self.assertEqual(branches, [])

    @patch('services.branch_service.run_git_command')
    def test_list_remote_branches(self, mock_run_git):
        """Testa listagem de branches remotas."""
        mock_run_git.return_value = "  origin/main\n  origin/feature/new\n"

        branches = list_remote_branches(self.test_repo_path)
        self.assertIn("main", branches)
        self.assertIn("feature/new", branches)

    @patch('services.branch_service.run_git_command')
    def test_create_branch(self, mock_run_git):
        """Testa criação de nova branch."""
        mock_run_git.return_value = "Switched to a new branch 'feature/test'"

        result = create_branch(self.test_repo_path, "feature/test")
        self.assertIn("feature/test", result)
        self.assertIn("✅", result)

    @patch('services.branch_service.run_git_command')
    def test_checkout_branch(self, mock_run_git):
        """Testa checkout de branch."""
        mock_run_git.return_value = "Switched to branch 'develop'"

        result = checkout_branch(self.test_repo_path, "develop")
        self.assertIn("develop", result)
        self.assertIn("✅", result)

    @patch('services.branch_service.run_git_command')
    def test_safe_checkout_with_changes(self, mock_run_git):
        """Testa safe_checkout que rejeita mudanças não commitadas."""
        mock_run_git.return_value = " M file.py\n"  # Arquivo modificado

        with self.assertRaises(GitCommandError):
            safe_checkout(self.test_repo_path, "develop")

    @patch('services.branch_service.run_git_command')
    def test_safe_checkout_no_changes(self, mock_run_git):
        """Testa safe_checkout sem mudanças."""
        # Primeira chamada: status vazio
        # Segunda chamada: checkout bem-sucedido
        mock_run_git.side_effect = [
            "",  # status clean
            "Switched to branch 'develop'"
        ]

        result = safe_checkout(self.test_repo_path, "develop")
        self.assertIn("sucesso", result)


class TestBranchServiceErrors(unittest.TestCase):
    """Testes para tratamento de erros em branch_service."""

    def setUp(self):
        """Setup comum."""
        self.test_repo_path = "/tmp/test_repo"
        from core.cache import get_cache
        get_cache().clear()

    @patch('services.branch_service.run_git_command')
    def test_list_branches_error(self, mock_run_git):
        """Testa erro ao listar branches."""
        mock_run_git.side_effect = GitCommandError("Repository not found")

        with self.assertRaises(GitCommandError):
            list_branches(self.test_repo_path)

    @patch('services.branch_service.run_git_command')
    def test_create_branch_error(self, mock_run_git):
        """Testa erro ao criar branch."""
        mock_run_git.side_effect = GitCommandError("Branch already exists")

        with self.assertRaises(GitCommandError):
            create_branch(self.test_repo_path, "existing-branch")


if __name__ == "__main__":
    unittest.main()

