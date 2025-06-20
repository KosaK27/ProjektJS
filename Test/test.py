import unittest
import pytest
import os
from datetime import datetime
from tkinter import Tk
from memory_profiler import profile
import timeit
from animal_manager import Dog
from data_manager import DataManager
from main import ShelterApp

class TestAll(unittest.TestCase):
    def setUp(self):
        self.data_manager = DataManager("test_zwierzeta.json", "test_adopcje.json")
        self.test_csv = "test_zwierzeta.csv"
        self.root = Tk()
        self.app = ShelterApp(self.root)

    def tearDown(self):
        if os.path.exists(self.test_csv):
            os.remove(self.test_csv)
        if os.path.exists("test_zwierzeta.json"):
            os.remove("test_zwierzeta.json")
        if os.path.exists("test_adopcje.json"):
            os.remove("test_adopcje.json")
        self.root.destroy()

    # === Testy jednostkowe ===
    # Testuje metodę get_feeding_status klasy Animal
    def test_get_feeding_status(self):
        animal = Dog("1", "Reksio", 5)
        animal.last_fed = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.assertTrue("godziny temu" in animal.get_feeding_status())
        animal.last_fed = None
        self.assertEqual(animal.get_feeding_status(), "Brak danych")
        animal.last_fed = "invalid_date"
        self.assertEqual(animal.get_feeding_status(), "Nieprawidłowy format daty")

    # Testuje zapis i odczyt danych zwierząt w DataManager
    def test_data_manager_save_load_animals(self):
        animal = Dog("1", "Reksio", 5)
        animal.is_vaccinated = True
        self.data_manager.animals = {"1": animal}
        self.data_manager.save_animals(self.data_manager.animals, 2, 1)
        self.data_manager.animals = {}
        self.data_manager.load_animals()
        self.assertIn("1", self.data_manager.animals)
        self.assertEqual(self.data_manager.animals["1"].name, "Reksio")
        self.assertTrue(self.data_manager.animals["1"].is_vaccinated)

    # === Testy funkcjonalne ===
    # Testuje dodawanie nowego zwierzęcia
    def test_add_animal(self):
        self.app.animals = {}
        self.app.next_id = 1
        animal = Dog("1", "Reksio", 5)
        animal.is_vaccinated = True
        animal.admission_date = "2025-06-20 02:00:00"
        self.app.animals["1"] = animal
        self.app.data_manager.save_animals(self.app.animals, 2, 1)
        self.app.refresh_animals_tree()
        items = self.app.animals_tree.get_children()
        self.assertEqual(len(items), 1)
        values = self.app.animals_tree.item(items[0])["values"]
        self.assertEqual(values[1], "Reksio")
        self.assertEqual(values[2], 5)
        self.assertEqual(values[3], "Pies")

    # === Testy integracyjne ===
    # Testuje eksport i import danych zwierząt
    def test_export_import_animals(self):
        animal = Dog("1", "Reksio", 5)
        animal.is_vaccinated = True
        self.data_manager.animals = {"1": animal}
        self.data_manager.save_animals(self.data_manager.animals, 2, 1)
        self.data_manager.export_animals_csv(self.test_csv)
        self.data_manager.animals = {}
        self.data_manager.import_animals_csv(self.test_csv, replace=True)
        self.assertIn("1", self.data_manager.animals)
        self.assertEqual(self.data_manager.animals["1"].name, "Reksio")
        self.assertTrue(self.data_manager.animals["1"].is_vaccinated)

    # === Testy graniczne / błędne dane ===
    # Testuje import pliku CSV z błędnymi danymi
    def test_import_invalid_csv(self):
        with open(self.test_csv, 'w', encoding='utf-8') as f:
            f.write("ID;Imię;Wiek;Gatunek;Zaszczepione;Ostatnie karmienie;Data przyjęcia;Status\n")
            f.write("1;;-1;Nieznany;Tak;invalid_date;invalid_date;Adoptowane\n")
        errors = self.data_manager.import_animals_csv(self.test_csv, replace=True)
        self.assertGreater(len(errors), 0)
        self.assertIn("Imię nie może być puste", errors[0])
        self.assertIn("Nieprawidłowy gatunek", errors[0])
        self.assertIn("Nieprawidłowy format daty", errors[0])

    # === Testy wydajności ===
    @pytest.mark.performance
    def test_performance_save_animals(self):
        animals = {str(i): Dog(str(i), f"Animal{i}", 5) for i in range(1000)}
        execution_time = timeit.timeit(
            lambda: self.data_manager.save_animals(animals, 1001, 1),
            number=100
        )
        self.assertLess(execution_time, 1.0, f"Zapis zajął zbyt długo: {execution_time} sekund")

    @pytest.mark.performance
    def test_performance_import_csv(self):
        with open(self.test_csv, 'w', encoding='utf-8') as f:
            f.write("ID;Imię;Wiek;Gatunek;Zaszczepione;Ostatnie karmienie;Data przyjęcia;Status\n")
            for i in range(1000):
                f.write(f"{i};Animal{i};5;Pies;Tak;2025-06-20 02:00:00;2025-06-19 02:00:00;W schronisku\n")
        execution_time = timeit.timeit(
            lambda: self.data_manager.import_animals_csv(self.test_csv, replace=True),
            number=10
        )
        self.assertLess(execution_time, 1.0, f"Import CSV zajął zbyt długo: {execution_time} sekund")

    # === Testy pamięci ===
    @profile
    def test_memory_save_animals(self):
        animals = {str(i): Dog(str(i), f"Animal{i}", 5) for i in range(1000)}
        self.data_manager.save_animals(animals, 1001, 1)

if __name__ == '__main__':
    unittest.main()