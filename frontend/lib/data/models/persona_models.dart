// frontend/lib/data/models/persona_models.dart

class Persona {
  final String personaId;
  final String name;
  final String description;
  final String emoji;
  final String color;
  final String toneStyle;
  final String speakingStyle;
  final String unlockCondition;
  final bool isUnlocked;

  Persona({
    required this.personaId,
    required this.name,
    required this.description,
    required this.emoji,
    required this.color,
    required this.toneStyle,
    required this.speakingStyle,
    required this.unlockCondition,
    required this.isUnlocked,
  });

  factory Persona.fromJson(Map<String, dynamic> json) {
    return Persona(
      personaId: json['persona_id'] ?? '',
      name: json['name'] ?? '',
      description: json['description'] ?? '',
      emoji: json['emoji'] ?? '',
      color: json['color'] ?? '#000000',
      toneStyle: json['tone_style'] ?? '',
      speakingStyle: json['speaking_style'] ?? '',
      unlockCondition: json['unlock_condition'] ?? '',
      isUnlocked: json['is_unlocked'] ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'persona_id': personaId,
      'name': name,
      'description': description,
      'emoji': emoji,
      'color': color,
      'tone_style': toneStyle,
      'speaking_style': speakingStyle,
      'unlock_condition': unlockCondition,
      'is_unlocked': isUnlocked,
    };
  }

  // Copy method for updates
  Persona copyWith({
    String? personaId,
    String? name,
    String? description,
    String? emoji,
    String? color,
    String? toneStyle,
    String? speakingStyle,
    String? unlockCondition,
    bool? isUnlocked,
  }) {
    return Persona(
      personaId: personaId ?? this.personaId,
      name: name ?? this.name,
      description: description ?? this.description,
      emoji: emoji ?? this.emoji,
      color: color ?? this.color,
      toneStyle: toneStyle ?? this.toneStyle,
      speakingStyle: speakingStyle ?? this.speakingStyle,
      unlockCondition: unlockCondition ?? this.unlockCondition,
      isUnlocked: isUnlocked ?? this.isUnlocked,
    );
  }

  @override
  String toString() => 'Persona(id: $personaId, name: $name, unlocked: $isUnlocked)';
}

// ============================================================================
// PERSONA CHAT MODELS
// ============================================================================

class PersonaChatRequest {
  final String message;
  final String? personaId;
  final String? conversationId;

  PersonaChatRequest({
    required this.message,
    this.personaId,
    this.conversationId,
  });

  Map<String, dynamic> toJson() {
    return {
      'message': message,
      if (personaId != null) 'persona_id': personaId,
      if (conversationId != null) 'conversation_id': conversationId,
    };
  }
}

class PersonaChatResponse {
  final String response;
  final String personaName;
  final String personaEmoji;
  final String personaColor;
  final String conversationId;

  PersonaChatResponse({
    required this.response,
    required this.personaName,
    required this.personaEmoji,
    required this.personaColor,
    required this.conversationId,
  });

  factory PersonaChatResponse.fromJson(Map<String, dynamic> json) {
    return PersonaChatResponse(
      response: json['response'] ?? '',
      personaName: json['persona_name'] ?? '',
      personaEmoji: json['persona_emoji'] ?? '',
      personaColor: json['persona_color'] ?? '#000000',
      conversationId: json['conversation_id'] ?? '',
    );
  }

  @override
  String toString() => 'PersonaChatResponse(persona: $personaName, convId: $conversationId)';
}

// ============================================================================
// PERSONA CHAT MESSAGE (for UI display)
// ============================================================================

class PersonaChatMessage {
  final String id;
  final String sender; // 'user' or 'assistant'
  final String content;
  final String personaName;
  final String personaEmoji;
  final String personaColor;
  final DateTime timestamp;

  PersonaChatMessage({
    required this.id,
    required this.sender,
    required this.content,
    required this.personaName,
    required this.personaEmoji,
    required this.personaColor,
    required this.timestamp,
  });

  bool get isUserMessage => sender == 'user';
  bool get isAssistantMessage => sender == 'assistant';

  @override
  String toString() => 'PersonaChatMessage(sender: $sender, persona: $personaName)';
}

// ============================================================================
// CHAT HISTORY RESPONSE
// ============================================================================

class ChatMessage {
  final String sender; // 'user' or 'assistant'
  final String content;
  final DateTime createdAt;

  ChatMessage({
    required this.sender,
    required this.content,
    required this.createdAt,
  });

  factory ChatMessage.fromJson(Map<String, dynamic> json) {
    return ChatMessage(
      sender: json['sender'] ?? '',
      content: json['content'] ?? '',
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'] as String)
          : DateTime.now(),
    );
  }
}

class ChatHistoryResponse {
  final String conversationId;
  final String personaId;
  final String personaName;
  final String personaEmoji;
  final String personaColor;
  final List<ChatMessage> messages;

  ChatHistoryResponse({
    required this.conversationId,
    required this.personaId,
    required this.personaName,
    required this.personaEmoji,
    required this.personaColor,
    required this.messages,
  });

  factory ChatHistoryResponse.fromJson(Map<String, dynamic> json) {
    final messagesList = (json['messages'] as List<dynamic>?)
            ?.map((msg) => ChatMessage.fromJson(msg as Map<String, dynamic>))
            .toList() ??
        [];

    return ChatHistoryResponse(
      conversationId: json['conversation_id'] ?? '',
      personaId: json['persona_id'] ?? '',
      personaName: json['persona_name'] ?? '',
      personaEmoji: json['persona_emoji'] ?? '',
      personaColor: json['persona_color'] ?? '#000000',
      messages: messagesList,
    );
  }
}
