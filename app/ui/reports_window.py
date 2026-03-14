"""Reports UI window for ERP Paraguay.

This module provides the user interface for generating various reports.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import logging

from app.reports.pdf_reports import (
    generate_sales_report,
    generate_inventory_report,
    generate_customer_statement
)
from app.services.customer_service import list_customers

logger = logging.getLogger(__name__)


class ReportsWindow:
    """Main reports window for generating various reports."""

    def __init__(self, parent):
        """Initialize the reports window.

        Args:
            parent: The parent Tkinter window
        """
        self.window = tk.Toplevel(parent)
        self.window.title("ERP Paraguay - Relatórios")
        self.window.geometry("500x400")

        self.customers_cache = {}
        self._load_customers()
        self._build_ui()

    def _build_ui(self):
        """Build the user interface."""
        main_frame = ttk.Frame(self.window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        ttk.Label(main_frame, text="Generar Relatório", font=("", 14)).pack(pady=(0, 20))

        # Report type selection
        report_frame = ttk.LabelFrame(main_frame, text="Tipo de Relatório", padding=10)
        report_frame.pack(fill=tk.X, pady=(0, 10))

        self.report_type = tk.StringVar(value="sales")
        ttk.Radiobutton(report_frame, text="Relatório de Ventas", variable=self.report_type, value="sales", command=self._on_report_type_change).pack(anchor=tk.W, pady=5)
        ttk.Radiobutton(report_frame, text="Relatório de Inventario", variable=self.report_type, value="inventory", command=self._on_report_type_change).pack(anchor=tk.W, pady=5)
        ttk.Radiobutton(report_frame, text="Estado de Cliente", variable=self.report_type, value="customer", command=self._on_report_type_change).pack(anchor=tk.W, pady=5)

        # Date range frame (for sales and customer reports)
        self.date_frame = ttk.LabelFrame(main_frame, text="Período", padding=10)
        self.date_frame.pack(fill=tk.X, pady=(0, 10))

        # Start date
        ttk.Label(self.date_frame, text="Data Inicio:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.start_date_var = tk.StringVar(value=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"))
        ttk.Entry(self.date_frame, textvariable=self.start_date_var, width=15).grid(row=0, column=1, padx=5, sticky=tk.W)

        # End date
        ttk.Label(self.date_frame, text="Data Fin:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.end_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(self.date_frame, textvariable=self.end_date_var, width=15).grid(row=1, column=1, padx=5, sticky=tk.W)

        # Customer selection (for customer statement)
        self.customer_frame = ttk.LabelFrame(main_frame, text="Cliente", padding=10)
        ttk.Label(self.customer_frame, text="Cliente:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.customer_var = tk.StringVar()
        self.customer_combobox = ttk.Combobox(
            self.customer_frame,
            textvariable=self.customer_var,
            values=list(self.customers_cache.keys()),
            width=30,
            state='readonly'
        )
        self.customer_combobox.grid(row=0, column=1, padx=5, pady=5)

        # Generate button
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=20)
        ttk.Button(button_frame, text="Gerar PDF", command=self._generate_report, width=20).pack()
        ttk.Button(button_frame, text="Cerrar", command=self.window.destroy, width=20).pack(pady=(10, 0))

        # Initial state
        self._on_report_type_change()

    def _load_customers(self):
        """Load customers into cache."""
        try:
            customers = list_customers(active_only=True)
            self.customers_cache = {c.name: c for c in customers}
        except Exception as e:
            logger.exception("Error loading customers")

    def _on_report_type_change(self):
        """Handle report type change."""
        report_type = self.report_type.get()

        # Show/hide date frame
        if report_type in ["sales", "customer"]:
            self.date_frame.pack(fill=tk.X, pady=(0, 10))
        else:
            self.date_frame.pack_forget()

        # Show/hide customer frame
        if report_type == "customer":
            self.customer_frame.pack(fill=tk.X, pady=(0, 10))
        else:
            self.customer_frame.pack_forget()

    def _generate_report(self):
        """Generate the selected report."""
        report_type = self.report_type.get()

        try:
            # Get file path
            path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF", "*.pdf")],
                initialfile=f"{report_type}_report.pdf",
            )
            if not path:
                return

            if report_type == "sales":
                # Parse dates
                start_date = datetime.strptime(self.start_date_var.get(), "%Y-%m-%d")
                end_date = datetime.strptime(self.end_date_var.get(), "%Y-%m-%d")
                end_date = end_date.replace(hour=23, minute=59, second=59)

                generate_sales_report(path, start_date, end_date)
                messagebox.showinfo("Sucesso", f"Relatório de ventas guardado:\n{path}")

            elif report_type == "inventory":
                generate_inventory_report(path)
                messagebox.showinfo("Sucesso", f"Relatório de inventario guardado:\n{path}")

            elif report_type == "customer":
                # Get customer
                customer_name = self.customer_var.get()
                if not customer_name:
                    messagebox.showwarning("Aviso", "Seleccione un cliente")
                    return

                customer = self.customers_cache.get(customer_name)
                if not customer:
                    messagebox.showerror("Erro", "Cliente no encontrado")
                    return

                # Parse dates
                start_date = datetime.strptime(self.start_date_var.get(), "%Y-%m-%d")
                end_date = datetime.strptime(self.end_date_var.get(), "%Y-%m-%d")
                end_date = end_date.replace(hour=23, minute=59, second=59)

                generate_customer_statement(path, customer.id, start_date, end_date)
                messagebox.showinfo("Sucesso", f"Estado de cuenta guardado:\n{path}")

        except ValueError as e:
            messagebox.showerror("Erro", f"Formato de data inválido. Use AAAA-MM-DD")
        except Exception as e:
            logger.exception("Error generating report")
            messagebox.showerror("Erro", f"Error al generar relatório: {e}")
