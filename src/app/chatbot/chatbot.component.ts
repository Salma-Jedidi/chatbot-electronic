import { Component, ViewChild, ElementRef, AfterViewInit } from '@angular/core';
import { ChatbotService } from '../services/chatbot.service';
import { Renderer2 } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-chatbot',
  standalone: true,
  imports: [RouterModule, FormsModule, CommonModule], 
  templateUrl: './chatbot.component.html',
  styleUrls: ['./chatbot.component.css'],
})
export class ChatbotComponent implements AfterViewInit {
  @ViewChild('messageArea', { static: false }) messageArea!: ElementRef;
  userQuery: string = '';
  selectedQuestion: string = '';
  messages: Array<{ type: 'user' | 'bot', content: string, time: string }> = [];

  predefinedQuestions = [
    { "user": "What is the price of the iPhone?" },
    { "user": "Tell me about the laptops." },
    {"user": "What categories of electronics do you have?"}
    // more questions...
  ];
  constructor(private chatbotService: ChatbotService, private renderer: Renderer2) {}

  ngAfterViewInit() {
    if (this.messageArea) {
      this.scrollToBottom();  // Call this after the view is initialized
    }
  }

  sendMessage() {
    const date = new Date();
    const hour = this.formatTime(date.getHours());
    const minute = this.formatTime(date.getMinutes());
    const strTime = `${hour}:${minute}`;
    const rawText = this.selectedQuestion || this.userQuery;

    // Add user message to the messages array
    this.messages.push({ type: 'user', content: rawText, time: strTime });

    this.userQuery = '';
    this.selectedQuestion = '';

    // Send user message to the server
    this.chatbotService.sendMessage(rawText).subscribe(
      (data) => {
        // Add bot message to the messages array
        this.messages.push({ type: 'bot', content: data.response, time: strTime });
        this.scrollToBottom();  // Auto-scroll after receiving bot response
      },
      (error) => {
        console.error('Error sending message:', error);
        this.messages.push({ type: 'bot', content: 'Désolé, une erreur est survenue. Veuillez réessayer.', time: strTime });
        this.scrollToBottom();  // Auto-scroll even in case of error
      }
    );
  }

  // Format time to always show two digits
  formatTime(time: number): string {
    return time < 10 ? `0${time}` : `${time}`;
  }

  // Scroll to the bottom of the message area
  scrollToBottom() {
    if (this.messageArea) {
      setTimeout(() => {
        this.messageArea.nativeElement.scrollTop = this.messageArea.nativeElement.scrollHeight;
      }, 0);
    }
  }

  // Handle user selecting a predefined question
  selectPredefinedQuestion(question: string) {
    this.selectedQuestion = question;
    this.sendMessage();  // Automatically send selected predefined question
  }
}
