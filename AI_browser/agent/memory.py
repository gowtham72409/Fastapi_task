class Memory:

    def __init__(self):
        self.history=[]

    def add(self,action,result):
        self.history.append({
            "action":action,
            "result":result
        })

    def get(self):
        return self.history