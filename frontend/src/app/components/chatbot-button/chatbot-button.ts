import { ChangeDetectorRef, Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AssistantService } from '../../services/assistant'

@Component({
  imports: [FormsModule],
  selector: 'app-chatbot-button',
  styleUrl: './chatbot-button.scss',
  templateUrl: './chatbot-button.html',
})
export class ChatbotButton {
  isOpen = false;
  isLoading = false;
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

  constructor(
  private assistantService: AssistantService,
  private cdr: ChangeDetectorRef
) {}

  toggleChat(): void {
    this.isOpen = !this.isOpen;
  }

  sendMessage(): void {
    const prompt = this.messageInput.trim();

    if (!prompt) {
      return;
    }

    this.messages.push({
      content: prompt,
      role: 'user'
    });

    this.messageInput = '';
    this.isLoading = true;

    this.assistantService.sendMessage(prompt).subscribe({
      

      next: (response) => {
        console.log('Réponse reçue par Angular :', response);
        const data = response.response;

        if (typeof data === 'string') {
          this.messages.push({
            content: data,
            role: 'assistant'
          });
          this.isLoading = false;
          this.cdr.detectChanges();
          return;
        }

        this.messages.push({
          content: `${data.count} centrales nucléaires disponibles :\n\n${data.plants.map(plant => `• ${plant}`).join('\n')}`,
          role: 'assistant'
        });
        this.isLoading = false;
        this.cdr.detectChanges();
      },
      error: (error) => {
        console.error('Erreur assistant :', error);

        this.messages.push({
          content: 'Une erreur est survenue lors de la communication avec l’assistant.',
          role: 'assistant'
        });
        this.isLoading = false;
        this.cdr.detectChanges();
      }
    });
  }
}