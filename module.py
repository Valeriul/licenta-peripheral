class Module:
    def __init__(self, port):
        self.state = None  # Initialize the state to None
        self.port = port   # Assign the provided port

    def get_state(self):
        pass

class Sensor(Module):
    def __init__(self, port):
        super().__init__(port)  # Call the parent class initializer


class Control(Module):
    def __init__(self, port):
        super().__init__(port)  # Call the parent class initializer

    def set_state(self, state):
        pass