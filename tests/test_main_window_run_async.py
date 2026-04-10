from unittest.mock import MagicMock, patch

# Testa que _run_async rejeita agendamento duplicado quando is_loading True

def test_run_async_rejects_when_loading(monkeypatch):
    # Import MainWindow lazily
    from ui.main_window import MainWindow

    win = MainWindow.__new__(MainWindow)
    # Não inicializar tkinter internals; criar atributos usados
    win.is_loading = True
    win.log = MagicMock()

    # Mock run_in_thread para garantir que não seja chamado
    with patch('ui.main_window.run_in_thread') as mock_run:
        result = win._run_async(lambda: None)
        # Verifica que run_in_thread NÃO foi chamado e mensagem foi logada
        mock_run.assert_not_called()
        win.log.assert_called()
        assert result is None


def test_run_async_allows_when_not_loading(monkeypatch):
    from ui.main_window import MainWindow

    win = MainWindow.__new__(MainWindow)
    win.is_loading = False
    win.log = MagicMock()

    # Mock run_in_thread para capture callbacks
    calls = {}

    def fake_run(func, args=(), on_success=None, on_error=None, on_finally=None):
        # Simular execução síncrona do worker
        try:
            res = func(*args)
            if on_success:
                on_success(res)
        except Exception as e:
            if on_error:
                on_error(e)
        finally:
            if on_finally:
                on_finally()
        calls['ran'] = True
        return MagicMock()

    with patch('ui.main_window.run_in_thread', new=fake_run):
        def work():
            return 'ok'

        called = {'ok': False}

        def on_success(res):
            called['ok'] = True
            assert res == 'ok'

        res = win._run_async(work, on_success=on_success)
        assert calls.get('ran', False)
        assert called['ok']
        # Depois da execução, is_loading deve ser False
        assert win.is_loading is False


