"""Financial management UI window for ERP Paraguay.

This module provides the user interface for expense tracking and P&L reporting.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import logging

from app.services.financial_service import (
    list_expenses,
    get_expense_by_id,
    create_expense,
    update_expense,
    delete_expense,
    get_profit_loss_statement,
    get_expenses_by_category,
    get_financial_summary,
    EXPENSE_CATEGORIES
)

logger = logging.getLogger(__name__)


class FinancialWindow:
    """Main financial window for expense tracking and reports."""

    def __init__(self, parent):
        """Initialize the financial window.

        Args:
            parent: The parent Tkinter window
        """
        self.window = tk.Toplevel(parent)
        self.window.title("ERP Paraguay - Financeiro")
        self.window.geometry("1100x700")

        # Default date range: current month
        today = datetime.now()
        self.start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        self.end_date = today

        self.selected_expense_id = None

        self._build_ui()
        self._load_data()

    def _build_ui(self):
        """Build the user interface."""
        # Main container with notebook (tabs)
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tab 1: Despesas
        self.expenses_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.expenses_frame, text="Despesas")
        self._build_expenses_tab()

        # Tab 2: Relatório P&L
        self.pl_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.pl_frame, text="Relatório P&L")
        self._build_pl_tab()

        # Tab 3: Resumo Financeiro
        self.summary_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.summary_frame, text="Resumo")
        self._build_summary_tab()

    def _build_expenses_tab(self):
        """Build the expenses tab."""
        # Top frame with filters and buttons
        top_frame = ttk.Frame(self.expenses_frame, padding=10)
        top_frame.pack(fill=tk.X)

        # Date range
        ttk.Label(top_frame, text="Período:").pack(side=tk.LEFT, padx=(0, 5))
        self.start_date_var = tk.StringVar(value=self.start_date.strftime("%Y-%m-%d"))
        ttk.Entry(top_frame, textvariable=self.start_date_var, width=12).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(top_frame, text="até").pack(side=tk.LEFT, padx=(0, 5))
        self.end_date_var = tk.StringVar(value=self.end_date.strftime("%Y-%m-%d"))
        ttk.Entry(top_frame, textvariable=self.end_date_var, width=12).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(top_frame, text="Filtrar", command=self._apply_date_filter).pack(side=tk.LEFT, padx=(0, 20))

        # Category filter
        ttk.Label(top_frame, text="Categoria:").pack(side=tk.LEFT, padx=(0, 5))
        self.category_var = tk.StringVar(value="Todas")
        category_values = ["Todas"] + list(EXPENSE_CATEGORIES.values())
        self.category_combo = ttk.Combobox(top_frame, textvariable=self.category_var, values=category_values, state="readonly", width=15)
        self.category_combo.pack(side=tk.LEFT, padx=(0, 5))
        self.category_combo.bind("<<ComboboxSelected>>", self._on_category_change)

        # Buttons
        ttk.Button(top_frame, text="Nova Despesa", command=self._new_expense).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(top_frame, text="Editar", command=self._edit_expense).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(top_frame, text="Excluir", command=self._delete_expense).pack(side=tk.LEFT, padx=(0, 20))
        ttk.Button(top_frame, text="Atualizar", command=self._load_expenses).pack(side=tk.LEFT)

        # Expenses table
        table_frame = ttk.Frame(self.expenses_frame, padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("id", "date", "category", "description", "amount", "payment", "reference")
        self.expenses_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=20
        )

        self.expenses_tree.heading("id", text="ID")
        self.expenses_tree.heading("date", text="Data")
        self.expenses_tree.heading("category", text="Categoria")
        self.expenses_tree.heading("description", text="Descrição")
        self.expenses_tree.heading("amount", text="Valor")
        self.expenses_tree.heading("payment", text="Pagamento")
        self.expenses_tree.heading("reference", text="Referência")

        self.expenses_tree.column("id", width=50, anchor=tk.CENTER)
        self.expenses_tree.column("date", width=120)
        self.expenses_tree.column("category", width=120)
        self.expenses_tree.column("description", width=300)
        self.expenses_tree.column("amount", width=100, anchor=tk.E)
        self.expenses_tree.column("payment", width=100)
        self.expenses_tree.column("reference", width=120)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.expenses_tree.yview)
        self.expenses_tree.configure(yscrollcommand=scrollbar.set)

        self.expenses_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.expenses_tree.bind('<<TreeviewSelect>>', self._on_expense_select)

        # Total label
        self.expenses_total_var = tk.StringVar(value="Total: R$ 0.00")
        total_label = ttk.Label(table_frame, textvariable=self.expenses_total_var, font=("", 11, "bold"))
        total_label.pack(pady=5)

    def _build_pl_tab(self):
        """Build the P&L statement tab."""
        # Top frame with date range
        top_frame = ttk.Frame(self.pl_frame, padding=10)
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text="Período:").pack(side=tk.LEFT, padx=(0, 5))
        self.pl_start_var = tk.StringVar(value=self.start_date.strftime("%Y-%m-%d"))
        ttk.Entry(top_frame, textvariable=self.pl_start_var, width=12).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(top_frame, text="até").pack(side=tk.LEFT, padx=(0, 5))
        self.pl_end_var = tk.StringVar(value=self.end_date.strftime("%Y-%m-%d"))
        ttk.Entry(top_frame, textvariable=self.pl_end_var, width=12).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(top_frame, text="Gerar Relatório", command=self._generate_pl_report).pack(side=tk.LEFT, padx=(0, 20))

        ttk.Button(top_frame, text="Este Mês", command=lambda: self._set_pl_period("month")).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(top_frame, text="Este Ano", command=lambda: self._set_pl_period("year")).pack(side=tk.LEFT, padx=(0, 5))

        # P&L content frame
        self.pl_content_frame = ttk.Frame(self.pl_frame, padding=20)
        self.pl_content_frame.pack(fill=tk.BOTH, expand=True)

    def _build_summary_tab(self):
        """Build the financial summary tab."""
        # Top frame with date range
        top_frame = ttk.Frame(self.summary_frame, padding=10)
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text="Período:").pack(side=tk.LEFT, padx=(0, 5))
        self.sum_start_var = tk.StringVar(value=self.start_date.strftime("%Y-%m-%d"))
        ttk.Entry(top_frame, textvariable=self.sum_start_var, width=12).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(top_frame, text="até").pack(side=tk.LEFT, padx=(0, 5))
        self.sum_end_var = tk.StringVar(value=self.end_date.strftime("%Y-%m-%d"))
        ttk.Entry(top_frame, textvariable=self.sum_end_var, width=12).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(top_frame, text="Atualizar", command=self._load_summary).pack(side=tk.LEFT, padx=(0, 20))
        ttk.Button(top_frame, text="Este Mês", command=lambda: self._set_summary_period("month")).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(top_frame, text="Este Ano", command=lambda: self._set_summary_period("year")).pack(side=tk.LEFT, padx=(0, 5))

        # Summary content frame
        self.summary_content_frame = ttk.Frame(self.summary_frame, padding=20)
        self.summary_content_frame.pack(fill=tk.BOTH, expand=True)

    def _load_data(self):
        """Load initial data."""
        self._load_expenses()
        self._generate_pl_report()
        self._load_summary()

    def _load_expenses(self):
        """Load expenses into table."""
        # Clear existing items
        for item in self.expenses_tree.get_children():
            self.expenses_tree.delete(item)

        try:
            expenses = list_expenses(
                start_date=self.start_date,
                end_date=self.end_date,
                category=None if self.category_var.get() == "Todas" else self._get_category_key(self.category_var.get())
            )

            total = 0
            for expense in expenses:
                category_display = EXPENSE_CATEGORIES.get(expense.category, expense.category)
                self.expenses_tree.insert("", tk.END, values=(
                    expense.id,
                    expense.expense_date.strftime("%Y-%m-%d"),
                    category_display,
                    expense.description,
                    f"R$ {expense.amount:.2f}",
                    expense.payment_method or "-",
                    expense.reference or "-"
                ))
                total += float(expense.amount)

            self.expenses_total_var.set(f"Total: R$ {total:.2f}")

        except Exception as e:
            logger.exception("Error loading expenses")
            messagebox.showerror("Erro", f"Erro ao carregar despesas: {e}")

    def _on_expense_select(self, event):
        """Handle expense selection."""
        selection = self.expenses_tree.selection()
        if selection:
            item = self.expenses_tree.item(selection[0])
            values = item['values']
            self.selected_expense_id = values[0]

    def _new_expense(self):
        """Open dialog to create a new expense."""
        self._open_expense_dialog()

    def _edit_expense(self):
        """Open dialog to edit selected expense."""
        if not self.selected_expense_id:
            messagebox.showwarning("Aviso", "Selecione uma despesa para editar")
            return

        try:
            expense = get_expense_by_id(self.selected_expense_id)
            if expense:
                self._open_expense_dialog(expense)
            else:
                messagebox.showerror("Erro", "Despesa não encontrada")
        except Exception as e:
            logger.exception("Error loading expense")
            messagebox.showerror("Erro", f"Erro ao carregar despesa: {e}")

    def _delete_expense(self):
        """Delete the selected expense."""
        if not self.selected_expense_id:
            messagebox.showwarning("Aviso", "Selecione uma despesa para excluir")
            return

        if not messagebox.askyesno("Confirmar", "Deseja realmente excluir esta despesa?"):
            return

        try:
            success, error = delete_expense(self.selected_expense_id)
            if success:
                messagebox.showinfo("Sucesso", "Despesa excluída com sucesso")
                self._load_expenses()
                self.selected_expense_id = None
            else:
                messagebox.showerror("Erro", error or "Erro ao excluir despesa")
        except Exception as e:
            logger.exception("Error deleting expense")
            messagebox.showerror("Erro", f"Erro ao excluir despesa: {e}")

    def _open_expense_dialog(self, expense=None):
        """Open dialog for creating/editing an expense.

        Args:
            expense: Expense object for editing, None for new expense
        """
        dialog = tk.Toplevel(self.window)
        dialog.title("Editar Despesa" if expense else "Nova Despesa")
        dialog.geometry("500x400")
        dialog.transient(self.window)
        dialog.grab_set()

        # Form fields
        form_frame = ttk.Frame(dialog, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)

        row = 0

        # Category
        ttk.Label(form_frame, text="Categoria *").grid(row=row, column=0, sticky=tk.W, pady=5)
        category_var = tk.StringVar(value=EXPENSE_CATEGORIES.get(expense.category, expense.category) if expense else "")
        category_combo = ttk.Combobox(form_frame, textvariable=category_var, values=list(EXPENSE_CATEGORIES.values()), state="readonly", width=30)
        category_combo.grid(row=row, column=1, pady=5)
        row += 1

        # Amount
        ttk.Label(form_frame, text="Valor *").grid(row=row, column=0, sticky=tk.W, pady=5)
        amount_var = tk.StringVar(value=str(expense.amount) if expense else "")
        ttk.Entry(form_frame, textvariable=amount_var, width=30).grid(row=row, column=1, pady=5)
        row += 1

        # Description
        ttk.Label(form_frame, text="Descrição *").grid(row=row, column=0, sticky=tk.W, pady=5)
        description_var = tk.StringVar(value=expense.description if expense else "")
        desc_entry = ttk.Entry(form_frame, textvariable=description_var, width=30)
        desc_entry.grid(row=row, column=1, pady=5)
        row += 1

        # Date
        ttk.Label(form_frame, text="Data *").grid(row=row, column=0, sticky=tk.W, pady=5)
        date_var = tk.StringVar(value=expense.expense_date.strftime("%Y-%m-%d") if expense else datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(form_frame, textvariable=date_var, width=30).grid(row=row, column=1, pady=5)
        row += 1

        # Payment method
        ttk.Label(form_frame, text="Método de Pagamento").grid(row=row, column=0, sticky=tk.W, pady=5)
        payment_var = tk.StringVar(value=expense.payment_method or "" if expense else "")
        payment_combo = ttk.Combobox(form_frame, textvariable=payment_var, values=["", "Dinheiro", "Transferência", "Cartão", "Cheque", "PIX"], state="readonly", width=28)
        payment_combo.grid(row=row, column=1, pady=5)
        row += 1

        # Reference
        ttk.Label(form_frame, text="Referência").grid(row=row, column=0, sticky=tk.W, pady=5)
        ref_var = tk.StringVar(value=expense.reference or "" if expense else "")
        ttk.Entry(form_frame, textvariable=ref_var, width=30).grid(row=row, column=1, pady=5)
        row += 1

        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)

        def save():
            # Validate
            category = category_var.get()
            if not category:
                messagebox.showwarning("Aviso", "Categoria é obrigatória")
                return

            amount = amount_var.get()
            if not amount:
                messagebox.showwarning("Aviso", "Valor é obrigatório")
                return

            try:
                amount_val = float(amount)
                if amount_val <= 0:
                    messagebox.showwarning("Aviso", "Valor deve ser maior que zero")
                    return
            except ValueError:
                messagebox.showerror("Erro", "Valor inválido")
                return

            description = description_var.get().strip()
            if not description:
                messagebox.showwarning("Aviso", "Descrição é obrigatória")
                return

            date_str = date_var.get()
            try:
                expense_date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Erro", "Data inválida (use AAAA-MM-DD)")
                return

            # Map category display name back to key
            category_key = self._get_category_key(category)

            # Map payment method
            payment_map = {
                "Dinheiro": "cash",
                "Transferência": "transfer",
                "Cartão": "card",
                "Cheque": "check",
                "PIX": "pix"
            }
            payment_method = payment_map.get(payment_var.get(), None)
            if payment_var.get() == "":
                payment_method = None

            try:
                if expense:
                    # Update existing
                    success, error, _ = update_expense(
                        expense.id,
                        category=category_key,
                        amount=amount_val,
                        description=description,
                        expense_date=expense_date,
                        payment_method=payment_method,
                        reference=ref_var.get().strip() or None
                    )
                else:
                    # Create new
                    success, error, _ = create_expense(
                        category=category_key,
                        amount=amount_val,
                        description=description,
                        expense_date=expense_date,
                        payment_method=payment_method,
                        reference=ref_var.get().strip() or None
                    )

                if success:
                    messagebox.showinfo("Sucesso", "Despesa salva com sucesso")
                    dialog.destroy()
                    self._load_expenses()
                    self._generate_pl_report()
                    self._load_summary()
                else:
                    messagebox.showerror("Erro", error or "Erro ao salvar despesa")
            except Exception as e:
                logger.exception("Error saving expense")
                messagebox.showerror("Erro", f"Erro ao salvar despesa: {e}")

        ttk.Button(button_frame, text="Salvar", command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def _get_category_key(self, display_name: str) -> str:
        """Get category key from display name.

        Args:
            display_name: Display name of the category

        Returns:
            Category key
        """
        for key, value in EXPENSE_CATEGORIES.items():
            if value == display_name:
                return key
        return display_name.lower()

    def _apply_date_filter(self):
        """Apply date filter to expenses."""
        try:
            start = datetime.strptime(self.start_date_var.get(), "%Y-%m-%d")
            end = datetime.strptime(self.end_date_var.get(), "%Y-%m-%d")
            end = end.replace(hour=23, minute=59, second=59)

            self.start_date = start
            self.end_date = end

            self._load_expenses()
        except ValueError:
            messagebox.showerror("Erro", "Formato de data inválido (use AAAA-MM-DD)")

    def _on_category_change(self, event):
        """Handle category filter change."""
        self._load_expenses()

    def _generate_pl_report(self):
        """Generate P&L report."""
        try:
            start = datetime.strptime(self.pl_start_var.get(), "%Y-%m-%d")
            end = datetime.strptime(self.pl_end_var.get(), "%Y-%m-%d")
            end = end.replace(hour=23, minute=59, second=59)
        except ValueError:
            messagebox.showerror("Erro", "Formato de data inválido")
            return

        try:
            pl = get_profit_loss_statement(start, end)
            self._display_pl_report(pl)
        except Exception as e:
            logger.exception("Error generating P&L")
            messagebox.showerror("Erro", f"Erro ao gerar relatório: {e}")

    def _display_pl_report(self, pl: dict):
        """Display P&L report.

        Args:
            pl: P&L statement dictionary
        """
        # Clear previous content
        for widget in self.pl_content_frame.winfo_children():
            widget.destroy()

        # Title
        ttk.Label(self.pl_content_frame, text="Demonstração de Resultados", font=("", 14, "bold")).pack(pady=(0, 20))

        # Period
        period_text = f"Período: {pl['period_start'].strftime('%d/%m/%Y')} - {pl['period_end'].strftime('%d/%m/%Y')}"
        ttk.Label(self.pl_content_frame, text=period_text, font=("", 11)).pack(pady=(0, 20))

        # Create table for P&L
        pl_data = [
            ("Receita Bruta", f"R$ {pl['revenue']['total']:,.2f}", ""),
            ("(-) Custo dos Produtos", f"R$ {pl['cost_of_goods_sold']:,.2f}", ""),
            ("(=) Lucro Bruto", f"R$ {pl['gross_profit']:,.2f}", "bold"),
            ("", "", ""),
            ("(-) Despesas Totais", f"R$ {pl['expenses']['total']:,.2f}", ""),
        ]

        # Add expenses by category
        for category, amount in pl['expenses']['by_category'].items():
            pl_data.append((f"  • {category}", f"R$ {amount:,.2f}", ""))

        pl_data.extend([
            ("", "", ""),
            ("(=) Lucro Operacional", f"R$ {pl['operating_profit']:,.2f}", "bold"),
            ("", "", ""),
            ("(=) Lucro Líquido", f"R$ {pl['net_profit']:,.2f}", "bold"),
            ("", "", ""),
            ("Margem de Lucro", f"{pl['profit_margin']:.2f}%", "bold")
        ])

        # Create table
        for i, (label, value, style) in enumerate(pl_data):
            frame = ttk.Frame(self.pl_content_frame)
            frame.pack(fill=tk.X, pady=2)

            font_spec = ("", 10, "bold") if style == "bold" else ("", 10)
            fg_color = "green" if pl['net_profit'] >= 0 and label == "(=) Lucro Líquido" else "black"

            ttk.Label(frame, text=label, font=font_spec, width=30).pack(side=tk.LEFT)
            ttk.Label(frame, text=value, font=font_spec, foreground=fg_color).pack(side=tk.RIGHT)

    def _load_summary(self):
        """Load financial summary."""
        try:
            start = datetime.strptime(self.sum_start_var.get(), "%Y-%m-%d")
            end = datetime.strptime(self.sum_end_var.get(), "%Y-%m-%d")
            end = end.replace(hour=23, minute=59, second=59)
        except ValueError:
            messagebox.showerror("Erro", "Formato de data inválido")
            return

        try:
            summary = get_financial_summary(start, end)
            self._display_summary(summary)
        except Exception as e:
            logger.exception("Error loading summary")
            messagebox.showerror("Erro", f"Erro ao carregar resumo: {e}")

    def _display_summary(self, summary: dict):
        """Display financial summary.

        Args:
            summary: Financial summary dictionary
        """
        # Clear previous content
        for widget in self.summary_content_frame.winfo_children():
            widget.destroy()

        # Create columns
        left_col = ttk.Frame(self.summary_content_frame)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 20))

        right_col = ttk.Frame(self.summary_content_frame)
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Left column - KPIs
        ttk.Label(left_col, text="Indicadores Chave", font=("", 12, "bold")).pack(pady=(0, 15))

        kpis = [
            ("Receita Total", f"R$ {summary['revenue']['total']:,.2f}", "green"),
            ("Lucro Líquido", f"R$ {summary['net_profit']:,.2f}", "green" if summary['net_profit'] >= 0 else "red"),
            ("Margem de Lucro", f"{summary['profit_margin']:.1f}%", "blue"),
            ("Vendas", f"{summary['revenue']['sales_count']}", "black"),
            ("Despesas Totais", f"R$ {summary['expenses']['total']:,.2f}", "red")
        ]

        for label, value, color in kpis:
            frame = ttk.Frame(left_col)
            frame.pack(fill=tk.X, pady=5)

            ttk.Label(frame, text=label + ":", font=("", 10)).pack(side=tk.LEFT)
            ttk.Label(frame, text=value, font=("", 10, "bold"), foreground=color).pack(side=tk.RIGHT)

        # Right column - Cash Flow
        ttk.Label(right_col, text="Fluxo de Caixa", font=("", 12, "bold")).pack(pady=(0, 15))

        cf_data = [
            ("Entradas (Caixa)", f"R$ {summary['cash_flow']['cash_in']:,.2f}", "green"),
            ("Saídas (Pagamentos)", f"R$ {summary['cash_flow']['cash_out']:,.2f}", "red"),
            ("Saldo do Período", f"R$ {summary['cash_flow']['net_flow']:,.2f}", "green" if summary['cash_flow']['net_flow'] >= 0 else "red")
        ]

        for label, value, color in cf_data:
            frame = ttk.Frame(right_col)
            frame.pack(fill=tk.X, pady=5)

            ttk.Label(frame, text=label + ":", font=("", 10)).pack(side=tk.LEFT)
            ttk.Label(frame, text=value, font=("", 10, "bold"), foreground=color).pack(side=tk.RIGHT)

    def _set_pl_period(self, period: str):
        """Set P&L report period.

        Args:
            period: 'month' or 'year'
        """
        today = datetime.now()
        if period == "month":
            start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:  # year
            start = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

        end = today

        self.pl_start_var.set(start.strftime("%Y-%m-%d"))
        self.pl_end_var.set(end.strftime("%Y-%m-%d"))
        self._generate_pl_report()

    def _set_summary_period(self, period: str):
        """Set summary period.

        Args:
            period: 'month' or 'year'
        """
        today = datetime.now()
        if period == "month":
            start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:  # year
            start = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

        end = today

        self.sum_start_var.set(start.strftime("%Y-%m-%d"))
        self.sum_end_var.set(end.strftime("%Y-%m-%d"))
        self._load_summary()
