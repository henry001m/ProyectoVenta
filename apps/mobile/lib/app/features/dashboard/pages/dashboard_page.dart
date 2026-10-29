import 'package:flutter/material.dart';

class DashboardPage extends StatelessWidget {
  const DashboardPage({super.key});

  @override
  Widget build(BuildContext context) => ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text('Resumen de mercado', style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: 16),
          const Wrap(spacing: 12, runSpacing: 12, children: [
            _Metric(label: 'Observaciones', value: '0'),
            _Metric(label: 'Analizadas', value: '0'),
            _Metric(label: 'Demanda', value: '0'),
            _Metric(label: 'Ventas detectadas', value: '0'),
          ]),
          const SizedBox(height: 16),
          const Card(child: Padding(padding: EdgeInsets.all(16), child: Text('Importa publicaciones desde WhatsApp, TikTok o Marketplace para iniciar el análisis.'))),
        ],
      );
}
class _Metric extends StatelessWidget { const _Metric({required this.label, required this.value}); final String label; final String value; @override Widget build(BuildContext context) => SizedBox(width: 160, child: Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(label), Text(value, style: Theme.of(context).textTheme.headlineMedium)])))); }

