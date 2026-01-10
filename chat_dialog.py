"""
Interactive Chat Dialog for SEAL Geo RAG Chatbot
"""

import os
from datetime import datetime
from qgis.PyQt.QtCore import Qt, QTimer
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QLineEdit, QPushButton, QLabel, QMessageBox, QFileDialog
)
from qgis.PyQt.QtGui import QTextCursor, QFont


class ChatDialog(QDialog):
    """Interactive chat dialog for continuous conversation with RAG chatbot."""
    
    def __init__(self, sealgeo_agent, initial_mission="", parent=None):
        """Initialize chat dialog.
        
        Args:
            sealgeo_agent: SEALGeoAgent instance for API queries
            initial_mission: Optional initial mission text
            parent: Parent widget
        """
        super().__init__(parent)
        self.sealgeo_agent = sealgeo_agent
        self.conversation_history = []
        
        self.setWindowTitle("SEAL Geo RAG Chatbot - Interactive Chat")
        self.setMinimumSize(700, 600)
        self.resize(800, 650)
        
        self.setup_ui()
        
        # If initial mission provided, send it as first message
        if initial_mission:
            QTimer.singleShot(100, lambda: self.send_message(initial_mission))
    
    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout()
        
        # Header
        header_label = QLabel("💬 Interactive Chat with SEAL Geo RAG Chatbot")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label)
        
        # Info label
        info_label = QLabel(
            "Ask questions about mission planning, flood response, geospatial operations, etc.\n"
            "The chatbot uses RAG (Retrieval-Augmented Generation) with mission-specific knowledge."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(info_label)
        
        # Chat history display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11pt;
            }
        """)
        layout.addWidget(self.chat_display)
        
        # Input area
        input_layout = QHBoxLayout()
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type your message here...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #4CAF50;
                border-radius: 4px;
                font-size: 11pt;
            }
            QLineEdit:focus {
                border-color: #45a049;
            }
        """)
        self.input_field.returnPressed.connect(self.on_send_clicked)
        input_layout.addWidget(self.input_field)
        
        self.send_button = QPushButton("Send")
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.send_button.clicked.connect(self.on_send_clicked)
        input_layout.addWidget(self.send_button)
        
        layout.addLayout(input_layout)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        self.clear_button = QPushButton("Clear Chat")
        self.clear_button.clicked.connect(self.clear_chat)
        button_layout.addWidget(self.clear_button)
        
        button_layout.addStretch()
        
        self.save_button = QPushButton("Save Conversation")
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 6px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        self.save_button.clicked.connect(self.save_conversation)
        button_layout.addWidget(self.save_button)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Welcome message
        self.append_system_message("Welcome! Ask me anything about mission planning, flood response, or geospatial operations.")
    
    def append_system_message(self, text):
        """Append a system message to the chat display."""
        self.chat_display.append(f'<div style="color: #888; font-style: italic; margin: 5px 0;">ℹ️ {text}</div>')
        self.chat_display.append("")
    
    def append_user_message(self, text):
        """Append a user message to the chat display."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.chat_display.append(
            f'<div style="background-color: #E3F2FD; padding: 8px; border-radius: 8px; margin: 5px 0;">'
            f'<b style="color: #1976D2;">You</b> <span style="color: #999; font-size: 9pt;">({timestamp})</span><br>'
            f'{self._format_text(text)}'
            f'</div>'
        )
        self.chat_display.append("")
        
        # Scroll to bottom
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.chat_display.setTextCursor(cursor)
    
    def append_bot_message(self, text):
        """Append a bot message to the chat display."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.chat_display.append(
            f'<div style="background-color: #F1F8E9; padding: 8px; border-radius: 8px; margin: 5px 0;">'
            f'<b style="color: #558B2F;">🤖 SEAL Geo RAG</b> <span style="color: #999; font-size: 9pt;">({timestamp})</span><br>'
            f'{self._format_text(text)}'
            f'</div>'
        )
        self.chat_display.append("")
        
        # Scroll to bottom
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.chat_display.setTextCursor(cursor)
    
    def append_error_message(self, text):
        """Append an error message to the chat display."""
        self.chat_display.append(
            f'<div style="background-color: #FFEBEE; padding: 8px; border-radius: 8px; margin: 5px 0; color: #C62828;">'
            f'<b>❌ Error:</b> {self._format_text(text)}'
            f'</div>'
        )
        self.chat_display.append("")
    
    def _format_text(self, text):
        """Format text for HTML display (escape HTML and preserve line breaks)."""
        # Escape HTML special characters
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        # Convert line breaks to <br>
        text = text.replace('\n', '<br>')
        return text
    
    def on_send_clicked(self):
        """Handle send button click."""
        message = self.input_field.text().strip()
        
        if not message:
            return
        
        self.send_message(message)
    
    def send_message(self, message):
        """Send a message to the chatbot.
        
        Args:
            message: Message text to send
        """
        # Clear input field
        self.input_field.clear()
        
        # Disable input while processing
        self.input_field.setEnabled(False)
        self.send_button.setEnabled(False)
        self.send_button.setText("Sending...")
        
        # Display user message
        self.append_user_message(message)
        
        # Add to conversation history
        self.conversation_history.append({
            'timestamp': datetime.now().isoformat(),
            'role': 'user',
            'content': message
        })
        
        # Query the chatbot
        try:
            # Call the chatbot endpoint directly for cleaner response
            result = self.sealgeo_agent._query_chatbot(message)
            
            if result and 'answer' in result:
                response = result['answer']
                self.append_bot_message(response)
                
                # Add to conversation history
                self.conversation_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'role': 'assistant',
                    'content': response
                })
            else:
                error_msg = "No response received from the chatbot. Please try again."
                self.append_error_message(error_msg)
                
                # Still log the error in history
                self.conversation_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'role': 'error',
                    'content': error_msg
                })
        
        except Exception as e:
            error_msg = f"Failed to query chatbot: {str(e)}"
            self.append_error_message(error_msg)
            
            # Log error in history
            self.conversation_history.append({
                'timestamp': datetime.now().isoformat(),
                'role': 'error',
                'content': error_msg
            })
        
        finally:
            # Re-enable input
            self.input_field.setEnabled(True)
            self.send_button.setEnabled(True)
            self.send_button.setText("Send")
            self.input_field.setFocus()
    
    def clear_chat(self):
        """Clear the chat history."""
        reply = QMessageBox.question(
            self,
            "Clear Chat",
            "Are you sure you want to clear the chat history?\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.chat_display.clear()
            self.conversation_history = []
            self.append_system_message("Chat cleared. Start a new conversation!")
    
    def save_conversation(self):
        """Save the conversation to a file."""
        if not self.conversation_history:
            QMessageBox.information(
                self,
                "No Conversation",
                "There is no conversation to save yet."
            )
            return
        
        # Ask user for save location
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Conversation",
            os.path.expanduser(f"~/sealgeo_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"),
            "Text Files (*.txt);;JSON Files (*.json);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            # Determine format from extension
            if file_path.endswith('.json'):
                self._save_as_json(file_path)
            else:
                self._save_as_text(file_path)
            
            QMessageBox.information(
                self,
                "Success",
                f"Conversation saved to:\n{file_path}"
            )
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save conversation:\n{str(e)}"
            )
    
    def _save_as_text(self, file_path):
        """Save conversation as formatted text file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("SEAL Geo RAG Chatbot - Conversation Transcript\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            for entry in self.conversation_history:
                timestamp = datetime.fromisoformat(entry['timestamp']).strftime('%H:%M:%S')
                role = entry['role'].upper()
                content = entry['content']
                
                if role == 'USER':
                    f.write(f"[{timestamp}] YOU:\n")
                elif role == 'ASSISTANT':
                    f.write(f"[{timestamp}] SEAL GEO RAG:\n")
                elif role == 'ERROR':
                    f.write(f"[{timestamp}] ERROR:\n")
                
                f.write(f"{content}\n")
                f.write("\n" + "-" * 80 + "\n\n")
            
            f.write("=" * 80 + "\n")
            f.write("End of Conversation\n")
            f.write("=" * 80 + "\n")
    
    def _save_as_json(self, file_path):
        """Save conversation as JSON file."""
        import json
        
        output = {
            'session_id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'timestamp': datetime.now().isoformat(),
            'chatbot': 'SEAL Geo RAG',
            'conversation': self.conversation_history
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
    
    def get_conversation_history(self):
        """Get the conversation history.
        
        Returns:
            List of conversation entries
        """
        return self.conversation_history
