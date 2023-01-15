#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import threading
import time
from queue import Queue
from threading import Thread


class ThreadPoolManger:
    """线程池管理器"""

    def __init__(self, thread_num):
        # 初始化参数
        self.work_queue = Queue()
        self.results_queue = Queue()
        self.thread_num = thread_num
        self.__init_threading_pool(self.thread_num)

    def __init_threading_pool(self, thread_num):
        # 初始化线程池，创建指定数量的线程池
        for i in range(thread_num):
            thread = ThreadManger(self.work_queue, self.results_queue)
            thread.start()

    def add_job(self, func, *args):
        # 将任务放入队列，等待线程池阻塞读取，参数是被执行的函数和函数的参数
        self.work_queue.put((func, args))

    def get_thread_num(self) -> int:
        return self.work_queue.qsize()

    def get_results(self) -> list:
        # 获取所有的线程的执行结果
        # while not self.results_queue.empty():
        #     yield self.results_queue.get()
        return list(self.results_queue.queue)

    def wait_finish(self, delay: int = 1) -> list:
        while True:
            if self.get_thread_num() > 0:
                time.sleep(delay)
            else:
                self.work_queue.join()  # 阻塞主线程，等待队列中的任务执行完毕
                # break
                return self.get_results()


class ThreadManger(Thread):
    """定义线程类，继承threading.Thread"""

    def __init__(self, work_queue, results_queue):
        Thread.__init__(self)
        self.work_queue = work_queue
        self.results_queue = results_queue
        self.daemon = True

    def run(self):
        # 启动线程
        while True:
            target, args = self.work_queue.get()
            self.results_queue.put(target(*args))  # 将任务执行结果放入结果队列
            self.work_queue.task_done()  # 已完成信号


# 处理中心
def handle_request(param):
    delay = random.randint(1, 10)
    time.sleep(delay)
    print(f"thread {threading.current_thread().name} is running", param)


if __name__ == '__main__':
    # 创建一个有4个线程的线程池
    thread_pool = ThreadPoolManger(4)

    # 循环
    while True:
        thread_pool.add_job(handle_request, "args")
        time.sleep(1)
