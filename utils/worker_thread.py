"""
Worker thread para executar operações Git sem congelar a UI.
Implementa padrão produtor-consumidor com fila thread-safe.
"""
import threading
from queue import Queue
from typing import Callable, Any, Optional
from core.logger_config import get_logger

logger = get_logger()


class WorkerThread(threading.Thread):
    """
    Thread worker que executa tarefas de forma assíncrona.

    Uso:
        worker = WorkerThread(target_func, args=(arg1, arg2),
                            on_success=callback_sucesso,
                            on_error=callback_erro)
        worker.start()
    """

    def __init__(
        self,
        target: Callable,
        args: tuple = (),
        on_success: Optional[Callable[[Any], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        on_finally: Optional[Callable[[], None]] = None
    ):
        super().__init__(daemon=True)
        self.target = target
        self.args = args
        self.on_success = on_success
        self.on_error = on_error
        self.on_finally = on_finally
        self.result = None
        self.exception = None

    def run(self):
        """Executa a tarefa e chama callbacks."""
        try:
            logger.debug(f"Worker iniciado: {self.target.__name__}")
            self.result = self.target(*self.args)

            if self.on_success:
                logger.debug(f"Worker sucesso: {self.target.__name__}")
                self.on_success(self.result)

        except Exception as e:
            logger.error(f"Worker erro em {self.target.__name__}: {e}")
            self.exception = e

            if self.on_error:
                self.on_error(e)

        finally:
            if self.on_finally:
                self.on_finally()
            logger.debug(f"Worker finalizado: {self.target.__name__}")


def run_in_thread(
    func: Callable,
    args: tuple = (),
    on_success: Optional[Callable] = None,
    on_error: Optional[Callable] = None,
    on_finally: Optional[Callable] = None
) -> WorkerThread:
    """
    Executa função em thread separada sem bloquear UI.

    Retorna: WorkerThread (pode usar .join() para aguardar)
    """
    worker = WorkerThread(
        target=func,
        args=args,
        on_success=on_success,
        on_error=on_error,
        on_finally=on_finally
    )
    worker.start()
    return worker

