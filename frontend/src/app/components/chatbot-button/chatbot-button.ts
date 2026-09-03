import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';

@Component({
  imports: [FormsModule],
  selector: 'app-chatbot-button',
  styleUrl: './chatbot-button.scss',
  templateUrl: './chatbot-button.html',
})
export class ChatbotButton {
  isOpen = false;
  messageInput = '';
  messages: {
    content: string;
    role: 'user' | 'assistant';
  }[] = [
  {
    content: 'Bonjour ! Je suis l’assistant EnergIA. Comment puis-je vous aider ?',
    role: 'assistant'
  }
  ];
  toggleChat(): void {
    this.isOpen = !this.isOpen;
  }
}
