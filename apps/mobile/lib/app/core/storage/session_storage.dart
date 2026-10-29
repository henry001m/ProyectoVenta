import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

class SessionStorage {
  static const _tokenKey = 'access_token';
  final FlutterSecureStorage _secure = const FlutterSecureStorage();
  late SharedPreferences preferences;
  bool hasToken = false;
  Future<void> init() async { preferences = await SharedPreferences.getInstance(); hasToken = await _secure.read(key: _tokenKey) != null; }
  Future<String?> readToken() => _secure.read(key: _tokenKey);
  Future<void> saveToken(String token) async { hasToken = true; await _secure.write(key: _tokenKey, value: token); }
  Future<void> clear() async { hasToken = false; await _secure.delete(key: _tokenKey); await preferences.clear(); }
}

