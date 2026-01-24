"""User Selection Dialog - Styled Version

Frameless, dark-themed dialog for selecting user profiles.
"""

from PySide6 import QtWidgets, QtCore, QtGui
from user_manager import UserManager
from styled_dialog import StyledDialog, StyledMessageBox, StyledInputDialog
from typing import Optional


class UserSelectionDialog(StyledDialog):
    """Styled dialog for selecting or creating user profiles."""
    
    def __init__(self, user_manager: UserManager, parent=None):
        self.user_manager = user_manager
        self.selected_user: Optional[str] = None
        
        super().__init__(
            parent=parent,
            title="Select Profile",
            header_icon="👤",
            min_width=350,
            max_width=450,
        )

    def _build_content(self, layout: QtWidgets.QVBoxLayout):
        # Instruction
        label = QtWidgets.QLabel("Choose your profile:")
        label.setStyleSheet("font-weight: bold; font-size: 13px; color: #E0E0E0;")
        layout.addWidget(label)

        # User List
        self.user_list = QtWidgets.QListWidget()
        self.user_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.user_list.setMinimumHeight(150)
        self.refresh_user_list()
        self.user_list.itemDoubleClicked.connect(self.accept_selection)
        layout.addWidget(self.user_list)

        # Management Buttons
        mgmt_layout = QtWidgets.QHBoxLayout()
        
        new_btn = QtWidgets.QPushButton("➕ New Profile")
        new_btn.clicked.connect(self.create_new_user)
        mgmt_layout.addWidget(new_btn)
        
        del_btn = QtWidgets.QPushButton("🗑️ Delete")
        del_btn.setObjectName("dangerButton")
        del_btn.clicked.connect(self.delete_user)
        mgmt_layout.addWidget(del_btn)
        
        layout.addLayout(mgmt_layout)
        
        layout.addSpacing(10)
        
        # Bottom Buttons
        self.add_button_row(layout, [
            ("Exit", "default", self.reject),
            ("Start", "primary", self.accept_selection),
        ])

    def refresh_user_list(self):
        self.user_list.clear()
        users = self.user_manager.get_users()
        for user in users:
            self.user_list.addItem(user)
        
        # Auto-select first user if list is not empty
        if self.user_list.count() > 0:
            self.user_list.setCurrentRow(0)

    def create_new_user(self):
        name, ok = StyledInputDialog.get_text(
            self, 
            "New Profile", 
            "Enter profile name:",
            icon="👤"
        )
        if ok and name:
            name = name.strip()
            if not name:
                return
            
            clean_name = self.user_manager.sanitize_username(name)
            if not clean_name:
                StyledMessageBox.warning(
                    self, 
                    "Invalid Name", 
                    "Name contains invalid characters.",
                    "Allowed: A-Z, 0-9, space, -, _"
                )
                return

            if self.user_manager.create_user(name):
                self.refresh_user_list()
                # Select the new user
                items = self.user_list.findItems(clean_name, QtCore.Qt.MatchFlag.MatchExactly)
                if items:
                    self.user_list.setCurrentItem(items[0])
            else:
                StyledMessageBox.warning(
                    self, 
                    "Error", 
                    "Could not create user.",
                    "Name might be invalid or already taken."
                )

    def delete_user(self):
        current_item = self.user_list.currentItem()
        if not current_item:
            return
            
        username = current_item.text()
        
        result = StyledMessageBox.question(
            self, 
            "Confirm Deletion", 
            f"Are you sure you want to delete profile '{username}'?\n\nThis cannot be undone.",
            ["Cancel", "Delete"]
        )
        
        if result == "Delete":
            if self.user_manager.delete_user(username):
                self.refresh_user_list()
            else:
                StyledMessageBox.warning(self, "Error", "Could not delete user.")

    def accept_selection(self):
        current_item = self.user_list.currentItem()
        if current_item:
            self.selected_user = current_item.text()
            self.accept()
        elif self.user_list.count() == 0:
            StyledMessageBox.warning(
                self, 
                "No Profiles", 
                "No user profiles exist yet.\n\nClick '➕ New Profile' to create one."
            )
        else:
            StyledMessageBox.warning(self, "Select User", "Please select a user profile.")
