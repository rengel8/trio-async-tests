import trio
import random
import time
import threading

cycles = 4

class Tracer(trio.abc.Instrument):
    def before_run(self):
        print("!!! run started")

    def _print_with_task(self, msg, task):
        # repr(task) is perhaps more useful than task.name in general,
        # but in context of a tutorial the extra noise is unhelpful.
        print("{}: {}".format(msg, task.name))

    def task_spawned(self, task):
        self._print_with_task("### new task spawned", task)

    def task_scheduled(self, task):
        self._print_with_task("### task scheduled", task)

    def before_task_step(self, task):
        self._print_with_task(">>> about to run one step of task", task)

    def after_task_step(self, task):
        self._print_with_task("<<< task step finished", task)

    def task_exited(self, task):
        self._print_with_task("### task exited", task)

    def before_io_wait(self, timeout):
        if timeout:
            print("### waiting for I/O for up to {} seconds".format(timeout))
        else:
            print("### doing a quick check for I/O")
        self._sleep_time = trio.current_time()

    def after_io_wait(self, timeout):
        duration = trio.current_time() - self._sleep_time
        print("### finished I/O check (took {} seconds)".format(duration))

    def after_run(self):
        print("!!! run finished")


# Sync.........................................................
t1 = time.time()
def rand_number():
    n = 0
    for i in range(0, 1000000):
        n1 = random.randint(1, 99)
        n2 = random.randint(1, 99)
        n = n + ((n1 * n2) ** .5)
    return n

def rand_sync():
    for i in range(0, cycles):
        print(' - cycle', (i + 1), '..', rand_number())
    return 'done'
rand_sync()
print("sync performance (seconds)", time.time() - t1, 'per cycle:', (time.time() - t1) / cycles)
# -------------------------------------------------------------


# Async1.......................................................
t1 = time.time()
async def rand_async():
    async with trio.open_nursery() as nursery:
        randomlist = []
        for i in range(0, 1000000):
            n1 = random.randint(1, 99)
            n2 = random.randint(1, 99)
            n = (n1 * n2) ** .5
            randomlist.append(n)
            nursery.cancel_scope.cancel()
    return randomlist
trio.run(rand_async)
print("\nasync1 performance (seconds)", time.time() - t1, 'for one cycle')
# -------------------------------------------------------------


# Async2.......................................................
t1 = time.time()
async def rand_number2():
    n = 0
    for i in range(0, 1000000):
        n1 = random.randint(1, 99)
        n2 = random.randint(1, 99)
        n = n + ((n1 * n2) ** .5)
    return n

async def rand_async2():
    async with trio.open_nursery() as nursery:
        for i in range(0, cycles):
            nursery.start_soon(rand_number2)
        nursery.cancel_scope.cancel()
    return 'ready'
trio.run(rand_async2)
print("\nasync2 performance (seconds)", time.time() - t1)
# -------------------------------------------------------------

'''
# Async3 - multi-threading.....................................
t1 = time.time()
async def rand_number3():
    n = 0
    for i in range(0, 1000000):
        n1 = random.randint(1, 99)
        n2 = random.randint(1, 99)
        n = n + ((n1 * n2) ** .5)
    return n

async def rand_async3():
    async with trio.open_nursery() as nursery:
        for i in range(0, cycles):
            nursery.start_soon(rand_number3)
        nursery.cancel_scope.cancel()
    return 'ready'
trio.run(rand_async3)
print("\nasync3 mt performance (seconds)", time.time() - t1)
# -------------------------------------------------------------
'''


# multi-threading.....................................
t1 = time.time()
print('')
def rand_number3(i):
    n = 0
    for i in range(0, 1000000):
        n1 = random.randint(1, 99)
        n2 = random.randint(1, 99)
        n = n + ((n1 * n2) ** .5)
    # sleep(random.randint(1, 3))
    print(' - ', n,',', threading.current_thread().getName())
    #print(threading.current_thread().getName())
    return n

def rand_mt():
    for i in range(0, cycles):
        t = threading.Thread(target=rand_number3, args=(i,))
        t.setName('Thread#' + str(i))
        t.start()
    t.join()
    return 'ready'
rand_mt()
print("mt performance (seconds)", time.time() - t1)
# -------------------------------------------------------------
