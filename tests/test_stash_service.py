"""
Testes unitários para stash_service.
"""
import unittest
from unittest.mock import patch, MagicMock
from services.stash_service import (
    stash_save,
    stash_list,
    stash_apply,
    stash_pop,
    stash_drop,
    stash_clear
)
from core.git_operations import GitCommandError


class TestStashService(unittest.TestCase):
    """Testes para operações de stash."""

    def setUp(self):
        """Setup comum para todos os testes."""
        self.test_repo_path = "/tmp/test_repo"

    @patch('services.stash_service.run_git_command')
    def test_stash_save_with_changes(self, mock_run):
        """Testa salvar stash quando há alterações."""
        # Mock para verificar alterações
        mock_run.side_effect = [
            "M file.py\n",  # status com alterações
            ""  # stash save
        ]

        result = stash_save(self.test_repo_path, "test message")

        self.assertIn("Stash salvo", result)
        self.assertEqual(mock_run.call_count, 2)

    @patch('services.stash_service.run_git_command')
    def test_stash_save_no_changes(self, mock_run):
        """Testa salvar stash quando não há alterações."""
        mock_run.return_value = ""  # status vazio

        result = stash_save(self.test_repo_path)

        self.assertIn("Não há alterações", result)

    @patch('services.stash_service.run_git_command')
    def test_stash_list_with_stashes(self, mock_run):
        """Testa listar stashes quando existem stashes."""
        mock_run.return_value = "stash@{0}: WIP on main\nstash@{1}: test stash"

        result = stash_list(self.test_repo_path)

        self.assertEqual(len(result), 2)
        self.assertIn("stash@{0}", result[0])

    @patch('services.stash_service.run_git_command')
    def test_stash_list_empty(self, mock_run):
        """Testa listar stashes quando não existem."""
        mock_run.return_value = ""

        result = stash_list(self.test_repo_path)

        self.assertEqual(result, [])

    @patch('services.stash_service.run_git_command')
    def test_stash_apply_success(self, mock_run):
        """Testa aplicar stash com sucesso."""
        mock_run.return_value = ""

        result = stash_apply(self.test_repo_path, "stash@{0}")

        self.assertIn("aplicado com sucesso", result)
        mock_run.assert_called_once_with(
            self.test_repo_path,
            ["stash", "apply", "stash@{0}"]
        )

    @patch('services.stash_service.run_git_command')
    def test_stash_pop_success(self, mock_run):
        """Testa aplicar e remover stash com sucesso."""
        mock_run.return_value = ""

        result = stash_pop(self.test_repo_path, "stash@{0}")

        self.assertIn("aplicado e removido", result)
        mock_run.assert_called_once_with(
            self.test_repo_path,
            ["stash", "pop", "stash@{0}"]
        )

    @patch('services.stash_service.run_git_command')
    def test_stash_drop_success(self, mock_run):
        """Testa remover stash com sucesso."""
        mock_run.return_value = ""

        result = stash_drop(self.test_repo_path, "stash@{0}")

        self.assertIn("removido com sucesso", result)
        mock_run.assert_called_once_with(
            self.test_repo_path,
            ["stash", "drop", "stash@{0}"]
        )

    @patch('services.stash_service.stash_list')
    @patch('services.stash_service.run_git_command')
    def test_stash_clear_with_stashes(self, mock_run, mock_list):
        """Testa limpar todos os stashes."""
        mock_list.return_value = ["stash@{0}: test", "stash@{1}: test2"]
        mock_run.return_value = ""

        result = stash_clear(self.test_repo_path)

        self.assertIn("Todos os stashes", result)
        self.assertIn("2", result)

    @patch('services.stash_service.stash_list')
    def test_stash_clear_no_stashes(self, mock_list):
        """Testa limpar quando não há stashes."""
        mock_list.return_value = []

        result = stash_clear(self.test_repo_path)

        self.assertIn("Não há stashes", result)


class TestStashServiceErrors(unittest.TestCase):
    """Testes para tratamento de erros nas operações de stash."""

    def setUp(self):
        """Setup comum para todos os testes."""
        self.test_repo_path = "/tmp/test_repo"

    @patch('services.stash_service.run_git_command')
    def test_stash_apply_error(self, mock_run):
        """Testa erro ao aplicar stash."""
        mock_run.side_effect = GitCommandError("Stash not found")

        with self.assertRaises(GitCommandError):
            stash_apply(self.test_repo_path, "stash@{99}")

    @patch('services.stash_service.run_git_command')
    def test_stash_pop_error(self, mock_run):
        """Testa erro ao aplicar e remover stash."""
        mock_run.side_effect = GitCommandError("Stash not found")

        with self.assertRaises(GitCommandError):
            stash_pop(self.test_repo_path, "stash@{99}")


if __name__ == "__main__":
    unittest.main()

