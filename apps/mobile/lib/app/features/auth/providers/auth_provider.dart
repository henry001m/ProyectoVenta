import 'package:flutter/foundation.dart';
import '../../../core/network/api_client.dart';
import '../../../core/storage/session_storage.dart';

class AuthProvider extends ChangeNotifier {
  AuthProvider(this._api, this._storage);
  final ApiClient _api; final SessionStorage _storage;
  bool loading = false; String? error;
  Future<bool> login(String email, String password) async { loading = true; error = null; notifyListeners(); try { final response = await _api.post<Map<String, dynamic>>('/auth/login', data: {'email': email, 'password': password}); final token = response.data?['access_token'] as String?; if (token == null) throw Exception('Token ausente'); await _storage.saveToken(token); return true; } catch (_) { error = 'No se pudo iniciar sesión'; return false; } finally { loading = false; notifyListeners(); } }
  Future<void> logout() async { await _storage.clear(); notifyListeners(); }
}

