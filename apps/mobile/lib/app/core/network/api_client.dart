import 'package:dio/dio.dart';
import '../storage/session_storage.dart';

class ApiClient {
  ApiClient(this._dio, this._storage) { _dio.options = BaseOptions(baseUrl: const String.fromEnvironment('API_BASE_URL', defaultValue: 'http://localhost:8000/api/v1'), connectTimeout: const Duration(seconds: 10), receiveTimeout: const Duration(seconds: 15)); _dio.interceptors.add(InterceptorsWrapper(onRequest: (options, handler) async { final token = await _storage.readToken(); if (token != null) options.headers['Authorization'] = 'Bearer $token'; handler.next(options); })); }
  final Dio _dio;
  final SessionStorage _storage;
  Future<Response<T>> get<T>(String path, {Map<String, dynamic>? queryParameters}) => _dio.get<T>(path, queryParameters: queryParameters);
  Future<Response<T>> post<T>(String path, {Object? data}) => _dio.post<T>(path, data: data);
}

