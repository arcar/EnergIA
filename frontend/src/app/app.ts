import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { Sidebar } from './components/sidebar/sidebar';
import { Navbar } from './components/navbar/navbar';
import { ChatbotButton } from './components/chatbot-button/chatbot-button';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, Sidebar, Navbar,ChatbotButton],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {

}