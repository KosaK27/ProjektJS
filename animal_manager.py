from datetime import datetime, timedelta

# Bazowa klasa dla zwierząt
class Animal:
    # Inicjalizacja zwierzęcia z podstawowymi atrybutami
    def __init__(self, id, name, age):
        self.id = id
        self.name = name
        self.age = age
        self.is_adopted = False
        self.is_vaccinated = False
        self.last_fed = None
        self.admission_date = None

    # Zwraca status ostatniego karmienia
    def get_feeding_status(self):
        if not self.last_fed:
            return "Brak danych"
        try:
            last_fed_time = datetime.strptime(self.last_fed, "%Y-%m-%d %H:%M:%S")
            delta = datetime.now() - last_fed_time
            hours = int(delta.total_seconds() // 3600)
            return f"{hours} godziny temu"
        except ValueError:
            return "Nieprawidłowy format daty"

# Klasa dla psów, dziedzicząca po Animal
class Dog(Animal):
    pass

# Klasa dla kotów, dziedzicząca po Animal
class Cat(Animal):
    pass

# Klasa dla ptaków, dziedzicząca po Animal
class Bird(Animal):
    pass

# Klasa dla królików, dziedzicząca po Animal
class Rabbit(Animal):
    pass

# Klasa dla chomików, dziedzicząca po Animal
class Hamster(Animal):
    pass

# Klasa dla żółwi, dziedzicząca po Animal
class Turtle(Animal):
    pass