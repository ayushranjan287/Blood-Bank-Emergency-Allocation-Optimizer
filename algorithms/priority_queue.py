class MaxHeap:
    def __init__(self):
        self.heap = []

    def priority_value(self, priority):
        priorities = {
            "Critical": 3,
            "High": 2,
            "Normal": 1
        }
        return priorities.get(priority, 0)

    def insert(self, patient):
        self.heap.append(patient)
        self._heapify_up(len(self.heap) - 1)

    def _heapify_up(self, index):
        while index > 0:
            parent = (index - 1) // 2

            if self.priority_value(self.heap[index]["priority"]) > \
               self.priority_value(self.heap[parent]["priority"]):
                self.heap[index], self.heap[parent] = \
                    self.heap[parent], self.heap[index]
                index = parent
            else:
                break

    def extract_max(self):
        if not self.heap:
            return None

        if len(self.heap) == 1:
            return self.heap.pop()

        highest_priority = self.heap[0]
        self.heap[0] = self.heap.pop()
        self._heapify_down(0)

        return highest_priority

    def _heapify_down(self, index):
        size = len(self.heap)

        while True:
            largest = index
            left = 2 * index + 1
            right = 2 * index + 2

            if left < size and \
               self.priority_value(self.heap[left]["priority"]) > \
               self.priority_value(self.heap[largest]["priority"]):
                largest = left

            if right < size and \
               self.priority_value(self.heap[right]["priority"]) > \
               self.priority_value(self.heap[largest]["priority"]):
                largest = right

            if largest != index:
                self.heap[index], self.heap[largest] = \
                    self.heap[largest], self.heap[index]
                index = largest
            else:
                break