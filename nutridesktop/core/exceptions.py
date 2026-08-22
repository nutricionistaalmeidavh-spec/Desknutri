import sys, traceback
from .logging_setup import configure_logging

def install_exception_hook(show_message=None):
    logger=configure_logging()
    def hook(exc_type, exc, tb):
        logger.error("Unhandled exception", exc_info=(exc_type, exc, tb))
        if show_message:
            show_message("Erro inesperado", "Ocorreu um erro e ele foi registrado. Seus dados não foram apagados.")
        else:
            traceback.print_exception(exc_type, exc, tb)
    sys.excepthook=hook
