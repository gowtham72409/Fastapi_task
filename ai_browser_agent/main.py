from agent import AIAgent

if __name__ == "__main__":

    agent = AIAgent()

    task = input("Enter task: ")

    agent.run(task)