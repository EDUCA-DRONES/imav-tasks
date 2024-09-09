from missions.indoor.Factory import TaskFactory

task = TaskFactory.create(input('Informe a task: '))
task.run()