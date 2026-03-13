from agent import AIAgent

agent=AIAgent()

while True:

    user_input=input("Enter task:")

    if user_input == "exit":
        break

    agent.run(user_input)



