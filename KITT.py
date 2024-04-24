class KITT:
    def __init__(self, model, color):
        self.model = model
        self.color = color
        self.is_engine_on = False

    def start_engine(self):
        self.is_engine_on = True
        print(f"{self.model}'s engine started.")

    def stop_engine(self):
        self.is_engine_on = False
        print(f"{self.model}'s engine stopped.")

if __name__ == "__main__":
    car1 = KITT("TRX4", "black")    # Make the first instance of KITT
    car2 = KITT("Rustler", "red")   # Make the second instance of KITT

    car2.color = "blue"             # Change the color of
    car1.start_engine()             # Start the engine of car1
    print(car1.is_engine_on)        # Output: "True"
    print(car1.model)               # Output: "TRX4"
    print(car1.color)               # Output: "black"
