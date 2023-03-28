import queue
from nonebot import require

require("nonebot_plugin_apscheduler")

from nonebot_plugin_apscheduler import scheduler


class TaskQueue:
    def __init__(self):
        self._q = queue.Queue()

    def add_task(self, task):
        self._q.put(task)

    @scheduler.scheduled_job("cron", second="*/2", id="job_0")
    def start(self):
        task = self._q.get()
        try:
            task.run()
        except Exception as e:
            print(f"Error running task: {e}")
        finally:
            self._q.task_done()

    def empty(self):
        return self._q.empty()
