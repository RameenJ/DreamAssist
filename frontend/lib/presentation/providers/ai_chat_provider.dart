import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../../data/services/ai_api_service.dart';
import '../../core/providers/app_providers.dart';

part 'ai_chat_provider.g.dart';

/// Chat message for UI
class ChatMessage {
  final String message;
  final bool isUser;
  final DateTime timestamp;
  final List<String>? sources;

  ChatMessage({
    required this.message,
    required this.isUser,
    DateTime? timestamp,
    this.sources,
  }) : timestamp = timestamp ?? DateTime.now();
}

/// AI Chat state
class AiChatState {
  final List<ChatMessage> messages;
  final bool isLoading;
  final String? error;
  final String? currentBookId;

  const AiChatState({
    this.messages = const [],
    this.isLoading = false,
    this.error,
    this.currentBookId,
  });

  AiChatState copyWith({
    List<ChatMessage>? messages,
    bool? isLoading,
    String? error,
    String? currentBookId,
  }) {
    return AiChatState(
      messages: messages ?? this.messages,
      isLoading: isLoading ?? this.isLoading,
      error: error,
      currentBookId: currentBookId ?? this.currentBookId,
    );
  }
}

/// AI Chat state notifier
@riverpod
class AiChat extends _$AiChat {
  @override
  AiChatState build() {
    return const AiChatState();
  }

  AiApiService get _aiService => ref.watch(aiApiServiceProvider);

  /// Set the current book context for chat
  void setCurrentBook(String bookId) {
    state = state.copyWith(
      currentBookId: bookId,
      messages: [], // Clear previous messages when switching books
      error: null,
    );
  }

  /// Send a message to AI mentor
  Future<void> sendMessage(String query) async {
    if (state.currentBookId == null) {
      state = state.copyWith(
        error: 'No book selected. Please select a book first.',
      );
      return;
    }

    // Add user message to chat
    final userMessage = ChatMessage(
      message: query,
      isUser: true,
    );

    state = state.copyWith(
      messages: [...state.messages, userMessage],
      isLoading: true,
      error: null,
    );

    final result = await _aiService.chatWithBook(state.currentBookId!, query);
    
    result.when(
      success: (response) {
        // Add AI response to chat
        final aiMessage = ChatMessage(
          message: response.answer,
          isUser: false,
          sources: response.sources,
        );

        state = state.copyWith(
          messages: [...state.messages, aiMessage],
          isLoading: false,
        );
      },
      failure: (message) {
        state = state.copyWith(
          isLoading: false,
          error: message,
        );
      },
    );
  }

  /// Clear chat history
  void clearChat() {
    state = state.copyWith(
      messages: [],
      error: null,
    );
  }

  /// Clear error
  void clearError() {
    state = state.copyWith(error: null);
  }

  /// Get chat history for current book
  List<ChatMessage> getChatHistory() {
    return state.messages;
  }
}
