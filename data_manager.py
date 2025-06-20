import json
import csv
from datetime import datetime
from animal_manager import Animal, Dog, Cat, Bird, Rabbit, Hamster, Turtle

# Klasa zarządzająca danymi zwierząt i adopcji
class DataManager:
    # Inicjalizacja menedżera danych z nazwami plików
    def __init__(self, animals_filename, adoptions_filename):
        self.animals_filename = animals_filename
        self.adoptions_filename = adoptions_filename
        self.animals = {}
        self.adoptions = {}
        self.species_map = {"Pies": Dog, "Kot": Cat, "Ptak": Bird, "Królik": Rabbit, "Chomik": Hamster, "Żółw": Turtle}
        self.load_animals()
        self.load_adoptions()

    # Wczytuje dane zwierząt z pliku JSON
    def load_animals(self):
        try:
            with open(self.animals_filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.animals = {str(k): self.species_map[v["species"]](str(k), v["name"], v["age"]) for k, v in data["animals"].items()}
                for k, v in data["animals"].items():
                    self.animals[str(k)].is_adopted = v["is_adopted"]
                    self.animals[str(k)].is_vaccinated = v["is_vaccinated"]
                    self.animals[str(k)].last_fed = v["last_fed"]
                    self.animals[str(k)].admission_date = v["admission_date"]
                self.next_id = data.get("next_id", 1)
                self.next_adoption_id = data.get("next_adoption_id", 1)
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            self.animals = {}
            self.next_id = 1
            self.next_adoption_id = 1

    # Wczytuje dane adopcji z pliku JSON
    def load_adoptions(self):
        try:
            with open(self.adoptions_filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.adoptions = {str(k): v for k, v in data.get("adoptions", {}).items()}
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            self.adoptions = {}

    # Zapisuje dane zwierząt do pliku JSON
    def save_animals(self, animals, next_id, next_adoption_id):
        try:
            with open(self.animals_filename, 'w', encoding='utf-8') as f:
                json.dump({
                    "animals": {k: {
                        "species": next(s for s, cls in self.species_map.items() if cls == v.__class__),
                        "name": v.name,
                        "age": v.age,
                        "is_adopted": v.is_adopted,
                        "is_vaccinated": v.is_vaccinated,
                        "last_fed": v.last_fed,
                        "admission_date": v.admission_date
                    } for k, v in animals.items()},
                    "next_id": next_id,
                    "next_adoption_id": next_adoption_id
                }, f, indent=4, ensure_ascii=False)
            self.animals = animals
            self.next_id = next_id
            self.next_adoption_id = next_adoption_id
        except Exception as e:
            print(f"Błąd zapisu zwierząt: {e}")

    # Zapisuje dane adopcji do pliku JSON
    def save_adoptions(self, adoptions):
        try:
            with open(self.adoptions_filename, 'w', encoding='utf-8') as f:
                json.dump({"adoptions": adoptions}, f, indent=4, ensure_ascii=False)
            self.adoptions = adoptions
        except Exception as e:
            print(f"Błąd zapisu adopcji: {e}")

    # Zwraca kolejny dostępny ID dla zwierzęcia lub adopcji
    def get_next_id(self):
        return self.next_id

    # Zwraca kolejny dostępny ID dla adopcji
    def get_next_adoption_id(self):
        return self.next_adoption_id

    # Importuje dane zwierząt z pliku CSV
    def import_animals_csv(self, file_path, replace=True):
        errors = []
        new_animals = {} if replace else self.animals.copy()
        new_next_id = 1 if replace else self.next_id
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter=';')
                headers = next(reader)
                if headers != ["ID", "Imię", "Wiek", "Gatunek", "Zaszczepione", "Ostatnie karmienie", "Data przyjęcia", "Status"]:
                    errors.append("Nieprawidłowe nagłówki pliku CSV")
                    return errors
                row_index = 0
                while row_index < len(list(reader)):
                    f.seek(0)
                    reader = csv.reader(f, delimiter=';')
                    next(reader)
                    for row_index, row in enumerate(reader):
                        row_errors = []
                        try:
                            animal_id = row[0].strip()
                            name = row[1].strip()
                            age = int(row[2].strip()) if row[2].strip() else 0
                            species = row[3].strip()
                            is_vaccinated = row[4].strip().lower() == "tak"
                            last_fed = row[5].strip() if row[5].strip() else None
                            admission_date = row[6].strip() if row[6].strip() else None
                            is_adopted = row[7].strip().lower() == "adoptowane"
                            if not name:
                                row_errors.append("Imię nie może być puste")
                            if age < 0:
                                row_errors.append("Wiek musi być nieujemny")
                            if species not in self.species_map:
                                row_errors.append(f"Nieprawidłowy gatunek: {species}")
                            if last_fed:
                                try:
                                    datetime.strptime(last_fed, "%Y-%m-%d %H:%M:%S")
                                except ValueError:
                                    row_errors.append(f"Nieprawidłowy format daty ostatniego karmienia: {last_fed}")
                            if admission_date:
                                try:
                                    datetime.strptime(admission_date, "%Y-%m-%d %H:%M:%S")
                                except ValueError:
                                    row_errors.append(f"Nieprawidłowy format daty przyjęcia: {admission_date}")
                            if animal_id in new_animals:
                                row_errors.append(f"Powielone ID zwierzęcia: {animal_id}")
                            if not row_errors:
                                animal = self.species_map[species](animal_id, name, age)
                                animal.is_vaccinated = is_vaccinated
                                animal.last_fed = last_fed
                                animal.admission_date = admission_date
                                animal.is_adopted = is_adopted
                                new_animals[animal_id] = animal
                                new_next_id = max(new_next_id, int(animal_id) + 1)
                            else:
                                errors.append(f"Wiersz {row_index + 2}: {', '.join(row_errors)}")
                        except Exception as e:
                            errors.append(f"Wiersz {row_index + 2}: Błąd: {str(e)}")
            self.animals = new_animals
            self.next_id = new_next_id
            self.save_animals(self.animals, self.next_id, self.next_adoption_id)
        except Exception as e:
            errors.append(f"Błąd importu: {str(e)}")
        return errors

    # Importuje dane adopcji z pliku CSV
    def import_adoptions_csv(self, file_path, replace=True):
        errors = []
        new_adoptions = {} if replace else self.adoptions.copy()
        new_next_adoption_id = 1 if replace else self.next_adoption_id
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter=';')
                headers = next(reader)
                if headers != ["ID", "ID zwierzęcia", "Nazwisko", "PESEL", "Numer telefonu", "Data adopcji"]:
                    errors.append("Nieprawidłowe nagłówki pliku CSV")
                    return errors
                row_index = 0
                while row_index < len(list(reader)):
                    f.seek(0)
                    reader = csv.reader(f, delimiter=';')
                    next(reader)
                    for row_index, row in enumerate(reader):
                        try:
                            adoption_id = row[0].strip()
                            animal_id = row[1].strip()
                            surname = row[2].strip()
                            pesel = row[3].strip()
                            phone_number = row[4].strip()
                            adoption_date = row[5].strip()
                            if not surname or not pesel.isdigit() or len(pesel) != 11 or not phone_number.isdigit() or len(phone_number) != 9:
                                errors.append(f"Wiersz {row_index + 2}: Nieprawidłowe dane: nazwisko niepuste, PESEL 11 cyfr, telefon 9 cyfr")
                                continue
                            if animal_id not in self.animals:
                                errors.append(f"Wiersz {row_index + 2}: Nie znaleziono zwierzęcia o ID {animal_id}")
                                continue
                            try:
                                datetime.strptime(adoption_date, "%Y-%m-%d %H:%M:%S")
                            except ValueError:
                                errors.append(f"Wiersz {row_index + 2}: Nieprawidłowy format daty adopcji: {adoption_date}")
                                continue
                            if adoption_id in new_adoptions:
                                errors.append(f"Wiersz {row_index + 2}: Powielone ID adopcji: {adoption_id}")
                                continue
                            new_adoptions[adoption_id] = {
                                "animal_id": animal_id,
                                "surname": surname,
                                "pesel": pesel,
                                "phone_number": phone_number,
                                "adoption_date": adoption_date
                            }
                            self.animals[animal_id].is_adopted = True
                            new_next_adoption_id = max(new_next_adoption_id, int(adoption_id) + 1)
                        except Exception as e:
                            errors.append(f"Wiersz {row_index + 2}: Błąd: {str(e)}")
            self.adoptions = new_adoptions
            self.next_adoption_id = new_next_adoption_id
            self.save_adoptions(self.adoptions)
            self.save_animals(self.animals, self.next_id, self.next_adoption_id)
        except Exception as e:
            errors.append(f"Błąd importu: {str(e)}")
        return errors

    # Eksportuje dane zwierząt do pliku CSV
    def export_animals_csv(self, file_path):
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';')
                headers = ("ID", "Imię", "Wiek", "Gatunek", "Zaszczepione", "Ostatnie karmienie", "Data przyjęcia", "Status")
                writer.writerow(headers)
                for animal_id, animal in sorted(self.animals.items(), key=lambda x: int(x[0])):
                    writer.writerow([
                        animal_id,
                        animal.name,
                        animal.age,
                        next(s for s, cls in self.species_map.items() if cls == animal.__class__),
                        "Tak" if animal.is_vaccinated else "Nie",
                        animal.last_fed or "",
                        animal.admission_date or "",
                        "Adoptowane" if animal.is_adopted else "W schronisku"
                    ])
        except Exception as e:
            print(f"Błąd eksportu zwierząt: {e}")

    # Eksportuje dane adopcji do pliku CSV
    def export_adoptions_csv(self, file_path):
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';')
                headers = ("ID", "ID zwierzęcia", "Nazwisko", "PESEL", "Numer telefonu", "Data adopcji")
                writer.writerow(headers)
                for adoption_id, adoption in sorted(self.adoptions.items(), key=lambda x: int(x[0])):
                    writer.writerow([
                        adoption_id,
                        adoption["animal_id"],
                        adoption["surname"],
                        adoption["pesel"],
                        adoption["phone_number"],
                        adoption["adoption_date"]
                    ])
        except Exception as e:
            print(f"Błąd eksportu adopcji: {e}")