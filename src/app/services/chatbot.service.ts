import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ChatbotService {

  private apiUrl = 'http://127.0.0.1:5001/api';

  constructor(private http: HttpClient) { }

  sendMessage(message: string): Observable<any> {
    const body = { msg: message };
    return this.http.post<any>(this.apiUrl, body);
  }
 
  testConnection(): Observable<any> {
    console.log('Testing connection from service...');
    return this.http.get<any>(`${this.apiUrl}/test/connection`);
  }
  
  
}
