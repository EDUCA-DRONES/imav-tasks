from missions.outdoor import TaskTwo
from missions.outdoor import TaskThree
from missions.outdoor import Task
from missions.outdoor import TaskFour

from missions.indoor import TaskOne


class TaskFactory:
    @staticmethod
    def create(task) -> Task.Task: 
        tasks = {
            '2': TaskTwo.TaskTwo,
            '3': TaskThree.TaskThree,    
            '4': TaskFour.TaskFour,
            '11': TaskOne.TaskOne

        }
        
        if(not tasks.get(task, None)):
            raise Exception('This task not exists')
        
        return tasks[task]()
    