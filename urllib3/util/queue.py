import collections
from ..packages import six
from ..packages.six.moves import queue

if six.PY2:
    # Queue is imported for side effects on MS Windows. See issue #229.
    import Queue as _unused_module_Queue  # noqa: F401


class LifoQueue(queue.Queue):
    def _init(self, _):
        """
        Initialize the queue.

        Args:
            self: (todo): write your description
            _: (str): write your description
        """
        self.queue = collections.deque()

    def _qsize(self, len=len):
        """
        Returns the number of bytes in the queue.

        Args:
            self: (todo): write your description
            len: (todo): write your description
            len: (todo): write your description
        """
        return len(self.queue)

    def _put(self, item):
        """
        Put an item into the queue.

        Args:
            self: (todo): write your description
            item: (todo): write your description
        """
        self.queue.append(item)

    def _get(self):
        """
        Get the next item from the queue.

        Args:
            self: (todo): write your description
        """
        return self.queue.pop()
