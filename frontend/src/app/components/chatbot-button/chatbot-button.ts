import { Component } from '@angular/core';

@Component({
  imports: [],
  selector: 'app-chatbot-button',
  styleUrl: './chatbot-button.scss',
  templateUrl: './chatbot-button.html',
})
export class ChatbotButton {
  isOpen = false;
  toggleChat(): void {
    this.isOpen = !this.isOpen;
  }
}
