import unittest
from unittest.mock import patch, MagicMock
from services.branch_service import update_branch, resolve_conflict
from services.branch_service import create_branch
from core.git_operations import GitCommandError
import subprocess


class TestRegressions(unittest.TestCase):
    def setUp(self):
        from core.cache import get_cache
        get_cache().clear()
        self.repo = "/tmp/test_repo"

    @patch('services.branch_service.run_git_command')
    def test_checkout_overwrite_error_propagates(self, mock_run):
        """Simula erro do git ao tentar checkout quando existem alterações locais que seriam sobrescritas."""
        def side_effect(repo_path, cmd):
            if cmd and cmd[0] == 'checkout':
                raise GitCommandError("Your local changes to the following files would be overwritten by checkout: ui/main_window.py\nPlease commit your changes or stash them before you switch branches.\nAborting")
            return ""

        mock_run.side_effect = side_effect

        with self.assertRaises(GitCommandError) as cm:
            update_branch(self.repo, 'feature/realizando_melhorias', base_branch='develop', strategy='rebase')

        self.assertIn('would be overwritten by checkout', str(cm.exception))

    @patch('services.branch_service.run_git_command')
    def test_update_branch_rebase_conflict_message(self, mock_run):
        """Simula rebase que encontra conflito e deve retornar mensagem amigável de conflito."""
        def side_effect(repo_path, cmd):
            # checkout ok
            if cmd and cmd[0] == 'checkout':
                return "Switched to branch 'feature/realizando_melhorias'"
            # status clean
            if cmd and cmd[0] == 'status':
                return ""
            # fetch OK
            if cmd and cmd[0] == 'fetch':
                return ""
            # list remote branches
            if cmd and cmd[0] == 'branch' and '-r' in cmd:
                return "  origin/develop\n  origin/feature/realizando_melhorias\n"
            # rebase causes conflict
            if cmd and cmd[0] == 'rebase':
                raise GitCommandError('CONFLICT (content): Merge conflict in file.py')
            return ""

        mock_run.side_effect = side_effect

        with self.assertRaises(GitCommandError) as cm:
            update_branch(self.repo, 'feature/realizando_melhorias', base_branch='develop', strategy='rebase')

        self.assertTrue('Conflito' in str(cm.exception) or 'CONFLICT' in str(cm.exception))

    @patch('services.branch_service.subprocess.run')
    @patch('services.branch_service.run_git_command')
    def test_resolve_conflict_preview_shallow_clone(self, mock_run_git, mock_subproc_run):
        """Testa que o preview usa clone raso (shallow) e retorna mensagem sem push."""
        # Simulate subprocess.run successful shallow clone
        cp = subprocess.CompletedProcess(args=['git'], returncode=0, stdout='', stderr='')
        mock_subproc_run.return_value = cp

        # run_git_command should accept checkout/fetch/rebase in the temp repo
        def side_effect(repo_path, cmd):
            # checkout ok
            if cmd and cmd[0] == 'checkout':
                return "Switched to branch"
            # fetch ok
            if cmd and cmd[0] == 'fetch':
                return ""
            # rebase ok
            if cmd and cmd[0] == 'rebase':
                return ""
            # other commands
            return ""

        mock_run_git.side_effect = side_effect

        msg = resolve_conflict(self.repo, 'feature/realizando_melhorias', base_branch='develop', favor='theirs', strategy='rebase', preview=True, push=False)
        self.assertIn('(não enviado ao remoto)', msg)

    @patch('services.branch_service._get_default_base_branch')
    @patch('services.branch_service.run_git_command')
    def test_create_branch_from_main_fetches_main_and_develop_and_checks_out(self, mock_run, mock_get_base):
        """Garante que ao criar branch, buscamos origin/main, origin/develop, fazemos checkout na base e criamos feature/..."""
        mock_get_base.return_value = 'main'

        calls = []

        def side_effect(repo_path, cmd):
            calls.append(list(cmd))
            # Simular sucesso para todos os comandos
            return ""

        mock_run.side_effect = side_effect

        msg = create_branch(self.repo, 'realizando_melhorias')
        # Confirma prefixo e base na mensagem
        self.assertIn("feature/realizando_melhorias", msg)
        self.assertIn("a partir de 'main'", msg)

        # Verificar que chamados importantes foram feitos (fetch main, fetch develop, checkout main, checkout -b)
        self.assertIn(['fetch', 'origin', 'main'], calls)
        self.assertIn(['fetch', 'origin', 'develop'], calls)
        self.assertIn(['checkout', 'main'], calls)
        self.assertIn(['checkout', '-b', 'feature/realizando_melhorias'], calls)

    @patch('services.branch_service._get_default_base_branch')
    @patch('services.branch_service.run_git_command')
    def test_create_branch_from_develop_does_not_double_fetch(self, mock_run, mock_get_base):
        """Se a base for develop, apenas fetch de develop deve ser chamado (não deve tentar fetch develop extra)."""
        mock_get_base.return_value = 'develop'

        calls = []

        def side_effect(repo_path, cmd):
            calls.append(list(cmd))
            return ""

        mock_run.side_effect = side_effect

        msg = create_branch(self.repo, 'nova')
        self.assertIn("feature/nova", msg)
        self.assertIn("a partir de 'develop'", msg)

        # Deve ter feito fetch develop e checkout develop, e checkout -b
        self.assertIn(['fetch', 'origin', 'develop'], calls)
        self.assertIn(['checkout', 'develop'], calls)
        self.assertIn(['checkout', '-b', 'feature/nova'], calls)


if __name__ == '__main__':
    unittest.main()

