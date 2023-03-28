import queue


class TaskQueue:
    def __init__(self):
        self._q = queue.Queue()

    def add_task(self, task):
        self._q.put(task)

    def start(self):
        while True:
            task = self._q.get()
            try:
                task.run()
            except Exception as e:
                print(f"Error running task: {e}")
            finally:
                self._q.task_done()

    def empty(self):
        return self._q.empty()
