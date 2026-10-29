import 'package:dio/dio.dart';
import 'package:get_it/get_it.dart';
import '../network/api_client.dart';
import '../storage/session_storage.dart';
import '../../features/auth/providers/auth_provider.dart';
import '../../features/observations/providers/observations_provider.dart';

final getIt = GetIt.instance;

Future<void> configureDependencies() async {
  getIt.registerSingleton<SessionStorage>(SessionStorage());
  await getIt<SessionStorage>().init();
  getIt.registerLazySingleton<Dio>(() => Dio());
  getIt.registerLazySingleton<ApiClient>(() => ApiClient(getIt<Dio>(), getIt<SessionStorage>()));
  getIt.registerFactory<AuthProvider>(() => AuthProvider(getIt<ApiClient>(), getIt<SessionStorage>()));
  getIt.registerFactory<ObservationsProvider>(() => ObservationsProvider(getIt<ApiClient>()));
}

