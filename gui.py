from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from .cli import format_report
from .diagnosis import DiagnosisEngine
from .knowledge_base import MedicalKnowledgeBase, RISK_FACTOR_CATALOG, SYMPTOM_CATALOG
from .models import PatientProfile


def parse_csv_terms(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


class DiagnosisApp:
    def __init__(self, root: tk.Tk, knowledge_base: MedicalKnowledgeBase | None = None) -> None:
        self.root = root
        self.knowledge_base = knowledge_base or MedicalKnowledgeBase()
        self.engine = DiagnosisEngine(self.knowledge_base)

        self.symptom_items = sorted(SYMPTOM_CATALOG)
        self.risk_items = sorted(RISK_FACTOR_CATALOG)

        self.age_var = tk.StringVar()
        self.duration_var = tk.StringVar()
        self.extra_symptoms_var = tk.StringVar()
        self.extra_risks_var = tk.StringVar()
        self.top_var = tk.StringVar(value="3")
        self.status_var = tk.StringVar(
            value="Select symptoms and run a preliminary diagnosis."
        )

        self._configure_root()
        self._build_layout()
        self._render_intro()

    def _configure_root(self) -> None:
        self.root.title("Medical Diagnosis Semantic Network")
        self.root.geometry("1180x760")
        self.root.minsize(1000, 680)
        self.root.configure(bg="#f4efe6")

        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")

        style.configure("App.TFrame", background="#f4efe6")
        style.configure("Card.TFrame", background="#fffaf2")
        style.configure(
            "Title.TLabel",
            background="#f4efe6",
            foreground="#20343d",
            font=("Georgia", 22, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            background="#f4efe6",
            foreground="#4c5d66",
            font=("Segoe UI", 10),
        )
        style.configure(
            "Section.TLabel",
            background="#fffaf2",
            foreground="#20343d",
            font=("Segoe UI Semibold", 11),
        )
        style.configure(
            "Body.TLabel",
            background="#fffaf2",
            foreground="#34444c",
            font=("Segoe UI", 10),
        )
        style.configure("Accent.TButton", font=("Segoe UI Semibold", 10))

    def _build_layout(self) -> None:
        container = ttk.Frame(self.root, style="App.TFrame", padding=18)
        container.grid(sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(1, weight=1)
        container.rowconfigure(2, weight=0)

        header = ttk.Frame(container, style="App.TFrame")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        header.columnconfigure(0, weight=1)

        ttk.Label(
            header,
            text="Medical Diagnosis Using Semantic Networks",
            style="Title.TLabel",
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text=(
                "Frame-based patient input, interpretable graph reasoning, and ranked "
                "preliminary diagnoses."
            ),
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        left_card = ttk.Frame(container, style="Card.TFrame", padding=14)
        left_card.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        left_card.columnconfigure(0, weight=1)
        left_card.columnconfigure(1, weight=1)
        left_card.rowconfigure(1, weight=1)
        left_card.rowconfigure(4, weight=1)

        ttk.Label(left_card, text="Patient Input", style="Section.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(
            left_card,
            text="Choose known terms from the knowledge base or add custom terms below.",
            style="Body.TLabel",
        ).grid(row=0, column=1, sticky="e")

        ttk.Label(left_card, text="Symptoms", style="Section.TLabel").grid(
            row=1, column=0, sticky="w", pady=(10, 6)
        )
        ttk.Label(left_card, text="Risk Factors", style="Section.TLabel").grid(
            row=1, column=1, sticky="w", pady=(10, 6)
        )

        self.symptom_listbox = self._build_listbox(left_card, self.symptom_items, row=2, column=0)
        self.risk_listbox = self._build_listbox(left_card, self.risk_items, row=2, column=1)

        ttk.Label(
            left_card,
            text="Additional symptoms (comma-separated)",
            style="Body.TLabel",
        ).grid(row=3, column=0, sticky="w", pady=(12, 4))
        ttk.Label(
            left_card,
            text="Additional risk factors (comma-separated)",
            style="Body.TLabel",
        ).grid(row=3, column=1, sticky="w", pady=(12, 4))

        ttk.Entry(left_card, textvariable=self.extra_symptoms_var).grid(
            row=4, column=0, sticky="ew", padx=(0, 8)
        )
        ttk.Entry(left_card, textvariable=self.extra_risks_var).grid(
            row=4, column=1, sticky="ew"
        )

        meta_frame = ttk.Frame(left_card, style="Card.TFrame")
        meta_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        for column in range(6):
            meta_frame.columnconfigure(column, weight=1)

        ttk.Label(meta_frame, text="Age", style="Body.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Entry(meta_frame, textvariable=self.age_var, width=10).grid(
            row=1, column=0, sticky="ew", padx=(0, 8)
        )

        ttk.Label(meta_frame, text="Duration (days)", style="Body.TLabel").grid(
            row=0, column=1, sticky="w"
        )
        ttk.Entry(meta_frame, textvariable=self.duration_var, width=10).grid(
            row=1, column=1, sticky="ew", padx=(0, 8)
        )

        ttk.Label(meta_frame, text="Top results", style="Body.TLabel").grid(
            row=0, column=2, sticky="w"
        )
        ttk.Spinbox(meta_frame, from_=1, to=5, textvariable=self.top_var, width=6).grid(
            row=1, column=2, sticky="w"
        )

        ttk.Button(meta_frame, text="Load Demo", command=self.load_demo, style="Accent.TButton").grid(
            row=1, column=3, sticky="ew", padx=(16, 8)
        )
        ttk.Button(meta_frame, text="Run Diagnosis", command=self.run_diagnosis, style="Accent.TButton").grid(
            row=1, column=4, sticky="ew", padx=(0, 8)
        )
        ttk.Button(meta_frame, text="Clear", command=self.clear_form).grid(
            row=1, column=5, sticky="ew"
        )

        right_card = ttk.Frame(container, style="Card.TFrame", padding=14)
        right_card.grid(row=1, column=1, sticky="nsew")
        right_card.columnconfigure(0, weight=1)
        right_card.rowconfigure(1, weight=1)

        ttk.Label(right_card, text="Diagnosis Output", style="Section.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        self.output = ScrolledText(
            right_card,
            wrap="word",
            font=("Consolas", 10),
            background="#1f2d33",
            foreground="#f6f7f3",
            insertbackground="#f6f7f3",
            padx=12,
            pady=12,
        )
        self.output.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        self.output.configure(state="disabled")

        footer = ttk.Frame(container, style="App.TFrame")
        footer.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        footer.columnconfigure(0, weight=1)
        ttk.Label(
            footer,
            textvariable=self.status_var,
            style="Subtitle.TLabel",
        ).grid(row=0, column=0, sticky="w")

    def _build_listbox(
        self,
        parent: ttk.Frame,
        items: list[str],
        row: int,
        column: int,
    ) -> tk.Listbox:
        frame = ttk.Frame(parent, style="Card.TFrame")
        frame.grid(row=row, column=column, sticky="nsew", padx=(0, 8) if column == 0 else (0, 0))
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        listbox = tk.Listbox(
            frame,
            selectmode=tk.MULTIPLE,
            exportselection=False,
            height=14,
            activestyle="none",
            bg="#fbf7ee",
            fg="#20343d",
            selectbackground="#d96f32",
            selectforeground="#fffdf8",
            highlightthickness=1,
            highlightbackground="#d3cabd",
            relief="flat",
            font=("Segoe UI", 10),
        )
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        listbox.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        for item in items:
            listbox.insert(tk.END, item)

        return listbox

    def _render_intro(self) -> None:
        intro = (
            "Interface ready.\n\n"
            "1. Select symptoms and risk factors from the left panel.\n"
            "2. Add any extra free-text terms if needed.\n"
            "3. Click 'Run Diagnosis' to see ranked results, supporting tests, and warnings.\n\n"
            "This is an educational support interface and not a medical device."
        )
        self._set_output(intro)

    def _set_output(self, content: str) -> None:
        self.output.configure(state="normal")
        self.output.delete("1.0", tk.END)
        self.output.insert("1.0", content)
        self.output.configure(state="disabled")

    def _selected_items(self, listbox: tk.Listbox) -> list[str]:
        return [listbox.get(index) for index in listbox.curselection()]

    def _parse_optional_int(self, value: str, field_name: str) -> int | None:
        value = value.strip()
        if not value:
            return None
        try:
            return int(value)
        except ValueError as exc:
            raise ValueError(f"{field_name} must be a whole number.") from exc

    def _set_selection(self, listbox: tk.Listbox, values: list[str]) -> None:
        value_set = set(values)
        listbox.selection_clear(0, tk.END)
        for index, item in enumerate(listbox.get(0, tk.END)):
            if item in value_set:
                listbox.selection_set(index)

    def load_demo(self) -> None:
        self._set_selection(
            self.symptom_listbox,
            ["fever", "cough", "fatigue", "loss of taste or smell"],
        )
        self._set_selection(self.risk_listbox, ["recent viral exposure"])
        self.extra_symptoms_var.set("")
        self.extra_risks_var.set("")
        self.age_var.set("42")
        self.duration_var.set("3")
        self.top_var.set("3")
        self.status_var.set("Demo patient loaded. Run diagnosis to view the example output.")

    def clear_form(self) -> None:
        self.symptom_listbox.selection_clear(0, tk.END)
        self.risk_listbox.selection_clear(0, tk.END)
        self.extra_symptoms_var.set("")
        self.extra_risks_var.set("")
        self.age_var.set("")
        self.duration_var.set("")
        self.top_var.set("3")
        self.status_var.set("Input cleared.")
        self._render_intro()

    def run_diagnosis(self) -> None:
        symptoms = self._selected_items(self.symptom_listbox)
        symptoms.extend(parse_csv_terms(self.extra_symptoms_var.get()))

        risk_factors = self._selected_items(self.risk_listbox)
        risk_factors.extend(parse_csv_terms(self.extra_risks_var.get()))

        deduped_symptoms = list(dict.fromkeys(symptoms))
        deduped_risks = list(dict.fromkeys(risk_factors))

        if not deduped_symptoms:
            messagebox.showerror("Missing symptoms", "Please select or enter at least one symptom.")
            return

        try:
            patient = PatientProfile(
                symptoms=deduped_symptoms,
                risk_factors=deduped_risks,
                age=self._parse_optional_int(self.age_var.get(), "Age"),
                duration_days=self._parse_optional_int(
                    self.duration_var.get(), "Duration"
                ),
            )
            top_n = self._parse_optional_int(self.top_var.get(), "Top results") or 3
        except ValueError as error:
            messagebox.showerror("Invalid input", str(error))
            return

        report = self.engine.diagnose(patient, top_n=max(1, min(top_n, 5)))
        self._set_output(format_report(report))

        unknown_count = len(report.unknown_terms)
        red_flag_count = len(report.detected_red_flags)
        self.status_var.set(
            "Diagnosis completed. "
            f"{len(report.top_diagnoses)} ranked results, "
            f"{red_flag_count} red flags, {unknown_count} unknown terms."
        )


def launch_gui(knowledge_base: MedicalKnowledgeBase | None = None) -> None:
    root = tk.Tk()
    DiagnosisApp(root, knowledge_base=knowledge_base)
    root.mainloop()
