import 'package:go_router/go_router.dart';
import 'package:get_it/get_it.dart';
import '../storage/session_storage.dart';
import '../../features/auth/pages/login_page.dart';
import '../../features/dashboard/pages/dashboard_page.dart';
import '../../features/observations/pages/observations_page.dart';
import '../../features/whatsapp/pages/whatsapp_page.dart';
import '../../shared/layout/app_shell.dart';

class AppRouter {
  static final router = GoRouter(
      initialLocation: '/login',
      redirect: (context, state) {
        final onLogin = state.matchedLocation == '/login';
        final authenticated = GetIt.I<SessionStorage>().hasToken;
        if (!authenticated && !onLogin) return '/login';
        if (authenticated && onLogin) return '/dashboard';
        return null;
      },
      routes: [
        GoRoute(path: '/login', builder: (_, __) => const LoginPage()),
        ShellRoute(builder: (_, __, child) => AppShell(child: child), routes: [
          GoRoute(
              path: '/dashboard', builder: (_, __) => const DashboardPage()),
          GoRoute(
              path: '/observations',
              builder: (_, __) => const ObservationsPage()),
          GoRoute(path: '/whatsapp', builder: (_, __) => const WhatsAppPage())
        ])
      ]);
}
