from PySide6 import QtWidgets, QtCore, QtGui
from user_manager import UserManager
from typing import Optional

class UserSelectionDialog(QtWidgets.QDialog):
    def __init__(self, user_manager: UserManager, parent=None):
        super().__init__(parent)
        self.user_manager = user_manager
        self.selected_user: Optional[str] = None
        self.setWindowTitle("Select User")
        self.setMinimumWidth(300)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Title/Instruction
        label = QtWidgets.QLabel("Choose your profile:")
        label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(label)

        # User List
        self.user_list = QtWidgets.QListWidget()
        self.user_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.refresh_user_list()
        self.user_list.itemDoubleClicked.connect(self.accept_selection)
        layout.addWidget(self.user_list)

        # Buttons Layout
        btn_layout = QtWidgets.QHBoxLayout()
        
        # New User Button
        new_btn = QtWidgets.QPushButton("+ New Profile")
        new_btn.clicked.connect(self.create_new_user)
        btn_layout.addWidget(new_btn)
        
        # Delete User Button
        del_btn = QtWidgets.QPushButton("Delete")
        del_btn.setStyleSheet("color: #d32f2f;")
        del_btn.clicked.connect(self.delete_user)
        btn_layout.addWidget(del_btn)

        layout.addLayout(btn_layout)
        
        # Bottom Buttons
        bottom_layout = QtWidgets.QHBoxLayout()
        
        ok_btn = QtWidgets.QPushButton("Start")
        ok_btn.setStyleSheet("font-weight: bold; background-color: #2196f3; color: white; padding: 6px;")
        ok_btn.clicked.connect(self.accept_selection)
        
        cancel_btn = QtWidgets.QPushButton("Exit")
        cancel_btn.clicked.connect(self.reject)
        
        bottom_layout.addWidget(cancel_btn)
        bottom_layout.addWidget(ok_btn)
        
        layout.addLayout(bottom_layout)

    def refresh_user_list(self):
        self.user_list.clear()
        users = self.user_manager.get_users()
        for user in users:
            self.user_list.addItem(user)
        
        # Do not auto-select the first user (row 0) to avoid accidental logins to the wrong account.
        # User must explicitly choose.

    def create_new_user(self):
        name, ok = QtWidgets.QInputDialog.getText(self, "New User", "Enter profile name:")
        if ok and name:
            name = name.strip()
            if not name:
                return
            
            clean_name = self.user_manager.sanitize_username(name)
            if not clean_name:
                QtWidgets.QMessageBox.warning(self, "Invalid Name", "Name contains invalid characters.\nAllowed: A-Z, 0-9, space, -, _")
                return

            if self.user_manager.create_user(name):
                self.refresh_user_list()
                # Select the new user
                items = self.user_list.findItems(clean_name, QtCore.Qt.MatchFlag.MatchExactly)
                if items:
                    self.user_list.setCurrentItem(items[0])
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "Could not create user. Name might be invalid or already taken.")

    def delete_user(self):
        current_item = self.user_list.currentItem()
        if not current_item:
            return
            
        username = current_item.text()
        
        confirm = QtWidgets.QMessageBox.question(
            self, 
            "Confirm Deletion", 
            f"Are you sure you want to delete profile '{username}'?\nThis cannot be undone.",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )
        
        if confirm == QtWidgets.QMessageBox.StandardButton.Yes:
            if self.user_manager.delete_user(username):
                self.refresh_user_list()
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "Could not delete user.")

    def accept_selection(self):
        current_item = self.user_list.currentItem()
        if current_item:
            self.selected_user = current_item.text()
            self.accept()
        else:
            QtWidgets.QMessageBox.warning(self, "Select User", "Please select a user profile.")

