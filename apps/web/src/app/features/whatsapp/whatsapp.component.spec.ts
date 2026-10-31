import { fakeAsync, TestBed, tick } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { WhatsAppModule } from './whatsapp.module';
import { WhatsAppComponent } from './whatsapp.component';
import { WhatsAppService } from './whatsapp.service';
import { API_BASE_URL } from '@/core/config/api.config';

describe('WhatsApp inbox', () => {
  let http: HttpTestingController;
  let component: WhatsAppComponent;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HttpClientTestingModule, WhatsAppModule] });
    http = TestBed.inject(HttpTestingController);
    const fixture = TestBed.createComponent(WhatsAppComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  afterEach(() => http.verify());

  function flushInitial(account: unknown[] = [], conversations: unknown[] = []): void {
    http.expectOne(`${API_BASE_URL}/whatsapp/accounts`).flush(account);
    http.expectOne(request => request.url === `${API_BASE_URL}/whatsapp/conversations`).flush(conversations);
  }

  it('shows disconnected and empty states', () => {
    flushInitial();
    expect(component.accountConnected).toBeFalse();
    expect(component.conversations).toEqual([]);
    expect(component.loadingConversations).toBeFalse();
  });

  it('sends search and unread filters to the API', fakeAsync(() => {
    flushInitial();
    component.onSearch('Jordan');
    tick(251);
    const searchRequest = http.expectOne(request => request.url === `${API_BASE_URL}/whatsapp/conversations` && request.params.get('search') === 'Jordan');
    searchRequest.flush([]);
    component.toggleUnread();
    const unreadRequest = http.expectOne(request => request.url === `${API_BASE_URL}/whatsapp/conversations` && request.params.get('unread_only') === 'true');
    unreadRequest.flush([]);
    expect(component.unreadOnly).toBeTrue();
  }));

  it('loads messages and posts a text reply', () => {
    flushInitial([{ id: 7, status: 'connected' }], []);
    const conversation = {
      id: 20,
      contact: { id: 11, wa_id: '59170000001', phone_number: '59170000001', display_name: 'Cliente' },
      last_message_at: '2026-10-30T10:00:00Z', last_customer_message_at: '2026-10-30T10:00:00Z', unread_count: 1,
      last_message_preview: 'Busco Jordan', last_message_type: 'text', last_message_direction: 'inbound',
    };
    component.selectConversation(conversation);
    http.expectOne(`${API_BASE_URL}/whatsapp/conversations/20/messages?limit=50`).flush([]);
    http.expectOne(request => request.url === `${API_BASE_URL}/whatsapp/conversations`).flush([conversation]);
    component.draft = 'Hola, sí tenemos';
    component.send();
    const sendRequest = http.expectOne(`${API_BASE_URL}/whatsapp/conversations/20/messages`);
    expect(sendRequest.request.body).toEqual({ type: 'text', text: 'Hola, sí tenemos' });
    sendRequest.flush({ id: 5, meta_message_id: 'wamid.5', direction: 'outbound', message_type: 'text', body: 'Hola, sí tenemos', status: 'sent', timestamp: '2026-10-30T10:01:00Z', media_id: null });
    http.expectOne(request => request.url === `${API_BASE_URL}/whatsapp/conversations`).flush([conversation]);
    expect(component.draft).toBe('');
    expect(component.messages[0].body).toBe('Hola, sí tenemos');
  });
});

describe('WhatsAppService', () => {
  it('serializes pagination, search, and unread filter', () => {
    TestBed.configureTestingModule({ imports: [HttpClientTestingModule] });
    const service = TestBed.inject(WhatsAppService);
    const http = TestBed.inject(HttpTestingController);
    service.conversations({ search: 'Nike', unreadOnly: true, limit: 25, offset: 25 }).subscribe();
    const request = http.expectOne(item => item.url === `${API_BASE_URL}/whatsapp/conversations`);
    expect(request.request.params.get('search')).toBe('Nike');
    expect(request.request.params.get('unread_only')).toBe('true');
    expect(request.request.params.get('limit')).toBe('25');
    expect(request.request.params.get('offset')).toBe('25');
    request.flush([]);
    http.verify();
  });
});
