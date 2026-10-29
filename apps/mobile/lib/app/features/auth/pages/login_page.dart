import 'package:flutter/material.dart';
import 'package:get_it/get_it.dart';
import 'package:go_router/go_router.dart';
import '../providers/auth_provider.dart';

class LoginPage extends StatefulWidget { const LoginPage({super.key}); @override State<LoginPage> createState() => _LoginPageState(); }
class _LoginPageState extends State<LoginPage> {
  final email = TextEditingController(text: 'demo@kicks.local'); final password = TextEditingController(text: 'password123');
  @override void dispose() { email.dispose(); password.dispose(); super.dispose(); }
  @override
  Widget build(BuildContext context) => Scaffold(
        body: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 420),
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(mainAxisSize: MainAxisSize.min, children: [
                  Text('Kicks Insight', style: Theme.of(context).textTheme.headlineMedium),
                  const SizedBox(height: 8),
                  TextField(controller: email, decoration: const InputDecoration(labelText: 'Correo')),
                  TextField(controller: password, obscureText: true, decoration: const InputDecoration(labelText: 'Contraseña')),
                  const SizedBox(height: 16),
                  FilledButton(
                    onPressed: () async {
                      final ok = await GetIt.I<AuthProvider>().login(email.text, password.text);
                      if (ok && context.mounted) context.go('/dashboard');
                    },
                    child: const Text('Ingresar'),
                  ),
                ]),
              ),
            ),
          ),
        ),
      );
}

