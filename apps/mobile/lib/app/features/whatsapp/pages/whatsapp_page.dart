import 'dart:async';

import 'package:flutter/material.dart';
import 'package:get_it/get_it.dart';

import '../models/whatsapp_conversation.dart';
import '../providers/whatsapp_provider.dart';

class WhatsAppPage extends StatefulWidget {
  const WhatsAppPage({super.key});

  @override
  State<WhatsAppPage> createState() => _WhatsAppPageState();
}

class _WhatsAppPageState extends State<WhatsAppPage>
    with WidgetsBindingObserver {
  late final WhatsAppProvider provider = GetIt.I<WhatsAppProvider>();
  final searchController = TextEditingController();
  final draftController = TextEditingController();
  Timer? poll;
  Timer? messagePoll;
  Timer? searchDebounce;
  WhatsAppConversation? selected;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    provider.loadAccountStatus();
    provider.loadConversations();
    _startPolling();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      provider.loadConversations();
      _startPolling();
    } else {
      poll?.cancel();
      poll = null;
      messagePoll?.cancel();
      messagePoll = null;
    }
  }

  void _startPolling() {
    poll?.cancel();
    poll = Timer.periodic(
        const Duration(seconds: 10), (_) => provider.loadConversations());
    _startMessagePolling();
  }

  void _startMessagePolling() {
    messagePoll?.cancel();
    if (selected == null) return;
    messagePoll = Timer.periodic(
        const Duration(seconds: 5), (_) => provider.loadMessages(selected!.id));
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    poll?.cancel();
    messagePoll?.cancel();
    searchDebounce?.cancel();
    searchController.dispose();
    draftController.dispose();
    provider.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AnimatedBuilder(
        animation: provider,
        builder: (context, _) => LayoutBuilder(
          builder: (context, constraints) {
            final wide = constraints.maxWidth >= 850;
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _pageHeader(context),
                if (provider.error != null)
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: Text(provider.error!,
                        style: TextStyle(
                            color: Theme.of(context).colorScheme.error)),
                  ),
                Expanded(
                  child: wide
                      ? Row(
                          children: [
                            SizedBox(
                                width: 350, child: _conversationList(context)),
                            const VerticalDivider(width: 1),
                            Expanded(
                              child: selected == null
                                  ? _emptyChat(context)
                                  : _chatView(context, selected!,
                                      showBack: false),
                            ),
                          ],
                        )
                      : _conversationList(context),
                ),
              ],
            );
          },
        ),
      );

  Widget _pageHeader(BuildContext context) => Padding(
        padding: const EdgeInsets.fromLTRB(16, 14, 16, 8),
        child: Row(
          children: [
            Expanded(
              child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('WhatsApp Business',
                        style: Theme.of(context).textTheme.headlineSmall),
                    const Text('Chats individuales recibidos por Cloud API'),
                  ]),
            ),
            if (!provider.accountChecking)
              Padding(
                padding: const EdgeInsets.only(right: 6),
                child: Text(
                    provider.accountConnected ? 'Conectado' : 'Desconectado',
                    style: TextStyle(
                        color: provider.accountConnected
                            ? Colors.green.shade700
                            : Colors.orange.shade800,
                        fontSize: 12)),
              ),
            IconButton(
              tooltip: 'Conectar número configurado en el backend',
              onPressed: provider.connecting || provider.accountConnected
                  ? null
                  : _connect,
              icon: provider.connecting
                  ? const SizedBox.square(
                      dimension: 20,
                      child: CircularProgressIndicator(strokeWidth: 2))
                  : const Icon(Icons.link),
            ),
          ],
        ),
      );

  Widget _conversationList(BuildContext context) => Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 8, 12, 6),
            child: TextField(
              controller: searchController,
              onChanged: (_) {
                searchDebounce?.cancel();
                searchDebounce = Timer(
                    const Duration(milliseconds: 300),
                    () => provider.loadConversations(
                        search: searchController.text));
              },
              decoration: const InputDecoration(
                  prefixIcon: Icon(Icons.search),
                  hintText: 'Buscar conversaciones',
                  border: OutlineInputBorder(),
                  isDense: true),
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            child: Row(children: [
              Expanded(
                child: Wrap(spacing: 4, runSpacing: 2, children: [
                  FilterChip(
                      label: const Text('Todas'),
                      selected: !provider.unreadOnly,
                      onSelected: (_) =>
                          provider.loadConversations(unreadOnly: false)),
                  FilterChip(
                      label: const Text('No leídas'),
                      selected: provider.unreadOnly,
                      onSelected: (_) =>
                          provider.loadConversations(unreadOnly: true)),
                ]),
              ),
              IconButton(
                  onPressed: provider.loadConversations,
                  tooltip: 'Actualizar',
                  icon: const Icon(Icons.refresh)),
            ]),
          ),
          if (provider.loading) const LinearProgressIndicator(),
          Expanded(
            child: provider.conversations.isEmpty
                ? Center(
                    child: Padding(
                      padding: const EdgeInsets.all(24),
                      child: Text(
                          provider.error ??
                              'No hay conversaciones. Los chats aparecerán cuando Meta los entregue a Cloud API.',
                          textAlign: TextAlign.center),
                    ),
                  )
                : RefreshIndicator(
                    onRefresh: provider.loadConversations,
                    child: ListView.separated(
                      itemCount: provider.conversations.length,
                      separatorBuilder: (_, __) =>
                          const Divider(height: 1, indent: 72),
                      itemBuilder: (context, index) {
                        final conversation = provider.conversations[index];
                        final name = _contactName(conversation);
                        final isSelected = selected?.id == conversation.id;
                        final preview = conversation.lastMessagePreview ??
                            _fallbackPreview(conversation.lastMessageType);
                        return ListTile(
                          selected: isSelected,
                          leading: CircleAvatar(
                              child: Text(
                                  name.isEmpty ? '?' : name[0].toUpperCase())),
                          title: Text(name,
                              maxLines: 1, overflow: TextOverflow.ellipsis),
                          subtitle: Text(
                              '${conversation.lastMessageDirection == 'outbound' ? 'Tú: ' : ''}$preview',
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis),
                          trailing: conversation.unreadCount > 0
                              ? Badge(
                                  label: Text('${conversation.unreadCount}'))
                              : null,
                          onTap: () => _openConversation(conversation,
                              wide: MediaQuery.sizeOf(context).width >= 850),
                        );
                      },
                    ),
                  ),
          ),
          const Padding(
            padding: EdgeInsets.fromLTRB(12, 8, 12, 10),
            child: Text(
                'No incluye la bandeja personal ni grupos que Meta no comparta.',
                style: TextStyle(fontSize: 11, color: Colors.grey)),
          ),
        ],
      );

  Widget _emptyChat(BuildContext context) => Center(
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Icon(Icons.chat_bubble_outline,
              size: 64, color: Theme.of(context).colorScheme.primary),
          const SizedBox(height: 12),
          Text('Tu bandeja de WhatsApp',
              style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 6),
          const Text(
              'Selecciona una conversación para ver los mensajes y responder.'),
        ]),
      );

  Widget _chatView(BuildContext context, WhatsAppConversation conversation,
          {required bool showBack}) =>
      Column(
        children: [
          Material(
            color: Theme.of(context).colorScheme.surface,
            child: ListTile(
              leading: showBack
                  ? BackButton(onPressed: () => Navigator.of(context).pop())
                  : CircleAvatar(
                      child: Text(_contactName(conversation)
                          .characters
                          .first
                          .toUpperCase())),
              title: Text(_contactName(conversation)),
              subtitle: Text(conversation.waId),
            ),
          ),
          Expanded(
            child: provider.loadingMessages
                ? const Center(child: CircularProgressIndicator())
                : provider.messages.isEmpty
                    ? Center(
                        child: Text(provider.error ??
                            'No hay mensajes guardados todavía.'))
                    : ListView.builder(
                        padding: const EdgeInsets.all(12),
                        itemCount: provider.messages.length,
                        itemBuilder: (context, index) {
                          final message = provider.messages[index];
                          final outbound = message.direction == 'outbound';
                          return Align(
                            alignment: outbound
                                ? Alignment.centerRight
                                : Alignment.centerLeft,
                            child: ConstrainedBox(
                              constraints: BoxConstraints(
                                  maxWidth:
                                      MediaQuery.sizeOf(context).width * .72),
                              child: Card(
                                color: outbound
                                    ? Theme.of(context)
                                        .colorScheme
                                        .primaryContainer
                                    : Theme.of(context).colorScheme.surface,
                                child: Padding(
                                  padding: const EdgeInsets.symmetric(
                                      horizontal: 12, vertical: 8),
                                  child: Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.end,
                                      children: [
                                        Align(
                                            alignment: Alignment.centerLeft,
                                            child: Text(message.body.isEmpty
                                                ? '[${message.type}]'
                                                : message.body)),
                                        Text(
                                            '${_time(message.timestamp)}${outbound ? ' · ${message.status}' : ''}',
                                            style: Theme.of(context)
                                                .textTheme
                                                .labelSmall),
                                      ]),
                                ),
                              ),
                            ),
                          );
                        },
                      ),
          ),
          _composer(context, conversation),
        ],
      );

  Widget _composer(BuildContext context, WhatsAppConversation conversation) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(8),
        child: Row(children: [
          Expanded(
              child: TextField(
                  controller: draftController,
                  textInputAction: TextInputAction.send,
                  onSubmitted: (value) =>
                      _send(conversation, value, draftController),
                  decoration: const InputDecoration(
                      hintText: 'Escribe un mensaje',
                      border: OutlineInputBorder(),
                      isDense: true))),
          const SizedBox(width: 8),
          IconButton.filled(
              onPressed: provider.sending || !provider.accountConnected
                  ? null
                  : () => _send(
                      conversation, draftController.text, draftController),
              icon: provider.sending
                  ? const SizedBox.square(
                      dimension: 18,
                      child: CircularProgressIndicator(strokeWidth: 2))
                  : const Icon(Icons.send),
              tooltip: 'Enviar'),
        ]),
      ),
    );
  }

  Future<void> _openConversation(WhatsAppConversation conversation,
      {required bool wide}) async {
    await provider.selectConversation(conversation);
    if (!mounted) return;
    if (wide) {
      setState(() => selected = conversation);
      _startMessagePolling();
      return;
    }
    poll?.cancel();
    messagePoll?.cancel();
    messagePoll = Timer.periodic(const Duration(seconds: 5),
        (_) => provider.loadMessages(conversation.id));
    await Navigator.of(context).push(MaterialPageRoute<void>(
        builder: (_) => Scaffold(
            body: SafeArea(
                child: AnimatedBuilder(
                    animation: provider,
                    builder: (context, _) =>
                        _chatView(context, conversation, showBack: true))))));
    if (!mounted) return;
    messagePoll?.cancel();
    messagePoll = null;
    _startPolling();
    provider.loadConversations();
  }

  Future<void> _send(WhatsAppConversation conversation, String text,
      TextEditingController controller) async {
    if (provider.sending || text.trim().isEmpty) return;
    final sent = await provider.sendText(conversation.id, text);
    if (sent) controller.clear();
    if (!sent && mounted)
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(provider.error ?? 'No se pudo enviar el mensaje.')));
  }

  Future<void> _connect() async {
    final connected = await provider.connectConfiguredAccount();
    if (!connected && mounted)
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(provider.error ?? 'No se pudo conectar WhatsApp.')));
  }

  String _contactName(WhatsAppConversation conversation) =>
      conversation.contactName.trim().isNotEmpty
          ? conversation.contactName
          : conversation.waId;
  String _fallbackPreview(String? type) => switch (type) {
        'image' => '[Imagen]',
        'audio' => '[Audio]',
        'video' => '[Video]',
        'document' => '[Archivo]',
        _ => 'Sin mensajes'
      };
  String _time(DateTime value) =>
      '${value.toLocal().hour.toString().padLeft(2, '0')}:${value.toLocal().minute.toString().padLeft(2, '0')}';
}
