import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from tkcalendar import DateEntry
from animal_manager import Dog, Cat, Bird, Rabbit, Hamster, Turtle
from data_manager import DataManager
from decorators import log_action
from datetime import datetime, time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# Klasa zarządzająca aplikacją schroniska
class ShelterApp:
    # Inicjalizacja aplikacji z interfejsem i danymi
    def __init__(self, root):
        self.root = root
        self.root.title("System Schroniska")
        self.root.geometry("1200x800")
        self.root.minsize(1200, 800)
        self.data_manager = DataManager("zwierzeta.json", "adopcje.json")
        self.animals = self.data_manager.animals
        self.adoptions = self.data_manager.adoptions
        self.next_id = self.data_manager.get_next_id()
        self.next_adoption_id = self.data_manager.get_next_adoption_id()
        self.animals_sort_column = None
        self.animals_sort_reverse = False
        self.animals_sort_default = True
        self.adoptions_sort_column = None
        self.adoptions_sort_reverse = False
        self.adoptions_sort_default = True
        self.filtered_animals = None
        self.filtered_adoptions = None
        self.species_map = {"Pies": Dog, "Kot": Cat, "Ptak": Bird, "Królik": Rabbit, "Chomik": Hamster, "Żółw": Turtle}
        self.species_options = list(self.species_map.keys())
        self.setup_ui()
        self.refresh_animals_tree()
        self.refresh_adoptions_tree()

    # Konfiguracja interfejsu graficznego
    def setup_ui(self):
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", padding=10, font=("Arial", 10), background="#4CAF50", foreground="white")
        style.configure("TLabel", font=("Arial", 12))
        style.configure("Treeview", font=("Arial", 10), rowheight=25)
        style.configure("Treeview.Heading", font=("Arial", 11, "bold"), background="#2196F3", foreground="white")
        notebook = ttk.Notebook(self.root)
        notebook.grid(row=0, column=0, sticky="wens")
        animals_frame = ttk.Frame(notebook, padding=10)
        notebook.add(animals_frame, text="Lista zwierząt")
        animals_frame.grid_rowconfigure(0, weight=1)
        animals_frame.grid_columnconfigure(0, weight=1)
        self.animals_tree = ttk.Treeview(animals_frame, columns=("ID", "Imię", "Wiek", "Gatunek", "Zaszczepione", "Ostatnie karmienie", "Data przyjęcia", "Status"), show="headings")
        for col in self.animals_tree["columns"]:
            self.animals_tree.heading(col, text=col, command=lambda c=col: self.sort_column(c, False))
            self.animals_tree.column(col, width=100 if col in ["ID", "Wiek", "Gatunek", "Zaszczepione", "Status"] else 150)
        self.animals_tree.grid(row=0, column=0, sticky="wens")
        animals_scrollbar = ttk.Scrollbar(animals_frame, orient=tk.VERTICAL, command=self.animals_tree.yview)
        animals_scrollbar.grid(row=0, column=1, sticky="ns")
        self.animals_tree.configure(yscrollcommand=animals_scrollbar.set)
        animals_buttons_frame = ttk.Frame(animals_frame)
        animals_buttons_frame.grid(row=1, column=0, columnspan=2, pady=10)
        animals_buttons_frame.grid_columnconfigure(10, weight=1)
        ttk.Button(animals_buttons_frame, text="Adoptuj", command=self.open_adopt_window).grid(row=0, column=0, padx=5)
        ttk.Button(animals_buttons_frame, text="Nakarm", command=self.mark_fed).grid(row=0, column=1, padx=5)
        ttk.Button(animals_buttons_frame, text="Odśwież", command=self.refresh_animals_tree).grid(row=0, column=8, padx=5, sticky="e")
        ttk.Button(animals_buttons_frame, text="Raporty", command=self.open_report_window).grid(row=0, column=7, padx=5)
        ttk.Button(animals_buttons_frame, text="Wyszukaj", command=self.open_animal_search_window).grid(row=0, column=6, padx=5)
        ttk.Button(animals_buttons_frame, text="Usuń", command=self.delete_animal).grid(row=0, column=5, padx=5)
        ttk.Button(animals_buttons_frame, text="Edytuj", command=self.open_edit_animal_window).grid(row=0, column=4, padx=5)
        ttk.Button(animals_buttons_frame, text="Dodaj", command=self.open_add_animal_window).grid(row=0, column=3, padx=5)
        ttk.Button(animals_buttons_frame, text="Importuj CSV", command=self.import_animals_csv).grid(row=0, column=9, padx=5)
        ttk.Button(animals_buttons_frame, text="Eksport CSV", command=self.export_animals_csv).grid(row=0, column=10, padx=5)
        adoptions_frame = ttk.Frame(notebook, padding=10)
        notebook.add(adoptions_frame, text="Adopcje")
        adoptions_frame.grid_rowconfigure(0, weight=1)
        adoptions_frame.grid_columnconfigure(0, weight=1)
        self.adoptions_tree = ttk.Treeview(adoptions_frame, columns=("ID", "ID zwierzęcia", "Nazwisko", "PESEL", "Numer telefonu", "Data adopcji"), show="headings")
        for col in self.adoptions_tree["columns"]:
            self.adoptions_tree.heading(col, text=col, command=lambda c=col: self.sort_column(c, True))
            self.adoptions_tree.column(col, width=100 if col == "ID" else 150)
        self.adoptions_tree.grid(row=0, column=0, sticky="wens")
        adoptions_scrollbar = ttk.Scrollbar(adoptions_frame, orient=tk.VERTICAL, command=self.adoptions_tree.yview)
        adoptions_scrollbar.grid(row=0, column=1, sticky="ns")
        self.adoptions_tree.configure(yscrollcommand=adoptions_scrollbar.set)
        adoptions_buttons_frame = ttk.Frame(adoptions_frame)
        adoptions_buttons_frame.grid(row=1, column=0, columnspan=2, pady=10)
        adoptions_buttons_frame.grid_columnconfigure(5, weight=1)
        ttk.Button(adoptions_buttons_frame, text="Edytuj", command=self.open_edit_adoption_window).grid(row=0, column=1, padx=5)
        ttk.Button(adoptions_buttons_frame, text="Usuń", command=self.delete_adoption).grid(row=0, column=2, padx=5)
        ttk.Button(adoptions_buttons_frame, text="Wyszukaj", command=self.open_adoption_search_window).grid(row=0, column=3, padx=5)
        ttk.Button(adoptions_buttons_frame, text="Importuj CSV", command=self.import_adoptions_csv).grid(row=0, column=4, padx=5)
        ttk.Button(adoptions_buttons_frame, text="Eksport CSV", command=self.export_adoptions_csv).grid(row=0, column=5, padx=5)

    # Otwiera okno do dodawania nowego zwierzęcia
    def open_add_animal_window(self):
        add_window = tk.Toplevel(self.root)
        add_window.title("Dodaj zwierzę")
        add_window.geometry("400x400")
        add_window.minsize(400, 400)
        ttk.Label(add_window, text="Imię:").grid(row=0, column=0, padx=2, pady=5, sticky="w")
        name_entry = ttk.Entry(add_window, width=20)
        name_entry.grid(row=0, column=1, padx=2, pady=5)
        ttk.Label(add_window, text="Wiek:").grid(row=1, column=0, padx=2, pady=5, sticky="w")
        age_entry = ttk.Entry(add_window, width=10)
        age_entry.grid(row=1, column=1, padx=2, pady=5)
        ttk.Label(add_window, text="Gatunek:").grid(row=2, column=0, padx=2, pady=5, sticky="w")
        species_var = tk.StringVar(value="Pies")
        ttk.OptionMenu(add_window, species_var, "Pies", *self.species_options).grid(row=2, column=1, padx=2, pady=5)
        ttk.Label(add_window, text="Zaszczepione:").grid(row=3, column=0, padx=2, pady=5, sticky="w")
        vaccinated_var = tk.BooleanVar()
        ttk.Checkbutton(add_window, variable=vaccinated_var).grid(row=3, column=1, padx=2, pady=5)
        def validate_and_add():
            try:
                name = name_entry.get().strip()
                age = int(age_entry.get().strip())
                assert name and age >= 0
                if any(animal.name.lower() == name.lower() for animal in self.animals.values()):
                    messagebox.showerror("Błąd", f"Zwierzę o imieniu {name} już istnieje")
                    return
                species = species_var.get()
                animal_id = str(self.next_id)
                self.next_id += 1
                animal_class = self.species_map[species]
                animal = animal_class(animal_id, name, age)
                animal.is_vaccinated = vaccinated_var.get()
                animal.admission_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.animals[animal_id] = animal
                self.data_manager.save_animals(self.animals, self.next_id, self.next_adoption_id)
                self.refresh_animals_tree()
                add_window.destroy()
                messagebox.showinfo("Sukces", f"Dodano {species.lower()} o imieniu {name}")
            except (ValueError, AssertionError):
                messagebox.showerror("Błąd", "Sprawdź dane: imię niepuste, wiek liczba nieujemna")
        ttk.Button(add_window, text="Zapisz", command=validate_and_add).grid(row=4, column=0, columnspan=2, pady=10)

    # Otwiera okno do edycji danych zwierzęcia
    def open_edit_animal_window(self):
        selected = self.animals_tree.selection()
        if not selected:
            messagebox.showerror("Błąd", "Wybierz zwierzę")
            return
        animal_id = str(self.animals_tree.item(selected[0])["values"][0])
        animal = self.animals.get(animal_id)
        if not animal:
            messagebox.showerror("Błąd", f"Nie znaleziono zwierzęcia o ID {animal_id}")
            return
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Edytuj zwierzę")
        edit_window.geometry("400x400")
        edit_window.minsize(400, 400)
        ttk.Label(edit_window, text="ID:").grid(row=0, column=0, padx=2, pady=5, sticky="w")
        ttk.Label(edit_window, text=animal_id).grid(row=0, column=1, padx=2, pady=5)
        ttk.Label(edit_window, text="Imię:").grid(row=1, column=0, padx=2, pady=5, sticky="w")
        name_entry = ttk.Entry(edit_window, width=20)
        name_entry.insert(0, animal.name)
        name_entry.grid(row=1, column=1, padx=2, pady=5)
        ttk.Label(edit_window, text="Wiek:").grid(row=2, column=0, padx=2, pady=5, sticky="w")
        age_entry = ttk.Entry(edit_window, width=10)
        age_entry.insert(0, str(animal.age))
        age_entry.grid(row=2, column=1, padx=2, pady=5)
        ttk.Label(edit_window, text="Gatunek:").grid(row=3, column=0, padx=2, pady=5, sticky="w")
        species_var = tk.StringVar(value=next(k for k, v in self.species_map.items() if v == animal.__class__))
        ttk.OptionMenu(edit_window, species_var, species_var.get(), *self.species_options).grid(row=3, column=1, padx=2, pady=5)
        ttk.Label(edit_window, text="Zaszczepione:").grid(row=4, column=0, padx=2, pady=5, sticky="w")
        vaccinated_var = tk.BooleanVar(value=animal.is_vaccinated)
        ttk.Checkbutton(edit_window, variable=vaccinated_var).grid(row=4, column=1, padx=2, pady=5)
        ttk.Label(edit_window, text="Adoptowane:").grid(row=5, column=0, padx=2, pady=5, sticky="w")
        adopted_var = tk.BooleanVar(value=animal.is_adopted)
        ttk.Checkbutton(edit_window, variable=adopted_var).grid(row=5, column=1, padx=2, pady=5)
        def save_changes():
            try:
                name = name_entry.get().strip()
                age = int(age_entry.get().strip())
                assert name and age >= 0
                species = species_var.get()
                is_vaccinated = vaccinated_var.get()
                is_adopted = adopted_var.get()
                animal_class = self.species_map[species]
                new_animal = animal_class(animal_id, name, age)
                new_animal.is_vaccinated = is_vaccinated
                new_animal.last_fed = animal.last_fed
                new_animal.admission_date = animal.admission_date
                new_animal.is_adopted = is_adopted
                if not is_adopted and animal.is_adopted:
                    for adoption_id, adoption in list(self.adoptions.items()):
                        if adoption["animal_id"] == animal_id:
                            del self.adoptions[adoption_id]
                            break
                self.animals[animal_id] = new_animal
                self.data_manager.save_animals(self.animals, self.next_id, self.next_adoption_id)
                self.data_manager.save_adoptions(self.adoptions)
                self.refresh_animals_tree()
                self.refresh_adoptions_tree()
                edit_window.destroy()
                messagebox.showinfo("Sukces", "Zaktualizowano dane")
            except (ValueError, AssertionError):
                messagebox.showerror("Błąd", "Sprawdź dane: imię niepuste, wiek liczba nieujemna")
        ttk.Button(edit_window, text="Zapisz", command=save_changes).grid(row=6, column=0, columnspan=2, pady=10)

    # Oznacza zwierzę jako nakarmione
    def mark_fed(self):
        selected = self.animals_tree.selection()
        if not selected:
            messagebox.showerror("Błąd", "Wybierz zwierzę")
            return
        animal_id = str(self.animals_tree.item(selected[0])["values"][0])
        animal = self.animals.get(animal_id)
        if not animal:
            messagebox.showerror("Błąd", f"Nie znaleziono zwierzęcia o ID {animal_id}")
            return
        animal.last_fed = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.data_manager.save_animals(self.animals, self.next_id, self.next_adoption_id)
        self.refresh_animals_tree()
        messagebox.showinfo("Sukces", f"Oznaczono karmienie dla {animal.name}")

    # Otwiera okno do adopcji zwierzęcia
    def open_adopt_window(self):
        selected = self.animals_tree.selection()
        if not selected:
            messagebox.showerror("Błąd", "Wybierz zwierzę")
            return
        animal_id = str(self.animals_tree.item(selected[0])["values"][0])
        animal = self.animals.get(animal_id)
        if not animal or animal.is_adopted:
            messagebox.showerror("Błąd", f"Zwierzę {animal.name if animal else 'nie istnieje'} już adoptowane lub nie istnieje")
            return
        adopt_window = tk.Toplevel(self.root)
        adopt_window.title("Adopcja zwierzęcia")
        adopt_window.geometry("400x300")
        adopt_window.minsize(400, 300)
        ttk.Label(adopt_window, text="ID zwierzęcia:").grid(row=0, column=0, padx=2, pady=5, sticky="w")
        ttk.Label(adopt_window, text=animal_id).grid(row=0, column=1, padx=2, pady=5)
        ttk.Label(adopt_window, text="Nazwisko:").grid(row=1, column=0, padx=2, pady=5, sticky="w")
        surname_entry = ttk.Entry(adopt_window, width=20)
        surname_entry.grid(row=1, column=1, padx=2, pady=5)
        ttk.Label(adopt_window, text="PESEL:").grid(row=2, column=0, padx=2, pady=5, sticky="w")
        pesel_entry = ttk.Entry(adopt_window, width=20)
        pesel_entry.grid(row=2, column=1, padx=2, pady=5)
        ttk.Label(adopt_window, text="Numer telefonu:").grid(row=3, column=0, padx=2, pady=5, sticky="w")
        phone_entry = ttk.Entry(adopt_window, width=20)
        phone_entry.grid(row=3, column=1, padx=2, pady=5)
        def validate_and_adopt():
            try:
                surname = surname_entry.get().strip()
                pesel = pesel_entry.get().strip()
                phone = phone_entry.get().strip()
                assert surname and pesel.isdigit() and len(pesel) == 11 and phone.isdigit() and len(phone) == 9
                animal.is_adopted = True
                adoption_id = str(self.next_adoption_id)
                self.next_adoption_id += 1
                self.adoptions[adoption_id] = {
                    "animal_id": animal_id,
                    "surname": surname,
                    "pesel": pesel,
                    "phone_number": phone,
                    "adoption_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                self.data_manager.save_animals(self.animals, self.next_id, self.next_adoption_id)
                self.data_manager.save_adoptions(self.adoptions)
                self.refresh_animals_tree()
                self.refresh_adoptions_tree()
                adopt_window.destroy()
                messagebox.showinfo("Sukces", f"Zwierzę {animal.name} adoptowane")
            except AssertionError:
                messagebox.showerror("Błąd", "Sprawdź dane: nazwisko niepuste, PESEL 11 cyfr, telefon 9 cyfr")
        ttk.Button(adopt_window, text="Zapisz", command=validate_and_adopt).grid(row=4, column=0, columnspan=2, pady=10)

    # Otwiera okno do edycji danych adopcji
    def open_edit_adoption_window(self):
        selected = self.adoptions_tree.selection()
        if not selected:
            messagebox.showerror("Błąd", "Wybierz adopcję")
            return
        adoption_id = str(self.adoptions_tree.item(selected[0])["values"][0])
        adoption = self.adoptions.get(adoption_id)
        if not adoption:
            messagebox.showerror("Błąd", f"Nie znaleziono adopcji o ID {adoption_id}")
            return
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Edytuj adopcję")
        edit_window.geometry("400x400")
        edit_window.minsize(400, 400)
        ttk.Label(edit_window, text="ID adopcji:").grid(row=0, column=0, padx=2, pady=5, sticky="w")
        ttk.Label(edit_window, text=adoption_id).grid(row=0, column=1, padx=2, pady=5)
        ttk.Label(edit_window, text="ID zwierzęcia:").grid(row=1, column=0, padx=2, pady=5, sticky="w")
        ttk.Label(edit_window, text=adoption["animal_id"]).grid(row=1, column=1, padx=2, pady=5)
        ttk.Label(edit_window, text="Nazwisko:").grid(row=2, column=0, padx=2, pady=5, sticky="w")
        surname_entry = ttk.Entry(edit_window, width=20)
        surname_entry.insert(0, adoption["surname"])
        surname_entry.grid(row=2, column=1, padx=2, pady=5)
        ttk.Label(edit_window, text="PESEL:").grid(row=3, column=0, padx=2, pady=5, sticky="w")
        pesel_entry = ttk.Entry(edit_window, width=20)
        pesel_entry.insert(0, adoption["pesel"])
        pesel_entry.grid(row=3, column=1, padx=2, pady=5)
        ttk.Label(edit_window, text="Numer telefonu:").grid(row=4, column=0, padx=2, pady=5, sticky="w")
        phone_entry = ttk.Entry(edit_window, width=20)
        phone_entry.insert(0, adoption["phone_number"])
        phone_entry.grid(row=4, column=1, padx=2, pady=5)
        def save_changes():
            try:
                surname = surname_entry.get().strip()
                pesel = pesel_entry.get().strip()
                phone = phone_entry.get().strip()
                assert surname and pesel.isdigit() and len(pesel) == 11 and phone.isdigit() and len(phone) == 9
                self.adoptions[adoption_id] = {
                    "animal_id": adoption["animal_id"],
                    "surname": surname,
                    "pesel": pesel,
                    "phone_number": phone,
                    "adoption_date": adoption["adoption_date"]
                }
                self.data_manager.save_adoptions(self.adoptions)
                self.refresh_adoptions_tree()
                edit_window.destroy()
                messagebox.showinfo("Sukces", "Zaktualizowano adopcję")
            except AssertionError:
                messagebox.showerror("Błąd", "Sprawdź dane: nazwisko niepuste, PESEL 11 cyfr, telefon 9 cyfr")
        ttk.Button(edit_window, text="Zapisz", command=save_changes).grid(row=5, column=0, columnspan=2, pady=10)

    # Otwiera okno wyszukiwania zwierząt
    def open_animal_search_window(self):
        search_window = tk.Toplevel(self.root)
        search_window.title("Wyszukiwanie zwierząt")
        search_window.geometry("1000x600")
        search_window.minsize(1000, 600)
        ttk.Label(search_window, text="ID:").grid(row=0, column=0, padx=2, pady=5, sticky="w")
        id_entry = ttk.Entry(search_window, width=20)
        id_entry.grid(row=0, column=1, padx=2, pady=5)
        ttk.Label(search_window, text="Imię:").grid(row=1, column=0, padx=2, pady=5, sticky="w")
        name_entry = ttk.Entry(search_window, width=20)
        name_entry.grid(row=1, column=1, padx=2, pady=5)
        ttk.Label(search_window, text="Wiek:").grid(row=2, column=0, padx=2, pady=5, sticky="w")
        age_entry = ttk.Entry(search_window, width=10)
        age_entry.grid(row=2, column=1, padx=2, pady=5)
        ttk.Label(search_window, text="Gatunek:").grid(row=3, column=0, padx=2, pady=5, sticky="w")
        species_var = tk.StringVar(value="Wszystkie")
        ttk.OptionMenu(search_window, species_var, "Wszystkie", "Wszystkie", *self.species_options).grid(row=3, column=1, padx=2, pady=5)
        ttk.Label(search_window, text="Zaszczepione:").grid(row=4, column=0, padx=2, pady=5, sticky="w")
        vaccinated_var = tk.StringVar(value="Wszystkie")
        ttk.OptionMenu(search_window, vaccinated_var, "Wszystkie", "Wszystkie", "Tak", "Nie").grid(row=4, column=1, padx=2, pady=5)
        ttk.Label(search_window, text="Status:").grid(row=5, column=0, padx=2, pady=5, sticky="w")
        status_var = tk.StringVar(value="Wszystkie")
        ttk.OptionMenu(search_window, status_var, "Wszystkie", "Wszystkie", "W schronisku", "Adoptowane").grid(row=5, column=1, padx=2, pady=5)
        ttk.Label(search_window, text="Data przyjęcia od:").grid(row=6, column=0, padx=2, pady=5, sticky="w")
        admission_from_entry = DateEntry(search_window, width=18, date_pattern='yyyy-mm-dd')
        admission_from_entry.set_date(datetime(2020, 1, 1))
        admission_from_entry.grid(row=6, column=1, padx=2, pady=5)
        ttk.Label(search_window, text="Data przyjęcia do:").grid(row=7, column=0, padx=2, pady=5, sticky="w")
        admission_to_entry = DateEntry(search_window, width=18, date_pattern='yyyy-mm-dd')
        admission_to_entry.grid(row=7, column=1, padx=2, pady=5)
        results_frame = ttk.Frame(search_window)
        results_frame.grid(row=9, column=0, columnspan=2, sticky="wens", padx=5, pady=5)
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)
        results_tree = ttk.Treeview(results_frame, columns=("ID", "Imię", "Wiek", "Gatunek", "Zaszczepione", "Ostatnie karmienie", "Data przyjęcia", "Status"), show="headings")
        for col in results_tree["columns"]:
            results_tree.heading(col, text=col)
            results_tree.column(col, width=100 if col in ["ID", "Wiek", "Gatunek", "Zaszczepione", "Status"] else 150)
        results_tree.grid(row=0, column=0, sticky="wens")
        results_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=results_tree.yview)
        results_scrollbar.grid(row=0, column=1, sticky="ns")
        results_tree.configure(yscrollcommand=results_scrollbar.set)
        def validate_date(entry):
            try:
                date = entry.get_date()
                return datetime.combine(date, time(0, 0) if entry == admission_from_entry else time(23, 59, 59))
            except ValueError:
                return None
        # Wykonuje wyszukiwanie zwierząt na podstawie filtrów
        def perform_search():
            try:
                id_query = id_entry.get().strip()
                name_query = name_entry.get().strip().lower()
                age_query = age_entry.get().strip()
                species_query = species_var.get()
                vaccinated_query = vaccinated_var.get()
                status_query = status_var.get()
                admission_from = validate_date(admission_from_entry)
                admission_to = validate_date(admission_to_entry)
                for item in results_tree.get_children():
                    results_tree.delete(item)
                filtered = list(self.animals.items())
                if id_query:
                    filtered = [(k, v) for k, v in filtered if id_query == k]
                if name_query:
                    filtered = list(filter(lambda x: name_query in x[1].name.lower(), filtered))
                if age_query:
                    try:
                        age = int(age_query)
                        filtered = [(k, v) for k, v in filtered if v.age == age]
                    except ValueError:
                        messagebox.showerror("Błąd", "Wiek musi być liczbą")
                        return
                if species_query != "Wszystkie":
                    filtered = [(k, v) for k, v in filtered if next(k for k, cls in self.species_map.items() if cls == v.__class__) == species_query]
                if vaccinated_query != "Wszystkie":
                    filtered = [(k, v) for k, v in filtered if v.is_vaccinated == (vaccinated_query == "Tak")]
                if status_query != "Wszystkie":
                    filtered = [(k, v) for k, v in filtered if v.is_adopted == (status_query == "Adoptowane")]
                if admission_from and admission_to:
                    filtered = [(k, v) for k, v in filtered if v.admission_date and admission_from <= datetime.strptime(v.admission_date, "%Y-%m-%d %H:%M:%S") <= admission_to]
                for animal_id, animal in filtered:
                    results_tree.insert("", "end", values=(
                        animal_id, animal.name, animal.age,
                        next(k for k, v in self.species_map.items() if v == animal.__class__),
                        "Tak" if animal.is_vaccinated else "Nie",
                        animal.get_feeding_status(),
                        animal.admission_date or "",
                        "Adoptowane" if animal.is_adopted else "W schronisku"
                    ))
            except Exception as e:
                messagebox.showerror("Błąd", f"Wystąpił błąd: {str(e)}")
        ttk.Button(search_window, text="Szukaj", command=perform_search).grid(row=8, column=0, columnspan=2, pady=10)

    # Otwiera okno wyszukiwania adopcji
    def open_adoption_search_window(self):
        search_window = tk.Toplevel(self.root)
        search_window.title("Wyszukiwanie adopcji")
        search_window.geometry("1000x600")
        search_window.minsize(1000, 600)
        ttk.Label(search_window, text="ID adopcji:").grid(row=0, column=0, padx=2, pady=5, sticky="w")
        id_entry = ttk.Entry(search_window, width=20)
        id_entry.grid(row=0, column=1, padx=2, pady=5)
        ttk.Label(search_window, text="ID zwierzęcia:").grid(row=1, column=0, padx=2, pady=5, sticky="w")
        animal_id_entry = ttk.Entry(search_window, width=20)
        animal_id_entry.grid(row=1, column=1, padx=2, pady=5)
        ttk.Label(search_window, text="Nazwisko:").grid(row=2, column=0, padx=2, pady=5, sticky="w")
        surname_entry = ttk.Entry(search_window, width=20)
        surname_entry.grid(row=2, column=1, padx=2, pady=5)
        ttk.Label(search_window, text="PESEL:").grid(row=3, column=0, padx=2, pady=5, sticky="w")
        pesel_entry = ttk.Entry(search_window, width=20)
        pesel_entry.grid(row=3, column=1, padx=2, pady=5)
        ttk.Label(search_window, text="Numer telefonu:").grid(row=4, column=0, padx=2, pady=5, sticky="w")
        phone_entry = ttk.Entry(search_window, width=20)
        phone_entry.grid(row=4, column=1, padx=2, pady=5)
        ttk.Label(search_window, text="Data adopcji od:").grid(row=5, column=0, padx=2, pady=5, sticky="w")
        adoption_from_entry = DateEntry(search_window, width=18, date_pattern='yyyy-mm-dd')
        adoption_from_entry.set_date(datetime(2020, 1, 1))
        adoption_from_entry.grid(row=5, column=1, padx=2, pady=5)
        ttk.Label(search_window, text="Data adopcji do:").grid(row=6, column=0, padx=2, pady=5, sticky="w")
        adoption_to_entry = DateEntry(search_window, width=18, date_pattern='yyyy-mm-dd')
        adoption_to_entry.grid(row=6, column=1, padx=2, pady=5)
        results_frame = ttk.Frame(search_window)
        results_frame.grid(row=8, column=0, columnspan=2, sticky="wens", padx=5, pady=5)
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)
        results_tree = ttk.Treeview(results_frame, columns=("ID", "ID zwierzęcia", "Nazwisko", "PESEL", "Numer telefonu", "Data adopcji"), show="headings")
        for col in results_tree["columns"]:
            results_tree.heading(col, text=col)
            results_tree.column(col, width=100 if col == "ID" else 150)
        results_tree.grid(row=0, column=0, sticky="wens")
        results_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=results_tree.yview)
        results_scrollbar.grid(row=0, column=1, sticky="ns")
        results_tree.configure(yscrollcommand=results_scrollbar.set)
        def validate_date(entry):
            try:
                date = entry.get_date()
                return datetime.combine(date, time(0, 0) if entry == adoption_from_entry else time(23, 59, 59))
            except ValueError:
                return None
        # Wykonuje wyszukiwanie adopcji na podstawie filtrów
        def perform_search():
            try:
                id_query = id_entry.get().strip()
                animal_id_query = animal_id_entry.get().strip()
                surname_query = surname_entry.get().strip().lower()
                pesel_query = pesel_entry.get().strip()
                phone_query = phone_entry.get().strip()
                adoption_from = validate_date(adoption_from_entry)
                adoption_to = validate_date(adoption_to_entry)
                for item in results_tree.get_children():
                    results_tree.delete(item)
                filtered = list(self.adoptions.items())
                if id_query:
                    filtered = [(k, v) for k, v in filtered if id_query == k]
                if animal_id_query:
                    filtered = [(k, v) for k, v in filtered if animal_id_query == v["animal_id"]]
                if surname_query:
                    filtered = [(k, v) for k, v in filtered if surname_query in v["surname"].lower()]
                if pesel_query:
                    filtered = [(k, v) for k, v in filtered if pesel_query in v["pesel"]]
                if phone_query:
                    filtered = [(k, v) for k, v in filtered if phone_query in v["phone_number"]]
                if adoption_from and adoption_to:
                    filtered = [(k, v) for k, v in filtered if adoption_from <= datetime.strptime(v["adoption_date"], "%Y-%m-%d %H:%M:%S") <= adoption_to]
                for adoption_id, adoption in filtered:
                    results_tree.insert("", "end", values=(
                        adoption_id, adoption["animal_id"], adoption["surname"],
                        adoption["pesel"], adoption["phone_number"], adoption["adoption_date"]
                    ))
            except Exception as e:
                messagebox.showerror("Błąd", f"Wystąpił błąd: {str(e)}")
        ttk.Button(search_window, text="Szukaj", command=perform_search).grid(row=7, column=0, columnspan=2, pady=10)

    # Zlicza zwierzęta danego typu rekurencyjnie
    def count_animals_by_type(self, animals, animal_class, index=0):
        if index >= len(animals):
            return 0
        count = 1 if isinstance(animals[index][1], animal_class) and not animals[index][1].is_adopted else 0
        return count + self.count_animals_by_type(animals, animal_class, index + 1)

    # Otwiera okno z raportami i wykresami
    def open_report_window(self):
        report_window = tk.Toplevel(self.root)
        report_window.title("Raporty")
        report_window.geometry("800x600")
        report_window.minsize(800, 600)
        fig, ax = plt.subplots(figsize=(6, 4))
        canvas = FigureCanvasTkAgg(fig, master=report_window)
        canvas.get_tk_widget().grid(row=0, column=0, columnspan=5, padx=10, pady=10, sticky="wens")
        ttk.Label(report_window, text="Typ wykresu:").grid(row=1, column=0, padx=2, pady=5, sticky="w")
        chart_type_var = tk.StringVar(value="Słupkowy")
        ttk.OptionMenu(report_window, chart_type_var, "Słupkowy", "Słupkowy", "Kołowy").grid(row=1, column=1, padx=2, pady=5)
        ttk.Label(report_window, text="Dane:").grid(row=1, column=2, padx=2, pady=5, sticky="w")
        chart_data_var = tk.StringVar(value="Szczepienia")
        ttk.OptionMenu(report_window, chart_data_var, "Szczepienia", "Szczepienia", "Gatunki").grid(row=1, column=3, padx=2, pady=5)
        # Generuje wykres na podstawie wybranych danych
        def generate_report():
            animals_list = list(self.animals.items())
            vaccinated = len(list(filter(lambda x: x[1].is_vaccinated and not x[1].is_adopted, animals_list)))
            not_vaccinated = len(list(filter(lambda x: not x[1].is_vaccinated and not x[1].is_adopted, animals_list)))
            dogs = self.count_animals_by_type(animals_list, Dog)
            cats = self.count_animals_by_type(animals_list, Cat)
            birds = self.count_animals_by_type(animals_list, Bird)
            rabbits = self.count_animals_by_type(animals_list, Rabbit)
            hamsters = self.count_animals_by_type(animals_list, Hamster)
            turtles = self.count_animals_by_type(animals_list, Turtle)
            ax.clear()
            if chart_data_var.get() == "Szczepienia":
                labels, data = ["Zaszczepione", "Niezaszczepione"], [vaccinated, not_vaccinated]
            else:
                labels = ["Psy", "Koty", "Ptaki", "Króliki", "Chomiki", "Żółwie"]
                data = [dogs, cats, birds, rabbits, hamsters, turtles]
            if chart_type_var.get() == "Słupkowy":
                bars = ax.bar(labels, data, color=['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#cc99ff', '#99cccc'])
                for bar in bars:
                    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1, str(bar.get_height()), ha='center', fontsize=10)
                ax.set_ylabel("Liczba zwierząt")
            else:
                ax.pie(data, labels=labels, colors=['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#cc99ff', '#99cccc'], autopct='%1.0f%%', textprops={'fontsize': 10})
                ax.set_ylabel("Procent zwierząt")
            ax.set_title(f"Statystyki - {chart_data_var.get()}")
            fig.tight_layout()
            canvas.draw()
        # Zapisuje wykres do pliku
        def save_chart():
            file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
            if file_path:
                fig.savefig(file_path)
                messagebox.showinfo("Sukces", f"Zapisano wykres do {file_path}")
        ttk.Button(report_window, text="Generuj", command=generate_report).grid(row=1, column=4, padx=5, pady=5)
        ttk.Button(report_window, text="Zapisz wykres", command=save_chart).grid(row=1, column=5, padx=5, pady=5)

    # Sortuje kolumny w tabeli zwierząt lub adopcji
    def sort_column(self, col, is_adoption):
        tree = self.adoptions_tree if is_adoption else self.animals_tree
        current_column = self.adoptions_sort_column if is_adoption else self.animals_sort_column
        current_reverse = self.adoptions_sort_reverse if is_adoption else self.animals_sort_reverse
        current_default = self.adoptions_sort_default if is_adoption else self.animals_sort_default
        if current_column == col:
            if current_default:
                current_reverse = False
                current_default = False
            elif not current_reverse:
                current_reverse = True
                current_default = False
            else:
                current_reverse = False
                current_default = True
        else:
            current_column = col
            current_reverse = False
            current_default = False
        default_headers = {c: c for c in tree["columns"]}
        for header_col, header_text in default_headers.items():
            tree.heading(header_col, text=header_text + (" ↓" if header_col == col and not current_default and current_reverse else " ↑" if header_col == col and not current_default else ""))
        if is_adoption:
            self.adoptions_sort_column, self.adoptions_sort_reverse, self.adoptions_sort_default = current_column, current_reverse, current_default
            items = self.adoptions
            get_key = lambda x: int(x[0]) if col == "ID" else x[1]["animal_id"] if col == "ID zwierzęcia" else x[1][{"Nazwisko": "surname", "PESEL": "pesel", "Numer telefonu": "phone_number", "Data adopcji": "adoption_date"}.get(col, "surname")]
        else:
            self.animals_sort_column, self.animals_sort_reverse, self.animals_sort_default = current_column, current_reverse, current_default
            items = self.animals
            get_key = lambda x: int(x[0]) if col == "ID" else x[1].name if col == "Imię" else x[1].age if col == "Wiek" else next(k for k, v in self.species_map.items() if v == x[1].__class__) if col == "Gatunek" else ("Tak" if x[1].is_vaccinated else "Nie") if col == "Zaszczepione" else x[1].last_fed or "" if col == "Ostatnie karmienie" else x[1].admission_date or "" if col == "Data przyjęcia" else "Adoptowane" if x[1].is_adopted else "W schronisku"
        sorted_items = sorted(items.items(), key=lambda x: int(x[0]) if current_default else get_key(x), reverse=current_reverse if not current_default else False)
        for item in tree.get_children():
            tree.delete(item)
        for item_id, data in sorted_items:
            values = (item_id, data["animal_id"], data["surname"], data["pesel"], data["phone_number"], data["adoption_date"]) if is_adoption else (item_id, data.name, data.age, next(k for k, v in self.species_map.items() if v == data.__class__), "Tak" if data.is_vaccinated else "Nie", data.get_feeding_status(), data.admission_date or "", "Adoptowane" if data.is_adopted else "W schronisku")
            tree.insert("", tk.END, values=values)

    # Odświeża tabelę zwierząt
    def refresh_animals_tree(self):
        items = self.filtered_animals or self.animals
        def get_key(x):
            if self.animals_sort_default:
                return int(x[0])
            if self.animals_sort_column == "ID":
                return int(x[0])
            elif self.animals_sort_column == "Imię":
                return x[1].name
            elif self.animals_sort_column == "Wiek":
                return x[1].age
            elif self.animals_sort_column == "Gatunek":
                return next(k for k, v in self.species_map.items() if v == x[1].__class__)
            elif self.animals_sort_column == "Zaszczepione":
                return "Tak" if x[1].is_vaccinated else "Nie"
            elif self.animals_sort_column == "Ostatnie karmienie":
                return x[1].last_fed or ""
            elif self.animals_sort_column == "Data przyjęcia":
                return x[1].admission_date or ""
            else:
                return "Adoptowane" if x[1].is_adopted else "W schronisku"
        sorted_items = sorted(items.items(), key=get_key, reverse=self.animals_sort_reverse if not self.animals_sort_default else False)
        for item in self.animals_tree.get_children():
            self.animals_tree.delete(item)
        for animal_id, animal in sorted_items:
            self.animals_tree.insert("", "end", values=(
                animal_id, animal.name, animal.age,
                next(k for k, v in self.species_map.items() if v == animal.__class__),
                "Tak" if animal.is_vaccinated else "Nie",
                animal.get_feeding_status(),
                animal.admission_date or "",
                "Adoptowane" if animal.is_adopted else "W schronisku"
            ))

    # Odświeża tabelę adopcji
    def refresh_adoptions_tree(self):
        items = self.filtered_adoptions or self.adoptions
        get_key = lambda x: int(x[0]) if self.adoptions_sort_default else (int(x[0]) if self.adoptions_sort_column == "ID" else x[1]["animal_id"] if self.adoptions_sort_column == "ID zwierzęcia" else x[1][{"Nazwisko": "surname", "PESEL": "pesel", "Numer telefonu": "phone_number", "Data adopcji": "adoption_date"}.get(self.adoptions_sort_column, "surname")])
        sorted_items = sorted(items.items(), key=get_key, reverse=self.adoptions_sort_reverse if not self.adoptions_sort_default else False)
        for item in self.adoptions_tree.get_children():
            self.adoptions_tree.delete(item)
        for adoption_id, adoption in sorted_items:
            self.adoptions_tree.insert("", "end", values=(
                adoption_id, adoption["animal_id"], adoption["surname"],
                adoption["pesel"], adoption["phone_number"], adoption["adoption_date"]
            ))

    # Usuwa wybrane zwierzę
    @log_action
    def delete_animal(self):
        selected = self.animals_tree.selection()
        if not selected:
            messagebox.showerror("Błąd", "Wybierz zwierzę")
            return
        animal_id = str(self.animals_tree.item(selected[0])["values"][0])
        animal = self.animals.get(animal_id)
        if animal:
            if any(adoption["animal_id"] == animal_id for adoption in self.adoptions.values()):
                messagebox.showerror("Błąd", f"Zwierzę {animal.name} jest adoptowane")
                return
            print(f"Usunięto zwierzę: {animal.name} (ID: {animal_id})")
            del self.animals[animal_id]
            self.filtered_animals = None
            self.data_manager.save_animals(self.animals, self.next_id, self.next_adoption_id)
            self.refresh_animals_tree()
            messagebox.showinfo("Sukces", f"Usunięto zwierzę {animal.name}")

    # Usuwa wybraną adopcję
    @log_action
    def delete_adoption(self):
        selected = self.adoptions_tree.selection()
        if not selected:
            messagebox.showerror("Błąd", "Wybierz adopcję")
            return
        adoption_id = str(self.adoptions_tree.item(selected[0])["values"][0])
        adoption = self.adoptions.get(adoption_id)
        if adoption:
            animal = self.animals.get(adoption["animal_id"])
            if animal:
                animal.is_adopted = False
                self.filtered_animals = None
                self.data_manager.save_animals(self.animals, self.next_id, self.next_adoption_id)
            del self.adoptions[adoption_id]
            self.filtered_adoptions = None
            self.data_manager.save_adoptions(self.adoptions)
            self.refresh_animals_tree()
            self.refresh_adoptions_tree()
            messagebox.showinfo("Sukces", f"Usunięto adopcję o ID {adoption_id}")

    # Importuje dane zwierząt z pliku CSV
    @log_action
    def import_animals_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return
        choice_window = tk.Toplevel(self.root)
        choice_window.title("Opcje importu")
        choice_window.geometry("400x200")
        choice_window.minsize(400, 200)
        ttk.Label(choice_window, text="Wybierz tryb importu:").grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")
        replace_var = tk.BooleanVar(value=True)
        ttk.Radiobutton(choice_window, text="Zastąp dane", variable=replace_var, value=True).grid(row=1, column=0, columnspan=2, padx=10, pady=5)
        ttk.Radiobutton(choice_window, text="Dopisz dane", variable=replace_var, value=False).grid(row=2, column=0, columnspan=2, padx=10, pady=5)
        def confirm_import():
            errors = self.data_manager.import_animals_csv(file_path, replace_var.get())
            choice_window.destroy()
            if errors:
                messagebox.showerror("Błąd importu", "\n".join(errors))
            self.animals = self.data_manager.animals
            self.next_id = self.data_manager.get_next_id()
            self.filtered_animals = None
            self.refresh_animals_tree()
            messagebox.showinfo("Sukces", f"Zaimportowano zwierzęta z {file_path}")
        ttk.Button(choice_window, text="Potwierdź", command=confirm_import).grid(row=3, column=0, columnspan=2, pady=10)

    # Importuje dane adopcji z pliku CSV
    @log_action
    def import_adoptions_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return
        choice_window = tk.Toplevel(self.root)
        choice_window.title("Opcje importu")
        choice_window.geometry("400x200")
        choice_window.minsize(400, 200)
        ttk.Label(choice_window, text="Wybierz tryb importu:").grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")
        replace_var = tk.BooleanVar(value=True)
        ttk.Radiobutton(choice_window, text="Zastąp dane", variable=replace_var, value=True).grid(row=1, column=0, columnspan=2, padx=10, pady=5)
        ttk.Radiobutton(choice_window, text="Dopisz dane", variable=replace_var, value=False).grid(row=2, column=0, columnspan=2, padx=10, pady=5)
        def confirm_import():
            errors = self.data_manager.import_adoptions_csv(file_path, replace_var.get())
            choice_window.destroy()
            if errors:
                messagebox.showerror("Błąd importu", "\n".join(errors))
            self.adoptions = self.data_manager.adoptions
            self.animals = self.data_manager.animals
            self.next_id = self.data_manager.get_next_id()
            self.next_adoption_id = self.data_manager.get_next_adoption_id()
            self.filtered_adoptions = None
            self.refresh_adoptions_tree()
            self.refresh_animals_tree()
            messagebox.showinfo("Sukces", f"Zaimportowano adopcje z {file_path}")
        ttk.Button(choice_window, text="Potwierdź", command=confirm_import).grid(row=3, column=0, columnspan=2, pady=10)

    # Eksportuje dane zwierząt do pliku CSV
    @log_action
    def export_animals_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file_path:
            self.data_manager.export_animals_csv(file_path)
            messagebox.showinfo("Sukces", f"Zwierzęta wyeksportowano do {file_path}")

    # Eksportuje dane adopcji do pliku CSV
    @log_action
    def export_adoptions_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file_path:
            self.data_manager.export_adoptions_csv(file_path)
            messagebox.showinfo("Sukces", f"Adopcje wyeksportowano do {file_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ShelterApp(root)
    root.mainloop()