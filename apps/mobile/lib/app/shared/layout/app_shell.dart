import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class AppShell extends StatelessWidget { const AppShell({super.key, required this.child}); final Widget child; @override Widget build(BuildContext context) => Scaffold(appBar: AppBar(title: const Text('Kicks Insight')), drawer: Drawer(child: ListView(children: [const DrawerHeader(child: Text('Mercado')), ListTile(leading: const Icon(Icons.dashboard), title: const Text('Dashboard'), onTap: () => context.go('/dashboard')), ListTile(leading: const Icon(Icons.inbox), title: const Text('Observaciones'), onTap: () => context.go('/observations'))])), body: child); }

