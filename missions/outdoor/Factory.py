from missions.outdoor import TaskTwo
from missions.outdoor import TaskThree
from missions.outdoor import Task

class TaskFactory:
    @staticmethod
    def create(task) -> Task.Task: 
        tasks = {
            '2': TaskTwo.TaskTwo,
            '3': TaskThree.TaskThree,    
        }
        
        if(not tasks.get(task, None)):
            raise Exception('This task not exists')
        
        return tasks[task]()
    