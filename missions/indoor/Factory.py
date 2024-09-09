
from missions.indoor import Task
from missions.indoor import TaskOne


class TaskFactory:
    @staticmethod
    def create(task) -> Task.Task: 
        tasks = {
            '1': TaskOne.TaskOne

        }
        
        if(not tasks.get(task, None)):
            raise Exception('This task not exists')
        
        return tasks[task]()
    