// frontend/lib/presentation/screens/persona/persona_chat_screen.dart

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:avatar_glow/avatar_glow.dart';
import '../../widgets/persona_widgets.dart';
import '../../providers/persona_provider.dart';
import '../../../data/models/persona_models.dart';

enum AvatarState { idle, listening, thinking, speaking }

class PersonaChatScreen extends ConsumerStatefulWidget {
  const PersonaChatScreen({Key? key}) : super(key: key);

  @override
  ConsumerState<PersonaChatScreen> createState() => _PersonaChatScreenState();
}

class _PersonaChatScreenState extends ConsumerState<PersonaChatScreen>
    with TickerProviderStateMixin {
  final TextEditingController _messageController = TextEditingController();
  late AnimationController _animationController;
  late AnimationController _typingAnimationController;
  late FlutterTts _flutterTts;
  
  bool _showPersonaIntro = true;
  AvatarState _avatarState = AvatarState.idle;
  bool _isSpeaking = false;
  bool _isTyping = false;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 600),
      vsync: this,
    );
    _animationController.forward();
    
    _typingAnimationController = AnimationController(
      duration: const Duration(milliseconds: 500),
      vsync: this,
    );
    
    _messageController.addListener(() {
      setState(() {
        _isTyping = _messageController.text.isNotEmpty;
        if (_isTyping) {
          _typingAnimationController.repeat(reverse: true);
        } else {
          _typingAnimationController.stop();
        }
      });
    });
    
    _initializeTTS();
    _loadChatHistory();
  }

  void _loadChatHistory() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) {
        final selectedPersona = ref.read(selectedPersonaProvider);
        ref.refresh(chatHistoryProvider(selectedPersona));
      }
    });
  }

  @override
  void dispose() {
    _animationController.dispose();
    _typingAnimationController.dispose();
    _messageController.dispose();
    super.dispose();
  }

  Future<void> _initializeTTS() async {
    try {
      _flutterTts = FlutterTts();
      await _flutterTts.setLanguage("en-US");
      await _flutterTts.setSpeechRate(0.9);
      await _flutterTts.setPitch(0.8);
      _flutterTts.setCompletionHandler(_onTTSComplete);
    } catch (e) {
      debugPrint('Failed to initialize TTS: $e');
    }
  }

  void _onTTSComplete() {
    setState(() {
      _isSpeaking = false;
      _avatarState = AvatarState.idle;
    });
  }

  Future<void> _speakResponse(String text) async {
    setState(() {
      _isSpeaking = true;
      _avatarState = AvatarState.speaking;
    });

    try {
      await _flutterTts.speak(text);
    } catch (e) {
      debugPrint('Error speaking: $e');
      setState(() {
        _isSpeaking = false;
        _avatarState = AvatarState.idle;
      });
    }
  }

  void _showPersonaSelector() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => PersonaSelectorModal(
        onPersonaSelected: (personaId) {
          ref.read(personaChatProvider.notifier).startNewConversation(personaId);
          setState(() => _showPersonaIntro = true);
        },
      ),
    );
  }

  void _sendMessage() {
    if (_messageController.text.trim().isEmpty) return;

    final message = _messageController.text.trim();
    final selectedPersona = ref.read(selectedPersonaProvider);
    _messageController.clear();

    setState(() => _showPersonaIntro = false);
    setState(() => _avatarState = AvatarState.thinking);

    ref.read(personaChatProvider.notifier).sendMessage(
      message: message,
      personaId: selectedPersona,
    );
  }

  @override
  Widget build(BuildContext context) {
    final selectedPersona = ref.watch(selectedPersonaProvider);
    final chatHistoryAsync = ref.watch(chatHistoryProvider(selectedPersona));
    final chatState = ref.watch(personaChatProvider);
    final currentPersonaAsync = ref.watch(currentPersonaProvider);

    chatHistoryAsync.whenData((history) {
      if (history != null && chatState.messages.isEmpty) {
        ref.read(personaChatProvider.notifier).loadHistory(history);
      }
    });

    chatState.messages.isNotEmpty
        ? _onMessageReceived(chatState.messages.first)
        : null;

    return currentPersonaAsync.when(
      loading: () => Scaffold(
        appBar: AppBar(title: const Text('Loading...')),
        body: const Center(child: CircularProgressIndicator()),
      ),
      error: (error, stack) => Scaffold(
        appBar: AppBar(title: const Text('Error')),
        body: Center(child: Text('Error: $error')),
      ),
      data: (persona) {
        if (persona == null) {
          return Scaffold(
            appBar: AppBar(title: const Text('No Persona Selected')),
          );
        }

        return Scaffold(
          appBar: AppBar(
            title: Text('${persona.emoji} ${persona.name}'),
            elevation: 0,
          ),
          body: Column(
            children: [
              Padding(
                padding: const EdgeInsets.all(16),
                child: PersonaHeader(
                  onPersonaTap: _showPersonaSelector,
                ),
              ),

              Expanded(
                child: chatState.messages.isEmpty && _showPersonaIntro
                    ? _buildPersonaIntro(persona)
                    : _buildChatWithAvatar(chatState, persona),
              ),

              _buildInputArea(context, chatState),
            ],
          ),
        );
      },
    );
  }

  void _onMessageReceived(PersonaChatMessage message) {
    if (!message.isUserMessage && _avatarState == AvatarState.thinking && !_isSpeaking) {
      Future.delayed(const Duration(milliseconds: 500), () {
        setState(() => _avatarState = AvatarState.idle);
        _speakResponse(message.content);
      });
    }
  }

  Widget _buildAvatarWithState(Persona persona) {
    String getImagePath(String personaId, String state) {
      if (personaId.toLowerCase() == 'einstein') {
        return 'assets/images/${personaId}_chibi_$state.jpeg';
      }
      return 'assets/images/${personaId}_$state.png';
    }

    String imagePath = getImagePath(persona.personaId, 'idle');
    Color glowColor = Colors.white.withOpacity(0.6);
    bool showGlow = true;
    
    final screenWidth = MediaQuery.of(context).size.width;
    final avatarSize = (screenWidth * 0.45).clamp(150.0, 250.0);

    switch (_avatarState) {
      case AvatarState.idle:
        imagePath = getImagePath(persona.personaId, 'idle');
        glowColor = _hexToColor(persona.color).withOpacity(0.4);
        showGlow = true;
        break;
      case AvatarState.listening:
        imagePath = getImagePath(persona.personaId, 'listening');
        glowColor = Colors.green.withOpacity(0.6);
        showGlow = true;
        break;
      case AvatarState.thinking:
        imagePath = getImagePath(persona.personaId, 'thinking');
        glowColor = _hexToColor(persona.color).withOpacity(0.7);
        showGlow = true;
        break;
      case AvatarState.speaking:
        imagePath = getImagePath(persona.personaId, 'speaking');
        glowColor = _hexToColor(persona.color).withOpacity(0.8);
        showGlow = true;
        break;
    }

    Widget avatar = Container(
      width: avatarSize,
      height: avatarSize,
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.95),
        borderRadius: BorderRadius.circular(20),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(20),
        child: Image.asset(
          imagePath,
          width: avatarSize,
          height: avatarSize,
          fit: BoxFit.cover,
          errorBuilder: (context, error, stackTrace) {
            return Center(
              child: Icon(Icons.person, size: avatarSize * 0.5),
            );
          },
        ),
      ),
    );

    if (showGlow) {
      avatar = AvatarGlow(
        glowColor: glowColor,
        endRadius: avatarSize * 1.2,
        duration: Duration(milliseconds: _avatarState == AvatarState.speaking ? 600 : 1500),
        repeat: true,
        repeatPauseDuration: const Duration(milliseconds: 50),
        child: avatar,
      );
    }

    if (_avatarState == AvatarState.speaking) {
      _animationController.repeat(reverse: true);
      return ScaleTransition(
        scale: Tween<double>(begin: 0.92, end: 1.12).animate(
          CurvedAnimation(parent: _animationController, curve: Curves.elasticInOut),
        ),
        child: avatar,
      );
    } else if (_isTyping && _avatarState == AvatarState.idle) {
      return Transform.translate(
        offset: Offset(0, -15 * _typingAnimationController.value),
        child: avatar,
      );
    } else {
      _animationController.stop();
      return avatar;
    }
  }

  Widget _buildPersonaIntro(Persona persona) {
    return ScaleTransition(
      scale: Tween<double>(begin: 0.5, end: 1.0).animate(
        CurvedAnimation(parent: _animationController, curve: Curves.easeOut),
      ),
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const SizedBox(height: 40),
            _buildAvatarWithState(persona),
            const SizedBox(height: 24),
            Text(
              'Meet ${persona.name}',
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.bold,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            Text(
              persona.description,
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                color: Colors.grey.shade600,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            _buildTraitsCard(persona, context),
            const SizedBox(height: 32),
            ElevatedButton.icon(
              onPressed: () {
                setState(() => _showPersonaIntro = false);
              },
              icon: const Icon(Icons.chat_bubble_outline),
              label: const Text('Start Chatting'),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(
                  horizontal: 32,
                  vertical: 16,
                ),
              ),
            ),
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }

  Widget _buildTraitsCard(Persona persona, BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: _hexToColor(persona.color).withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: _hexToColor(persona.color).withOpacity(0.3),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Teaching Style',
            style: Theme.of(context).textTheme.titleSmall?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            '• Tone: ${persona.toneStyle}',
            style: Theme.of(context).textTheme.bodySmall,
          ),
          const SizedBox(height: 4),
          Text(
            '• Style: ${persona.speakingStyle}',
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ),
    );
  }

  Widget _buildChatWithAvatar(ChatState chatState, Persona persona) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.only(top: 8, bottom: 8),
          child: SizedBox(
            height: 120,
            child: _buildAvatarWithState(persona),
          ),
        ),

        Expanded(
          child: _buildChatMessages(chatState),
        ),
      ],
    );
  }

  Widget _buildChatMessages(ChatState chatState) {
    return ListView.builder(
      reverse: true,
      padding: const EdgeInsets.all(16),
      itemCount: chatState.messages.length,
      itemBuilder: (context, index) {
        final message = chatState.messages[chatState.messages.length - 1 - index];
        return _buildChatBubble(message, context);
      },
    );
  }

  Widget _buildChatBubble(PersonaChatMessage message, BuildContext context) {
    final isUser = message.isUserMessage;

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        mainAxisAlignment:
        isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          if (!isUser) ...[
            CircleAvatar(
              backgroundColor: _hexToColor(message.personaColor).withOpacity(0.2),
              child: Text(message.personaEmoji, style: const TextStyle(fontSize: 20)),
            ),
            const SizedBox(width: 8),
          ],
          Flexible(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: isUser
                    ? Colors.blue.withOpacity(0.8)
                    : _hexToColor(message.personaColor).withOpacity(0.1),
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(16),
                  topRight: const Radius.circular(16),
                  bottomLeft: Radius.circular(isUser ? 16 : 4),
                  bottomRight: Radius.circular(isUser ? 4 : 16),
                ),
                border: !isUser
                    ? Border.all(
                      color: _hexToColor(message.personaColor).withOpacity(0.3),
                    )
                    : null,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (!isUser)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 4),
                      child: Text(
                        message.personaName,
                        style: Theme.of(context).textTheme.labelSmall?.copyWith(
                          color: _hexToColor(message.personaColor),
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  Text(
                    message.content,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: isUser ? Colors.white : null,
                    ),
                  ),
                ],
              ),
            ),
          ),
          if (isUser) const SizedBox(width: 8),
        ],
      ),
    );
  }

  Widget _buildInputArea(BuildContext context, ChatState chatState) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.grey.shade100,
        border: Border(
          top: BorderSide(color: Colors.grey.shade300),
        ),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (chatState.isLoading)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: SizedBox(
                height: 24,
                child: Row(
                  children: [
                    const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      'Thinking...',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Colors.grey,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          
          if (chatState.error != null)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Text(
                'Error: ${chatState.error}',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Colors.red,
                ),
              ),
            ),
          
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _messageController,
                  enabled: !chatState.isLoading,
                  decoration: InputDecoration(
                    hintText: 'Type your message...',
                    prefixIcon: _isTyping ? Icon(Icons.edit, color: Colors.blue.shade400) : null,
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide: BorderSide(
                        color: _isTyping ? Colors.blue : Colors.grey.shade300,
                        width: _isTyping ? 2 : 1,
                      ),
                    ),
                    contentPadding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 14,
                    ),
                    filled: true,
                    fillColor: Colors.white,
                  ),
                  onSubmitted: (_) => _sendMessage(),
                  maxLines: 1,
                ),
              ),
              const SizedBox(width: 12),
              
              FloatingActionButton.small(
                onPressed: chatState.isLoading || _messageController.text.isEmpty
                    ? null
                    : _sendMessage,
                backgroundColor: _messageController.text.isNotEmpty
                    ? Colors.blue
                    : Colors.grey.shade300,
                child: const Icon(Icons.send, color: Colors.white, size: 20),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Color _hexToColor(String hex) {
    hex = hex.replaceFirst('#', '');
    return Color(int.parse(hex, radix: 16) + 0xFF000000);
  }
}
