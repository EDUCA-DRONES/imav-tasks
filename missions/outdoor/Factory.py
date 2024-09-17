from missions.outdoor import TaskOneClient, TaskTwo
from missions.outdoor import TaskThree
from missions.outdoor import Task
from missions.outdoor import TaskFour

from missions.outdoor import TaskOne


class TaskFactory:
    @staticmethod
    def create(task) -> Task.Task: 
        tasks = {
            '1': TaskOne.TaskOne,
            '2': TaskTwo.TaskTwo,
            '3': TaskThree.TaskThree,    
            '4': TaskFour.TaskFour,
            '1-2': TaskOneClient.TaskOneClient

        }
        
        if(not tasks.get(task, None)):
            raise Exception('This task not exists')
        
        return tasks[task]()
    