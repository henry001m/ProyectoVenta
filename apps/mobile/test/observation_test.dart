import 'package:flutter_test/flutter_test.dart';
import 'package:kicks_insight/app/features/observations/models/observation.dart';

void main() { test('parses observation', () { final item = Observation.fromJson({'id': 1, 'raw_text': 'Nike talla 42', 'status': 'analyzed', 'price': 450}); expect(item.id, 1); expect(item.price, 450); }); }

