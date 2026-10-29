import 'package:flutter/material.dart';
import 'package:get_it/get_it.dart';
import '../providers/observations_provider.dart';

class ObservationsPage extends StatefulWidget { const ObservationsPage({super.key}); @override State<ObservationsPage> createState() => _ObservationsPageState(); }
class _ObservationsPageState extends State<ObservationsPage> { @override void initState() { super.initState(); GetIt.I<ObservationsProvider>().load(); } @override Widget build(BuildContext context) { final provider = GetIt.I<ObservationsProvider>(); return AnimatedBuilder(animation: provider, builder: (_, __) => ListView(padding: const EdgeInsets.all(16), children: [Text('Observaciones', style: Theme.of(context).textTheme.headlineMedium), const SizedBox(height: 12), FilledButton.icon(onPressed: () => _showImport(context), icon: const Icon(Icons.add), label: const Text('Importar publicación')), if (provider.loading) const LinearProgressIndicator(), if (provider.error != null) Text(provider.error!, style: TextStyle(color: Theme.of(context).colorScheme.error)), ...provider.items.map((item) => Card(child: ListTile(title: Text(item.rawText), subtitle: Text('${item.brand ?? 'Pendiente'} · ${item.status}'), trailing: Text(item.price?.toStringAsFixed(0) ?? '—'))))])); }
  void _showImport(BuildContext context) { showDialog<void>(context: context, builder: (_) => const AlertDialog(title: Text('Importación asistida'), content: Text('La carga de texto, enlaces, capturas y archivos se conectará al endpoint /sources/import.'))); }
}

