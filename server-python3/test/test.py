import threading
import sys
import subprocess


import eventlet
import eventlet.tpool
import eventlet.green.subprocess
from eventlet import green


eventlet.monkey_patch()


def consume(stream, pref=b'T> '):
    print("CHK consume 1")
    p = pref
    while True:
        print("CHK consume 2")
        data = stream.read(1024)
        print("CHK consume 3")
        if not data:
            break
        if p:
            data = p + data
            p = None
        sys.stdout.buffer.write(data.replace(b'\n', b'\n' + pref))
        print("CHK consume 4")
        sys.stdout.flush()
        print("CHK consume 5")


def start_daemon_thread(fn):
    thread = threading.Thread(target=fn)
    thread.daemon = True
    print("CHK start_daemon_thread 1")
    thread.start()
    print("CHK start_daemon_thread 2")
    return thread


def consume_input():
    print("CHK consume_input input")
    while True:
        line = input() + '\n'
        print("CHK consume_input line", line)
        proc.stdin.write(bytes(line, 'ascii'))
        proc.stdin.flush()


proc = green.subprocess.Popen("cmd", stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)


def spawn(fn):
    print("CHK spawn")
    return start_daemon_thread(fn)
    #return eventlet.spawn(fn)
    #return eventlet.tpool.execute(fn)


thread1 = spawn(lambda: consume(proc.stdout, b"T> "))
thread2 = spawn(lambda: consume(proc.stderr, b"E> "))
print("CHK sleeping")
eventlet.sleep(2)

consume_input()
