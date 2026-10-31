import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:kicks_insight/app/core/network/api_client.dart';
import 'package:kicks_insight/app/core/storage/session_storage.dart';
import 'package:kicks_insight/app/features/whatsapp/pages/whatsapp_page.dart';
import 'package:kicks_insight/app/features/whatsapp/providers/whatsapp_provider.dart';

class _NoTokenStorage extends SessionStorage {
  @override
  Future<String?> readToken() async => null;
}

class _InboxAdapter implements HttpClientAdapter {
  final requests = <RequestOptions>[];
  bool hasSentReply = false;

  @override
  Future<ResponseBody> fetch(RequestOptions options,
      Stream<Uint8List>? requestStream, Future<void>? cancelFuture) async {
    requests.add(options);
    final path = options.path;
    Object body;
    if (path.endsWith('/whatsapp/accounts')) {
      body = [
        {'id': 1, 'status': 'connected'}
      ];
    } else if (path.endsWith('/whatsapp/conversations/1/messages') &&
        options.method == 'POST') {
      hasSentReply = true;
      body = {
        'id': 2,
        'meta_message_id': 'wamid-out',
        'direction': 'outbound',
        'message_type': 'text',
        'body': 'Sí, disponible',
        'status': 'sent',
        'timestamp': '2026-10-30T10:01:00Z',
        'media_id': null
      };
    } else if (path.endsWith('/whatsapp/conversations/1/messages')) {
      body = [
        {
          'id': 1,
          'meta_message_id': 'wamid-in',
          'direction': 'inbound',
          'message_type': 'text',
          'body': '¿Tienes talla 42?',
          'status': 'received',
          'timestamp': '2026-10-30T10:00:00Z',
          'media_id': null
        },
        if (hasSentReply)
          {
            'id': 2,
            'meta_message_id': 'wamid-out',
            'direction': 'outbound',
            'message_type': 'text',
            'body': 'Sí, disponible',
            'status': 'sent',
            'timestamp': '2026-10-30T10:01:00Z',
            'media_id': null
          },
      ];
    } else if (path.endsWith('/whatsapp/conversations')) {
      body = [
        {
          'id': 1,
          'contact': {
            'id': 10,
            'wa_id': '59170000001',
            'phone_number': '59170000001',
            'display_name': 'Cliente de prueba'
          },
          'last_message_at': '2026-10-30T10:00:00Z',
          'last_customer_message_at': '2026-10-30T10:00:00Z',
          'unread_count': 1,
          'last_message_preview': '¿Tienes talla 42?',
          'last_message_type': 'text',
          'last_message_direction': 'inbound'
        }
      ];
    } else {
      body = {};
    }
    return ResponseBody.fromString(jsonEncode(body), 200, headers: {
      Headers.contentTypeHeader: [Headers.jsonContentType]
    });
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late Dio dio;
  late _InboxAdapter adapter;
  late WhatsAppProvider provider;

  setUp(() {
    adapter = _InboxAdapter();
    dio = Dio()..httpClientAdapter = adapter;
    provider = WhatsAppProvider(ApiClient(dio, _NoTokenStorage()));
  });

  tearDown(() async {
    await GetIt.I.reset();
    dio.close(force: true);
  });

  test('loads account, filtered conversation list, messages, and sends a reply',
      () async {
    await provider.loadAccountStatus();
    await provider.loadConversations(search: 'Cliente', unreadOnly: true);
    expect(provider.accountConnected, isTrue);
    expect(
        provider.conversations.single.lastMessagePreview, '¿Tienes talla 42?');
    expect(adapter.requests.last.queryParameters['unread_only'], isTrue);

    await provider.selectConversation(provider.conversations.single);
    expect(provider.messages.single.body, '¿Tienes talla 42?');
    expect(await provider.sendText(1, 'Sí, disponible'), isTrue);
    expect(adapter.requests.any((request) => request.method == 'POST'), isTrue);
    expect(provider.messages.last.direction, 'outbound');
  });

  testWidgets('renders a two-panel inbox and opens a conversation',
      (tester) async {
    addTearDown(() => tester.binding.setSurfaceSize(null));
    GetIt.I.registerFactory<WhatsAppProvider>(() => provider);
    await tester.binding.setSurfaceSize(const Size(1100, 800));
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: WhatsAppPage())));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));
    expect(find.text('WhatsApp Business'), findsOneWidget);
    expect(find.text('Cliente de prueba'), findsOneWidget);
    await tester.tap(find.text('Cliente de prueba').first);
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));
    expect(find.text('¿Tienes talla 42?'), findsOneWidget);
    await tester.binding.setSurfaceSize(null);
  });
}
