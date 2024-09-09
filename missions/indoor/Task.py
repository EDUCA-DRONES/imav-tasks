from abc import ABC, abstractmethod

class Task(ABC):
    @abstractmethod
    def run(self):
        raise Exception('Needed to implement this method')
    