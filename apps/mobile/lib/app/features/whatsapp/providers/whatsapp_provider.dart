import 'package:flutter/foundation.dart';
import '../../../core/network/api_client.dart';
import '../models/whatsapp_conversation.dart';

class WhatsAppProvider extends ChangeNotifier {
  WhatsAppProvider(this._api);
  final ApiClient _api;
  bool loading = false;
  bool connecting = false;
  bool sending = false;
  bool loadingMessages = false;
  bool accountChecking = true;
  bool accountConnected = false;
  bool unreadOnly = false;
  String? error;
  String search = '';
  int? selectedConversationId;
  List<WhatsAppConversation> conversations = [];
  List<WhatsAppMessage> messages = [];

  Future<void> loadAccountStatus() async {
    accountChecking = true;
    notifyListeners();
    try {
      final response = await _api.get<List<dynamic>>('/whatsapp/accounts');
      accountConnected = (response.data ?? [])
          .whereType<Map<String, dynamic>>()
          .any((account) => account['status'] == 'connected');
    } catch (_) {
      accountConnected = false;
    } finally {
      accountChecking = false;
      notifyListeners();
    }
  }

  Future<bool> connectConfiguredAccount() async {
    connecting = true;
    error = null;
    notifyListeners();
    try {
      await _api.post('/whatsapp/accounts', data: const <String, dynamic>{});
      accountConnected = true;
      await loadConversations();
      return true;
    } catch (_) {
      error =
          'No se pudo conectar. Configura las credenciales de Meta en el backend y confirma que el Phone Number ID esté autorizado.';
      return false;
    } finally {
      connecting = false;
      notifyListeners();
    }
  }

  Future<void> loadConversations({String? search, bool? unreadOnly}) async {
    if (search != null) this.search = search;
    if (unreadOnly != null) this.unreadOnly = unreadOnly;
    loading = true;
    error = null;
    notifyListeners();
    try {
      final response = await _api
          .get<List<dynamic>>('/whatsapp/conversations', queryParameters: {
        'limit': 50,
        'offset': 0,
        'search': this.search,
        'unread_only': this.unreadOnly,
      });
      conversations = (response.data ?? [])
          .whereType<Map<String, dynamic>>()
          .map(WhatsAppConversation.fromJson)
          .toList();
    } catch (_) {
      error =
          'No se pudieron cargar las conversaciones. Verifica la conexión con la API.';
    } finally {
      loading = false;
      notifyListeners();
    }
  }

  Future<void> loadMessages(int conversationId, {int? beforeId}) async {
    loadingMessages = true;
    try {
      final response = await _api.get<List<dynamic>>(
          '/whatsapp/conversations/$conversationId/messages',
          queryParameters: beforeId == null ? null : {'before_id': beforeId});
      messages = (response.data ?? [])
          .whereType<Map<String, dynamic>>()
          .map(WhatsAppMessage.fromJson)
          .toList();
      error = null;
    } catch (_) {
      error = 'No se pudieron cargar los mensajes.';
    } finally {
      loadingMessages = false;
      notifyListeners();
    }
  }

  Future<void> selectConversation(WhatsAppConversation conversation) async {
    selectedConversationId = conversation.id;
    messages = [];
    error = null;
    notifyListeners();
    await loadMessages(conversation.id);
  }

  Future<bool> sendText(int conversationId, String text) async {
    final trimmed = text.trim();
    if (trimmed.isEmpty) return false;
    sending = true;
    notifyListeners();
    try {
      await _api.post('/whatsapp/conversations/$conversationId/messages',
          data: {'type': 'text', 'text': trimmed});
      await loadMessages(conversationId);
      return true;
    } catch (_) {
      error =
          'No se pudo enviar. Revisa la ventana de 24 horas o usa una plantilla aprobada.';
      notifyListeners();
      return false;
    } finally {
      sending = false;
      notifyListeners();
    }
  }
}
