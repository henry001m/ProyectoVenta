import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { API_BASE_URL } from '@/core/config/api.config';
import { WhatsAppAccount, WhatsAppConversation, WhatsAppConversationQuery, WhatsAppMessage } from './whatsapp.models';

@Injectable({ providedIn: 'root' })
export class WhatsAppService {
  constructor(private readonly http: HttpClient) {}

  conversations(query: WhatsAppConversationQuery = {}): Observable<WhatsAppConversation[]> {
    let params = new HttpParams()
      .set('limit', query.limit ?? 50)
      .set('offset', query.offset ?? 0)
      .set('unread_only', query.unreadOnly ?? false);
    if (query.search?.trim()) params = params.set('search', query.search.trim());
    return this.http.get<WhatsAppConversation[]>(`${API_BASE_URL}/whatsapp/conversations`, { params });
  }

  accounts(): Observable<WhatsAppAccount[]> {
    return this.http.get<WhatsAppAccount[]>(`${API_BASE_URL}/whatsapp/accounts`);
  }

  connectConfiguredAccount(): Observable<WhatsAppAccount> {
    return this.http.post<WhatsAppAccount>(`${API_BASE_URL}/whatsapp/accounts`, {});
  }

  messages(conversationId: number, beforeId?: number): Observable<WhatsAppMessage[]> {
    let params = new HttpParams().set('limit', 50);
    if (beforeId) params = params.set('before_id', beforeId);
    return this.http.get<WhatsAppMessage[]>(`${API_BASE_URL}/whatsapp/conversations/${conversationId}/messages`, { params });
  }

  sendText(conversationId: number, text: string): Observable<WhatsAppMessage> {
    return this.http.post<WhatsAppMessage>(`${API_BASE_URL}/whatsapp/conversations/${conversationId}/messages`, { type: 'text', text });
  }
}
