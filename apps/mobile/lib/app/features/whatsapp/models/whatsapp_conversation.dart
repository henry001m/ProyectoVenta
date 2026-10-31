class WhatsAppConversation {
  const WhatsAppConversation(
      {required this.id,
      required this.contactId,
      required this.contactName,
      required this.waId,
      required this.unreadCount,
      this.lastMessageAt,
      this.lastMessagePreview,
      this.lastMessageType,
      this.lastMessageDirection});
  final int id;
  final int contactId;
  final String contactName;
  final String waId;
  final int unreadCount;
  final DateTime? lastMessageAt;
  final String? lastMessagePreview;
  final String? lastMessageType;
  final String? lastMessageDirection;

  factory WhatsAppConversation.fromJson(Map<String, dynamic> json) {
    final contact = json['contact'] as Map<String, dynamic>? ?? const {};
    return WhatsAppConversation(
        id: json['id'] as int,
        contactId: contact['id'] as int? ?? 0,
        contactName: contact['display_name'] as String? ??
            contact['phone_number'] as String? ??
            'Contacto',
        waId: contact['wa_id'] as String? ?? '',
        unreadCount: json['unread_count'] as int? ?? 0,
        lastMessageAt:
            DateTime.tryParse(json['last_message_at'] as String? ?? ''),
        lastMessagePreview: json['last_message_preview'] as String?,
        lastMessageType: json['last_message_type'] as String?,
        lastMessageDirection: json['last_message_direction'] as String?);
  }
}

class WhatsAppMessage {
  const WhatsAppMessage(
      {required this.id,
      required this.direction,
      required this.type,
      required this.body,
      required this.status,
      required this.timestamp});
  final int id;
  final String direction;
  final String type;
  final String body;
  final String status;
  final DateTime timestamp;

  factory WhatsAppMessage.fromJson(Map<String, dynamic> json) =>
      WhatsAppMessage(
          id: json['id'] as int,
          direction: json['direction'] as String? ?? 'inbound',
          type: json['message_type'] as String? ?? 'text',
          body: json['body'] as String? ?? '',
          status: json['status'] as String? ?? 'received',
          timestamp: DateTime.tryParse(json['timestamp'] as String? ?? '') ??
              DateTime.now());
}
