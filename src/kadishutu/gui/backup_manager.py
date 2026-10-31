from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from kadishutu.core.shared.backups import (
    BackupEntry,
    create_backup,
    delete_backup,
    list_backups,
    restore_backup,
    validate_backup,
)


def _format_size(size: int) -> str:
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.2f} MiB"
    if size >= 1024:
        return f"{size / 1024:.1f} KiB"
    return f"{size} B"


class BackupManagerDialog(QDialog):
    def __init__(self, target: Path, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.target = Path(target)
        self.entries: list[BackupEntry] = []
        self.restored = False
        self.setWindowTitle(f"Backups — {self.target.name}")
        self.resize(820, 520)
        self.setModal(True)

        self.outer = QVBoxLayout(self)
        self.outer.setContentsMargins(20, 18, 20, 18)
        self.outer.setSpacing(12)

        self.title = QLabel("Backups", self)
        self.title.setObjectName("PageTitle")
        self.outer.addWidget(self.title)
        self.path_label = QLabel(str(self.target), self)
        self.path_label.setObjectName("Muted")
        self.path_label.setWordWrap(True)
        self.outer.addWidget(self.path_label)
        self.summary = QLabel(self)
        self.summary.setObjectName("Muted")
        self.outer.addWidget(self.summary)

        self.table = QTableWidget(0, 4, self)
        self.table.setHorizontalHeaderLabels(
            ["Created", "Size", "Type", "File"]
        )
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        for column in range(3):
            header.setSectionResizeMode(
                column,
                QHeaderView.ResizeMode.ResizeToContents,
            )
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.itemSelectionChanged.connect(self.selection_changed)
        self.outer.addWidget(self.table, 1)

        self.details = QLabel("Select a backup to see details.", self)
        self.details.setWordWrap(True)
        self.details.setObjectName("Muted")
        self.outer.addWidget(self.details)

        self.status = QLabel("", self)
        self.status.setWordWrap(True)
        self.outer.addWidget(self.status)

        actions = QHBoxLayout()
        self.create_button = QPushButton("Create backup now", self)
        self.create_button.setObjectName("PrimaryButton")
        self.create_button.clicked.connect(self.create_now)
        actions.addWidget(self.create_button)
        self.restore_button = QPushButton("Restore selected", self)
        self.restore_button.clicked.connect(self.restore_selected)
        actions.addWidget(self.restore_button)
        self.delete_button = QPushButton("Delete selected", self)
        self.delete_button.clicked.connect(self.delete_selected)
        actions.addWidget(self.delete_button)
        actions.addStretch()
        self.folder_button = QPushButton("Open folder", self)
        self.folder_button.clicked.connect(self.open_folder)
        actions.addWidget(self.folder_button)
        self.close_button = QPushButton("Close", self)
        self.close_button.clicked.connect(self.reject)
        actions.addWidget(self.close_button)
        self.outer.addLayout(actions)

        self.refresh()

    def refresh(self):
        previous = self.selected_entry()
        previous_path = previous.path if previous else None
        self.entries = list_backups(self.target)
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        for entry in self.entries:
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [
                entry.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                _format_size(entry.size),
                "Automatic" if entry.kind == "timestamped" else "Legacy",
                entry.path.name,
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, str(entry.path))
                self.table.setItem(row, column, item)
        self.table.blockSignals(False)

        if previous_path is not None:
            for row, entry in enumerate(self.entries):
                if entry.path == previous_path:
                    self.table.selectRow(row)
                    break
            else:
                if self.entries:
                    self.table.selectRow(0)
        elif self.entries:
            self.table.selectRow(0)
        else:
            self.table.clearSelection()

        total = sum(entry.size for entry in self.entries)
        current = (
            _format_size(self.target.stat().st_size)
            if self.target.exists()
            else "missing"
        )
        self.summary.setText(
            f"{len(self.entries)} backup(s) · {_format_size(total)} total · "
            f"current save: {current}"
        )
        self.create_button.setEnabled(self.target.is_file())
        self.selection_changed()

    def selected_entry(self) -> BackupEntry | None:
        row = self.table.currentRow()
        if 0 <= row < len(self.entries):
            return self.entries[row]
        return None

    def selection_changed(self):
        entry = self.selected_entry()
        if entry is None:
            self.restore_button.setEnabled(False)
            self.delete_button.setEnabled(False)
            self.details.setText("Select a backup to see details.")
            return
        check = validate_backup(entry)
        self.restore_button.setEnabled(True)
        self.delete_button.setEnabled(True)
        self.details.setText(
            f"{entry.path}\n"
            f"{_format_size(entry.size)} · "
            f"{'Automatic' if entry.kind == 'timestamped' else 'Legacy'} · "
            f"{check.message}"
        )

    def create_now(self):
        try:
            entry = create_backup(self.target)
        except Exception as exc:
            QMessageBox.critical(self, "Backup failed", str(exc))
            return
        self.refresh()
        for row, candidate in enumerate(self.entries):
            if candidate.path == entry.path:
                self.table.selectRow(row)
                break
        self.status.setText(f"Created {entry.path.name}")

    def restore_selected(self):
        entry = self.selected_entry()
        if entry is None:
            return
        check = validate_backup(entry)
        if not check.ok:
            answer = QMessageBox.warning(
                self,
                "Backup check failed",
                f"{check.message}\n\nRestore this backup anyway?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        answer = QMessageBox.question(
            self,
            "Restore backup",
            "Replace the current save with this backup?\n\n"
            "A safety backup of the current save will be created first. "
            "Close the game before continuing.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            safety = restore_backup(entry)
        except Exception as exc:
            QMessageBox.critical(self, "Restore failed", str(exc))
            return

        self.restored = True
        self.refresh()
        message = f"Restored {entry.path.name}."
        if safety is not None:
            message += f"\nSafety backup: {safety.name}"
        self.status.setText(message)
        QMessageBox.information(self, "Backup restored", message)

    def delete_selected(self):
        entry = self.selected_entry()
        if entry is None:
            return
        answer = QMessageBox.warning(
            self,
            "Delete backup",
            f"Permanently delete this backup?\n\n{entry.path}\n\n"
            "This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            delete_backup(entry)
        except Exception as exc:
            QMessageBox.critical(self, "Delete failed", str(exc))
            return
        self.refresh()
        self.status.setText(f"Deleted {entry.path.name}")

    def open_folder(self):
        QDesktopServices.openUrl(
            QUrl.fromLocalFile(str(self.target.parent))
        )
