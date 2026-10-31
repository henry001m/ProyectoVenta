export interface WhatsAppContact {
  id: number;
  wa_id: string;
  phone_number: string | null;
  display_name: string | null;
}

export interface WhatsAppConversation {
  id: number;
  contact: WhatsAppContact;
  last_message_at: string | null;
  last_customer_message_at: string | null;
  unread_count: number;
  last_message_preview: string | null;
  last_message_type: string | null;
  last_message_direction: string | null;
}

export interface WhatsAppMessage {
  id: number;
  meta_message_id: string;
  direction: 'inbound' | 'outbound';
  message_type: string;
  body: string;
  status: string;
  timestamp: string;
  media_id: string | null;
}

export interface WhatsAppConversationQuery {
  search?: string;
  unreadOnly?: boolean;
  limit?: number;
  offset?: number;
}

export interface WhatsAppAccount {
  id: number;
  display_phone_number: string | null;
  status: 'connected' | 'disconnected' | string;
}
