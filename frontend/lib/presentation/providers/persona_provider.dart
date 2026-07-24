// frontend/lib/presentation/providers/persona_provider.dart

import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/models/persona_models.dart';
import '../../data/repositories/persona_repository.dart';

// ============================================================================
// PROVIDERS
// ============================================================================

/// Repository provider
final personaRepositoryProvider = Provider<PersonaRepository>((ref) {
  return PersonaRepository();
});

/// Get all available personas (with unlock status)
final allPersonasProvider = FutureProvider<List<Persona>>((ref) async {
  final repository = ref.watch(personaRepositoryProvider);
  return repository.getAllPersonas();
});

/// Get only unlocked personas for current user
final unlockedPersonasProvider = FutureProvider<List<Persona>>((ref) async {
  final repository = ref.watch(personaRepositoryProvider);
  return repository.getUnlockedPersonas();
});

/// Notifier for managing selected persona
class SelectedPersonaNotifier extends Notifier<String> {
  final PersonaRepository _repository = PersonaRepository();
  
  @override
  String build() {
    _loadSelectedPersona();
    return 'newton';
  }

  /// Load selected persona from backend/cache
  Future<void> _loadSelectedPersona() async {
    // TODO: Load from user profile via backend
    // For now, default to Newton
    state = 'newton';
  }

  /// Select a new persona
  Future<bool> selectPersona(String personaId) async {
    try {
      final success = await _repository.selectPersona(personaId);
      if (success) {
        state = personaId;
      }
      return success;
    } catch (e) {
      return false;
    }
  }
}

/// Selected persona provider
final selectedPersonaProvider = NotifierProvider<SelectedPersonaNotifier, String>(() {
  return SelectedPersonaNotifier();
});

/// Get currently selected persona details
final currentPersonaProvider = FutureProvider<Persona?>((ref) async {
  try {
    final personaId = ref.watch(selectedPersonaProvider);
    final repository = ref.watch(personaRepositoryProvider);
    return repository.getPersonaDetails(personaId);
  } catch (e) {
    return null;
  }
});

// ============================================================================
// CHAT STATE MANAGEMENT
// ============================================================================

/// Chat message provider state
class ChatState {
  final List<PersonaChatMessage> messages;
  final bool isLoading;
  final String? error;
  final String? conversationId;

  ChatState({
    this.messages = const [],
    this.isLoading = false,
    this.error,
    this.conversationId,
  });

  ChatState copyWith({
    List<PersonaChatMessage>? messages,
    bool? isLoading,
    String? error,
    String? conversationId,
  }) {
    return ChatState(
      messages: messages ?? this.messages,
      isLoading: isLoading ?? this.isLoading,
      error: error,
      conversationId: conversationId ?? this.conversationId,
    );
  }
}

/// Chat notifier for managing conversation
class PersonaChatNotifier extends Notifier<ChatState> {
  final PersonaRepository _repository = PersonaRepository();

  @override
  ChatState build() {
    return ChatState();
  }

  /// Send message to persona and get response
  Future<void> sendMessage({
    required String message,
    String? personaId,
  }) async {
    // Set loading state
    state = state.copyWith(isLoading: true, error: null);

    try {
      final response = await _repository.chatWithPersona(
        message: message,
        personaId: personaId,
        conversationId: state.conversationId,
      );

      // Create user message
      final userMessage = PersonaChatMessage(
        id: DateTime.now().toString(),
        sender: 'user',
        content: message,
        personaName: 'You',
        personaEmoji: '👤',
        personaColor: '#808080',
        timestamp: DateTime.now(),
      );

      // Create assistant message
      final assistantMessage = PersonaChatMessage(
        id: DateTime.now().toString(),
        sender: 'assistant',
        content: response.response,
        personaName: response.personaName,
        personaEmoji: response.personaEmoji,
        personaColor: response.personaColor,
        timestamp: DateTime.now(),
      );

      // Update state with both messages
      final updatedMessages = [...state.messages, userMessage, assistantMessage];
      state = state.copyWith(
        messages: updatedMessages,
        isLoading: false,
        conversationId: response.conversationId,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  /// Clear conversation
  void clearConversation() {
    state = ChatState();
  }

  /// Start new conversation with persona
  void startNewConversation(String personaId) {
    state = ChatState();
  }

  /// Load chat history into the current state
  void loadHistory(ChatState history) {
    if (history.messages.isNotEmpty) {
      state = ChatState(
        messages: history.messages,
        conversationId: history.conversationId,
        isLoading: false,
      );
    }
  }
}

/// Persona chat provider
final personaChatProvider = NotifierProvider<PersonaChatNotifier, ChatState>(() {
  return PersonaChatNotifier();
});

/// Load chat history for a specific persona
final chatHistoryProvider = FutureProvider.family<ChatState?, String>((ref, personaId) async {
  try {
    final repository = ref.watch(personaRepositoryProvider);
    final history = await repository.getChatHistory(personaId);
    
    if (history == null) {
      return null;
    }

    // Convert ChatMessage objects to PersonaChatMessage objects for UI display
    final uiMessages = history.messages.map((msg) {
      return PersonaChatMessage(
        id: DateTime.now().toString(),
        sender: msg.sender,
        content: msg.content,
        personaName: msg.sender == 'user' ? 'You' : history.personaName,
        personaEmoji: msg.sender == 'user' ? '👤' : history.personaEmoji,
        personaColor: msg.sender == 'user' ? '#808080' : history.personaColor,
        timestamp: msg.createdAt,
      );
    }).toList();

    return ChatState(
      messages: uiMessages,
      conversationId: history.conversationId,
      isLoading: false,
    );
  } catch (e) {
    return null;
  }
});

// ============================================================================
// CONVENIENCE PROVIDERS
// ============================================================================

/// Check if a specific persona is unlocked
final isPersonaUnlockedProvider = FutureProvider.family<bool, String>((ref, personaId) async {
  final unlockedPersonas = await ref.watch(unlockedPersonasProvider.future);
  return unlockedPersonas.any((p) => p.personaId == personaId);
});

/// Get persona by ID
final personaByIdProvider = FutureProvider.family<Persona?, String>((ref, personaId) async {
  try {
    final repository = ref.watch(personaRepositoryProvider);
    return repository.getPersonaDetails(personaId);
  } catch (e) {
    return null;
  }
});

/// Get unlock progress (count of unlocked personas)
final unlockedCountProvider = FutureProvider<int>((ref) async {
  final unlockedPersonas = await ref.watch(unlockedPersonasProvider.future);
  return unlockedPersonas.length;
});

/// Get total personas count
final totalPersonasProvider = FutureProvider<int>((ref) async {
  final allPersonas = await ref.watch(allPersonasProvider.future);
  return allPersonas.length;
});
