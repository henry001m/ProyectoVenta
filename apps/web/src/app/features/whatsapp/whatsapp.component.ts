import { Component, ElementRef, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { Subject, Subscription, interval, of } from 'rxjs';
import { catchError, debounceTime, filter, switchMap } from 'rxjs/operators';
import { WhatsAppConversation, WhatsAppMessage } from './whatsapp.models';
import { WhatsAppService } from './whatsapp.service';

@Component({
  selector: 'ki-whatsapp',
  standalone: false,
  templateUrl: './whatsapp.component.html',
  styleUrls: ['./whatsapp.component.scss'],
})
export class WhatsAppComponent implements OnInit, OnDestroy {
  @ViewChild('messageLog') private messageLog?: ElementRef<HTMLElement>;

  conversations: WhatsAppConversation[] = [];
  messages: WhatsAppMessage[] = [];
  selected: WhatsAppConversation | null = null;
  search = '';
  unreadOnly = false;
  draft = '';
  loadingConversations = true;
  loadingMessages = false;
  sending = false;
  conversationsError = '';
  accountConnected = false;
  accountChecking = true;
  accountConnecting = false;
  accountError = '';
  messagesError = '';
  sendError = '';

  private readonly subscriptions = new Subscription();
  private readonly searchChanges = new Subject<void>();

  constructor(private readonly whatsapp: WhatsAppService) {}

  ngOnInit(): void {
    this.loadAccountStatus();
    this.loadConversations();
    this.subscriptions.add(this.searchChanges.pipe(debounceTime(250)).subscribe(() => this.loadConversations()));
    this.subscriptions.add(interval(10_000).pipe(
      filter(() => document.visibilityState === 'visible'),
      switchMap(() => this.whatsapp.conversations({ search: this.search, unreadOnly: this.unreadOnly }).pipe(
        catchError(() => { this.conversationsError = 'No se pudo actualizar la bandeja.'; return of(this.conversations); }),
      )),
    ).subscribe({ next: items => this.updateConversations(items) }));
    this.subscriptions.add(interval(5_000).pipe(
      filter(() => document.visibilityState === 'visible' && this.selected !== null),
      switchMap(() => this.whatsapp.messages(this.selected!.id).pipe(
        catchError(() => { this.messagesError = 'No se pudieron actualizar los mensajes.'; return of(this.messages); }),
      )),
    ).subscribe({ next: messages => { this.messages = messages; this.scrollToLatest(); } }));
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
    this.searchChanges.complete();
  }

  onSearch(value: string): void {
    this.search = value;
    this.searchChanges.next();
  }

  toggleUnread(): void {
    this.unreadOnly = !this.unreadOnly;
    this.loadConversations();
  }

  loadAccountStatus(): void {
    this.accountChecking = true;
    this.accountError = '';
    this.subscriptions.add(this.whatsapp.accounts().subscribe({
      next: accounts => { this.accountConnected = accounts.some(account => account.status === 'connected'); this.accountChecking = false; },
      error: () => { this.accountConnected = false; this.accountChecking = false; this.accountError = 'No se pudo consultar el estado de WhatsApp.'; },
    }));
  }

  connectConfiguredAccount(): void {
    if (this.accountConnecting) return;
    this.accountConnecting = true;
    this.accountError = '';
    this.subscriptions.add(this.whatsapp.connectConfiguredAccount().subscribe({
      next: () => { this.accountConnected = true; this.accountConnecting = false; this.loadConversations(); },
      error: error => { this.accountConnecting = false; this.accountError = error?.error?.detail ?? 'No se pudo conectar. Revisa la configuración de Meta en el backend.'; },
    }));
  }

  loadConversations(): void {
    this.loadingConversations = true;
    this.conversationsError = '';
    this.subscriptions.add(this.whatsapp.conversations({ search: this.search, unreadOnly: this.unreadOnly }).subscribe({
      next: items => { this.updateConversations(items); this.loadingConversations = false; },
      error: () => { this.loadingConversations = false; this.conversationsError = 'No se pudo cargar la bandeja. Comprueba la conexión con Kicks Insight.'; },
    }));
  }

  selectConversation(conversation: WhatsAppConversation): void {
    this.selected = conversation;
    this.messages = [];
    this.loadingMessages = true;
    this.messagesError = '';
    this.sendError = '';
    this.subscriptions.add(this.whatsapp.messages(conversation.id).subscribe({
      next: messages => { this.messages = messages; this.loadingMessages = false; this.scrollToLatest(); this.loadConversations(); },
      error: () => { this.loadingMessages = false; this.messagesError = 'No se pudieron cargar los mensajes de esta conversación.'; },
    }));
  }

  backToList(): void { this.selected = null; this.messages = []; }

  send(): void {
    const text = this.draft.trim();
    if (!text || !this.selected || this.sending) return;
    this.sending = true;
    this.sendError = '';
    this.subscriptions.add(this.whatsapp.sendText(this.selected.id, text).subscribe({
      next: message => { this.messages = [...this.messages, message]; this.draft = ''; this.sending = false; this.scrollToLatest(); this.loadConversations(); },
      error: error => { this.sending = false; this.sendError = error?.error?.detail ?? 'No se pudo enviar. Fuera de la ventana de 24 horas se necesita una plantilla aprobada.'; },
    }));
  }

  contactName(conversation: WhatsAppConversation): string {
    return conversation.contact.display_name || conversation.contact.phone_number || conversation.contact.wa_id;
  }

  messageTime(value: string | null): Date | null { return value ? new Date(value) : null; }

  private updateConversations(items: WhatsAppConversation[]): void {
    this.conversations = items;
    if (this.selected) this.selected = items.find(item => item.id === this.selected?.id) ?? this.selected;
  }

  private scrollToLatest(): void {
    setTimeout(() => {
      const element = this.messageLog?.nativeElement;
      if (element) element.scrollTop = element.scrollHeight;
    });
  }
}
