from threading import Thread, Barrier
from django.test import TransactionTestCase
from django.db import connections
from queue import Queue


class ConcurrentTestCase(TransactionTestCase):
    def run_concurrently(self, funcs):
        barrier = Barrier(len(funcs))
        errors = Queue()

        def runner(fn):
            try:
                barrier.wait()
                fn()
            except Exception as e:
                errors.put(e)
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

        return list(errors.queue)