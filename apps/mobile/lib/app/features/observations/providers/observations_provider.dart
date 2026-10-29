import 'package:flutter/foundation.dart';
import '../../../core/network/api_client.dart';
import '../models/observation.dart';

class ObservationsProvider extends ChangeNotifier {
  ObservationsProvider(this._api); final ApiClient _api; bool loading = false; String? error; List<Observation> items = [];
  Future<void> load() async { loading = true; notifyListeners(); try { final response = await _api.get<List<dynamic>>('/observations'); items = (response.data ?? []).whereType<Map<String, dynamic>>().map(Observation.fromJson).toList(); } catch (_) { error = 'No se pudieron cargar las observaciones'; } finally { loading = false; notifyListeners(); } }
}

