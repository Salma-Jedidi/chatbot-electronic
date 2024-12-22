import { RouterModule, Routes } from '@angular/router';
import { ChatbotComponent } from './chatbot/chatbot.component';
import { AppComponent } from './app.component';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

export const routes: Routes = [
    { path: '', component: AppComponent },
    { path: 'chat', component: ChatbotComponent }
];
@NgModule({
    imports: [RouterModule.forRoot(routes),CommonModule,FormsModule],
    exports: [RouterModule],
  })
  export class AppRoutingModule {}