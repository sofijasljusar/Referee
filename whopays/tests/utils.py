from threading import Thread, Barrier
from django.test import TransactionTestCase
from django.db import connections


class ConcurrentTestCase(TransactionTestCase):
    def run_concurrently(self, funcs):
        barrier = Barrier(len(funcs))
        errors = []

        def runner(fn):
            try:
                barrier.wait()
                fn()
            except Exception as e:
                errors.append(e)
            finally:
                connections.close_all()

        threads = [
            Thread(target=runner, args=(fn,))
            for fn in funcs
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        return errors