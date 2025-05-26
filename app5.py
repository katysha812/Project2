import sys
import os
import bcrypt
from sqlalchemy import create_engine, Column, Integer, String, Date, Float, ForeignKey, func
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QGroupBox, QFormLayout,
                            QComboBox, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                            QHBoxLayout, QLabel, QDateEdit, QMessageBox, QDialog,
                            QDialogButtonBox, QSpinBox, QDoubleSpinBox, QFileDialog)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import QHeaderView
from PyQt6.QtGui import QIntValidator
from PyQt6.QtGui import QPalette, QColor
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

Base = declarative_base()


# Модели данных (соответствуют вашей структуре БД)
class Пользователи(Base):
    __tablename__ = 'пользователи'
    __table_args__ = {'schema': 'Проект2'}

    id = Column(Integer, primary_key=True)
    фио = Column(String(500), nullable=False)
    логин = Column(String(100), nullable=False, unique=True)
    пароль = Column(String(100), nullable=False, unique=True)
    пин_код = Column(Integer, nullable=False, unique=True)

    платежи = relationship("Платежи", back_populates="пользователи")


class Категории(Base):
    __tablename__ = 'категории'
    __table_args__ = {'schema': 'Проект2'}

    id = Column(Integer, primary_key=True)
    название = Column(String(255), nullable=False)

    платежи = relationship("Платежи", back_populates="категории")

class Платежи(Base):
    __tablename__ = 'платежи'
    __table_args__ = {'schema': 'Проект2'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_пользователя = Column(Integer, ForeignKey('Проект2.пользователи.id'))
    дата = Column(Date, nullable=False)
    id_категории = Column(Integer, ForeignKey('Проект2.категории.id'))
    наименование_платежа = Column(String(255), nullable=False)
    количество = Column(Integer, nullable=False)
    цена = Column(Float, nullable=False)
    стоимость = Column(Float, nullable=False)

    категории = relationship("Категории", back_populates="платежи")
    пользователи = relationship("Пользователи", back_populates="платежи")


class PaymentApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Учет платежей")
        self.setGeometry(100, 100, 1000, 600)

        self.setStyleSheet("""
            QWidget {
                background-color: #282c34; /* Очень темно-серый фон (vscode) */
                color: #abb2bf; /* Светло-серый текст (vscode) */
                font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
                font-size: 14px;
            }
            QGroupBox {
                border: 1px solid #44475a; /* Темная граница */
                border-radius: 5px;
                margin-top: 1ex;
                background-color: #3e4451; /* Чуть светлее фон */
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
                color: #abb2bf;
            }
            QPushButton {
                background-color: #e91e63; /* Розовый цвет */
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #ff4081; /* Чуть светлее при наведении */
            }
            QPushButton:pressed {
                background-color: #c2185b; /* Темнее при нажатии */
            }
            QTableWidget {
                border: 1px solid #44475a; /* Темная граница */
                gridline-color: #44475a;
                background-color: #282c34; /* Очень темно-серый фон (vscode) */
            }
            QHeaderView::section {
                background-color: #44475a; /* Темная граница */
                color: #abb2bf; /* Светло-серый текст (vscode) */
                padding: 8px;
                border: none;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #3e4451; /* Чуть светлее фон */
                color: white;
            }
            QLineEdit, QComboBox, QDateEdit {
                background-color: #3e4451; /* Чуть светлее фон */
                color: #abb2bf; /* Светло-серый текст (vscode) */
                border: 1px solid #44475a; /* Темная граница */
                padding: 6px;
                border-radius: 4px;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus {
                border: 1px solid #528bff; /* Синий при фокусе */
            }
            QLabel {
                color: #abb2bf; /* Светло-серый текст (vscode) */
            }
            QMessageBox {
                background-color: #3e4451; /* Чуть светлее фон */
                 */
            }
        """)

        # Подключение к вашей базе данных
        self.engine = create_engine(
            'postgresql+psycopg2://postgres:1234@localhost:5432/postgres?options=-csearch_path=Проект2')
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()
        self.current_user_id = None
        self.initUI()
        # Вызов окна входа при создании экземпляра класса
        self.show_login_dialog()

    def initUI(self):
        self.layout = QVBoxLayout(self)

        # Основная панель (изначально скрыта)
        self.mainBox = QWidget()
        self.mainBox.hide()
        mainLayout = QVBoxLayout(self.mainBox)

        # Панель управления
        controlPanel = QWidget()
        controlLayout = QHBoxLayout(controlPanel)

        # Кнопка "Выбор пользователя"
        self.userSelectionButton = QPushButton("Выбор пользователя")
        self.userSelectionButton.clicked.connect(self.show_login_dialog)  # Исправленная строка

        controlLayout.addWidget(self.userSelectionButton)

        # Кнопки управления
        self.addButton = QPushButton("+")
        self.addButton.clicked.connect(self.show_add_payment_dialog)

        self.delButton = QPushButton("-")
        self.delButton.clicked.connect(self.delete_payment)

        # Фильтры по дате
        self.dateFrom = QDateEdit(calendarPopup=True)
        self.dateFrom.setDate(QDate.currentDate().addMonths(-1))
        self.dateFrom.setFixedWidth(120)

        self.dateTo = QDateEdit(calendarPopup=True)
        self.dateTo.setDate(QDate.currentDate())
        self.dateTo.setFixedWidth(120)

        # Фильтр по категориям
        self.categoryFilter = QComboBox()
        self.load_categories()
        self.categoryFilter.setFixedWidth(150)

        # Кнопки действий
        self.selectButton = QPushButton("Применить фильтры")
        self.selectButton.clicked.connect(self.load_data)

        self.clearButton = QPushButton("Сбросить")
        self.clearButton.clicked.connect(self.clear_filters)

        self.reportButton = QPushButton("Создать отчет")
        self.reportButton.clicked.connect(self.generate_report)

        # Расположение элементов управления
        controlLayout.addWidget(self.addButton)
        controlLayout.addWidget(self.delButton)
        controlLayout.addWidget(QLabel("Период с:"))
        controlLayout.addWidget(self.dateFrom)
        controlLayout.addWidget(QLabel("по:"))
        controlLayout.addWidget(self.dateTo)
        controlLayout.addWidget(QLabel("Категория:"))
        controlLayout.addWidget(self.categoryFilter)
        controlLayout.addWidget(self.selectButton)
        controlLayout.addWidget(self.clearButton)
        controlLayout.addWidget(self.reportButton)
        controlLayout.addStretch()

        # Таблица платежей
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Дата", "Наименование", "Количество", "Цена", "Сумма", "Категория"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.MultiSelection)

        mainLayout.addWidget(controlPanel)
        mainLayout.addWidget(self.table)
        self.layout.addWidget(self.mainBox)

    def load_logins(self):
        """Загрузка логинов пользователей из БД"""
        self.loginCombo.clear()
        self.loginCombo.addItem("Выберите пользователя", None)
        for user in self.session.query(Пользователи).all():
            self.loginCombo.addItem(user.логин, user)

    def load_categories(self):
        """Загрузка категорий из БД"""
        self.categoryFilter.clear()
        self.categoryFilter.addItem("Все категории", None)
        for category in self.session.query(Категории).all():
            self.categoryFilter.addItem(category.название, category)

    def load_data(self):
        """Загрузка данных только для текущего пользователя"""
        if not self.current_user_id:
            return

        query = self.session.query(
            Платежи.дата,
            Платежи.наименование_платежа,
            Платежи.количество,
            Платежи.цена,
            Платежи.стоимость,
            Категории.название
        ).join(Категории).filter(
            Платежи.id_пользователя == self.current_user_id,
            Платежи.дата.between(
                self.dateFrom.date().toString("yyyy-MM-dd"),
                self.dateTo.date().toString("yyyy-MM-dd")
            )
        )

        if self.categoryFilter.currentData():
            query = query.filter(Платежи.id_категории == self.categoryFilter.currentData().id)

        payments = query.order_by(Платежи.дата.desc()).all()

        self.table.setRowCount(0)
        for row, payment in enumerate(payments):
            self.table.insertRow(row)

            date_item = QTableWidgetItem(payment.дата.strftime("%d.%m.%Y"))
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, date_item)

            self.table.setItem(row, 1, QTableWidgetItem(payment.наименование_платежа))

            qty_item = QTableWidgetItem(str(payment.количество))
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 2, qty_item)

            price_item = QTableWidgetItem(f"{payment.цена:.2f}")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 3, price_item)

            amount_item = QTableWidgetItem(f"{payment.стоимость:.2f}")
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 4, amount_item)

            self.table.setItem(row, 5, QTableWidgetItem(payment.название))

    def show_add_payment_dialog(self):
        """Диалог добавления платежа"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить платеж")
        dialog.setFixedSize(400, 300)
        layout = QFormLayout(dialog)

        category_combo = QComboBox()
        for category in self.session.query(Категории).all():
            category_combo.addItem(category.название, category)

        name_edit = QLineEdit()
        name_edit.setPlaceholderText("Минимум 3 символа")

        qty_spin = QSpinBox()
        qty_spin.setMinimum(1)
        qty_spin.setMaximum(999)

        price_spin = QDoubleSpinBox()
        price_spin.setMinimum(0.01)
        price_spin.setMaximum(1000000)
        price_spin.setDecimals(2)
        price_spin.setPrefix("₽ ")

        def calculate_amount():
            try:
                amount = qty_spin.value() * price_spin.value()
                amount_label.setText(f"Сумма: {amount:.2f} ₽")
            except:
                amount_label.setText("Сумма: --")

        qty_spin.valueChanged.connect(calculate_amount)
        price_spin.valueChanged.connect(calculate_amount)

        amount_label = QLabel("Сумма: --")

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        layout.addRow("Категория:", category_combo)
        layout.addRow("Наименование платежа:", name_edit)
        layout.addRow("Количество:", qty_spin)
        layout.addRow("Цена:", price_spin)
        layout.addRow(amount_label)
        layout.addRow(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            if len(name_edit.text().strip()) < 3:
                QMessageBox.warning(self, "Ошибка", "Наименование должно содержать минимум 3 символа")
                return

            try:
                new_payment = Платежи(
                    id_пользователя=self.current_user_id,
                    дата=datetime.now().date(),
                    id_категории=category_combo.currentData().id,
                    наименование_платежа=name_edit.text().strip(),
                    количество=qty_spin.value(),
                    цена=price_spin.value(),
                    стоимость=qty_spin.value() * price_spin.value()
                )

                self.session.add(new_payment)
                print(f"Перед commit: new_payment.id = {new_payment.id}")
                self.session.commit()
                print(f"После commit: new_payment.id = {new_payment.id}")
                self.load_data()
                QMessageBox.information(self, "Успех", "Платеж добавлен")
                QApplication.beep()
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "Ошибка", f"Не удалось добавить платеж: {str(e)}")
                print(f"Ошибка: {str(e)}")
                import traceback
                traceback.print_exc()

    def delete_payment(self):
        """Удаление платежа с подтверждением"""
        selected_rows = set(index.row() for index in self.table.selectedIndexes())
        if not selected_rows:
            QMessageBox.warning(self, "Ошибка", "Выберите платежи для удаления")
            return

        # Get the ID to be deleted (from first selected row if multiple are selected)
        first_selected_row = sorted(selected_rows)[0]  # Always get the FIRST selected
        payment_name_to_delete = self.table.item(first_selected_row, 1).text()

        confirm = QMessageBox(self)
        confirm.setWindowTitle("Подтверждение удаления")
        confirm.setText(f"Удалить запись '{payment_name_to_delete}'?")
        confirm.setInformativeText("Вы уверены, что хотите удалить эту запись?")
        confirm.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        confirm.button(QMessageBox.StandardButton.Ok).setText("Удалить")
        confirm.button(QMessageBox.StandardButton.Cancel).setText("Отмена")
        confirm.setDefaultButton(QMessageBox.StandardButton.Cancel)
        confirm.setIcon(QMessageBox.Icon.Question)

        if confirm.exec() == QMessageBox.StandardButton.Ok:
            try:
                for row in sorted(selected_rows, reverse=True):
                    payment_name = self.table.item(row, 1).text()
                    payment_date = datetime.strptime(self.table.item(row, 0).text(), "%d.%m.%Y").date()

                    payment = self.session.query(Платежи).filter(
                        Платежи.id_пользователя == self.current_user_id,
                        Платежи.наименование_платежа == payment_name,
                        Платежи.дата == payment_date
                    ).first()

                    if payment:
                        self.session.delete(payment)

                self.session.commit()
                self.load_data()
                QMessageBox.information(self, "Успех", f"Удалено {len(selected_rows)} платежей")
                QApplication.beep()
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить платежи: {str(e)}")

    def generate_report(self):
        """Генерация отчета в PDF по выбранным данным"""
        selected_rows = set(index.row() for index in self.table.selectedIndexes())

        if not selected_rows:
            QMessageBox.warning(self, "Ошибка", "Выберите платежи для отчета")
            return

        user = self.session.query(Пользователи).get(self.current_user_id)
        if not user:
            return

        # Получаем данные только для выбранных строк
        payments = []
        for row in selected_rows:
            payment_date = datetime.strptime(self.table.item(row, 0).text(), "%d.%m.%Y").date()
            payment_name = self.table.item(row, 1).text()
            category = self.table.item(row, 5).text()
            amount = float(self.table.item(row, 4).text())
            payments.append((category, payment_name, payment_date, amount))

        # Группируем по категориям и сортируем
        categories = {}
        total = 0.0
        for category, name, date, amount in payments:
            if category not in categories:
                categories[category] = []
            categories[category].append((date.strftime("%d.%m.%Y"), name, amount))
            total += amount

        # Сортируем категории и платежи внутри категорий
        sorted_categories = sorted(categories.items())
        for category in sorted_categories:
            category[1].sort(key=lambda x: x[0])  # Сортировка по дате

        filename, _ = QFileDialog.getSaveFileName(self, "Сохранить отчет", f"Отчет_{user.логин}_{datetime.now().strftime('%Y%m%d')}.pdf", "PDF Files (*.pdf)")

        if not filename:
            return

        try:
            font_path = os.path.join(os.path.dirname(file))
            pdfmetrics.registerFont(TTFont('DejaVuSan', font_path))
            font_name = 'DejaVuSan'
        except:
            font_name = 'Helvetica'
            QMessageBox.warning(self, "Внимание", "Шрифт DejaVuSan не найден. Используется стандартный шрифт.")

        doc = SimpleDocTemplate(filename, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        # Стили для отчета
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontName=font_name,
            fontSize=16,
            alignment=1,
            spaceAfter=20
        )

        category_style = ParagraphStyle(
            'Category',
            parent=styles['Heading2'],
            fontName=font_name,
            fontSize=12,
            textColor=colors.darkblue,
            spaceAfter=5
        )

        item_style = ParagraphStyle(
            'Item',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=10,
            spaceAfter=5
        )

        total_style = ParagraphStyle(
            'Total',
            parent=styles['Heading2'],
            fontName=font_name,
            fontSize=14,
            textColor=colors.darkred,
            alignment=2
        )

        # Заголовок отчета
        elements.append(Paragraph("ОТЧЕТ О ПЛАТЕЖАХ", title_style))
        elements.append(Spacer(1, 12))

        # Данные отчета (соответствуют макету из картинки)
        for category, items in sorted_categories:
            # Название категории и сумма
            category_total = sum(item[2] for item in items)
            elements.append(Paragraph(f"<b>{category}</b> - {category_total:.2f} р.", category_style))

            # Платежи в категории
            for date, name, amount in items:
                elements.append(Paragraph(f"{name} - {amount:.2f} р.", item_style))

            elements.append(Spacer(1, 10))

        # Итоговая сумма
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("_" * 80, styles['Normal']))
        elements.append(Paragraph(f"<b>ИТОГО:</b> {total:.2f} р.", total_style))

        doc.build(elements)
        QMessageBox.information(self, "Успех", f"Отчет сохранен в файл:\n{filename}")

    def clear_filters(self):
        """Сброс фильтров"""
        self.dateFrom.setDate(QDate.currentDate().addMonths(-1))
        self.dateTo.setDate(QDate.currentDate())
        self.categoryFilter.setCurrentIndex(0)
        self.load_data()

    def showUserSelectionDialog(self):
        """Shows the login dialog when the 'Выбор пользователя' button is pressed."""
        self.show_login_dialog()

    def show_login_dialog(self):
        """Shows the login dialog"""
        login_dialog = QDialog(self)
        login_dialog.setWindowTitle("Вход")
        login_dialog.setWindowFlags(login_dialog.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)
        login_dialog.setModal(True)

        login_layout = QVBoxLayout(login_dialog)

        # Use the existing components from the login box
        self.loginCombo = QComboBox()
        self.load_logins()
        self.passwordInput = QLineEdit()
        self.passwordInput.setEchoMode(QLineEdit.EchoMode.Password)
        self.pinInput = QLineEdit()
        self.pinInput.setEchoMode(QLineEdit.EchoMode.Password)
        self.pinInput.setValidator(QIntValidator(1000, 9999))
        self.loginButton = QPushButton("Войти")
        self.loginButton.setStyleSheet("""
            QPushButton {
                background-color: #e91e63;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #ff4081;
            }
            QPushButton:pressed {
                background-color: #c2185b;
            }
        """)
        self.loginButton.clicked.connect(self.authenticate_user_from_dialog)

        login_form_layout = QFormLayout()
        login_form_layout.addRow("Логин:", self.loginCombo)
        login_form_layout.addRow("Пароль:", self.passwordInput)
        login_form_layout.addRow("Пин-код:", self.pinInput)
        login_form_layout.addRow(self.loginButton)

        login_layout.addLayout(login_form_layout)
        # load logins
        self.load_logins()

        self.login_dialog = login_dialog
        login_dialog.exec()

    def authenticate_user_from_dialog(self):
        """Аутентификация пользователя с проверкой пароля и пин-кода (для диалога входа)"""
        user = self.loginCombo.currentData()
        if not user:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя")
            return

        try:
            pin_code = int(self.pinInput.text())
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Пин-код должен быть числом")
            return

        # Проверка пин-кода
        if user.пин_код != pin_code:
            QMessageBox.warning(self, "Ошибка", "Неверный пин-код")
            return

        # Проверка пароля с bcrypt
        if not bcrypt.checkpw(self.passwordInput.text().encode('utf-8'), user.пароль.encode('utf-8')):
            QMessageBox.warning(self, "Ошибка", "Неверный пароль")
            return

        self.current_user_id = user.id
        self.load_data()
        self.login_dialog.accept()
        self.mainBox.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PaymentApp()
    window.show()
    sys.exit(app.exec())